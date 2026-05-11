"""
创建论文类型配置
"""

def create_paper_config():
    """创建论文类型配置"""
    from app import create_db_app
    from models import db, get_models
    
    app = create_db_app()
    
    with app.app_context():
        models = get_models()
        FileTypeConfig = models.get('FileTypeConfig')
        
        if not FileTypeConfig:
            print('❌ FileTypeConfig模型未加载')
            return
        
        # 检查是否已存在
        existing = FileTypeConfig.query.filter_by(type_code='paper').first()
        if existing:
            print(f'ℹ️ 论文配置已存在: {existing.type_code}')
            return
        
        # 创建论文配置
        paper_config = FileTypeConfig(
            type_code='paper',
            type_name='论文',
            type_description='学术论文检测分析',
            ocr_model_api='/api/ocr/paper',
            ocr_model_type='internal',
            storage_table_basic='document_basic',
            storage_table_items=None,
            storage_table_details=None,
            form_component=None,  # 不使用特定组件，使用动态表单
            ocr_config={
                'timeout': 300,
                'retry': 3,
                'language': 'ch'
            },
            form_config={
                'use_dynamic_form': True,
                'sections': [
                    {
                        'title': '基本信息',
                        'fields': [
                            {
                                'name': 'paper_title',
                                'label': '论文标题',
                                'type': 'text',
                                'required': True,
                                'span': 24,
                                'placeholder': '请输入论文标题'
                            },
                            {
                                'name': 'paper_number',
                                'label': '论文编号',
                                'type': 'text',
                                'required': True,
                                'span': 12,
                                'placeholder': '系统自动生成或手动输入'
                            },
                            {
                                'name': 'paper_type',
                                'label': '论文类型',
                                'type': 'select',
                                'required': True,
                                'span': 12,
                                'options': [
                                    {'label': '期刊论文', 'value': 'journal'},
                                    {'label': '会议论文', 'value': 'conference'},
                                    {'label': '学位论文', 'value': 'thesis'},
                                    {'label': '其他', 'value': 'other'}
                                ]
                            }
                        ]
                    },
                    {
                        'title': '作者信息',
                        'fields': [
                            {
                                'name': 'author',
                                'label': '作者',
                                'type': 'text',
                                'required': True,
                                'span': 12,
                                'placeholder': '请输入作者姓名'
                            },
                            {
                                'name': 'co_authors',
                                'label': '共同作者',
                                'type': 'text',
                                'span': 12,
                                'placeholder': '多个作者用逗号分隔'
                            },
                            {
                                'name': 'institution',
                                'label': '所属机构',
                                'type': 'text',
                                'required': True,
                                'span': 24,
                                'placeholder': '请输入所属机构'
                            },
                            {
                                'name': 'email',
                                'label': '联系邮箱',
                                'type': 'text',
                                'span': 12,
                                'placeholder': '请输入联系邮箱'
                            },
                            {
                                'name': 'phone',
                                'label': '联系电话',
                                'type': 'text',
                                'span': 12,
                                'placeholder': '请输入联系电话'
                            }
                        ]
                    },
                    {
                        'title': '发表信息',
                        'fields': [
                            {
                                'name': 'journal_name',
                                'label': '期刊/会议名称',
                                'type': 'text',
                                'span': 12,
                                'placeholder': '请输入期刊或会议名称'
                            },
                            {
                                'name': 'publish_date',
                                'label': '发表日期',
                                'type': 'date',
                                'span': 12,
                                'placeholder': '请选择发表日期'
                            },
                            {
                                'name': 'volume_issue',
                                'label': '卷期',
                                'type': 'text',
                                'span': 12,
                                'placeholder': '例如：Vol.10, No.3'
                            },
                            {
                                'name': 'page_range',
                                'label': '页码范围',
                                'type': 'text',
                                'span': 12,
                                'placeholder': '例如：123-135'
                            },
                            {
                                'name': 'doi',
                                'label': 'DOI',
                                'type': 'text',
                                'span': 24,
                                'placeholder': '请输入DOI'
                            }
                        ]
                    },
                    {
                        'title': '内容信息',
                        'fields': [
                            {
                                'name': 'keywords',
                                'label': '关键词',
                                'type': 'text',
                                'required': True,
                                'span': 24,
                                'placeholder': '多个关键词用逗号分隔'
                            },
                            {
                                'name': 'abstract',
                                'label': '摘要',
                                'type': 'textarea',
                                'required': True,
                                'span': 24,
                                'rows': 5,
                                'placeholder': '请输入论文摘要'
                            },
                            {
                                'name': 'research_field',
                                'label': '研究领域',
                                'type': 'select',
                                'span': 12,
                                'options': [
                                    {'label': '计算机科学', 'value': 'cs'},
                                    {'label': '电子工程', 'value': 'ee'},
                                    {'label': '材料科学', 'value': 'ms'},
                                    {'label': '化学', 'value': 'chem'},
                                    {'label': '物理', 'value': 'phys'},
                                    {'label': '生物', 'value': 'bio'},
                                    {'label': '其他', 'value': 'other'}
                                ]
                            },
                            {
                                'name': 'language',
                                'label': '语言',
                                'type': 'select',
                                'span': 12,
                                'options': [
                                    {'label': '中文', 'value': 'zh'},
                                    {'label': '英文', 'value': 'en'},
                                    {'label': '其他', 'value': 'other'}
                                ]
                            }
                        ]
                    },
                    {
                        'title': '质量评估',
                        'fields': [
                            {
                                'name': 'impact_factor',
                                'label': '影响因子',
                                'type': 'number',
                                'span': 12,
                                'min': 0,
                                'placeholder': '请输入影响因子'
                            },
                            {
                                'name': 'citation_count',
                                'label': '引用次数',
                                'type': 'number',
                                'span': 12,
                                'min': 0,
                                'placeholder': '请输入引用次数'
                            },
                            {
                                'name': 'peer_reviewed',
                                'label': '是否同行评审',
                                'type': 'radio',
                                'span': 12,
                                'options': [
                                    {'label': '是', 'value': '是'},
                                    {'label': '否', 'value': '否'}
                                ]
                            },
                            {
                                'name': 'open_access',
                                'label': '开放获取',
                                'type': 'radio',
                                'span': 12,
                                'options': [
                                    {'label': '是', 'value': '是'},
                                    {'label': '否', 'value': '否'}
                                ]
                            }
                        ]
                    },
                    {
                        'title': '备注信息',
                        'fields': [
                            {
                                'name': 'notes',
                                'label': '备注',
                                'type': 'textarea',
                                'span': 24,
                                'rows': 3,
                                'placeholder': '请输入备注信息'
                            }
                        ]
                    }
                ]
            },
            field_mapping={
                'paper_title': 'basic_data.paper_title',
                'paper_number': 'basic_data.paper_number',
                'author': 'basic_data.author',
                'institution': 'basic_data.institution'
            },
            validation_rules={
                'paper_title': {'required': True, 'min_length': 5},
                'paper_number': {'required': True, 'pattern': '^PAPER[0-9]{14}$'},
                'author': {'required': True},
                'email': {'pattern': '^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$'}
            },
            is_active=True,
            sort_order=2
        )
        
        db.session.add(paper_config)
        db.session.commit()
        
        print(f'✅ 论文配置创建成功: {paper_config.type_code}')
        print(f'   配置ID: {paper_config.id}')
        print(f'   包含 {len(paper_config.form_config.get("sections", []))} 个表单区块')
        
        # 显示配置的字段数量
        total_fields = sum(len(section.get('fields', [])) for section in paper_config.form_config.get('sections', []))
        print(f'   共 {total_fields} 个表单字段')


if __name__ == '__main__':
    create_paper_config()


