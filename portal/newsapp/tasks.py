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

from .models import News, Category

logger = logging.getLogger('app')

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
def news_pars(self):
    logger.info("Запуск задачи парсинга новостей")
    sources = [
        ("https://people.onliner.by/", 1),
        ("https://auto.onliner.by/", 2),
        ("https://tech.onliner.by/", 3),
        ("https://realt.onliner.by/", 4),
        ("https://money.onliner.by/", 5)
    ]
    driver = None
    for url, category_id in sources:
        try:
            driver = webdriver.Chrome()
            driver.get(url)

            # Ждем чтобы страница полностью загрузилась
            time.sleep(3)
            wait = WebDriverWait(driver, 10)


            title_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.news-tidings__link")))
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

            # Поиск автора
            try:
                authors = driver.find_element(By.CSS_SELECTOR, ".news-header__author-link")
                if authors:
                    author_text = authors.text.strip()
                else:
                    raise ValueError("Автор не найден")
            except Exception as e:
                logger.error(f"Ошибка при поиске Автора: {e}")
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
                raise

            # Поиск контента
            try:
                paragraphs = driver.find_elements(By.TAG_NAME, "p")
                content_texts = []
                for p in paragraphs:
                    text = p.get_attribute('innerText') or p.text
                    if text.strip():
                        content_texts.append(text.strip())

                content_text = "\n\n".join(content_texts)
                logger.info(f"Найдено {len(content_texts)} абзацев текста")
            except Exception as e:
                logger.error(f"Ошибка при поиске контента: {e}")
                raise

            # Сохранение в базу данных
            try:
                category_obj = Category.objects.get(id=category_id)
                existing_news = News.objects.filter(
                    title=title_text,
                    category=category_obj
                ).first()
                if existing_news:
                    continue
                created = News.objects.create(
                    title=title_text,
                    author=author_text,
                    image_url=image_url,
                    content=content_text,
                    category=category_obj,
                    moderation_status='approved',
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