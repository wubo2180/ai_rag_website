#!/usr/bin/env python3
"""
创建管理员用户脚本
单独创建admin用户，避免复杂的关系问题
"""

import os
import sys
import importlib.util
from datetime import datetime
from werkzeug.security import generate_password_hash
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入根目录的app.py模块
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app_file_path = os.path.join(root_dir, 'app.py')
spec = importlib.util.spec_from_file_location("app_main", app_file_path)
app_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_main)

# 导入models
sys.path.append(os.path.join(root_dir, 'app'))
from models import db, get_models

def create_admin_user():
    """创建管理员用户"""
    print("🔧 正在创建管理员用户...")
    
    # 获取模型
    models = get_models()
    User = models['User']
    
    try:
        # 检查是否已有管理员用户
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print("⚠️  管理员用户已存在")
            print(f"   用户名: {admin_user.username}")
            print(f"   邮箱: {admin_user.email}")
            print(f"   角色: {admin_user.role}")
            print(f"   状态: {'激活' if admin_user.is_active else '禁用'}")
            
            # 询问是否重置密码
            reset = input("\n是否重置管理员密码？(y/N): ").strip().lower()
            if reset == 'y':
                admin_user.password = 'admin123'  # User模型应该有password setter
                db.session.commit()
                print("✅ 管理员密码已重置为: admin123")
            return
        
        # 创建新的管理员用户
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password='admin123',  # 会通过模型的password setter自动加密
            real_name='系统管理员',
            role='admin',
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ 管理员用户创建成功!")
        print("\n📝 账户信息:")
        print("   用户名: admin")
        print("   密码: admin123")
        print("   邮箱: admin@example.com")
        print("   角色: 管理员")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建管理员用户失败: {str(e)}")
        print(f"错误详情: {type(e).__name__}")
        
        # 提供手动创建的SQL语句
        print("\n💡 你也可以直接在MySQL中执行以下SQL语句:")
        hashed_password = generate_password_hash('admin123')
        print(f"""
INSERT INTO users (
    username, email, password_hash, real_name, role, 
    is_active, created_at, updated_at
) VALUES (
    'admin', 'admin@example.com', '{hashed_password}', 
    '系统管理员', 'admin', 1, NOW(), NOW()
);
        """)
        raise

def check_database_connection():
    """检查数据库连接"""
    print("🔍 检查数据库连接...")
    
    try:
        db.session.execute(text('SELECT 1'))
        print("✅ 数据库连接正常")
        return True
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🚀 管理员用户创建工具")
    print("=" * 40)
    
    # 创建Flask应用
    flask_app = app_main.create_db_app('development')
    
    with flask_app.app_context():
        # 检查数据库连接
        if not check_database_connection():
            print("请确保数据库服务正常运行")
            sys.exit(1)
        
        # 创建管理员用户
        create_admin_user()
        
        print("\n" + "=" * 40)
        print("🎉 操作完成!")

if __name__ == '__main__':
    main()
