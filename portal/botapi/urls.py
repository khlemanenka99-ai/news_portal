from django.urls import path
from botapi.views import NewsCreateAPIView

urlpatterns = [
    path('create/', NewsCreateAPIView.as_view(), name='news-create'),
    ]