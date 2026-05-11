#!/bin/bash
# OCR系统生产环境部署脚本

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 检查必要命令
check_dependencies() {
    log_step "步骤 1/10: 检查系统依赖"
    
    local missing_deps=()
    
    if ! command -v docker &> /dev/null; then
        missing_deps+=("docker")
    fi
    
    if ! command -v docker compose &> /dev/null && ! command -v docker-compose &> /dev/null; then
        missing_deps+=("docker-compose")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_deps+=("git")
    fi
    
    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "缺少以下依赖: ${missing_deps[*]}"
        log_error "请先安装这些依赖，然后重新运行此脚本"
        exit 1
    fi
    
    log_info "✅ 所有必要依赖已安装"
    log_info "   Docker: $(docker --version)"
    log_info "   Docker Compose: $(docker compose version 2>/dev/null || docker-compose --version)"
    log_info "   Git: $(git --version)"
}

# 检查环境变量配置
check_env_config() {
    log_step "步骤 2/10: 检查环境变量配置"
    
    if [ ! -f "backend/.env" ]; then
        log_warn "后端 .env 文件不存在"
        log_info "从模板创建 .env 文件..."
        cp backend/env_example.txt backend/.env
        log_warn "⚠️  请编辑 backend/.env 文件，修改生产环境配置"
        log_warn "   特别注意修改以下配置："
        log_warn "   - SECRET_KEY"
        log_warn "   - JWT_SECRET_KEY"
        log_warn "   - MYSQL_PASSWORD"
        log_warn "   - MINIO_ACCESS_KEY"
        log_warn "   - MINIO_SECRET_KEY"
        read -p "配置完成后，按回车继续..."
    else
        log_info "✅ 后端 .env 文件已存在"
    fi
    
    # 检查是否使用了默认密钥（不安全）
    if grep -q "your-secret-key-change-this-in-production" backend/.env; then
        log_error "❌ 检测到使用了默认的 SECRET_KEY，这在生产环境是不安全的！"
        log_error "   请修改 backend/.env 中的 SECRET_KEY 和 JWT_SECRET_KEY"
        exit 1
    fi
    
    log_info "✅ 环境变量配置检查通过"
}

# 检查 docker-compose.yml 配置
check_compose_config() {
    log_step "步骤 3/10: 检查 Docker Compose 配置"
    
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml 文件不存在"
        exit 1
    fi
    
    # 验证配置文件语法
    if docker compose config > /dev/null 2>&1; then
        log_info "✅ Docker Compose 配置文件语法正确"
    else
        log_error "❌ Docker Compose 配置文件语法错误"
        docker compose config
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    log_step "步骤 4/10: 创建必要的目录"
    
    mkdir -p deployment/nginx
    mkdir -p deployment/mysql
    mkdir -p deployment/logs
    mkdir -p deployment/backups
    mkdir -p backend/logs
    
    log_info "✅ 目录结构创建完成"
}

# 停止旧服务
stop_old_services() {
    log_step "步骤 5/10: 停止旧服务"
    
    if docker compose ps | grep -q "Up"; then
        log_info "检测到运行中的服务，正在停止..."
        docker compose down
        log_info "✅ 旧服务已停止"
    else
        log_info "没有运行中的服务"
    fi
}

# 构建 Docker 镜像
build_images() {
    log_step "步骤 6/10: 构建 Docker 镜像"
    
    log_info "开始构建后端镜像..."
    docker compose build backend
    
    log_info "开始构建前端镜像..."
    docker compose build frontend
    
    log_info "✅ Docker 镜像构建完成"
}

# 启动服务
start_services() {
    log_step "步骤 7/10: 启动服务"
    
    log_info "启动基础服务（MySQL, Redis, MinIO）..."
    docker compose up -d mysql redis minio
    
    log_info "等待基础服务就绪（30秒）..."
    sleep 30
    
    log_info "启动应用服务（Backend, Frontend）..."
    docker compose up -d backend frontend
    
    log_info "等待应用服务就绪（20秒）..."
    sleep 20
    
    log_info "✅ 所有服务已启动"
    docker compose ps
}

# 初始化数据库
init_database() {
    log_step "步骤 8/10: 初始化数据库"
    
    log_info "检查数据库连接..."
    
    # 等待数据库完全就绪
    local retry=0
    local max_retries=30
    while ! docker compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} -e "SELECT 1" > /dev/null 2>&1; do
        retry=$((retry + 1))
        if [ $retry -ge $max_retries ]; then
            log_error "数据库连接超时"
            exit 1
        fi
        log_info "等待数据库就绪... ($retry/$max_retries)"
        sleep 2
    done
    
    log_info "✅ 数据库连接成功"
    
    # 运行数据库迁移
    log_info "运行数据库迁移..."
    if docker compose exec backend flask db upgrade; then
        log_info "✅ 数据库迁移完成"
    else
        log_warn "数据库迁移失败，可能是首次部署"
        log_info "尝试初始化迁移..."
        docker compose exec backend flask db init || true
        docker compose exec backend flask db migrate -m "Initial migration" || true
        docker compose exec backend flask db upgrade || true
    fi
}

# 初始化 MinIO
init_minio() {
    log_step "步骤 9/10: 初始化 MinIO"
    
    log_info "配置 MinIO 客户端..."
    docker compose exec minio mc alias set local http://localhost:9000 ${MINIO_ACCESS_KEY:-minioadmin} ${MINIO_SECRET_KEY:-minioadmin123} || true
    
    log_info "创建存储桶..."
    docker compose exec minio mc mb local/ocr-files || log_warn "存储桶可能已存在"
    
    log_info "设置存储桶权限..."
    docker compose exec minio mc anonymous set none local/ocr-files
    
    log_info "✅ MinIO 初始化完成"
}

# 健康检查
health_check() {
    log_step "步骤 10/10: 健康检查"
    
    log_info "检查服务健康状态..."
    
    # 检查容器状态
    local unhealthy_containers=$(docker compose ps | grep -v "Up" | grep -v "NAME" | wc -l)
    if [ $unhealthy_containers -gt 0 ]; then
        log_error "有容器未正常运行:"
        docker compose ps
        exit 1
    fi
    
    log_info "✅ 所有容器运行正常"
    
    # 检查后端 API
    log_info "检查后端 API..."
    local retry=0
    local max_retries=30
    while ! curl -f http://localhost:5000/api/health > /dev/null 2>&1; do
        retry=$((retry + 1))
        if [ $retry -ge $max_retries ]; then
            log_error "后端 API 健康检查失败"
            docker compose logs backend
            exit 1
        fi
        log_info "等待后端 API 就绪... ($retry/$max_retries)"
        sleep 2
    done
    
    log_info "✅ 后端 API 运行正常"
    
    # 检查前端
    log_info "检查前端服务..."
    if curl -f http://localhost:80 > /dev/null 2>&1; then
        log_info "✅ 前端服务运行正常"
    else
        log_warn "⚠️  前端服务可能未完全就绪"
    fi
}

# 显示部署信息
show_deployment_info() {
    echo ""
    log_step "🎉 部署完成！"
    
    echo -e "${GREEN}服务访问地址：${NC}"
    echo -e "  前端界面:    http://$(hostname -I | awk '{print $1}'):80"
    echo -e "  后端API:     http://$(hostname -I | awk '{print $1}'):5000/api"
    echo -e "  MinIO控制台: http://$(hostname -I | awk '{print $1}'):9001"
    echo ""
    
    echo -e "${YELLOW}默认管理员账户（请登录后立即修改密码）：${NC}"
    echo -e "  用户名: admin"
    echo -e "  密码:   Admin@2025"
    echo ""
    
    echo -e "${YELLOW}重要提醒：${NC}"
    echo -e "  1. 请尽快登录系统修改管理员密码"
    echo -e "  2. 请确认外部 OCR 服务地址配置正确"
    echo -e "  3. 建议配置自动备份（见文档）"
    echo -e "  4. 生产环境建议配置 HTTPS（见文档）"
    echo ""
    
    echo -e "${GREEN}常用管理命令：${NC}"
    echo -e "  查看服务状态:   docker compose ps"
    echo -e "  查看日志:       docker compose logs -f"
    echo -e "  重启服务:       docker compose restart"
    echo -e "  停止服务:       docker compose down"
    echo ""
}

# 主流程
main() {
    echo -e "${BLUE}"
    echo "================================================"
    echo "   OCR 数据识别系统 - 生产环境部署脚本"
    echo "================================================"
    echo -e "${NC}"
    
    # 检查是否在项目根目录
    if [ ! -f "docker-compose.yml" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 执行部署步骤
    check_dependencies
    check_env_config
    check_compose_config
    create_directories
    stop_old_services
    build_images
    start_services
    init_database
    init_minio
    health_check
    show_deployment_info
    
    log_info "🎊 部署流程全部完成！"
}

# 运行主流程
main

