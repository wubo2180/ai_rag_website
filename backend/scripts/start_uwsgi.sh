#!/bin/bash
# uWSGI启动脚本

echo "🚀 启动uWSGI服务..."

# 设置环境变量
export DJANGO_SETTINGS_MODULE=config.settings
export PYTHONPATH="/www/wwwroot/ai_rag_website/backend:$PYTHONPATH"

# 切换到项目目录
cd /www/wwwroot/ai_rag_website/backend

# 测试Django设置
echo "📋 测试Django设置..."
python test_django_setup.py

if [ $? -ne 0 ]; then
    echo "❌ Django设置测试失败，请检查配置"
    exit 1
fi

# 创建必要的目录
mkdir -p logs
mkdir -p staticfiles
mkdir -p media

# 收集静态文件
echo "📦 收集静态文件..."
python manage.py collectstatic --noinput

# 应用数据库迁移
echo "🗄️ 应用数据库迁移..."
python manage.py migrate

# 启动uWSGI
echo "🔥 启动uWSGI服务器..."
uwsgi --ini uwsgi.ini