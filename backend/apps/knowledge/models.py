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
        ordering = ['document', 'chunk_index']
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"