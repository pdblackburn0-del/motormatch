from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.vehicles.models import Bid, SavedVehicle, Vehicle
from apps.messaging.models import Message
from apps.notifications.models import Notification
from apps.users.models import UserProfile
from apps.users.middleware import get_recently_viewed_pks


@login_required
def dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    my_listings          = Vehicle.objects.filter(owner=request.user).order_by('-created_at')
    saved_count          = SavedVehicle.objects.filter(user=request.user).count()
    my_bids              = Bid.objects.filter(bidder=request.user).select_related('vehicle', 'vehicle__owner').order_by('-updated_at')
    my_messages           = Message.objects.filter(recipient=request.user).select_related('sender', 'vehicle').order_by('-created_at')[:5]
    unread_messages_count = Message.objects.filter(recipient=request.user, is_read=False).count()
    unread_notifications  = Notification.objects.filter(user=request.user, is_read=False).count()

    # Recently viewed
    rv_pks           = get_recently_viewed_pks(request.user.pk)
    rv_vehicles_map  = {v.pk: v for v in Vehicle.objects.filter(pk__in=rv_pks)} if rv_pks else {}
    recently_viewed  = [rv_vehicles_map[pk] for pk in rv_pks if pk in rv_vehicles_map]

    return render(request, 'pages/dashboard.html', {
        'profile':               profile,
        'my_listings':           my_listings,
        'saved_count':           saved_count,
        'my_bids':               my_bids,
        'my_messages':           my_messages,
        'unread_messages_count': unread_messages_count,
        'unread_notifications':  unread_notifications,
        'recently_viewed':       recently_viewed,
    })


@login_required
def profile_view(request):
    from django.contrib import messages
    from apps.users.forms import ProfileForm
    prof, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=prof)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            from django.shortcuts import redirect
            return redirect('profile')
    else:
        form = ProfileForm(instance=prof)
    return render(request, 'users/profile.html', {'form': form, 'profile': prof})


@login_required
def login_event_detail(request, pk):
    from django.shortcuts import get_object_or_404
    from apps.users.models import LoginEvent
    event = get_object_or_404(LoginEvent, pk=pk, user=request.user)
    return render(request, 'users/login_event.html', {'event': event})


@login_required
def confirm_login_event(request, pk):
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect
    from django.views.decorators.http import require_POST
    from apps.users.models import LoginEvent
    event = get_object_or_404(LoginEvent, pk=pk, user=request.user)
    event.is_confirmed = True
    event.save(update_fields=['is_confirmed'])
    messages.success(request, 'Login confirmed. Stay safe!')
    return redirect('dashboard')


def enquiry_sent(request):
    return render(request, 'pages/enquiry_sent.html')
