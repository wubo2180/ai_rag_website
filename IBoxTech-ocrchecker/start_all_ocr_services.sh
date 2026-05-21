#!/bin/bash
# OCR统一识别服务 - 启动所有服务

echo "🚀 启动OCR统一识别服务..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  端口 $port 已被占用 ($service 可能已在运行)${NC}"
        return 1
    else
        return 0
    fi
}

# 启动服务函数
start_service() {
    local service_name=$1
    local service_dir=$2
    local port=$3
    local start_cmd=$4
    
    echo -e "${YELLOW}启动 $service_name (端口: $port)...${NC}"
    
    # 检查目录是否存在
    if [ ! -d "$service_dir" ]; then
        echo -e "${RED}❌ 目录不存在: $service_dir${NC}"
        return 1
    fi
    
    cd "$service_dir"
    
    # 启动服务
    eval "$start_cmd" > /dev/null 2>&1 &
    local pid=$!
    
    # 等待服务启动
    echo "   等待服务启动..."
    sleep 3
    
    # 检查服务是否启动成功
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name 启动成功 (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name 启动失败${NC}"
        return 1
    fi
}

# 1. 启动委托单OCR服务
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  启动委托单OCR服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if check_port 6001 "委托单OCR"; then
    start_service \
        "委托单OCR" \
        "/home/xjlab/zhy/all-anbos/ai_rag_website/IBoxTech-ocr-commission" \
        6001 \
        "nohup ./venv/bin/python api_server.py > /tmp/ocr_commission.log 2>&1"
else
    echo -e "${GREEN}✅ 委托单OCR服务已在运行${NC}"
fi

echo ""

# 2. 启动论文OCR服务
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  启动论文OCR服务"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if check_port 6002 "论文OCR"; then
    start_service \
        "论文OCR" \
        "/home/xjlab/zhy/all-anbos/ai_rag_website/IBoxTech-ocr-paper" \
        6002 \
        "nohup ./venv/bin/python api_server.py > /tmp/ocr_paper.log 2>&1"
else
    echo -e "${GREEN}✅ 论文OCR服务已在运行${NC}"
fi

echo ""

# 3. 启动主系统
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  启动IBoxTech-ocrchecker主系统"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if check_port 5001 "主系统"; then
    start_service \
        "主系统" \
        "/home/xjlab/zhy/all-anbos/ai_rag_website/IBoxTech-ocrchecker/backend" \
        5001 \
        "nohup ./venv/bin/python app.py > /tmp/ocrchecker.log 2>&1"
else
    echo -e "${GREEN}✅ 主系统已在运行${NC}"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 所有服务启动完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 服务状态:"
echo "   - 委托单OCR: http://localhost:6001/health"
echo "   - 论文OCR:   http://localhost:6002/health"
echo "   - 主系统:     http://localhost:5001/health"
echo ""
echo "📝 日志文件:"
echo "   - 委托单OCR: /tmp/ocr_commission.log"
echo "   - 论文OCR:   /tmp/ocr_paper.log"
echo "   - 主系统:     /tmp/ocrchecker.log"
echo ""
echo "💡 查看实时日志:"
echo "   tail -f /tmp/ocr_commission.log"
echo "   tail -f /tmp/ocr_paper.log"
echo "   tail -f /tmp/ocrchecker.log"
echo ""

