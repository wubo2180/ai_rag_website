from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Document, DocumentCategory, DocumentAccess, DocumentFolder


class DocumentCategorySerializer(serializers.ModelSerializer):
    """文献分类序列化器"""
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentCategory
        fields = [
            'id', 'name', 'description', 'color', 
            'created_by', 'created_at', 'updated_at', 'document_count'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_document_count(self, obj):
        """获取分类下的文档数量"""
        try:
            return obj.documents.count()
        except Exception:
            return 0
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class DocumentUploadSerializer(serializers.ModelSerializer):
    """文档上传序列化器"""
    
    class Meta:
        model = Document
        fields = [
            'title', 'description', 'file', 'category', 'folder', 'tags', 'is_public'
        ]
    
    def validate_file(self, value):
        """验证文件"""
        # 检查文件大小（限制为50MB）
        max_size = 50 * 1024 * 1024  # 50MB
        if value.size > max_size:
            raise serializers.ValidationError("文件大小不能超过50MB")
        
        # 检查文件类型
        allowed_extensions = [
            '.pdf', '.doc', '.docx', '.txt', '.md', '.csv',
            '.ppt', '.pptx', '.xls', '.xlsx',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp'
        ]
        
        import os
        ext = os.path.splitext(value.name)[1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"不支持的文件类型。支持的格式：{', '.join(allowed_extensions)}"
            )
        
        return value
    
    def create(self, validated_data):
        import os
        
        # 自动设置上传者
        validated_data['uploaded_by'] = self.context['request'].user
        
        # 自动提取文件信息
        file = validated_data.get('file')
        if file:
            # 设置原始文件名
            validated_data['original_filename'] = file.name
            
            # 设置文件大小
            validated_data['file_size'] = file.size
            
            # 根据扩展名设置文件类型
            ext = os.path.splitext(file.name)[1].lower()
            type_mapping = {
                '.pdf': 'pdf',
                '.doc': 'doc',
                '.docx': 'docx',
                '.txt': 'txt',
                '.md': 'md',
                '.csv': 'csv',
                '.ppt': 'ppt',
                '.pptx': 'pptx',
                '.xls': 'xls',
                '.xlsx': 'xlsx',
                '.jpg': 'image',
                '.jpeg': 'image',
                '.png': 'image',
                '.gif': 'image',
                '.bmp': 'image',
            }
            validated_data['file_type'] = type_mapping.get(ext, 'other')
            
            # 如果没有提供标题，使用文件名（不含扩展名）
            if not validated_data.get('title'):
                validated_data['title'] = os.path.splitext(file.name)[0]
        
        return super().create(validated_data)


class DocumentListSerializer(serializers.ModelSerializer):
    """文档列表序列化器"""
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)
    file_size_human = serializers.ReadOnlyField()
    file_type_icon = serializers.CharField(source='get_file_type_display_icon', read_only=True)
    tags_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'description', 'file', 'file_type', 
            'file_size', 'file_size_human', 'file_type_icon',
            'original_filename', 'category', 'category_name', 'category_color',
            'tags', 'tags_list', 'uploaded_by', 'uploaded_by_name',
            'is_public', 'created_at', 'updated_at'
        ]
    
    def get_tags_list(self, obj):
        """将标签字符串转换为列表"""
        if obj.tags:
            return [tag.strip() for tag in obj.tags.split(',') if tag.strip()]
        return []


class DocumentDetailSerializer(DocumentListSerializer):
    """文档详情序列化器"""
    access_count = serializers.SerializerMethodField()
    
    class Meta(DocumentListSerializer.Meta):
        fields = DocumentListSerializer.Meta.fields + ['access_count']
    
    def get_access_count(self, obj):
        """获取文档访问次数"""
        return obj.access_logs.count()


class DocumentUpdateSerializer(serializers.ModelSerializer):
    """文档更新序列化器"""
    
    class Meta:
        model = Document
        fields = ['title', 'description', 'category', 'tags', 'is_public']
    
    def validate(self, attrs):
        # 只允许文档的上传者或管理员更新
        request = self.context['request']
        if self.instance.uploaded_by != request.user and not request.user.is_staff:
            raise serializers.ValidationError("您没有权限修改此文档")
        return attrs


class DocumentAccessSerializer(serializers.ModelSerializer):
    """文档访问记录序列化器"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DocumentAccess
        fields = ['id', 'user', 'user_name', 'access_time', 'action']
        read_only_fields = ['user', 'access_time']


class DocumentFolderSerializer(serializers.ModelSerializer):
    """文档文件夹序列化器"""
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    document_count = serializers.ReadOnlyField()
    total_document_count = serializers.ReadOnlyField()
    full_path = serializers.CharField(source='get_full_path', read_only=True)
    subfolders = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentFolder
        fields = [
            'id', 'name', 'description', 'category', 'category_name',
            'parent', 'parent_name', 'full_path',
            'document_count', 'total_document_count',
            'created_by', 'created_by_name',
            'created_at', 'updated_at', 'subfolders'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']
    
    def get_subfolders(self, obj):
        """获取子文件夹列表（仅一级）"""
        subfolders = obj.subfolders.all()
        return [{
            'id': folder.id,
            'name': folder.name,
            'document_count': folder.document_count
        } for folder in subfolders]