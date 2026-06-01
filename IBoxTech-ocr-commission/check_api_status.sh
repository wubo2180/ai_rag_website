#!/bin/bash

# OCR API 服务状态检查脚本

echo "📊 OCR API 服务状态"
echo "==================="

PID_FILE="logs/api_server.pid"

# 检查PID文件
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "📋 PID文件存在: $PID"
    
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ 服务正在运行 (PID: $PID)"
        
        # 检查端口占用
        if lsof -i :6001 > /dev/null 2>&1; then
            echo "✅ 端口6001已监听"
        else
            echo "⚠️  端口6001未监听"
        fi
        
        # 测试API响应
        echo "🔍 测试API响应..."
        if curl -s http://localhost:6001/health > /dev/null; then
            echo "✅ API响应正常"
        else
            echo "❌ API无响应"
        fi
        
    else
        echo "❌ PID文件存在但进程不运行"
        rm -f "$PID_FILE"
    fi
else
    echo "⚠️  PID文件不存在"
fi

echo ""
echo "📊 进程信息:"
ps aux | grep -E "(api_server|uvicorn)" | grep -v grep || echo "   无相关进程"

echo ""
echo "🌐 网络监听:"
netstat -tlnp | grep :6001 || echo "   端口6001未监听"

echo ""
echo "📝 最新日志 (最后10行):"
LATEST_LOG=$(ls -t logs/api_server_*.log 2>/dev/null | head -1)
if [ ! -z "$LATEST_LOG" ]; then
    echo "   文件: $LATEST_LOG"
    tail -10 "$LATEST_LOG"
else
    echo "   无日志文件"
fi
