"""
Custom django-allauth account adapter.

Blocks login for:
  • Banned users   — is_active=False  →  "Your account has been banned."
  • Suspended users — is_suspended=True (and suspension has not expired)
                    →  "Your account is suspended until <date>."
"""
from django.utils import timezone
from allauth.account.adapter import DefaultAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.shortcuts import redirect
from django.contrib import messages as django_messages


class AccountAdapter(DefaultAccountAdapter):

    def authentication_error(self, request, credentials, error=None, exception=None, extra_context=None):
        # Let the default handler deal with wrong passwords / unknown users
        pass

    def pre_login(self, request, user, **kwargs):
        """Called by allauth right after credential verification, before session setup."""
        # 1. Hard ban — user.is_active = False
        if not user.is_active:
            ban_reason = ''
            try:
                ban_reason = user.profile.ban_reason or ''
            except Exception:
                pass
            msg = 'Your account has been permanently banned.'
            if ban_reason:
                msg += f' Reason: {ban_reason}'
            django_messages.error(request, msg)
            raise ImmediateHttpResponse(redirect('account_login'))

        # 2. Suspension — profile.is_suspended
        try:
            profile = user.profile
        except Exception:
            return super().pre_login(request, user, **kwargs)

        if profile.is_suspended:
            until = profile.suspension_until
            if until is None or until > timezone.now():
                # Still suspended
                if until:
                    local_until = until.strftime('%d %b %Y at %H:%M UTC')
                    msg = f'Your account is suspended until {local_until}.'
                else:
                    msg = 'Your account is currently suspended.'
                if profile.ban_reason:
                    msg += f' Reason: {profile.ban_reason}'
                django_messages.error(request, msg)
                raise ImmediateHttpResponse(redirect('account_login'))
            else:
                # Suspension expired — lift it automatically
                profile.is_suspended = False
                profile.suspension_until = None
                profile.save(update_fields=['is_suspended', 'suspension_until'])

        return super().pre_login(request, user, **kwargs)
