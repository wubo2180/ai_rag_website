from django.urls import path, include

app_name = 'api'

urlpatterns = [
    # 用户认证 API
    path('auth/', include('apps.accounts.api_urls')),
    
    # 聊天 API (merged api_urls.py into urls.py)
    path('chat/', include('apps.chat.urls')),
    
    # 知识库 API（Dify集成）
    path('knowledge/', include('apps.knowledge.api_urls')),
    
    # 材料知识图谱 API
    path('kg/', include('apps.knowledge.kg_urls')),
    
    # AI 服务 API
    path('ai/', include('apps.ai_service.api_urls')),
    
    # 文档管理 API
    path('documents/', include('apps.documents.urls')),
]