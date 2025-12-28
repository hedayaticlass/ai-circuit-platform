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
        path('api/google-client-id/', views.google_client_id_api, name='google_client_id_api'),
        path('api/google-signin/', views.google_signin_api, name='google_signin_api'),

        # URLهای مرتبط با نظرات
        path('reviews/', views.reviews_page, name='reviews_page'),
        path('reviews/list/', views.reviews_list, name='reviews_list'),
        path('api/reviews/submit/', views.submit_review, name='submit_review'),
        path('api/reviews/stats/', views.reviews_stats, name='reviews_stats'),
        path('api/reviews/featured/', views.get_featured_reviews, name='get_featured_reviews'),
        path('api/reviews/chat-history/', views.get_user_chat_history, name='get_user_chat_history'),
        path('api/chat/history/message/<int:message_id>', views.get_chat_message_content, name='get_chat_message_content'),
        path('api/chat/render-code/', views.render_python_code_api, name='render_python_code_api'),
        path('api/schematic/generate/', views.generate_schematic_api, name='generate_schematic_api'),
        path('api/simulation/run/', views.run_simulation_api, name='run_simulation_api'),
        path('api/spice/generate/', views.generate_spice_api, name='generate_spice_api'),

]
