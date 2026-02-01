from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import NewsForm, CommentsForm
from .models import Category, News, Comments
from django.db.models import Q, F, Avg
from django.core.cache import cache

from weatherapp.models import Weather


def news_view(request):
    categories = Category.objects.all()
    category_id = request.GET.get('category')
    news = News.objects.filter(is_approved=True)
    query = request.GET.get('q')

    if category_id:
        news = news.filter(category_id=category_id)
    if query:
        news = news.filter(
            Q(title__icontains=query)
        )

    rate_usd = cache.get('dollar_to_byn_rate')
    rate_eur = cache.get('euro_to_byn_rate')
    rate_rub = cache.get('ruble_to_byn_rate')
    news_n = news.order_by('-date_created')
    t = Weather.objects.exclude(temperature__isnull=True).aggregate(
        t_avg=Avg('temperature'),
    )
    return render(request, 'news.html', {
        'news': news_n,
        'categories': categories,
        'selected_category': category_id,
        'rate_usd': rate_usd,
        'rate_eur': rate_eur,
        'rate_rub': rate_rub,
        't_avg': t['t_avg']
    })


def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk)
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
    session_key = f'viewed_news_{news.pk}'
    if not request.session.get(session_key, False):
        News.objects.filter(id=news.pk).update(views=F('views') + 1)
        news.refresh_from_db()
        request.session[session_key] = True
        request.session.set_expiry(600)
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
