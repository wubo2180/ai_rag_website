#!/usr/bin/env python3
"""
数据库初始化脚本
创建所有必要的数据库表和初始数据
"""

import os
import sys
import importlib.util
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入根目录的app.py模块 (避免与app目录冲突)
import importlib.util
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_file_path = os.path.join(root_dir, 'app.py')
spec = importlib.util.spec_from_file_location("app_main", app_file_path)
app_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_main)

# 导入models
sys.path.append(os.path.join(root_dir, 'app'))
from models import db, get_models

# 获取所有模型类
models = get_models()
User = models['User']
File = models['File']
OCRResult = models['OCRResult']
ReviewRecord = models['ReviewRecord']
FileAssignment = models['FileAssignment']


def create_tables():
    """创建所有数据库表"""
    print("正在创建数据库表...")
    
    try:
        # 创建所有表
        db.create_all()
        print("✅ 数据库表创建成功")
        
    except Exception as e:
        print(f"❌ 创建数据库表失败: {str(e)}")
        raise


def create_initial_data():
    """创建初始数据"""
    print("正在创建初始数据...")
    
    try:
        # 检查是否已有管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # 创建默认管理员用户
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password='admin123',
                real_name='系统管理员',
                role='admin'
            )
            db.session.add(admin_user)
            print("✅ 创建默认管理员用户: admin / admin123")
        
        # 创建测试普通用户
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com',
                password='test123',
                real_name='测试用户',
                role='user'
            )
            db.session.add(test_user)
            print("✅ 创建测试用户: testuser / test123")
        
        # 提交更改
        db.session.commit()
        print("✅ 初始数据创建成功")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建初始数据失败: {str(e)}")
        raise


def check_database_connection():
    """检查数据库连接"""
    print("正在检查数据库连接...")
    
    try:
        # 尝试执行简单查询
        db.session.execute(text('SELECT 1'))
        print("✅ 数据库连接正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        print("请检查以下配置:")
        print("1. MySQL服务是否启动")
        print("2. 数据库连接配置是否正确")
        print("3. 数据库用户是否有足够权限")
        return False


def print_table_info():
    """打印数据库表信息"""
    print("\n📊 数据库表结构:")
    
    tables_info = {
        'users': '用户表 - 存储用户账户信息',
        'files': '文件表 - 存储上传文件的元数据',
        'ocr_results': 'OCR结果表 - 存储文件识别结果',
        'review_records': '核对记录表 - 存储人工核对操作记录',
        'file_assignments': '文件分派表 - 存储文件分配给用户的记录'
    }
    
    for table, description in tables_info.items():
        print(f"  • {table}: {description}")


def main():
    """主函数"""
    print("🚀 开始初始化OCR数据识别系统数据库...")
    print("=" * 50)
    
    # 创建Flask应用 (只用于数据库初始化)
    flask_app = app_main.create_db_app('development')
    
    with flask_app.app_context():
        # 检查数据库连接
        if not check_database_connection():
            sys.exit(1)
        
        try:
            # 创建数据库表
            create_tables()
            
            # 创建初始数据
            create_initial_data()
            
            # 打印表信息
            print_table_info()
            
            print("\n" + "=" * 50)
            print("🎉 数据库初始化完成!")
            print("\n📝 默认账户信息:")
            print("  管理员账户: admin / admin123")
            print("  测试账户: testuser / test123")
            print("\n🌐 启动应用:")
            print("  1. 启动后端: cd backend && python app.py")
            print("  2. 启动前端: cd frontend && npm run dev")
            print("  3. 访问系统: http://localhost:5173")
            
        except Exception as e:
            print(f"\n❌ 数据库初始化失败: {str(e)}")
            sys.exit(1)


if __name__ == '__main__':
    main()
