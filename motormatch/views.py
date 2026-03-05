import hashlib
import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProfileForm, SellForm, VehicleEditForm
from .models import Bid, LoginEvent, Message, Notification, Review, SavedVehicle, UserProfile, Vehicle


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

    seller_reviews = []
    seller_avg     = None
    if car.owner:
        seller_reviews = car.owner.reviews_received.select_related('reviewer__profile').all()
        prof = getattr(car.owner, 'profile', None)
        seller_avg = prof.average_rating() if prof else None

    user_already_reviewed = (
        request.user.is_authenticated and car.owner
        and car.owner.reviews_received.filter(reviewer=request.user).exists()
    )

    return render(request, 'vehicle_detail.html', {
        'car': car,
        'is_saved': is_saved,
        'seller_reviews': seller_reviews,
        'seller_avg': seller_avg,
        'user_already_reviewed': user_already_reviewed,
    })


def comparison(request):
    car1_id = request.GET.get('car1')
    car2_id = request.GET.get('car2')

    all_vehicles = Vehicle.objects.all().order_by('title')
    car1 = Vehicle.objects.filter(pk=car1_id).first() if car1_id else None
    car2 = Vehicle.objects.filter(pk=car2_id).first() if car2_id else None

    cars = [c for c in (car1, car2) if c]

    return render(request, 'comparison.html', {
        'all_vehicles': all_vehicles,
        'car1': car1,
        'car2': car2,
        'cars': cars,
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
    saved_records = SavedVehicle.objects.filter(user=request.user).select_related('vehicle').order_by('-saved_at')

    return render(request, 'saved.html', {
        'saved_records': saved_records
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


@login_required
def notifications_list(request):
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})


@login_required
@require_POST
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'ok': True})


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

    reviewer_name = request.user.profile.get_display_name() if hasattr(request.user, 'profile') else request.user.email.split('@')[0]
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
def inbox(request):
    received = Message.objects.filter(recipient=request.user).select_related('sender', 'vehicle').order_by('-created_at')
    sent     = Message.objects.filter(sender=request.user).select_related('recipient', 'vehicle').order_by('-created_at')
    received.filter(is_read=False).update(is_read=True)
    return render(request, 'inbox.html', {'received': received, 'sent': sent})


@login_required
@require_POST
def send_message(request, pk=None):
    recipient_id = request.POST.get('recipient_id')
    vehicle_id   = request.POST.get('vehicle_id') or pk
    subject      = request.POST.get('subject', '').strip()
    body         = request.POST.get('body', '').strip()

    from django.contrib.auth import get_user_model
    User = get_user_model()

    if not recipient_id or not body:
        messages.error(request, 'Message body is required.')
        return redirect(request.META.get('HTTP_REFERER', 'home'))

    recipient = get_object_or_404(User, pk=recipient_id)
    vehicle   = Vehicle.objects.filter(pk=vehicle_id).first() if vehicle_id else None

    sender_name = request.user.profile.get_display_name() if hasattr(request.user, 'profile') else request.user.email.split('@')[0]

    Message.objects.create(
        sender=request.user,
        recipient=recipient,
        vehicle=vehicle,
        subject=subject or (f'Re: {vehicle.title}' if vehicle else 'New message'),
        body=body,
    )

    Notification.objects.create(
        user=recipient,
        title='New message',
        message=f'{sender_name} sent you a message{": " + vehicle.title if vehicle else ""}.',
        notif_type='info',
        url='/inbox/',
    )

    messages.success(request, 'Message sent!')
    return redirect(request.META.get('HTTP_REFERER', 'home'))


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

    if vehicle.owner:
        bidder_name = request.user.profile.get_display_name() if hasattr(request.user, 'profile') else request.user.email.split('@')[0]
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


@login_required
def login_event_detail(request, pk):
    event = get_object_or_404(LoginEvent, pk=pk, user=request.user)
    return render(request, 'login_event.html', {'event': event})


@login_required
@require_POST
def delete_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
    vehicle.delete()
    messages.success(request, 'Listing removed successfully.')
    return redirect('dashboard')


@login_required
def edit_vehicle(request, pk):
    vehicle = get_object_or_404(Vehicle, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = VehicleEditForm(request.POST, request.FILES, instance=vehicle)
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing updated successfully.')
            return redirect('vehicle_detail', pk=vehicle.pk)
    else:
        form = VehicleEditForm(instance=vehicle)
    return render(request, 'edit_vehicle.html', {'form': form, 'vehicle': vehicle})


def seller_profile(request, pk):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    seller = get_object_or_404(User, pk=pk)
    seller_profile_obj = getattr(seller, 'profile', None)
    listings = Vehicle.objects.filter(owner=seller).order_by('-created_at')
    reviews = seller.reviews_received.select_related('reviewer__profile').order_by('-created_at')
    avg = seller_profile_obj.average_rating() if seller_profile_obj else None
    return render(request, 'seller_profile.html', {
        'seller': seller,
        'seller_profile': seller_profile_obj,
        'listings': listings,
        'reviews': reviews,
        'avg': avg,
    })


@login_required
@require_POST
def confirm_login_event(request, pk):
    event = get_object_or_404(LoginEvent, pk=pk, user=request.user)
    event.is_confirmed = True
    event.save(update_fields=['is_confirmed'])
    messages.success(request, 'Login confirmed. Stay safe!')
    return redirect('dashboard')