#!/usr/bin/env python3
"""
测试重复导入检测机制
"""
import requests
import json
import sys
from pathlib import Path


class DuplicateCheckTester:
    """重复检测测试器"""
    
    def __init__(self, base_url='http://localhost:5001'):
        self.base_url = base_url
        self.token = None
        self.headers = {}
    
    def login(self, username='admin', password='admin123'):
        """登录获取token"""
        url = f'{self.base_url}/api/auth/login'
        data = {'username': username, 'password': password}
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.token = result['data']['access_token']
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    self.headers['Content-Type'] = 'application/json'
                    print(f"✅ 登录成功")
                    return True
            
            print(f"❌ 登录失败: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ 登录失败: {str(e)}")
            return False
    
    def test_import_single(self, pdf_path, json_base_dir):
        """测试单个文件导入"""
        url = f'{self.base_url}/api/commissions/import/single'
        data = {
            'pdf_path': pdf_path,
            'json_base_dir': json_base_dir
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            result = response.json()
            
            return {
                'status_code': response.status_code,
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'commission_number': result.get('commission_number', ''),
                'full_response': result
            }
            
        except Exception as e:
            return {
                'status_code': 500,
                'success': False,
                'message': f'请求失败: {str(e)}',
                'commission_number': '',
                'full_response': {}
            }
    
    def run_duplicate_test(self, pdf_path, json_base_dir):
        """运行重复导入测试"""
        print("="*70)
        print("  重复导入检测测试")
        print("="*70)
        print(f"\n测试文件: {pdf_path}")
        print(f"JSON目录: {json_base_dir}\n")
        
        # 检查文件是否存在
        if not Path(pdf_path).exists():
            print(f"❌ PDF文件不存在: {pdf_path}")
            return False
        
        # 第一次导入
        print("📤 【第一次导入】")
        print("-" * 70)
        result1 = self.test_import_single(pdf_path, json_base_dir)
        
        print(f"   状态码: {result1['status_code']}")
        print(f"   成功: {result1['success']}")
        print(f"   消息: {result1['message']}")
        print(f"   委托编号: {result1['commission_number']}")
        
        if result1['success']:
            print(f"   ✅ 第一次导入成功")
            first_time_success = True
            commission_number = result1['commission_number']
        elif '已存在' in result1['message']:
            print(f"   ℹ️  数据已存在（可能之前导入过）")
            first_time_success = False
            commission_number = result1['commission_number']
        else:
            print(f"   ❌ 第一次导入失败（非重复原因）")
            print(f"   详细信息: {json.dumps(result1['full_response'], ensure_ascii=False, indent=2)}")
            return False
        
        # 第二次导入（测试重复检测）
        print(f"\n📤 【第二次导入 - 测试重复检测】")
        print("-" * 70)
        result2 = self.test_import_single(pdf_path, json_base_dir)
        
        print(f"   状态码: {result2['status_code']}")
        print(f"   成功: {result2['success']}")
        print(f"   消息: {result2['message']}")
        print(f"   委托编号: {result2['commission_number']}")
        
        # 验证结果
        print(f"\n📊 【测试结果分析】")
        print("=" * 70)
        
        if not result2['success'] and '已存在' in result2['message']:
            print(f"✅ 测试通过！重复检测机制正常工作")
            print(f"   - 第二次导入被正确拒绝")
            print(f"   - 返回了明确的错误信息")
            print(f"   - 委托编号: {result2['commission_number']}")
            return True
        elif result2['success']:
            print(f"⚠️  警告！重复数据被导入成功")
            print(f"   - 这表示防重复机制可能失效")
            print(f"   - 需要检查数据库约束和代码逻辑")
            print(f"   详细信息: {json.dumps(result2['full_response'], ensure_ascii=False, indent=2)}")
            return False
        else:
            print(f"❌ 测试无法判断（第二次导入失败但不是因为重复）")
            print(f"   消息: {result2['message']}")
            print(f"   详细信息: {json.dumps(result2['full_response'], ensure_ascii=False, indent=2)}")
            return False


def main():
    """主函数"""
    print("\n" + "="*70)
    print("  重复导入检测测试工具")
    print("="*70 + "\n")
    
    # 创建测试器
    tester = DuplicateCheckTester()
    
    # 登录
    print("🔐 正在登录...")
    if not tester.login():
        print("❌ 登录失败，退出测试")
        sys.exit(1)
    
    print()
    
    # 配置测试文件
    pdf_path = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf/测试中心品质部原材料（OA）2024年9月份_第29页.pdf"
    json_base_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_json"
    
    # 运行测试
    success = tester.run_duplicate_test(pdf_path, json_base_dir)
    
    print("\n" + "="*70)
    if success:
        print("  ✅ 测试完成：防重复机制正常")
    else:
        print("  ⚠️  测试完成：发现潜在问题")
    print("="*70 + "\n")
    
    # 提示信息
    print("💡 说明:")
    print("   1. 此测试会尝试导入同一文件两次")
    print("   2. 第一次应该成功（或提示已存在）")
    print("   3. 第二次应该被拒绝并提示'已存在'")
    print("   4. 如果两次都成功，说明防重复机制失效")
    print()
    print("📝 注意:")
    print("   - 如果数据库中已有该文件，第一次也会提示'已存在'")
    print("   - 可以先删除数据库中的测试数据，再运行此测试")
    print("   - 测试不会真正造成数据重复（会被拦截）")
    print()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

