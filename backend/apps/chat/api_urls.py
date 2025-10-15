from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import (
    ChatSessionListAPIView,
    ChatSessionDetailAPIView,
    ChatHistoryAPIView,
    ChatAPIView,
    AvailableModelsAPIView,
    ChatSessionRenameAPIView,
)

app_name = 'chat_api'

urlpatterns = [
    # 聊天会话相关API
    path('sessions/', ChatSessionListAPIView.as_view(), name='session-list'),
    path('sessions/<uuid:pk>/', ChatSessionDetailAPIView.as_view(), name='session-detail'),
    path('sessions/<uuid:session_id>/history/', ChatHistoryAPIView.as_view(), name='session-history'),
    path('sessions/<uuid:session_id>/rename/', ChatSessionRenameAPIView.as_view(), name='session-rename'),
    
    # 聊天API
    path('chat/', ChatAPIView.as_view(), name='chat'),
    
    # 可用模型API
    path('models/', AvailableModelsAPIView.as_view(), name='available-models'),
]