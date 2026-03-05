from django.contrib import admin
from .models import Vehicle

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('title', 'variant', 'price', 'year', 'fuel')
    search_fields = ('title', 'variant')
