"""
Tests for motormatch/consumers.py — ConversationConsumer participant checks.

Uses channels.testing.WebsocketCommunicator to drive the consumer
in-process (no real server needed).  Each communicator has the Django
user injected directly into the scope so we can exercise the auth /
participant guards in isolation.
"""

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test import TransactionTestCase

from motormatch.consumers import ConversationConsumer
from motormatch.models import Message

User = get_user_model()


def _make_communicator(user, other_pk):
    """
    Build a WebsocketCommunicator for ConversationConsumer with *user*
    injected into the scope.  ``other_pk`` is passed as the URL kwarg.
    """
    app  = ConversationConsumer.as_asgi()
    path = f'/ws/inbox/{other_pk}/'
    comm = WebsocketCommunicator(app, path)
    comm.scope['user']      = user
    comm.scope['url_route'] = {'kwargs': {'other_pk': str(other_pk)}}
    return comm


class ConversationConsumerParticipantTests(TransactionTestCase):
    """Verify that the consumer enforces participant checks on connect."""

    def setUp(self):
        self.alice   = User.objects.create_user(username='alice',   email='alice@test.com',   password='x')
        self.bob     = User.objects.create_user(username='bob',     email='bob@test.com',     password='x')
        self.charlie = User.objects.create_user(username='charlie', email='charlie@test.com', password='x')

    # ------------------------------------------------------------------ #

    def test_unauthenticated_user_is_rejected_4403(self):
        """AnonymousUser must not be accepted; expect close code 4403."""

        @async_to_sync
        async def run():
            comm = _make_communicator(AnonymousUser(), self.bob.pk)
            connected, code = await comm.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4403)
            await comm.disconnect()

        run()

    def test_non_participant_is_rejected_4003(self):
        """
        Authenticated user with no message thread to other_pk must be
        rejected with close code 4003.
        """

        @async_to_sync
        async def run():
            # charlie has never messaged alice
            comm = _make_communicator(self.charlie, self.alice.pk)
            connected, code = await comm.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4003)
            await comm.disconnect()

        run()

    def test_participant_is_accepted(self):
        """If a message thread exists, the connection should be accepted."""

        Message.objects.create(
            sender=self.alice, recipient=self.bob,
            subject='hi', body='hello',
        )

        @async_to_sync
        async def run():
            comm = _make_communicator(self.alice, self.bob.pk)
            connected, _ = await comm.connect()
            self.assertTrue(connected)
            await comm.disconnect()

        run()

    def test_participant_other_side_is_also_accepted(self):
        """The check is symmetric — recipient can also connect."""

        Message.objects.create(
            sender=self.alice, recipient=self.bob,
            subject='hi', body='hello',
        )

        @async_to_sync
        async def run():
            comm = _make_communicator(self.bob, self.alice.pk)
            connected, _ = await comm.connect()
            self.assertTrue(connected)
            await comm.disconnect()

        run()

    def test_connecting_to_self_is_rejected_4403(self):
        """user.pk == other_pk makes no sense; expect close code 4403."""

        @async_to_sync
        async def run():
            comm = _make_communicator(self.alice, self.alice.pk)
            connected, code = await comm.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4403)
            await comm.disconnect()

        run()

    def test_third_party_cannot_join_existing_thread(self):
        """
        Charlie must not be able to join alice↔bob's channel even though
        the thread exists between alice and bob.
        """

        Message.objects.create(
            sender=self.alice, recipient=self.bob,
            subject='hi', body='hello',
        )

        @async_to_sync
        async def run():
            # charlie tries to join alice's channel
            comm = _make_communicator(self.charlie, self.alice.pk)
            connected, code = await comm.connect()
            self.assertFalse(connected)
            self.assertEqual(code, 4003)
            await comm.disconnect()

        run()
