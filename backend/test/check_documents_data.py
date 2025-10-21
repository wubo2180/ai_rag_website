"""
检查文档管理数据库数据
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.documents.models import DocumentCategory, DocumentFolder, Document
from django.contrib.auth.models import User

def check_database():
    """检查数据库中的数据"""
    
    print("=" * 60)
    print("文档管理数据库检查")
    print("=" * 60)
    
    # 1. 检查用户
    print("\n【1. 用户列表】")
    users = User.objects.all()
    if users.exists():
        for user in users:
            print(f"  - ID: {user.id}, 用户名: {user.username}, 管理员: {user.is_staff}")
    else:
        print("  ⚠️  没有用户！请先创建用户。")
    
    # 2. 检查分类
    print("\n【2. 文档分类】")
    categories = DocumentCategory.objects.all()
    if categories.exists():
        for cat in categories:
            print(f"  - ID: {cat.id}, 名称: {cat.name}, 创建者: {cat.created_by.username}")
            print(f"    描述: {cat.description}")
            print(f"    颜色: {cat.color}")
            print(f"    文档数: {cat.document_count}, 文件夹数: {cat.folder_count}")
    else:
        print("  ⚠️  没有文档分类！")
        print("  💡 建议：登录前端页面创建分类，或运行以下命令创建测试分类：")
        print("     python create_test_categories.py")
    
    # 3. 检查文件夹
    print("\n【3. 文件夹】")
    folders = DocumentFolder.objects.all()
    if folders.exists():
        for folder in folders:
            print(f"  - ID: {folder.id}, 名称: {folder.name}")
            print(f"    分类: {folder.category.name if folder.category else '无'}")
            print(f"    父文件夹: {folder.parent.name if folder.parent else '根目录'}")
            print(f"    文档数: {folder.document_count}")
    else:
        print("  ⚠️  没有文件夹！")
    
    # 4. 检查文档
    print("\n【4. 文档】")
    documents = Document.objects.all()
    if documents.exists():
        for doc in documents[:10]:  # 只显示前10个
            print(f"  - ID: {doc.id}, 标题: {doc.title}")
            print(f"    分类: {doc.category.name if doc.category else '无'}")
            print(f"    文件夹: {doc.folder.name if doc.folder else '根目录'}")
            print(f"    上传者: {doc.uploaded_by.username}")
        if documents.count() > 10:
            print(f"  ... 还有 {documents.count() - 10} 个文档")
    else:
        print("  ⚠️  没有文档！")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    check_database()
