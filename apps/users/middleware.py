"""
Redis-backed online presence tracking.

Every authenticated request updates a `online_{pk}` key in Redis with a 5-minute TTL.
`get_online_status(user_pk)` returns a human-readable status used in the chat header.
"""

from datetime import datetime as _dt, timezone as _tz

from django.core.cache import cache
from django.utils import timezone

# ── Constants ────────────────────────────────────────────────────────────────
ONLINE_TTL    = 300   # 5-minute Redis TTL for the last-seen key
ONLINE_WINDOW = 120   # within 2 minutes → "Online now"


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
    elif seconds < 60:
        display = 'Just now'
    elif seconds < 3600:
        m = int(seconds / 60)
        display = f'{m} min{"s" if m != 1 else ""} ago'
    elif seconds < 86400:
        h = int(seconds / 3600)
        display = f'{h} hour{"s" if h != 1 else ""} ago'
    else:
        d = int(seconds / 86400)
        display = f'{d} day{"s" if d != 1 else ""} ago'

    return {'online': online, 'last_seen': last_seen, 'display': display}


# ── Poll-count cache helpers ───────────────────────────────────────────────────

def invalidate_poll_cache(user_pk):
    """
    Bust the notification-poll count cache for a user.
    Call this whenever a new message or notification is created for that user.
    """
    cache.delete(f'poll_counts_{user_pk}')


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
