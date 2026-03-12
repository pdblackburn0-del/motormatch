from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in
from django.core.cache import cache
from django.db import models
from django.db.models import Avg
from django.db.models.signals import post_save
from django.dispatch import receiver

from cloudinary.models import CloudinaryField

from apps.notifications.models import Notification

User = get_user_model()


class UserProfile(models.Model):
    BADGE_NONE       = ''
    BADGE_MEMBER     = 'member'
    BADGE_VERIFIED   = 'verified'
    BADGE_TRUSTED    = 'trusted'
    BADGE_TOP_SELLER = 'top_seller'
    BADGE_DEALER     = 'dealer'
    BADGE_STAFF      = 'staff'

    BADGE_CHOICES = [
        (BADGE_NONE,       'None'),
        (BADGE_MEMBER,     'Member'),
        (BADGE_VERIFIED,   'Verified'),
        (BADGE_TRUSTED,    'Trusted'),
        (BADGE_TOP_SELLER, 'Top Seller'),
        (BADGE_DEALER,     'Dealer'),
        (BADGE_STAFF,      'Staff'),
    ]

    BADGE_META = {
        BADGE_MEMBER:     ('Member',     'bg-secondary',         '#6b7280'),
        BADGE_VERIFIED:   ('Verified',   'bg-primary',           '#2563eb'),
        BADGE_TRUSTED:    ('Trusted',    'bg-success',           '#16a34a'),
        BADGE_TOP_SELLER: ('Top Seller', 'bg-warning text-dark', '#d97706'),
        BADGE_DEALER:     ('Dealer',     'bg-info text-dark',    '#0891b2'),
        BADGE_STAFF:      ('Staff',      'bg-danger',            '#dc2626'),
    }

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name  = models.CharField(max_length=100, blank=True)
    phone      = models.CharField(max_length=30, blank=True)
    avatar     = CloudinaryField('avatar', folder='avatars', blank=True, null=True)
    bio        = models.TextField(blank=True)
    location   = models.CharField(max_length=100, blank=True)
    badge      = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    is_suspended     = models.BooleanField(default=False, db_index=True)
    suspension_until = models.DateTimeField(null=True, blank=True)
    ban_reason       = models.CharField(max_length=500, blank=True)

    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'motormatch'

    def get_badge_info(self):
        return self.BADGE_META.get(self.badge) if self.badge else None

    def get_display_name(self):
        full = f'{self.first_name} {self.last_name}'.strip()
        return full or self.user.email.split('@')[0]

    def get_initials(self):
        if self.first_name and self.last_name:
            return f'{self.first_name[0]}{self.last_name[0]}'.upper()
        if self.first_name:
            return self.first_name[:2].upper()
        return self.user.email[:2].upper()

    def average_rating(self):
        result = self.user.reviews_received.aggregate(avg=Avg('rating'))['avg']
        return round(result, 1) if result is not None else None

    def review_count(self):
        return self.user.reviews_received.count()

    def __str__(self):
        return f'Profile: {self.user.email}'


class Review(models.Model):
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', null=True)
    reviewer      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    rating        = models.PositiveSmallIntegerField(default=5)
    comment       = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label     = 'motormatch'
        unique_together = ('reviewed_user', 'reviewer')
        ordering      = ['-created_at']

    def __str__(self):
        return f'{self.reviewer} → {self.reviewed_user} ({self.rating}★)'


class LoginEvent(models.Model):
    user         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_events')
    ip_address   = models.CharField(max_length=45)
    user_agent   = models.TextField(blank=True)
    city         = models.CharField(max_length=100, blank=True)
    region       = models.CharField(max_length=100, blank=True)
    country      = models.CharField(max_length=100, blank=True)
    country_code = models.CharField(max_length=5, blank=True)
    isp          = models.CharField(max_length=200, blank=True)
    lat          = models.FloatField(null=True, blank=True)
    lon          = models.FloatField(null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'motormatch'
        ordering  = ['-created_at']

    def location_string(self):
        parts = [p for p in (self.city, self.region, self.country) if p]
        return ', '.join(parts) if parts else 'Unknown location'

    def is_local(self):
        return self.ip_address in ('127.0.0.1', '::1', 'localhost')

    def __str__(self):
        return f'{self.user.email} from {self.ip_address} at {self.created_at}'


def _fetch_geo(ip):
    cache_key = f'geo_{ip}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    try:
        import requests as _req
        r = _req.get(
            f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country,countryCode,isp,lat,lon',
            timeout=2,
        )
        if r.ok:
            d = r.json()
            if d.get('status') == 'success':
                cache.set(cache_key, d, timeout=86400 * 30)
                return d
    except Exception:
        pass
    cache.set(cache_key, {}, timeout=3600)
    return {}


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def record_login_event(sender, request, user, **kwargs):
    ip  = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    ua  = request.META.get('HTTP_USER_AGENT', '')
    geo = {} if ip in ('127.0.0.1', '::1', '') else _fetch_geo(ip)

    event = LoginEvent.objects.create(
        user=user,
        ip_address=ip or '127.0.0.1',
        user_agent=ua,
        city=geo.get('city', ''),
        region=geo.get('regionName', ''),
        country=geo.get('country', ''),
        country_code=geo.get('countryCode', ''),
        isp=geo.get('isp', ''),
        lat=geo.get('lat'),
        lon=geo.get('lon'),
    )

    location_hint = event.location_string() if geo else ('local network' if event.is_local() else ip)

    Notification.objects.create(
        user=user,
        title='New login detected',
        message=f'Your account was accessed from {location_hint}.',
        notif_type=Notification.TYPE_INFO,
        url=f'/security/login/{event.pk}/',
    )
