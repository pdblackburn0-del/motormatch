from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from cloudinary.models import CloudinaryField

from apps.vehicles.models import Vehicle

User = get_user_model()

_FLAG_KEYWORDS = [
    'hate', 'kill', 'murder', 'rape', 'terrorist', 'bomb',
    'nigger', 'nigga', 'faggot', 'chink', 'spic', 'kike',
    'retard', 'whore', 'cunt', 'slut',
]


class Message(models.Model):
    sender      = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipient   = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    vehicle     = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    subject     = models.CharField(max_length=200, blank=True)
    body        = models.TextField(blank=True)
    attachment  = CloudinaryField('attachment', folder='message_attachments', blank=True, null=True)
    gif_url     = models.CharField(max_length=500, blank=True)

    is_read          = models.BooleanField(default=False, db_index=True)
    is_flagged       = models.BooleanField(default=False, db_index=True)
    flag_reason      = models.CharField(max_length=500, blank=True)
    is_deleted       = models.BooleanField(default=False, db_index=True)
    deleted_by_staff = models.BooleanField(default=False)
    deleted_at       = models.DateTimeField(null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'motormatch'
        ordering  = ['-created_at']
        indexes   = [
            models.Index(fields=['sender', 'recipient'], name='msg_sender_recipient_idx'),
            models.Index(fields=['recipient', 'is_read'], name='msg_recipient_read_idx'),
        ]

    def __str__(self):
        return f'{self.sender.email} → {self.recipient.email}: {self.subject}'

    @property
    def display_body(self):
        return None if self.is_deleted else self.body


class MessageReaction(models.Model):
    message    = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='message_reactions')
    emoji      = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label     = 'motormatch'
        unique_together = ('message', 'user')

    def __str__(self):
        return f'{self.user_id} → {self.message_id}: {self.emoji}'


class BannedKeyword(models.Model):
    SEVERITY_FLAG   = 'flag'
    SEVERITY_DELETE = 'delete'

    SEVERITY_CHOICES = [
        ('flag',   'Flag for review'),
        ('delete', 'Auto-delete (hate speech / slurs)'),
    ]

    CATEGORY_CHOICES = [
        ('hate',     'Hate Speech'),
        ('fraud',    'Fraud / Scam'),
        ('spam',     'Spam'),
        ('violence', 'Violence'),
        ('adult',    'Adult Content'),
        ('other',    'Other'),
    ]

    word      = models.CharField(max_length=200, unique=True, db_index=True)
    severity  = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=SEVERITY_FLAG)
    category  = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other', blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    added_by  = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='banned_keywords_added',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'motormatch'
        ordering  = ['word']

    def __str__(self):
        return f'{self.word} ({self.severity})'


@receiver(post_save, sender=Message)
def auto_flag_message(sender, instance, created, **kwargs):
    if not created:
        return

    text = f'{instance.subject} {instance.body}'.lower()

    try:
        db_keywords = list(BannedKeyword.objects.filter(is_active=True).values('word', 'severity'))
    except Exception:
        db_keywords = [{'word': kw, 'severity': 'flag'} for kw in _FLAG_KEYWORDS]

    db_words_set = {kw['word'].lower() for kw in db_keywords}
    for kw in _FLAG_KEYWORDS:
        if kw.lower() not in db_words_set:
            db_keywords.append({'word': kw, 'severity': 'flag'})

    triggered_delete = []
    triggered_flag   = []

    for kw_obj in db_keywords:
        if kw_obj['word'].lower() in text:
            if kw_obj['severity'] == BannedKeyword.SEVERITY_DELETE:
                triggered_delete.append(kw_obj['word'])
            else:
                triggered_flag.append(kw_obj['word'])

    update_kwargs = {}
    if triggered_delete:
        update_kwargs.update(
            is_flagged=True,
            is_deleted=True,
            deleted_by_staff=True,
            deleted_at=timezone.now(),
            flag_reason=f"Auto-deleted: {', '.join(triggered_delete[:3])}",
        )
    elif triggered_flag:
        update_kwargs.update(
            is_flagged=True,
            flag_reason=f"Auto-flagged: {', '.join(triggered_flag[:5])}",
        )

    if not update_kwargs:
        return

    Message.objects.filter(pk=instance.pk).update(**update_kwargs)

    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                'admin_moderation',
                {
                    'type':         'new_flag',
                    'message_id':   instance.pk,
                    'sender':       instance.sender.email,
                    'recipient':    instance.recipient.email,
                    'flag_reason':  update_kwargs.get('flag_reason', ''),
                    'body':         (instance.body or '')[:80],
                    'created_at':   instance.created_at.strftime('%d %b'),
                    'auto_deleted': bool(triggered_delete),
                },
            )
    except Exception:
        pass
