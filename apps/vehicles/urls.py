from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('vehicle/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicle/<int:pk>/save/', views.save_vehicle, name='save_vehicle'),
    path('vehicle/<int:pk>/bid/', views.place_bid, name='place_bid'),
    path('vehicle/<int:pk>/review/', views.add_review, name='add_review'),
    path('vehicle/<int:pk>/delete/', views.delete_vehicle, name='delete_vehicle'),
    path('vehicle/<int:pk>/destroy/', views.hard_delete_vehicle, name='hard_delete_vehicle'),
    path('vehicle/<int:pk>/edit/', views.edit_vehicle, name='edit_vehicle'),
    path('compare/', views.comparison, name='comparison'),
    path('saved/', views.saved, name='saved'),
    path('saved/clear/', views.clear_saved_vehicles, name='clear_saved_vehicles'),
    path('sell/', views.sell, name='sell'),
    path('seller/<int:pk>/', views.seller_profile, name='seller_profile'),
    path('bids/<int:pk>/respond/', views.respond_bid, name='respond_bid'),
    path('bids/<int:pk>/bidder-respond/', views.bidder_respond_bid, name='bidder_respond_bid'),
    path('api/dvla/', views.dvla_lookup, name='dvla_lookup'),
]
