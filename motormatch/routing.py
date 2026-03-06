"""WebSocket URL routing for motormatch app."""
from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'^ws/admin/moderation/$', consumers.AdminModerationConsumer.as_asgi()),
]
