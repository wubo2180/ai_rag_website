"""
智能体模块模型
包含智能体定义、任务、执行记录等
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
import json


class AgentCategory(models.TextChoices):
    """智能体分类"""
    DATA_ANALYSIS = 'data_analysis', '数据分析'
    PROPERTY_PREDICTION = 'property_prediction', '性质预测'  
    PROCESS_OPTIMIZATION = 'process_optimization', '工艺优化'
    KNOWLEDGE_EXTRACTION = 'knowledge_extraction', '知识抽取'
    DECISION_SUPPORT = 'decision_support', '决策支持'
    OTHER = 'other', '其他'


class AgentStatus(models.TextChoices):
    """智能体状态"""
    ACTIVE = 'active', '活跃'
    INACTIVE = 'inactive', '非活跃'
    MAINTENANCE = 'maintenance', '维护中'
    DEPRECATED = 'deprecated', '已弃用'


class TaskStatus(models.TextChoices):
    """任务状态"""
    PENDING = 'pending', '等待中'
    RUNNING = 'running', '执行中'
    COMPLETED = 'completed', '已完成'
    FAILED = 'failed', '失败'
    CANCELLED = 'cancelled', '已取消'


class SmartAgent(models.Model):
    """智能体模型"""
    
    # 基本信息
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, verbose_name='智能体名称')
    display_name = models.CharField(max_length=200, verbose_name='显示名称')
    description = models.TextField(verbose_name='描述')
    category = models.CharField(
        max_length=50, 
        choices=AgentCategory.choices, 
        default=AgentCategory.OTHER,
        verbose_name='分类'
    )
    
    # 外观和图标
    icon = models.CharField(max_length=100, blank=True, verbose_name='图标类名')
    color_theme = models.CharField(max_length=20, default='blue', verbose_name='主题色')
    avatar_url = models.URLField(blank=True, verbose_name='头像URL')
    
    # 功能配置
    capabilities = models.JSONField(default=list, verbose_name='能力列表')
    supported_inputs = models.JSONField(default=list, verbose_name='支持的输入类型')
    supported_outputs = models.JSONField(default=list, verbose_name='支持的输出类型')
    
    # AI模型配置
    ai_model = models.CharField(max_length=100, verbose_name='AI模型', help_text='如: gpt-4, claude-3等')
    model_config = models.JSONField(default=dict, verbose_name='模型配置')
    prompt_template = models.TextField(verbose_name='提示词模板')
    
    # 状态和权限
    status = models.CharField(
        max_length=20, 
        choices=AgentStatus.choices, 
        default=AgentStatus.ACTIVE,
        verbose_name='状态'
    )
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    popularity_score = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(10.0)],
        verbose_name='受欢迎程度'
    )
    
    # 统计信息
    usage_count = models.PositiveIntegerField(default=0, verbose_name='使用次数')
    success_rate = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name='成功率'
    )
    average_execution_time = models.FloatField(default=0.0, verbose_name='平均执行时间(秒)')
    
    # 元数据
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='created_agents',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    version = models.CharField(max_length=20, default='1.0.0', verbose_name='版本')
    
    class Meta:
        db_table = 'smart_agent'
        verbose_name = '智能体'
        verbose_name_plural = '智能体'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.display_name} ({self.name})"
    
    def update_statistics(self):
        """更新统计信息"""
        tasks = self.tasks.all()
        if tasks.exists():
            completed_tasks = tasks.filter(status=TaskStatus.COMPLETED)
            self.success_rate = completed_tasks.count() / tasks.count()
            
            if completed_tasks.exists():
                total_time = sum(task.execution_time or 0 for task in completed_tasks)
                self.average_execution_time = total_time / completed_tasks.count()
        
        self.save(update_fields=['success_rate', 'average_execution_time'])


class AgentTask(models.Model):
    """智能体任务"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(SmartAgent, on_delete=models.CASCADE, related_name='tasks')
    
    # 任务信息
    title = models.CharField(max_length=200, verbose_name='任务标题')
    description = models.TextField(blank=True, verbose_name='任务描述')
    
    # 输入输出
    input_data = models.JSONField(verbose_name='输入数据')
    output_data = models.JSONField(null=True, blank=True, verbose_name='输出数据')
    
    # 执行状态
    status = models.CharField(
        max_length=20,
        choices=TaskStatus.choices,
        default=TaskStatus.PENDING,
        verbose_name='状态'
    )
    progress = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name='进度百分比'
    )
    
    # 执行信息
    started_at = models.DateTimeField(null=True, blank=True, verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    execution_time = models.FloatField(null=True, blank=True, verbose_name='执行时间(秒)')
    
    # 错误信息
    error_message = models.TextField(blank=True, verbose_name='错误信息')
    error_traceback = models.TextField(blank=True, verbose_name='错误堆栈')
    
    # 元数据
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'agent_task'
        verbose_name = '智能体任务'
        verbose_name_plural = '智能体任务'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.agent.display_name}"


class AgentExecution(models.Model):
    """智能体执行记录"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, related_name='executions')
    
    # 执行步骤
    step_name = models.CharField(max_length=100, verbose_name='步骤名称')
    step_order = models.PositiveIntegerField(verbose_name='步骤顺序')
    
    # 执行详情
    input_data = models.JSONField(verbose_name='步骤输入')
    output_data = models.JSONField(null=True, blank=True, verbose_name='步骤输出')
    
    # 时间记录
    started_at = models.DateTimeField(verbose_name='开始时间')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='完成时间')
    
    # 状态和日志
    status = models.CharField(max_length=20, choices=TaskStatus.choices, verbose_name='状态')
    logs = models.TextField(blank=True, verbose_name='执行日志')
    
    class Meta:
        db_table = 'agent_execution'
        verbose_name = '执行记录'
        verbose_name_plural = '执行记录'
        ordering = ['step_order']
    
    def __str__(self):
        return f"{self.task.title} - {self.step_name}"


class AgentFeedback(models.Model):
    """智能体反馈"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(SmartAgent, on_delete=models.CASCADE, related_name='feedbacks')
    task = models.ForeignKey(AgentTask, on_delete=models.CASCADE, null=True, blank=True)
    
    # 反馈内容
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name='评分(1-5)'
    )
    comment = models.TextField(blank=True, verbose_name='评论')
    
    # 标签
    tags = models.JSONField(default=list, verbose_name='标签')
    
    # 元数据
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='反馈者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'agent_feedback'
        verbose_name = '智能体反馈'
        verbose_name_plural = '智能体反馈'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.agent.display_name} - {self.rating}星"
