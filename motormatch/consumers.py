"""
Django Channels WebSocket consumer for the admin moderation panel.
Connects to the 'admin_moderation' channel group and pushes real-time
events to any open admin dashboard tabs whenever a message is auto-flagged
or auto-deleted by the keyword signal.

Only staff users are permitted to connect.
"""

import json

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
