"""
测试文档API响应格式
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.documents.models import Document
from apps.documents.serializers import DocumentListSerializer

def test_document_serialization():
    print("=" * 60)
    print("测试文档序列化格式")
    print("=" * 60)
    
    # 获取一个文档
    documents = Document.objects.all()[:3]
    
    print(f"📊 找到 {documents.count()} 个文档")
    
    if not documents:
        print("❌ 没有找到文档")
        return
    
    for doc in documents:
        print(f"\n📄 文档: {doc.title}")
        print(f"   ID: {doc.id}")
        print(f"   原始文件名: {doc.original_filename}")
        print(f"   文件字段: {doc.file}")
        if doc.file:
            print(f"   文件路径: {doc.file.name}")
            print(f"   文件URL: {doc.file.url}")
            is_csv = doc.file.name.lower().endswith('.csv')
            print(f"   是CSV文件: {is_csv}")
        
        # 序列化测试
        try:
            serializer = DocumentListSerializer(doc)
            data = serializer.data
            
            print(f"   序列化数据:")
            if 'file' in data:
                print(f"   - file: {data['file']}")
            if 'original_filename' in data:
                print(f"   - original_filename: {data['original_filename']}")
        except Exception as e:
            print(f"   序列化失败: {e}")

if __name__ == '__main__':
    test_document_serialization()