from django.urls import path
from . import views

urlpatterns = [
    path('offers/', views.offers, name='offers'),
    path('offer-submitted/', views.offer_submitted, name='offer_submitted'),
]
