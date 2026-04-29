from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from apps.chat.views import AvailableModelsAPIView  # 修改：从 api_views 改为 views
from django.views.generic import TemplateView
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import os

def test_api(request):
    return JsonResponse({"status": "API working", "message": "Test endpoint"})

def favicon_ico_view(request):
    """返回 favicon.ico，重定向到 SVG 版本"""
    return RedirectView.as_view(url='/favicon.svg', permanent=True)(request)

def favicon_svg_view(request):
    """直接返回 SVG favicon 内容"""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="32" height="32">
  <circle cx="16" cy="16" r="14" fill="#4a90e2"/>
  <text x="16" y="20" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="white">D</text>
</svg>'''
    return HttpResponse(svg_content, content_type='image/svg+xml')

def serve_vue_app(request):
    """服务Vue.js单页应用"""
    from django.http import FileResponse
    vue_index_path = os.path.join(settings.BASE_DIR.parent, 'frontend', 'dist', 'index.html')
    
    if os.path.exists(vue_index_path):
        return FileResponse(open(vue_index_path, 'rb'), content_type='text/html')
    else:
        return HttpResponse("Vue.js应用未构建，请运行 'npm run build'", status=404)

urlpatterns = [
    # 管理后台
    path('admin/', admin.site.urls),
    
    # API 路由 - 必须在前面，避免被Vue.js路由捕获
    path('api/test/', test_api, name='api-test'),
    
    # 用户认证 API
    path('api/auth/', include('apps.accounts.urls')),
    
    # 聊天 API
    path('api/chat/', include('apps.chat.urls')),
    
    # 知识库 API（Dify集成）
    path('api/knowledgebase/', include('apps.knowledgebase.urls')),
    
    # 材料知识图谱 API
    path('api/knowledgegraph/', include('apps.knowledgegraph.urls')),
    
    # AI 服务 API
    path('api/ai-service/', include('apps.ai_service.urls')),

    # OCR 统一代理 API（Django app）
    path('api/ocr/', include('apps.ocr.urls')),
    
    # 文档管理 API
    path('api/documents/', include('apps.documents.urls')),
    path('api/smart-agent/', include('apps.smart_agent.urls')),
    
    
    # Favicon 处理
    path('favicon.ico', favicon_ico_view, name='favicon_ico'),
    path('favicon.svg', favicon_svg_view, name='favicon_svg'),
    
    # Vue.js 应用的主要路由
    path('', serve_vue_app, name='home'),
    path('chat/', serve_vue_app, name='chat'),
    path('chat/<path:path>', serve_vue_app, name='chat_sub'),
    path('documents/', serve_vue_app, name='documents'),
    path('documents/<path:path>', serve_vue_app, name='documents_sub'),
    path('login/', serve_vue_app, name='login'),
    path('register/', serve_vue_app, name='register'),
    path('profile/', serve_vue_app, name='profile'),
]

# 开发环境下提供静态文件和媒体文件服务
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)