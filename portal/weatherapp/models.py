from django.db import models

class City(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=100)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return self.name

class Weather_codes(models.Model):
    objects = models.Manager()

    code = models.IntegerField(unique=True, default=0)
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.description

class Weather(models.Model):
    objects = models.Manager()

    city = models.ForeignKey(
        City,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        default=0.00
    )
    windspeed = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )
    winddirection = models.IntegerField(null=True, blank=True)
    date_updated = models.DateTimeField(auto_now=True)
    weathercode = models.ForeignKey(
        "Weather_codes",
        to_field='code',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )



