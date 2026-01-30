from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import News


# @receiver(post_save, sender=News)
# def clear_cache_on_news_add(sender, instance, created, **kwargs):
#     if created:
#         cache.clear()  # Очищает весь кеш
#         # Или, например, очистка конкретных ключей:
#         # cache.delete('конкретный ключ')
#
#         print("Кеш очищен после добавления нового файла.")

# сообщение админу при предложении новости