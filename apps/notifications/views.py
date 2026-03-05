from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from apps.notifications.models import Notification
from apps.messaging.models import Message


@login_required
def notifications_list(request):
    from django.shortcuts import render
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/notifications.html', {'notifications': notifs})


@login_required
@require_POST
def mark_notification_read(request, pk):
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save()
    return JsonResponse({'ok': True})


@login_required
@require_POST
def dismiss_notification(request, pk):
    Notification.objects.filter(pk=pk, user=request.user).update(is_read=True)
    unread = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'ok': True, 'unread': unread})


@login_required
@require_POST
def dismiss_all_notifications(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True, 'unread': 0})


@login_required
def notifications_poll(request):
    unread_notifs = Notification.objects.filter(user=request.user, is_read=False).exclude(title='New message').count()
    unread_msgs   = Message.objects.filter(recipient=request.user, is_read=False).count()
    latest = list(
        Notification.objects
        .filter(user=request.user, is_read=False)
        .exclude(title='New message')
        .order_by('-created_at')[:10]
        .values('id', 'title', 'message', 'notif_type', 'url', 'created_at')
    )
    for n in latest:
        n['created_at'] = n['created_at'].strftime('%-d %b %H:%M')
    return JsonResponse({'unread_notifs': unread_notifs, 'unread_msgs': unread_msgs, 'latest': latest})
