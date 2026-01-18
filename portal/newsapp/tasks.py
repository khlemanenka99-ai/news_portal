import re

from celery import shared_task
import logging
import requests
from django.core.cache import cache
import time

from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .models import News, Category

# celery -A portal worker --loglevel=info команда для запуска воркера
# celery -A portal beat --loglevel=info команда для запуска расписания для воркера
# celery -A newsapp.tasks call dollar_to_byn для вызова одной задачи

logger = logging.getLogger('api')

@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def to_byn(self):
    logger.info("Запуск задачи валютных курсов")
    cache_keys = {
        'usd': 'dollar_to_byn_rate',
        'eur': 'euro_to_byn_rate',
        'rub': 'ruble_to_byn_rate'
    }
    codes = {
        'usd': 431,
        'eur': 451,
        'rub': 456
    }
    try:
        for key, code in codes.items():
            url = f'https://api.nbrb.by/exrates/rates/{code}?periodicity=0'
            response = requests.get(url, timeout=10)
            data = response.json()
            rate = data.get('Cur_OfficialRate')
            if rate is None:
                raise ValueError(f"Курс валюты с кодом {code} не найден")
            logger.info(f"{key.upper()}: {rate}")
            cache.set(cache_keys[key], rate, timeout=3600)
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def fetch_weather(self):
    logger.info("Запуск задачи погоды")
    latitude = 53.9006
    longitude = 27.5590
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            "?latitude={}&longitude={}&current_weather=true"
        ).format(latitude, longitude)
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Проверка статуса ответа
        data = response.json()

        weather = data.get('current_weather')
        if weather is None:
            raise ValueError("Данные о текущей погоде не найдены")

        cache.set('current_weather_minsk', weather, timeout=3600)
        logger.info(f"Погода успешно обновлена: {weather}")

    except Exception as e:
        logger.error(f"Ошибка: {e}")
        raise self.retry(exc=e)


@shared_task(bind=True, max_retries=5, default_retry_delay=10)
def news_pars(self):
    logger.info("Запуск задачи парсинга новостей")
    sources = [
        ("https://people.onliner.by/", 3),
        ("https://auto.onliner.by/", 4),
        ("https://tech.onliner.by/", 5),
        ("https://realt.onliner.by/", 6),
        ("https://money.onliner.by/", 7)
    ]
    driver = None
    for url, category_id in sources:
        try:
            driver = webdriver.Chrome()
            driver.get(url)

            # Ждем чтобы страница полностью загрузилась
            time.sleep(3)
            wait = WebDriverWait(driver, 10)

            news_block = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".news-tidings__link"))
            )
            title_link = news_block.find_element(By.CSS_SELECTOR, "a.news-tidings__stub, a.news-tiles__stub")
            # Скроллим в видимую часть через JS
            driver.execute_script("arguments[0].scrollIntoView(true);", title_link)
            time.sleep(2)
            # Кликаем через JS
            driver.execute_script("arguments[0].click();", title_link)

            time.sleep(3)

            # Поиск заголовка
            try:
                titles = driver.find_elements(By.TAG_NAME, "h1")
                if titles:
                    title_text = titles[0].text.strip()
                else:
                    raise ValueError("Заголовок не найден")
            except Exception as e:
                logger.error(f"Ошибка при поиске заголовка: {e}")
                raise

            # Поиск изображения
            try:
                div_element = driver.find_element(By.CLASS_NAME, 'news-header__image')
                style_attribute = div_element.get_attribute('style')
                match = re.search(r'"\s*(https?://[^\s"]+)\s*"', style_attribute)
                if match:
                    image_url = match.group(1)
                    logger.info(f"Найдено изображение: {image_url}")
                else:
                    logger.warning("URL изображения не найден")
                    image_url = ""
            except Exception as e:
                logger.warning(f"Ошибка при поиске изображения: {e}")
                image_url = ""

            # Поиск контента
            try:
                paragraphs = driver.find_elements(By.TAG_NAME, "p")
                content_texts = [p.text.strip() for p in paragraphs if p.text.strip()]
                content_text = " ".join(content_texts)
                logger.info(f"Найдено {len(content_texts)} абзацев текста")
            except Exception as e:
                logger.error(f"Ошибка при поиске контента: {e}")
                raise

            # Сохранение в базу данных
            try:
                category_obj = Category.objects.get(id=category_id)
                existing_news, created = News.objects.update_or_create(
                    title=title_text,
                    defaults={
                        'image_url': image_url,
                        'content': content_text,
                        'category': category_obj,
                        'is_approved': True,
                        'date_updated': timezone.now()
                    }
                )
            except Exception as e:
                logger.error(f"Ошибка при сохранении новости в БД: {e}", exc_info=True)
                raise

        except Exception as e:
            logger.error(f"Ошибка в задаче парсинга: {e}", exc_info=True)
            # Пробрасываем исключение для retry механизма Celery
            raise self.retry(exc=e)
        finally:
            driver.quit()