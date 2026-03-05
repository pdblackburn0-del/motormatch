from django.contrib import admin

from apps.vehicles.models import Bid, SavedVehicle, Vehicle
from apps.users.models import Review


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display    = ('title', 'variant', 'price', 'year', 'fuel', 'transmission', 'mileage', 'badge', 'owner')
    list_filter     = ('fuel', 'transmission', 'badge', 'year')
    search_fields   = ('title', 'variant', 'owner__email')
    ordering        = ('-created_at', 'title')
    readonly_fields = ('get_image',)


@admin.register(SavedVehicle)
class SavedVehicleAdmin(admin.ModelAdmin):
    list_display = ('user', 'vehicle', 'saved_at')
    list_filter  = ('saved_at',)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display  = ('bidder', 'vehicle', 'amount', 'status', 'created_at')
    list_filter   = ('status',)
    search_fields = ('bidder__email', 'vehicle__title')


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display  = ('reviewer', 'reviewed_user', 'rating', 'created_at')
    list_filter   = ('rating',)
    search_fields = ('reviewer__email', 'reviewed_user__email')
