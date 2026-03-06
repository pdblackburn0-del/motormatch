from django.urls import path

from . import views

urlpatterns = [

    path('inbox/', views.inbox, name='inbox'),

    path('inbox/<int:user_pk>/', views.conversation, name='conversation'),

    path('inbox/<int:user_pk>/send/', views.send_message_ajax, name='send_message_ajax'),

    path('inbox/<int:user_pk>/poll/', views.poll_messages, name='poll_messages'),

    path('inbox/<int:user_pk>/typing/', views.set_typing, name='set_typing'),

    path('inbox/<int:user_pk>/delete/', views.delete_conversation, name='delete_conversation'),

    path('messages/send/', views.send_message, name='send_message_direct'),

    path('vehicle/<int:pk>/message/', views.send_message, name='send_message'),

    path('api/tenor/', views.tenor_search, name='tenor_search'),

    path('inbox/<int:user_pk>/message/<int:msg_pk>/delete/', views.delete_message, name='delete_message'),

]
