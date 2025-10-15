#!/bin/bash

################################################################################
# 数据库恢复脚本
# 用途: 从备份文件恢复 PostgreSQL 数据库
# 使用: ./restore.sh <backup_file.sql.gz>
################################################################################

set -e

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# 检查参数
if [ -z "$1" ]; then
    log_error "请指定备份文件"
    echo "使用方法: $0 <backup_file.sql.gz>"
    exit 1
fi

BACKUP_FILE="$1"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    log_error "备份文件不存在: $BACKUP_FILE"
    exit 1
fi

cd "$PROJECT_DIR"

# 检查容器是否运行
if ! docker compose ps | grep -q "django_rag_db.*Up"; then
    log_error "数据库容器未运行"
    exit 1
fi

log_warn "⚠️  警告: 此操作将覆盖当前数据库！"
read -p "是否继续? (输入 'yes' 确认): " confirm

if [ "$confirm" != "yes" ]; then
    log_info "操作已取消"
    exit 0
fi

# 创建当前数据库备份
log_info "创建当前数据库的安全备份..."
SAFETY_BACKUP="/tmp/db_safety_backup_$(date +%Y%m%d_%H%M%S).sql"
docker compose exec -T db pg_dump -U postgres rag_db > "$SAFETY_BACKUP"
log_info "安全备份已保存到: $SAFETY_BACKUP"

# 解压备份文件
log_info "解压备份文件..."
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" > /tmp/restore_temp.sql
    SQL_FILE="/tmp/restore_temp.sql"
else
    SQL_FILE="$BACKUP_FILE"
fi

# 删除现有数据库并重新创建
log_info "准备数据库..."
docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS rag_db;"
docker compose exec -T db psql -U postgres -c "CREATE DATABASE rag_db;"

# 恢复数据
log_info "开始恢复数据库..."
if cat "$SQL_FILE" | docker compose exec -T db psql -U postgres rag_db; then
    log_info "数据库恢复成功"
    
    # 清理临时文件
    if [[ "$BACKUP_FILE" == *.gz ]]; then
        rm -f /tmp/restore_temp.sql
    fi
    
    # 重启 web 容器
    log_info "重启 Web 容器..."
    docker compose restart web
    
    log_info "恢复完成！"
    log_info "安全备份保存在: $SAFETY_BACKUP"
else
    log_error "数据库恢复失败"
    log_warn "尝试恢复安全备份..."
    cat "$SAFETY_BACKUP" | docker compose exec -T db psql -U postgres rag_db
    exit 1
fi
