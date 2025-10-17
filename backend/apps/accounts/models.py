from django.db import models
from django.contrib.auth.models import AbstractUser

from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    bio = models.TextField(max_length=500, blank=True, verbose_name='个人简介')
    # avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    # AI 模型偏好设置 - AI_UI_928_2 整合
    preferred_ai_model = models.CharField(
        max_length=50, 
        default='deepseek',
        verbose_name='偏好AI模型'
    )
    enable_deep_thinking = models.BooleanField(
        default=True,
        verbose_name='启用深度思考模式'
    )
    
    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'
    
    def __str__(self):
        return f"{self.user.username} - 资料"