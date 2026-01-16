from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .forms import RegisterForm, NewsForm, CommentsForm
from .models import Category, News
from django.db.models import Q
from django.core.cache import cache
from django.views.decorators.cache import cache_page

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('products')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})



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
    weather_minsk = cache.get('current_weather_minsk')
    news_n = news.order_by('-date_created')
    return render(request, 'news.html', {
        'news': news_n,
        'categories': categories,
        'selected_category': category_id,
        'rate_usd': rate_usd,
        'rate_eur': rate_eur,
        'rate_rub': rate_rub,
        'weather_minsk': weather_minsk
    })


def news_detail(request, pk):
    news = get_object_or_404(News, pk=pk)
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
    return render(request, 'news_detail.html', {
        'news': news,
        'form': form,
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
