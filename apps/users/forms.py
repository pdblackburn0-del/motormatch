import re

import phonenumbers
from phonenumbers import NumberParseException

from django import forms
from django.core.exceptions import ValidationError

from allauth.account.forms import SignupForm

from apps.users.models import UserProfile

from motormatch.utils import validate_image_file, _MAX_AVATAR_BYTES, sanitize_plain_text

_NAME_RE     = re.compile(r"^[A-Za-z\u00C0-\u024F'\- ]+$")
_LOCATION_RE = re.compile(r'^[A-Za-z0-9\s,\-\.]+$')
_BIO_MAX = 500


def _validate_and_format_uk_phone(value):
    """Validate a UK phone number and normalise to international format (+44 XXXX XXXXXX).
    Returns the formatted number, or the original value if empty.
    Raises ValidationError if the number is invalid.
    """
    if not value:
        return value
    try:
        parsed = phonenumbers.parse(value, 'GB')
        if not phonenumbers.is_valid_number(parsed):
            raise ValidationError(
                'Enter a valid UK phone number (e.g. 07700 900000 or +44 7700 900000).'
            )
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except NumberParseException:
        raise ValidationError(
            'Enter a valid UK phone number (e.g. 07700 900000 or +44 7700 900000).'
        )


class ProfileForm(forms.ModelForm):

    avatar = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'phone', 'bio', 'location', 'avatar']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+44 7000 000000'}),
            'bio':        forms.Textarea(attrs={
                'class': 'form-control', 'rows': 3,
                'placeholder': 'Tell us a bit about yourself...',
                'maxlength': str(_BIO_MAX), 'data-maxlength': str(_BIO_MAX),
            }),
            'location':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. London, UK'}),
        }

    def clean_first_name(self):
        val = sanitize_plain_text(self.cleaned_data.get('first_name', '')).strip()
        if val:
            if len(val) < 2:
                raise ValidationError('First name must be at least 2 characters.')
            if not _NAME_RE.match(val):
                raise ValidationError('First name can only contain letters, hyphens, and apostrophes.')
        return val

    def clean_last_name(self):
        val = sanitize_plain_text(self.cleaned_data.get('last_name', '')).strip()
        if val:
            if len(val) < 2:
                raise ValidationError('Last name must be at least 2 characters.')
            if not _NAME_RE.match(val):
                raise ValidationError('Last name can only contain letters, hyphens, and apostrophes.')
        return val

    def clean_phone(self):
        val = sanitize_plain_text(self.cleaned_data.get('phone', ''))
        return _validate_and_format_uk_phone(val)

    def clean_location(self):
        val = sanitize_plain_text(self.cleaned_data.get('location', ''))
        if val and len(val.strip()) < 2:
            raise ValidationError('Enter a valid location (e.g. London, UK).')
        if val and not _LOCATION_RE.match(val):
            raise ValidationError('Location may only contain letters, numbers, spaces, and commas.')
        return val

    def clean_bio(self):
        val = sanitize_plain_text(self.cleaned_data.get('bio', ''))
        if val and len(val) > _BIO_MAX:
            raise ValidationError(f'Bio must be {_BIO_MAX} characters or fewer.')
        return val

    def clean_avatar(self):
        f = self.cleaned_data.get('avatar')
        if f and hasattr(f, 'size'):
            validate_image_file(f, max_bytes=_MAX_AVATAR_BYTES)
        return f


class CustomSignupForm(SignupForm):

    first_name = forms.CharField(
        max_length=100, label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'John', 'class': 'form-control py-2'}),
    )

    last_name = forms.CharField(
        max_length=100, label='Last Name',
        widget=forms.TextInput(attrs={'placeholder': 'Doe', 'class': 'form-control py-2'}),
    )

    phone = forms.CharField(
        max_length=30, label='Phone Number', required=False,
        widget=forms.TextInput(attrs={'placeholder': '+44 7000 000000', 'class': 'form-control py-2'}),
    )

    field_order = ['first_name', 'last_name', 'email', 'phone', 'password1', 'password2']

    def clean_first_name(self):
        val = sanitize_plain_text(self.cleaned_data.get('first_name', '')).strip()
        if val:
            if len(val) < 2:
                raise ValidationError('First name must be at least 2 characters.')
            if not _NAME_RE.match(val):
                raise ValidationError('First name can only contain letters, hyphens, and apostrophes.')
        return val

    def clean_last_name(self):
        val = sanitize_plain_text(self.cleaned_data.get('last_name', '')).strip()
        if val:
            if len(val) < 2:
                raise ValidationError('Last name must be at least 2 characters.')
            if not _NAME_RE.match(val):
                raise ValidationError('Last name can only contain letters, hyphens, and apostrophes.')
        return val

    def clean_phone(self):
        val = sanitize_plain_text(self.cleaned_data.get('phone', ''))
        return _validate_and_format_uk_phone(val)

    def save(self, request):
        user = super().save(request)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.first_name = self.cleaned_data.get('first_name', '')
        profile.last_name  = self.cleaned_data.get('last_name', '')
        profile.phone      = self.cleaned_data.get('phone', '') or ''
        profile.save()
        return user
