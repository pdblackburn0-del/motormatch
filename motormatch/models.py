from django.contrib.auth.signals import user_logged_in
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class UserProfile(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True)
    last_name  = models.CharField(max_length=100, blank=True)
    phone      = models.CharField(max_length=30, blank=True)
    avatar     = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio        = models.TextField(blank=True)
    location   = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def get_display_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.user.email.split('@')[0]

    def get_initials(self):
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        if self.first_name:
            return self.first_name[:2].upper()
        return self.user.email[:2].upper()

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
    price        = models.CharField(max_length=50) # using CharField to include currency symbols for now, as in template
    mileage      = models.CharField(max_length=50)
    year         = models.CharField(max_length=4, blank=True, null=True)
    fuel         = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50, blank=True, null=True)
    badge        = models.CharField(max_length=50, blank=True, null=True)
    badge_color  = models.CharField(max_length=20, blank=True, null=True)
    image        = models.URLField(max_length=500, blank=True, null=True)
    image_file   = models.ImageField(
        upload_to='car_images/', blank=True, null=True
    )
    location     = models.CharField(max_length=100, blank=True)
    description  = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    # Whitelist mapping badge_color values to safe Bootstrap classes.
    _BADGE_CLASS_MAP = {
        '#16a34a': 'badge-green',
        '#dc2626': 'badge-red',
    }

    def get_badge_class(self):
        """Return a safe CSS class for the badge colour."""
        return self._BADGE_CLASS_MAP.get(
            (self.badge_color or '').lower(), 'badge-default'
        )

    def get_image(self):
        """Return local file if uploaded, else fall back to URL."""
        if self.image_file and self.image_file.name:
            return self.image_file.url
        return self.image or ''

    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return None
        return round(sum(r.rating for r in reviews) / reviews.count(), 1)

    def __str__(self):
        return f"{self.title} - {self.variant}"


class SavedVehicle(models.Model):
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_vehicles')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'vehicle')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.email} → {self.vehicle.title}"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------
class Review(models.Model):
    vehicle    = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='reviews')
    reviewer   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    rating     = models.PositiveSmallIntegerField(default=5)
    comment    = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('vehicle', 'reviewer')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer.email} → {self.vehicle.title} ({self.rating}★)"


# ---------------------------------------------------------------------------
# Message
# ---------------------------------------------------------------------------
class Message(models.Model):
    sender     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient  = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    vehicle    = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject    = models.CharField(max_length=200, blank=True)
    body       = models.TextField()
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.email} → {self.recipient.email}: {self.subject}"


# ---------------------------------------------------------------------------
# Bid
# ---------------------------------------------------------------------------
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

    vehicle    = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='bids')
    bidder     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids_placed')
    amount     = models.DecimalField(max_digits=12, decimal_places=2)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note       = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bidder.email} bid £{self.amount} on {self.vehicle.title}"


# ---------------------------------------------------------------------------
# Signals
# ---------------------------------------------------------------------------

@receiver(user_logged_in)
def notify_login(sender, request, user, **kwargs):
    """Create an info notification every time a user logs in."""
    ip = request.META.get('REMOTE_ADDR', 'unknown')
    Notification.objects.create(
        user=user,
        title='New login',
        message=f'You logged in from {ip}.',
        notif_type=Notification.TYPE_INFO,
        url='/dashboard/',
    )


@receiver(post_save, sender=SavedVehicle)
def notify_vehicle_saved(sender, instance, created, **kwargs):
    """Notify a seller when someone saves their listing."""
    if created and instance.vehicle.owner and instance.vehicle.owner != instance.user:
        Notification.objects.create(
            user=instance.vehicle.owner,
            title='Someone saved your listing',
            message=f'{instance.user.email} saved your listing: {instance.vehicle.title}.',
            notif_type=Notification.TYPE_SUCCESS,
            url=f'/vehicle/{instance.vehicle.pk}/',
        )
