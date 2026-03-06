from django import forms

from allauth.account.forms import SignupForm

from .models import Vehicle, UserProfile

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

class VehicleEditForm(forms.ModelForm):

    image = forms.CharField(

        required=False,

        label='Image URL (alternative to upload)',

        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'https://...'})

    )

    class Meta:

        model = Vehicle

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

            'image_file':   forms.ClearableFileInput(attrs={'class': 'form-control'}),

        }

        labels = {

            'image': 'Image URL (alternative to upload)',

        }

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

    image_url    = forms.CharField(label='Or paste an image URL', required=False, widget=forms.TextInput(attrs={'placeholder': 'https://...', 'class': 'form-control'}))

    location     = forms.CharField(max_length=100, required=False, label='Location', widget=forms.TextInput(attrs={'placeholder': 'e.g. London, UK', 'class': 'form-control'}))

    description  = forms.CharField(required=False, label='Description', widget=forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Tell buyers about the car — service history, modifications, reason for sale...'}))

    def save(self, owner=None, commit=True):

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

            location=data.get('location') or '',

            description=data.get('description') or '',

            owner=owner,

        )

        if data.get('image_file'):

            vehicle.image_file = data['image_file']

        if commit:

            vehicle.save()

        return vehicle

class CustomSignupForm(SignupForm):

    """
    Extends allauth's SignupForm to capture first and last name.
    allauth calls .save(request) after its own save, so we hook in there.
    """

    first_name = forms.CharField(

        max_length=100,

        label='First Name',

        widget=forms.TextInput(attrs={'placeholder': 'John', 'class': 'form-control py-2'}),

    )

    last_name = forms.CharField(

        max_length=100,

        label='Last Name',

        widget=forms.TextInput(attrs={'placeholder': 'Doe', 'class': 'form-control py-2'}),

    )

    phone = forms.CharField(

        max_length=30,

        label='Phone Number',

        required=False,

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
