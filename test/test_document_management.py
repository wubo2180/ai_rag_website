"""
文档管理功能测试脚本
测试分类、文件夹、文档的创建和查询
"""
import requests
import json

BASE_URL = 'http://localhost:8000/api/documents'
TOKEN = None  # 需要先登录获取token

def login():
    """登录获取token"""
    global TOKEN
    response = requests.post('http://localhost:8000/api/auth/login/', {
        'username': 'admin',  # 修改为你的用户名
        'password': 'admin123'  # 修改为你的密码
    })
    if response.status_code == 200:
        TOKEN = response.json()['access']
        print("✅ 登录成功")
        return True
    else:
        print("❌ 登录失败:", response.text)
        return False

def get_headers():
    """获取请求头"""
    return {
        'Authorization': f'Bearer {TOKEN}',
        'Content-Type': 'application/json'
    }

def test_create_category():
    """测试创建分类"""
    print("\n📁 测试创建分类...")
    data = {
        'name': '技术文档',
        'description': '存放技术相关文档',
        'color': '#1890ff'
    }
    response = requests.post(
        f'{BASE_URL}/categories/',
        json=data,
        headers=get_headers()
    )
    if response.status_code == 201:
        category = response.json()
        print(f"✅ 分类创建成功: {category['name']} (ID: {category['id']})")
        return category['id']
    else:
        print(f"❌ 创建失败: {response.text}")
        return None

def test_list_categories():
    """测试获取分类列表"""
    print("\n📋 测试获取分类列表...")
    response = requests.get(
        f'{BASE_URL}/categories/',
        headers=get_headers()
    )
    if response.status_code == 200:
        categories = response.json()
        print(f"✅ 获取到 {len(categories)} 个分类:")
        for cat in categories:
            print(f"  - {cat['name']}: {cat['document_count']} 文档, {cat.get('folder_count', 0)} 文件夹")
        return categories
    else:
        print(f"❌ 获取失败: {response.text}")
        return []

def test_create_folder(category_id):
    """测试创建文件夹"""
    print(f"\n📂 测试在分类 {category_id} 中创建文件夹...")
    data = {
        'name': 'API文档',
        'description': 'REST API相关文档',
        'category': category_id
    }
    response = requests.post(
        f'{BASE_URL}/folders/',
        json=data,
        headers=get_headers()
    )
    if response.status_code == 201:
        folder = response.json()
        print(f"✅ 文件夹创建成功: {folder['name']} (ID: {folder['id']})")
        return folder['id']
    else:
        print(f"❌ 创建失败: {response.text}")
        return None

def test_create_subfolder(category_id, parent_id):
    """测试创建子文件夹"""
    print(f"\n📂 测试创建子文件夹 (父文件夹: {parent_id})...")
    data = {
        'name': 'v1.0',
        'description': 'API v1.0版本文档',
        'category': category_id,
        'parent': parent_id
    }
    response = requests.post(
        f'{BASE_URL}/folders/',
        json=data,
        headers=get_headers()
    )
    if response.status_code == 201:
        folder = response.json()
        print(f"✅ 子文件夹创建成功: {folder['full_path']}")
        return folder['id']
    else:
        print(f"❌ 创建失败: {response.text}")
        return None

def test_get_category_documents(category_id):
    """测试获取分类下的文档和文件夹"""
    print(f"\n📄 测试获取分类 {category_id} 的内容...")
    response = requests.get(
        f'{BASE_URL}/categories/{category_id}/documents/',
        headers=get_headers()
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取:")
        print(f"  - 文件夹数: {len(data.get('folders', []))}")
        print(f"  - 文档数: {len(data.get('documents', []))}")
        
        if data.get('folders'):
            print("\n  文件夹列表:")
            for folder in data['folders']:
                print(f"    📁 {folder['name']} ({folder['document_count']} 文档)")
        
        return data
    else:
        print(f"❌ 获取失败: {response.text}")
        return None

def test_get_folder_contents(category_id, folder_id):
    """测试获取文件夹内容"""
    print(f"\n📂 测试获取文件夹 {folder_id} 的内容...")
    response = requests.get(
        f'{BASE_URL}/categories/{category_id}/documents/?folder={folder_id}',
        headers=get_headers()
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功获取:")
        print(f"  - 子文件夹数: {len(data.get('folders', []))}")
        print(f"  - 文档数: {len(data.get('documents', []))}")
        return data
    else:
        print(f"❌ 获取失败: {response.text}")
        return None

def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("文档管理功能测试")
    print("="*60)
    
    # 登录
    if not login():
        return
    
    # 测试分类
    categories = test_list_categories()
    
    # 创建新分类
    category_id = test_create_category()
    if not category_id:
        # 如果创建失败，使用已有分类
        if categories:
            category_id = categories[0]['id']
    
    # 测试文件夹
    if category_id:
        folder_id = test_create_folder(category_id)
        
        # 创建子文件夹
        if folder_id:
            subfolder_id = test_create_subfolder(category_id, folder_id)
        
        # 获取分类内容
        test_get_category_documents(category_id)
        
        # 获取文件夹内容
        if folder_id:
            test_get_folder_contents(category_id, folder_id)
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)
    print("\n📌 接下来可以:")
    print("  1. 访问 Django Admin: http://localhost:8000/admin")
    print("  2. 使用前端界面: http://localhost:5173/documents")
    print("  3. 测试批量上传功能")

if __name__ == '__main__':
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务器")
        print("请确保后端服务已启动: python manage.py runserver")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
