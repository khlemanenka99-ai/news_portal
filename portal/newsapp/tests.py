from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
import datetime
from .forms import NewsForm
from .models import News, Category, Comments


class AddNewsViewTest(TestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.category = Category.objects.create(name="Тестовая категория")
        # URL для тестирования
        self.url = reverse('addNews')
        self.valid_form_data = {
            'title': 'Тестовая новость',
            'content': 'Содержание тестовой новости',
            'category': self.category.id,
            'image_url': 'https://example.com/image.jpg',
        }
        self.client = Client()

    def test_add_news_view_url_exists(self):
        """Проверка доступности URL"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_add_news_view_requires_login(self):
        """Проверка, что view требует аутентификации"""
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next=' + self.url)

    def test_add_news_view_get_authenticated(self):
        """Проверка GET запроса авторизованным пользователем"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'addNews.html')

        self.assertIsInstance(response.context['form'], NewsForm)
        self.assertContains(response, 'form-control')  # CSS класс из формы

    def test_add_news_view_post_valid_data(self):
        """Проверка POST запроса с валидными данными"""

        self.client.login(username='testuser', password='testpass123')
        initial_count = News.objects.count()
        response = self.client.post(self.url, data=self.valid_form_data)
        self.assertRedirects(response, reverse('news'))
        self.assertEqual(News.objects.count(), initial_count + 1)
        news = News.objects.latest('id')
        self.assertEqual(news.title, 'Тестовая новость')
        self.assertEqual(news.content, 'Содержание тестовой новости')
        self.assertEqual(news.category, self.category)
        self.assertEqual(news.image_url, 'https://example.com/image.jpg')
        self.assertEqual(news.author, 'testuser')  # username сохраняется

    def test_add_news_view_post_invalid_title(self):
        """Проверка POST запроса с невалидными данными"""
        self.client.login(username='testuser', password='testpass123')
        invalid_data = {
            'content': 'Содержание без заголовка',
            'category': self.category.id,
        }
        initial_count = News.objects.count()

        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'addNews.html')
        self.assertTrue(response.context['form'].errors)
        self.assertIn('title', response.context['form'].errors)
        self.assertEqual(News.objects.count(), initial_count)

    def test_add_news_view_post_invalid_content(self):
        """Проверка POST запроса с невалидными данными"""
        self.client.login(username='testuser', password='testpass123')
        invalid_data = {
            'title': 'Заголовок бкз содержания',
            'category': self.category.id,
        }
        initial_count = News.objects.count()

        response = self.client.post(self.url, data=invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'addNews.html')
        self.assertTrue(response.context['form'].errors)
        self.assertIn('content', response.context['form'].errors)
        self.assertEqual(News.objects.count(), initial_count)


class NewsViewTest(TestCase):
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем тестовые категории
        self.category1 = Category.objects.create(name="Политика")
        self.category2 = Category.objects.create(name="Спорт")
        self.category3 = Category.objects.create(name="Технологии")

        # Создаем тестового пользователя
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

        # Создаем тестовые новости с разными статусами и категориями
        now = datetime.datetime.now()

        # Одобренные новости
        self.news1 = News.objects.create(
            title='Новость 1 - Политика',
            content='Содержание новости 1',
            author=self.user,
            category=self.category1,
            is_approved=True,
            date_updated=now - datetime.timedelta(days=1)
        )

        self.news2 = News.objects.create(
            title='Новость 2 - Спорт',
            content='Содержание новости 2',
            author=self.user,
            category=self.category2,
            is_approved=True,
            date_updated=now - datetime.timedelta(days=2)
        )

        self.news3 = News.objects.create(
            title='Новость 3 - Технологии',
            content='Содержание новости 3',
            author=self.user,
            category=self.category3,
            is_approved=True,
            date_updated=now - datetime.timedelta(days=3)
        )

        # Неодобренная новость (не должна отображаться)
        self.news_unapproved = News.objects.create(
            title='Неодобренная новость',
            content='Эта новость не должна отображаться',
            author=self.user,
            category=self.category1,
            is_approved=False
        )
        # URL для тестирования
        self.url = reverse('news')

        # RequestFactory для создания запросов
        self.factory = RequestFactory()

    def tearDown(self):
        """Очистка после тестов"""
        cache.clear()

    def test_news_view_url_exists(self):
        """Проверка доступности URL"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_news_view_template_used(self):
        """Проверка используемого шаблона"""
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'news.html')

    def test_news_view_context_contains_all_data(self):
        """Проверка контекста со всеми данными"""
        response = self.client.get(self.url)

        # Проверяем наличие всех переменных в контексте
        self.assertIn('news', response.context)
        self.assertIn('categories', response.context)
        self.assertIn('selected_category', response.context)
        self.assertIn('rate_usd', response.context)
        self.assertIn('rate_eur', response.context)
        self.assertIn('rate_rub', response.context)
        self.assertIn('t_avg', response.context)

    def test_news_view_shows_only_approved_news(self):
        """Проверка, что отображаются только одобренные новости"""
        response = self.client.get(self.url)
        news_in_context = response.context['news']

        # Должны быть 3 одобренные новости
        self.assertEqual(news_in_context.count(), 3)

        # Проверяем, что неодобренной новости нет
        news_titles = [news.title for news in news_in_context]
        self.assertNotIn('Неодобренная новость', news_titles)

        # Проверяем, что одобренные новости есть
        self.assertIn('Новость 1 - Политика', news_titles)
        self.assertIn('Новость 2 - Спорт', news_titles)
        self.assertIn('Новость 3 - Технологии', news_titles)


    def test_news_view_with_category_filter(self):
        """Проверка фильтрации по категории"""
        # Фильтруем по первой категории
        response = self.client.get(f'{self.url}?category={self.category1.id}')
        news_in_context = response.context['news']

        # Должна быть только одна новость этой категории
        self.assertEqual(news_in_context.count(), 1)
        self.assertEqual(news_in_context[0].title, 'Новость 1 - Политика')
        self.assertEqual(news_in_context[0].category, self.category1)

        # Проверяем, что selected_category установлен
        self.assertEqual(response.context['selected_category'], str(self.category1.id))

    def test_news_view_with_invalid_category(self):
        """Проверка с несуществующей категорией"""
        response = self.client.get(f'{self.url}?category=999')
        news_in_context = response.context['news']

        # Не должно быть новостей (или все, если фильтр игнорирует несуществующие)
        # Зависит от реализации - можно проверить оба варианта
        self.assertEqual(news_in_context.count(), 0)

    def test_news_view_with_search_query(self):
        """Проверка поиска по заголовку"""
        # Ищем по слову "Политика"
        response = self.client.get(f'{self.url}?q=Политика')
        news_in_context = response.context['news']

        # Должна найтись только одна новость
        self.assertEqual(news_in_context.count(), 1)
        self.assertEqual(news_in_context[0].title, 'Новость 1 - Политика')

        # Ищем по слову "Новость"
        response = self.client.get(f'{self.url}?q=Новость')
        news_in_context = response.context['news']

        # Должны найтись все новости
        self.assertEqual(news_in_context.count(), 3)

    def test_news_view_search_case_insensitive(self):
        """Проверка регистронезависимого поиска"""
        # Поиск в нижнем регистре
        response = self.client.get(f'{self.url}?q=политика')
        news_in_context = response.context['news']

        # Должна найтись новость
        self.assertEqual(news_in_context.count(), 1)
        self.assertEqual(news_in_context[0].title, 'Новость 1 - Политика')

        # Поиск в верхнем регистре
        response = self.client.get(f'{self.url}?q=ПОЛИТИКА')
        news_in_context = response.context['news']
        self.assertEqual(news_in_context.count(), 1)

    def test_news_view_search_partial_match(self):
        """Проверка частичного совпадения при поиске"""
        # Создаем новость с длинным заголовком
        News.objects.create(
            title='Очень интересная новость про политику и экономику',
            content='Содержание',
            author=self.user,
            category=self.category1,
            is_approved=True
        )

        # Ищем по части слова
        response = self.client.get(f'{self.url}?q=интерес')
        news_in_context = response.context['news']

        # Должна найтись новость
        self.assertGreaterEqual(news_in_context.count(), 1)

    def test_news_view_combined_filters(self):
        """Проверка комбинированных фильтров (категория + поиск)"""
        # Добавляем еще одну новость в категорию "Политика"
        News.objects.create(
            title='Еще одна политическая новость',
            content='Содержание',
            author=self.user,
            category=self.category1,
            is_approved=True
        )

        # Фильтруем по категории и ищем по слову "политическая"
        response = self.client.get(
            f'{self.url}?category={self.category1.id}&q=политическая'
        )
        news_in_context = response.context['news']

        # Должна найтись только одна новость
        self.assertEqual(news_in_context.count(), 1)
        self.assertEqual(news_in_context[0].title, 'Еще одна политическая новость')

class CurrenciesViewTest(TestCase):
    def setUp(self):
        # Очищаем кэш
        cache.clear()
        # Устанавливаем кэш курсов валют
        cache.set('dollar_to_byn_rate', 3.25, timeout=300)
        cache.set('euro_to_byn_rate', 3.55, timeout=300)
        cache.set('ruble_to_byn_rate', 0.035, timeout=300)
        self.url = reverse('news')

    def test_news_view_currency_rates_in_context(self):
        """Проверка курсов валют в контексте"""
        response = self.client.get(self.url)

        # Проверяем значения из кэша
        self.assertEqual(response.context['rate_usd'], 3.25)
        self.assertEqual(response.context['rate_eur'], 3.55)
        self.assertEqual(response.context['rate_rub'], 0.035)

    def test_news_view_currency_rates_when_cache_empty(self):
        """Проверка, когда кэш пустой"""
        # Очищаем кэш
        cache.clear()

        response = self.client.get(self.url)

        # Должны быть None или другие значения по умолчанию
        self.assertIsNone(response.context['rate_usd'])
        self.assertIsNone(response.context['rate_eur'])
        self.assertIsNone(response.context['rate_rub'])


class NewsDetailUnitTests(TestCase):

    def setUp(self):
        # Минимальная настройка
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Технологии")
        self.news = News.objects.create(
            title='Тестовая новость',
            content='Содержание',
            author='author',
            category=self.category,
            is_approved=True,
            views=0
        )
        self.url = reverse('news_detail', kwargs={'pk': self.news.pk})
        self.client = Client()


    def test_view_returns_200_for_existing_news(self):
        """GET запрос возвращает 200 для существующей новости"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_returns_404_for_nonexistent_news(self):
        """GET запрос возвращает 404 для несуществующей новости"""
        response = self.client.get(reverse('news_detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_view_increments_views_counter(self):
        """Счетчик просмотров увеличивается при первом просмотре"""
        initial_views = self.news.views
        self.client.get(self.url)
        self.news.refresh_from_db()
        self.assertEqual(self.news.views, initial_views + 1)

    def test_view_does_not_increment_views_on_repeated_views(self):
        """Счетчик не увеличивается при повторном просмотре в той же сессии"""
        self.client.get(self.url)  # Первый просмотр
        self.news.refresh_from_db()
        first_count = self.news.views

        self.client.get(self.url)  # Второй просмотр (та же сессия)
        self.news.refresh_from_db()
        self.assertEqual(self.news.views, first_count)  # Не изменился

    def test_view_returns_comments_in_context(self):
        """Комментарии передаются в контексте"""
        # Создаем тестовый комментарий
        Comments.objects.create(
            news=self.news,
            author='commenter',
            comments='Тестовый комментарий'
        )

        response = self.client.get(self.url)
        self.assertIn('comments', response.context)
        self.assertEqual(response.context['comments'].count(), 1)

    def test_view_returns_form_in_context(self):
        """Форма комментариев передается в контексте"""
        response = self.client.get(self.url)
        self.assertIn('form', response.context)
        self.assertEqual(response.context['form'].__class__.__name__, 'CommentsForm')


class NewsDetailViewIntegrationTest(TestCase):
    """Интеграционные тесты полного сценария"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='integrationuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Интеграционная категория")
        self.news = News.objects.create(
            title='Интеграционная новость',
            content='Тестовое содержание',
            author='testauthor',
            category=self.category,
            is_approved=True,
            views=0
        )
        self.client = Client()
        self.url = reverse('news_detail', kwargs={'pk': self.news.pk})


class AddNewsViewUnitTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name="Технологии")
        self.url = reverse('addNews')
        self.valid_data = {
            'title': 'Тестовая новость',
            'content': 'Содержание',
            'category': self.category.id,
            'image_url': 'https://example.com/image.jpg',
        }
        self.client = Client()

    # ===== ОСНОВНЫЕ UNIT-ТЕСТЫ =====

    def test_requires_login(self):
        """View требует авторизации"""
        response = self.client.get(self.url)
        self.assertRedirects(response, f'/login/?next={self.url}')

    def test_get_request_returns_form(self):
        """GET запрос возвращает форму"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'addNews.html')
        self.assertIsInstance(response.context['form'], NewsForm)
        self.assertFalse(response.context['form'].is_bound)

    def test_post_valid_data_creates_news(self):
        """POST с валидными данными создает новость"""
        self.client.login(username='testuser', password='testpass123')
        initial_count = News.objects.count()

        response = self.client.post(self.url, self.valid_data)

        self.assertRedirects(response, reverse('news'))
        self.assertEqual(News.objects.count(), initial_count + 1)

        news = News.objects.latest('id')
        self.assertEqual(news.title, 'Тестовая новость')
        self.assertEqual(news.author, 'testuser')

    def test_post_invalid_data_returns_errors(self):
        """POST с невалидными данными возвращает ошибки"""
        self.client.login(username='testuser', password='testpass123')

        invalid_data = {'title': '', 'content': 'Текст'}  # Пустой заголовок

        response = self.client.post(self.url, invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
        self.assertIn('title', response.context['form'].errors)

    def test_form_saves_with_author(self):
        """Форма сохраняется с автором из request.user"""
        self.client.login(username='testuser', password='testpass123')

        response = self.client.post(self.url, self.valid_data)
        news = News.objects.latest('id')

        self.assertEqual(news.author, 'testuser')
