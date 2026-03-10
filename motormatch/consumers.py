"""
WebSocket consumers for the motormatch project.

AdminModerationConsumer
    Pushes real-time moderation events to open admin dashboard tabs.
    Only staff users are permitted to connect.

ConversationConsumer
    Per-conversation real-time channel used by the messaging feature.
    On connect the consumer verifies (via a DB query) that the connecting
    user is an actual participant in the requested conversation before
    accepting the socket.  The same check is repeated on every incoming
    message so a user whose conversation is later deleted cannot keep
    pushing events through a stale socket.
"""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

class AdminModerationConsumer(AsyncWebsocketConsumer):

    GROUP_NAME = 'admin_moderation'

    async def connect(self):

        user = self.scope.get('user')

        if not user or not user.is_authenticated or not user.is_staff:

            await self.close(code=4403)

            return

        await self.channel_layer.group_add(self.GROUP_NAME, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):

        await self.channel_layer.group_discard(self.GROUP_NAME, self.channel_name)

    async def new_flag(self, event):

        """Push a flagged/deleted message notification to the browser."""

        await self.send(text_data=json.dumps({

            'event':        'new_flag',

            'message_id':   event['message_id'],

            'sender':       event['sender'],

            'recipient':    event['recipient'],

            'flag_reason':  event['flag_reason'],

            'body':         event['body'],

            'created_at':   event['created_at'],

            'auto_deleted': event['auto_deleted'],

        }))


class ConversationConsumer(AsyncWebsocketConsumer):
    """
    Real-time channel for a two-user messaging conversation.

    The URL pattern must supply an ``other_pk`` kwarg identifying the
    other participant.  Connection is refused (4003) if no message
    thread exists between the connecting user and ``other_pk``, ensuring
    that only legitimate participants can join the channel group.
    """

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    @database_sync_to_async
    def _is_participant(self, user_pk, other_pk):
        """Return True if at least one message exists between the two users."""
        from django.contrib.auth import get_user_model
        from django.db.models import Q
        from motormatch.models import Message

        User = get_user_model()

        if not User.objects.filter(pk=other_pk, is_active=True).exists():
            return False

        return Message.objects.filter(
            Q(sender_id=user_pk, recipient_id=other_pk) |
            Q(sender_id=other_pk, recipient_id=user_pk)
        ).exists()

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    async def connect(self):

        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4403)
            return

        try:
            other_pk = int(self.scope['url_route']['kwargs']['other_pk'])
        except (KeyError, ValueError, TypeError):
            await self.close(code=4400)
            return

        if user.pk == other_pk:
            await self.close(code=4403)
            return

        if not await self._is_participant(user.pk, other_pk):
            await self.close(code=4003)
            return

        # Deterministic group name scoped to exactly these two users.
        a, b = sorted([user.pk, other_pk])
        self.group_name = f'chat_{a}_{b}'
        self.other_pk   = other_pk

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):

        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Re-verify participation before processing any incoming frame."""

        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4403)
            return

        if not await self._is_participant(user.pk, self.other_pk):
            await self.close(code=4003)
            return

        # Messages are sent via the HTTP API; the client does not push
        # application data through this socket.  Any frame received here
        # is silently ignored after the participant check above.

    # ------------------------------------------------------------------ #
    # Server-push event handlers                                           #
    # ------------------------------------------------------------------ #

    async def chat_message(self, event):
        """Forward a new-message event to the connected browser tab."""

        await self.send(text_data=json.dumps({
            'event':   'chat_message',
            'message': event['message'],
        }))

    async def chat_typing(self, event):
        """Forward a typing-indicator event to the connected browser tab."""

        await self.send(text_data=json.dumps({
            'event':     'typing',
            'is_typing': event['is_typing'],
        }))

    async def chat_read(self, event):
        """Notify the sender that the recipient has read up to a message."""

        await self.send(text_data=json.dumps({
            'event':      'read',
            'read_up_to': event['read_up_to'],
        }))
