from django.urls import path
from django.views.generic import TemplateView
from . import views
from .enhanced_views import (
    StreamChatAPIView, 
    RelatedQuestionsAPIView,
    EnhancedModelsAPIView,
    ChatModelSwitchAPIView
)

app_name = 'chat'

urlpatterns = [
    # REST API路由 - 纯API架构
    path('sessions/', views.ChatSessionListAPIView.as_view(), name='session-list'),
    path('sessions/<int:pk>/', views.ChatSessionDetailAPIView.as_view(), name='session-detail'),
    path('sessions/<int:session_id>/history/', views.ChatHistoryAPIView.as_view(), name='session-history'),
    path('sessions/<int:session_id>/rename/', views.ChatSessionRenameAPIView.as_view(), name='session-rename'),
    path('chat/', views.ChatAPIView.as_view(), name='chat'),
    path('models/', views.AvailableModelsAPIView.as_view(), name='available-models'),
    path('test/', views.test_ai_connection, name='test_ai'),  # 保留测试接口
    
    # 增强版API - 流式聊天和智能建议
    path('stream/', StreamChatAPIView.as_view(), name='stream_chat'),
    path('suggestions/', RelatedQuestionsAPIView.as_view(), name='related_questions'),
    path('enhanced-models/', EnhancedModelsAPIView.as_view(), name='enhanced_models'),
    path('model-switch/', ChatModelSwitchAPIView.as_view(), name='model_switch'),
]