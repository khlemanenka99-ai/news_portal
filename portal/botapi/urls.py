from django.urls import path
from botapi.views import NewsCreateAPIView, NewsCheckAPIView

urlpatterns = [
    path('create/', NewsCreateAPIView.as_view(), name='news-create'),
    path('check/<int:news_id>/', NewsCheckAPIView.as_view(), name='news-check'),
    ]