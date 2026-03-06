"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.shortcuts import render


# ── Custom error handlers ─────────────────────────────────────────────────────
def handler400_view(request, exception=None):
    return render(request, 'errors/400.html', status=400)

def handler403_view(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def handler404_view(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def handler500_view(request):
    return render(request, 'errors/500.html', status=500)

def handler429_view(request, exception=None):
    return render(request, 'errors/429.html', status=429)

def handler503_view(request, exception=None):
    return render(request, 'errors/503.html', status=503)


handler400 = handler400_view
handler403 = handler403_view
handler404 = handler404_view
handler500 = handler500_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),

    # ── Apps ──────────────────────────────────────────────────────────────
    path('', include('apps.vehicles.urls')),
    path('', include('apps.messaging.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.users.urls')),

    # ── Dev-only error page previews ──────────────────────────────────────
    # Visit /test-error/404/ etc. to preview any error page while DEBUG=True
    path('test-error/400/', handler400_view),
    path('test-error/403/', handler403_view),
    path('test-error/404/', handler404_view),
    path('test-error/429/', handler429_view),
    path('test-error/500/', handler500_view),
    path('test-error/503/', handler503_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
