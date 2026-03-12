from django.contrib.auth import get_user_model
from django.db import models

from apps.notifications.models import Notification
from apps.users.models import UserProfile, Review, LoginEvent
from apps.vehicles.models import Vehicle, SavedVehicle, VehicleImage, Bid
from apps.messaging.models import Message, MessageReaction, BannedKeyword

User = get_user_model()


class AdminNote(models.Model):
    author  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True,
                                related_name='admin_notes_written')
    user    = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='admin_notes')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, null=True, blank=True,
                                related_name='admin_notes')
    note       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'motormatch'
        ordering  = ['-created_at']

    def __str__(self):
        target = f'User:{self.user_id}' if self.user_id else f'Vehicle:{self.vehicle_id}'
        return f'Note by {self.author} on {target}'


__all__ = [
    'Notification',
    'UserProfile', 'Review', 'LoginEvent',
    'Vehicle', 'SavedVehicle', 'VehicleImage', 'Bid',
    'Message', 'MessageReaction', 'BannedKeyword',
    'AdminNote',
]
