from django import forms
from .models import Vehicle

FUEL_CHOICES = [
    ('Petrol', 'Petrol'),
    ('Diesel', 'Diesel'),
    ('Hybrid', 'Hybrid'),
    ('Electric', 'Electric'),
    ('Plug-in Hybrid', 'Plug-in Hybrid'),
]

TRANSMISSION_CHOICES = [
    ('Automatic', 'Automatic'),
    ('Manual', 'Manual'),
    ('Semi-Automatic', 'Semi-Automatic'),
]


class SellForm(forms.Form):
    make         = forms.CharField(max_length=100, label='Make', widget=forms.TextInput(attrs={'placeholder': 'e.g., Ford', 'class': 'form-control'}))
    model        = forms.CharField(max_length=100, label='Model', widget=forms.TextInput(attrs={'placeholder': 'e.g., Fiesta', 'class': 'form-control'}))
    variant      = forms.CharField(max_length=200, label='Variant / Trim', required=False, widget=forms.TextInput(attrs={'placeholder': 'e.g., Sport Sedan 4D', 'class': 'form-control'}))
    year         = forms.IntegerField(label='Year', min_value=1900, max_value=2099, widget=forms.NumberInput(attrs={'placeholder': 'e.g., 2022', 'class': 'form-control'}))
    price        = forms.DecimalField(max_digits=10, decimal_places=2, label='Asking Price (£)', widget=forms.NumberInput(attrs={'placeholder': '5000', 'class': 'form-control'}))
    mileage      = forms.CharField(max_length=50, label='Mileage', widget=forms.TextInput(attrs={'placeholder': 'e.g., 32k mi', 'class': 'form-control'}))
    fuel         = forms.ChoiceField(choices=FUEL_CHOICES, label='Fuel Type', widget=forms.Select(attrs={'class': 'form-select'}))
    transmission = forms.ChoiceField(choices=TRANSMISSION_CHOICES, label='Transmission', widget=forms.Select(attrs={'class': 'form-select'}))
    image_file   = forms.ImageField(label='Main Photo', required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    image_url    = forms.URLField(label='Or paste an image URL', required=False, widget=forms.URLInput(attrs={'placeholder': 'https://...', 'class': 'form-control'}))

    def save(self, commit=True):
        data = self.cleaned_data
        vehicle = Vehicle(
            title=f"{data['year']} {data['make']} {data['model']}",
            variant=data.get('variant') or '',
            price=f"£{data['price']:,.0f}",
            mileage=data['mileage'],
            year=str(data['year']),
            fuel=data['fuel'],
            transmission=data['transmission'],
            badge='Used',
            badge_color='default',
            image=data.get('image_url') or '',
        )
        if data.get('image_file'):
            vehicle.image_file = data['image_file']
        if commit:
            vehicle.save()
        return vehicle
