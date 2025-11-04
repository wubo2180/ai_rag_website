#!/usr/bin/env python3
"""
AI服务调试脚本 - 诊断Dify API连接问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.conf import settings
import requests
import json

def test_dify_connection():
    """测试Dify API连接"""
    print("🔍 测试Dify API连接")
    print("=" * 50)
    
    api_url = getattr(settings, 'DIFY_API_URL', 'http://172.20.46.18:8088/v1/chat-messages')
    api_key = settings.DIFY_API_KEY
    if not api_key:
        print("❌ DIFY_API_KEY not configured in settings")
        return False
    
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key}")
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # 测试简单请求
    request_body = {
        "inputs": {
            "largeModel": "通义千问"
        },
        "query": "测试消息",
        "user": "debug_user",
        "response_mode": "blocking"
    }
    
    print(f"\n请求体: {json.dumps(request_body, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(api_url, headers=headers, json=request_body, timeout=30)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("📄 响应成功:")
            result = response.json()
            print(f"  消息ID: {result.get('id', 'N/A')}")
            print(f"  回答: {result.get('answer', 'N/A')[:100]}...")
        else:
            print(f"❌ 错误响应:")
            print(f"  状态码: {response.status_code}")
            print(f"  内容: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        return False
    
    return True

def test_django_serializer():
    """测试Django序列化器"""
    print("\n🔍 测试Django序列化器")
    print("=" * 50)
    
    from apps.chat.serializers import ChatMessageCreateSerializer
    
    # 测试数据
    test_data = {
        'message': '你好',
        'model': 'deepseek',
        'session_id': None
    }
    
    print(f"测试数据: {json.dumps(test_data, indent=2, ensure_ascii=False)}")
    
    serializer = ChatMessageCreateSerializer(data=test_data)
    
    if serializer.is_valid():
        print("✅ 序列化器验证通过")
        validated_data = serializer.validated_data
        print(f"验证后数据: {json.dumps(dict(validated_data), indent=2, ensure_ascii=False, default=str)}")
        return True
    else:
        print("❌ 序列化器验证失败")
        print(f"错误: {serializer.errors}")
        return False

def main():
    """主调试流程"""
    print("🚀 AI服务调试工具")
    print("=" * 60)
    
    # 1. 检查Django设置
    print(f"Django DEBUG: {settings.DEBUG}")
    print(f"DIFY_API_URL: {getattr(settings, 'DIFY_API_URL', 'Not Set')}")
    print(f"DIFY_API_KEY: {getattr(settings, 'DIFY_API_KEY', 'Not Set')}")
    
    # 2. 测试序列化器
    serializer_ok = test_django_serializer()
    
    # 3. 测试API连接
    api_ok = test_dify_connection()
    
    # 4. 生成诊断报告
    print(f"\n📋 诊断报告")
    print("=" * 50)
    print(f"  序列化器: {'✅ 正常' if serializer_ok else '❌ 异常'}")
    print(f"  API连接:  {'✅ 正常' if api_ok else '❌ 异常'}")
    
    if serializer_ok and api_ok:
        print(f"\n🎉 所有组件正常，API应该可以工作！")
    else:
        print(f"\n⚠️  发现问题，请检查上述错误信息")

if __name__ == "__main__":
    main()