from django.db import models
from django.contrib.auth.models import User


class Department(models.Model):
    """部门模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name='部门名称')
    description = models.TextField(blank=True, verbose_name='部门描述')
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        verbose_name='上级部门'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '部门'
        verbose_name_plural = '部门'
        ordering = ('name',)

    def __str__(self):
        return self.name


class UserProfile(models.Model):
    class RoleChoices(models.TextChoices):
        ADMIN = 'ADMIN', '管理员'
        EMPLOYEE = 'EMPLOYEE', '普通员工'
        SUPERVISOR = 'SUPERVISOR', '部门主管'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_url = models.URLField(blank=True, default='', verbose_name='头像URL')
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    bio = models.TextField(max_length=500, blank=True, verbose_name='个人简介')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    preferred_ai_model = models.CharField(
        max_length=50,
        default='deepseek',
        verbose_name='偏好AI模型'
    )
    enable_deep_thinking = models.BooleanField(
        default=True,
        verbose_name='启用深度思考模式'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name='所属部门'
    )
    role = models.CharField(
        max_length=20,
        choices=RoleChoices.choices,
        default=RoleChoices.EMPLOYEE,
        verbose_name='角色'
    )

    class Meta:
        verbose_name = '用户资料'
        verbose_name_plural = '用户资料'

    def __str__(self):
        return f"{self.user.username} - 资料"

    @property
    def is_admin(self):
        return self.role == self.RoleChoices.ADMIN or self.user.is_staff