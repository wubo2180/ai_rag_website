"""
数据库迁移脚本：添加OCR任务表

运行方式：
python migrate_ocr_tasks.py
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_ocr_tasks_table():
    """创建OCR任务表"""
    from app import create_db_app
    from models import db
    from models.ocr_task import OcrTask
    
    app = create_db_app()
    
    with app.app_context():
        try:
            # 创建表
            db.create_all()
            print('✅ OCR任务表创建成功！')
            
            # 显示表结构
            print('\n表结构信息：')
            print(f'表名: {OcrTask.__tablename__}')
            print('字段:')
            for column in OcrTask.__table__.columns:
                print(f'  - {column.name}: {column.type}')
            
        except Exception as e:
            print(f'❌ 创建表失败: {str(e)}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    create_ocr_tasks_table()

