#!/bin/bash

# 启动前端服务脚本

set -e

echo "🚀 启动OCR系统前端服务..."

# 切换到前端目录
cd frontend

# 检查node_modules
if [ ! -d "node_modules" ]; then
    echo "❌ 前端依赖未安装，请先运行安装脚本: ./scripts/setup.sh"
    echo "   或手动安装: cd frontend && npm install"
    exit 1
fi

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  前端环境配置文件不存在，使用默认配置"
    echo "VITE_API_BASE_URL=http://localhost:5000/api" > .env
fi

echo "🌐 启动Vite开发服务器..."
echo "   访问地址: http://localhost:5173"
echo "   按 Ctrl+C 停止服务"
echo ""

# 启动开发服务器
npm run dev
