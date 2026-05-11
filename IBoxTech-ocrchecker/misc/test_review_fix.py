#!/usr/bin/env python3
"""
测试核对信息页面修复
"""
import requests
import json

base_url = "http://localhost:5001"

def login():
    """登录获取token"""
    response = requests.post(f"{base_url}/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        return response.json()['access_token']
    raise Exception(f"登录失败: {response.text}")

def test_get_commission_data(token):
    """测试获取委托数据（应该不包含data_reviewer和review_date）"""
    print("\n" + "="*60)
    print("测试1: 获取委托数据（检查是否排除了系统字段）")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 假设file_id=5
    response = requests.get(f"{base_url}/api/files/5/commission-data", headers=headers)
    
    print(f"📥 响应状态: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            basic_info = data['data'].get('basic_info', {})
            
            print("\n✅ 成功获取委托数据")
            print(f"📋 委托编号: {basic_info.get('commission_number')}")
            print(f"📋 委托部门: {basic_info.get('commission_department')}")
            print(f"📋 委托人: {basic_info.get('commissioner')}")
            
            # 检查系统字段是否被排除
            if 'data_reviewer' in basic_info:
                print("\n❌ 错误：basic_info中仍包含data_reviewer字段")
            else:
                print("\n✅ 正确：basic_info中已排除data_reviewer字段")
            
            if 'review_date' in basic_info:
                print("❌ 错误：basic_info中仍包含review_date字段")
            else:
                print("✅ 正确：basic_info中已排除review_date字段")
            
            # 检查新字段是否存在
            new_fields = ['product_number', 'sample_weight', 'project_number', 'material_number', 'product_quantity']
            print("\n📋 新字段检查:")
            for field in new_fields:
                if field in basic_info:
                    print(f"  ✅ {field}: {basic_info.get(field)}")
                else:
                    print(f"  ⚠️  {field}: 不存在")
            
            print("\n📋 返回的字段列表:")
            for key in sorted(basic_info.keys()):
                print(f"  - {key}")
        else:
            print(f"❌ 获取失败: {data['message']}")
    else:
        print(f"❌ 请求失败: {response.text}")

def test_update_commission_data(token):
    """测试更新委托数据（尝试提交data_reviewer和review_date，应该被忽略）"""
    print("\n" + "="*60)
    print("测试2: 更新委托数据（尝试修改系统字段）")
    print("="*60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 构造更新数据，包含系统字段
    update_data = {
        "commission_number": "IBTC20240918013",
        "basic_info": {
            "commissioner": "测试用户",
            "data_reviewer": "黑客试图修改",  # 尝试修改系统字段
            "review_date": "2025-01-01",  # 尝试修改系统字段
            "commission_date": "2024-09-18"
        }
    }
    
    response = requests.put(
        f"{base_url}/api/files/5/commission-data",
        headers=headers,
        json=update_data
    )
    
    print(f"📥 响应状态: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            print("\n✅ 更新成功")
            
            # 再次查询，验证系统字段没有被修改
            response = requests.get(f"{base_url}/api/files/5/commission-data", headers=headers)
            if response.status_code == 200:
                data = response.json()
                basic_info = data['data'].get('basic_info', {})
                
                print("\n📋 验证：系统字段是否被保护")
                if 'data_reviewer' not in basic_info:
                    print("✅ data_reviewer字段被成功排除（未返回）")
                else:
                    if basic_info['data_reviewer'] == "黑客试图修改":
                        print("❌ 严重错误：data_reviewer被恶意修改！")
                    else:
                        print("⚠️  data_reviewer字段仍在返回数据中")
                
                if 'review_date' not in basic_info:
                    print("✅ review_date字段被成功排除（未返回）")
                else:
                    if str(basic_info['review_date']) == "2025-01-01":
                        print("❌ 严重错误：review_date被恶意修改！")
                    else:
                        print("⚠️  review_date字段仍在返回数据中")
                
                print(f"\n📋 委托人更新结果: {basic_info.get('commissioner')}")
        else:
            print(f"❌ 更新失败: {data['message']}")
    else:
        print(f"❌ 请求失败: {response.text}")

if __name__ == "__main__":
    try:
        print("🚀 开始测试核对信息修复...")
        token = login()
        print("✅ 登录成功")
        
        test_get_commission_data(token)
        test_update_commission_data(token)
        
        print("\n" + "="*60)
        print("✅ 所有测试完成")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

