import imghdr

import bleach

from django import forms


def sanitize_plain_text(value):
    if not value:
        return value
    return bleach.clean(value, tags=[], strip=True)

_ALLOWED_IMAGE_TYPES = {'jpeg', 'png', 'webp'}
_ALLOWED_ATTACHMENT_TYPES = {'jpeg', 'png', 'webp', 'gif'}
_MAX_VEHICLE_IMAGE_BYTES = 5 * 1024 * 1024
_MAX_AVATAR_BYTES = 2 * 1024 * 1024
_MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024


def validate_image_file(f, max_bytes=_MAX_VEHICLE_IMAGE_BYTES, allowed_types=None):
    if allowed_types is None:
        allowed_types = _ALLOWED_IMAGE_TYPES
    if f.size > max_bytes:
        raise forms.ValidationError(f'File must be under {max_bytes // (1024 * 1024)} MB.')
    img_type = imghdr.what(f)
    f.seek(0)
    if img_type not in allowed_types:
        labels = ', '.join(t.upper() for t in sorted(allowed_types))
        raise forms.ValidationError(f'Only {labels} images are allowed.')


def validate_image_url(url):
    if not url:
        return
    url_lower = url.lower().split('?')[0]
    if not url_lower.startswith('https://'):
        raise forms.ValidationError('Image URL must start with https://.')
    if not any(url_lower.endswith(ext) for ext in ('.jpg', '.jpeg', '.png', '.webp')):
        raise forms.ValidationError('Image URL must point to a JPEG, PNG, or WebP file.')
