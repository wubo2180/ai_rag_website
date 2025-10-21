"""
测试知识图谱 API 的认证机制
"""
import os
import sys
import django
import requests

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.tokens import RefreshToken

def test_kg_api_auth():
    print("=" * 60)
    print("测试知识图谱 API 认证")
    print("=" * 60)
    
    # 获取用户
    user = User.objects.first()
    if not user:
        print("❌ 未找到用户")
        return
    
    print(f"🧑‍💻 使用用户: {user.username}")
    
    # 生成 JWT token
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    
    print(f"🔑 JWT Token: {access_token[:50]}...")
    
    # 测试不带认证的请求
    print("\n📡 测试不带认证的请求:")
    try:
        response = requests.get('http://localhost:8000/api/kg/graph/full_graph/')
        print(f"   状态码: {response.status_code}")
        if response.status_code == 401:
            print("   ✅ 正确返回401 - 需要认证")
        else:
            print(f"   ❌ 意外状态码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")
    
    # 测试带认证的请求
    print("\n📡 测试带认证的请求:")
    try:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        response = requests.get('http://localhost:8000/api/kg/graph/full_graph/', headers=headers)
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ 认证成功!")
            print(f"   📊 节点数量: {len(data.get('nodes', []))}")
            print(f"   🔗 边数量: {len(data.get('edges', []))}")
            if 'stats' in data:
                stats = data['stats']
                print(f"   📈 统计信息:")
                print(f"      - 原材料: {stats.get('raw_materials_count', 0)}")
                print(f"      - 中间体: {stats.get('intermediates_count', 0)}")
                print(f"      - 配方: {stats.get('formulas_count', 0)}")
                print(f"      - 性能: {stats.get('performances_count', 0)}")
        else:
            print(f"   ❌ 认证失败: {response.status_code}")
            if response.content:
                print(f"   错误内容: {response.text}")
    except Exception as e:
        print(f"   ❌ 请求失败: {e}")

if __name__ == '__main__':
    test_kg_api_auth()