#!/usr/bin/env python3
"""
委托测试API测试脚本
"""
import os
import sys
import json
import requests
from datetime import datetime, date

# 测试配置
BASE_URL = 'http://localhost:5001/api'
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.test_commission_number = f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
    def login(self):
        """登录获取访问令牌"""
        try:
            print("🔐 正在登录...")
            response = self.session.post(
                f"{BASE_URL}/auth/login",
                json=ADMIN_CREDENTIALS
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.access_token = data['data']['access_token']
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}'
                    })
                    print("✅ 登录成功")
                    return True
                else:
                    print(f"❌ 登录失败: {data.get('message')}")
            else:
                print(f"❌ 登录失败: HTTP {response.status_code}")
            
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
        
        return False
    
    def test_create_commission(self):
        """测试创建委托测试申请单"""
        try:
            print("\n📝 测试创建委托测试申请单...")
            
            # 构造测试数据
            test_data = {
                "form_number": f"FM-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "commission_number": self.test_commission_number,
                "service_type": "加急",
                "need_report": "是",
                "commission_department": "品质部",
                "commissioner": "张三",
                "commission_date": "2023-09-19",
                "commission_address": "深圳市南山区",
                "sample_name": "填料测试样品",
                "sample_quantity": "1.0 KG",
                "sample_code": "TEST001",
                "sample_batch": "20230919001",
                "delivery_time": "2023-09-19 10:00:00",
                "required_time": "2023-09-20",
                "sample_disposal": "留样",
                "storage_method": "常温保存",
                "test_nature": "基础性能测试",
                "test_description": "对填料样品进行RoHs测试和红外扫描",
                "special_condition_flag": "无",
                "special_condition_detail": "",
                "tester": "李四",
                "data_reviewer": "王五",
                "review_date": "2023-09-19",
                "form_complete": "是",
                "sample_info_consistent": "是",
                "sample_condition_ok": "是",
                "other_notes": "",
                "delivery_person_signature": "张三 2023-09-19",
                "business_receiver_signature": "赵六 2023-09-19",
                
                # 测试项目数据
                "test_items": [
                    {
                        "test_item": "红外扫描匹配",
                        "test_equipment": "傅里叶红外光谱仪",
                        "test_standard": "GB/T 6040",
                        "test_condition": "常温",
                        "product_standard": "企业标准",
                        "unit": "%",
                        "test_result": "与历史谱图完全重叠97.443%",
                        "tester": "材易",
                        "remark": "主峰基体发射正常"
                    },
                    {
                        "test_item": "外观检测",
                        "test_equipment": "目测",
                        "test_standard": "企业标准",
                        "test_condition": "常温",
                        "product_standard": "Q/IBOX001",
                        "unit": "/",
                        "test_result": "白色轻质粉末",
                        "tester": "材易",
                        "remark": "外观正常"
                    }
                ],
                
                # 特殊测试数据
                "special_tests": [
                    {
                        "test_type": "RoHs",
                        "element_name": "铅(Pb)",
                        "standard_value": "<1000",
                        "measured_value": "ND",
                        "remark": "合格"
                    },
                    {
                        "test_type": "RoHs",
                        "element_name": "汞(Hg)",
                        "standard_value": "<1000",
                        "measured_value": "ND",
                        "remark": "合格"
                    },
                    {
                        "test_type": "RoHs",
                        "element_name": "镉(Cd)",
                        "standard_value": "<100",
                        "measured_value": "ND",
                        "remark": "合格"
                    },
                    {
                        "test_type": "RoHs",
                        "element_name": "六价铬(Cr6+)",
                        "standard_value": "<1000",
                        "measured_value": "ND",
                        "remark": "合格"
                    }
                ]
            }
            
            response = self.session.post(
                f"{BASE_URL}/commissions",
                json=test_data
            )
            
            if response.status_code == 201:
                result = response.json()
                if result.get('success'):
                    print("✅ 委托单创建成功")
                    print(f"   委托编号: {result['data']['commission_number']}")
                    print(f"   ID: {result['data']['id']}")
                    return True
                else:
                    print(f"❌ 创建失败: {result.get('message')}")
            else:
                print(f"❌ 创建失败: HTTP {response.status_code}")
                print(f"   错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 创建异常: {str(e)}")
        
        return False
    
    def test_get_commissions(self):
        """测试获取委托单列表"""
        try:
            print("\n📋 测试获取委托单列表...")
            
            response = self.session.get(f"{BASE_URL}/commissions")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    commissions = result['data']['commissions']
                    pagination = result['data']['pagination']
                    
                    print("✅ 获取列表成功")
                    print(f"   总数: {pagination['total']}")
                    print(f"   当前页: {pagination['current_page']}")
                    print(f"   每页数量: {pagination['per_page']}")
                    
                    if commissions:
                        print(f"   第一个委托单: {commissions[0]['commission_number']}")
                    
                    return True
                else:
                    print(f"❌ 获取失败: {result.get('message')}")
            else:
                print(f"❌ 获取失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 获取异常: {str(e)}")
        
        return False
    
    def test_get_commission_detail(self):
        """测试获取委托单详情"""
        try:
            print(f"\n📄 测试获取委托单详情: {self.test_commission_number}")
            
            response = self.session.get(f"{BASE_URL}/commissions/{self.test_commission_number}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    data = result['data']
                    print("✅ 获取详情成功")
                    print(f"   委托人: {data.get('commissioner')}")
                    print(f"   样品名称: {data.get('sample_name')}")
                    print(f"   测试项目数: {len(data.get('test_items', []))}")
                    print(f"   特殊测试数: {len(data.get('special_tests', []))}")
                    return True
                else:
                    print(f"❌ 获取失败: {result.get('message')}")
            else:
                print(f"❌ 获取失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 获取异常: {str(e)}")
        
        return False
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        try:
            print("\n📊 测试获取统计信息...")
            
            response = self.session.get(f"{BASE_URL}/commissions/statistics")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    stats = result['data']
                    print("✅ 获取统计成功")
                    print(f"   总委托数: {stats['total_commissions']}")
                    print(f"   月度统计: {len(stats['monthly_stats'])} 个月")
                    print(f"   测试类型: {len(stats['test_type_stats'])} 种")
                    print(f"   部门统计: {len(stats['department_stats'])} 个部门")
                    return True
                else:
                    print(f"❌ 获取失败: {result.get('message')}")
            else:
                print(f"❌ 获取失败: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 获取异常: {str(e)}")
        
        return False
    
    def test_ocr_result(self):
        """测试OCR结果保存"""
        try:
            print(f"\n🔤 测试OCR结果保存...")
            
            ocr_data = {
                "commission_number": self.test_commission_number,
                "original_pdf_path": "/path/to/test.pdf",
                "ocr_raw_data": {
                    "fields": [
                        {"text": "委托编号：" + self.test_commission_number, "confidence": 0.998},
                        {"text": "样品名称：填料", "confidence": 0.999}
                    ]
                },
                "field_mapping": {
                    "commission_number": self.test_commission_number,
                    "sample_name": "填料"
                },
                "total_fields": 31,
                "recognized_fields": 28,
                "avg_confidence": "0.95",
                "ocr_status": "completed"
            }
            
            response = self.session.post(
                f"{BASE_URL}/commissions/ocr",
                json=ocr_data
            )
            
            if response.status_code == 201:
                result = response.json()
                if result.get('success'):
                    print("✅ OCR结果保存成功")
                    print(f"   OCR ID: {result['data']['id']}")
                    return True
                else:
                    print(f"❌ 保存失败: {result.get('message')}")
            else:
                print(f"❌ 保存失败: HTTP {response.status_code}")
                print(f"   错误信息: {response.text}")
                
        except Exception as e:
            print(f"❌ 保存异常: {str(e)}")
        
        return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("委托测试API接口测试")
        print("=" * 60)
        
        tests = [
            ("登录", self.login),
            ("创建委托单", self.test_create_commission),
            ("获取委托单列表", self.test_get_commissions),
            ("获取委托单详情", self.test_get_commission_detail),
            ("获取统计信息", self.test_get_statistics),
            ("保存OCR结果", self.test_ocr_result),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name} 测试异常: {str(e)}")
                failed += 1
        
        print("\n" + "=" * 60)
        print("📈 测试结果统计:")
        print(f"   ✅ 通过: {passed}")
        print(f"   ❌ 失败: {failed}")
        print(f"   📊 成功率: {passed/(passed+failed)*100:.1f}%")
        
        if failed == 0:
            print("\n🎉 所有测试通过！委托测试系统工作正常！")
        else:
            print(f"\n⚠️  有 {failed} 个测试失败，请检查相关功能")
        
        print("=" * 60)
        return failed == 0


def main():
    """主函数"""
    # 检查后端服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 后端服务未正常运行，请先启动: python app.py")
            return False
    except requests.exceptions.RequestException:
        print("❌ 无法连接后端服务，请确保后端服务已启动: python app.py")
        return False
    
    # 运行测试
    tester = APITester()
    return tester.run_all_tests()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
