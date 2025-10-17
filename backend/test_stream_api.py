#!/usr/bin/env python3
"""
测试修复后的 Dify API 调用
"""
import requests
import json

# 使用与test_dify_api.py相同的配置
API_KEY = "app-2WflAIBZKQGLwUImUXbYaLsN"
BASE_URL = "http://172.20.46.18:8088/v1"

def test_streaming_request():
    """测试流式请求格式"""
    print("🔍 测试流式请求格式")
    print("=" * 50)
    
    url = f"{BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 测试流式请求
    payload = {
        'inputs': {
            'largeModel': '通义千问'
        },
        'query': '你好',
        'response_mode': 'streaming',  # 使用流式模式
        'user': 'test_user'
    }
    
    print(f"请求URL: {url}")
    print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30, stream=True)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("📡 流式响应内容:")
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    print(f"  {line_str}")
                    if 'data: [DONE]' in line_str:
                        break
        else:
            print(f"❌ 错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

def test_blocking_request():
    """测试阻塞式请求格式"""
    print("\n🔍 测试阻塞式请求格式")
    print("=" * 50)
    
    url = f"{BASE_URL}/chat-messages"
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    
    # 测试阻塞式请求
    payload = {
        'inputs': {
            'largeModel': '通义千问'
        },
        'query': '你好',
        'response_mode': 'blocking',  # 使用阻塞模式
        'user': 'test_user'
    }
    
    print(f"请求URL: {url}")
    print(f"请求体: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        print(f"\n✅ 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("📄 阻塞式响应内容:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"❌ 错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 Dify API 请求格式测试")
    print("=" * 60)
    
    # 先测试阻塞式请求（已知可以工作）
    test_blocking_request()
    
    # 再测试流式请求（需要验证）
    test_streaming_request()
    
    print("\n✅ 测试完成")