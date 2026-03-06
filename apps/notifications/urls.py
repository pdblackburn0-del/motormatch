from django.urls import path

from . import views

urlpatterns = [

    path('notifications/', views.notifications_list, name='notifications'),

    path('notifications/dismiss-all/', views.dismiss_all_notifications, name='dismiss_all_notifications'),

    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),

    path('notifications/<int:pk>/dismiss/', views.dismiss_notification, name='dismiss_notification'),

    path('notifications/poll/', views.notifications_poll, name='notifications_poll'),

]
