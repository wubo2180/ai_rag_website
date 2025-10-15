#!/bin/bash

# Django RAG 项目快速部署脚本
# 用法: ./deploy.sh [start|stop|restart|rebuild|logs|backup|clean]

set -e

PROJECT_NAME="django-rag"
COMPOSE_FILE="docker-compose.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印函数
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_info "Docker 环境检查通过"
}

# 检查环境变量文件
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env 文件不存在"
        if [ -f .env.example ]; then
            print_info "从 .env.example 复制..."
            cp .env.example .env
            print_warning "请编辑 .env 文件并配置必要的环境变量"
            print_warning "特别注意修改: SECRET_KEY, DB_PASSWORD, ALLOWED_HOSTS"
            read -p "是否现在编辑 .env 文件? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                ${EDITOR:-nano} .env
            fi
        else
            print_error ".env.example 文件也不存在，无法继续"
            exit 1
        fi
    fi
    print_info "环境变量文件检查通过"
}

# 启动服务
start() {
    print_info "启动 $PROJECT_NAME 服务..."
    check_docker
    check_env
    
    docker-compose -f $COMPOSE_FILE up -d
    
    print_info "服务启动成功！"
    print_info "访问地址: http://localhost"
    print_info "管理后台: http://localhost/admin (admin/admin123)"
    print_warning "请立即修改默认密码！"
    
    sleep 2
    docker-compose logs --tail=50
}

# 停止服务
stop() {
    print_info "停止 $PROJECT_NAME 服务..."
    docker-compose -f $COMPOSE_FILE down
    print_info "服务已停止"
}

# 重启服务
restart() {
    print_info "重启 $PROJECT_NAME 服务..."
    docker-compose -f $COMPOSE_FILE restart
    print_info "服务已重启"
}

# 重新构建
rebuild() {
    print_info "重新构建 $PROJECT_NAME..."
    docker-compose -f $COMPOSE_FILE down
    docker-compose -f $COMPOSE_FILE build --no-cache
    docker-compose -f $COMPOSE_FILE up -d
    print_info "重新构建完成"
}

# 查看日志
logs() {
    docker-compose -f $COMPOSE_FILE logs -f --tail=100
}

# 备份数据库
backup() {
    print_info "开始备份数据库..."
    
    BACKUP_DIR="./backups"
    mkdir -p $BACKUP_DIR
    
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/db_backup_$TIMESTAMP.sql"
    
    docker-compose exec -T db pg_dump -U postgres rag_db > $BACKUP_FILE
    
    if [ -f $BACKUP_FILE ]; then
        print_info "数据库备份成功: $BACKUP_FILE"
        
        # 压缩备份文件
        gzip $BACKUP_FILE
        print_info "备份文件已压缩: $BACKUP_FILE.gz"
    else
        print_error "数据库备份失败"
        exit 1
    fi
}

# 清理资源
clean() {
    print_warning "这将删除所有容器、卷和未使用的镜像"
    read -p "确定要继续吗? (yes/no) " -r
    echo
    if [[ $REPLY == "yes" ]]; then
        print_info "停止并删除容器..."
        docker-compose -f $COMPOSE_FILE down -v
        
        print_info "清理未使用的 Docker 资源..."
        docker system prune -af --volumes
        
        print_info "清理完成"
    else
        print_info "取消清理操作"
    fi
}

# 查看状态
status() {
    print_info "服务状态:"
    docker-compose -f $COMPOSE_FILE ps
}

# 更新应用
update() {
    print_info "更新应用..."
    
    # 备份数据库
    backup
    
    # 拉取最新代码（如果使用 git）
    if [ -d .git ]; then
        print_info "拉取最新代码..."
        git pull
    fi
    
    # 重新构建和启动
    rebuild
    
    print_info "更新完成"
}

# 显示帮助
show_help() {
    echo "Django RAG 项目部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "可用命令:"
    echo "  start     - 启动所有服务"
    echo "  stop      - 停止所有服务"
    echo "  restart   - 重启所有服务"
    echo "  rebuild   - 重新构建并启动"
    echo "  logs      - 查看日志"
    echo "  status    - 查看服务状态"
    echo "  backup    - 备份数据库"
    echo "  update    - 更新应用（备份+拉取代码+重建）"
    echo "  clean     - 清理所有资源（⚠️ 危险操作）"
    echo "  help      - 显示此帮助信息"
    echo ""
}

# 主逻辑
case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    rebuild)
        rebuild
        ;;
    logs)
        logs
        ;;
    status)
        status
        ;;
    backup)
        backup
        ;;
    update)
        update
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "未知命令: $1"
        show_help
        exit 1
        ;;
esac
