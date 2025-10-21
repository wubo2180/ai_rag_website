"""
测试URL路由加载
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.urls import get_resolver, URLPattern, URLResolver

def print_urls(patterns, prefix=''):
    """递归打印所有URL模式"""
    for pattern in patterns:
        if isinstance(pattern, URLPattern):
            route = str(pattern.pattern)
            full_route = prefix + route
            print(f"  {full_route:60s} [{pattern.name}]")
        elif isinstance(pattern, URLResolver):
            route = str(pattern.pattern)
            full_route = prefix + route
            print_urls(pattern.url_patterns, full_route)

def check_document_urls():
    """检查文档管理相关的URL"""
    print("=" * 80)
    print("检查文档管理URL路由")
    print("=" * 80)
    
    resolver = get_resolver()
    
    print("\n【所有已注册的URL模式】")
    print_urls(resolver.url_patterns)
    
    print("\n" + "=" * 80)
    print("【文档管理相关的URL】")
    print("=" * 80)
    
    # 查找包含 documents 的URL
    all_patterns = []
    
    def collect_patterns(patterns, prefix=''):
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                route = str(pattern.pattern)
                full_route = prefix + route
                all_patterns.append(full_route)
            elif isinstance(pattern, URLResolver):
                route = str(pattern.pattern)
                full_route = prefix + route
                collect_patterns(pattern.url_patterns, full_route)
    
    collect_patterns(resolver.url_patterns)
    
    document_patterns = [p for p in all_patterns if 'documents' in p]
    
    if document_patterns:
        for pattern in sorted(document_patterns):
            print(f"  ✓ {pattern}")
        
        # 检查关键路由
        target_pattern = 'api/documents/categories/<int:category_id>/documents/'
        if any(target_pattern in p for p in document_patterns):
            print(f"\n✅ 找到目标路由: {target_pattern}")
        else:
            print(f"\n❌ 未找到目标路由: {target_pattern}")
            print("\n可能的问题:")
            print("  1. urls.py 文件有语法错误")
            print("  2. views.py 中的 DocumentsByCategoryAPIView 有错误")
            print("  3. Django 服务器需要重启")
    else:
        print("  ❌ 没有找到任何 documents 相关的URL!")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    check_document_urls()
