import re

from celery import shared_task
import logging
import requests
from django.core.cache import cache
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .models import News

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
    try:
        driver = webdriver.Chrome()
        driver.get("https://people.onliner.by/")

        # Ждем чтобы страница полностью загрузилась
        time.sleep(3)
        wait = WebDriverWait(driver, 10)

        title_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.news-tidings__link")))
        # Скроллим в видимую часть через JS
        driver.execute_script("arguments[0].scrollIntoView(true);", title_link)
        time.sleep(2)
        # Кликаем через JS
        driver.execute_script("arguments[0].click();", title_link)
    except Exception as e:
        logger.error(f"Ошибка при поиске или клике: {e}")
        raise self.retry(exc=e)

    time.sleep(3)

    try:
        titles = driver.find_elements(By.TAG_NAME, "h1")
        title_text = None
        if titles:
            title_text = titles[0].text
        else:
            logger.warning("Заголовок h1 не найден")

        # Получение стиля и извлечение URL
        div_element = driver.find_element(By.CLASS_NAME, 'news-header__image')
        style_attribute = div_element.get_attribute('style')
        # получение url с помощью регулярки
        match = re.search(r'"\s*(https?://[^\s"]+)\s*"', style_attribute)
        if match:
            image_url = match.group(1)
        else:
            logger.error("URL изображения не найден")
            image_url = None

        # Получение текста (абзацев)
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        content_texts = [p.text for p in paragraphs]
    except Exception as e:
        logger.error(f"Ошибка в блоке поиска тегов: {e}")

    try:
        existing_news, created = News.objects.update_or_create(
            title=title_text if title_text else '',
            defaults={
                'image_url': image_url if image_url else '',
                'content': ' '.join(content_texts),
                'is_approved': True,
            }
        )
        if created:
            logger.info("Создана новая новость.")
        else:
            logger.info("Обновлена существующая новость.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении новости: {e}")
    driver.quit()