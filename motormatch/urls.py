from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),
    path('vehicle/<int:pk>/', views.vehicle_detail, name='vehicle_detail'),
    path('vehicle/<int:pk>/save/', views.save_vehicle, name='save_vehicle'),
    path('vehicle/<int:pk>/bid/', views.place_bid, name='place_bid'),
    path('vehicle/<int:pk>/review/', views.add_review, name='add_review'),
    path('vehicle/<int:pk>/message/', views.send_message, name='send_message'),
    path('compare/', views.comparison, name='comparison'),
    path('saved/', views.saved, name='saved'),
    path('sell/', views.sell, name='sell'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('offers/', views.offers, name='offers'),
    path('offer-submitted/', views.offer_submitted, name='offer_submitted'),
    path('enquiry-sent/', views.enquiry_sent, name='enquiry_sent'),
    path('notifications/', views.notifications_list, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('inbox/', views.inbox, name='inbox'),
    path('messages/send/', views.send_message, name='send_message_direct'),
    path('bids/<int:pk>/respond/', views.respond_bid, name='respond_bid'),
    path('api/dvla/', views.dvla_lookup, name='dvla_lookup'),
]
