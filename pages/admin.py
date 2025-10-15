from django.contrib import admin
from .models import ContactMessage
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'user', 'created_at', 'is_read', 'has_notes']
    list_filter = ['created_at', 'is_read']
    search_fields = ['name', 'email', 'subject', 'message', 'user']
    readonly_fields = ['created_at']
    list_per_page = 20

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    mark_as_read.short_description = "علامت زدن به عنوان خوانده شده"

    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)

    mark_as_unread.short_description = "علامت زدن به عنوان خوانده نشده"

    def has_notes(self, obj):
        return bool(obj.admin_notes)

    has_notes.boolean = True
    has_notes.short_description = 'یادداشت دارد'

    actions = [mark_as_read, mark_as_unread]

    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'name', 'email')
        }),
        ('محتوا', {
            'fields': ('subject', 'message')
        }),
        ('وضعیت', {
            'fields': ('is_read', 'created_at')
        }),
    )






