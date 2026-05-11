"""
创建文件类型配置和通用文档表

⚠️ 注意：此迁移脚本已废弃
- DocumentBasic 模型已被删除，改用专门的业务表（CommissionBasic、PaperArticle 等）
- FileTypeConfig 仍在使用中
- 此脚本仅供参考，不应再执行
"""

def upgrade():
    """升级数据库"""
    from app import create_db_app
    from models import db, get_models
    
    app = create_db_app()
    
    with app.app_context():
        # 导入新模型
        models = get_models()
        FileTypeConfig = models['FileTypeConfig']
        DocumentBasic = models['DocumentBasic']
        
        # 创建表
        print('创建file_type_configs表...')
        db.create_all()
        print('✅ 表创建成功')
        
        # 插入委托单类型配置
        print('初始化委托单类型配置...')
        commission_config = FileTypeConfig.query.filter_by(type_code='commission').first()
        
        if not commission_config:
            commission_config = FileTypeConfig(
                type_code='commission',
                type_name='委托单',
                type_description='检测委托测试申请单',
                ocr_model_api='/api/external-ocr/recognize',
                ocr_model_type='external',
                storage_table_basic='commission_basic',
                storage_table_items='test_items',
                storage_table_details='special_tests',
                form_component='CommissionForm',
                ocr_config={
                    'timeout': 300,
                    'retry': 3
                },
                form_config={
                    'use_dynamic_form': False,
                    'component_path': '/views/FileRecognize/components/CommissionForm.vue'
                },
                field_mapping={
                    'commission_number': 'basic_info.commission_number',
                    'form_number': 'basic_info.form_number',
                    'commissioner': 'basic_info.commissioner'
                },
                is_active=True,
                sort_order=1
            )
            db.session.add(commission_config)
            db.session.commit()
            print(f'✅ 委托单配置创建成功: {commission_config.type_code}')
        else:
            print(f'ℹ️ 委托单配置已存在: {commission_config.type_code}')
        
        print('\n数据库升级完成！')
        print(f'新增表：')
        print(f'  - file_type_configs (文件类型配置表)')
        print(f'  - document_basic (通用文档数据表)')


if __name__ == '__main__':
    upgrade()


