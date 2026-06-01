#!/bin/bash

# OCR API 后台运行脚本

echo "🚀 启动 OCR API 后台服务"
echo "=========================="

# 激活conda环境
# source ~/miniconda3/etc/profile.d/conda.sh
# conda activate pdf-ocr

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 创建日志目录
mkdir -p logs

# 获取当前时间戳
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "📝 日志文件: logs/api_server_${TIMESTAMP}.log"
echo "📝 PID文件: logs/api_server.pid"

# 使用nohup后台运行，重定向输出到日志文件
nohup python3 api_server.py > logs/api_server_${TIMESTAMP}.log 2>&1 &

# 保存进程ID
echo $! > logs/api_server.pid

echo "✅ API服务器已在后台启动"
echo "   PID: $(cat logs/api_server.pid)"
echo "   日志: logs/api_server_${TIMESTAMP}.log"
echo "   API地址: http://localhost:6001"
echo ""
echo "📋 管理命令:"
echo "   查看日志: tail -f logs/api_server_${TIMESTAMP}.log"
echo "   查看进程: ps aux | grep api_server.py"
echo "   停止服务: kill \$(cat logs/api_server.pid)"
echo "   或运行: ./stop_api_server.sh"
