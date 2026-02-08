# import asyncio
# import logging
#
# from asgiref.sync import sync_to_async
# from django.db.models.signals import post_save, pre_save
# from django.dispatch import receiver
# from django.conf import settings
# from .models import News
# from telegram import Bot
# from telegram.error import TelegramError
#
# logger = logging.getLogger('app')
#
# @receiver(pre_save, sender=News)
# def track_status(sender, instance, **kwargs):
#     try:
#         old_news = News.objects.get(pk=instance.pk)
#         old_status = old_news.moderation_status
#         new_status = instance.moderation_status
#         if old_status != new_status:
#             logger.info(f"✅ YES! Статус изменился: {old_status} → {new_status}")
#             return new_status
#         handle_status_change_async(instance.pk, new_status)
#     except Exception as e:
#         logger.error(f"ошибка изменения статуса: {e}")

