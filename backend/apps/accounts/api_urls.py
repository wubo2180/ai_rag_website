from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    UserProfileAPIView,
    ChangePasswordAPIView,
    UserInfoAPIView,
)

app_name = 'accounts_api'

urlpatterns = [
    # JWT Token 相关
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),
    
    # 用户认证
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    
    # 用户信息
    path('profile/', UserProfileAPIView.as_view(), name='profile'),
    path('user-info/', UserInfoAPIView.as_view(), name='user-info'),
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
]