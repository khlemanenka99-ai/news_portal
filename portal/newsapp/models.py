from django.db import models
from django.utils import timezone


class Category(models.Model):
    objects = models.Manager()

    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class TG_Author(models.Model):
    objects = models.Manager()

    telegram_user_id = models.BigIntegerField(null=True, blank=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

class News(models.Model):
    objects = models.Manager()

    title = models.CharField(max_length=100, unique=True)
    content = models.TextField(null=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    image_url = models.URLField(blank=True, null=True)
    is_approved = models.BooleanField(default=False)
    author = models.CharField(max_length=50, blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    telegram_author = models.ForeignKey(
        TG_Author,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return self.title

class Comments(models.Model):
    objects = models.Manager()

    comments = models.TextField(null=True, blank=True)
    news = models.ForeignKey(
        News,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    author = models.CharField(max_length=50, null=True, blank=True)
    date_created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.comments