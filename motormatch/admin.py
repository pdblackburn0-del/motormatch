import csv
from django import forms
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.http import HttpResponse
from django.utils.html import format_html

try:
    from cloudinary.forms import CloudinaryFileField
    _CLOUDINARY_AVAILABLE = True
except ImportError:
    _CLOUDINARY_AVAILABLE = False

from motormatch.models import (
    Bid, LoginEvent, Message, Notification, Review, SavedVehicle,
    UserProfile, Vehicle,
)

User = get_user_model()

_BADGE_HEX = {
    'member':     '#6b7280',
    'verified':   '#2563eb',
    'trusted':    '#16a34a',
    'top_seller': '#d97706',
    'dealer':     '#0891b2',
    'staff':      '#dc2626',
}

_STATUS_HEX = {
    'pending':   ('#d97706', '#fef3c7'),
    'accepted':  ('#16a34a', '#dcfce7'),
    'declined':  ('#dc2626', '#fee2e2'),
    'countered': ('#2563eb', '#dbeafe'),
}

_NOTIF_HEX = {
    'info':    ('#2563eb', '#dbeafe'),
    'success': ('#16a34a', '#dcfce7'),
    'warning': ('#d97706', '#fef3c7'),
}


# ── Custom Admin Site ──────────────────────────────────────────────────────────

class MotorMatchAdminSite(AdminSite):
    site_header = 'Motor Match'
    site_title  = 'Motor Match Admin'
    index_title = 'Overview'

    def index(self, request, extra_context=None):
        extra_context = extra_context or {}
        try:
            extra_context.update({
                'stat_users':    User.objects.count(),
                'stat_vehicles': Vehicle.objects.filter(is_removed=False).count(),
                'stat_bids':     Bid.objects.filter(status=Bid.STATUS_PENDING).count(),
                'stat_messages': Message.objects.filter(is_read=False).count(),
                'recent_logins':   (LoginEvent.objects
                                    .select_related('user')
                                    .order_by('-created_at')[:6]),
                'recent_vehicles': (Vehicle.objects
                                    .filter(is_removed=False)
                                    .select_related('owner')
                                    .order_by('-created_at')[:5]),
                'recent_bids':     (Bid.objects
                                    .select_related('bidder', 'vehicle')
                                    .order_by('-created_at')[:5]),
            })
        except Exception:
            pass
        return super().index(request, extra_context=extra_context)


admin_site = MotorMatchAdminSite(name='motormatch_admin')


# ── Helpers ───────────────────────────────────────────────────────────────────

def _pill(label, fg, bg):
    return format_html(
        '<span style="background:{};color:{};padding:2px 10px;border-radius:99px;'
        'font-size:11px;font-weight:600;white-space:nowrap;">{}</span>',
        bg, fg, label,
    )

def _dash():
    return format_html('<span style="color:#9ca3af;">—</span>')


# ── User + Profile ─────────────────────────────────────────────────────────────

class UserProfileInline(admin.StackedInline):
    model               = UserProfile
    can_delete          = False
    verbose_name_plural = 'Profile'
    extra               = 0
    fields              = ('first_name', 'last_name', 'phone', 'location', 'bio', 'badge')


class UserAdmin(BaseUserAdmin):
    inlines       = [UserProfileInline]
    list_display  = ('email', '_name', 'is_staff', 'is_active', 'date_joined')
    list_filter   = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'profile__first_name', 'profile__last_name')
    ordering      = ('-date_joined',)
    list_per_page = 25
    actions       = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff']

    def _name(self, obj):
        try:
            return obj.profile.get_display_name()
        except UserProfile.DoesNotExist:
            return '—'
    _name.short_description = 'Name'

    @admin.action(description='✔️ Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')

    @admin.action(description='❌ Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')

    @admin.action(description='🛡️ Grant staff status')
    def make_staff(self, request, queryset):
        updated = queryset.update(is_staff=True)
        self.message_user(request, f'{updated} user(s) granted staff status.')

    @admin.action(description='🚫 Remove staff status')
    def remove_staff(self, request, queryset):
        updated = queryset.exclude(pk=request.user.pk).update(is_staff=False)
        self.message_user(request, f'{updated} user(s) had staff status removed.')


class UserProfileAdmin(admin.ModelAdmin):
    list_display       = ('_avatar', '_name', '_email', '_badge', 'location', '_rating', '_listings', 'created_at')
    list_display_links = ('_avatar', '_name')
    list_filter        = ('badge',)
    search_fields      = ('user__email', 'first_name', 'last_name', 'location')
    ordering           = ('-created_at',)
    readonly_fields    = ('user', 'created_at', '_rating', '_listings', '_avatar_preview')
    list_per_page      = 25
    actions            = ['set_badge_verified', 'set_badge_trusted', 'set_badge_top_seller',
                          'set_badge_dealer', 'set_badge_member', 'remove_badge']
    fieldsets = (
        ('Identity', {
            'fields': ('user', 'first_name', 'last_name', 'phone', '_avatar_preview', 'avatar', 'location', 'bio'),
        }),
        ('Trust & Badge', {
            'fields': ('badge',),
            'description': 'Assign a trust level that is visible on seller profiles and listings.',
        }),
        ('Metrics', {
            'fields': ('_rating', '_listings', 'created_at'),
        }),
    )

    def _avatar(self, obj):
        try:
            if obj.avatar and obj.avatar.name:
                return format_html(
                    '<img src="{}" style="width:32px;height:32px;border-radius:50%;'
                    'object-fit:cover;border:2px solid #e5e7eb;" />',
                    obj.avatar.url,
                )
        except Exception:
            pass
        return format_html(
            '<div style="width:32px;height:32px;border-radius:50%;background:#2563eb;color:#fff;'
            'display:inline-flex;align-items:center;justify-content:center;'
            'font-size:11px;font-weight:700;">{}</div>',
            obj.get_initials(),
        )
    _avatar.short_description = ''

    def _avatar_preview(self, obj):
        """Read-only avatar preview shown in the change form."""
        try:
            if obj.avatar and obj.avatar.name:
                return format_html(
                    '<img src="{}" style="width:80px;height:80px;border-radius:50%;'
                    'object-fit:cover;border:2px solid #e5e7eb;margin-bottom:6px;" /><br>'
                    '<small style="color:#6b7280;">Current avatar</small>',
                    obj.avatar.url,
                )
        except Exception:
            pass
        return format_html('<span style="color:#9ca3af;">No avatar uploaded</span>')
    _avatar_preview.short_description = 'Current Avatar'

    def _name(self, obj):
        return obj.get_display_name()
    _name.short_description = 'Name'

    def _email(self, obj):
        return obj.user.email
    _email.short_description = 'Email'
    _email.admin_order_field = 'user__email'

    def _badge(self, obj):
        if not obj.badge:
            return _dash()
        hex_col = _BADGE_HEX.get(obj.badge, '#6b7280')
        return _pill(obj.get_badge_display(), '#fff', hex_col)
    _badge.short_description = 'Badge'

    def _rating(self, obj):
        try:
            r = obj.average_rating()
            return f'{r} ★' if r is not None else '—'
        except Exception:
            return '—'
    _rating.short_description = 'Avg Rating'

    def _listings(self, obj):
        try:
            return obj.user.vehicles.filter(is_removed=False).count()
        except Exception:
            return 0
    _listings.short_description = 'Active Listings'

    @admin.action(description='🔵 Set badge → Verified')
    def set_badge_verified(self, request, queryset):
        queryset.update(badge=UserProfile.BADGE_VERIFIED)
        self.message_user(request, f'{queryset.count()} profile(s) set to Verified.')

    @admin.action(description='🟢 Set badge → Trusted')
    def set_badge_trusted(self, request, queryset):
        queryset.update(badge=UserProfile.BADGE_TRUSTED)
        self.message_user(request, f'{queryset.count()} profile(s) set to Trusted.')

    @admin.action(description='🟡 Set badge → Top Seller')
    def set_badge_top_seller(self, request, queryset):
        queryset.update(badge=UserProfile.BADGE_TOP_SELLER)
        self.message_user(request, f'{queryset.count()} profile(s) set to Top Seller.')

    @admin.action(description='🔷 Set badge → Dealer')
    def set_badge_dealer(self, request, queryset):
        queryset.update(badge=UserProfile.BADGE_DEALER)
        self.message_user(request, f'{queryset.count()} profile(s) set to Dealer.')

    @admin.action(description='⚫ Set badge → Member')
    def set_badge_member(self, request, queryset):
        queryset.update(badge=UserProfile.BADGE_MEMBER)
        self.message_user(request, f'{queryset.count()} profile(s) set to Member.')

    @admin.action(description='🚫 Remove badge')
    def remove_badge(self, request, queryset):
        queryset.update(badge='')
        self.message_user(request, f'{queryset.count()} badge(s) removed.')


# ── Vehicle ────────────────────────────────────────────────────────────────────

class VehicleAdmin(admin.ModelAdmin):
    list_display       = ('_thumb', 'title', 'variant', '_price', 'year', 'fuel',
                          'transmission', '_badge', '_owner', 'is_removed', 'created_at')
    list_display_links = ('_thumb', 'title')
    list_filter        = ('fuel', 'transmission', 'is_removed', 'year')
    search_fields      = ('title', 'variant', 'owner__email', 'location')
    ordering           = ('-created_at',)
    date_hierarchy     = 'created_at'
    readonly_fields    = ('created_at', '_thumb')
    list_per_page      = 20
    actions            = ['mark_removed', 'mark_available', 'export_csv']
    fieldsets          = (
        ('Listing', {
            'fields': ('owner', 'title', 'variant', 'price', 'year', 'mileage',
                       'fuel', 'transmission', 'location', 'description'),
        }),
        ('Media', {
            'fields': ('_thumb', 'image_file', 'image'),
        }),
        ('Status & Badge', {
            'fields': ('badge', 'badge_color', 'is_removed'),
        }),
        ('Meta', {
            'fields': ('created_at',),
        }),
    )

    def _thumb(self, obj):
        url = obj.get_image()
        if url:
            return format_html(
                '<img src="{}" style="width:56px;height:40px;object-fit:cover;'
                'border-radius:4px;border:1px solid #e5e7eb;" />',
                url,
            )
        return format_html(
            '<div style="width:56px;height:40px;background:#f3f4f6;border-radius:4px;'
            'border:1px solid #e5e7eb;display:inline-flex;align-items:center;'
            'justify-content:center;color:#9ca3af;font-size:18px;">&#128663;</div>'
        )
    _thumb.short_description = ''

    def _price(self, obj):
        # price is a CharField and may already include the £ symbol
        price = str(obj.price or '')
        display = price if price.startswith('£') else f'£{price}'
        return format_html('<span style="font-weight:600;color:#111827;">{}</span>', display)
    _price.short_description = 'Price'
    _price.admin_order_field = 'price'

    def _badge(self, obj):
        if not obj.badge:
            return _dash()
        color = obj.badge_color or '#374151'
        return _pill(obj.badge, '#fff', color)
    _badge.short_description = 'Condition'

    def _owner(self, obj):
        if not obj.owner:
            return _dash()
        return format_html(
            '<span style="color:#2563eb;">{}</span>',
            obj.owner.email,
        )
    _owner.short_description = 'Owner'
    _owner.admin_order_field = 'owner__email'

    @admin.action(description='Mark selected listings as removed')
    def mark_removed(self, request, queryset):
        updated = queryset.update(is_removed=True)
        self.message_user(request, f'{updated} listing(s) marked as removed.')

    @admin.action(description='Mark selected listings as available')
    def mark_available(self, request, queryset):
        updated = queryset.update(is_removed=False)
        self.message_user(request, f'{updated} listing(s) marked as available.')

    @admin.action(description='📥 Export selected listings to CSV')
    def export_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="vehicles.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Title', 'Variant', 'Price', 'Year', 'Fuel',
                         'Transmission', 'Mileage', 'Location', 'Owner Email',
                         'Is Removed', 'Created At'])
        for v in queryset.select_related('owner'):
            writer.writerow([
                v.pk, v.title, v.variant, v.price, v.year, v.fuel,
                v.transmission, v.mileage, v.location,
                v.owner.email if v.owner else '',
                v.is_removed,
                v.created_at.strftime('%Y-%m-%d %H:%M'),
            ])
        return response


# ── SavedVehicle ───────────────────────────────────────────────────────────────

class SavedVehicleAdmin(admin.ModelAdmin):
    list_display  = ('user', '_vehicle', 'saved_at')
    list_filter   = ('saved_at',)
    search_fields = ('user__email', 'vehicle__title')
    ordering      = ('-saved_at',)
    date_hierarchy = 'saved_at'
    list_per_page  = 25

    def _vehicle(self, obj):
        return str(obj.vehicle)
    _vehicle.short_description = 'Vehicle'
    _vehicle.admin_order_field = 'vehicle__title'


# ── Bid ────────────────────────────────────────────────────────────────────────

class BidAdmin(admin.ModelAdmin):
    list_display    = ('bidder', '_vehicle', '_amount', '_counter', '_status', 'created_at')
    list_filter     = ('status',)
    search_fields   = ('bidder__email', 'vehicle__title')
    ordering        = ('-created_at',)
    date_hierarchy  = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    list_per_page   = 25
    actions         = ['accept_bids', 'decline_bids']
    fieldsets       = (
        ('Bid Details', {
            'fields': ('vehicle', 'bidder', 'amount', 'counter_amount', 'status', 'note'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    def _vehicle(self, obj):
        return str(obj.vehicle.title)
    _vehicle.short_description = 'Vehicle'
    _vehicle.admin_order_field = 'vehicle__title'

    def _amount(self, obj):
        return format_html('<span style="font-weight:600;">£{}</span>', obj.amount)
    _amount.short_description = 'Bid Amount'
    _amount.admin_order_field = 'amount'

    def _counter(self, obj):
        if not obj.counter_amount:
            return _dash()
        return format_html('<span style="color:#6b7280;">£{}</span>', obj.counter_amount)
    _counter.short_description = 'Counter'

    def _status(self, obj):
        fg, bg = _STATUS_HEX.get(obj.status, ('#374151', '#f3f4f6'))
        return _pill(obj.get_status_display(), fg, bg)
    _status.short_description = 'Status'

    @admin.action(description='Accept selected bids')
    def accept_bids(self, request, queryset):
        updated = queryset.update(status=Bid.STATUS_ACCEPTED)
        self.message_user(request, f'{updated} bid(s) accepted.')

    @admin.action(description='Decline selected bids')
    def decline_bids(self, request, queryset):
        updated = queryset.update(status=Bid.STATUS_DECLINED)
        self.message_user(request, f'{updated} bid(s) declined.')


# ── Notification ───────────────────────────────────────────────────────────────

class NotificationAdmin(admin.ModelAdmin):
    list_display    = ('user', 'title', '_type_pill', '_read_pill', 'created_at')
    list_filter     = ('notif_type', 'is_read')
    search_fields   = ('user__email', 'title', 'message')
    ordering        = ('-created_at',)
    date_hierarchy  = 'created_at'
    readonly_fields = ('created_at',)
    list_per_page   = 25
    actions         = ['mark_read', 'mark_unread']
    fieldsets       = (
        ('Notification', {
            'fields': ('user', 'title', 'message', 'notif_type', 'url'),
        }),
        ('Status', {
            'fields': ('is_read', 'created_at'),
        }),
    )

    def _type_pill(self, obj):
        fg, bg = _NOTIF_HEX.get(obj.notif_type, ('#374151', '#f3f4f6'))
        return _pill(obj.get_notif_type_display(), fg, bg)
    _type_pill.short_description = 'Type'

    def _read_pill(self, obj):
        if obj.is_read:
            return _pill('Read', '#16a34a', '#dcfce7')
        return _pill('Unread', '#dc2626', '#fee2e2')
    _read_pill.short_description = 'Status'

    @admin.action(description='Mark selected notifications as read')
    def mark_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} notification(s) marked as read.')

    @admin.action(description='Mark selected notifications as unread')
    def mark_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} notification(s) marked as unread.')


# ── Review ─────────────────────────────────────────────────────────────────────

class ReviewAdmin(admin.ModelAdmin):
    list_display    = ('reviewer', 'reviewed_user', '_stars', '_comment', 'created_at')
    list_filter     = ('rating',)
    search_fields   = ('reviewer__email', 'reviewed_user__email', 'comment')
    ordering        = ('-created_at',)
    date_hierarchy  = 'created_at'
    readonly_fields = ('created_at',)
    list_per_page   = 25
    fieldsets       = (
        ('Review', {
            'fields': ('reviewer', 'reviewed_user', 'rating', 'comment'),
        }),
        ('Meta', {
            'fields': ('created_at',),
        }),
    )

    def _stars(self, obj):
        filled = '★' * obj.rating
        empty  = '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color:#d97706;font-size:14px;">{}</span>'
            '<span style="color:#d1d5db;font-size:14px;">{}</span>',
            filled, empty,
        )
    _stars.short_description = 'Rating'
    _stars.admin_order_field = 'rating'

    def _comment(self, obj):
        text = obj.comment or ''
        if len(text) > 70:
            text = text[:67] + '…'
        return text if text else _dash()
    _comment.short_description = 'Comment'


# ── LoginEvent ─────────────────────────────────────────────────────────────────

class LoginEventAdmin(admin.ModelAdmin):
    list_display    = ('user', '_masked_ip', '_location', 'isp', '_confirmed', 'created_at')
    list_filter     = ('is_confirmed', 'country')
    search_fields   = ('user__email', 'city', 'country')
    ordering        = ('-created_at',)
    date_hierarchy  = 'created_at'
    list_per_page   = 25
    readonly_fields = (
        'user', '_masked_ip', 'user_agent', 'city', 'region', 'country',
        'country_code', 'isp', 'lat', 'lon', 'is_confirmed', 'created_at',
    )
    fieldsets = (
        ('Session', {
            'fields': ('user', '_masked_ip', 'user_agent', 'created_at'),
        }),
        ('Location', {
            'fields': ('city', 'region', 'country', 'country_code', 'isp', 'lat', 'lon'),
        }),
        ('Verification', {
            'fields': ('is_confirmed',),
        }),
    )

    def _masked_ip(self, obj):
        """Show only the first two octets of the IP — e.g. 192.168.x.x"""
        ip = obj.ip_address or ''
        parts = ip.split('.')
        if len(parts) == 4:
            masked = f'{parts[0]}.{parts[1]}.x.x'
        elif ':' in ip:  # IPv6 — show first two groups only
            groups = ip.split(':')
            masked = ':'.join(groups[:2]) + ':x:x:x:x:x:x'
        else:
            masked = '*.*.x.x'
        return format_html(
            '<span style="font-family:monospace;color:#6b7280;">{}</span>',
            masked,
        )
    _masked_ip.short_description = 'IP Address'

    def _location(self, obj):
        return obj.location_string()
    _location.short_description = 'Location'

    def _confirmed(self, obj):
        if obj.is_confirmed:
            return _pill('Confirmed', '#16a34a', '#dcfce7')
        return _pill('Unconfirmed', '#dc2626', '#fee2e2')
    _confirmed.short_description = 'Verified'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── Register all models with the custom site ───────────────────────────────────

admin_site.register(User,         UserAdmin)
admin_site.register(UserProfile,  UserProfileAdmin)
admin_site.register(Vehicle,      VehicleAdmin)
admin_site.register(SavedVehicle, SavedVehicleAdmin)
admin_site.register(Bid,          BidAdmin)
admin_site.register(Notification, NotificationAdmin)
admin_site.register(Review,       ReviewAdmin)
admin_site.register(LoginEvent,   LoginEventAdmin)

