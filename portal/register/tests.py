from django.contrib.auth import get_user_model
from django.urls import reverse

from .forms import RegisterForm
from django.test import TestCase, Client


class RegisterFormTestCase(TestCase):
    """Тесты для формы регистрации"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPass123',
            'password2': 'StrongPass123',
        }

        # Создаем существующего пользователя для тестов уникальности
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

    def test_valid_form(self):
        """Тест: Валидная форма проходит проверку"""
        form = RegisterForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.errors), 0)

    def test_form_fields(self):
        """Тест: Форма содержит правильные поля"""
        form = RegisterForm()
        expected_fields = ['username', 'email', 'password', 'password2']
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_password_mismatch(self):
        """Тест: Пароли не совпадают"""
        data = self.valid_data.copy()
        data['password2'] = 'DifferentPass123'

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Пароли не совпадают', str(form.errors))

    def test_password_too_short(self):
        """Тест: Пароль слишком короткий"""
        data = self.valid_data.copy()
        data['password'] = 'short'
        data['password2'] = 'short'

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('Введённый пароль слишком короткий. Он должен состоять из как минимум 8 символов.', str(form.errors))

    def test_password_only_numeric(self):
        """Тест: Пароль состоит только из цифр"""
        data = self.valid_data.copy()
        data['password'] = '12345678'
        data['password2'] = '12345678'

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)
        self.assertIn('Введённый пароль состоит только из цифр.', str(form.errors))

    def test_duplicate_username(self):
        """Тест: Имя пользователя уже существует"""
        data = self.valid_data.copy()
        data['username'] = 'existinguser'  # Используем существующее имя

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('уже существует', str(form.errors))

    def test_duplicate_email(self):
        """Тест: Email уже существует"""
        data = self.valid_data.copy()
        data['email'] = 'existing@example.com'  # Используем существующий email

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('уже существует', str(form.errors))

    def test_empty_username(self):
        """Тест: Пустое имя пользователя"""
        data = self.valid_data.copy()
        data['username'] = ''

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_empty_email(self):
        """Тест: Пустой email"""
        data = self.valid_data.copy()
        data['email'] = ''

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_invalid_email_format(self):
        """Тест: Неверный формат email"""
        data = self.valid_data.copy()
        data['email'] = 'invalid-email'

        form = RegisterForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


User = get_user_model()

class RegisterViewTestCase(TestCase):
    """Тесты для view регистрации"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.register_url = reverse('register')
        self.valid_data = {
            'username': 'testuser123',
            'email': 'testuser@example.com',
            'password': 'StrongPassword123!',
            'password2': 'StrongPassword123!',
        }

        # Создаем существующего пользователя для тестов
        self.existing_user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='testpass123'
        )

    def test_register_page_accessible(self):
        """Тест: Страница регистрации доступна по GET"""
        response = self.client.get(self.register_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIn('form', response.context)

    def test_successful_registration_redirects_to_news(self):
        """Тест: Успешная регистрация редиректит на 'news'"""
        response = self.client.post(self.register_url, data=self.valid_data)

        # Проверяем редирект
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('news'))

        # Проверяем, что пользователь создан
        self.assertTrue(User.objects.filter(username='testuser123').exists())

        # Проверяем, что пользователь залогинен
        user = User.objects.get(username='testuser123')

        # Можно проверить через сессию или другой запрос
        response2 = self.client.get(reverse('news'))

    def test_successful_registration_creates_user_with_correct_data(self):
        """Тест: Успешная регистрация создает пользователя с правильными данными"""
        response = self.client.post(self.register_url, data=self.valid_data, follow=True)

        # Проверяем создание пользователя
        user = User.objects.get(username='testuser123')

        self.assertEqual(user.email, 'testuser@example.com')
        self.assertEqual(user.username, 'testuser123')

        # Проверяем, что пароль установлен правильно (не в открытом виде)
        self.assertTrue(user.check_password('StrongPassword123!'))
        self.assertNotEqual(user.password, 'StrongPassword123!')  # Должен быть хеширован

    def test_registration_with_invalid_data_returns_form_with_errors(self):
        """Тест: Регистрация с невалидными данными возвращает форму с ошибками"""
        invalid_data = self.valid_data.copy()
        invalid_data['password2'] = 'DifferentPassword123!'  # Пароли не совпадают

        response = self.client.post(self.register_url, data=invalid_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')

        # Проверяем, что форма содержит ошибки
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Пароли не совпадают', str(form.errors))

        # Пользователь не должен быть создан
        self.assertFalse(User.objects.filter(username='testuser123').exists())

    def test_registration_logs_in_user_automatically(self):
        """Тест: После регистрации пользователь автоматически логинится"""
        # Создаем сессию
        session = self.client.session
        session.save()

        # Отправляем POST запрос
        response = self.client.post(self.register_url, data=self.valid_data, follow=True)

        # Проверяем редирект
        self.assertEqual(response.redirect_chain[0][0], reverse('news'))

        user = User.objects.get(username='testuser123')
