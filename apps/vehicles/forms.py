import datetime
import re

from django import forms
from django.core.exceptions import ValidationError

from apps.vehicles.models import Vehicle

from motormatch.utils import validate_image_file, validate_image_url, sanitize_plain_text

FUEL_CHOICES = [
    ('Petrol',         'Petrol'),
    ('Diesel',         'Diesel'),
    ('Hybrid',         'Hybrid'),
    ('Electric',       'Electric'),
    ('Plug-in Hybrid', 'Plug-in Hybrid'),
]

TRANSMISSION_CHOICES = [
    ('Automatic',      'Automatic'),
    ('Manual',         'Manual'),
    ('Semi-Automatic', 'Semi-Automatic'),
]

_CURRENT_YEAR = datetime.date.today().year
DESCRIPTION_MAX_LENGTH = 2000
_LOCATION_RE = re.compile(r'^[A-Za-z0-9\s,\-\.]+$')


class VehicleEditForm(forms.ModelForm):

    image = forms.CharField(
        required=False,
        label='Image URL (alternative to upload)',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
    )

    class Meta:
        model  = Vehicle
        fields = ['title', 'variant', 'price', 'mileage', 'year', 'fuel',
                  'transmission', 'location', 'description', 'image_file', 'image']
        widgets = {
            'title':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2019 Ford Focus'}),
            'variant':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ST-Line 5dr'}),
            'price':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. £7,500'}),
            'mileage':      forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 32,000 miles'}),
            'year':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2019'}),
            'fuel':         forms.Select(choices=FUEL_CHOICES, attrs={'class': 'form-select'}),
            'transmission': forms.Select(choices=TRANSMISSION_CHOICES, attrs={'class': 'form-select'}),
            'location':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. London, UK'}),
            'description':  forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'image_file':   forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'}),
        }

    def clean_image(self):
        url = self.cleaned_data.get('image', '').strip()
        validate_image_url(url)
        return url

    def clean_description(self):
        return sanitize_plain_text(self.cleaned_data.get('description', ''))


class SellForm(forms.Form):

    make = forms.CharField(
        max_length=100, label='Make',
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Ford', 'class': 'form-control'}),
    )

    model = forms.CharField(
        max_length=100, label='Model',
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Fiesta', 'class': 'form-control'}),
    )

    variant = forms.CharField(
        max_length=200, label='Variant / Trim', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'e.g., Sport Sedan 4D', 'class': 'form-control'}),
    )

    year = forms.IntegerField(
        label='Year', min_value=1900, max_value=_CURRENT_YEAR + 1,
        widget=forms.NumberInput(attrs={'placeholder': 'e.g., 2022', 'class': 'form-control'}),
        error_messages={'invalid': 'Enter a valid 4-digit year (e.g. 2022).'},
    )

    price = forms.DecimalField(
        max_digits=10, decimal_places=2, min_value=0, label='Asking Price (\u00a3)',
        widget=forms.NumberInput(attrs={'placeholder': '5000', 'class': 'form-control', 'min': '0'}),
        error_messages={'invalid': 'Enter a valid price (e.g. 5000).'},
    )

    mileage = forms.IntegerField(
        min_value=0, label='Mileage',
        widget=forms.NumberInput(attrs={'placeholder': '32000', 'class': 'form-control', 'min': '0'}),
        error_messages={'invalid': 'Enter mileage as a whole number (e.g. 32000).'},
    )

    fuel = forms.ChoiceField(
        choices=FUEL_CHOICES, label='Fuel Type',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    transmission = forms.ChoiceField(
        choices=TRANSMISSION_CHOICES, label='Transmission',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    image_file = forms.ImageField(
        label='Main Photo', required=False,
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/jpeg,image/png,image/webp'}),
    )

    image_url = forms.CharField(
        label='Or paste an image URL', required=False,
        widget=forms.TextInput(attrs={'placeholder': 'https://...', 'class': 'form-control'}),
    )

    location = forms.CharField(
        max_length=100, required=False, label='Location',
        widget=forms.TextInput(attrs={'placeholder': 'e.g. London, UK', 'class': 'form-control'}),
    )

    description = forms.CharField(
        required=False, max_length=DESCRIPTION_MAX_LENGTH, label='Description',
        widget=forms.Textarea(attrs={
            'rows': 4, 'class': 'form-control',
            'placeholder': 'Tell buyers about the car \u2014 service history, modifications, reason for sale...',
            'maxlength': str(DESCRIPTION_MAX_LENGTH),
            'data-maxlength': str(DESCRIPTION_MAX_LENGTH),
        }),
    )

    def clean_image_file(self):
        f = self.cleaned_data.get('image_file')
        if f:
            validate_image_file(f)
        return f

    def clean_image_url(self):
        url = self.cleaned_data.get('image_url', '').strip()
        validate_image_url(url)
        return url

    def clean_location(self):
        val = sanitize_plain_text(self.cleaned_data.get('location', ''))
        if val and len(val.strip()) < 2:
            raise ValidationError('Enter a valid location (e.g. London, UK or SW1A 1AA).')
        if val and not _LOCATION_RE.match(val):
            raise ValidationError('Location may only contain letters, numbers, spaces, and commas.')
        return val

    def clean_description(self):
        return sanitize_plain_text(self.cleaned_data.get('description', ''))

    def save(self, owner=None, commit=True):
        data = self.cleaned_data
        vehicle = Vehicle(
            title=f"{data['year']} {data['make']} {data['model']}",
            variant=data.get('variant') or '',
            price=data['price'],
            mileage=data['mileage'],
            year=data['year'],
            fuel=data['fuel'],
            transmission=data['transmission'],
            badge='Used',
            badge_color='default',
            image=data.get('image_url') or '',
            location=data.get('location') or '',
            description=data.get('description') or '',
            owner=owner,
        )
        if data.get('image_file'):
            vehicle.image_file = data['image_file']
        if commit:
            vehicle.save()
        return vehicle
