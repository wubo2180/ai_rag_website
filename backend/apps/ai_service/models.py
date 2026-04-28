from django.db import models


class KnowledgeExtractionHistory(models.Model):
    """知识抽取历史记录"""

    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
    ]

    user_id = models.CharField(max_length=128, default='anonymous', db_index=True, verbose_name='用户标识')
    file_name = models.CharField(max_length=255, verbose_name='文件名')
    file_type = models.CharField(max_length=20, blank=True, default='', verbose_name='文件类型')
    file_size = models.BigIntegerField(default=0, verbose_name='文件大小(字节)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success', verbose_name='抽取状态')
    item_count = models.IntegerField(default=0, verbose_name='抽取条目数')
    elapsed_time = models.FloatField(null=True, blank=True, verbose_name='耗时(秒)')
    error_message = models.TextField(blank=True, default='', verbose_name='错误信息')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '知识抽取历史'
        verbose_name_plural = '知识抽取历史'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user_id} - {self.file_name} ({self.status})"
