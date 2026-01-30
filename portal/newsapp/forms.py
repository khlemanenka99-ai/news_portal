from django import forms
from .models import News, Category, Comments


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
