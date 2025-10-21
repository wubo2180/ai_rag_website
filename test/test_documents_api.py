"""
测试文档管理 API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/documents"

def test_documents_api():
    """测试文档管理API"""
    
    # 1. 登录获取 token
    print("=== 1. 登录 ===")
    login_url = "http://localhost:8000/api/token/"
    login_data = {
        "username": "admin",  # 请根据实际情况修改
        "password": "admin123"  # 请根据实际情况修改
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        response.raise_for_status()
        tokens = response.json()
        access_token = tokens.get('access')
        print(f"✓ 登录成功，获取 token: {access_token[:20]}...")
    except Exception as e:
        print(f"✗ 登录失败: {e}")
        return
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # 2. 获取分类列表
    print("\n=== 2. 获取分类列表 ===")
    try:
        response = requests.get(f"{BASE_URL}/categories/", headers=headers)
        response.raise_for_status()
        categories = response.json()
        print(f"✓ 获取分类成功，共 {len(categories)} 个分类")
        
        if categories:
            category_id = categories[0]['id']
            print(f"第一个分类: ID={category_id}, 名称={categories[0]['name']}")
            
            # 3. 测试获取分类下的文档
            print(f"\n=== 3. 获取分类 {category_id} 下的文档 ===")
            try:
                response = requests.get(
                    f"{BASE_URL}/categories/{category_id}/documents/",
                    headers=headers
                )
                response.raise_for_status()
                data = response.json()
                print(f"✓ 获取成功")
                print(f"  - 文件夹数量: {len(data.get('folders', []))}")
                print(f"  - 文档数量: {len(data.get('documents', []))}")
                print(f"返回数据结构: {json.dumps(data, indent=2, ensure_ascii=False)}")
            except Exception as e:
                print(f"✗ 获取分类文档失败: {e}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"响应状态码: {e.response.status_code}")
                    print(f"响应内容: {e.response.text}")
        else:
            print("没有分类，无法测试")
    except Exception as e:
        print(f"✗ 获取分类失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")
    
    # 4. 获取统计信息
    print("\n=== 4. 获取统计信息 ===")
    try:
        response = requests.get(f"{BASE_URL}/stats/", headers=headers)
        response.raise_for_status()
        stats = response.json()
        print(f"✓ 获取统计信息成功")
        print(f"统计数据: {json.dumps(stats, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"✗ 获取统计信息失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"响应状态码: {e.response.status_code}")
            print(f"响应内容: {e.response.text}")

if __name__ == "__main__":
    test_documents_api()
