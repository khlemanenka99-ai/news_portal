from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Avg, F
from .models import News
from weatherapp.models import Weather


class NewsService:

    @staticmethod
    def get_news(category_id=None, query=None):
        news = News.objects.filter(moderation_status='approved').order_by('-date_created')
        if category_id:
            news = news.filter(category_id=category_id)

        if query:
            news = news.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )

        return news

    @staticmethod
    def get_paginated_news(news, page_number=1, per_page=12):

        paginator = Paginator(news, per_page)
        page_obj = paginator.get_page(page_number)
        return page_obj, paginator

    @staticmethod
    def get_news_by_id(news_id):

        return News.objects.get(id=news_id)

    @staticmethod
    def increment_views(news_id, request):

        news = News.objects.filter(id=news_id).first()
        session_key = f'viewed_news_{news.pk}'
        if not request.session.get(session_key, False):
            News.objects.filter(id=news.pk).update(views=F('views') + 1)
            news.refresh_from_db()
            request.session[session_key] = True
            request.session.set_expiry(600)


    @staticmethod
    def avg_temperature():

        return Weather.objects.exclude(temperature__isnull=True).aggregate(
        t_avg=Avg('temperature'),
    )

    @staticmethod
    def currency():
        rate_usd = cache.get('dollar_to_byn_rate')
        rate_eur = cache.get('euro_to_byn_rate')
        rate_rub = cache.get('ruble_to_byn_rate')

        return rate_usd, rate_eur, rate_rub

