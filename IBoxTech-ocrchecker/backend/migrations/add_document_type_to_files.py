#!/usr/bin/env python3
"""
为files表添加document_type_code字段的Python迁移脚本
执行日期: 2025-11-05
"""

import sys
import os

# 获取项目根目录
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
sys.path.insert(0, backend_dir)

from app import create_db_app
from models import db


def upgrade():
    """执行数据库升级"""
    app = create_db_app()
    
    with app.app_context():
        print("开始执行数据库迁移...")
        
        try:
            # 添加document_type_code字段
            print("1. 添加document_type_code字段...")
            db.engine.execute("""
                ALTER TABLE `files` 
                ADD COLUMN `document_type_code` VARCHAR(50) NULL 
                COMMENT '文档类型代码（commission/paper等）' 
                AFTER `file_type`
            """)
            print("   ✓ 字段添加成功")
            
            # 创建索引
            print("2. 创建索引...")
            db.engine.execute("""
                CREATE INDEX `idx_document_type_code` 
                ON `files` (`document_type_code`)
            """)
            print("   ✓ 索引创建成功")
            
            # 可选：为现有记录设置默认值
            # print("3. 为现有记录设置默认值...")
            # db.engine.execute("""
            #     UPDATE `files` 
            #     SET `document_type_code` = 'commission' 
            #     WHERE `document_type_code` IS NULL
            # """)
            # print("   ✓ 默认值设置成功")
            
            # 验证
            print("3. 验证迁移...")
            result = db.engine.execute("""
                SELECT 
                    COLUMN_NAME, 
                    COLUMN_TYPE, 
                    IS_NULLABLE, 
                    COLUMN_COMMENT 
                FROM 
                    INFORMATION_SCHEMA.COLUMNS 
                WHERE 
                    TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'files' 
                    AND COLUMN_NAME = 'document_type_code'
            """)
            
            row = result.fetchone()
            if row:
                print(f"   ✓ 字段验证成功:")
                print(f"     - 字段名: {row[0]}")
                print(f"     - 类型: {row[1]}")
                print(f"     - 可为空: {row[2]}")
                print(f"     - 注释: {row[3]}")
            else:
                print("   ✗ 字段验证失败")
                return False
            
            print("\n✅ 数据库迁移完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 迁移失败: {str(e)}")
            return False


def downgrade():
    """执行数据库回滚"""
    app = create_db_app()
    
    with app.app_context():
        print("开始回滚数据库迁移...")
        
        try:
            # 删除索引
            print("1. 删除索引...")
            db.engine.execute("""
                ALTER TABLE `files` 
                DROP INDEX `idx_document_type_code`
            """)
            print("   ✓ 索引删除成功")
            
            # 删除字段
            print("2. 删除document_type_code字段...")
            db.engine.execute("""
                ALTER TABLE `files` 
                DROP COLUMN `document_type_code`
            """)
            print("   ✓ 字段删除成功")
            
            print("\n✅ 数据库回滚完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 回滚失败: {str(e)}")
            return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='数据库迁移工具')
    parser.add_argument('action', choices=['upgrade', 'downgrade'], 
                        help='执行升级或回滚')
    
    args = parser.parse_args()
    
    if args.action == 'upgrade':
        success = upgrade()
    else:
        success = downgrade()
    
    sys.exit(0 if success else 1)


