import hashlib
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ProfileForm, SellForm
from .models import SavedVehicle, UserProfile, Vehicle


def index(request):
    query = request.GET.get('q', '').strip()

    body_types = [
        {'name': 'SUV', 'icon': 'bi bi-truck'},
        {'name': 'Sedan', 'icon': 'bi bi-car-front'},
        {'name': 'Hatchback', 'icon': 'bi bi-car-front-fill'},
        {'name': 'Truck', 'icon': 'bi bi-truck-flatbed'},
        {'name': 'Coupe', 'icon': 'bi bi-lightning-charge'},
        {'name': 'Convertible', 'icon': 'bi bi-wind'},
    ]

    vehicles = Vehicle.objects.all()

    if query:
        vehicles = vehicles.filter(
            Q(title__icontains=query)
            | Q(variant__icontains=query)
            | Q(fuel__icontains=query)
            | Q(transmission__icontains=query)
        )

    saved_pks = set()

    if request.user.is_authenticated:
        saved_pks = set(
            SavedVehicle.objects.filter(user=request.user)
            .values_list('vehicle_id', flat=True)
        )

    featured_cars = vehicles[:4]
    recommended_cars = vehicles[:4]
    remaining_cars = vehicles[4:]

    return render(request, 'home.html', {
        'body_types': body_types,
        'featured_cars': featured_cars,
        'recommended_cars': recommended_cars,
        'remaining_cars': remaining_cars,
        'query': query,
        'saved_pks': saved_pks,
    })


def vehicle_detail(request, pk):
    car = get_object_or_404(Vehicle, pk=pk)

    is_saved = (
        request.user.is_authenticated
        and SavedVehicle.objects.filter(user=request.user, vehicle=car).exists()
    )

    return render(request, 'vehicle_detail.html', {
        'car': car,
        'is_saved': is_saved,
    })


def comparison(request):
    car1_specs = [
        {'label': 'Engine/Motor', 'icon': 'bi bi-cpu', 'value': 'Electric Dual Motor'},
        {'label': 'Mileage', 'icon': 'bi bi-speedometer2', 'value': '24,000 mi'},
        {'label': 'Fuel Type', 'icon': 'bi bi-fuel-pump', 'value': 'Electric'},
        {'label': 'Transmission', 'icon': 'bi bi-gear', 'value': '1-Speed Auto'},
        {'label': 'Drivetrain', 'icon': 'bi bi-arrows-move', 'value': 'AWD'},
        {'label': 'Horsepower', 'icon': 'bi bi-lightning-charge', 'value': '450 hp'},
        {'label': 'Seating', 'icon': 'bi bi-person', 'value': '5 Passengers'},
    ]

    car2_specs = [
        {'label': 'Engine/Motor', 'icon': 'bi bi-cpu', 'value': '2.0L Turbo Inline-4'},
        {'label': 'Mileage', 'icon': 'bi bi-speedometer2', 'value': '15,000 mi'},
        {'label': 'Fuel Type', 'icon': 'bi bi-fuel-pump', 'value': 'Hybrid'},
        {'label': 'Transmission', 'icon': 'bi bi-gear', 'value': '7-Speed Auto'},
        {'label': 'Drivetrain', 'icon': 'bi bi-arrows-move', 'value': 'AWD'},
        {'label': 'Horsepower', 'icon': 'bi bi-lightning-charge', 'value': '261 hp'},
        {'label': 'Seating', 'icon': 'bi bi-person', 'value': '5 Passengers'},
    ]

    return render(request, 'comparison.html', {
        'car1_specs': car1_specs,
        'car2_specs': car2_specs,
    })


@login_required
def sell(request):
    if request.method == 'POST':
        form = SellForm(request.POST, request.FILES)

        if form.is_valid():
            vehicle = form.save()
            return redirect('vehicle_detail', pk=vehicle.pk)

    else:
        form = SellForm()

    return render(request, 'sell.html', {'form': form})


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    my_listings = Vehicle.objects.filter(owner=request.user)

    saved_count = SavedVehicle.objects.filter(user=request.user).count()

    return render(request, 'dashboard.html', {
        'profile': profile,
        'my_listings': my_listings,
        'saved_count': saved_count,
    })


@login_required
def saved(request):
    saved_vehicles = SavedVehicle.objects.filter(user=request.user)

    return render(request, 'saved.html', {
        'saved_vehicles': saved_vehicles
    })


@login_required
def offers(request):
    offers_list = [
        {'name': 'Michael Johnson', 'amount': '£32,500', 'type': 'Cash Offer'},
        {'name': 'Sarah Anderson', 'amount': '£31,000', 'type': 'Financing'},
        {'name': 'David Kim', 'amount': '£28,000', 'type': 'Cash Offer'},
    ]

    return render(request, 'offers.html', {'offers': offers_list})


def offer_submitted(request):
    return render(request, 'offer_submitted.html')


def enquiry_sent(request):
    return render(request, 'enquiry_sent.html')


@login_required
def save_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    obj, created = SavedVehicle.objects.get_or_create(user=request.user, vehicle=vehicle)
    if not created:
        obj.delete()
    is_saved = created
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': is_saved})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def profile(request):
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=prof)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = ProfileForm(instance=prof)
    return render(request, 'profile.html', {'form': form, 'profile': prof})


_MAKES = ['Ford', 'Vauxhall', 'BMW', 'Audi', 'Toyota', 'Honda', 'Volkswagen',
          'Mercedes-Benz', 'Nissan', 'Hyundai', 'Kia', 'Renault', 'Peugeot',
          'Fiat', 'Volvo', 'Land Rover', 'Mini', 'Skoda', 'Seat', 'Mazda']
_MODELS = {
    'Ford':          ['Fiesta', 'Focus', 'Mondeo', 'Puma', 'Kuga'],
    'Vauxhall':      ['Astra', 'Corsa', 'Insignia', 'Mokka', 'Crossland'],
    'BMW':           ['1 Series', '3 Series', '5 Series', 'X3', 'X5'],
    'Audi':          ['A1', 'A3', 'A4', 'Q3', 'Q5'],
    'Toyota':        ['Yaris', 'Corolla', 'Camry', 'RAV4', 'C-HR'],
    'Honda':         ['Civic', 'Jazz', 'HR-V', 'CR-V', 'Accord'],
    'Volkswagen':    ['Polo', 'Golf', 'Passat', 'Tiguan', 'T-Roc'],
    'Mercedes-Benz': ['A-Class', 'C-Class', 'E-Class', 'GLC', 'GLA'],
    'Nissan':        ['Micra', 'Juke', 'Qashqai', 'Leaf', 'X-Trail'],
    'Hyundai':       ['i10', 'i20', 'i30', 'Tucson', 'Kona'],
    'Kia':           ['Picanto', 'Rio', 'Ceed', 'Sportage', 'Niro'],
    'Renault':       ['Clio', 'Megane', 'Captur', 'Kadjar', 'Zoe'],
    'Peugeot':       ['108', '208', '308', '2008', '3008'],
    'Fiat':          ['500', 'Punto', 'Tipo', '500X', 'Panda'],
    'Volvo':         ['V40', 'V60', 'XC40', 'XC60', 'S90'],
    'Land Rover':    ['Discovery Sport', 'Range Rover Evoque', 'Defender', 'Discovery', 'Freelander'],
    'Mini':          ['Hatch', 'Convertible', 'Clubman', 'Countryman', 'Paceman'],
    'Skoda':         ['Fabia', 'Octavia', 'Superb', 'Karoq', 'Kodiaq'],
    'Seat':          ['Ibiza', 'Leon', 'Arona', 'Ateca', 'Tarraco'],
    'Mazda':         ['Mazda2', 'Mazda3', 'Mazda6', 'CX-3', 'CX-5'],
}
_FUELS         = ['Petrol', 'Diesel', 'Hybrid', 'Electric', 'Petrol', 'Diesel']
_TRANSMISSIONS = ['Manual', 'Automatic', 'Manual', 'Manual', 'Automatic']
_COLOURS       = ['White', 'Black', 'Silver', 'Grey', 'Blue', 'Red', 'Green', 'Orange']


def dvla_lookup(request):
    reg = request.GET.get('reg', '').replace(' ', '').upper()
    if not reg:
        return JsonResponse({'error': 'No registration provided.'}, status=400)
    valid = bool(
        re.match(r'^[A-Z]{2}\d{2}[A-Z]{3}$', reg)
        or re.match(r'^[A-Z]\d{3}[A-Z]{3}$', reg)
        or re.match(r'^[A-Z]{3}\d{3}[A-Z]$', reg)
    )
    if not valid:
        return JsonResponse({'error': 'Enter a valid UK registration (e.g. AB12 CDE).'}, status=400)
    seed    = int(hashlib.md5(reg.encode()).hexdigest(), 16)
    make    = _MAKES[seed % len(_MAKES)]
    model   = _MODELS[make][(seed // len(_MAKES)) % len(_MODELS[make])]
    year    = 2005 + (seed % 19)
    fuel    = _FUELS[seed % len(_FUELS)]
    trans   = _TRANSMISSIONS[seed % len(_TRANSMISSIONS)]
    colour  = _COLOURS[seed % len(_COLOURS)]
    mileage = f'{(seed % 150) * 1000 + 5000:,} mi'
    return JsonResponse({
        'make': make, 'model': model, 'year': year,
        'fuel': fuel, 'transmission': trans,
        'colour': colour, 'mileage': mileage, 'reg': reg,
    })