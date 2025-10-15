from django.db import models
from django.contrib.auth.models import User
import os


class DocumentCategory(models.Model):
    """文献分类模型"""
    name = models.CharField(max_length=100, verbose_name='分类名称')
    description = models.TextField(blank=True, verbose_name='分类描述')
    color = models.CharField(max_length=7, default='#1890ff', verbose_name='分类颜色')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='创建者')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '文献分类'
        verbose_name_plural = '文献分类'
        ordering = ['name']

    def __str__(self):
        return self.name


class Document(models.Model):
    """文献资料模型"""
    FILE_TYPES = [
        ('pdf', 'PDF文档'),
        ('doc', 'Word文档'),
        ('docx', 'Word文档'),
        ('txt', '文本文件'),
        ('md', 'Markdown文档'),
        ('ppt', 'PowerPoint'),
        ('pptx', 'PowerPoint'),
        ('xls', 'Excel表格'),
        ('xlsx', 'Excel表格'),
        ('image', '图片文件'),
        ('other', '其他文件'),
    ]

    title = models.CharField(max_length=255, verbose_name='文档标题')
    description = models.TextField(blank=True, verbose_name='文档描述')
    file = models.FileField(upload_to='documents/%Y/%m/', verbose_name='文件')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES, verbose_name='文件类型')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    original_filename = models.CharField(max_length=255, verbose_name='原始文件名')
    
    category = models.ForeignKey(
        DocumentCategory, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='documents',
        verbose_name='所属分类'
    )
    
    tags = models.CharField(max_length=500, blank=True, verbose_name='标签（逗号分隔）')
    
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents', verbose_name='上传者')
    is_public = models.BooleanField(default=False, verbose_name='是否公开')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '文档资料'
        verbose_name_plural = '文档资料'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def file_size_human(self):
        """返回人类可读的文件大小"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    @property
    def file_extension(self):
        """获取文件扩展名"""
        return os.path.splitext(self.original_filename)[1].lower()

    def get_file_type_display_icon(self):
        """获取文件类型对应的图标"""
        icons = {
            'pdf': '📄',
            'doc': '📝',
            'docx': '📝',
            'txt': '📋',
            'md': '📝',
            'ppt': '📊',
            'pptx': '📊',
            'xls': '📈',
            'xlsx': '📈',
            'image': '🖼️',
            'other': '📁',
        }
        return icons.get(self.file_type, '📁')

    def save(self, *args, **kwargs):
        """保存时自动设置文件信息"""
        if self.file:
            # 设置原始文件名
            if not self.original_filename:
                self.original_filename = self.file.name
            
            # 设置文件大小
            if not self.file_size:
                self.file_size = self.file.size
            
            # 根据文件扩展名设置文件类型
            if not self.file_type:
                ext = self.file_extension.lower()
                type_mapping = {
                    '.pdf': 'pdf',
                    '.doc': 'doc',
                    '.docx': 'docx',
                    '.txt': 'txt',
                    '.md': 'md',
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
                self.file_type = type_mapping.get(ext, 'other')
            
            # 如果没有标题，使用文件名
            if not self.title:
                self.title = os.path.splitext(self.original_filename)[0]

        super().save(*args, **kwargs)


class DocumentAccess(models.Model):
    """文档访问记录"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='access_logs')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_accesses')
    access_time = models.DateTimeField(auto_now_add=True, verbose_name='访问时间')
    action = models.CharField(
        max_length=20,
        choices=[
            ('view', '查看'),
            ('download', '下载'),
        ],
        default='view',
        verbose_name='操作类型'
    )

    class Meta:
        verbose_name = '文档访问记录'
        verbose_name_plural = '文档访问记录'
        ordering = ['-access_time']
