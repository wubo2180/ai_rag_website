from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # API 端点
    path('api/register/', views.register_page, name='api_register'),
    path('api/login/', views.login_view, name='api_login'),
    path('api/logout/', views.logout_view, name='api_logout'),
    path('api/profile/', views.profile, name='api_profile'),
    path('api/profile/update/', views.update_profile, name='api_update_profile'),
    path('api/change-password/', views.change_password_api, name='api_change_password'),
    path('api/upload-avatar/', views.upload_avatar, name='api_upload_avatar'),
    
    # 传统视图（用于兼容）
    path('profile/', views.profile_view, name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('password/', views.change_password, name='change_password'),
    path('login/', views.login_page, name='login'),
    path('register/', views.register_page, name='register'),
    path('logout/', views.logout_page, name='logout'),
]