#!/bin/bash

# OCR API 停止服务脚本

echo "🛑 停止 OCR API 服务"
echo "==================="

PID_FILE="logs/api_server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "📋 停止进程 PID: $PID"
        kill "$PID"
        
        # 等待进程停止
        sleep 2
        
        # 检查是否停止成功
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚠️  进程未正常停止，强制终止..."
            kill -9 "$PID"
        fi
        
        echo "✅ API服务器已停止"
    else
        echo "⚠️  进程 $PID 不存在（可能已经停止）"
    fi
    
    # 删除PID文件
    rm -f "$PID_FILE"
else
    echo "⚠️  PID文件不存在: $PID_FILE"
    
    # 尝试通过进程名查找并停止
    API_PIDS=$(pgrep -f "python3 api_server.py")
    if [ ! -z "$API_PIDS" ]; then
        echo "🔍 发现API服务器进程: $API_PIDS"
        echo "📋 停止所有API服务器进程..."
        pkill -f "python3 api_server.py"
        echo "✅ 已停止所有API服务器进程"
    else
        echo "ℹ️  未发现运行中的API服务器进程"
    fi
fi

echo ""
echo "📊 当前API相关进程:"
ps aux | grep -E "(api_server|uvicorn)" | grep -v grep || echo "   无相关进程运行"
