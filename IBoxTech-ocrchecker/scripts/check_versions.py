#!/usr/bin/env python3
"""
版本兼容性检查脚本
"""
import sys
import os
import subprocess
import importlib.util

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - 版本符合要求")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - 需要Python 3.8+")
        return False

def check_dependencies():
    """检查依赖库版本兼容性"""
    print("\n📦 检查依赖库版本兼容性...")
    
    # 关键依赖版本检查
    critical_deps = {
        'Flask': ('2.3.0', '3.0.0'),
        'Flask-SQLAlchemy': ('3.0.0', '4.0.0'),
        'SQLAlchemy': ('1.4.0', '2.0.0'),
        'paddleocr': ('2.0.0', '3.0.0'),
        'opencv-python': ('4.5.0', '5.0.0'),
        'Pillow': ('9.0.0', '12.0.0')
    }
    
    success = True
    for package, (min_ver, max_ver) in critical_deps.items():
        try:
            # 尝试导入包
            if package == 'opencv-python':
                import cv2
                version = cv2.__version__
            elif package == 'Flask-SQLAlchemy':
                import flask_sqlalchemy
                version = flask_sqlalchemy.__version__
            else:
                module = importlib.import_module(package.lower().replace('-', '_'))
                version = getattr(module, '__version__', 'unknown')
            
            print(f"  ✅ {package}: {version}")
            
        except ImportError as e:
            print(f"  ❌ {package}: 未安装 - {str(e)}")
            success = False
        except Exception as e:
            print(f"  ⚠️ {package}: 检查失败 - {str(e)}")
    
    return success

def check_database_models():
    """检查数据库模型是否正确加载"""
    print("\n🗄️ 检查数据库模型...")
    
    try:
        # 添加项目根目录到Python路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backend_path = os.path.join(project_root, 'backend')
        sys.path.insert(0, backend_path)
        
        # 导入数据库实例和模型
        from app.models import db, get_models
        print("  ✅ 数据库实例导入成功")
        
        # 获取所有模型
        models = get_models()
        print(f"  ✅ 成功加载 {len(models)} 个数据库模型:")
        for model_name in models.keys():
            print(f"    - {model_name}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ 数据库模型加载失败: {str(e)}")
        return False

def check_flask_app():
    """检查Flask应用是否可以正常创建"""
    print("\n🌐 检查Flask应用...")
    
    try:
        # 添加项目根目录到Python路径
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backend_path = os.path.join(project_root, 'backend')
        sys.path.insert(0, backend_path)
        
        # 导入并创建Flask应用
        from app import create_app
        
        # 设置测试环境变量
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret-key'
        os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret'
        os.environ['MYSQL_HOST'] = 'localhost'
        os.environ['MYSQL_PORT'] = '3306'
        os.environ['MYSQL_USER'] = 'test'
        os.environ['MYSQL_PASSWORD'] = 'test'
        os.environ['MYSQL_DB'] = 'test'
        
        app = create_app('testing')
        print("  ✅ Flask应用创建成功")
        
        # 检查路由是否注册
        with app.app_context():
            routes = [str(rule) for rule in app.url_map.iter_rules()]
            api_routes = [r for r in routes if r.startswith('/api')]
            print(f"  ✅ API路由注册成功 ({len(api_routes)} 个路由)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Flask应用创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_frontend_dependencies():
    """检查前端依赖"""
    print("\n📱 检查前端依赖...")
    
    try:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        frontend_path = os.path.join(project_root, 'frontend')
        
        if not os.path.exists(os.path.join(frontend_path, 'package.json')):
            print("  ❌ package.json 文件不存在")
            return False
        
        if os.path.exists(os.path.join(frontend_path, 'node_modules')):
            print("  ✅ node_modules 目录存在")
        else:
            print("  ⚠️ node_modules 目录不存在，需要运行 npm install")
        
        # 检查Node.js版本
        try:
            result = subprocess.run(['node', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                node_version = result.stdout.strip()
                print(f"  ✅ Node.js: {node_version}")
            else:
                print("  ❌ Node.js 版本检查失败")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("  ❌ Node.js 未安装或不在PATH中")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ 前端依赖检查失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("🔍 OCR数据识别系统 - 版本兼容性检查")
    print("=" * 50)
    
    checks = [
        ("Python版本", check_python_version),
        ("Python依赖库", check_dependencies),
        ("数据库模型", check_database_models),
        ("Flask应用", check_flask_app),
        ("前端依赖", check_frontend_dependencies)
    ]
    
    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name}检查过程中发生错误: {str(e)}")
            results.append((check_name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("📊 检查结果总结:")
    
    passed = 0
    total = len(results)
    
    for check_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {check_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 项检查通过")
    
    if passed == total:
        print("\n🎉 恭喜！所有版本兼容性检查都通过了！")
        print("   您可以继续启动系统。")
        return 0
    else:
        print("\n⚠️ 部分检查未通过，请根据上述提示解决问题。")
        return 1

if __name__ == '__main__':
    exit(main())
