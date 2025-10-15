from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.http import JsonResponse
from apps.chat.api_views import AvailableModelsAPIView

def test_api(request):
    return JsonResponse({"status": "API working", "message": "Test endpoint"})

urlpatterns = [
    path('', RedirectView.as_view(url='/chat/', permanent=False), name='home'),
    path('admin/', admin.site.urls),
    
    # API 路由
    path('api/', include('api_urls')),
    
    # 测试API
    path('api/test/', test_api, name='api-test'),
    # 直接定义聊天API
    path('api/chat/models/', AvailableModelsAPIView.as_view(), name='api-chat-models'),
    
    # Web 页面路由
    path('accounts/', include('apps.accounts.urls')),
    path('chat/', include('apps.chat.urls')),
    path('knowledge/', include('apps.knowledge.urls')),
]