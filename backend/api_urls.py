from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # 用户认证 API
    path('auth/', include('apps.accounts.api_urls')),
    
    # 聊天 API
    path('chat/', include('apps.chat.api_urls')),
    
    # AI 服务 API
    path('ai/', include('apps.ai_service.api_urls')),
    
    # 知识库 API
    path('knowledge/', include('apps.knowledge.api_urls')),
    
    # 文档管理 API
    path('documents/', include('apps.documents.urls')),
]