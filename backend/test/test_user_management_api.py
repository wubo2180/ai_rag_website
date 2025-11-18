"""
测试用户管理 API
运行前请确保：
1. 后端服务正在运行（python manage.py runserver 8080）
2. 已经有一个管理员用户登录
"""

import requests
import json

# 配置
BASE_URL = "http://127.0.0.1:8080/api"
# 请替换为你的实际 token
ACCESS_TOKEN = "your_access_token_here"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

def test_get_users():
    """测试获取用户列表"""
    print("\n=== 测试获取用户列表 ===")
    url = f"{BASE_URL}/auth/users/"
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200

def test_get_departments():
    """测试获取部门列表"""
    print("\n=== 测试获取部门列表 ===")
    url = f"{BASE_URL}/auth/departments/"
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.status_code == 200

def test_user_info():
    """测试获取当前用户信息"""
    print("\n=== 测试获取当前用户信息 ===")
    url = f"{BASE_URL}/auth/user-info/"
    response = requests.get(url, headers=headers)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"用户名: {data.get('user', {}).get('username')}")
        print(f"角色: {data.get('profile', {}).get('role')}")
        print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
    else:
        print(f"错误: {response.text}")
    return response.status_code == 200

def main():
    print("开始测试用户管理 API...")
    print(f"BASE_URL: {BASE_URL}")
    
    if ACCESS_TOKEN == "your_access_token_here":
        print("\n⚠️  警告: 请先替换 ACCESS_TOKEN 为你的实际 token")
        print("你可以：")
        print("1. 在浏览器中登录")
        print("2. 打开开发者工具 -> Application -> Local Storage")
        print("3. 复制 access_token 的值")
        return
    
    # 运行测试
    results = {
        "用户信息": test_user_info(),
        "用户列表": test_get_users(),
        "部门列表": test_get_departments(),
    }
    
    print("\n=== 测试结果汇总 ===")
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")

if __name__ == "__main__":
    main()
