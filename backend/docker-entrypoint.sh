#!/bin/bash
set -e

echo "等待数据库启动..."
until PGPASSWORD=$DB_PASSWORD psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -c '\q'; do
  >&2 echo "PostgreSQL 未就绪 - 等待中..."
  sleep 1
done

>&2 echo "PostgreSQL 已就绪 - 执行迁移"

# 运行数据库迁移
python manage.py migrate --noinput

# 创建超级用户（如果不存在）
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('超级用户已创建: admin / admin123')
else:
    print('超级用户已存在')
END

# 收集静态文件
python manage.py collectstatic --noinput

echo "启动应用..."
exec "$@"
