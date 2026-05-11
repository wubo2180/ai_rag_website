#!/bin/bash
# OCR统一识别服务 - 停止所有服务

echo "🛑 停止OCR统一识别服务..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 停止服务函数
stop_service_by_port() {
    local port=$1
    local service_name=$2
    
    echo -e "${YELLOW}停止 $service_name (端口: $port)...${NC}"
    
    # 查找占用端口的进程
    local pids=$(lsof -ti:$port)
    
    if [ -z "$pids" ]; then
        echo -e "${YELLOW}⚠️  没有服务运行在端口 $port${NC}"
        return 0
    fi
    
    # 停止所有占用该端口的进程
    for pid in $pids; do
        echo "   杀死进程 PID: $pid"
        kill -15 $pid 2>/dev/null || kill -9 $pid 2>/dev/null
    done
    
    # 等待进程结束
    sleep 2
    
    # 检查是否成功停止
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}❌ 停止失败，强制终止...${NC}"
        for pid in $(lsof -ti:$port); do
            kill -9 $pid 2>/dev/null
        done
    else
        echo -e "${GREEN}✅ $service_name 已停止${NC}"
    fi
    
    echo ""
}

# 1. 停止主系统
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  停止IBoxTech-ocrchecker主系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
stop_service_by_port 5001 "主系统"

# 2. 停止委托单OCR服务
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  停止委托单OCR服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
stop_service_by_port 6001 "委托单OCR"

# 3. 停止论文OCR服务
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  停止论文OCR服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
stop_service_by_port 6002 "论文OCR"

# 清理临时文件
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🗑️  清理临时文件"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "/tmp/ocr_commission.log" ]; then
    rm /tmp/ocr_commission.log
    echo -e "${GREEN}✅ 已删除 /tmp/ocr_commission.log${NC}"
fi

if [ -f "/tmp/ocr_paper.log" ]; then
    rm /tmp/ocr_paper.log
    echo -e "${GREEN}✅ 已删除 /tmp/ocr_paper.log${NC}"
fi

if [ -f "/tmp/ocrchecker.log" ]; then
    rm /tmp/ocrchecker.log
    echo -e "${GREEN}✅ 已删除 /tmp/ocrchecker.log${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 所有服务已停止！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""


