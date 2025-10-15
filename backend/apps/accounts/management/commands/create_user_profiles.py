"""
创建用户 Profile 的管理命令
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = '为所有没有 Profile 的用户创建 UserProfile'

    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        created_count = 0
        
        for user in users_without_profile:
            UserProfile.objects.create(user=user)
            created_count += 1
            self.stdout.write(
                self.style.SUCCESS(f'为用户 {user.username} 创建了 Profile')
            )
        
        if created_count == 0:
            self.stdout.write(
                self.style.SUCCESS('所有用户都已有 Profile，无需创建')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'成功为 {created_count} 个用户创建了 Profile')
            )