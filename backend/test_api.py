#!/usr/bin/env python
"""
测试文档管理API的脚本
"""
import os
import sys
import django
import requests
import json

# 添加Django项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

BASE_URL = 'http://localhost:8000/api'

def test_auth():
    """测试用户认证"""
    print("🔐 测试用户认证...")
    
    # 登录测试用户
    login_data = {
        'username': 'testuser',
        'password': 'testpass123'
    }
    
    response = requests.post(f'{BASE_URL}/auth/login/', json=login_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data.get('access')
        print(f"✅ 登录成功，获取到 token: {token[:20]}...")
        return token
    else:
        print(f"❌ 登录失败: {response.status_code} - {response.text}")
        return None

def test_documents_api(token):
    """测试文档管理API"""
    if not token:
        print("❌ 无法测试API，token为空")
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n📊 测试统计API...")
    response = requests.get(f'{BASE_URL}/documents/stats/', headers=headers)
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ 统计API成功: {stats}")
    else:
        print(f"❌ 统计API失败: {response.status_code} - {response.text}")
    
    print("\n📂 测试分类API...")
    response = requests.get(f'{BASE_URL}/documents/categories/', headers=headers)
    if response.status_code == 200:
        categories = response.json()
        categories_list = categories if isinstance(categories, list) else categories.get('results', [])
        print(f"✅ 分类API成功，找到 {len(categories_list)} 个分类")
        for cat in categories_list[:3]:  # 显示前3个分类
            print(f"   - {cat['name']}: {cat['description']}")
    else:
        print(f"❌ 分类API失败: {response.status_code} - {response.text}")
    
    print("\n📄 测试文档列表API...")
    response = requests.get(f'{BASE_URL}/documents/list/', headers=headers)
    if response.status_code == 200:
        documents = response.json()
        doc_count = len(documents) if isinstance(documents, list) else len(documents.get('results', []))
        print(f"✅ 文档列表API成功，找到 {doc_count} 个文档")
    else:
        print(f"❌ 文档列表API失败: {response.status_code} - {response.text}")

if __name__ == '__main__':
    print("🚀 开始测试文档管理API...")
    
    # 测试认证
    token = test_auth()
    
    # 测试API
    test_documents_api(token)
    
    print(f"\n🎉 API测试完成！")
    print(f"📋 如果所有测试都通过，说明后端API工作正常")
    print(f"🌐 前端应该可以正常使用了：http://localhost:3000/documents")