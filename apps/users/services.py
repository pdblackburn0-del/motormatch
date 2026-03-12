def ban_user(user, reason: str = ''):
    user.is_active = False
    user.save(update_fields=['is_active'])
    try:
        profile = user.profile
        profile.ban_reason = reason
        profile.is_suspended = False
        profile.suspension_until = None
        profile.save(update_fields=['ban_reason', 'is_suspended', 'suspension_until'])
    except Exception:
        pass


def suspend_user(user, until=None, reason: str = ''):
    user.is_active = False
    user.save(update_fields=['is_active'])
    try:
        profile = user.profile
        profile.is_suspended = True
        profile.suspension_until = until
        profile.ban_reason = reason
        profile.save(update_fields=['is_suspended', 'suspension_until', 'ban_reason'])
    except Exception:
        pass


def lift_suspension(profile):
    profile.is_suspended = False
    profile.suspension_until = None
    profile.save(update_fields=['is_suspended', 'suspension_until'])
    try:
        user = profile.user
        user.is_active = True
        user.save(update_fields=['is_active'])
    except Exception:
        pass
