from django.urls import path
from .views import news_view, news_detail, add_news_view

urlpatterns = [
    path('', news_view, name='news'),
    path('news/<int:pk>/', news_detail, name='news_detail'),
    path('addNews/', add_news_view, name='addNews')
]