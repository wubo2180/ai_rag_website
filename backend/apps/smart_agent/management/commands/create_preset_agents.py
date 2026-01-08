"""
创建预设智能体的管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.smart_agent.models import SmartAgent, AgentCategory, AgentStatus


class Command(BaseCommand):
    help = '创建预设的智能体'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='删除现有智能体并重新创建',
        )
    
    def handle(self, *args, **options):
        """执行命令"""
        
        if options['reset']:
            SmartAgent.objects.all().delete()
            self.stdout.write(
                self.style.WARNING('已删除所有现有智能体')
            )
        
        # 获取或创建超级用户作为创建者
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser(
                'admin', 'admin@example.com', 'admin123'
            )
        
        # 预设智能体数据
        agents_data = [
            {
                'name': 'data_chain_generator',
                'display_name': '四级关联数据链生成智能体',
                'description': '基于材料基因工程理论，自动构建"成分-工艺-结构-性能"四级关联数据链。能够从原始数据中提取关键信息，建立材料成分、制备工艺、微观结构与宏观性能之间的关联关系。',
                'category': AgentCategory.DATA_ANALYSIS,
                'icon': 'mdi-link-variant',
                'color_theme': 'blue',
                'capabilities': [
                    '数据清洗与预处理',
                    '特征提取与工程',
                    '关联关系分析',
                    '数据链可视化',
                    '异常检测'
                ],
                'supported_inputs': ['csv', 'excel', 'json', 'database'],
                'supported_outputs': ['关联图谱', '数据报告', '可视化图表'],
                'ai_model': 'gpt-4',
                'model_config': {
                    'temperature': 0.3,
                    'max_tokens': 2000
                },
                'prompt_template': '''
你是一个材料基因工程专家，专门分析材料的"成分-工艺-结构-性能"四级关联关系。

请分析以下材料数据：
{input_data}

任务要求：
1. 识别材料成分信息
2. 分析制备工艺参数
3. 描述微观结构特征
4. 评估宏观性能表现
5. 建立四级关联关系

输出格式：
- 成分分析
- 工艺解析
- 结构特征
- 性能评价
- 关联关系图
'''
            },
            {
                'name': 'formula_generator',
                'display_name': '产品配方生成智能体',
                'description': '基于材料基因工程理论和机器学习算法，智能生成满足特定性能要求的材料配方。能够根据目标性能、成本约束、环保要求等多维度条件，自动推荐最优成分配比和工艺参数组合。支持新材料配方设计、现有配方优化、替代材料方案生成等多种应用场景。',
                'category': AgentCategory.FORMULA_GENERATION,
                'icon': 'fas fa-vial',
                'color_theme': 'teal',
                'capabilities': [
                    '智能配方设计',
                    '成分配比优化',
                    '性能目标匹配',
                    '成本约束分析',
                    '环保合规检查',
                    '工艺参数推荐',
                    '替代方案生成',
                    '配方可行性评估'
                ],
                'supported_inputs': ['性能需求', '应用场景', '成本约束', '环保要求', '工艺条件'],
                'supported_outputs': ['配方方案', '成分配比表', '工艺参数', '性能预测', '成本分析'],
                'ai_model': 'gpt-4',
                'model_config': {
                    'temperature': 0.4,
                    'max_tokens': 2500
                },
                'prompt_template': '''
你是一个材料配方设计专家，精通材料基因工程和配方优化理论，能够根据性能需求智能生成最优材料配方。

用户需求：
{input_data}

任务要求：
1. 分析目标性能指标和约束条件
2. 基于材料数据库和成分-性能关联关系，设计候选配方
3. 优化成分配比，确保性能达标
4. 评估配方的成本效益和可行性
5. 提供详细的工艺参数建议

输出格式：
**一、配方概述**
- 配方编号和名称
- 适用场景
- 核心性能指标

**二、成分配比**
- 主要成分及配比（重量百分比）
- 添加剂及用量
- 成分选择依据

**三、工艺参数**
- 混合工艺条件
- 加工温度和压力
- 固化/烧结条件
- 后处理工艺

**四、性能预测**
- 力学性能预测值
- 物理化学性能
- 耐久性和稳定性
- 性能置信区间

**五、成本分析**
- 原材料成本估算
- 加工成本评估
- 总成本预测
- 性价比分析

**六、优势与注意事项**
- 配方优势特点
- 潜在风险提示
- 质量控制要点
- 优化建议

**七、替代方案**（如有）
- 备选配方方案
- 方案对比分析
'''
            },
            {
                'name': 'property_predictor',
                'display_name': '化学性质预测智能体',
                'description': '基于机器学习和深度学习算法，预测材料的物理化学性质。能够根据材料成分、结构信息预测力学性能、电学性能、热学性能等关键属性。',
                'category': AgentCategory.PROPERTY_PREDICTION,
                'icon': 'mdi-flask',
                'color_theme': 'green',
                'capabilities': [
                    '力学性能预测',
                    '电学性能预测',
                    '热学性能预测',
                    '化学稳定性预测',
                    '性能优化建议'
                ],
                'supported_inputs': ['molecular_structure', 'composition', 'crystal_structure'],
                'supported_outputs': ['性能预测报告', '置信区间', '优化建议'],
                'ai_model': 'gpt-4',
                'model_config': {
                    'temperature': 0.2,
                    'max_tokens': 1500
                },
                'prompt_template': '''
你是一个材料性质预测专家，能够基于材料的成分和结构信息预测其物理化学性质。

材料信息：
{input_data}

请预测以下性质：
1. 力学性能（强度、硬度、韧性等）
2. 电学性能（导电性、介电常数等）
3. 热学性能（导热性、热膨胀系数等）
4. 化学稳定性（耐腐蚀性、氧化性等）

输出要求：
- 具体数值预测（包含置信区间）
- 预测依据说明
- 性能优化建议
- 相关文献参考
'''
            },
            {
                'name': 'process_optimizer',
                'display_name': '生产流程工艺优化智能体',
                'description': '针对材料制备和生产过程进行工艺参数优化。通过分析历史数据和工艺条件，提供最佳的生产参数组合，提高产品质量和生产效率。',
                'category': AgentCategory.PROCESS_OPTIMIZATION,
                'icon': 'mdi-cog',
                'color_theme': 'orange',
                'capabilities': [
                    '工艺参数优化',
                    '生产效率提升',
                    '质量控制优化',
                    '成本分析',
                    '工艺流程设计'
                ],
                'supported_inputs': ['工艺参数', '生产数据', '质量指标'],
                'supported_outputs': ['优化方案', '参数推荐', '效果预测'],
                'ai_model': 'gpt-4',
                'model_config': {
                    'temperature': 0.1,
                    'max_tokens': 2000
                },
                'prompt_template': '''
你是一个生产工艺优化专家，专门分析和优化材料制备生产流程。

当前工艺数据：
{input_data}

优化目标：
1. 提高产品质量
2. 降低生产成本
3. 提升生产效率
4. 减少环境影响

请提供：
- 关键工艺参数分析
- 优化参数建议
- 预期改善效果
- 实施风险评估
- 监控指标建议
'''
            },
            {
                'name': 'knowledge_extractor',
                'display_name': '科技文献知识抽取智能体',
                'description': '从科技文献、专利、研究报告中自动抽取材料相关的关键信息。能够识别材料名称、性能数据、制备方法等结构化信息。',
                'category': AgentCategory.KNOWLEDGE_EXTRACTION,
                'icon': 'mdi-book-open-variant',
                'color_theme': 'purple',
                'capabilities': [
                    '文献信息抽取',
                    '专利分析',
                    '数据结构化',
                    '知识图谱构建',
                    '文本挖掘'
                ],
                'supported_inputs': ['pdf', 'txt', 'html', 'xml'],
                'supported_outputs': ['结构化数据', '知识图谱', '摘要报告'],
                'ai_model': 'gpt-4',
                'model_config': {
                    'temperature': 0.2,
                    'max_tokens': 1800
                },
                'prompt_template': '''
你是一个科技文献知识抽取专家，专门从材料科学文献中提取关键信息。

文献内容：
{input_data}

请提取以下信息：
1. 材料名称和分类
2. 化学成分和配比
3. 制备工艺和条件
4. 性能测试数据
5. 应用领域

输出格式：
- 结构化数据表
- 关键发现摘要
- 技术特点分析
- 应用前景评估
'''
            },
            {
                'name': 'decision_support',
                'display_name': '材料选择决策支持智能体',
                'description': '为特定应用场景推荐最适合的材料选择。综合考虑性能要求、成本约束、加工难度等因素，提供材料选择的决策支持。',
                'category': AgentCategory.DECISION_SUPPORT,
                'icon': 'mdi-chart-line',
                'color_theme': 'red',
                'capabilities': [
                    '材料性能匹配',
                    '成本效益分析',
                    '风险评估',
                    '替代方案推荐',
                    '决策树构建'
                ],
                'supported_inputs': ['需求规格', '约束条件', '材料数据库'],
                'supported_outputs': ['推荐方案', '对比分析', '决策报告'],
                'ai_model': 'gpt-4',
                'model_config': {
                    'temperature': 0.3,
                    'max_tokens': 2000
                },
                'prompt_template': '''
你是一个材料选择决策专家，能够为特定应用推荐最佳材料方案。

应用需求：
{input_data}

决策考虑因素：
1. 性能要求匹配度
2. 成本效益分析
3. 加工制造难度
4. 供应链可靠性
5. 环境影响评估

请提供：
- 推荐材料清单（排序）
- 每种材料的优缺点分析
- 成本效益比较
- 实施建议和风险提示
'''
            }
        ]
        
        # 创建智能体
        created_count = 0
        for agent_data in agents_data:
            agent, created = SmartAgent.objects.get_or_create(
                name=agent_data['name'],
                defaults={
                    **agent_data,
                    'created_by': admin_user,
                    'status': AgentStatus.ACTIVE,
                    'is_public': True,
                    'popularity_score': 8.0,
                    'version': '1.0.0'
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 创建智能体: {agent.display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  智能体已存在: {agent.display_name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 完成！共创建了 {created_count} 个新智能体')
        )