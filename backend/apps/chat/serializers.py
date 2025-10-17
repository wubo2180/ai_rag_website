from rest_framework import serializers
from .models import ChatSession, ChatMessage
from django.contrib.auth.models import User


class ChatSessionSerializer(serializers.ModelSerializer):
    """聊天会话序列化器"""
    user = serializers.StringRelatedField(read_only=True)
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'user', 'dify_conversation_id', 
            'created_at', 'updated_at', 'message_count', 'last_message'
        ]
        read_only_fields = ['id', 'dify_conversation_id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        """获取消息数量"""
        return obj.messages.count()
    
    def get_last_message(self, obj):
        """获取最后一条消息"""
        last_message = obj.messages.last()
        if last_message:
            return {
                'content': last_message.content[:100],
                'is_user': last_message.is_user,
                'timestamp': last_message.timestamp
            }
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    """聊天消息序列化器"""
    session = ChatSessionSerializer(read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'session', 'content', 'is_user', 
            'dify_message_id', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class ChatMessageCreateSerializer(serializers.Serializer):
    """创建聊天消息的序列化器"""
    message = serializers.CharField(max_length=5000, help_text="用户消息内容")
    session_id = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="会话ID（可选，不提供则创建新会话）")
    model = serializers.CharField(required=False, allow_blank=True, default='deepseek', help_text="使用的AI模型（可选）")
    
    def validate_message(self, value):
        """验证消息内容"""
        if not value or not value.strip():
            raise serializers.ValidationError("消息内容不能为空")
        return value.strip()
    
    def validate_session_id(self, value):
        """验证会话ID - 支持整数ID和UUID格式"""
        # 处理空值情况
        if not value or (isinstance(value, str) and value.strip() == ''):
            return None
        
        # 如果是字符串，去除空白字符
        if isinstance(value, str):
            value = value.strip()
            
        # 处理特殊值
        if value in ['null', 'undefined', 'None', '']:
            return None
        
        # 尝试转换为整数（数据库主键）
        try:
            int_value = int(value)
            if int_value <= 0:
                raise serializers.ValidationError("会话ID必须是正整数")
            return int_value
        except (ValueError, TypeError):
            pass
        
        # 如果不是整数，尝试UUID格式（向后兼容）
        import uuid
        try:
            uuid_obj = uuid.UUID(str(value))
            return str(uuid_obj)
        except (ValueError, TypeError, AttributeError):
            raise serializers.ValidationError(
                f"会话ID格式无效: '{value}'。请提供有效的整数ID、UUID格式或留空创建新会话。"
            )


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """创建聊天会话序列化器"""
    class Meta:
        model = ChatSession
        fields = ['title']
    
    def validate_title(self, value):
        """验证会话标题"""
        if not value.strip():
            raise serializers.ValidationError("会话标题不能为空")
        if len(value) > 100:
            raise serializers.ValidationError("会话标题不能超过100个字符")
        return value.strip()


class ChatSessionUpdateSerializer(serializers.ModelSerializer):
    """更新聊天会话序列化器"""
    class Meta:
        model = ChatSession
        fields = ['title']
    
    def validate_title(self, value):
        """验证会话标题"""
        if not value.strip():
            raise serializers.ValidationError("会话标题不能为空")
        if len(value) > 100:
            raise serializers.ValidationError("会话标题不能超过100个字符")
        return value.strip()


class ChatHistorySerializer(serializers.ModelSerializer):
    """聊天历史序列化器（包含消息）"""
    messages = ChatMessageSerializer(many=True, read_only=True)
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = ChatSession
        fields = [
            'id', 'title', 'user', 'dify_conversation_id',
            'created_at', 'updated_at', 'messages'
        ]
        read_only_fields = ['id', 'dify_conversation_id', 'created_at', 'updated_at']