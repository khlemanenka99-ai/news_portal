from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path
from .views import register_view, news_view, news_detail, add_news_view

urlpatterns = [
    path('', news_view, name='news'),
    path('news/<int:pk>/', news_detail, name='news_detail'),
    path('register/', register_view, name='register'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('addNews/', add_news_view, name='addNews')
]