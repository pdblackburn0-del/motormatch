from django.contrib import admin
from .models import Bid, LoginEvent, Message, Notification, Review, SavedVehicle, UserProfile, Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display  = ('title', 'variant', 'price', 'year', 'fuel', 'transmission', 'mileage', 'badge', 'owner')
    list_filter   = ('fuel', 'transmission', 'badge', 'year')
    search_fields = ('title', 'variant', 'owner__email')
    ordering      = ('-created_at', 'title')
    readonly_fields = ('get_image',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'first_name', 'last_name', 'phone', 'location')
    search_fields = ('user__email', 'first_name', 'last_name')


@admin.register(SavedVehicle)
class SavedVehicleAdmin(admin.ModelAdmin):
    list_display  = ('user', 'vehicle', 'saved_at')
    list_filter   = ('saved_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ('user', 'title', 'notif_type', 'is_read', 'created_at')
    list_filter   = ('notif_type', 'is_read')
    search_fields = ('user__email', 'title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('reviewer', 'reviewed_user', 'rating', 'created_at')
    list_filter   = ('rating',)
    search_fields = ('reviewer__email', 'reviewed_user__email')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display  = ('sender', 'recipient', 'subject', 'vehicle', 'is_read', 'created_at')
    list_filter   = ('is_read',)
    search_fields = ('sender__email', 'recipient__email', 'subject')


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display  = ('bidder', 'vehicle', 'amount', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('bidder__email', 'vehicle__title')


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    list_display  = ('user', 'ip_address', 'city', 'country', 'is_confirmed', 'created_at')
    list_filter   = ('is_confirmed', 'country')
    search_fields = ('user__email', 'ip_address', 'city')
    readonly_fields = ('user', 'ip_address', 'user_agent', 'city', 'region', 'country', 'country_code', 'isp', 'lat', 'lon', 'created_at')

