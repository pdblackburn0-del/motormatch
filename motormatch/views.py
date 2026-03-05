import hashlib
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileForm, SellForm
from .models import Bid, Message, Notification, Review, SavedVehicle, UserProfile, Vehicle


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
            vehicle = form.save(owner=request.user)
            messages.success(request, 'Your listing has been published!')
            return redirect('vehicle_detail', pk=vehicle.pk)

    else:
        form = SellForm()

    return render(request, 'sell.html', {'form': form})


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    my_listings = Vehicle.objects.filter(owner=request.user).order_by('-created_at')
    saved_count = SavedVehicle.objects.filter(user=request.user).count()
    my_bids     = Bid.objects.filter(bidder=request.user).select_related('vehicle').order_by('-created_at')[:10]
    my_messages = Message.objects.filter(recipient=request.user).select_related('sender', 'vehicle').order_by('-created_at')[:5]
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()

    return render(request, 'dashboard.html', {
        'profile': profile,
        'my_listings': my_listings,
        'saved_count': saved_count,
        'my_bids': my_bids,
        'my_messages': my_messages,
        'unread_notifications': unread_notifications,
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


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    # Mark all as read on page visit
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


@login_required
@require_POST
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'ok': True})


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------

@login_required
@require_POST
def add_review(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    rating  = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
        messages.error(request, 'Please select a rating between 1 and 5.')
        return redirect('vehicle_detail', pk=pk)

    Review.objects.update_or_create(
        vehicle=vehicle,
        reviewer=request.user,
        defaults={'rating': int(rating), 'comment': comment},
    )
    messages.success(request, 'Review submitted!')
    return redirect('vehicle_detail', pk=pk)


# ---------------------------------------------------------------------------
# Messaging
# ---------------------------------------------------------------------------

@login_required
def inbox(request):
    received = Message.objects.filter(recipient=request.user).select_related('sender', 'vehicle').order_by('-created_at')
    sent     = Message.objects.filter(sender=request.user).select_related('recipient', 'vehicle').order_by('-created_at')
    # Mark received as read on open
    received.filter(is_read=False).update(is_read=True)
    return render(request, 'inbox.html', {'received': received, 'sent': sent})


@login_required
@require_POST
def send_message(request):
    recipient_id = request.POST.get('recipient_id')
    vehicle_id   = request.POST.get('vehicle_id')
    subject      = request.POST.get('subject', '').strip()
    body         = request.POST.get('body', '').strip()

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if not recipient_id or not body:
        messages.error(request, 'Message body is required.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    recipient = get_object_or_404(User, pk=recipient_id)
    vehicle   = Vehicle.objects.filter(pk=vehicle_id).first() if vehicle_id else None

    msg = Message.objects.create(
        sender=request.user,
        recipient=recipient,
        vehicle=vehicle,
        subject=subject or (f'Re: {vehicle.title}' if vehicle else 'New message'),
        body=body,
    )

    # Notify recipient
    Notification.objects.create(
        user=recipient,
        title='New message',
        message=f'{request.user.email} sent you a message{": " + vehicle.title if vehicle else ""}.',
        notif_type='info',
        url=f'/inbox/',
    )

    messages.success(request, 'Message sent!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


# ---------------------------------------------------------------------------
# Bids
# ---------------------------------------------------------------------------

@login_required
@require_POST
def place_bid(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    amount  = request.POST.get('amount', '').strip()
    note    = request.POST.get('note', '').strip()

    try:
        from decimal import Decimal
        amount_dec = Decimal(amount.replace(',', '').replace('£', ''))
    except Exception:
        messages.error(request, 'Please enter a valid bid amount.')
        return redirect('vehicle_detail', pk=pk)

    bid, created = Bid.objects.update_or_create(
        vehicle=vehicle,
        bidder=request.user,
        defaults={'amount': amount_dec, 'note': note, 'status': 'pending'},
    )

    # Notify the seller
    if vehicle.owner:
        Notification.objects.create(
            user=vehicle.owner,
            title='New bid on your listing',
            message=f'{request.user.email} placed a bid of £{amount_dec:,.0f} on {vehicle.title}.',
            notif_type='success',
            url=f'/vehicle/{vehicle.pk}/',
        )

    messages.success(request, f'Bid of £{amount_dec:,.0f} placed!' if created else f'Bid updated to £{amount_dec:,.0f}.')
    return redirect('vehicle_detail', pk=pk)


@login_required
@require_POST
def respond_bid(request, pk):
    bid    = get_object_or_404(Bid, pk=pk, vehicle__owner=request.user)
    action = request.POST.get('action')  # 'accept' | 'decline' | 'counter'

    if action not in ('accept', 'decline', 'counter'):
        messages.error(request, 'Invalid action.')
        return redirect('dashboard')

    if action == 'counter':
        counter_amount = request.POST.get('counter_amount', '').strip()
        try:
            from decimal import Decimal
            ca = Decimal(counter_amount.replace(',', '').replace('£', ''))
        except Exception:
            messages.error(request, 'Enter a valid counter amount.')
            return redirect('dashboard')
        bid.status = 'countered'
        bid.note   = f'Counter offer: £{ca:,.0f}. ' + (bid.note or '')
        bid.save()
        Notification.objects.create(
            user=bid.bidder,
            title='Counter offer received',
            message=f'A counter offer of £{ca:,.0f} was made on {bid.vehicle.title}.',
            notif_type='info',
            url=f'/vehicle/{bid.vehicle.pk}/',
        )
        messages.success(request, 'Counter offer sent.')
    else:
        bid.status = 'accepted' if action == 'accept' else 'declined'
        bid.save()
        verb = 'accepted' if action == 'accept' else 'declined'
        Notification.objects.create(
            user=bid.bidder,
            title=f'Bid {verb}',
            message=f'Your bid on {bid.vehicle.title} was {verb}.',
            notif_type='success' if action == 'accept' else 'warning',
            url=f'/vehicle/{bid.vehicle.pk}/',
        )
        messages.success(request, f'Bid {verb}.')

    return redirect('dashboard')


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