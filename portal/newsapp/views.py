from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.cache import cache_page
from .forms import NewsForm, CommentsForm
from .models import Category, Comments
from .services import NewsService

cache_page(60)
def news_view(request):
    category_id = request.GET.get('category')
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    news = NewsService.get_news(category_id=category_id, query=query)
    page_obj, paginator = NewsService.get_paginated_news(
        news=news,
        page_number=page_number,
        per_page=12
    )
    rate_usd, rate_eur, rate_rub = NewsService.currency()
    t = NewsService.avg_temperature()
    return render(request, 'news.html', {
        'page_obj': page_obj,
        'categories': Category.objects.all(),
        'selected_category': request.GET.get('category'),
        'rate_usd': rate_usd,
        'rate_eur': rate_eur,
        'rate_rub': rate_rub,
        't_avg': t['t_avg']
    })

cache_page(60)
def news_detail(request, pk):
    news = NewsService.get_news_by_id(pk)
    comments = Comments.objects.filter(news=news).order_by('-date_created')
    if request.method == 'POST':
        form = CommentsForm(request.POST)
        if form.is_valid():
            comments = form.save(commit=False)
            comments.author = request.user.username
            comments.news = news
            comments.save()
            return redirect('news_detail', pk=pk)
    else:
        form = CommentsForm()

    NewsService.increment_views(pk, request)

    return render(request, 'news_detail.html', {
        'news': news,
        'form': form,
        'comments': comments
    })

@login_required(login_url='/login/')
def add_news_view(request):
    if request.method == 'POST':
        form = NewsForm(request.POST)
        if form.is_valid():
            news = form.save(commit=False)
            news.author = request.user.username
            news.save()
            return redirect('news')
    else:
        form = NewsForm()
    return render(request, 'addNews.html', {'form': form})
