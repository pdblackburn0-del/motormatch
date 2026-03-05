from django.contrib import admin

from apps.messaging.models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ('sender', 'recipient', 'subject', 'vehicle', 'is_read', 'created_at')
    list_filter   = ('is_read',)
    search_fields = ('sender__email', 'recipient__email', 'subject')
