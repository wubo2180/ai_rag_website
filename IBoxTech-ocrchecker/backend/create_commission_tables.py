#!/usr/bin/env python3
"""
创建委托测试相关数据表
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 从根目录导入
import importlib.util

# 动态导入app.py
app_spec = importlib.util.spec_from_file_location("app_main", os.path.join(os.path.dirname(__file__), "app.py"))
app_main = importlib.util.module_from_spec(app_spec)
app_spec.loader.exec_module(app_main)

# 导入模型
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from models import db, get_models


def create_tables():
    """创建委托测试相关表"""
    try:
        app = app_main.create_db_app()
        
        with app.app_context():
            print("🔧 开始创建委托测试相关表...")
            
            # 导入所有模型
            models = get_models()
            CommissionBasic = models['CommissionBasic']
            TestItem = models['TestItem']
            SpecialTest = models['SpecialTest']
            CommissionOcrResult = models['CommissionOcrResult']
            
            print("✅ 模型导入完成")
            
            # 创建表
            db.create_all()
            print("✅ 数据表创建完成")
            
            # 验证表是否创建成功
            from sqlalchemy import text
            tables = db.session.execute(text("SHOW TABLES")).fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = ['commission_basic', 'test_items', 'special_tests', 'commission_ocr_results']
            created_tables = [table for table in expected_tables if table in table_names]
            
            print("\n📋 表创建状态:")
            for table in expected_tables:
                status = "✅ 已创建" if table in table_names else "❌ 创建失败"
                print(f"   {table}: {status}")
            
            if len(created_tables) == len(expected_tables):
                print("\n🎉 所有委托测试表创建成功！")
                
                # 显示表结构信息
                print("\n📊 表结构信息:")
                for table_name in expected_tables:
                    result = db.session.execute(text(f"DESCRIBE {table_name}")).fetchall()
                    print(f"\n{table_name} 表结构:")
                    for row in result:
                        print(f"   {row[0]} {row[1]} {row[2]} {row[3]} {row[4]} {row[5]}")
                        
            else:
                print(f"\n⚠️  部分表创建失败，成功: {len(created_tables)}/{len(expected_tables)}")
                return False
            
        return True
        
    except Exception as e:
        print(f"❌ 创建表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("委托测试数据表创建工具")
    print("=" * 60)
    
    success = create_tables()
    
    if success:
        print("\n✨ 委托测试系统数据表已准备就绪！")
        print("\n📝 接下来你可以:")
        print("   1. 启动后端服务: python app.py")
        print("   2. 测试API接口: GET /api/commissions")
        print("   3. 使用OCR工具导入数据")
        print("   4. 在前端界面进行数据审核")
    else:
        print("\n💥 表创建失败，请检查错误信息并重试")
        sys.exit(1)


if __name__ == '__main__':
    main()
