"""
MySQL 依赖安装脚本
"""
import subprocess
import sys

def install_mysql_dependencies():
    """安装MySQL相关依赖"""
    packages = [
        'mysqlclient',  # 推荐的MySQL客户端
        # 'PyMySQL',    # 备选方案
    ]
    
    print("🔧 安装MySQL相关依赖...")
    
    for package in packages:
        try:
            print(f"📦 正在安装 {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
            print(f"✅ {package} 安装成功")
        except subprocess.CalledProcessError as e:
            print(f"❌ {package} 安装失败: {e}")
            if package == 'mysqlclient':
                print("💡 尝试安装备选方案 PyMySQL...")
                try:
                    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyMySQL'])
                    print("✅ PyMySQL 安装成功")
                    
                    # 创建PyMySQL配置
                    with open('apps/__init__.py', 'w') as f:
                        f.write('import pymysql\npymysql.install_as_MySQLdb()\n')
                    print("✅ PyMySQL 配置完成")
                    
                except subprocess.CalledProcessError:
                    print("❌ PyMySQL 也安装失败，请手动安装")

if __name__ == '__main__':
    install_mysql_dependencies()
    print("\n🎉 MySQL依赖安装完成！")
    print("📋 下一步:")
    print("1. 启动MySQL Docker容器")
    print("2. 复制 .env.mysql 为 .env")  
    print("3. 运行 python manage.py migrate")