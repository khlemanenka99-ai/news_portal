import logging
import os
import django
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal.settings')
django.setup()

from newsapp.models import News, TG_Author, Category

logger = logging.getLogger('bot')

class Database:
    @staticmethod
    async def save_news_from_telegram(user_data, news_data):
        """Асинхронный метод сохранения новости"""
        try:
            # Используем sync_to_async для синхронных ORM-операций
            return await sync_to_async(Database._save_news_sync)(user_data, news_data)
        except Exception as e:
            print(f"Ошибка сохранения в БД: {e}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _save_news_sync(user_data, news_data):
        """Синхронная часть сохранения"""
        try:
            telegram_author, created = TG_Author.objects.get_or_create(
                telegram_user_id=user_data.get('id'),
                defaults={
                    'telegram_username': user_data.get('username'),
                }
            )

            # 2. Категория (по умолчанию)
            category = news_data.get('category')
            if not category:
                category = Category.objects.first()
                if not category:
                    category = Category.objects.create(name="Общее", slug="general")

            image_url = news_data.get('image_url')

            news = News.objects.create(
                title=news_data.get('title'),
                content=news_data.get('content'),
                category=category,
                image_url=image_url,
                author=f"Telegram: @{user_data.get('username') or user_data.get('id')}",
                telegram_author=telegram_author,
            )
            return news.id

        except Exception as e:
            logger.error(f"Ошибка в _save_news_sync: {e}")
            import traceback
            traceback.print_exc()
            return None
