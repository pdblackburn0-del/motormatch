"""
Custom django-allauth account adapter.

Blocks login for:
  • Banned users   — is_active=False  →  "Your account has been banned."
  • Suspended users — is_suspended=True (and suspension has not expired)
                    →  "Your account is suspended until <date>."
"""

from django.utils import timezone
from django.contrib.auth import get_user_model

from allauth.account.adapter import DefaultAccountAdapter

from allauth.exceptions import ImmediateHttpResponse

from django.shortcuts import redirect

from django.contrib import messages as django_messages

class AccountAdapter(DefaultAccountAdapter):

    def authentication_error(self, request, credentials, error=None, exception=None, extra_context=None):

        pass

    def pre_signup(self, request, user):

        email = getattr(user, 'email', '') or ''

        if email:
            User = get_user_model()
            try:
                existing = User.objects.get(email__iexact=email)
                if not existing.is_active:
                    ban_reason = ''
                    try:
                        ban_reason = existing.profile.ban_reason or ''
                    except Exception:
                        pass
                    msg = 'This email address is associated with a banned account and cannot be used to register.'
                    if ban_reason:
                        msg += f' Reason: {ban_reason}'
                    django_messages.error(request, msg)
                    raise ImmediateHttpResponse(redirect('account_signup'))
            except User.DoesNotExist:
                pass

        return super().pre_signup(request, user)

    def pre_login(self, request, user, **kwargs):

        """Called by allauth right after credential verification, before session setup."""

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

        try:

            profile = user.profile

        except Exception:

            return super().pre_login(request, user, **kwargs)

        if profile.is_suspended:

            until = profile.suspension_until

            if until is None or until > timezone.now():

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

                profile.is_suspended = False

                profile.suspension_until = None

                profile.save(update_fields=['is_suspended', 'suspension_until'])

        return super().pre_login(request, user, **kwargs)
