from django.contrib import admin

from apps.users.models import LoginEvent, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display   = ('user', 'first_name', 'last_name', 'phone', 'location', 'badge')
    list_editable  = ('badge',)
    list_filter    = ('badge',)
    search_fields  = ('user__email', 'first_name', 'last_name')
    fieldsets = (
        ('Identity', {'fields': ('user', 'first_name', 'last_name', 'phone', 'avatar', 'bio', 'location')}),
        ('Badge',    {'fields': ('badge',), 'description': 'Assign a trust badge visible on seller profiles and reviews.'}),
    )


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display  = ('user', 'ip_address', 'city', 'country', 'is_confirmed', 'created_at')
    list_filter   = ('is_confirmed',)
    search_fields = ('user__email', 'ip_address')
