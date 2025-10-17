#!/usr/bin/env python3
"""
测试Django流式API端点
"""
import requests
import json

def test_django_stream_api():
    """测试Django的流式聊天API"""
    print("🔍 测试Django流式聊天API")
    print("=" * 50)
    
    url = "http://127.0.0.1:8000/api/chat/api/stream/"
    headers = {
        'Content-Type': 'application/json'
    }
    
    # 测试请求
    payload = {
        'message': '你好',
        'model': 'deepseek',
        'deep_thinking': False
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

if __name__ == "__main__":
    print("🚀 Django流式API测试")
    print("=" * 60)
    
    test_django_stream_api()
    
    print("\n✅ 测试完成")