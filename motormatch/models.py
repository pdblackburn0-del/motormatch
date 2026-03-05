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
    title = models.CharField(max_length=200)
    variant = models.CharField(max_length=200)
    price = models.CharField(max_length=50) # using CharField to include currency symbols for now, as in template
    mileage = models.CharField(max_length=50)
    year = models.CharField(max_length=4, blank=True, null=True)
    fuel = models.CharField(max_length=50)
    transmission = models.CharField(max_length=50, blank=True, null=True)
    badge = models.CharField(max_length=50, blank=True, null=True)
    badge_color = models.CharField(max_length=20, blank=True, null=True)
    image = models.URLField(max_length=500, blank=True, null=True)
    image_file = models.ImageField(
        upload_to='car_images/', blank=True, null=True
    )

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
