from django.contrib import admin
from .models import City, Weather


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'latitude', 'longitude')
    search_fields = ('name',)

@admin.register(Weather)
class WeatherAdmin(admin.ModelAdmin):
    list_display = ('city', 'temperature', 'windspeed', 'winddirection', 'date_updated', 'weathercode')
    search_fields = ('city',)
