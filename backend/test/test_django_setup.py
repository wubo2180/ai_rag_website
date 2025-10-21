#!/usr/bin/env python
"""
Django设置测试脚本
用于验证Django项目配置是否正确
"""
import os
import sys
import django

# 设置项目路径
project_path = '/www/wwwroot/ai_rag_website/backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    # 尝试设置Django
    django.setup()
    print("✅ Django设置成功!")
    
    # 测试导入settings
    from django.conf import settings
    print(f"✅ Settings模块导入成功!")
    print(f"   - DEBUG: {settings.DEBUG}")
    print(f"   - ALLOWED_HOSTS: {settings.ALLOWED_HOSTS}")
    
    # 测试WSGI应用
    from config.wsgi import application
    print("✅ WSGI应用导入成功!")
    
except Exception as e:
    print(f"❌ Django设置失败: {e}")
    print(f"   - 当前工作目录: {os.getcwd()}")
    print(f"   - Python路径: {sys.path}")
    print(f"   - DJANGO_SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")