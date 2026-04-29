#!/bin/bash

# 启动后端服务脚本

set -e

echo "🚀 启动OCR系统后端服务..."

# 切换到后端目录
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行安装脚本: ./scripts/setup.sh"
    exit 1
fi

# 激活虚拟环境
echo "🔧 激活Python虚拟环境..."
source venv/bin/activate

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "❌ 环境配置文件不存在，请先创建 .env 文件"
    echo "   可以复制 env_example.txt 并修改相应配置"
    exit 1
fi

# 检查数据库连接
echo "🔍 检查服务依赖..."

# 检查MySQL
if ! mysqladmin ping -h"${MYSQL_HOST:-localhost}" -P"${MYSQL_PORT:-3306}" -u"${MYSQL_USER:-root}" -p"${MYSQL_PASSWORD:-}" --silent; then
    echo "⚠️  无法连接到MySQL，请检查MySQL服务是否启动"
fi

# 检查Redis
if ! redis-cli ping > /dev/null 2>&1; then
    echo "⚠️  无法连接到Redis，请检查Redis服务是否启动"
fi

# 设置Python路径
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "🌐 启动Flask服务器..."
echo "   访问地址: http://localhost:5000"
echo "   API文档: http://localhost:5000/api"
echo "   按 Ctrl+C 停止服务"
echo ""

# 启动应用
python app.py
