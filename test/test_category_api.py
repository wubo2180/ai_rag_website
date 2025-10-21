"""
测试分类 API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/documents"

def test_category_api():
    """测试分类 API"""
    
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
    
    # 2. 获取当前分类列表
    print("\n=== 2. 获取分类列表 ===")
    try:
        response = requests.get(f"{BASE_URL}/categories/", headers=headers)
        response.raise_for_status()
        categories_before = response.json()
        print(f"✓ 当前分类数量: {len(categories_before)}")
        print(f"分类列表: {json.dumps(categories_before, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"✗ 获取分类失败: {e}")
        return
    
    # 3. 创建新分类
    print("\n=== 3. 创建新分类 ===")
    new_category = {
        "name": "测试分类_" + str(len(categories_before) + 1),
        "description": "这是一个测试分类",
        "color": "#ff6b6b"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/categories/", json=new_category, headers=headers)
        response.raise_for_status()
        created_category = response.json()
        print(f"✓ 创建成功")
        print(f"新分类数据: {json.dumps(created_category, indent=2, ensure_ascii=False)}")
    except Exception as e:
        print(f"✗ 创建失败: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"错误详情: {e.response.text}")
        return
    
    # 4. 再次获取分类列表
    print("\n=== 4. 再次获取分类列表 ===")
    try:
        response = requests.get(f"{BASE_URL}/categories/", headers=headers)
        response.raise_for_status()
        categories_after = response.json()
        print(f"✓ 更新后分类数量: {len(categories_after)}")
        print(f"分类列表: {json.dumps(categories_after, indent=2, ensure_ascii=False)}")
        
        # 检查新分类是否在列表中
        new_category_id = created_category.get('id')
        found = any(cat.get('id') == new_category_id for cat in categories_after)
        if found:
            print(f"✓ 新分类已在列表中")
        else:
            print(f"✗ 新分类不在列表中！")
    except Exception as e:
        print(f"✗ 获取分类失败: {e}")

if __name__ == "__main__":
    test_category_api()
