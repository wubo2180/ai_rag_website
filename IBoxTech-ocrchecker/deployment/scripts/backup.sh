#!/bin/bash
# OCR系统自动备份脚本

set -e

# 配置
BACKUP_DIR="/opt/backups/ocr-system"
PROJECT_DIR="/opt/IBoxTech-ocrchecker"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 从环境变量或配置文件读取密码
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-"rootpassword"}

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

# 创建备份目录
mkdir -p $BACKUP_DIR

log_info "========================================="
log_info "OCR 系统备份开始"
log_info "备份时间: $(date '+%Y-%m-%d %H:%M:%S')"
log_info "========================================="

# 进入项目目录
cd $PROJECT_DIR

# 1. 备份 MySQL 数据库
log_info "1/4 备份 MySQL 数据库..."
if docker compose exec -T mysql mysqldump \
    -u root \
    -p$MYSQL_ROOT_PASSWORD \
    --single-transaction \
    --quick \
    --lock-tables=false \
    --routines \
    --triggers \
    --events \
    ocr_system > $BACKUP_DIR/db_backup_$DATE.sql; then
    
    gzip $BACKUP_DIR/db_backup_$DATE.sql
    log_info "✅ 数据库备份完成: db_backup_$DATE.sql.gz"
    log_info "   大小: $(du -h $BACKUP_DIR/db_backup_$DATE.sql.gz | cut -f1)"
else
    log_error "❌ 数据库备份失败"
    exit 1
fi

# 2. 备份 MinIO 数据
log_info "2/4 备份 MinIO 数据..."
if docker compose exec -T minio tar czf - /data 2>/dev/null > $BACKUP_DIR/minio_backup_$DATE.tar.gz; then
    log_info "✅ MinIO 数据备份完成: minio_backup_$DATE.tar.gz"
    log_info "   大小: $(du -h $BACKUP_DIR/minio_backup_$DATE.tar.gz | cut -f1)"
else
    log_warn "⚠️  MinIO 数据备份失败（可能没有数据）"
fi

# 3. 备份配置文件
log_info "3/4 备份配置文件..."
if tar czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    backend/.env \
    docker-compose.yml \
    frontend/nginx.conf \
    backend/config/config.py 2>/dev/null; then
    
    log_info "✅ 配置文件备份完成: config_backup_$DATE.tar.gz"
    log_info "   大小: $(du -h $BACKUP_DIR/config_backup_$DATE.tar.gz | cut -f1)"
else
    log_warn "⚠️  部分配置文件备份失败"
fi

# 4. 清理旧备份
log_info "4/4 清理旧备份（保留 $RETENTION_DAYS 天）..."
deleted_count=$(find $BACKUP_DIR -name "*.gz" -name "*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete -print | wc -l)
log_info "✅ 清理了 $deleted_count 个旧备份文件"

# 显示备份统计
log_info "========================================="
log_info "备份完成"
log_info "备份目录: $BACKUP_DIR"
log_info "当前备份文件:"
ls -lh $BACKUP_DIR/*_$DATE.* 2>/dev/null || log_warn "没有备份文件"
log_info "========================================="

# 备份成功标记
echo $DATE > $BACKUP_DIR/last_backup.txt

