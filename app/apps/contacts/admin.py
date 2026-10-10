from django.contrib import admin

from .models import Feedback


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('kind', 'stars', 'short_message', 'name', 'contact', 'page', 'created_at', 'is_read')
    list_display_links = ('kind', 'short_message')
    list_filter = ('kind', 'rating', 'is_read', 'created_at')
    list_editable = ('is_read',)
    search_fields = ('message', 'name', 'contact')
    readonly_fields = ('kind', 'rating', 'message', 'name', 'contact', 'page', 'created_at')
    actions = ['mark_read']

    @admin.display(description='Оценка', ordering='rating')
    def stars(self, obj):
        return '★' * obj.rating if obj.rating else '—'

    @admin.display(description='Отзыв')
    def short_message(self, obj):
        return obj.message if len(obj.message) <= 80 else obj.message[:80] + '…'

    @admin.action(description='Отметить прочитанными')
    def mark_read(self, request, queryset):
        queryset.update(is_read=True)

    def has_add_permission(self, request):
        return False
