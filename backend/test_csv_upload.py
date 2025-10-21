#!/usr/bin/env python
"""
测试CSV文件上传和统计功能
"""

import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.documents.models import Document, DocumentCategory
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import tempfile
import csv

User = get_user_model()

def test_csv_upload():
    """测试CSV文件上传"""
    print("🧪 测试CSV文件上传功能...")
    
    # 创建测试用户
    user, created = User.objects.get_or_create(
        username='test_csv_user',
        defaults={'email': 'test@example.com'}
    )
    if created:
        user.set_password('testpass')
        user.save()
    
    # 创建测试分类
    category, created = DocumentCategory.objects.get_or_create(
        name='测试分类',
        defaults={'description': '用于测试的分类', 'created_by': user}
    )
    
    # 创建临时CSV文件
    csv_content = """材料类型,原材料/基体,中间体/填料系,配方特征,关键性能指标
导热材料,氧化铝,氧化铝填料,30%氧化铝,导热系数2.5W/mK
导热材料,氮化硼,氮化硼填料,40%氮化硼,导热系数3.2W/mK
绝缘材料,聚合物基体,陶瓷填料,20%陶瓷,绝缘强度15kV/mm"""
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        temp_file_path = f.name
    
    try:
        # 读取文件内容
        with open(temp_file_path, 'rb') as f:
            file_content = f.read()
        
        # 创建上传文件对象
        uploaded_file = SimpleUploadedFile(
            name='test_materials.csv',
            content=file_content,
            content_type='text/csv'
        )
        
        # 创建文档
        document = Document.objects.create(
            title='测试材料数据',
            description='用于测试的CSV材料数据',
            file=uploaded_file,
            category=category,
            uploaded_by=user
        )
        
        print(f"✅ CSV文件上传成功:")
        print(f"   - 文档ID: {document.id}")
        print(f"   - 文档标题: {document.title}")
        print(f"   - 文件类型: {document.file_type}")
        print(f"   - 文件大小: {document.file_size} 字节")
        print(f"   - 原始文件名: {document.original_filename}")
        print(f"   - 文件类型显示名: {document.get_file_type_display()}")
        print(f"   - 文件图标: {document.get_file_type_display_icon()}")
        
        # 测试统计功能
        print("\n📊 测试文档统计功能...")
        
        # 获取文档统计
        total_docs = Document.objects.count()
        csv_docs = Document.objects.filter(file_type='csv').count()
        
        print(f"✅ 统计结果:")
        print(f"   - 总文档数: {total_docs}")
        print(f"   - CSV文档数: {csv_docs}")
        
        # 测试文件类型统计
        file_type_stats = {}
        for doc in Document.objects.all():
            if doc.file_type in file_type_stats:
                file_type_stats[doc.file_type]['count'] += 1
                file_type_stats[doc.file_type]['size'] += doc.file_size
            else:
                file_type_stats[doc.file_type] = {
                    'count': 1,
                    'size': doc.file_size,
                    'name': dict(Document.FILE_TYPES)[doc.file_type]
                }
        
        print(f"\n📈 文件类型统计:")
        for file_type, stats in file_type_stats.items():
            print(f"   - {stats['name']} ({file_type}): {stats['count']} 个文件, {stats['size']} 字节")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时文件
        try:
            os.unlink(temp_file_path)
        except:
            pass

if __name__ == '__main__':
    success = test_csv_upload()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败！")