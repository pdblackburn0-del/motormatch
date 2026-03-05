from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    # Maps badge value → (label, Bootstrap bg class, hex colour)
    BADGE_META = {
        BADGE_MEMBER:     ('Member',     'bg-secondary',           '#6b7280'),
        BADGE_VERIFIED:   ('Verified',   'bg-primary',             '#2563eb'),
        BADGE_TRUSTED:    ('Trusted',    'bg-success',             '#16a34a'),
        BADGE_TOP_SELLER: ('Top Seller', 'bg-warning text-dark',   '#d97706'),
        BADGE_DEALER:     ('Dealer',     'bg-info text-dark',      '#0891b2'),
        BADGE_STAFF:      ('Staff',      'bg-danger',              '#dc2626'),
    }

    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name  = models.CharField(max_length=100, blank=True)
    phone      = models.CharField(max_length=30, blank=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio        = models.TextField(blank=True)
    location   = models.CharField(max_length=100, blank=True)
    badge      = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    def get_badge_info(self):
        """Returns (label, bg_class, hex) or None if no badge."""
        return self.BADGE_META.get(self.badge) if self.badge else None

    def get_display_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.user.email.split('@')[0]

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        if self.first_name:
            return self.first_name[:2].upper()
        return self.user.email[:2].upper()

    def average_rating(self):
        reviews = self.user.reviews_received.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def review_count(self):
        return self.user.reviews_received.count()

    def __str__(self):
        return f"Profile: {self.user.email}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


class Vehicle(models.Model):
    owner        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    title        = models.CharField(max_length=200)
    variant      = models.CharField(max_length=200)
    price        = models.CharField(max_length=50)
    mileage      = models.CharField(max_length=50)
    year         = models.CharField(max_length=4, blank=True, null=True)
    fuel         = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50, blank=True, null=True)
    badge        = models.CharField(max_length=50, blank=True, null=True)
    badge_color  = models.CharField(max_length=20, blank=True, null=True)
    image        = models.URLField(max_length=500, blank=True, null=True)
    image_file   = models.ImageField(upload_to='car_images/', blank=True, null=True)
    location     = models.CharField(max_length=100, blank=True)
    description  = models.TextField(blank=True)
    is_removed   = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    _BADGE_CLASS_MAP = {
        '#16a34a': 'badge-green',
        '#dc2626': 'badge-red',
    }

    def get_badge_class(self):
        return self._BADGE_CLASS_MAP.get((self.badge_color or '').lower(), 'badge-default')

    def get_image(self):
        if self.image_file and self.image_file.name:
            return self.image_file.url
        return self.image or ''

    def __str__(self):
        return f"{self.title} - {self.variant}"


class SavedVehicle(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_vehicles')
    vehicle  = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'vehicle')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.email} → {self.vehicle.title}"


class Notification(models.Model):
    TYPE_INFO    = 'info'
    TYPE_SUCCESS = 'success'
    TYPE_WARNING = 'warning'
    TYPE_CHOICES = [
        (TYPE_INFO,    'Info'),
        (TYPE_SUCCESS, 'Success'),
        (TYPE_WARNING, 'Warning'),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title      = models.CharField(max_length=200)
    message    = models.TextField(blank=True)
    notif_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_INFO)
    is_read    = models.BooleanField(default=False)
    url        = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.user.email}] {self.title}"


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
        ordering = ['-created_at']

    def location_string(self):
        parts = [p for p in (self.city, self.region, self.country) if p]
        return ', '.join(parts) if parts else 'Unknown location'

    def is_local(self):
        return self.ip_address in ('127.0.0.1', '::1', 'localhost')

    def __str__(self):
        return f"{self.user.email} from {self.ip_address} at {self.created_at}"


class Review(models.Model):
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received', null=True)
    reviewer      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    rating        = models.PositiveSmallIntegerField(default=5)
    comment       = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('reviewed_user', 'reviewer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer} → {self.reviewed_user} ({self.rating}★)"


class Message(models.Model):
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    vehicle    = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject    = models.CharField(max_length=200, blank=True)
    body       = models.TextField(blank=True)
    attachment = models.ImageField(upload_to='message_attachments/', blank=True, null=True)
    gif_url    = models.CharField(max_length=500, blank=True)  # Tenor GIF direct URL
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.email} → {self.recipient.email}: {self.subject}"


class Bid(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_ACCEPTED  = 'accepted'
    STATUS_DECLINED  = 'declined'
    STATUS_COUNTERED = 'countered'
    STATUS_CHOICES   = [
        (STATUS_PENDING,   'Pending'),
        (STATUS_ACCEPTED,  'Accepted'),
        (STATUS_DECLINED,  'Declined'),
        (STATUS_COUNTERED, 'Countered'),
    ]

    vehicle        = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bids')
    bidder         = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids_placed')
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    counter_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note           = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bidder.email} bid £{self.amount} on {self.vehicle.title}"


def _fetch_geo(ip):
    try:
        import requests as _req
        r = _req.get(f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country,countryCode,isp,lat,lon', timeout=2)
        if r.ok:
            d = r.json()
            if d.get('status') == 'success':
                return d
    except Exception:
        pass
    return {}


@receiver(user_logged_in)
def record_login_event(sender, request, user, **kwargs):
    ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip()
    ua = request.META.get('HTTP_USER_AGENT', '')

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

    if geo:
        location_hint = event.location_string()
    else:
        location_hint = 'local network' if event.is_local() else ip

    Notification.objects.create(
        user=user,
        title='New login detected',
        message=f'Your account was accessed from {location_hint}.',
        notif_type=Notification.TYPE_INFO,
        url=f'/security/login/{event.pk}/',
    )


@receiver(post_save, sender=SavedVehicle)
def notify_vehicle_saved(sender, instance, created, **kwargs):
    if created and instance.vehicle.owner and instance.vehicle.owner != instance.user:
        saver_name = instance.user.profile.get_display_name() if hasattr(instance.user, 'profile') else instance.user.email.split('@')[0]
        Notification.objects.create(
            user=instance.vehicle.owner,
            title='Someone saved your listing',
            message=f'{saver_name} saved your listing: {instance.vehicle.title}.',
            notif_type=Notification.TYPE_SUCCESS,
            url=f'/vehicle/{instance.vehicle.pk}/',
        )
