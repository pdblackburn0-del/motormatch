from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display  = ('title', 'variant', 'price', 'year', 'fuel', 'transmission', 'mileage', 'badge')
    list_filter   = ('fuel', 'transmission', 'badge', 'year')
    search_fields = ('title', 'variant')
    ordering      = ('-year', 'title')
    readonly_fields = ('get_image',)

