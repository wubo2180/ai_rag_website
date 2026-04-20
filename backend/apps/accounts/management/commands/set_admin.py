"""
设置用户为管理员的管理命令
用法：python manage.py set_admin <username>
     python manage.py set_admin <username> --remove  # 撤销管理员
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from apps.accounts.models import UserProfile


class Command(BaseCommand):
    help = '设置或撤销用户的管理员权限'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='目标用户名')
        parser.add_argument(
            '--remove',
            action='store_true',
            help='撤销管理员权限，恢复为普通员工',
        )

    def handle(self, *args, **options):
        username = options['username']
        remove = options['remove']

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'用户 "{username}" 不存在')

        profile, _ = UserProfile.objects.get_or_create(user=user)

        if remove:
            profile.role = UserProfile.RoleChoices.EMPLOYEE
            profile.save()
            user.is_staff = False
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'已撤销用户 "{username}" 的管理员权限，当前角色：普通员工'
            ))
        else:
            profile.role = UserProfile.RoleChoices.ADMIN
            profile.save()
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'已将用户 "{username}" 设置为管理员（role=ADMIN, is_staff=True）'
            ))
