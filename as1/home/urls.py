from . import views
from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import path


from django.urls import path
from .views import *
urlpatterns = [
        path('', views.landing, name='landing'),
        path('chat/', views.index, name='index'),
        path('signup/', views.signup_view, name='signup'),
        path('login/', views.login_view, name='login'),
        path('logout/', views.logout_view, name='logout'),
        path('api/chat/message', views.api_chat_message, name='api_chat_message'),
        path('api/chat/history/<str:session_id>', views.api_chat_history, name='api_chat_history'),
        path('api/chat/history/<str:session_id>/delete', views.api_chat_history, name='api_chat_history_delete'),
        path('api/chat/history/<str:session_id>/rename', views.api_chat_rename, name='api_chat_rename'),
        path('api/chat/sessions', views.api_chat_sessions, name='api_chat_sessions'),

]
