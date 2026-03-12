from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


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
        app_label = 'motormatch'
        ordering  = ['-created_at']

    def __str__(self):
        return f'[{self.user.email}] {self.title}'
