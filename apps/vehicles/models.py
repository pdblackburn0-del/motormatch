from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from cloudinary.models import CloudinaryField

from apps.notifications.models import Notification

User = get_user_model()


class Vehicle(models.Model):
    APPROVAL_PENDING  = 'pending'
    APPROVAL_APPROVED = 'approved'
    APPROVAL_REJECTED = 'rejected'

    APPROVAL_CHOICES = [
        (APPROVAL_PENDING,  'Pending Review'),
        (APPROVAL_APPROVED, 'Approved'),
        (APPROVAL_REJECTED, 'Rejected'),
    ]

    STATUS_ACTIVE       = 'active'
    STATUS_PENDING_SALE = 'pending_sale'
    STATUS_SOLD         = 'sold'
    STATUS_REMOVED      = 'removed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE,       'Active'),
        (STATUS_PENDING_SALE, 'Pending Sale'),
        (STATUS_SOLD,         'Sold'),
        (STATUS_REMOVED,      'Removed'),
    ]

    owner        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    title        = models.CharField(max_length=200)
    variant      = models.CharField(max_length=200)
    price        = models.CharField(max_length=50)
    mileage      = models.CharField(max_length=50)
    year         = models.CharField(max_length=4, blank=True, null=True, db_index=True)
    fuel         = models.CharField(max_length=50, db_index=True)
    transmission = models.CharField(max_length=50, blank=True, null=True, db_index=True)
    badge        = models.CharField(max_length=50, blank=True, null=True)
    badge_color  = models.CharField(max_length=20, blank=True, null=True)
    image        = models.URLField(max_length=500, blank=True, null=True)
    image_file   = CloudinaryField('image', folder='car_images', blank=True, null=True)
    location     = models.CharField(max_length=100, blank=True)
    description  = models.TextField(blank=True)
    is_removed   = models.BooleanField(default=False, db_index=True)

    listing_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES,
        default=STATUS_ACTIVE, db_index=True,
    )
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_CHOICES,
        default=APPROVAL_APPROVED, db_index=True,
    )
    approval_note = models.CharField(max_length=500, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True, null=True, blank=True, db_index=True)

    class Meta:
        app_label = 'motormatch'
        indexes   = [
            models.Index(fields=['is_removed', '-created_at'], name='vehicle_active_date_idx'),
            models.Index(fields=['owner', 'is_removed'],       name='vehicle_owner_active_idx'),
        ]

    _BADGE_CLASS_MAP = {
        '#16a34a': 'badge-green',
        '#dc2626': 'badge-red',
    }

    def get_badge_class(self):
        return self._BADGE_CLASS_MAP.get((self.badge_color or '').lower(), 'badge-default')

    def get_image(self):
        if self.image_file and self.image_file.public_id:
            return self.image_file.url
        return self.image or ''

    def __str__(self):
        return f'{self.title} - {self.variant}'


class SavedVehicle(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_vehicles')
    vehicle  = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label     = 'motormatch'
        unique_together = ('user', 'vehicle')
        ordering      = ['-saved_at']

    def __str__(self):
        return f'{self.user.email} → {self.vehicle.title}'


class VehicleImage(models.Model):
    vehicle    = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='images')
    image_file = CloudinaryField('image', folder='car_images', blank=True, null=True)
    order      = models.PositiveSmallIntegerField(default=0)

    class Meta:
        app_label = 'motormatch'
        ordering  = ['order']

    def get_url(self):
        if self.image_file and self.image_file.public_id:
            return self.image_file.url
        return ''

    def __str__(self):
        return f'Image {self.order} for {self.vehicle}'


class Bid(models.Model):
    STATUS_PENDING   = 'pending'
    STATUS_ACCEPTED  = 'accepted'
    STATUS_DECLINED  = 'declined'
    STATUS_COUNTERED = 'countered'

    STATUS_CHOICES = [
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
        app_label = 'motormatch'
        ordering  = ['-created_at']

    def __str__(self):
        return f'{self.bidder.email} bid £{self.amount} on {self.vehicle.title}'


@receiver(post_save, sender=SavedVehicle)
def notify_vehicle_saved(sender, instance, created, **kwargs):
    if not created:
        return
    if not instance.vehicle.owner or instance.vehicle.owner == instance.user:
        return
    saver_name = (
        instance.user.profile.get_display_name()
        if hasattr(instance.user, 'profile')
        else instance.user.email.split('@')[0]
    )
    Notification.objects.create(
        user=instance.vehicle.owner,
        title='Someone saved your listing',
        message=f'{saver_name} saved your listing: {instance.vehicle.title}.',
        notif_type=Notification.TYPE_SUCCESS,
        url=f'/vehicle/{instance.vehicle.pk}/',
    )
