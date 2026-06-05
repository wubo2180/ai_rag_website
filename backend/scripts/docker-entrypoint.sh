#!/bin/bash
set -e

echo "等待数据库启动..."

DATABASE_TYPE_VALUE="$(echo "${DATABASE_TYPE:-}" | tr '[:upper:]' '[:lower:]' | xargs)"

if [ "$DATABASE_TYPE_VALUE" = "mysql" ] || [ -n "${MYSQL_HOST}" ] || [ -n "${MYSQL_DATABASE}" ] || [ -n "${MYSQL_USER}" ]; then
  DB_HOST_VALUE="${MYSQL_HOST:-${DB_HOST:-localhost}}"
  DB_PORT_VALUE="${MYSQL_PORT:-${DB_PORT:-3306}}"
  DB_USER_VALUE="${MYSQL_USER:-${DB_USER:-root}}"
  DB_PASSWORD_VALUE="${MYSQL_PASSWORD:-${DB_PASSWORD:-}}"

  if ! command -v mysqladmin >/dev/null 2>&1; then
    >&2 echo "未找到 mysqladmin 命令，请确认镜像已安装 default-mysql-client"
    exit 1
  fi

  until MYSQL_PWD="$DB_PASSWORD_VALUE" mysqladmin ping -h "$DB_HOST_VALUE" -P "$DB_PORT_VALUE" -u "$DB_USER_VALUE" --silent; do
    >&2 echo "MySQL 未就绪 - 等待中..."
    sleep 1
  done

  >&2 echo "MySQL 已就绪 - 执行迁移"
else
  DB_HOST_VALUE="${DB_HOST:-localhost}"
  DB_USER_VALUE="${DB_USER:-postgres}"
  DB_NAME_VALUE="${DB_NAME:-postgres}"
  DB_PASSWORD_VALUE="${DB_PASSWORD:-}"

  if ! command -v psql >/dev/null 2>&1; then
    >&2 echo "当前进入 PostgreSQL 分支，但容器中没有 psql。"
    >&2 echo "请检查 backend/.env 是否使用无空格格式：DATABASE_TYPE=mysql, MYSQL_HOST=..."
    exit 1
  fi

  until PGPASSWORD="$DB_PASSWORD_VALUE" psql -h "$DB_HOST_VALUE" -U "$DB_USER_VALUE" -d "$DB_NAME_VALUE" -c '\q'; do
    >&2 echo "PostgreSQL 未就绪 - 等待中..."
    sleep 1
  done

  >&2 echo "PostgreSQL 已就绪 - 执行迁移"
fi

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
