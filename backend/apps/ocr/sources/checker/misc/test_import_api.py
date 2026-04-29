#!/usr/bin/env python3
"""
测试委托单导入API
"""
import requests
import json
from pathlib import Path


class ImportAPITester:
    """导入API测试器"""
    
    def __init__(self, base_url='http://localhost:5001', token=None):
        self.base_url = base_url
        self.token = token
        self.headers = {}
        
        if token:
            self.headers['Authorization'] = f'Bearer {token}'
        self.headers['Content-Type'] = 'application/json'
    
    def login(self, username='admin', password='admin123'):
        """登录获取token"""
        url = f'{self.base_url}/api/auth/login'
        data = {
            'username': username,
            'password': password
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.token = result['data']['access_token']
                    self.headers['Authorization'] = f'Bearer {self.token}'
                    print(f"✅ 登录成功")
                    return True
            
            print(f"❌ 登录失败: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ 登录失败: {str(e)}")
            return False
    
    def test_import_single(self, pdf_path, json_base_dir):
        """测试导入单个文件"""
        url = f'{self.base_url}/api/commissions/import/single'
        data = {
            'pdf_path': pdf_path,
            'json_base_dir': json_base_dir
        }
        
        print(f"\n📤 发送请求: POST {url}")
        print(f"   PDF: {pdf_path}")
        print(f"   JSON目录: {json_base_dir}")
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            print(f"\n📥 响应状态: {response.status_code}")
            
            result = response.json()
            print(f"   {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if response.status_code == 201:
                print(f"\n✅ 导入成功！")
                return True
            else:
                print(f"\n❌ 导入失败")
                return False
                
        except Exception as e:
            print(f"\n❌ 请求失败: {str(e)}")
            return False
    
    def test_import_batch(self, pdf_dir, json_base_dir, limit=None):
        """测试批量导入"""
        url = f'{self.base_url}/api/commissions/import/batch'
        data = {
            'pdf_dir': pdf_dir,
            'json_base_dir': json_base_dir
        }
        if limit:
            data['limit'] = limit
        
        print(f"\n📤 发送请求: POST {url}")
        print(f"   PDF目录: {pdf_dir}")
        print(f"   JSON目录: {json_base_dir}")
        if limit:
            print(f"   限制: {limit}个文件")
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            print(f"\n📥 响应状态: {response.status_code}")
            
            result = response.json()
            print(f"   {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            if response.status_code == 200:
                print(f"\n✅ 批量导入完成！")
                return True
            else:
                print(f"\n❌ 批量导入失败")
                return False
                
        except Exception as e:
            print(f"\n❌ 请求失败: {str(e)}")
            return False
    
    def test_get_documents(self, page=1, per_page=10):
        """测试获取委托单列表"""
        url = f'{self.base_url}/api/commissions/documents'
        params = {
            'page': page,
            'per_page': per_page
        }
        
        print(f"\n📤 发送请求: GET {url}")
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            print(f"\n📥 响应状态: {response.status_code}")
            
            result = response.json()
            if response.status_code == 200 and result.get('success'):
                docs = result['data']['documents']
                pagination = result['data']['pagination']
                print(f"\n✅ 获取成功！")
                print(f"   总数: {pagination['total']}")
                print(f"   当前页: {pagination['current_page']}/{pagination['pages']}")
                print(f"\n   委托单列表:")
                for i, doc in enumerate(docs, 1):
                    commission_number = doc.get('commission_number', 'N/A')
                    sample_name = doc.get('sample_name', 'N/A')
                    commissioner = doc.get('commissioner', 'N/A')
                    print(f"     {i}. {commission_number} (ID: {doc['id']})")
                    print(f"        样品: {sample_name}, 委托人: {commissioner}")
                return True
            else:
                print(f"\n❌ 获取失败")
                return False
                
        except Exception as e:
            print(f"\n❌ 请求失败: {str(e)}")
            return False


def main():
    """主函数"""
    print("="*60)
    print("  委托单导入API测试")
    print("="*60)
    
    # 创建测试器
    tester = ImportAPITester()
    
    # 1. 登录
    print("\n1️⃣  测试登录...")
    if not tester.login():
        print("❌ 登录失败，退出测试")
        return
    
    # 2. 测试导入单个文件（示例）
    print("\n2️⃣  测试单个文件导入...")
    # 使用有完整JSON数据的PDF文件
    # pdf_path = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf/测试中心品质部原材料（OA）2024年9月份_第29页.pdf"
    # json_base_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_json"
    pdf_path = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf"
    json_base_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_json"
    
    # 检查文件是否存在
    if Path(pdf_path).exists():
        # tester.test_import_single(pdf_path, json_base_dir)
        tester.test_import_batch(pdf_path, json_base_dir)
    else:
        print(f"⚠️  示例PDF文件不存在，跳过单个导入测试")
    
    # 3. 测试获取文档列表
    print("\n3️⃣  测试获取文档列表...")
    tester.test_get_documents(page=1, per_page=5)
    
    print("\n" + "="*60)
    print("  测试完成")
    print("="*60)
    
    print("\n💡 提示:")
    print("   - 确保后端服务已启动: cd backend && python3 app.py")
    print("   - 修改上面的pdf_path为实际存在的PDF文件路径")
    print("   - 数据将直接导入到commission_basic等业务表")


if __name__ == '__main__':
    main()

