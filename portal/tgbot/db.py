import logging
import aiohttp

logger = logging.getLogger('bot')

class Database:
    @staticmethod
    async def save_news_from_telegram(user_data, news_data):
        try:
            # Формируем данные для API
            api_data = {
                'title': news_data.get('title'),
                'content': news_data.get('content'),
                'image_url': news_data.get('image_url'),
                'author': f"telegram: @{user_data.get('username')}",
                'telegram_user_id': user_data.get('id'),
                'telegram_username': user_data.get('username'),
                'category': news_data.get('category'),
            }
            news_id = await Database._call_create_news_api(api_data)
            return news_id

        except Exception as e:
            logger.error(f"Ошибка сохранения через API: {e}")
            return None

    @staticmethod
    async def _call_create_news_api(data):
        api_url = f"http://127.0.0.1:8000/botapi/create/"
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(api_url, json=data) as response:
                    if response.status == 201:
                        result = await response.json()
                        return result.get('id')
                    else:
                        error_text = await response.text()
                        logger.error(f"API ошибка: {response.status}, {error_text}")
                        return None
            except Exception as e:
                logger.error(f"Ошибка соединения с API: {e}")
                return None
