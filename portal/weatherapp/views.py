from django.shortcuts import render
from django.views.decorators.cache import cache_page

from .models import City, Weather

@cache_page(900)
def weather_view(request):
    all_cities = City.objects.all().order_by('name')
    city_id = request.GET.get('city_id')
    if city_id:
        display_cities = City.objects.filter(id=city_id)
    else:
        display_cities = all_cities
    weather_data = Weather.objects.filter(city__in=display_cities)

    context = {
        'all_cities': all_cities,
        'display_cities': display_cities,
        'weather_data': weather_data,
    }
    return render(request, 'weather.html', context)




