from django import forms
from django.contrib.auth.models import User
from .models import News, Category, Comments


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


class NewsForm(forms.ModelForm):
    title = forms.CharField(
        label='Название статьи',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    content = forms.CharField(
        label='Статья',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        label='Выберите категорию',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    image_url = forms.URLField(
        label='URL картинки',
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = News
        fields = ['title', 'content', 'category', 'image_url']
        widgets = {
            'author': forms.HiddenInput(),
        }

class CommentsForm(forms.ModelForm):
    comments = forms.CharField(
        label='комментарии',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )

    class Meta:
        model = Comments
        fields = ['comments']
        widgets = {
            'author': forms.HiddenInput(),
        }
