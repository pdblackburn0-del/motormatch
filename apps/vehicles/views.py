import concurrent.futures

import hashlib

import json

import re

import urllib.parse

from django.contrib.auth import get_user_model

from motormatch.utils import sanitize_plain_text

from django.core.cache import cache

from django.core.paginator import Paginator

from django.contrib import messages

from django.contrib.auth.decorators import login_required

from django.db.models import Q

from django.http import JsonResponse

from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_POST

from apps.vehicles.models import Bid, SavedVehicle, Vehicle, VehicleImage
from motormatch.utils import validate_image_file

from apps.notifications.models import Notification

from apps.users.models import Review

from decimal import Decimal

from apps.users.middleware import push_recently_viewed, check_rate_limit
from apps.vehicles import services as vehicle_svc

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

_FUELS         = ['Petrol', 'Diesel', 'Hybrid', 'Electric']

_TRANSMISSIONS = ['Manual', 'Automatic']

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

    _home_cached = cache.get('homepage:public')
    if _home_cached is None:
        recently_listed = list(
            Vehicle.objects.filter(is_removed=False).order_by('-created_at')[:12]
        )
        total_listed = Vehicle.objects.filter(is_removed=False).count()
        cache.set('homepage:public', {'recently_listed': recently_listed, 'total_listed': total_listed}, 120)
    else:
        recently_listed = _home_cached['recently_listed']
        total_listed    = _home_cached['total_listed']

    return render(request, 'pages/home.html', {

        'body_types':      body_types,

        'featured_cars':   vehicles[:4],

        'recently_listed': recently_listed[:4],

        'remaining_cars':  recently_listed[4:],

        'query':           query,

        'saved_pks':       saved_pks,

        'total_listed':    total_listed,

    })

def vehicle_detail(request, pk):

    _vd_key = f'vd:{pk}'
    _public = cache.get(_vd_key)
    if _public is None:
        car = get_object_or_404(Vehicle, pk=pk)
        _seller_reviews    = []
        _seller_avg        = None
        _seller_badge_info = None
        if car.owner:
            _seller_reviews    = list(car.owner.reviews_received.select_related('reviewer__profile').all())
            _prof              = getattr(car.owner, 'profile', None)
            _seller_avg        = _prof.average_rating() if _prof else None
            _seller_badge_info = _prof.get_badge_info() if _prof else None
        _car_bids    = list(car.bids.select_related('bidder', 'bidder__profile').order_by('-amount'))
        _accepted_bid = next((b for b in _car_bids if b.status == 'accepted'), None)
        _extra_images = list(car.images.all())
        _public = {
            'car':               car,
            'seller_reviews':    _seller_reviews,
            'seller_avg':        _seller_avg,
            'seller_badge_info': _seller_badge_info,
            'car_bids':          _car_bids,
            'accepted_bid':      _accepted_bid,
            'extra_images':      _extra_images,
        }
        cache.set(_vd_key, _public, 300)
    else:
        car = _public['car']

    is_saved = (
        request.user.is_authenticated
        and SavedVehicle.objects.filter(user=request.user, vehicle=car).exists()
    )

    user_already_reviewed = (
        request.user.is_authenticated and car.owner
        and car.owner.reviews_received.filter(reviewer=request.user).exists()
    )

    user_bid = car.bids.filter(bidder=request.user).first() if request.user.is_authenticated else None

    if request.user.is_authenticated:

        push_recently_viewed(request.user.pk, car.pk)

    return render(request, 'vehicles/vehicle_detail.html', {

        'car':                   car,

        'is_saved':              is_saved,

        'seller_reviews':        _public['seller_reviews'],

        'seller_avg':            _public['seller_avg'],

        'user_already_reviewed': user_already_reviewed,

        'car_bids':              _public['car_bids'],

        'user_bid':              user_bid,

        'accepted_bid':          _public['accepted_bid'],

        'seller_badge_info':     _public['seller_badge_info'],

        'extra_images':          _public['extra_images'],

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

@require_POST

def clear_saved_vehicles(request):

    SavedVehicle.objects.filter(user=request.user).delete()

    return JsonResponse({'ok': True})

def browse(request):

    qs = Vehicle.objects.filter(is_removed=False, listing_status__in=[
        Vehicle.STATUS_ACTIVE, Vehicle.STATUS_PENDING_SALE,
    ])

    q            = request.GET.get('q', '').strip()

    fuel         = request.GET.get('fuel', '').strip()

    transmission = request.GET.get('transmission', '').strip()

    year_from    = request.GET.get('year_from', '').strip()

    year_to      = request.GET.get('year_to', '').strip()

    badge        = request.GET.get('badge', '').strip()

    sort         = request.GET.get('sort', '-created_at')

    if q:

        qs = qs.filter(Q(title__icontains=q) | Q(variant__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q))

    if fuel:

        qs = qs.filter(fuel__iexact=fuel)

    if transmission:

        qs = qs.filter(transmission__iexact=transmission)

    if year_from:

        qs = qs.filter(year__gte=year_from)

    if year_to:

        qs = qs.filter(year__lte=year_to)

    if badge:

        qs = qs.filter(badge__icontains=badge)

    sort_options = {

        '-created_at': '-created_at',

        'created_at':  'created_at',

        '-year':       '-year',

        'year':        'year',

        'title':       'title',

    }

    qs = qs.order_by(sort_options.get(sort, '-created_at'))

    _browse_key = 'browse:qs:' + hashlib.md5(
        json.dumps({'q': q, 'fuel': fuel, 'transmission': transmission,
                    'year_from': year_from, 'year_to': year_to,
                    'badge': badge, 'sort': sort}, sort_keys=True).encode()
    ).hexdigest()
    _browse_cached = cache.get(_browse_key)
    if _browse_cached is None:
        vehicles_list = list(qs)
        total = len(vehicles_list)
        cache.set(_browse_key, {'vehicles': vehicles_list, 'total': total}, 300)
    else:
        vehicles_list = _browse_cached['vehicles']
        total         = _browse_cached['total']

    paginator = Paginator(vehicles_list, 12)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    _qp = {k: v for k, v in {
        'q': q, 'fuel': fuel, 'transmission': transmission,
        'year_from': year_from, 'year_to': year_to,
        'badge': badge, 'sort': sort,
    }.items() if v and (k != 'sort' or v != '-created_at')}
    query_string = urllib.parse.urlencode(_qp)

    saved_pks = set()

    if request.user.is_authenticated:

        saved_pks = set(SavedVehicle.objects.filter(user=request.user).values_list('vehicle_id', flat=True))

    _facets = cache.get('browse:facets')
    if _facets is None:
        _base = Vehicle.objects.filter(is_removed=False)
        fuels         = sorted(set(_base.exclude(fuel='').values_list('fuel', flat=True)))
        transmissions = sorted(set(_base.exclude(transmission__isnull=True).exclude(transmission='').values_list('transmission', flat=True)))
        years         = sorted(set(_base.exclude(year__isnull=True).exclude(year='').values_list('year', flat=True)), reverse=True)
        cache.set('browse:facets', {'fuels': fuels, 'transmissions': transmissions, 'years': years}, 600)
    else:
        fuels         = _facets['fuels']
        transmissions = _facets['transmissions']
        years         = _facets['years']

    return render(request, 'vehicles/browse.html', {

        'vehicles':      page_obj.object_list,

        'page_obj':      page_obj,

        'query_string':  query_string,

        'saved_pks':     saved_pks,

        'fuels':         fuels,

        'transmissions': transmissions,

        'years':         years,

        'q':             q,

        'fuel':          fuel,

        'transmission':  transmission,

        'year_from':     year_from,

        'year_to':       year_to,

        'badge':         badge,

        'sort':          sort,

        'total':         total,

    })

@login_required

def sell(request):

    from apps.vehicles.forms import SellForm

    if request.method == 'POST':

        form = SellForm(request.POST, request.FILES)

        if form.is_valid():

            vehicle = form.save(owner=request.user)
            vehicle_svc.process_extra_photos(vehicle, request.FILES.getlist('extra_photos'))
            vehicle_svc.invalidate_listing_caches()
            messages.success(request, 'Your listing has been published!')
            return redirect('vehicle_detail', pk=vehicle.pk)

    else:

        form = SellForm()

    return render(request, 'vehicles/sell.html', {'form': form})

@login_required

def save_vehicle(request, pk):

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
    from django import forms as dj_forms

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    if request.method == 'POST':

        cover_file = request.FILES.get('image_file')
        cover_error = None
        if cover_file:
            try:
                validate_image_file(cover_file)
                cover_file.seek(0)
            except dj_forms.ValidationError as exc:
                cover_error = exc

        files = request.FILES if not cover_error else {}
        form = VehicleEditForm(request.POST, files, instance=vehicle)
        form_valid = form.is_valid()
        if cover_error:
            form.add_error('image_file', cover_error)

        if form_valid and not cover_error:

            form.save()
            vehicle_svc.add_photos_to_vehicle(
                vehicle,
                new_photos=request.FILES.getlist('new_photos'),
                delete_ids=request.POST.getlist('delete_image'),
            )
            vehicle_svc.invalidate_listing_caches(vehicle_pk=vehicle.pk)
            messages.success(request, 'Listing updated successfully.')
            return redirect('vehicle_detail', pk=vehicle.pk)

    else:

        form = VehicleEditForm(instance=vehicle)

    return render(request, 'vehicles/edit_vehicle.html', {'form': form, 'vehicle': vehicle})

@login_required

@require_POST

def delete_vehicle(request, pk):

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    vehicle.is_removed    = True

    vehicle.listing_status = Vehicle.STATUS_REMOVED

    vehicle.save(update_fields=['is_removed', 'listing_status'])

    vehicle_svc.invalidate_listing_caches(vehicle_pk=vehicle.pk)

    messages.success(request, 'Listing removed successfully.')

    return redirect('dashboard')

@login_required

@require_POST

def hard_delete_vehicle(request, pk):

    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)

    title = vehicle.title

    vehicle.delete()

    vehicle_svc.invalidate_listing_caches(vehicle_pk=pk)

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

    comment = sanitize_plain_text(request.POST.get('comment', '').strip())

    if not rating or not rating.isdigit() or not (1 <= int(rating) <= 5):

        messages.error(request, 'Please select a rating between 1 and 5.')

        return redirect('vehicle_detail', pk=pk)

    vehicle_svc.submit_review(request.user, vehicle, int(rating), comment)

    messages.success(request, 'Review submitted!')

    return redirect('vehicle_detail', pk=pk)


@login_required

@require_POST

def place_bid(request, pk):

    vehicle = get_object_or_404(Vehicle, pk=pk)

    if check_rate_limit(request.user.pk, 'place_bid', max_count=5, window=600):

        messages.error(request, 'You are placing bids too quickly. Please wait a moment before trying again.')

        return redirect('vehicle_detail', pk=pk)

    amount = request.POST.get('amount', '').strip()

    note = request.POST.get('note', '').strip()

    try:

        amount_dec = Decimal(amount.replace(',', '').replace('£', ''))

    except Exception:

        messages.error(request, 'Please enter a valid bid amount.')

        return redirect('vehicle_detail', pk=pk)

    try:

        bid, created = vehicle_svc.place_bid(request.user, vehicle, amount_dec, note)

    except ValueError as exc:

        messages.error(request, str(exc))

        return redirect('vehicle_detail', pk=pk)

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

    if action == 'counter':

        counter_str = request.POST.get('counter_amount', '').strip()

        try:

            ca = Decimal(counter_str.replace(',', '').replace('£', ''))

        except Exception:

            messages.error(request, 'Enter a valid counter amount.')

            return redirect('dashboard')

        vehicle_svc.respond_bid(
            request.user, bid, action,
            counter_amount=ca,
            counter_note=request.POST.get('counter_note', '').strip(),
        )
        messages.success(request, f'Counter offer of £{ca:,.0f} sent.')

    else:

        vehicle_svc.respond_bid(request.user, bid, action)
        verb = 'accepted' if action == 'accept' else 'declined'
        messages.success(request, f'Bid {verb}.')

    return redirect('dashboard')

@login_required

@require_POST

def bidder_respond_bid(request, pk):

    bid    = get_object_or_404(Bid, pk=pk, bidder=request.user, status='countered')

    action = request.POST.get('action')

    try:

        vehicle_svc.bidder_respond_bid(request.user, bid, action)

    except ValueError:

        messages.error(request, 'Invalid action.')

        return redirect('dashboard')

    if action == 'accept_counter':

        messages.success(request, f'You accepted the counter offer of £{bid.amount:,.0f}.')

    else:

        messages.success(request, 'You declined the counter offer.')

    return redirect('dashboard')


def seller_profile(request, pk):
    User = get_user_model()
    seller = get_object_or_404(User, pk=pk)
    seller_profile_obj = getattr(seller, 'profile', None)
    listings = Vehicle.objects.filter(owner=seller, is_removed=False).order_by('-created_at')
    reviews = seller.reviews_received.select_related('reviewer__profile').order_by('-created_at')
    avg = seller_profile_obj.average_rating() if seller_profile_obj else None

    if seller_profile_obj and seller_profile_obj.is_deleted:
        display_state = 'deleted'
    elif not seller.is_active and not getattr(seller_profile_obj, 'suspension_until', None):
        display_state = 'banned'
    elif seller_profile_obj and seller_profile_obj.is_suspended:
        display_state = 'suspended'
    else:
        display_state = 'active'

    return render(request, 'users/seller_profile.html', {
        'seller': seller,
        'seller_profile': seller_profile_obj,
        'listings': listings,
        'reviews': reviews,
        'avg': avg,
        'display_state': display_state,
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


def about(request):
    return render(request, 'legal/about.html')


def terms(request):
    return render(request, 'legal/terms.html')


def privacy(request):
    return render(request, 'legal/privacy.html')
