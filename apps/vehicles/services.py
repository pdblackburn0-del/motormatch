from decimal import Decimal

from django.core.cache import cache

from apps.vehicles.models import Bid, Vehicle, VehicleImage
from apps.users.models import Review
from apps.notifications.models import Notification
from motormatch.utils import validate_image_file


def invalidate_listing_caches(vehicle_pk=None):
    cache.delete('homepage:public')
    cache.delete('browse:facets')
    try:
        cache.delete_pattern('browse:qs:*')
    except Exception:
        pass
    if vehicle_pk is not None:
        cache.delete(f'vd:{vehicle_pk}')


def process_extra_photos(vehicle, files_list, start_order=0):
    from django import forms as dj_forms

    order = start_order
    for photo in files_list[:9]:
        try:
            validate_image_file(photo)
            photo.seek(0)
            VehicleImage.objects.create(vehicle=vehicle, image_file=photo, order=order)
            order += 1
        except dj_forms.ValidationError:
            pass


def add_photos_to_vehicle(vehicle, new_photos, delete_ids=None):
    from django import forms as dj_forms

    existing_count = vehicle.images.count()
    for i, photo in enumerate(new_photos):
        if existing_count + i >= 9:
            break
        try:
            validate_image_file(photo)
            photo.seek(0)
            VehicleImage.objects.create(vehicle=vehicle, image_file=photo, order=existing_count + i)
        except dj_forms.ValidationError:
            pass

    if delete_ids:
        vehicle.images.filter(pk__in=delete_ids, vehicle=vehicle).delete()


def submit_review(reviewer, vehicle, rating: int, comment: str):
    seller = vehicle.owner
    review, created = Review.objects.update_or_create(
        reviewed_user=seller,
        reviewer=reviewer,
        defaults={'rating': rating, 'comment': comment},
    )
    reviewer_name = (
        reviewer.profile.get_display_name()
        if hasattr(reviewer, 'profile')
        else reviewer.email.split('@')[0]
    )
    verb = 'left' if created else 'updated'
    Notification.objects.create(
        user=seller,
        title='New review on your profile',
        message=f'{reviewer_name} {verb} you a {rating}★ review.',
        notif_type=Notification.TYPE_SUCCESS if rating >= 4 else Notification.TYPE_INFO,
        url=f'/vehicle/{vehicle.pk}/',
    )
    cache.delete(f'vd:{vehicle.pk}')
    return review, created


def place_bid(bidder, vehicle, amount: Decimal, note: str = ''):
    if vehicle.listing_status != Vehicle.STATUS_ACTIVE:
        raise ValueError('This listing is no longer accepting bids.')

    highest = (
        vehicle.bids
        .exclude(bidder=bidder)
        .exclude(status__in=['declined'])
        .order_by('-amount')
        .values_list('amount', flat=True)
        .first()
    )
    if highest and amount <= highest:
        raise ValueError(f'Your bid must be higher than the current top bid of £{highest:,.0f}.')

    bid, created = Bid.objects.update_or_create(
        vehicle=vehicle,
        bidder=bidder,
        defaults={'amount': amount, 'note': note, 'status': 'pending'},
    )
    if vehicle.owner:
        bidder_name = (
            bidder.profile.get_display_name()
            if hasattr(bidder, 'profile')
            else bidder.email.split('@')[0]
        )
        Notification.objects.create(
            user=vehicle.owner,
            title='New bid on your listing',
            message=f'{bidder_name} placed a bid of £{amount:,.0f} on {vehicle.title}.',
            notif_type='success',
            url=f'/vehicle/{vehicle.pk}/',
        )
    cache.delete(f'vd:{vehicle.pk}')
    return bid, created


def respond_bid(seller_user, bid, action: str, counter_amount: Decimal = None, counter_note: str = ''):
    if action not in ('accept', 'decline', 'counter'):
        raise ValueError('Invalid action.')

    seller_name = (
        seller_user.profile.get_display_name()
        if hasattr(seller_user, 'profile')
        else seller_user.email.split('@')[0]
    )

    if action == 'counter':
        bid.status = 'countered'
        bid.counter_amount = counter_amount
        bid.note = counter_note or bid.note
        bid.save()
        Notification.objects.create(
            user=bid.bidder,
            title='Counter offer received',
            message=(
                f'{seller_name} countered with £{counter_amount:,.0f} on {bid.vehicle.title}.'
                ' Go to your dashboard to respond.'
            ),
            notif_type='info',
            url='/dashboard/#bids-section',
        )
    else:
        bid.status = 'accepted' if action == 'accept' else 'declined'
        bid.save()
        if action == 'accept':
            bid.vehicle.listing_status = Vehicle.STATUS_PENDING_SALE
            bid.vehicle.save(update_fields=['listing_status'])
        verb = 'accepted' if action == 'accept' else 'declined'
        Notification.objects.create(
            user=bid.bidder,
            title=f'Bid {verb}',
            message=f'{seller_name} {verb} your bid of £{bid.amount:,.0f} on {bid.vehicle.title}.',
            notif_type='success' if action == 'accept' else 'warning',
            url=f'/vehicle/{bid.vehicle.pk}/',
        )

    cache.delete(f'vd:{bid.vehicle.pk}')
    return bid


def bidder_respond_bid(bidder_user, bid, action: str):
    if action not in ('accept_counter', 'decline'):
        raise ValueError('Invalid action.')

    bidder_name = (
        bidder_user.profile.get_display_name()
        if hasattr(bidder_user, 'profile')
        else bidder_user.email.split('@')[0]
    )

    if action == 'accept_counter':
        if bid.counter_amount:
            bid.amount = bid.counter_amount
        bid.status = 'accepted'
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
    else:
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

    cache.delete(f'vd:{bid.vehicle.pk}')
    return bid
