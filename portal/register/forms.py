from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class RegisterForm(forms.ModelForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.CharField(
        label='Введите Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        label='Введите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Подтвердите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password2'):
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned_data

    def clean_password(self):
        password = self.cleaned_data.get('password')
        # Используем встроенные валидаторы пароля Django
        try:
            validate_password(password)
        except ValidationError as e:
            # Преобразуем ошибки в читаемый формат
            error_messages = []
            for error in e.messages:
                if 'too short' in error.lower():
                    error_messages.append('Пароль слишком короткий. Минимум 8 символов.')
                elif 'too common' in error.lower():
                    error_messages.append('Пароль слишком простой и распространенный.')
                elif 'numeric' in error.lower():
                    error_messages.append('Пароль не может состоять только из цифр.')
                else:
                    error_messages.append(error)

            raise ValidationError(error_messages)
        return password

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Проверка на уникальность имени пользователя
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Пользователь с таким именем уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Проверка на уникальность email
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

