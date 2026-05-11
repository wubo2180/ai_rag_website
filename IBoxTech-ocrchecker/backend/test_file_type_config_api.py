#!/usr/bin/env python3
"""
测试文件类型配置API
"""
import requests
import json

BASE_URL = "http://localhost:5000/api"

# 测试用的token（需要从登录接口获取）
# 在实际测试时，请先登录获取token
TOKEN = ""

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_get_configs():
    """测试获取配置列表"""
    print("\n" + "="*50)
    print("测试：获取文件类型配置列表")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/file-type-configs", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_get_config_by_code(type_code):
    """测试根据类型代码获取配置"""
    print("\n" + "="*50)
    print(f"测试：获取文件类型配置 - {type_code}")
    print("="*50)
    
    response = requests.get(f"{BASE_URL}/file-type-configs/by-code/{type_code}", headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_create_config():
    """测试创建配置"""
    print("\n" + "="*50)
    print("测试：创建文件类型配置")
    print("="*50)
    
    data = {
        "type_code": "test_type",
        "type_name": "测试类型",
        "type_description": "这是一个测试文件类型",
        "model_config_id": None,
        "storage_tables": [
            {
                "role": "basic",
                "table": "test_basic",
                "description": "测试基本表"
            }
        ],
        "adapter_class": "TestAdapter",
        "adapter_module": "adapters",
        "is_active": True,
        "sort_order": 99
    }
    
    response = requests.post(
        f"{BASE_URL}/file-type-configs",
        headers=headers,
        json=data
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_update_config(config_id):
    """测试更新配置"""
    print("\n" + "="*50)
    print(f"测试：更新文件类型配置 - ID: {config_id}")
    print("="*50)
    
    data = {
        "type_name": "测试类型（已更新）",
        "type_description": "这是一个更新后的测试文件类型"
    }
    
    response = requests.put(
        f"{BASE_URL}/file-type-configs/{config_id}",
        headers=headers,
        json=data
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_toggle_active(config_id, is_active):
    """测试切换状态"""
    print("\n" + "="*50)
    print(f"测试：切换配置状态 - ID: {config_id}, 状态: {is_active}")
    print("="*50)
    
    data = {
        "is_active": is_active
    }
    
    response = requests.patch(
        f"{BASE_URL}/file-type-configs/{config_id}/toggle-active",
        headers=headers,
        json=data
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def test_delete_config(config_id):
    """测试删除配置"""
    print("\n" + "="*50)
    print(f"测试：删除文件类型配置 - ID: {config_id}")
    print("="*50)
    
    response = requests.delete(
        f"{BASE_URL}/file-type-configs/{config_id}",
        headers=headers
    )
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    return response.json()


def main():
    """主测试流程"""
    print("\n🚀 开始测试文件类型配置API")
    print("⚠️  请确保：")
    print("   1. 后端服务已启动（python backend/run.py）")
    print("   2. 已设置正确的TOKEN（需要管理员权限）")
    
    if not TOKEN:
        print("\n❌ 错误：未设置TOKEN")
        print("请先登录获取token，然后修改脚本中的TOKEN变量")
        return
    
    try:
        # 1. 获取配置列表
        result = test_get_configs()
        
        # 2. 如果有配置，测试获取单个配置
        if result.get('success') and result.get('data'):
            configs = result['data']
            if len(configs) > 0:
                first_config = configs[0]
                test_get_config_by_code(first_config['type_code'])
        
        # 3. 测试创建配置
        create_result = test_create_config()
        
        # 4. 如果创建成功，测试更新、切换状态、删除
        if create_result.get('success'):
            config_id = create_result['data']['id']
            
            # 更新
            test_update_config(config_id)
            
            # 切换状态
            test_toggle_active(config_id, False)
            test_toggle_active(config_id, True)
            
            # 删除
            test_delete_config(config_id)
        
        print("\n" + "="*50)
        print("✅ 测试完成")
        print("="*50)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()

