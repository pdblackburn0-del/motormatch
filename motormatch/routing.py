"""WebSocket URL routing for motormatch app."""

from django.urls import re_path

from . import consumers

websocket_urlpatterns = [

    re_path(r'^ws/admin/moderation/$', consumers.AdminModerationConsumer.as_asgi()),

    # Per-conversation channel.  ``other_pk`` is the PK of the other
    # participant; the consumer verifies that a message thread exists
    # before accepting the connection.
    re_path(r'^ws/inbox/(?P<other_pk>\d+)/$', consumers.ConversationConsumer.as_asgi()),

]
