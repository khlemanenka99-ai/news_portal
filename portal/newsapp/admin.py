from django.contrib import admin

from .models import News, Category, Comments


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_approved', 'category', 'author')
    list_filter = ('is_approved',)
    actions = ['approve_selected']

    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)
    approve_selected.short_description = "Одобрить выбранные новости"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Comments)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ('comments', 'author')