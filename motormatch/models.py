from django.db import models

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
