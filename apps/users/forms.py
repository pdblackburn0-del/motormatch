from django import forms

from allauth.account.forms import SignupForm

from apps.users.models import UserProfile

from motormatch.utils import validate_image_file, _MAX_AVATAR_BYTES

class ProfileForm(forms.ModelForm):

    class Meta:

        model = UserProfile

        fields = ['first_name', 'last_name', 'phone', 'bio', 'location', 'avatar']

        widgets = {

            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),

            'last_name':  forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),

            'phone':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+44 7000 000000'}),

            'bio':        forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Tell us a bit about yourself...'}),

            'location':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. London, UK'}),

            'avatar':     forms.ClearableFileInput(attrs={'class': 'form-control'}),

        }

    def clean_avatar(self):
        f = self.cleaned_data.get('avatar')
        if f and hasattr(f, 'size'):
            validate_image_file(f, max_bytes=_MAX_AVATAR_BYTES)
        return f

class CustomSignupForm(SignupForm):

    """Extends allauth SignupForm to capture first name, last name, and phone."""

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

    def save(self, request):

        user = super().save(request)

        profile, _ = UserProfile.objects.get_or_create(user=user)

        profile.first_name = self.cleaned_data.get('first_name', '')

        profile.last_name  = self.cleaned_data.get('last_name', '')

        profile.phone      = self.cleaned_data.get('phone', '')

        profile.save()

        return user
