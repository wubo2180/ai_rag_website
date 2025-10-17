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
# AI_UI_928_2 集成 - 增强版API导入
from .enhanced_views import (
    StreamChatAPIView, 
    RelatedQuestionsAPIView,
    EnhancedModelsAPIView,
    ChatModelSwitchAPIView
)

app_name = 'chat_api'

urlpatterns = [
    # 聊天会话相关API
    path('sessions/', ChatSessionListAPIView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', ChatSessionDetailAPIView.as_view(), name='session-detail'),
    path('sessions/<int:session_id>/history/', ChatHistoryAPIView.as_view(), name='session-history'),
    path('sessions/<int:session_id>/rename/', ChatSessionRenameAPIView.as_view(), name='session-rename'),
    
    # 聊天API
    path('chat/', ChatAPIView.as_view(), name='chat'),
    
    # 可用模型API
    path('models/', AvailableModelsAPIView.as_view(), name='available-models'),
    
    # AI_UI_928_2 集成 - 增强版API路由
    path('api/stream/', StreamChatAPIView.as_view(), name='stream_chat'),
    path('api/suggestions/', RelatedQuestionsAPIView.as_view(), name='related_questions'),
    path('api/enhanced-models/', EnhancedModelsAPIView.as_view(), name='enhanced_models'),
    path('api/model-switch/', ChatModelSwitchAPIView.as_view(), name='model_switch'),
]