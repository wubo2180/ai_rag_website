#!/usr/bin/env python
"""
测试文件上传API的脚本
"""
import os
import sys
import django
import requests
import tempfile

# 添加Django项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

BASE_URL = 'http://localhost:8000/api'

def get_auth_token():
    """获取认证token"""
    login_data = {'username': 'testuser', 'password': 'testpass123'}
    response = requests.post(f'{BASE_URL}/auth/login/', json=login_data)
    
    if response.status_code == 200:
        return response.json().get('access')
    else:
        print(f"❌ 登录失败: {response.status_code}")
        return None

def test_file_upload(token):
    """测试文件上传"""
    if not token:
        return
    
    # 创建一个测试文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('这是一个测试文档内容\n')
        f.write('用于测试文件上传功能\n')
        f.write('创建时间：2025-10-16\n')
        test_file_path = f.name
    
    try:
        headers = {'Authorization': f'Bearer {token}'}
        
        # 准备文件上传数据
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            data = {
                'title': '测试文档',
                'description': '这是一个用于测试上传功能的文档',
                'tags': '测试,上传,文档',
                'is_public': 'false'
            }
            
            print("📤 测试文件上传...")
            response = requests.post(
                f'{BASE_URL}/documents/upload/',
                headers=headers,
                files=files,
                data=data
            )
            
            if response.status_code == 201:
                result = response.json()
                document = result.get('document', {})
                print(f"✅ 文件上传成功！")
                print(f"   文档ID: {document.get('id')}")
                print(f"   文档标题: {document.get('title')}")
                print(f"   文件大小: {document.get('file_size_human')}")
                return document.get('id')
            else:
                print(f"❌ 文件上传失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return None
                
    finally:
        # 清理测试文件
        if os.path.exists(test_file_path):
            os.unlink(test_file_path)

def test_document_list(token):
    """测试文档列表"""
    if not token:
        return
    
    headers = {'Authorization': f'Bearer {token}'}
    
    print("\n📋 测试文档列表...")
    response = requests.get(f'{BASE_URL}/documents/list/', headers=headers)
    
    if response.status_code == 200:
        documents = response.json()
        doc_list = documents if isinstance(documents, list) else documents.get('results', [])
        print(f"✅ 获取文档列表成功，共 {len(doc_list)} 个文档")
        
        for doc in doc_list[:3]:  # 显示前3个文档
            print(f"   - {doc['title']}: {doc['file_size_human']}")
    else:
        print(f"❌ 获取文档列表失败: {response.status_code}")

if __name__ == '__main__':
    print("🚀 开始测试文件上传功能...")
    
    # 获取认证token
    token = get_auth_token()
    if not token:
        print("❌ 无法获取认证token，测试终止")
        exit(1)
    
    # 测试文件上传
    doc_id = test_file_upload(token)
    
    # 测试文档列表
    test_document_list(token)
    
    print(f"\n🎉 文件上传测试完成！")
    if doc_id:
        print(f"✅ 文件上传功能正常工作")
        print(f"📂 可以在前端查看上传的文档：http://localhost:3000/documents")
    else:
        print(f"❌ 文件上传功能存在问题，请检查日志")