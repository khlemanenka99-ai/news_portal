from django.test import TestCase
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from newsapp.models import News, TG_Author
import json


class NewsAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.create_url = '/botapi/create/'
        self.check_url = '/botapi/check/{}/'

        # Тестовый автор
        self.author = TG_Author.objects.create(
            telegram_user_id=123456789,
            telegram_username='test_user'
        )

        # Тестовая новость
        self.news = News.objects.create(
            title='Тестовая новость',
            content='Тестовое содержание',
            telegram_author=self.author,
            moderation_status='pending'
        )

    # Test 1: Успешное создание новости
    def test_create_news_success(self):
        """Тест успешного создания новости"""
        data = {
            'title': 'Новая тестовая новость',
            'content': 'Содержание новости',
            'telegram_user_id': 987654321,
            'telegram_username': 'new_user',
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(News.objects.count(), 2)
        self.assertEqual(response.data['title'], data['title'])

    # Test 2: Создание без обязательных полей
    def test_create_news_missing_title(self):
        """Тест создания без заголовка"""
        data = {
            'content': 'Содержание без заголовка',
            'telegram_user_id': 111222333,
            'telegram_username': 'user_no_title',
        }

        response = self.client.post(
            self.create_url,
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test 3: Получение существующей новости
    def test_get_existing_news(self):
        """Тест получения существующей новости"""
        response = self.client.get(self.check_url.format(self.news.id))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.news.id)
        self.assertEqual(response.data['title'], self.news.title)
        self.assertEqual(response.data['status'], self.news.moderation_status)

    # Test 4: Получение несуществующей новости
    def test_get_nonexistent_news(self):
        """Тест получения несуществующей новости"""
        response = self.client.get(self.check_url.format(99999))

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)