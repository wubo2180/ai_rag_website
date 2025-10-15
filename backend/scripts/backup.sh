#!/bin/bash

################################################################################
# 数据库备份脚本
# 用途: 备份 PostgreSQL 数据库并自动清理旧备份
# 使用: ./backup.sh
################################################################################

set -e

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# 检查 Docker Compose 是否可用
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装或不可用"
    exit 1
fi

cd "$PROJECT_DIR"

# 检查容器是否运行
if ! docker compose ps | grep -q "django_rag_db.*Up"; then
    log_error "数据库容器未运行"
    exit 1
fi

# 创建备份目录
mkdir -p "$BACKUP_DIR"

log_info "开始备份数据库..."
log_info "备份目录: $BACKUP_DIR"

# 执行备份
if docker compose exec -T db pg_dump -U postgres rag_db > "$BACKUP_FILE"; then
    log_info "数据库导出成功"
    
    # 压缩备份文件
    log_info "压缩备份文件..."
    gzip "$BACKUP_FILE"
    BACKUP_FILE_GZ="${BACKUP_FILE}.gz"
    
    # 获取文件大小
    SIZE=$(du -h "$BACKUP_FILE_GZ" | cut -f1)
    log_info "备份完成: $BACKUP_FILE_GZ (大小: $SIZE)"
    
    # 清理旧备份
    log_info "清理 $RETENTION_DAYS 天前的备份..."
    DELETED=$(find "$BACKUP_DIR" -name "db_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
    if [ "$DELETED" -gt 0 ]; then
        log_info "删除了 $DELETED 个旧备份文件"
    else
        log_info "没有需要清理的旧备份"
    fi
    
    # 列出现有备份
    log_info "当前备份列表:"
    ls -lh "$BACKUP_DIR"/db_backup_*.sql.gz | tail -n 5
    
else
    log_error "数据库备份失败"
    exit 1
fi

log_info "备份任务完成"
