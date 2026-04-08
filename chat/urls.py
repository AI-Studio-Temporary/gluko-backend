from django.urls import path

from . import views

urlpatterns = [
    path('sessions/', views.ChatSessionListCreateView.as_view(), name='chat-sessions'),
    path('sessions/<int:session_id>/', views.ChatSessionDeleteView.as_view(), name='chat-session-delete'),
    path(
        'sessions/<int:session_id>/messages/',
        views.ChatMessageView.as_view(),
        name='chat-messages',
    ),
]
