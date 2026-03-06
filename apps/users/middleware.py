"""
Redis-backed online presence tracking.

Every authenticated request updates a `online_{pk}` key in Redis with a 5-minute TTL.
`get_online_status(user_pk)` returns a human-readable status used in the chat header.
"""

from datetime import datetime as _dt, timezone as _tz

from django.core.cache import cache
from django.utils import timezone

# ── Constants ────────────────────────────────────────────────────────────────
ONLINE_TTL    = 86400 * 7  # 7-day Redis TTL so last-seen persists long-term
ONLINE_WINDOW = 120        # within 2 minutes → "Online now"
ONLINE_WHILE  = 18000      # beyond 5 hours → "last seen in a while"


# ── Helpers ───────────────────────────────────────────────────────────────────

def set_user_online(user_pk):
    """Record last-seen timestamp for user_pk in Redis."""
    cache.set(f'online_{user_pk}', timezone.now().isoformat(), timeout=ONLINE_TTL)


def get_online_status(user_pk):
    """
    Returns::

        {
            'online':    bool,        # True if seen within last 2 min
            'last_seen': datetime|None,
            'display':   str|None,    # e.g. 'Online now' or '5 mins ago'
        }
    """
    val = cache.get(f'online_{user_pk}')
    if not val:
        return {'online': False, 'last_seen': None, 'display': None}

    last_seen = _dt.fromisoformat(val)
    if last_seen.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=_tz.utc)

    delta   = timezone.now() - last_seen
    seconds = delta.total_seconds()
    online  = seconds < ONLINE_WINDOW

    if online:
        display = 'Online now'
    elif seconds < 3600:
        m = int(seconds / 60)
        display = f'{m} min{"s" if m != 1 else ""} ago'
    elif seconds < ONLINE_WHILE:
        h = int(seconds / 3600)
        display = f'{h} hour{"s" if h != 1 else ""} ago'
    else:
        display = 'in a while'

    return {'online': online, 'last_seen': last_seen, 'display': display}


# ── Poll-count cache helpers ───────────────────────────────────────────────────

def invalidate_poll_cache(user_pk):
    """
    Bust the notification-poll count cache for a user.
    Call this whenever a new message or notification is created for that user.
    """
    cache.delete(f'poll_counts_{user_pk}')


# ── Recently Viewed ───────────────────────────────────────────────────────────

RECENTLY_VIEWED_MAX = 10
RECENTLY_VIEWED_TTL = 86400 * 30  # 30 days


def push_recently_viewed(user_pk, vehicle_pk):
    """
    Push *vehicle_pk* to the front of the user's recently-viewed list in Redis.
    Deduplicates (existing occurrence removed first) and caps at 10 entries.
    Silently no-ops if Redis is unavailable.
    """
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection('default')
        key  = f'recently_viewed:{user_pk}'
        val  = str(vehicle_pk)
        conn.lrem(key, 0, val)               # remove any existing duplicate
        conn.lpush(key, val)                 # push to head
        conn.ltrim(key, 0, RECENTLY_VIEWED_MAX - 1)  # keep max 10
        conn.expire(key, RECENTLY_VIEWED_TTL)
    except Exception:
        pass


def get_recently_viewed_pks(user_pk):
    """Return a list of vehicle PKs (ints) from the user's recently-viewed list."""
    try:
        from django_redis import get_redis_connection
        conn  = get_redis_connection('default')
        items = conn.lrange(f'recently_viewed:{user_pk}', 0, RECENTLY_VIEWED_MAX - 1)
        return [int(pk) for pk in items]
    except Exception:
        return []


# ── Rate Limiting ─────────────────────────────────────────────────────────────

def check_rate_limit(user_pk, action, max_count=5, window=60):
    """
    Atomic Redis-backed rate limiter using INCR + EXPIRE.

    Returns True  → limit exceeded (block the action).
    Returns False → within limit (allow the action).

    Fails open (returns False) if Redis is unavailable so the site keeps working.
    """
    import time
    try:
        from django_redis import get_redis_connection
        conn   = get_redis_connection('default')
        bucket = int(time.time() / window)
        key    = f'rl:{action}:{user_pk}:{bucket}'
        count  = conn.incr(key)
        if count == 1:
            conn.expire(key, window * 2)   # expire well after the window closes
        return count > max_count
    except Exception:
        return False  # fail open — don't block users if Redis is down


# ── Middleware ────────────────────────────────────────────────────────────────

class OnlinePresenceMiddleware:
    """After every authenticated request, update the user's last-seen key in Redis."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Update *after* response so it never delays the view
        if request.user.is_authenticated:
            set_user_online(request.user.pk)
        return response


class BanSuspendMiddleware:
    """
    On every request, check if the logged-in user has been banned or suspended
    since their session was created.  If so, log them out immediately and
    redirect to the login page with an appropriate error message.

    This handles the case where a moderator bans/suspends someone who is
    already logged in — they get kicked out on their very next request.
    """

    _EXEMPT_PATHS = ('/accounts/logout/', '/accounts/login/')

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if (
            request.user.is_authenticated
            and not request.path.startswith(self._EXEMPT_PATHS)
            # Skip admin paths so staff can still access the panel
            and not request.path.startswith('/control-panel/')
        ):
            user = request.user

            # 1. Hard ban
            if not user.is_active:
                from django.contrib.auth import logout
                from django.contrib import messages as django_messages
                from django.shortcuts import redirect
                ban_reason = ''
                try:
                    ban_reason = user.profile.ban_reason or ''
                except Exception:
                    pass
                logout(request)
                msg = 'Your account has been permanently banned.'
                if ban_reason:
                    msg += f' Reason: {ban_reason}'
                django_messages.error(request, msg)
                return redirect('account_login')

            # 2. Suspension
            try:
                profile = user.profile
            except Exception:
                profile = None

            if profile and profile.is_suspended:
                until = profile.suspension_until
                if until is None or until > timezone.now():
                    from django.contrib.auth import logout
                    from django.contrib import messages as django_messages
                    from django.shortcuts import redirect
                    logout(request)
                    if until:
                        local_until = until.strftime('%d %b %Y at %H:%M UTC')
                        msg = f'Your account is suspended until {local_until}.'
                    else:
                        msg = 'Your account is currently suspended.'
                    if profile.ban_reason:
                        msg += f' Reason: {profile.ban_reason}'
                    django_messages.error(request, msg)
                    return redirect('account_login')
                else:
                    # Suspension expired — lift it silently
                    profile.is_suspended = False
                    profile.suspension_until = None
                    profile.save(update_fields=['is_suspended', 'suspension_until'])

        return self.get_response(request)
