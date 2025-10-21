"""
验证 Chat 应用路由合并后的正常工作
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.urls import resolve, reverse
from django.test import RequestFactory
from apps.chat import views

def test_url_patterns():
    """测试URL模式是否正确解析"""
    print("=" * 60)
    print("测试 URL 路由解析")
    print("=" * 60)
    
    test_urls = [
        '/api/chat/sessions/',
        '/api/chat/sessions/1/',
        '/api/chat/sessions/1/history/',
        '/api/chat/sessions/1/rename/',
        '/api/chat/chat/',
        '/api/chat/models/',
    ]
    
    for url in test_urls:
        try:
            match = resolve(url)
            print(f"✅ {url}")
            print(f"   视图: {match.func.__name__ if hasattr(match.func, '__name__') else match.func.view_class.__name__}")
            print(f"   命名空间: {match.namespace}")
            print(f"   URL名称: {match.url_name}")
        except Exception as e:
            print(f"❌ {url}")
            print(f"   错误: {str(e)}")
        print()

def test_view_imports():
    """测试视图是否可以正确导入"""
    print("=" * 60)
    print("测试视图类导入")
    print("=" * 60)
    
    view_classes = [
        'ChatSessionListAPIView',
        'ChatSessionDetailAPIView',
        'ChatHistoryAPIView',
        'ChatAPIView',
        'AvailableModelsAPIView',
        'ChatSessionRenameAPIView',
    ]
    
    for view_name in view_classes:
        try:
            view_class = getattr(views, view_name)
            print(f"✅ {view_name}: {view_class}")
        except AttributeError:
            print(f"❌ {view_name}: 未找到")
    print()

def test_reverse_urls():
    """测试反向URL解析"""
    print("=" * 60)
    print("测试反向 URL 解析")
    print("=" * 60)
    
    url_names = [
        ('api:chat:session-list', {}, '/api/chat/sessions/'),
        ('api:chat:session-detail', {'pk': 1}, '/api/chat/sessions/1/'),
        ('api:chat:session-history', {'session_id': 1}, '/api/chat/sessions/1/history/'),
        ('api:chat:session-rename', {'session_id': 1}, '/api/chat/sessions/1/rename/'),
        ('api:chat:chat', {}, '/api/chat/chat/'),
        ('api:chat:available-models', {}, '/api/chat/models/'),
    ]
    
    for name, kwargs, expected in url_names:
        try:
            url = reverse(name, kwargs=kwargs)
            status = "✅" if url == expected else "⚠️"
            print(f"{status} {name}")
            print(f"   期望: {expected}")
            print(f"   实际: {url}")
        except Exception as e:
            print(f"❌ {name}")
            print(f"   错误: {str(e)}")
        print()

if __name__ == '__main__':
    print("\n🔍 Chat 应用路由合并验证\n")
    
    test_view_imports()
    test_url_patterns()
    test_reverse_urls()
    
    print("=" * 60)
    print("✅ 验证完成！")
    print("=" * 60)
