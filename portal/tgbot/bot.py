import os
import sys
import logging
import uuid

from django.conf import settings

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.portal.settings')

import django

django.setup()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ConversationHandler, \
    ContextTypes, filters

from portal.tgbot.config import WAITING_FOR_TITLE, WAITING_FOR_CONTENT, WAITING_FOR_PHOTO, WAITING_FOR_CONFIRMATION, \
    TELEGRAM_BOT_TOKEN
from portal.tgbot.db import Database

logger = logging.getLogger('bot')



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
    await update.message.reply_text(
        "✅ **Содержание сохранено!**\n\n"
        "📷 Пришли фото к новости"
    )
    return WAITING_FOR_PHOTO


async def add_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинаем загрузку фото"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "⬆️ Отправь фото в этот чат:"
    )
    return WAITING_FOR_PHOTO


async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение фото"""
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
            'first_name': user.first_name,
            'last_name': user.last_name
        }

        news_data = {
            'title': context.user_data.get('title'),
            'content': context.user_data.get('content'),
            'category': None,
            'image_url': context.user_data.get('photo_url'),
        }

        news_id = await Database.save_news_from_telegram(user_data, news_data)

        if news_id:
            await query.edit_message_text(
                f"🎉 **Успешно!**\n\n"
                f"✅ Новость **#{news_id}** отправлена на модерацию!\n"
                f"⏳ Мы проверим её в ближайшее время.\n\n"
                f"📊 Статус можно будет отслеживать в личном кабинете.\n\n"
                f"📝 Хочешь добавить ещё новость? Отправь /new"
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
            WAITING_FOR_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            WAITING_FOR_CONTENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_content)],
            WAITING_FOR_PHOTO: [
                CallbackQueryHandler(add_photo, pattern='^add_photo$'),
                MessageHandler(filters.PHOTO, get_photo),
            ],
            WAITING_FOR_CONFIRMATION: [CallbackQueryHandler(confirm, pattern='^(send|cancel)$')],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_error_handler(error)

    logger.info("🤖 Бот запущен...")
    app.run_polling()


if __name__ == '__main__':
    main()
