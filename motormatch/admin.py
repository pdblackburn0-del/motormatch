import csv

import json

from datetime import timedelta

from django import forms

from django.contrib import admin

from django.contrib.admin import AdminSite

from django.contrib.admin.models import LogEntry

from django.contrib.auth import get_user_model

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from django.contrib.sessions.models import Session

from django.db.models import Avg, Count, Q

from django.db.models.functions import TruncDate

from django.http import HttpResponse, HttpResponseForbidden, JsonResponse

from django.urls import path

from django.utils import timezone

from django.utils.html import format_html

from django.views.decorators.csrf import csrf_exempt

from django.views.decorators.http import require_POST

try:

    from cloudinary.forms import CloudinaryFileField

    _CLOUDINARY_AVAILABLE = True

except ImportError:

    _CLOUDINARY_AVAILABLE = False

from motormatch.models import (

    AdminNote, BannedKeyword, Bid, LoginEvent, Message, Notification, Review,

    SavedVehicle, UserProfile, Vehicle, VehicleImage,

)

User = get_user_model()


def _flush_user_sessions(user_pks):
    """Delete all DB sessions for the given user PKs for instant logout on ban."""
    str_pks = {str(pk) for pk in user_pks}
    for session in Session.objects.all():
        if session.get_decoded().get('_auth_user_id') in str_pks:
            session.delete()


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

class MotorMatchAdminSite(AdminSite):

    site_header = 'Motor Match'

    site_title  = 'Motor Match Admin'

    index_title = 'Overview'

    def index(self, request, extra_context=None):

        extra_context = extra_context or {}

        try:

            now      = timezone.now()

            today    = now.date()

            week_ago = now - timedelta(days=7)

            day30    = today - timedelta(days=29)

            extra_context.update({

                'stat_users':             User.objects.count(),

                'stat_vehicles':          Vehicle.objects.filter(is_removed=False).count(),

                'stat_bids':              Bid.objects.filter(status=Bid.STATUS_PENDING).count(),

                'stat_messages':          Message.objects.filter(is_read=False).count(),

                'stat_reviews':           Review.objects.count(),

                'stat_saved':             SavedVehicle.objects.count(),

                'stat_notifications':     Notification.objects.filter(is_read=False).count(),

                'stat_removed':           Vehicle.objects.filter(is_removed=True).count(),

                'stat_new_users_today':   User.objects.filter(date_joined__date=today).count(),

                'stat_bids_accepted':     Bid.objects.filter(status=Bid.STATUS_ACCEPTED).count(),

                'stat_logins_week':       LoginEvent.objects.filter(created_at__gte=week_ago).count(),

                'stat_active_staff':      User.objects.filter(is_staff=True, is_active=True).count(),

                'stat_flagged_msgs':      Message.objects.filter(is_flagged=True).count(),

                'stat_pending_listings':  Vehicle.objects.filter(approval_status=Vehicle.APPROVAL_PENDING).count(),

                'stat_suspended_users':   UserProfile.objects.filter(is_suspended=True).count(),

                'stat_admin_notes':       AdminNote.objects.count(),

                'stat_low_reviews':       Review.objects.filter(rating__lte=2).count(),

                'stat_bid_success_rate':  (

                    round(

                        Bid.objects.filter(status=Bid.STATUS_ACCEPTED).count() /

                        max(Bid.objects.count(), 1) * 100, 1

                    )

                ),

            })

            extra_context.update({

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

                'recent_reviews':  (Review.objects

                                    .select_related('reviewer', 'reviewed_user')

                                    .order_by('-created_at')[:4]),

                'pending_listings': (Vehicle.objects

                                     .filter(approval_status=Vehicle.APPROVAL_PENDING)

                                     .select_related('owner')

                                     .order_by('-created_at')[:6]),

                'suspended_users': (UserProfile.objects

                                    .filter(is_suspended=True)

                                    .select_related('user')

                                    .order_by('-created_at')[:6]),

                'low_reviews': (Review.objects

                                .filter(rating__lte=2)

                                .select_related('reviewer', 'reviewed_user')

                                .order_by('-created_at')[:5]),

            })

            extra_context['admin_log'] = (

                LogEntry.objects

                .select_related('user', 'content_type')

                .order_by('-action_time')[:12]

            )

            extra_context['flagged_messages'] = (

                Message.objects

                .filter(Q(is_flagged=True) | Q(is_deleted=True))

                .select_related('sender', 'recipient')

                .order_by('-created_at')[:8]

            )

            days30  = [today - timedelta(days=i) for i in range(29, -1, -1)]

            labels  = [d.strftime('%-d %b') for d in days30]

            def _daily(qs, date_field):

                rows = (qs.filter(**{f'{date_field}__date__gte': day30})

                          .annotate(_day=TruncDate(date_field))

                          .values('_day')

                          .annotate(c=Count('id')))

                m = {r['_day']: r['c'] for r in rows}

                return [m.get(d, 0) for d in days30]

            extra_context.update({

                'chart_labels':   json.dumps(labels),

                'chart_users':    json.dumps(_daily(User.objects, 'date_joined')),

                'chart_vehicles': json.dumps(_daily(Vehicle.objects, 'created_at')),

                'chart_bids':     json.dumps(_daily(Bid.objects, 'created_at')),

            })

        except Exception:

            pass

        return super().index(request, extra_context=extra_context)

    def get_app_list(self, request, app_label=None):

        """
        Return a custom-grouped sidebar instead of the default alphabetical
        app-per-section layout.  The auth app's User model is merged into the
        motormatch section so that /control-panel/auth/ is never linked.
        """

        app_list = super().get_app_list(request, app_label=app_label)

        model_map = {}

        for app in app_list:

            for model in app['models']:

                model_map[model['object_name']] = model

        _GROUPS = [

            ('Marketplace',   ['Vehicle', 'Bid', 'SavedVehicle']),

            ('Users',         ['User', 'UserProfile', 'LoginEvent']),

            ('Communication', ['Notification', 'Message']),

            ('Moderation',    ['Review', 'AdminNote', 'BannedKeyword', 'Message']),

        ]

        grouped_names = {n for _, names in _GROUPS for n in names}

        result = []

        for group_name, object_names in _GROUPS:

            models = [model_map[n] for n in object_names if n in model_map]

            if not models:

                continue

            result.append({

                'name':             group_name,

                'app_label':        group_name.lower(),

                'app_url':          '',

                'has_module_perms': True,

                'models':           models,

            })

        leftovers = [

            m for app in app_list

            for m in app['models']

            if m['object_name'] not in grouped_names

        ]

        if leftovers:

            result.append({

                'name':             'Other',

                'app_label':        'other',

                'app_url':          '',

                'has_module_perms': True,

                'models':           leftovers,

            })

        return result

    def app_index(self, request, app_label, extra_context=None):

        """Remove the standalone /control-panel/auth/ page — it's now merged."""

        if app_label == 'auth':

            from django.http import Http404

            raise Http404('No such admin section.')

        return super().app_index(request, app_label, extra_context)

    def get_urls(self):

        urls = super().get_urls()

        custom = [

            path('quick-moderate/', self.admin_view(self.quick_moderate_ajax),

                 name='quick_moderate'),

        ]

        return custom + urls

    def quick_moderate_ajax(self, request):

        """
        AJAX endpoint for the dashboard moderation panel quick-action buttons.
        POST params: message_id (int), action (str: ban | suspend_30d | dismiss | delete_msg)
        """

        if request.method != 'POST':

            return JsonResponse({'error': 'POST required'}, status=405)

        if not request.user.is_staff:

            return HttpResponseForbidden()

        action     = request.POST.get('action')

        message_id = request.POST.get('message_id')

        try:

            msg = Message.objects.select_related('sender').get(pk=message_id)

        except Message.DoesNotExist:

            return JsonResponse({'error': 'Message not found'}, status=404)

        sender = msg.sender

        if action == 'dismiss':

            msg.is_flagged  = False

            msg.flag_reason = ''

            msg.save(update_fields=['is_flagged', 'flag_reason'])

            return JsonResponse({'ok': True, 'action': 'dismiss'})

        if action == 'delete_msg':

            msg.is_flagged       = True

            msg.is_deleted       = True

            msg.deleted_by_staff = True

            msg.deleted_at       = timezone.now()

            msg.save(update_fields=['is_flagged', 'is_deleted', 'deleted_by_staff', 'deleted_at'])

            return JsonResponse({'ok': True, 'action': 'delete_msg'})

        profile, _ = UserProfile.objects.get_or_create(user=sender)

        if action == 'suspend_30d':

            profile.is_suspended     = True

            profile.suspension_until = timezone.now() + timedelta(days=30)

            profile.ban_reason       = 'Suspended via message moderation'

            profile.save(update_fields=['is_suspended', 'suspension_until', 'ban_reason'])

            sender.is_active = False

            sender.save(update_fields=['is_active'])

            _flush_user_sessions([sender.pk])

            return JsonResponse({'ok': True, 'action': 'suspend_30d',

                                 'user': sender.email})

        if action == 'ban':

            profile.is_suspended     = True

            profile.suspension_until = None

            profile.ban_reason       = 'Permanently banned via message moderation'

            profile.save(update_fields=['is_suspended', 'suspension_until', 'ban_reason'])

            sender.is_active = False

            sender.save(update_fields=['is_active'])

            _flush_user_sessions([sender.pk])

            return JsonResponse({'ok': True, 'action': 'ban', 'user': sender.email})

        return JsonResponse({'error': f'Unknown action: {action}'}, status=400)

admin_site = MotorMatchAdminSite(name='motormatch_admin')

def _pill(label, fg, bg):

    return format_html(

        '<span style="background:{};color:{};padding:2px 10px;border-radius:99px;'

        'font-size:11px;font-weight:600;white-space:nowrap;">{}</span>',

        bg, fg, label,

    )

def _dash():

    return format_html('<span style="color:#9ca3af;">—</span>')

class UserAdminNoteInline(admin.TabularInline):

    model               = AdminNote

    fk_name             = 'user'

    extra               = 1

    fields              = ('note', 'author', 'created_at')

    readonly_fields     = ('author', 'created_at')

    verbose_name        = 'Admin Note'

    verbose_name_plural = 'Admin Notes'

    can_delete          = True

    def has_add_permission(self, request, obj=None):

        return request.user.is_staff

    def save_formset(self, request, form, formset, change):

        instances = formset.save(commit=False)

        for instance in instances:

            if not instance.pk:

                instance.author = request.user

            instance.save()

        formset.save_m2m()

class VehicleImageInlineAdmin(admin.TabularInline):

    model   = VehicleImage
    extra   = 0
    fields  = ('image_file', 'order')
    ordering = ('order',)
    verbose_name        = 'Extra Photo'
    verbose_name_plural = 'Extra Photos'


class VehicleAdminNoteInline(admin.TabularInline):

    model               = AdminNote

    fk_name             = 'vehicle'

    extra               = 1

    fields              = ('note', 'author', 'created_at')

    readonly_fields     = ('author', 'created_at')

    verbose_name        = 'Admin Note'

    verbose_name_plural = 'Admin Notes'

    can_delete          = True

    def has_add_permission(self, request, obj=None):

        return request.user.is_staff

    def save_formset(self, request, form, formset, change):

        instances = formset.save(commit=False)

        for instance in instances:

            if not instance.pk:

                instance.author = request.user

            instance.save()

        formset.save_m2m()

class UserProfileInline(admin.StackedInline):

    model               = UserProfile

    can_delete          = False

    verbose_name_plural = 'Profile'

    extra               = 0

    fields              = ('first_name', 'last_name', 'phone', 'location', 'bio', 'badge')

class UserAdmin(BaseUserAdmin):

    inlines       = [UserProfileInline, UserAdminNoteInline]

    list_display  = ('email', '_name', '_trust', 'is_staff', 'is_active', 'date_joined')

    list_filter   = ('is_staff', 'is_superuser', 'is_active')

    search_fields = ('email', 'profile__first_name', 'profile__last_name')

    ordering      = ('-date_joined',)

    list_per_page = 25

    actions       = ['activate_users', 'deactivate_users', 'make_staff', 'remove_staff',

                     'ban_users_permanently']

    def _name(self, obj):

        try:

            return obj.profile.get_display_name()

        except UserProfile.DoesNotExist:

            return '—'

    _name.short_description = 'Name'

    def _trust(self, obj):

        try:

            if obj.profile.is_suspended:

                return _pill('Suspended', '#dc2626', '#fee2e2')

            return _pill('Active', '#16a34a', '#dcfce7')

        except Exception:

            return _dash()

    _trust.short_description = 'Status'

    @admin.action(description='✔️ Activate selected users')

    def activate_users(self, request, queryset):

        updated = queryset.update(is_active=True)

        UserProfile.objects.filter(user__in=queryset).update(
            is_suspended=False, suspension_until=None, ban_reason=''
        )

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

    @admin.action(description='🔴 Permanently ban selected users')

    def ban_users_permanently(self, request, queryset):

        targets = queryset.exclude(pk=request.user.pk)

        count = targets.count()

        pks = list(targets.values_list('pk', flat=True))

        targets.update(is_active=False)

        UserProfile.objects.filter(user__in=targets).update(

            is_suspended=True, ban_reason='Permanently banned by admin.',

        )

        _flush_user_sessions(pks)

        self.message_user(request, f'{count} user(s) permanently banned.')

class UserProfileAdmin(admin.ModelAdmin):

    list_display       = ('_avatar', '_name', '_email', '_badge', '_trust_score',

                          '_suspended', 'location', '_rating', '_listings', 'created_at')

    list_display_links = ('_avatar', '_name')

    list_filter        = ('badge', 'is_suspended')

    search_fields      = ('user__email', 'first_name', 'last_name', 'location')

    ordering           = ('-created_at',)

    readonly_fields    = ('user', 'created_at', '_rating', '_listings', '_avatar_preview', '_trust_score')

    list_per_page      = 25

    actions            = ['set_badge_verified', 'set_badge_trusted', 'set_badge_top_seller',

                          'set_badge_dealer', 'set_badge_member', 'remove_badge',

                          'suspend_user', 'lift_suspension', 'send_warning']

    fieldsets = (

        ('Identity', {

            'fields': ('user', 'first_name', 'last_name', 'phone', '_avatar_preview', 'avatar', 'location', 'bio'),

        }),

        ('Trust & Badge', {

            'fields': ('badge',),

            'description': 'Assign a trust level that is visible on seller profiles and listings.',

        }),

        ('Moderation', {

            'fields': ('is_suspended', 'suspension_until', 'ban_reason'),

            'description': 'Suspend or ban this user from the marketplace.',

        }),

        ('Metrics', {

            'fields': ('_rating', '_listings', '_trust_score', 'created_at'),

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

    def _trust_score(self, obj):

        """
        Compute a simple trust score 0–100 based on:
          listings (+5 each, max 40), accepted bids (+4 each, max 20),
          rating average (+20 max), flagged messages (-15 each, min 0).
        """

        try:

            listings  = min(obj.user.vehicles.filter(is_removed=False).count() * 5, 40)

            accepted  = min(obj.user.bids_placed.filter(status=Bid.STATUS_ACCEPTED).count() * 4, 20)

            avg_r     = obj.average_rating() or 0

            rating_pts = int(avg_r / 5 * 20)

            flagged   = obj.user.sent_messages.filter(is_flagged=True).count() * 15

            suspended_pen = 30 if obj.is_suspended else 0

            score = max(min(listings + accepted + rating_pts - flagged - suspended_pen + 20, 100), 0)

            if score >= 70:

                fg, bg, label = '#16a34a', '#dcfce7', f'High ({score})'

            elif score >= 40:

                fg, bg, label = '#d97706', '#fef3c7', f'Medium ({score})'

            else:

                fg, bg, label = '#dc2626', '#fee2e2', f'Low ({score})'

            return _pill(label, fg, bg)

        except Exception:

            return _dash()

    _trust_score.short_description = 'Trust'

    def _suspended(self, obj):

        if obj.is_suspended:

            until = ''

            if obj.suspension_until:

                until = f' until {obj.suspension_until.strftime("%d %b %Y")}'

            return _pill(f'Suspended{until}', '#dc2626', '#fee2e2')

        return _pill('Active', '#16a34a', '#dcfce7')

    _suspended.short_description = 'Status'

    @admin.action(description='⛔ Suspend selected users (30 days)')

    def suspend_user(self, request, queryset):

        until = timezone.now() + timedelta(days=30)

        pks = list(queryset.exclude(user=request.user).values_list('user_id', flat=True))

        updated = queryset.exclude(user=request.user).update(

            is_suspended=True, suspension_until=until,

            ban_reason='Suspended by admin',

        )

        User.objects.filter(pk__in=pks).update(is_active=False)

        _flush_user_sessions(pks)

        self.message_user(request, f'{updated} user(s) suspended for 30 days.')

    @admin.action(description='✅ Lift suspension on selected users')

    def lift_suspension(self, request, queryset):

        pks = queryset.values_list('user_id', flat=True)

        updated = queryset.update(is_suspended=False, suspension_until=None, ban_reason='')

        User.objects.filter(pk__in=pks).update(is_active=True)

        self.message_user(request, f'{updated} suspension(s) lifted.')

    @admin.action(description='⚠️ Send warning notification to selected users')

    def send_warning(self, request, queryset):

        count = 0

        for profile in queryset:

            Notification.objects.create(

                user=profile.user,

                title='Warning from Motor Match Admin',

                message='Your account has received an admin warning. Please review our community guidelines.',

                notif_type=Notification.TYPE_WARNING,

                url='/dashboard/',

            )

            count += 1

        self.message_user(request, f'Warning notification sent to {count} user(s).')

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

class VehicleAdmin(admin.ModelAdmin):

    list_display       = ('_thumb', 'title', 'variant', '_price', 'year', 'fuel',

                          'transmission', '_badge', '_owner', '_approval', 'listing_status', 'is_removed', 'created_at')

    list_display_links = ('_thumb', 'title')

    list_filter        = ('fuel', 'transmission', 'listing_status', 'is_removed', 'year', 'approval_status')

    search_fields      = ('title', 'variant', 'owner__email', 'location')

    ordering           = ('-created_at',)

    date_hierarchy     = 'created_at'

    readonly_fields    = ('created_at', '_thumb')

    list_per_page      = 20

    inlines            = [VehicleAdminNoteInline, VehicleImageInlineAdmin]

    actions            = ['mark_removed', 'mark_available', 'approve_listings',

                          'reject_listings', 'export_csv', 'mark_sold']

    fieldsets          = (

        ('Listing', {

            'fields': ('owner', 'title', 'variant', 'price', 'year', 'mileage',

                       'fuel', 'transmission', 'location', 'description'),

        }),

        ('Media', {

            'fields': ('_thumb', 'image_file', 'image'),

        }),

        ('Status & Badge', {

            'fields': ('badge', 'badge_color', 'listing_status', 'is_removed'),

        }),

        ('Approval', {

            'fields': ('approval_status', 'approval_note'),

            'description': 'Review and approve or reject this listing before it becomes publicly visible.',

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

    _APPROVAL_HEX = {

        'pending':  ('#d97706', '#fef3c7'),

        'approved': ('#16a34a', '#dcfce7'),

        'rejected': ('#dc2626', '#fee2e2'),

    }

    def _approval(self, obj):

        fg, bg = self._APPROVAL_HEX.get(obj.approval_status, ('#374151', '#f3f4f6'))

        return _pill(obj.get_approval_status_display(), fg, bg)

    _approval.short_description = 'Approval'

    _approval.admin_order_field = 'approval_status'

    @admin.action(description='Mark selected listings as removed')

    def mark_removed(self, request, queryset):

        updated = queryset.update(is_removed=True, listing_status=Vehicle.STATUS_REMOVED)

        self.message_user(request, f'{updated} listing(s) marked as removed.')

    @admin.action(description='Mark selected listings as available')

    def mark_available(self, request, queryset):

        updated = queryset.update(is_removed=False, listing_status=Vehicle.STATUS_ACTIVE)

        self.message_user(request, f'{updated} listing(s) marked as available.')

    @admin.action(description='✅ Approve selected listings')

    def approve_listings(self, request, queryset):

        updated = queryset.update(approval_status=Vehicle.APPROVAL_APPROVED)

        self.message_user(request, f'{updated} listing(s) approved.')

    @admin.action(description='❌ Reject selected listings')

    def reject_listings(self, request, queryset):

        updated = queryset.update(approval_status=Vehicle.APPROVAL_REJECTED, is_removed=True, listing_status=Vehicle.STATUS_REMOVED)

        self.message_user(request, f'{updated} listing(s) rejected and hidden.')

    @admin.action(description='💰 Mark selected listings as sold')

    def mark_sold(self, request, queryset):

        updated = queryset.update(listing_status=Vehicle.STATUS_SOLD)

        self.message_user(request, f'{updated} listing(s) marked as sold.')

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

        elif ':' in ip:

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

@admin.register(Message, site=admin_site)

class MessageModerationAdmin(admin.ModelAdmin):

    """Read-only moderation view — flagged and auto-deleted messages."""

    list_display   = ('_from', '_to', '_preview', '_flag_reason', '_status_col', 'created_at')

    list_filter    = ('is_flagged', 'is_deleted', 'deleted_by_staff', 'created_at')

    search_fields  = ('sender__email', 'recipient__email', 'body', 'subject')

    readonly_fields = (

        '_from', '_to', '_vehicle_link', '_body_full',

        'flag_reason', 'is_flagged', 'is_deleted', 'deleted_by_staff', 'deleted_at', 'created_at',

    )

    actions        = ['flag_messages', 'clear_flag', 'delete_messages_staff', 'restore_messages']

    ordering       = ('-created_at',)

    def has_add_permission(self, request):          return False

    def has_delete_permission(self, request, obj=None): return request.user.is_superuser

    def get_queryset(self, request):

        qs = super().get_queryset(request)

        if not request.user.is_superuser:

            return qs.filter(Q(is_flagged=True) | Q(is_deleted=True))

        return qs

    @admin.display(description='From')

    def _from(self, obj):

        e = obj.sender.email

        parts = e.split('@')

        return parts[0][:2] + '***@' + parts[1] if len(parts) == 2 else e[:4] + '***'

    @admin.display(description='To')

    def _to(self, obj):

        e = obj.recipient.email

        parts = e.split('@')

        return parts[0][:2] + '***@' + parts[1] if len(parts) == 2 else e[:4] + '***'

    @admin.display(description='Message preview')

    def _preview(self, obj):

        if obj.is_deleted:

            label = '✖ deleted by staff' if obj.deleted_by_staff else '✖ deleted'

            return format_html('<span style="color:#9ca3af;font-style:italic;">{}</span>', label)

        text = obj.body or obj.subject or '—'

        preview = text[:80] + '…' if len(text) > 80 else text

        color = '#dc2626' if obj.is_flagged else '#374151'

        return format_html('<span style="color:{};">{}</span>', color, preview)

    @admin.display(description='Flag reason')

    def _flag_reason(self, obj):

        if obj.flag_reason:

            bg = '#fce7f3' if 'deleted' in obj.flag_reason.lower() else '#fee2e2'

            return format_html(

                '<span style="background:{};color:#dc2626;padding:2px 8px;'

                'border-radius:99px;font-size:11px;font-weight:600;">{}</span>',

                bg, obj.flag_reason[:60],

            )

        return format_html('<span style="color:#9ca3af;">—</span>')

    @admin.display(description='Status')

    def _status_col(self, obj):

        if obj.is_deleted and obj.deleted_by_staff:

            return format_html('<span style="background:#fce7f3;color:#9d174d;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600;">Auto-deleted</span>')

        if obj.is_deleted:

            return format_html('<span style="background:#f3f4f6;color:#6b7280;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600;">Deleted</span>')

        if obj.is_flagged:

            return format_html('<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600;">Flagged</span>')

        return format_html('<span style="color:#9ca3af;">—</span>')

    @admin.display(description='Full message')

    def _body_full(self, obj):

        if obj.is_deleted:

            return format_html('<em style="color:#9ca3af;">Message deleted{}</em>',

                               ' by staff' if obj.deleted_by_staff else '')

        return format_html(

            '<div style="padding:12px;background:#fafafa;border:1px solid #e5e7eb;'

            'border-radius:6px;white-space:pre-wrap;font-size:13px;">{}</div>',

            obj.body or '(no body)',

        )

    @admin.display(description='Vehicle')

    def _vehicle_link(self, obj):

        if obj.vehicle:

            return format_html('<a href="{}">{}</a>',

                f'../vehicle/{obj.vehicle.pk}/change/', obj.vehicle.title)

        return '—'

    @admin.action(description='🚩 Manually flag selected messages')

    def flag_messages(self, request, queryset):

        updated = queryset.update(is_flagged=True, flag_reason='Manually flagged by admin')

        self.message_user(request, f'{updated} message(s) flagged.')

    @admin.action(description='✅ Clear flag on selected messages')

    def clear_flag(self, request, queryset):

        updated = queryset.update(is_flagged=False, flag_reason='')

        self.message_user(request, f'{updated} message(s) cleared.')

    @admin.action(description='🗑️ Delete selected messages (staff)')

    def delete_messages_staff(self, request, queryset):

        updated = queryset.update(

            is_deleted=True, deleted_by_staff=True,

            deleted_at=timezone.now(), is_flagged=True,

            flag_reason='Deleted by staff',

        )

        self.message_user(request, f'{updated} message(s) deleted by staff.')

    @admin.action(description='♻️ Restore deleted messages')

    def restore_messages(self, request, queryset):

        updated = queryset.update(is_deleted=False, deleted_by_staff=False, deleted_at=None)

        self.message_user(request, f'{updated} message(s) restored.')

    class Media:

        pass

class AdminNoteAdmin(admin.ModelAdmin):

    list_display    = ('__str__', 'author', '_target', 'created_at')

    list_filter     = ('created_at',)

    search_fields   = ('note', 'author__email', 'user__email', 'vehicle__title')

    ordering        = ('-created_at',)

    readonly_fields = ('author', 'created_at')

    list_per_page   = 30

    def _target(self, obj):

        if obj.user:

            return format_html('<span style="color:#2563eb;">User: {}</span>', obj.user.email)

        if obj.vehicle:

            return format_html('<span style="color:#16a34a;">Vehicle: {}</span>', obj.vehicle.title)

        return _dash()

    _target.short_description = 'Target'

    def save_model(self, request, obj, form, change):

        if not obj.pk:

            obj.author = request.user

        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):

        return request.user.is_superuser

class KeywordUploadForm(forms.Form):

    """Simple form for uploading a plain-text keyword file (one per line)."""

    keyword_file = forms.FileField(

        label='Keyword file (.txt, one word/phrase per line)',

        help_text='Lines starting with # are ignored. '

                  'Prefix a line with DELETE: to force auto-delete severity, '

                  'e.g.  DELETE:slur_word',

    )

    severity = forms.ChoiceField(

        choices=[('flag', 'Flag for review'), ('delete', 'Auto-delete message')],

        initial='flag',

    )

    category = forms.ChoiceField(choices=BannedKeyword.CATEGORY_CHOICES, initial='other')

class BannedKeywordAdmin(admin.ModelAdmin):

    list_display   = ('word', 'severity', 'category', 'is_active', 'added_by', 'created_at')

    list_filter    = ('severity', 'category', 'is_active')

    search_fields  = ('word',)

    list_editable  = ('is_active',)

    actions        = ['deactivate_keywords', 'activate_keywords']

    readonly_fields = ('added_by', 'created_at')

    def save_model(self, request, obj, form, change):

        if not obj.added_by_id:

            obj.added_by = request.user

        super().save_model(request, obj, form, change)

    def get_urls(self):

        urls = super().get_urls()

        custom = [

            path('upload-keywords/', self.admin_site.admin_view(self.upload_keywords_view),

                 name='motormatch_bannedkeyword_upload'),

        ]

        return custom + urls

    def upload_keywords_view(self, request):

        from django.contrib import messages as msg_fw

        from django.shortcuts import render, redirect

        if request.method == 'POST':

            form = KeywordUploadForm(request.POST, request.FILES)

            if form.is_valid():

                f        = form.cleaned_data['keyword_file']

                severity = form.cleaned_data['severity']

                category = form.cleaned_data['category']

                lines    = f.read().decode('utf-8', errors='replace').splitlines()

                added, skipped = 0, 0

                for line in lines:

                    line = line.strip()

                    if not line or line.startswith('#'):

                        continue

                    sev = severity

                    if line.upper().startswith('DELETE:'):

                        sev  = BannedKeyword.SEVERITY_DELETE

                        line = line[7:].strip()

                    word = line.lower()[:200]

                    _, created = BannedKeyword.objects.get_or_create(

                        word=word,

                        defaults={'severity': sev, 'category': category,

                                  'is_active': True, 'added_by': request.user},

                    )

                    if created:

                        added += 1

                    else:

                        skipped += 1

                msg_fw.success(request,

                    f'Uploaded: {added} new keyword(s) added, {skipped} already existed.')

                return redirect('../')

        else:

            form = KeywordUploadForm()

        context = dict(

            self.admin_site.each_context(request),

            form=form,

            title='Upload Keyword File',

            opts=self.model._meta,

        )

        return render(request, 'admin/motormatch/bannedkeyword/upload.html', context)

    def changelist_view(self, request, extra_context=None):

        extra_context = extra_context or {}

        extra_context['upload_url'] = 'upload-keywords/'

        return super().changelist_view(request, extra_context=extra_context)

    @admin.action(description='🚫 Deactivate selected keywords')

    def deactivate_keywords(self, request, queryset):

        queryset.update(is_active=False)

        self.message_user(request, f'{queryset.count()} keyword(s) deactivated.')

    @admin.action(description='✅ Activate selected keywords')

    def activate_keywords(self, request, queryset):

        queryset.update(is_active=True)

        self.message_user(request, f'{queryset.count()} keyword(s) activated.')

admin_site.register(User,          UserAdmin)

admin_site.register(UserProfile,   UserProfileAdmin)

admin_site.register(Vehicle,       VehicleAdmin)

admin_site.register(SavedVehicle,  SavedVehicleAdmin)

admin_site.register(Bid,           BidAdmin)

admin_site.register(Notification,  NotificationAdmin)

admin_site.register(Review,        ReviewAdmin)

admin_site.register(LoginEvent,    LoginEventAdmin)

admin_site.register(AdminNote,     AdminNoteAdmin)

admin_site.register(BannedKeyword, BannedKeywordAdmin)
