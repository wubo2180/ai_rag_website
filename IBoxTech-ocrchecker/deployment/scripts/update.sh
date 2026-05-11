#!/bin/bash
# OCR系统更新脚本（零停机更新）

set -e

PROJECT_DIR="/opt/IBoxTech-ocrchecker"

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
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "================================================"
    echo "   OCR 系统更新工具"
    echo "================================================"
    echo -e "${NC}"
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    cd $PROJECT_DIR
    
    # 步骤 1: 备份当前数据
    log_step "步骤 1/8: 备份当前数据"
    if [ -f "deployment/scripts/backup.sh" ]; then
        bash deployment/scripts/backup.sh
        log_info "✅ 数据备份完成"
    else
        log_warn "备份脚本不存在，跳过备份"
    fi
    
    # 步骤 2: 拉取最新代码
    log_step "步骤 2/8: 拉取最新代码"
    log_info "当前分支: $(git branch --show-current)"
    log_info "当前版本: $(git log -1 --oneline)"
    
    read -p "是否从远程仓库拉取最新代码？(yes/no): " pull_code
    if [ "$pull_code" = "yes" ]; then
        git pull origin main
        log_info "✅ 代码更新完成"
        log_info "新版本: $(git log -1 --oneline)"
    else
        log_info "跳过代码拉取"
    fi
    
    # 步骤 3: 检查配置变更
    log_step "步骤 3/8: 检查配置变更"
    if git diff HEAD@{1} backend/.env > /dev/null 2>&1; then
        log_info "环境变量文件无变更"
    else
        log_warn "⚠️  检测到环境变量文件可能有变更，请检查"
    fi
    
    # 步骤 4: 构建新镜像
    log_step "步骤 4/8: 构建新镜像"
    log_info "开始构建后端镜像..."
    docker compose build backend
    
    log_info "开始构建前端镜像..."
    docker compose build frontend
    
    log_info "✅ 镜像构建完成"
    
    # 步骤 5: 滚动更新后端
    log_step "步骤 5/8: 滚动更新后端服务"
    log_info "启动新版本后端（保留旧版本）..."
    docker compose up -d --scale backend=2 --no-recreate
    
    log_info "等待新实例就绪（30秒）..."
    sleep 30
    
    # 健康检查
    if curl -f http://localhost:5000/api/health > /dev/null 2>&1; then
        log_info "✅ 新版本后端运行正常"
        
        log_info "移除旧版本后端..."
        docker compose up -d --scale backend=1 --no-recreate
        
        log_info "✅ 后端服务更新完成"
    else
        log_error "❌ 新版本后端健康检查失败"
        log_error "回滚到旧版本..."
        docker compose up -d --scale backend=1 --no-recreate
        exit 1
    fi
    
    # 步骤 6: 更新前端
    log_step "步骤 6/8: 更新前端服务"
    log_info "重启前端服务..."
    docker compose up -d frontend
    
    log_info "等待前端服务就绪（10秒）..."
    sleep 10
    
    if curl -f http://localhost:80 > /dev/null 2>&1; then
        log_info "✅ 前端服务更新完成"
    else
        log_warn "⚠️  前端服务可能未完全就绪"
    fi
    
    # 步骤 7: 运行数据库迁移
    log_step "步骤 7/8: 运行数据库迁移"
    log_info "检查是否有新的数据库迁移..."
    
    if docker compose exec backend flask db upgrade; then
        log_info "✅ 数据库迁移完成"
    else
        log_warn "⚠️  数据库迁移失败或无新迁移"
    fi
    
    # 步骤 8: 清理旧资源
    log_step "步骤 8/8: 清理旧资源"
    read -p "是否清理未使用的 Docker 镜像？(yes/no): " clean_images
    if [ "$clean_images" = "yes" ]; then
        docker image prune -f
        log_info "✅ 旧镜像已清理"
    else
        log_info "跳过镜像清理"
    fi
    
    # 最终健康检查
    log_step "最终健康检查"
    if bash deployment/scripts/health_check.sh; then
        log_info "✅ 系统更新成功，所有服务运行正常"
    else
        log_error "❌ 系统存在问题，请检查"
        exit 1
    fi
    
    echo ""
    log_info "🎉 更新流程完成！"
    log_info "请访问系统进行功能验证"
}

# 运行主函数
main

