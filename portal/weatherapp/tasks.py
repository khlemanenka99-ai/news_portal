from celery import shared_task
import logging
import requests
from django.core.cache import cache
from django.utils import timezone

from .models import City, Weather, Weather_codes

logger = logging.getLogger('weather')

@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def fetch_weather(self):
    logger.info("Запуск задачи погоды")
    cities = City.objects.all()
    for city in cities:
        try:
            url = f"https://api.open-meteo.com/v1/forecast?latitude={city.latitude}&longitude={city.longitude}&current_weather=true"

            logger.debug(f"Запрос погоды для города {city.name}: {url}")

            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Проверка статуса ответа

            data = response.json()
            weather = data.get('current_weather')

            if weather is None:
                logger.warning(f"Данные о текущей погоде не найдены для города {city.name}")
                continue  # Пропускаем этот город и переходим к следующему

            # Извлечение данных из ответа API
            temperature = weather.get('temperature')
            windspeed = weather.get('windspeed')
            winddirection = weather.get('winddirection')
            weather_code_value = weather.get('weathercode')
            weather_code_obj = Weather_codes.objects.get(code=weather_code_value)
            try:
                existing, created = Weather.objects.update_or_create(
                    city=city,
                    defaults={
                        'city': city,
                        'temperature': temperature,
                        'windspeed': windspeed,
                        'winddirection': winddirection,
                        'weathercode': weather_code_obj,
                        'date_updated': timezone.now()
                    }
                )
            except Exception as e:
                logger.error(f"Ошибка при сохранении новости в БД: {e}", exc_info=True)
                raise
            logger.info(f"Погода успешно обновлена: {weather}")

        except Exception as e:
            logger.error(f"Ошибка: {e}")
            raise self.retry(exc=e)

