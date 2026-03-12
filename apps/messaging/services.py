from apps.messaging.models import Message, MessageReaction
from apps.notifications.models import Notification
from apps.users.middleware import invalidate_poll_cache


def create_message(sender, recipient, body: str, vehicle=None, attachment=None, gif_url: str = ''):
    return Message.objects.create(
        sender=sender,
        recipient=recipient,
        vehicle=vehicle,
        subject='',
        body=body,
        attachment=attachment or None,
        gif_url=gif_url,
    )


def notify_new_message(sender, recipient, referer: str = ''):
    if f'/inbox/{sender.pk}/' in referer:
        return
    sender_name = (
        sender.profile.get_display_name()
        if hasattr(sender, 'profile')
        else sender.email.split('@')[0]
    )
    Notification.objects.create(
        user=recipient,
        title='New message',
        message=f'{sender_name} sent you a message.',
        notif_type='info',
        url=f'/inbox/{sender.pk}/',
    )
    invalidate_poll_cache(recipient.pk)


def upsert_reaction(user, message, emoji: str):
    existing = MessageReaction.objects.filter(message=message, user=user).first()
    if existing:
        if existing.emoji == emoji:
            existing.delete()
        else:
            existing.emoji = emoji
            existing.save(update_fields=['emoji'])
    else:
        MessageReaction.objects.create(message=message, user=user, emoji=emoji)


def create_message(sender, recipient, body: str, vehicle=None, attachment=None, gif_url: str = ''):
    return Message.objects.create(
        sender=sender,
        recipient=recipient,
        vehicle=vehicle,
        subject='',
        body=body,
        attachment=attachment or None,
        gif_url=gif_url,
    )


def notify_new_message(sender, recipient, referer: str = ''):
    if f'/inbox/{sender.pk}/' in referer:
        return

    sender_name = (
        sender.profile.get_display_name()
        if hasattr(sender, 'profile')
        else sender.email.split('@')[0]
    )
    Notification.objects.create(
        user=recipient,
        title='New message',
        message=f'{sender_name} sent you a message.',
        notif_type='info',
        url=f'/inbox/{sender.pk}/',
    )
    invalidate_poll_cache(recipient.pk)


def upsert_reaction(user, message, emoji: str):
    existing = MessageReaction.objects.filter(message=message, user=user).first()
    if existing:
        if existing.emoji == emoji:
            existing.delete()
        else:
            existing.emoji = emoji
            existing.save(update_fields=['emoji'])
    else:
        MessageReaction.objects.create(message=message, user=user, emoji=emoji)
