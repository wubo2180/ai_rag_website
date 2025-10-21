#!/usr/bin/env python
"""
创建测试用户和数据的脚本
"""
import os
import sys
import django

# 添加Django项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

django.setup()

from django.contrib.auth.models import User
from apps.documents.models import DocumentCategory

def create_test_user():
    """创建测试用户"""
    username = 'testuser'
    email = 'test@example.com'
    password = 'testpass123'
    
    # 检查用户是否已存在
    if User.objects.filter(username=username).exists():
        print(f'用户 {username} 已存在')
        user = User.objects.get(username=username)
    else:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        print(f'创建测试用户: {username}')
    
    return user

def create_test_categories(user):
    """创建测试分类"""
    categories_data = [
        {'name': '学术论文', 'description': '学术研究论文和期刊文章', 'color': '#FF6B6B'},
        {'name': '技术文档', 'description': '技术规范和开发文档', 'color': '#4ECDC4'},
        {'name': '报告书', 'description': '各类研究报告和分析报告', 'color': '#45B7D1'},
        {'name': '参考资料', 'description': '参考文献和背景资料', 'color': '#96CEB4'},
        {'name': '其他', 'description': '其他类型文档', 'color': '#FFEAA7'},
    ]
    
    created_categories = []
    for category_data in categories_data:
        category, created = DocumentCategory.objects.get_or_create(
            name=category_data['name'],
            created_by=user,
            defaults={
                'description': category_data['description'],
                'color': category_data['color']
            }
        )
        created_categories.append(category)
        if created:
            print(f'创建分类: {category.name}')
        else:
            print(f'分类已存在: {category.name}')
    
    return created_categories

if __name__ == '__main__':
    print('开始创建测试数据...')
    
    # 创建测试用户
    user = create_test_user()
    
    # 创建测试分类
    categories = create_test_categories(user)
    
    print(f'\n测试数据创建完成！')
    print(f'测试用户: testuser / testpass123')
    print(f'创建了 {len(categories)} 个分类')
    print(f'访问 http://localhost:8000/admin/ 查看管理界面')
    print(f'访问前端登录页面使用测试账号登录')