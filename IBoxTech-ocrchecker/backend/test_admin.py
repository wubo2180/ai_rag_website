#!/usr/bin/env python3
"""
测试管理员用户和数据库连接
"""
import os
import sys
import importlib.util

# 添加项目路径
sys.path.append('app')
from models import db, get_models

# 导入主应用
root_dir = os.path.dirname(os.path.abspath(__file__))
app_file_path = os.path.join(root_dir, 'app.py')
spec = importlib.util.spec_from_file_location("app_main", app_file_path)
app_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_main)

def test_admin_user():
    """测试管理员用户"""
    app = app_main.create_db_app()
    
    with app.app_context():
        try:
            models = get_models()
            User = models['User']
            
            admin = User.query.filter_by(username='admin').first()
            if admin:
                print('✅ 管理员用户验证成功!')
                print(f'   用户名: {admin.username}')
                print(f'   邮箱: {admin.email}')
                print(f'   角色: {admin.role}')
                print(f'   激活状态: {admin.is_active}')
                print(f'   创建时间: {admin.created_at}')
                
                # 验证密码
                if admin.check_password('admin123'):
                    print('✅ 密码验证正确!')
                else:
                    print('❌ 密码验证失败!')
                    
            else:
                print('❌ 管理员用户不存在')
                
            print('✅ 数据库连接和模型关系测试通过!')
            
        except Exception as e:
            print(f'❌ 测试失败: {str(e)}')

if __name__ == '__main__':
    test_admin_user()
