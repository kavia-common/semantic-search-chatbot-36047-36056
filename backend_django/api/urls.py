from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health, name='Health'),
    # Documents
    path('documents/', views.list_documents, name='documents-list'),
    path('documents/upload/', views.upload_document, name='documents-upload'),
    path('documents/<int:doc_id>/', views.get_document, name='documents-detail'),
    # Chat
    path('chat/', views.chat, name='chat'),
    path('chat/sessions/', views.list_sessions, name='chat-sessions'),
    path('chat/sessions/<int:session_id>/', views.get_session, name='chat-session-detail'),
]
