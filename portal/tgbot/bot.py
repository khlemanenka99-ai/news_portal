import os
import sys
import logging
import uuid

import aiohttp
from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.portal.settings')

import django

django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, \
    ContextTypes, filters

from portal.tgbot.config import WAITING_FOR_TITLE, WAITING_FOR_CONTENT, WAITING_FOR_PHOTO, WAITING_FOR_CONFIRMATION, \
    TELEGRAM_BOT_TOKEN, WAITING_FOR_CATEGORY
from portal.tgbot.db import Database

logger = logging.getLogger('bot')

CATEGORY_NAMES = {
    1: 'Люди',
    2: 'Авто',
    3: 'Технологии',
    4: 'Недвижимость',
    5: 'Экономика'
}

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
    📋 *Доступные команды:*

    /start - Начало работы с ботом
    /help - Показать это сообщение
    /new - Предложить новость
    /status <ID> - Проверить статус новости

    ❓ *Нужна помощь?*
    Если возникли проблемы, свяжитесь с администратором.
        """

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 Привет, {update.effective_user.first_name}!\n"
        "✨ Я бот для отправки новостей.\n\n"
        "📝 Отправь команду /new чтобы предложить новость."
    )

async def new_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "✏️ Напиши заголовок новости:"
    )
    return WAITING_FOR_TITLE


async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text(
        "✅ **Заголовок сохранен!**\n\n"
        "📄 Теперь напиши содержание новости:"
    )
    return WAITING_FOR_CONTENT


async def get_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['content'] = update.message.text

    # callback_data должен быть строкой, а не числом!
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Люди", callback_data="1")],  # Строка "1", а не число 1
        [InlineKeyboardButton("Авто", callback_data="2")],
        [InlineKeyboardButton("Технологии", callback_data="3")],
        [InlineKeyboardButton("Недвижимость", callback_data="4")],
        [InlineKeyboardButton("Экономика", callback_data="5")],
    ])

    await update.message.reply_text(
        "✅ **Содержание сохранено!**\n\n"
        "📂 *Выберите категорию для поста:*\n"
        "Нажмите на кнопку ниже:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

    return WAITING_FOR_CATEGORY


async def handle_category_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие на inline-кнопку категории"""
    query = update.callback_query
    await query.answer()

    category_id = int(query.data)  # Преобразуем строку в число
    category_name = CATEGORY_NAMES[category_id]

    context.user_data['category'] = category_id
    await query.edit_message_text(
        f"✅ *Категория выбрана:* {category_name}\n"
        "📷 *Отправьте фото:*\n"
        "Прикрепите изображение к сообщению",
        parse_mode='Markdown'
    )
    return WAITING_FOR_PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    media_dir = os.path.join(settings.MEDIA_ROOT, 'news_photos')
    os.makedirs(media_dir, exist_ok=True)

    logger.info(f"📁 Сохраняем в: {media_dir}")

    # Сохраняем фото
    photo_file = await update.message.photo[-1].get_file()
    filename = f"{uuid.uuid4()}.jpg"
    filepath = os.path.join(media_dir, filename)
    await photo_file.download_to_drive(filepath)

    # Сохраняем данные
    context.user_data['photo_path'] = filepath
    context.user_data['photo_url'] = f"{settings.MEDIA_URL}news_photos/{filename}"

    # Показываем превью
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Отправить на модерацию", callback_data='send')],
        [InlineKeyboardButton("🔄 Начать заново", callback_data='cancel'),
         InlineKeyboardButton("❌ Отменить", callback_data='cancel')]
    ])

    await update.message.reply_text(
        f"✅ **Фото получено!**\n\n"
        f"👀 **Предпросмотр новости:**\n\n"
        f"📌 **Заголовок:** {context.user_data['title']}\n"
        f"📄 **Категория:** {CATEGORY_NAMES[context.user_data['category']]}\n"
        f"📄 **Содержание:** {context.user_data['content'][:100]}...\n"
        f"📷 **Фото:** добавлено ✅\n\n"
        f"📤 **Отправить новость на модерацию?**",
        reply_markup=keyboard
    )

    return WAITING_FOR_CONFIRMATION


async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'send':
        user = update.effective_user
        user_data = {
            'id': user.id,
            'username': user.username,
        }

        category = context.user_data.get('category', {})

        news_data = {
            'title': context.user_data.get('title'),
            'content': context.user_data.get('content'),
            'category': context.user_data.get('category'),
            'image_url': context.user_data.get('photo_url'),
        }

        news_id = await Database.save_news_from_telegram(user_data, news_data)

        if news_id:
            await query.edit_message_text(
                f"🎉 **Успешно!**\n\n"
                f"✅ Новость **#{news_id}** отправлена на модерацию!\n"
                f"⏳ Мы проверим её в ближайшее время.\n\n"
                f"📝 Хочешь добавить ещё новость? Отправь /new"
                f"🏷️ Что бы узнать статус новости отправь /status {news_id}"
            )
        else:
            await query.edit_message_text(
                "😔 **Ошибка!**\n\n"
                "❌ Не удалось сохранить новость.\n"
                "🔧 Попробуйте позже или свяжитесь с администратором."
            )
    else:
        await query.edit_message_text(
            "🔄 **Отменено**\n\n"
            "❌ Создание новости прервано.\n"
            "📝 Чтобы начать заново, отправь /new"
        )

    context.user_data.clear()
    return ConversationHandler.END


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("📝 Укажите ID новости: /status 123")
        return
    news_id = context.args[0]

    try:
        async with aiohttp.ClientSession() as session:
            url = f'http://127.0.0.1:8000/botapi/check/{news_id}/'
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['status'] == 'approved':
                        m_status = 'Опубликовано ✅'
                    elif data['status'] == 'rejected':
                        m_status = 'Отклонена ❌'
                    elif data['status'] == 'pending':
                        m_status = 'На модерации ⏳'
                    await update.message.reply_text(
                        f"📰 Новость #{news_id}\n"
                        f"📌 {data['title']}\n"
                        f"🏷️ Статус: {m_status}"
                    )
                else:
                    await update.message.reply_text("❌ Новость не найдена")
    except:
        await update.message.reply_text("❌ Ошибка запроса")



async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено")
    context.user_data.clear()
    return ConversationHandler.END


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update.message:
        await update.message.reply_text("❌ Произошла ошибка")


def main():
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('new', new_news)],
        states={
            WAITING_FOR_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)
            ],
            WAITING_FOR_CONTENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_content)
            ],
            WAITING_FOR_CATEGORY: [
                CallbackQueryHandler(handle_category_button)
            ],
            WAITING_FOR_PHOTO: [
                MessageHandler(filters.PHOTO, get_photo),
            ],
            WAITING_FOR_CONFIRMATION: [
                CallbackQueryHandler(confirm, pattern='^(send|cancel)$')
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(conv_handler)
    app.add_error_handler(error)

    logger.info("🤖 Бот запущен...")
    app.run_polling()


if __name__ == '__main__':
    main()