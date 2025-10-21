#!/usr/bin/env python
"""
测试 ASGI 配置
"""

import os
import sys

# 添加Django项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

def test_asgi_import():
    """测试 ASGI 应用导入"""
    print("=== 测试 ASGI 配置 ===")
    
    try:
        # 测试导入 application
        from config.asgi import application
        print("✓ 成功导入 'application'")
        print(f"application 类型: {type(application)}")
        
        # 测试导入 app
        from config.asgi import app
        print("✓ 成功导入 'app'")
        print(f"app 类型: {type(app)}")
        
        # 验证它们是同一个对象
        if app is application:
            print("✓ 'app' 和 'application' 指向同一个对象")
        else:
            print("✗ 'app' 和 'application' 不是同一个对象")
            
        # 测试 Django ASGI 应用
        from config.asgi import django_asgi_app
        print("✓ 成功导入 'django_asgi_app'")
        print(f"django_asgi_app 类型: {type(django_asgi_app)}")
        
        print("\n所有 ASGI 应用导入测试通过！")
        return True
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False

def test_asgi_callable():
    """测试 ASGI 应用是否可调用"""
    print("\n=== 测试 ASGI 可调用性 ===")
    
    try:
        from config.asgi import application, app
        
        # 检查是否可调用
        if callable(application):
            print("✓ 'application' 是可调用的")
        else:
            print("✗ 'application' 不是可调用的")
            
        if callable(app):
            print("✓ 'app' 是可调用的")
        else:
            print("✗ 'app' 不是可调用的")
            
        return True
        
    except Exception as e:
        print(f"✗ 测试可调用性失败: {e}")
        return False

if __name__ == "__main__":
    success1 = test_asgi_import()
    success2 = test_asgi_callable()
    
    if success1 and success2:
        print("\n🎉 ASGI 配置测试全部通过！")
        print("\n现在您可以使用以下命令启动 ASGI 服务器：")
        print("1. 使用 uvicorn:")
        print("   uvicorn config.asgi:app --host 0.0.0.0 --port 8000")
        print("   或:")
        print("   uvicorn config.asgi:application --host 0.0.0.0 --port 8000")
        print("\n2. 使用 gunicorn:")
        print("   gunicorn config.asgi:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000")
    else:
        print("\n❌ ASGI 配置存在问题，请检查修复。")