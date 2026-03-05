import concurrent.futures
import hashlib
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.vehicles.models import Bid, SavedVehicle, Vehicle
from apps.notifications.models import Notification
from apps.users.models import Review


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
_ENGINES       = ['1.0', '1.2', '1.4', '1.6', '1.8', '2.0', '2.5', '3.0']
_CO2           = [89, 99, 109, 119, 129, 139, 149, 179]

_VRM_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix='dvla_lookup')


def index(request):
    query = request.GET.get('q', '').strip()
    body_types = [
        {'name': 'SUV',         'icon': 'bi bi-truck'},
        {'name': 'Sedan',       'icon': 'bi bi-car-front'},
        {'name': 'Hatchback',   'icon': 'bi bi-car-front-fill'},
        {'name': 'Truck',       'icon': 'bi bi-truck-flatbed'},
        {'name': 'Coupe',       'icon': 'bi bi-lightning-charge'},
        {'name': 'Convertible', 'icon': 'bi bi-wind'},
    ]

    vehicles = Vehicle.objects.filter(is_removed=False)
    if query:
        vehicles = vehicles.filter(
            Q(title__icontains=query)
            | Q(variant__icontains=query)
            | Q(fuel__icontains=query)
            | Q(transmission__icontains=query)
        )

    saved_pks = set()
    if request.user.is_authenticated:
        saved_pks = set(SavedVehicle.objects.filter(user=request.user).values_list('vehicle_id', flat=True))

    recently_listed = Vehicle.objects.filter(is_removed=False).order_by('-created_at')[:12]
    total_listed    = Vehicle.objects.filter(is_removed=False).count()
    return render(request, 'pages/home.html', {
        'body_types':      body_types,
        'featured_cars':   vehicles[:4],
        'recently_listed': recently_listed[:4],
        'remaining_cars':  list(recently_listed[4:]),
        'query':           query,
        'saved_pks':       saved_pks,
        'total_listed':    total_listed,
    })


def vehicle_detail(request, pk):
    car = get_object_or_404(Vehicle, pk=pk)
    is_saved = (
        request.user.is_authenticated
        and SavedVehicle.objects.filter(user=request.user, vehicle=car).exists()
    )

    seller_reviews    = []
    seller_avg        = None
    seller_badge_info = None
    if car.owner:
        seller_reviews    = car.owner.reviews_received.select_related('reviewer__profile').all()
        prof              = getattr(car.owner, 'profile', None)
        seller_avg        = prof.average_rating() if prof else None
        seller_badge_info = prof.get_badge_info() if prof else None

    user_already_reviewed = (
        request.user.is_authenticated and car.owner
        and car.owner.reviews_received.filter(reviewer=request.user).exists()
    )

    car_bids     = car.bids.select_related('bidder', 'bidder__profile').order_by('-amount')
    user_bid     = car.bids.filter(bidder=request.user).first() if request.user.is_authenticated else None
    accepted_bid = car.bids.filter(status='accepted').select_related('bidder', 'bidder__profile').first()

    return render(request, 'vehicles/vehicle_detail.html', {
        'car':                   car,
        'is_saved':              is_saved,
        'seller_reviews':        seller_reviews,
        'seller_avg':            seller_avg,
        'user_already_reviewed': user_already_reviewed,
        'car_bids':              car_bids,
        'user_bid':              user_bid,
        'accepted_bid':          accepted_bid,
        'seller_badge_info':     seller_badge_info,
    })


def comparison(request):
    car1_id = request.GET.get('car1')
    car2_id = request.GET.get('car2')
    all_vehicles = Vehicle.objects.all().order_by('title')
    car1  = Vehicle.objects.filter(pk=car1_id).first() if car1_id else None
    car2  = Vehicle.objects.filter(pk=car2_id).first() if car2_id else None
    cars  = [c for c in (car1, car2) if c]
    return render(request, 'vehicles/comparison.html', {
        'all_vehicles': all_vehicles,
        'car1': car1, 'car2': car2, 'cars': cars,
    })


@login_required
def saved(request):
    saved_records = SavedVehicle.objects.filter(user=request.user).select_related('vehicle').order_by('-saved_at')
    return render(request, 'vehicles/saved.html', {'saved_records': saved_records})


@login_required
def sell(request):
    from apps.vehicles.forms import SellForm
    if request.method == 'POST':
        form = SellForm(request.POST, request.FILES)
        if form.is_valid():
            vehicle = form.save(owner=request.user)
            messages.success(request, 'Your listing has been published!')
            return redirect('vehicle_detail', pk=vehicle.pk)
    else:
        form = SellForm()
    return render(request, 'vehicles/sell.html', {'form': form})


@login_required
def save_vehicle(request, pk):
    from django.http import JsonResponse
    vehicle = get_object_or_404(Vehicle, pk=pk)
    obj, created = SavedVehicle.objects.get_or_create(user=request.user, vehicle=vehicle)
    if not created:
        obj.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'saved': created})
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def edit_vehicle(request, pk):
    from apps.vehicles.forms import VehicleEditForm
    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = VehicleEditForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing updated successfully.')
            return redirect('vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleEditForm(instance=vehicle)
    return render(request, 'vehicles/edit_vehicle.html', {'form': form, 'vehicle': vehicle})


@login_required
@require_POST
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
    vehicle.is_removed = True
    vehicle.save(update_fields=['is_removed'])
    messages.success(request, 'Listing removed successfully.')
    return redirect('dashboard')


@login_required
@require_POST
def hard_delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
    title = vehicle.title
    vehicle.delete()
    messages.success(request, f'Listing "{title}" has been permanently deleted.')
    return redirect('dashboard')


@login_required
@require_POST
def add_review(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk)
    seller  = vehicle.owner

    if not seller:
        messages.error(request, 'This listing has no seller to review.')
        return redirect('vehicle_detail', pk=pk)
    if seller == request.user:
        messages.error(request, "You can't review your own listing.")
        return redirect('vehicle_detail', pk=pk)

    rating  = request.POST.get('rating')
    comment = request.POST.get('comment', '').strip()

    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):
        messages.error(request, 'Please select a rating between 1 and 5.')
        return redirect('vehicle_detail', pk=pk)

    _, created = Review.objects.update_or_create(
        reviewed_user=seller,
        reviewer=request.user,
        defaults={'rating': int(rating), 'comment': comment},
    )

    reviewer_name = (
        request.user.profile.get_display_name()
        if hasattr(request.user, 'profile')
        else request.user.email.split('@')[0]
    )
    verb = 'left' if created else 'updated'
    Notification.objects.create(
        user=seller,
        title='New review on your profile',
        message=f'{reviewer_name} {verb} you a {rating}★ review.',
        notif_type=Notification.TYPE_SUCCESS if int(rating) >= 4 else Notification.TYPE_INFO,
        url=f'/vehicle/{pk}/',
    )
    messages.success(request, 'Review submitted!')
    return redirect('vehicle_detail', pk=pk)


@login_required
@require_POST
def place_bid(request, pk):
    from decimal import Decimal
    vehicle = get_object_or_404(Vehicle, pk=pk)

    if vehicle.is_removed:
        messages.error(request, 'This listing has been removed and is no longer accepting bids.')
        return redirect('vehicle_detail', pk=pk)
    if vehicle.bids.filter(status='accepted').exists():
        messages.error(request, 'A bid has already been accepted on this listing.')
        return redirect('vehicle_detail', pk=pk)

    amount = request.POST.get('amount', '').strip()
    note   = request.POST.get('note', '').strip()

    try:
        amount_dec = Decimal(amount.replace(',', '').replace('£', ''))
    except Exception:
        messages.error(request, 'Please enter a valid bid amount.')
        return redirect('vehicle_detail', pk=pk)

    highest = (
        vehicle.bids
        .exclude(bidder=request.user)
        .exclude(status__in=['declined'])
        .order_by('-amount')
        .values_list('amount', flat=True)
        .first()
    )
    if highest and amount_dec <= highest:
        messages.error(request, f'Your bid must be higher than the current top bid of £{highest:,.0f}.')
        return redirect('vehicle_detail', pk=pk)

    bid, created = Bid.objects.update_or_create(
        vehicle=vehicle,
        bidder=request.user,
        defaults={'amount': amount_dec, 'note': note, 'status': 'pending'},
    )

    if vehicle.owner:
        bidder_name = (
            request.user.profile.get_display_name()
            if hasattr(request.user, 'profile')
            else request.user.email.split('@')[0]
        )
        Notification.objects.create(
            user=vehicle.owner,
            title='New bid on your listing',
            message=f'{bidder_name} placed a bid of £{amount_dec:,.0f} on {vehicle.title}.',
            notif_type='success',
            url=f'/vehicle/{vehicle.pk}/',
        )

    messages.success(request, f'Bid of £{amount_dec:,.0f} placed!' if created else f'Bid updated to £{amount_dec:,.0f}.')
    return redirect('vehicle_detail', pk=pk)


@login_required
@require_POST
def respond_bid(request, pk):
    bid    = get_object_or_404(Bid, pk=pk, vehicle__owner=request.user)
    action = request.POST.get('action')

    if action not in ('accept', 'decline', 'counter'):
        messages.error(request, 'Invalid action.')
        return redirect('dashboard')

    seller_name = (
        request.user.profile.get_display_name()
        if hasattr(request.user, 'profile')
        else request.user.email.split('@')[0]
    )

    if action == 'counter':
        from decimal import Decimal
        counter_str = request.POST.get('counter_amount', '').strip()
        try:
            ca = Decimal(counter_str.replace(',', '').replace('£', ''))
        except Exception:
            messages.error(request, 'Enter a valid counter amount.')
            return redirect('dashboard')
        bid.status         = 'countered'
        bid.counter_amount = ca
        bid.note           = request.POST.get('counter_note', '').strip() or bid.note
        bid.save()
        Notification.objects.create(
            user=bid.bidder,
            title='Counter offer received',
            message=f'{seller_name} countered with £{ca:,.0f} on {bid.vehicle.title}. Go to your dashboard to respond.',
            notif_type='info',
            url='/dashboard/#bids-section',
        )
        messages.success(request, f'Counter offer of £{ca:,.0f} sent.')
    else:
        bid.status = 'accepted' if action == 'accept' else 'declined'
        bid.save()
        verb = 'accepted' if action == 'accept' else 'declined'
        Notification.objects.create(
            user=bid.bidder,
            title=f'Bid {verb}',
            message=f'{seller_name} {verb} your bid of £{bid.amount:,.0f} on {bid.vehicle.title}.',
            notif_type='success' if action == 'accept' else 'warning',
            url=f'/vehicle/{bid.vehicle.pk}/',
        )
        messages.success(request, f'Bid {verb}.')

    return redirect('dashboard')


@login_required
@require_POST
def bidder_respond_bid(request, pk):
    bid    = get_object_or_404(Bid, pk=pk, bidder=request.user, status='countered')
    action = request.POST.get('action')

    bidder_name = (
        request.user.profile.get_display_name()
        if hasattr(request.user, 'profile')
        else request.user.email.split('@')[0]
    )

    if action == 'accept_counter':
        if bid.counter_amount:
            bid.amount = bid.counter_amount
        bid.status         = 'accepted'
        bid.counter_amount = None
        bid.save()
        if bid.vehicle.owner:
            Notification.objects.create(
                user=bid.vehicle.owner,
                title='Counter offer accepted',
                message=f'{bidder_name} accepted your counter offer of £{bid.amount:,.0f} on {bid.vehicle.title}.',
                notif_type='success',
                url=f'/vehicle/{bid.vehicle.pk}/',
            )
        messages.success(request, f'You accepted the counter offer of £{bid.amount:,.0f}.')
    elif action == 'decline':
        bid.status = 'declined'
        bid.save()
        if bid.vehicle.owner:
            Notification.objects.create(
                user=bid.vehicle.owner,
                title='Counter offer declined',
                message=f'{bidder_name} declined your counter offer on {bid.vehicle.title}.',
                notif_type='warning',
                url=f'/vehicle/{bid.vehicle.pk}/',
            )
        messages.success(request, 'You declined the counter offer.')
    else:
        messages.error(request, 'Invalid action.')

    return redirect('dashboard')


def seller_profile(request, pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    seller             = get_object_or_404(User, pk=pk)
    seller_profile_obj = getattr(seller, 'profile', None)
    listings           = Vehicle.objects.filter(owner=seller, is_removed=False).order_by('-created_at')
    reviews            = seller.reviews_received.select_related('reviewer__profile').order_by('-created_at')
    avg                = seller_profile_obj.average_rating() if seller_profile_obj else None
    return render(request, 'users/seller_profile.html', {
        'seller':         seller,
        'seller_profile': seller_profile_obj,
        'listings':       listings,
        'reviews':        reviews,
        'avg':            avg,
    })


def _do_vrm_lookup(reg):
    seed  = int(hashlib.md5(reg.encode()).hexdigest(), 16)
    make  = _MAKES[seed % len(_MAKES)]
    model = _MODELS[make][(seed // len(_MAKES)) % len(_MODELS[make])]
    return {
        'reg':          reg,
        'make':         make,
        'model':        model,
        'year':         2005 + (seed % 19),
        'fuel':         _FUELS[seed % len(_FUELS)],
        'transmission': _TRANSMISSIONS[seed % len(_TRANSMISSIONS)],
        'colour':       _COLOURS[seed % len(_COLOURS)],
        'engine':       _ENGINES[seed % len(_ENGINES)] + 'L',
        'co2_gkm':      _CO2[seed % len(_CO2)],
        'mileage':      f'{(seed % 150) * 1000 + 5000:,} mi',
        'source':       'motormatch',
    }


def dvla_lookup(request):
    from django.core.cache import cache as _cache
    from django.http import JsonResponse

    ip     = (request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '')).split(',')[0].strip() or '127.0.0.1')
    rl_key = f'dvla_rl_{ip}'
    count  = _cache.get(rl_key, 0)
    if count >= 20:
        return JsonResponse({'error': 'Rate limit exceeded. Please try again in 10 minutes.', 'retry_after': 600}, status=429)
    _cache.set(rl_key, count + 1, timeout=600)

    reg = request.GET.get('reg', '').replace(' ', '').upper()
    if not reg:
        return JsonResponse({'error': 'No registration provided.'}, status=400)
    if not re.match(r'^[A-Z0-9]{2,8}$', reg):
        return JsonResponse({'error': 'Invalid registration. Must be 2–8 letters/digits (spaces are ignored).'}, status=400)

    try:
        future = _VRM_EXECUTOR.submit(_do_vrm_lookup, reg)
        data   = future.result(timeout=5)
        return JsonResponse(data)
    except concurrent.futures.TimeoutError:
        return JsonResponse({'error': 'Lookup timed out. Please try again.'}, status=503)
    except Exception:
        return JsonResponse({'error': 'Lookup failed. Please try again.'}, status=500)
