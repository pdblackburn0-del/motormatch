import urllib.parse

import urllib.request

from django.conf import settings

from django.contrib.auth import get_user_model

from django.contrib.auth.decorators import login_required

from django.db.models import Q

from django.http import JsonResponse

from django.shortcuts import get_object_or_404, redirect, render

from django.views.decorators.http import require_POST

from apps.messaging.models import Message

from apps.notifications.models import Notification

from apps.vehicles.models import Vehicle

from apps.users.middleware import get_online_status, invalidate_poll_cache, check_rate_limit

User = get_user_model()

@login_required

def inbox(request):

    Message.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    all_msgs = (

        Message.objects

        .filter(Q(sender=request.user) | Q(recipient=request.user))

        .select_related('sender', 'sender__profile', 'recipient', 'recipient__profile', 'vehicle')

        .order_by('-created_at')

    )

    seen          = set()

    conversations = []

    for msg in all_msgs:

        other = msg.recipient if msg.sender == request.user else msg.sender

        if other.pk not in seen:

            seen.add(other.pk)

            unread = Message.objects.filter(sender=other, recipient=request.user, is_read=False).count()

            conversations.append({'user': other, 'last_message': msg, 'unread': unread})

    return render(request, 'messaging/inbox.html', {'conversations': conversations})

@login_required

def conversation(request, user_pk):

    other = get_object_or_404(User, pk=user_pk)

    thread = (

        Message.objects

        .filter(Q(sender=request.user, recipient=other) | Q(sender=other, recipient=request.user))

        .select_related('sender', 'sender__profile', 'vehicle')

        .order_by('created_at')

    )

    thread.filter(recipient=request.user, is_read=False).update(is_read=True)

    vehicle       = next((m.vehicle for m in thread if m.vehicle), None)

    other_profile = getattr(other, 'profile', None)

    my_initials   = request.user.profile.get_initials() if hasattr(request.user, 'profile') else request.user.email[:2].upper()

    return render(request, 'messaging/conversation.html', {

        'other':         other,

        'other_profile': other_profile,

        'thread':        thread,

        'vehicle':       vehicle,

        'my_initials':   my_initials,

        'other_online':  get_online_status(other.pk),

    })

@login_required

@require_POST

def send_message_ajax(request, user_pk):

    other   = get_object_or_404(User, pk=user_pk)

    body    = request.POST.get('body', '').strip()

    vid     = request.POST.get('vehicle_id')

    attach  = request.FILES.get('attachment')

    gif_url = request.POST.get('gif_url', '').strip()

    if not body and not attach and not gif_url:

        return JsonResponse({'error': 'Empty message'}, status=400)

    if check_rate_limit(request.user.pk, 'send_message', max_count=20, window=60):

        return JsonResponse({'error': 'You are sending messages too quickly. Please slow down.'}, status=429)

    vehicle = Vehicle.objects.filter(pk=vid).first() if vid else None

    msg = Message.objects.create(

        sender=request.user,

        recipient=other,

        vehicle=vehicle,

        subject='',

        body=body,

        attachment=attach or None,

        gif_url=gif_url,

    )

    referer            = request.META.get('HTTP_REFERER', '')

    recipient_on_chat  = f'/inbox/{request.user.pk}/' in referer

    if not recipient_on_chat:

        sender_name = (

            request.user.profile.get_display_name()

            if hasattr(request.user, 'profile')

            else request.user.email.split('@')[0]

        )

        Notification.objects.create(

            user=other,

            title='New message',

            message=f'{sender_name} sent you a message.',

            notif_type='info',

            url=f'/inbox/{request.user.pk}/',

        )

        invalidate_poll_cache(other.pk)

    initials = request.user.profile.get_initials() if hasattr(request.user, 'profile') else request.user.email[:2].upper()

    return JsonResponse({

        'id':             msg.pk,

        'body':           msg.body,

        'attachment_url': msg.attachment.url if msg.attachment else None,

        'gif_url':        msg.gif_url,

        'time':           msg.created_at.strftime('%H:%M'),

        'date':           msg.created_at.strftime('%-d %b %Y'),

        'is_mine':        True,

        'initials':       initials,

        'is_read':        False,

    })

@login_required

def poll_messages(request, user_pk):

    from django.core.cache import cache

    other    = get_object_or_404(User, pk=user_pk)

    after_pk = int(request.GET.get('after', 0))

    new_msgs = (

        Message.objects

        .filter(

            Q(sender=request.user, recipient=other) | Q(sender=other, recipient=request.user),

            pk__gt=after_pk,

        )

        .select_related('sender', 'sender__profile')

        .order_by('created_at')

    )

    new_msgs.filter(recipient=request.user, is_read=False).update(is_read=True)

    Notification.objects.filter(

        user=request.user,

        url__contains=f'/inbox/{other.pk}/',

        is_read=False,

    ).update(is_read=True)

    read_up_to = (

        Message.objects

        .filter(sender=request.user, recipient=other, is_read=True)

        .order_by('-pk')

        .values_list('pk', flat=True)

        .first()

    ) or 0

    typing_key = f'typing_{other.pk}_to_{request.user.pk}'

    is_typing  = bool(cache.get(typing_key))

    my_initials = request.user.profile.get_initials() if hasattr(request.user, 'profile') else request.user.email[:2].upper()

    other_prof  = getattr(other, 'profile', None)

    other_init  = other_prof.get_initials() if other_prof else other.email[:2].upper()

    def serialise(m):

        is_mine = m.sender_id == request.user.pk

        return {

            'id':             m.pk,

            'body':           m.body,

            'attachment_url': m.attachment.url if m.attachment else None,

            'gif_url':        m.gif_url,

            'time':           m.created_at.strftime('%H:%M'),

            'date':           m.created_at.strftime('%-d %b %Y'),

            'is_mine':        is_mine,

            'initials':       my_initials if is_mine else other_init,

            'is_read':        m.is_read,

        }

    return JsonResponse({

        'messages':    [serialise(m) for m in new_msgs],

        'typing':      is_typing,

        'read_up_to':  read_up_to,

        'other_online': get_online_status(other.pk),

    })

@login_required

@require_POST

def set_typing(request, user_pk):

    from django.core.cache import cache

    key = f'typing_{request.user.pk}_to_{user_pk}'

    cache.set(key, True, timeout=4)

    return JsonResponse({'ok': True})

@login_required

@require_POST

def send_message(request, pk=None):

    from django.contrib import messages as django_messages

    recipient_id = request.POST.get('recipient_id')

    vehicle_id   = request.POST.get('vehicle_id') or pk

    subject      = request.POST.get('subject', '').strip()

    body         = request.POST.get('body', '').strip()

    if not recipient_id or not body:

        django_messages.error(request, 'Message body is required.')

        return redirect(request.META.get('HTTP_REFERER', 'home'))

    recipient   = get_object_or_404(User, pk=recipient_id)

    vehicle     = Vehicle.objects.filter(pk=vehicle_id).first() if vehicle_id else None

    sender_name = (

        request.user.profile.get_display_name()

        if hasattr(request.user, 'profile')

        else request.user.email.split('@')[0]

    )

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

    django_messages.success(request, 'Message sent!')

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required

@require_POST

def delete_conversation(request, user_pk):

    from django.contrib import messages as django_messages

    other = get_object_or_404(User, pk=user_pk)

    Message.objects.filter(

        Q(sender=request.user, recipient=other) |

        Q(sender=other, recipient=request.user)

    ).delete()

    django_messages.success(request, 'Conversation deleted.')

    return redirect('inbox')

@login_required

def tenor_search(request):

    from django.core.cache import cache as _cache

    import json as _json

    rl_key = f'tenor_rl_{request.user.pk}'

    count  = _cache.get(rl_key, 0)

    if count >= 30:

        return JsonResponse({'error': 'Too many GIF requests. Try again shortly.'}, status=429)

    _cache.set(rl_key, count + 1, timeout=60)

    q        = request.GET.get('q', '').strip()[:100]

    endpoint = 'search' if q else 'trending'

    api_key  = getattr(settings, 'TENOR_API_KEY', 'LIVDSRZULELA')

    url      = (

        f'https://api.tenor.com/v1/{endpoint}'

        f'?q={urllib.parse.quote(q)}'

        f'&key={api_key}'

        f'&limit=12'

        f'&media_filter=minimal'

        f'&contentfilter=medium'

    )

    try:

        req = urllib.request.Request(url, headers={'User-Agent': 'MotorMatch/1.0'})

        with urllib.request.urlopen(req, timeout=5) as resp:

            data = _json.loads(resp.read())

        gifs = []

        for r in data.get('results', []):

            media   = r.get('media', [{}])[0]

            gif_url = media.get('gif', {}).get('url', '')

            preview = media.get('tinygif', {}).get('url', gif_url)

            if gif_url:

                gifs.append({'url': gif_url, 'preview': preview, 'title': r.get('title', '')})

        return JsonResponse({'gifs': gifs})

    except Exception:

        return JsonResponse({'error': 'Could not fetch GIFs. Please try again.'}, status=503)
