#!/bin/bash

################################################################################
# 生产环境部署脚本
# 用途: 一键部署或更新应用到生产环境
# 使用: ./deploy_production.sh
################################################################################

set -e

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查是否在生产环境
check_production() {
    if [ ! -f ".env" ]; then
        log_error ".env 文件不存在"
        exit 1
    fi
    
    DEBUG_VALUE=$(grep "^DEBUG=" .env | cut -d= -f2)
    if [ "$DEBUG_VALUE" != "False" ]; then
        log_error "DEBUG 必须设置为 False"
        exit 1
    fi
    
    SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d= -f2)
    if [[ "$SECRET_KEY" == *"your-secret-key"* ]] || [[ "$SECRET_KEY" == *"insecure"* ]]; then
        log_error "必须修改 SECRET_KEY"
        exit 1
    fi
}

cd "$PROJECT_DIR"

echo "================================"
echo "  生产环境部署脚本"
echo "================================"
echo

# 步骤 1: 检查环境
log_step "1. 检查生产环境配置"
check_production
log_info "环境配置检查通过"
echo

# 步骤 2: 备份数据库
log_step "2. 备份当前数据库"
if docker compose ps | grep -q "django_rag_db.*Up"; then
    log_info "正在备份数据库..."
    bash scripts/backup.sh
else
    log_warn "数据库容器未运行，跳过备份"
fi
echo

# 步骤 3: 拉取最新代码
log_step "3. 拉取最新代码"
if [ -d ".git" ]; then
    log_info "从 Git 仓库拉取最新代码..."
    git pull
    log_info "代码更新完成"
else
    log_warn "不是 Git 仓库，跳过拉取代码"
fi
echo

# 步骤 4: 构建镜像
log_step "4. 构建 Docker 镜像"
log_info "正在构建镜像（这可能需要几分钟）..."
docker compose build --no-cache
log_info "镜像构建完成"
echo

# 步骤 5: 停止旧容器
log_step "5. 停止旧容器"
if docker compose ps -q | grep -q .; then
    log_info "停止运行中的容器..."
    docker compose down
    log_info "容器已停止"
else
    log_info "没有运行中的容器"
fi
echo

# 步骤 6: 启动新容器
log_step "6. 启动新容器"
log_info "启动服务..."
docker compose up -d
log_info "容器已启动"
echo

# 步骤 7: 等待服务就绪
log_step "7. 等待服务就绪"
log_info "等待数据库启动..."
sleep 10

MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker compose exec -T db pg_isready -U postgres &> /dev/null; then
        log_info "数据库已就绪"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 2
done
echo

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    log_error "数据库启动超时"
    exit 1
fi

log_info "等待 Web 服务启动..."
sleep 5
echo

# 步骤 8: 执行数据库迁移
log_step "8. 执行数据库迁移"
log_info "运行迁移..."
docker compose exec -T web python manage.py migrate --noinput
log_info "迁移完成"
echo

# 步骤 9: 收集静态文件
log_step "9. 收集静态文件"
log_info "收集静态文件..."
docker compose exec -T web python manage.py collectstatic --noinput
log_info "静态文件收集完成"
echo

# 步骤 10: 检查服务状态
log_step "10. 检查服务状态"
docker compose ps
echo

# 步骤 11: 健康检查
log_step "11. 健康检查"
log_info "检查容器健康状态..."

# 检查数据库
if docker compose exec -T db pg_isready -U postgres &> /dev/null; then
    log_info "✓ 数据库: 正常"
else
    log_error "✗ 数据库: 异常"
fi

# 检查 Web 服务
if curl -f -s -o /dev/null http://localhost:8000/admin/login/; then
    log_info "✓ Web服务: 正常"
else
    log_warn "✗ Web服务: 可能异常（检查日志）"
fi

# 检查 Nginx
if docker compose ps | grep -q "django_rag_nginx.*Up"; then
    log_info "✓ Nginx: 运行中"
else
    log_error "✗ Nginx: 未运行"
fi
echo

# 步骤 12: 查看日志
log_step "12. 最近的应用日志"
echo "--- Web 服务日志 (最近 20 行) ---"
docker compose logs --tail=20 web
echo
echo "--- Nginx 日志 (最近 10 行) ---"
docker compose logs --tail=10 nginx
echo

# 步骤 13: 清理旧镜像
log_step "13. 清理未使用的 Docker 资源"
log_info "清理悬空镜像..."
docker image prune -f
log_info "清理完成"
echo

echo "================================"
echo "  部署完成！"
echo "================================"
echo
log_info "部署摘要:"
echo "  - 数据库: 已备份并迁移"
echo "  - 代码: 已更新"
echo "  - 容器: 已重启"
echo "  - 静态文件: 已收集"
echo
log_info "后续步骤:"
echo "  1. 访问网站检查功能"
echo "  2. 查看日志: docker compose logs -f"
echo "  3. 监控服务: bash scripts/monitor.sh"
echo
log_warn "重要提示:"
echo "  - 请持续监控服务状态 24-48 小时"
echo "  - 数据库备份已保存在 ~/backups/"
echo "  - 如遇问题可使用 scripts/restore.sh 恢复"
echo
