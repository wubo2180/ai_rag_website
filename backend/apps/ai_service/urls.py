from django.urls import path
from . import views

app_name = 'ai_service_api'

# AI服务相关的API路由
urlpatterns = [
    # 知识抽取API
    path('knowledge-extraction/', views.KnowledgeExtractionView.as_view(), name='knowledge_extraction'),
    
    # 服务健康检查
    path('health/', views.health_check, name='health_check'),
    
    # 测试Dify连接
    path('test-dify/', views.test_dify_connection, name='test_dify_connection'),
]