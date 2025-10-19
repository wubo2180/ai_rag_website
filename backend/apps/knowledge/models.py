from django.db import models
from django.contrib.auth.models import User

class Knowledge(models.Model):
    """知识库条目"""
    title = models.CharField(max_length=200, verbose_name='标题')
    content = models.TextField(verbose_name='内容')
    category = models.CharField(max_length=100, blank=True, verbose_name='分类')
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    
    class Meta:
        verbose_name = '知识条目'
        verbose_name_plural = '知识条目'
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.title

class Document(models.Model):
    """文档模型"""
    title = models.CharField(max_length=200, verbose_name='文档标题')
    content = models.TextField(verbose_name='文档内容')
    file_path = models.FileField(upload_to='documents/', blank=True, null=True, verbose_name='文件路径')
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    processed = models.BooleanField(default=False, verbose_name='是否已处理')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='上传者')
    
    class Meta:
        verbose_name = '文档'
        verbose_name_plural = '文档'
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title

class KnowledgeChunk(models.Model):
    """知识块模型"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks', verbose_name='所属文档')
    content = models.TextField(verbose_name='内容')
    chunk_index = models.IntegerField(verbose_name='块索引')
    embedding_id = models.CharField(max_length=100, unique=True, verbose_name='嵌入ID')
    
    class Meta:
        unique_together = ['document', 'chunk_index']
        verbose_name = '知识块'
        verbose_name_plural = '知识块'


# ==================== 材料知识图谱模型 ====================
# 构建：原材料 → 中间体 → 配方 → 性能 四级关联数据链

class RawMaterial(models.Model):
    """第一级：原材料实体"""
    
    MATERIAL_TYPES = [
        ('polymer', '聚合物'),
        ('additive', '添加剂'),
        ('filler', '填料'),
        ('catalyst', '催化剂'),
        ('solvent', '溶剂'),
        ('other', '其他'),
    ]
    
    # 基本信息
    code = models.CharField(max_length=50, unique=True, verbose_name='原料编码')
    name = models.CharField(max_length=200, verbose_name='原料名称')
    chemical_name = models.CharField(max_length=300, blank=True, verbose_name='化学名称')
    cas_number = models.CharField(max_length=50, blank=True, verbose_name='CAS号')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES, verbose_name='材料类型')
    
    # 物理化学性质
    molecular_formula = models.CharField(max_length=200, blank=True, verbose_name='分子式')
    molecular_weight = models.FloatField(null=True, blank=True, verbose_name='分子量')
    density = models.FloatField(null=True, blank=True, verbose_name='密度 (g/cm³)')
    viscosity = models.FloatField(null=True, blank=True, verbose_name='粘度 (Pa·s)')
    
    # 供应商信息
    supplier = models.CharField(max_length=200, blank=True, verbose_name='供应商')
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name='单价')
    
    # 扩展属性（JSON格式）
    properties = models.JSONField(default=dict, blank=True, verbose_name='其他属性')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='raw_materials', verbose_name='创建人')
    
    class Meta:
        db_table = 'kg_raw_material'
        verbose_name = '原材料'
        verbose_name_plural = '原材料'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Intermediate(models.Model):
    """第二级：中间体实体"""
    
    INTERMEDIATE_TYPES = [
        ('prepolymer', '预聚物'),
        ('resin', '树脂'),
        ('compound', '复合物'),
        ('mixture', '混合物'),
        ('other', '其他'),
    ]
    
    # 基本信息
    code = models.CharField(max_length=50, unique=True, verbose_name='中间体编码')
    name = models.CharField(max_length=200, verbose_name='中间体名称')
    intermediate_type = models.CharField(max_length=20, choices=INTERMEDIATE_TYPES, verbose_name='中间体类型')
    
    # 制备信息
    preparation_method = models.TextField(blank=True, verbose_name='制备方法')
    reaction_conditions = models.JSONField(default=dict, blank=True, verbose_name='反应条件')
    
    # 性质
    viscosity = models.FloatField(null=True, blank=True, verbose_name='粘度')
    solid_content = models.FloatField(null=True, blank=True, verbose_name='固含量 (%)')
    
    # 与原材料的多对多关联
    raw_materials = models.ManyToManyField(
        RawMaterial,
        through='IntermediateComposition',
        related_name='intermediates',
        verbose_name='原材料组成'
    )
    
    # 扩展属性
    properties = models.JSONField(default=dict, blank=True, verbose_name='其他属性')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='intermediates', verbose_name='创建人')
    
    class Meta:
        db_table = 'kg_intermediate'
        verbose_name = '中间体'
        verbose_name_plural = '中间体'
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class IntermediateComposition(models.Model):
    """中间体组成关系（原材料→中间体）"""
    
    intermediate = models.ForeignKey(Intermediate, on_delete=models.CASCADE, verbose_name='中间体')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, verbose_name='原材料')
    
    # 配比信息
    weight_ratio = models.FloatField(verbose_name='质量比 (%)')
    addition_order = models.IntegerField(default=1, verbose_name='添加顺序')
    addition_temperature = models.FloatField(null=True, blank=True, verbose_name='添加温度 (℃)')
    addition_notes = models.TextField(blank=True, verbose_name='添加说明')
    
    class Meta:
        db_table = 'kg_intermediate_composition'
        verbose_name = '中间体组成'
        verbose_name_plural = '中间体组成'
        unique_together = [['intermediate', 'raw_material']]
    
    def __str__(self):
        return f"{self.intermediate.name} - {self.raw_material.name} ({self.weight_ratio}%)"


class Formula(models.Model):
    """第三级：配方实体"""
    
    FORMULA_STATUS = [
        ('draft', '草稿'),
        ('testing', '测试中'),
        ('validated', '已验证'),
        ('production', '生产中'),
        ('archived', '已归档'),
    ]
    
    APPLICATION_TYPES = [
        ('sealant', '密封胶'),
        ('adhesive', '粘合剂'),
        ('coating', '涂料'),
        ('composite', '复合材料'),
        ('other', '其他'),
    ]
    
    # 基本信息
    code = models.CharField(max_length=50, unique=True, verbose_name='配方编码')
    name = models.CharField(max_length=200, verbose_name='配方名称')
    version = models.CharField(max_length=20, default='1.0', verbose_name='版本号')
    status = models.CharField(max_length=20, choices=FORMULA_STATUS, default='draft', verbose_name='状态')
    application_type = models.CharField(max_length=20, choices=APPLICATION_TYPES, verbose_name='应用类型')
    
    # 工艺参数
    mixing_temperature = models.FloatField(null=True, blank=True, verbose_name='混合温度 (℃)')
    mixing_time = models.FloatField(null=True, blank=True, verbose_name='混合时间 (min)')
    curing_temperature = models.FloatField(null=True, blank=True, verbose_name='固化温度 (℃)')
    curing_time = models.FloatField(null=True, blank=True, verbose_name='固化时间 (h)')
    
    # 与中间体的多对多关联
    intermediates = models.ManyToManyField(
        Intermediate,
        through='FormulaComposition',
        related_name='formulas',
        verbose_name='中间体组成'
    )
    
    # 工艺描述
    process_description = models.TextField(blank=True, verbose_name='工艺描述')
    precautions = models.TextField(blank=True, verbose_name='注意事项')
    
    # 扩展属性
    properties = models.JSONField(default=dict, blank=True, verbose_name='其他属性')
    
    # 元数据
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='formulas', verbose_name='创建人')
    
    class Meta:
        db_table = 'kg_formula'
        verbose_name = '配方'
        verbose_name_plural = '配方'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.code} - {self.name} (v{self.version})"


class FormulaComposition(models.Model):
    """配方组成关系（中间体/原材料→配方）"""
    
    COMPONENT_TYPES = [
        ('intermediate', '中间体'),
        ('raw_material', '原材料'),
    ]
    
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE, related_name='components', verbose_name='配方')
    component_type = models.CharField(max_length=20, choices=COMPONENT_TYPES, verbose_name='组分类型')
    
    # 关联到中间体或原材料
    intermediate = models.ForeignKey(Intermediate, on_delete=models.CASCADE, null=True, blank=True, verbose_name='中间体')
    raw_material = models.ForeignKey(RawMaterial, on_delete=models.CASCADE, null=True, blank=True, verbose_name='原材料')
    
    # 配比信息
    weight_ratio = models.FloatField(verbose_name='质量比 (%)')
    addition_order = models.IntegerField(default=1, verbose_name='添加顺序')
    addition_notes = models.TextField(blank=True, verbose_name='添加说明')
    
    class Meta:
        db_table = 'kg_formula_composition'
        verbose_name = '配方组成'
        verbose_name_plural = '配方组成'
        ordering = ['addition_order']
    
    def __str__(self):
        component_name = self.intermediate.name if self.intermediate else self.raw_material.name
        return f"{self.formula.name} - {component_name} ({self.weight_ratio}%)"


class Performance(models.Model):
    """第四级：性能数据实体"""
    
    TEST_METHODS = [
        ('GB', '国标GB'),
        ('ISO', '国际标准ISO'),
        ('ASTM', '美国标准ASTM'),
        ('internal', '内部标准'),
        ('other', '其他'),
    ]
    
    # 关联配方
    formula = models.ForeignKey(Formula, on_delete=models.CASCADE, related_name='performances', verbose_name='配方')
    
    # 测试信息
    test_batch = models.CharField(max_length=50, verbose_name='测试批次')
    test_date = models.DateField(verbose_name='测试日期')
    test_method = models.CharField(max_length=20, choices=TEST_METHODS, verbose_name='测试标准')
    test_conditions = models.JSONField(default=dict, blank=True, verbose_name='测试条件')
    
    # 力学性能
    tensile_strength = models.FloatField(null=True, blank=True, verbose_name='拉伸强度 (MPa)')
    elongation_at_break = models.FloatField(null=True, blank=True, verbose_name='断裂伸长率 (%)')
    tear_strength = models.FloatField(null=True, blank=True, verbose_name='撕裂强度 (N/mm)')
    hardness = models.FloatField(null=True, blank=True, verbose_name='硬度 (Shore A)')
    
    # 粘接性能
    adhesion_strength = models.FloatField(null=True, blank=True, verbose_name='粘接强度 (MPa)')
    
    # 耐候性能
    weather_resistance = models.CharField(max_length=100, blank=True, verbose_name='耐候性')
    water_resistance = models.CharField(max_length=100, blank=True, verbose_name='耐水性')
    
    # 热性能
    heat_resistance_temp = models.FloatField(null=True, blank=True, verbose_name='耐热温度 (℃)')
    cold_resistance_temp = models.FloatField(null=True, blank=True, verbose_name='耐寒温度 (℃)')
    
    # 其他性能
    viscosity = models.FloatField(null=True, blank=True, verbose_name='粘度 (Pa·s)')
    density = models.FloatField(null=True, blank=True, verbose_name='密度 (g/cm³)')
    tack_free_time = models.FloatField(null=True, blank=True, verbose_name='表干时间 (h)')
    full_cure_time = models.FloatField(null=True, blank=True, verbose_name='完全固化时间 (h)')
    
    # 扩展性能数据
    additional_properties = models.JSONField(default=dict, blank=True, verbose_name='其他性能')
    
    # 评价
    overall_rating = models.IntegerField(
        null=True, 
        blank=True, 
        choices=[(i, f'{i}分') for i in range(1, 6)],
        verbose_name='综合评分'
    )
    notes = models.TextField(blank=True, verbose_name='备注')
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    tested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='performance_tests', verbose_name='测试人')
    
    class Meta:
        db_table = 'kg_performance'
        verbose_name = '性能数据'
        verbose_name_plural = '性能数据'
        ordering = ['-test_date']
    
    def __str__(self):
        return f"{self.formula.name} - 批次{self.test_batch} ({self.test_date})"


class KnowledgeGraphRelation(models.Model):
    """知识图谱关系索引（用于快速查询和可视化）"""
    
    RELATION_TYPES = [
        ('raw_to_intermediate', '原材料→中间体'),
        ('intermediate_to_formula', '中间体→配方'),
        ('raw_to_formula', '原材料→配方'),
        ('formula_to_performance', '配方→性能'),
    ]
    
    relation_type = models.CharField(max_length=30, choices=RELATION_TYPES, verbose_name='关系类型')
    
    # 源节点和目标节点
    source_type = models.CharField(max_length=50, verbose_name='源节点类型')
    source_id = models.IntegerField(verbose_name='源节点ID')
    source_name = models.CharField(max_length=200, verbose_name='源节点名称')
    
    target_type = models.CharField(max_length=50, verbose_name='目标节点类型')
    target_id = models.IntegerField(verbose_name='目标节点ID')
    target_name = models.CharField(max_length=200, verbose_name='目标节点名称')
    
    # 关系属性
    weight = models.FloatField(default=1.0, verbose_name='关系权重')
    properties = models.JSONField(default=dict, blank=True, verbose_name='关系属性')
    
    # 元数据
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'kg_relation'
        verbose_name = '知识图谱关系'
        verbose_name_plural = '知识图谱关系'
        indexes = [
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['relation_type']),
        ]
    
    def __str__(self):
        return f"{self.source_name} → {self.target_name} ({self.get_relation_type_display()})"