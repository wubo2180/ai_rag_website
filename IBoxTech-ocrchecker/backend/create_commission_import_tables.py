#!/usr/bin/env python3
"""
创建委托单导入相关的数据库表
"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models import db
from app.models.commission_document import (
    CommissionDocument,
    CommissionExtractedField,
    CommissionStatistics
)

def create_tables():
    """创建数据库表"""
    app = create_app()
    
    with app.app_context():
        print("开始创建数据库表...")
        
        try:
            # 创建表
            db.create_all()
            
            print("\n✅ 成功创建以下表:")
            print("  - commission_documents (委托单文档表)")
            print("  - commission_extracted_fields (提取字段表)")
            print("  - commission_statistics (统计信息表)")
            
            # 验证表是否创建
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'commission_documents',
                'commission_extracted_fields',
                'commission_statistics'
            ]
            
            print("\n📋 数据库表验证:")
            for table in required_tables:
                if table in tables:
                    print(f"  ✓ {table}")
                else:
                    print(f"  ✗ {table} (未找到)")
            
            print("\n🎉 数据库表创建完成!")
            print("\n下一步:")
            print("  1. 测试字段提取: python3 ../misc/json_field_extractor.py")
            print("  2. 测试导入API: python3 ../misc/test_import_api.py")
            print("  3. 查看使用指南: cat ../misc/USAGE_GUIDE.md")
            
        except Exception as e:
            print(f"\n❌ 创建表失败: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


if __name__ == '__main__':
    create_tables()

