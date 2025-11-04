"""
测试CSV转知识图谱功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.documents.models import Document
from ai_rag_website.backend.apps.knowledgegraph.views import ProcessCSVDocumentsAPIView
from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

def test_csv_processing():
    print("=" * 60)
    print("测试 CSV 转知识图谱功能")
    print("=" * 60)
    
    try:
        # 获取用户
        user = User.objects.first()
        if not user:
            print("❌ 未找到用户")
            return
        
        # 查找CSV文件
        csv_docs = Document.objects.filter(file__iendswith='.csv')
        print(f"📊 找到 {csv_docs.count()} 个CSV文件:")
        
        for doc in csv_docs[:5]:  # 只显示前5个
            print(f"   - {doc.title} (ID: {doc.id})")
        
        if not csv_docs.exists():
            print("❌ 未找到CSV文件，请先上传CSV文件到文档管理系统")
            return
        
        # 创建API请求
        factory = APIRequestFactory()
        view = ProcessCSVDocumentsAPIView()
        
        # 测试第一个CSV文件
        test_doc = csv_docs.first()
        request_data = {
            'document_ids': [test_doc.id]
        }
        
        django_request = factory.post('/api/kg/process-csv-documents/', request_data, format='json')
        django_request.user = user
        
        # 转换为DRF Request
        request = Request(django_request)
        request._full_data = request_data
        
        print(f"\n🔄 处理文档: {test_doc.title}")
        
        # 调用处理方法
        response = view.post(request)
        
        print(f"✅ 响应状态: {response.status_code}")
        print(f"📄 响应数据: {response.data}")
        
        if response.status_code == 200:
            print("✅ CSV处理成功！")
        else:
            print(f"❌ CSV处理失败: {response.data}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_csv_processing()