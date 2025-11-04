"""
智能体模块序列化器
"""
from rest_framework import serializers
from .models import SmartAgent, AgentTask, AgentExecution, AgentFeedback


class SmartAgentSerializer(serializers.ModelSerializer):
    """智能体序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SmartAgent
        fields = [
            'id', 'name', 'display_name', 'description', 'category',
            'icon', 'color_theme', 'avatar_url',
            'capabilities', 'supported_inputs', 'supported_outputs',
            'ai_model', 'model_config', 'prompt_template',
            'status', 'is_public', 'popularity_score',
            'usage_count', 'success_rate', 'average_execution_time',
            'created_by', 'created_by_name', 'created_at', 'updated_at', 'version',
            'task_count'
        ]
        read_only_fields = ['id', 'usage_count', 'success_rate', 'average_execution_time', 'created_at', 'updated_at']
    
    def get_task_count(self, obj):
        """获取任务数量"""
        return obj.tasks.count()
    
    def create(self, validated_data):
        """创建智能体"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class AgentTaskSerializer(serializers.ModelSerializer):
    """任务序列化器"""
    
    agent_name = serializers.CharField(source='agent.display_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    execution_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AgentTask
        fields = [
            'id', 'agent', 'agent_name', 'title', 'description',
            'input_data', 'output_data', 'status', 'progress',
            'started_at', 'completed_at', 'execution_time',
            'error_message', 'error_traceback',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
            'execution_count'
        ]
        read_only_fields = ['id', 'started_at', 'completed_at', 'execution_time', 'created_at', 'updated_at']
    
    def get_execution_count(self, obj):
        """获取执行步骤数量"""
        return obj.executions.count()
    
    def create(self, validated_data):
        """创建任务"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


class AgentExecutionSerializer(serializers.ModelSerializer):
    """执行记录序列化器"""
    
    task_title = serializers.CharField(source='task.title', read_only=True)
    
    class Meta:
        model = AgentExecution
        fields = [
            'id', 'task', 'task_title', 'step_name', 'step_order',
            'input_data', 'output_data', 'started_at', 'completed_at',
            'status', 'logs'
        ]
        read_only_fields = ['id']


class AgentFeedbackSerializer(serializers.ModelSerializer):
    """反馈序列化器"""
    
    agent_name = serializers.CharField(source='agent.display_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AgentFeedback
        fields = [
            'id', 'agent', 'agent_name', 'task', 'rating', 'comment', 'tags',
            'created_by', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        """创建反馈"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['created_by'] = request.user
        return super().create(validated_data)


# 简化序列化器用于列表显示
class SmartAgentListSerializer(serializers.ModelSerializer):
    """智能体列表序列化器"""
    
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    task_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SmartAgent
        fields = [
            'id', 'name', 'display_name', 'description', 'category',
            'icon', 'color_theme', 'status', 'is_public', 'popularity_score',
            'usage_count', 'success_rate', 'created_by_name', 'created_at',
            'task_count'
        ]
    
    def get_task_count(self, obj):
        return obj.tasks.count()


class AgentTaskListSerializer(serializers.ModelSerializer):
    """任务列表序列化器"""
    
    agent_name = serializers.CharField(source='agent.display_name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AgentTask
        fields = [
            'id', 'agent_name', 'title', 'status', 'progress',
            'started_at', 'completed_at', 'created_by_name', 'created_at'
        ]