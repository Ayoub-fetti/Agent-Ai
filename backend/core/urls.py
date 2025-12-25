from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('auth/login/', views.login, name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', views.logout, name='logout'),
    path('auth/profile/', views.profile, name='profile'),
    path('admin/users/', views.list_users, name='list_users'),
    path('admin/users/create/', views.create_user, name='create_user'),
    path('admin/users/<int:user_id>/role/', views.update_user_role, name='update_user_role'),
    path('admin/users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('admin/users/<int:user_id>/reset-password/', views.reset_password, name='reset_password'),
    path('tickets/sync/', views.sync_tickets, name='sync_tickets'),
    path('tickets/', views.list_tickets, name='list_tickets'),
    path('tickets/<int:ticket_id>/processed/', views.mark_ticket_processed, name='mark_processed'),
    path('tickets/<int:ticket_id>/', views.ticket_detail, name='ticket_detail'),
    path('tickets/<int:ticket_id>/internal-article/', views.create_internal_article, name='create_internal_article'),
    path('tickets/<int:ticket_id>/analyze/', views.analyze_ticket_from_zammad, name='analyze_ticket'),
    path('analysis/<int:analysis_id>/update/', views.update_ai_response, name='update_ai_response'),
    path('analysis/<int:analysis_id>/validate/', views.validate_response, name='validate_response'),
    path('analysis/<int:analysis_id>/send/', views.send_to_zammad, name='send_to_zammad'),
]
