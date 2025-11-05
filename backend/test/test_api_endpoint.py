"""
测试Django API端点的脚本
"""

import requests
import json
import os

def test_api_endpoint():
    """测试知识抽取API端点"""
    
    # API端点URL
    url = "http://127.0.0.1:8000/api/ai-service/knowledge-extraction/"
    
    print("🔗 测试知识抽取API端点...")
    
    # 首先测试GET请求
    print("📋 测试GET请求...")
    try:
        response = requests.get(url)
        print(f"GET响应状态码: {response.status_code}")
        if response.status_code == 200:
            print("GET请求成功:")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        else:
            print(f"GET请求失败: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保Django服务器正在运行")
        return
    except Exception as e:
        print(f"❌ GET请求异常: {str(e)}")
        return
    
    # 创建测试文件内容
    test_content = """材料科学研究报告

1. 研究背景
本研究旨在分析新型复合材料的力学性能。

2. 实验数据
- 原材料: 碳纤维
- 中间体: 预浸料  
- 配方: 环氧树脂基体60%，碳纤维40%
- 拉伸强度: 450 MPa
- 弹性模量: 72 GPa  
- 断裂伸长率: 8.5%

3. 结论
该复合材料具有优异的综合性能，适用于航空航天领域。
"""

    # 测试POST请求（文件上传）
    print("\n📁 测试POST请求（文件上传）...")
    try:
        # 创建临时文件
        files = {
            'file': ('test_material.txt', test_content.encode('utf-8'), 'text/plain')
        }
        data = {
            'user_id': 'test_user'
        }
        
        response = requests.post(url, files=files, data=data, timeout=120)
        print(f"POST响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ POST请求成功:")
            result = response.json()
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            print(f"❌ POST请求失败: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ POST请求异常: {str(e)}")

if __name__ == "__main__":
    test_api_endpoint()