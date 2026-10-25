from django.contrib import admin
from .models import Concert, Venue, ProductionElement, TicketPackage


@admin.register(Concert)
class ConcertAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'is_active')
    list_filter = ('is_active',)


@admin.register(ProductionElement)
class ProductionElementAdmin(admin.ModelAdmin):
    list_display = ('name',)


@admin.register(TicketPackage)
class TicketPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'price', 'is_active')
    list_filter = ('is_active',)