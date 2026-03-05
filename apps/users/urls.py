from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('enquiry-sent/', views.enquiry_sent, name='enquiry_sent'),
    path('security/login/<int:pk>/', views.login_event_detail, name='login_event_detail'),
    path('security/login/<int:pk>/confirm/', views.confirm_login_event, name='confirm_login_event'),
]
