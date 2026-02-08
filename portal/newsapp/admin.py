from django.contrib import admin
from django.utils import timezone

from .models import News, Category, Comments, TG_Author


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'moderation_status', 'author' , 'telegram_author', 'date_created', 'views', 'image_url')
    actions = ['approve_selected', 'rejected_selected']
    list_filter = ('moderation_status', 'category',)
    search_fields = ('title',)

    def approve_selected(self, request, queryset):
        queryset.update(moderation_status='approved')
        queryset.update(moderated_by=request.user)
        queryset.update(moderation_date=timezone.now())
    approve_selected.short_description = "Одобрить выбранные новости"

    def rejected_selected(self, request, queryset):
        queryset.update(moderation_status='rejected')
        queryset.update(moderated_by=request.user)
        queryset.update(moderation_date=timezone.now())
    rejected_selected.short_description = "Отклонить выбранные новости"


@admin.register(TG_Author)
class TG_AuthorAdmin(admin.ModelAdmin):
    list_display = ('telegram_user_id', 'telegram_username')
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('comments', 'author')