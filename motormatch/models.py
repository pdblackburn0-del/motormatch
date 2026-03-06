from django.contrib.auth.signals import user_logged_in

from django.core.cache import cache

from django.db import models

from django.contrib.auth import get_user_model

from django.db.models.signals import post_save

from django.dispatch import receiver

from django.utils import timezone

from cloudinary.models import CloudinaryField

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

    avatar     = CloudinaryField('avatar', folder='avatars', blank=True, null=True)

    bio        = models.TextField(blank=True)

    location   = models.CharField(max_length=100, blank=True)

    badge      = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    is_suspended     = models.BooleanField(default=False, db_index=True)

    suspension_until = models.DateTimeField(null=True, blank=True)

    ban_reason       = models.CharField(max_length=500, blank=True)

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

    APPROVAL_PENDING  = 'pending'

    APPROVAL_APPROVED = 'approved'

    APPROVAL_REJECTED = 'rejected'

    APPROVAL_CHOICES  = [

        (APPROVAL_PENDING,  'Pending Review'),

        (APPROVAL_APPROVED, 'Approved'),

        (APPROVAL_REJECTED, 'Rejected'),

    ]

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

    image_file   = CloudinaryField('image', folder='car_images', blank=True, null=True)

    location     = models.CharField(max_length=100, blank=True)

    description  = models.TextField(blank=True)

    is_removed   = models.BooleanField(default=False)

    approval_status = models.CharField(

        max_length=20, choices=APPROVAL_CHOICES,

        default=APPROVAL_APPROVED,

        db_index=True,

    )

    approval_note = models.CharField(max_length=500, blank=True)

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

_FLAG_KEYWORDS = [

    'hate', 'kill', 'murder', 'rape', 'terrorist', 'bomb',

    'nigger', 'nigga', 'faggot', 'chink', 'spic', 'kike',

    'retard', 'whore', 'cunt', 'slut',

]

class Message(models.Model):

    sender      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')

    recipient   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')

    vehicle     = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')

    subject     = models.CharField(max_length=200, blank=True)

    body        = models.TextField(blank=True)

    attachment  = CloudinaryField('attachment', folder='message_attachments', blank=True, null=True)

    gif_url     = models.CharField(max_length=500, blank=True)

    is_read          = models.BooleanField(default=False)

    is_flagged       = models.BooleanField(default=False, db_index=True)

    flag_reason      = models.CharField(max_length=500, blank=True)

    is_deleted       = models.BooleanField(default=False, db_index=True)

    deleted_by_staff = models.BooleanField(default=False)

    deleted_at       = models.DateTimeField(null=True, blank=True)

    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        return f"{self.sender.email} → {self.recipient.email}: {self.subject}"

    @property

    def display_body(self):

        """Return body text for display, respecting deletion by staff."""

        if self.is_deleted:

            return None

        return self.body

class MessageReaction(models.Model):

    ALLOWED = ['❤️', '😂', '👍', '😮', '😢', '😡']

    message    = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')

    emoji      = models.CharField(max_length=10)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        unique_together = ('message', 'user')

    def __str__(self):

        return f"{self.user_id} → {self.message_id}: {self.emoji}"

class AdminNote(models.Model):

    """Private notes that staff can attach to users or listings."""

    author  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,

                                related_name='admin_notes_written')

    user    = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,

                                related_name='admin_notes')

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True,

                                related_name='admin_notes')

    note    = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ['-created_at']

    def __str__(self):

        target = f'User:{self.user_id}' if self.user_id else f'Vehicle:{self.vehicle_id}'

        return f'Note by {self.author} on {target}'

class BannedKeyword(models.Model):

    """
    Database-driven keyword list for message moderation.
    'flag'   → message is flagged for admin review.
    'delete' → message is auto-deleted (e.g. slurs/hate speech); shows
               'Message deleted by staff' to both parties.
    Upload a .txt file (one word/phrase per line) via the admin Upload action.
    """

    SEVERITY_FLAG   = 'flag'

    SEVERITY_DELETE = 'delete'

    SEVERITY_CHOICES = [

        ('flag',   'Flag for review'),

        ('delete', 'Auto-delete (hate speech / slurs)'),

    ]

    CATEGORY_CHOICES = [

        ('hate',     'Hate Speech'),

        ('fraud',    'Fraud / Scam'),

        ('spam',     'Spam'),

        ('violence', 'Violence'),

        ('adult',    'Adult Content'),

        ('other',    'Other'),

    ]

    word      = models.CharField(max_length=200, unique=True, db_index=True)

    severity  = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_FLAG)

    category  = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    added_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,

                                  related_name='banned_keywords_added')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ['word']

    def __str__(self):

        return f"{self.word} ({self.severity})"

@receiver(post_save, sender=Message)

def auto_flag_message(sender, instance, created, **kwargs):

    """Automatically flag or delete messages containing banned keywords."""

    if not created:

        return

    text = f"{instance.subject} {instance.body}".lower()

    try:

        db_keywords = list(BannedKeyword.objects.filter(is_active=True).values('word', 'severity'))

    except Exception:

        db_keywords = [{'word': kw, 'severity': 'flag'} for kw in _FLAG_KEYWORDS]

    hardcoded_set = {kw.lower() for kw in _FLAG_KEYWORDS}

    db_words_set  = {kw['word'].lower() for kw in db_keywords}

    for kw in _FLAG_KEYWORDS:

        if kw.lower() not in db_words_set:

            db_keywords.append({'word': kw, 'severity': 'flag'})

    triggered_delete = []

    triggered_flag   = []

    for kw_obj in db_keywords:

        if kw_obj['word'].lower() in text:

            if kw_obj['severity'] == BannedKeyword.SEVERITY_DELETE:

                triggered_delete.append(kw_obj['word'])

            else:

                triggered_flag.append(kw_obj['word'])

    update_kwargs = {}

    if triggered_delete:

        update_kwargs.update(

            is_flagged=True,

            is_deleted=True,

            deleted_by_staff=True,

            deleted_at=timezone.now(),

            flag_reason=f"Auto-deleted: {', '.join(triggered_delete[:3])}",

        )

    elif triggered_flag:

        update_kwargs.update(

            is_flagged=True,

            flag_reason=f"Auto-flagged: {', '.join(triggered_flag[:5])}",

        )

    if update_kwargs:

        Message.objects.filter(pk=instance.pk).update(**update_kwargs)

        try:

            from asgiref.sync import async_to_sync

            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()

            if channel_layer:

                is_auto_deleted = bool(triggered_delete)

                async_to_sync(channel_layer.group_send)(

                    'admin_moderation',

                    {

                        'type':         'new_flag',

                        'message_id':   instance.pk,

                        'sender':       instance.sender.email,

                        'recipient':    instance.recipient.email,

                        'flag_reason':  update_kwargs.get('flag_reason', ''),

                        'body':         (instance.body or '')[:80],

                        'created_at':   instance.created_at.strftime('%d %b'),

                        'auto_deleted': is_auto_deleted,

                    }

                )

        except Exception:

            pass

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

    """Lookup geo data for an IP. Results are cached in Redis for 30 days."""

    cache_key = f'geo_{ip}'

    cached = cache.get(cache_key)

    if cached is not None:

        return cached

    try:

        import requests as _req

        r = _req.get(f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country,countryCode,isp,lat,lon', timeout=2)

        if r.ok:

            d = r.json()

            if d.get('status') == 'success':

                cache.set(cache_key, d, timeout=86400 * 30)

                return d

    except Exception:

        pass

    cache.set(cache_key, {}, timeout=3600)

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
