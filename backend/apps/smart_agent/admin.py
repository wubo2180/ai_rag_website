"""
智能体模块管理后台
"""
from django.contrib import admin
from .models import SmartAgent, AgentTask, AgentExecution, AgentFeedback


@admin.register(SmartAgent)
class SmartAgentAdmin(admin.ModelAdmin):
    """智能体管理"""
    
    list_display = [
        'display_name', 'name', 'category', 'status', 'is_public',
        'usage_count', 'success_rate', 'popularity_score', 'created_at'
    ]
    list_filter = ['category', 'status', 'is_public', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['id', 'usage_count', 'success_rate', 'average_execution_time', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('id', 'name', 'display_name', 'description', 'category')
        }),
        ('外观配置', {
            'fields': ('icon', 'color_theme', 'avatar_url'),
            'classes': ('collapse',)
        }),
        ('功能配置', {
            'fields': ('capabilities', 'supported_inputs', 'supported_outputs')
        }),
        ('AI模型配置', {
            'fields': ('ai_model', 'model_config', 'prompt_template')
        }),
        ('状态和权限', {
            'fields': ('status', 'is_public', 'popularity_score')
        }),
        ('统计信息', {
            'fields': ('usage_count', 'success_rate', 'average_execution_time'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at', 'version'),
            'classes': ('collapse',)
        })
    )


@admin.register(AgentTask)
class AgentTaskAdmin(admin.ModelAdmin):
    """任务管理"""
    
    list_display = [
        'title', 'agent', 'status', 'progress', 'created_by',
        'started_at', 'completed_at', 'created_at'
    ]
    list_filter = ['status', 'agent', 'created_at']
    search_fields = ['title', 'description', 'agent__display_name']
    readonly_fields = ['id', 'execution_time', 'created_at', 'updated_at']
    
    fieldsets = (
        ('任务信息', {
            'fields': ('id', 'agent', 'title', 'description')
        }),
        ('输入输出', {
            'fields': ('input_data', 'output_data')
        }),
        ('执行状态', {
            'fields': ('status', 'progress', 'started_at', 'completed_at', 'execution_time')
        }),
        ('错误信息', {
            'fields': ('error_message', 'error_traceback'),
            'classes': ('collapse',)
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(AgentExecution)
class AgentExecutionAdmin(admin.ModelAdmin):
    """执行记录管理"""
    
    list_display = [
        'task', 'step_name', 'step_order', 'status',
        'started_at', 'completed_at'
    ]
    list_filter = ['status', 'task__agent', 'started_at']
    search_fields = ['task__title', 'step_name']
    readonly_fields = ['id']
    
    fieldsets = (
        ('执行信息', {
            'fields': ('id', 'task', 'step_name', 'step_order')
        }),
        ('数据', {
            'fields': ('input_data', 'output_data')
        }),
        ('时间和状态', {
            'fields': ('started_at', 'completed_at', 'status')
        }),
        ('日志', {
            'fields': ('logs',),
            'classes': ('collapse',)
        })
    )


@admin.register(AgentFeedback)
class AgentFeedbackAdmin(admin.ModelAdmin):
    """反馈管理"""
    
    list_display = [
        'agent', 'rating', 'created_by', 'created_at'
    ]
    list_filter = ['rating', 'agent', 'created_at']
    search_fields = ['agent__display_name', 'comment', 'created_by__username']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('反馈信息', {
            'fields': ('id', 'agent', 'task', 'rating')
        }),
        ('内容', {
            'fields': ('comment', 'tags')
        }),
        ('元数据', {
            'fields': ('created_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
