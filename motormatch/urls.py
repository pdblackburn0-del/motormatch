from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('vehicle/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('compare/', views.comparison, name='comparison'),
    path('saved/', views.saved, name='saved'),
    path('sell/', views.sell, name='sell'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('offers/', views.offers, name='offers'),
    path('offer-submitted/', views.offer_submitted, name='offer_submitted'),
    path('enquiry-sent/', views.enquiry_sent, name='enquiry_sent'),
]