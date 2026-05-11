#!/bin/bash
# OCR系统数据恢复脚本

set -e

# 配置
BACKUP_DIR="/opt/backups/ocr-system"
PROJECT_DIR="/opt/IBoxTech-ocrchecker"
MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-"rootpassword"}

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

# 列出可用的备份
list_backups() {
    log_step "可用的备份文件"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR/*.sql.gz 2>/dev/null)" ]; then
        log_error "没有找到备份文件"
        exit 1
    fi
    
    echo "数据库备份:"
    ls -lh $BACKUP_DIR/db_backup_*.sql.gz 2>/dev/null || echo "  无"
    
    echo ""
    echo "MinIO 备份:"
    ls -lh $BACKUP_DIR/minio_backup_*.tar.gz 2>/dev/null || echo "  无"
    
    echo ""
    echo "配置文件备份:"
    ls -lh $BACKUP_DIR/config_backup_*.tar.gz 2>/dev/null || echo "  无"
}

# 选择备份文件
select_backup() {
    local backup_type=$1
    local pattern=$2
    
    local backups=($(ls -t $BACKUP_DIR/${pattern} 2>/dev/null))
    
    if [ ${#backups[@]} -eq 0 ]; then
        log_error "没有找到 $backup_type 备份文件"
        return 1
    fi
    
    echo "可用的 $backup_type 备份:"
    for i in "${!backups[@]}"; do
        echo "  [$i] $(basename ${backups[$i]}) - $(date -r ${backups[$i]} '+%Y-%m-%d %H:%M:%S')"
    done
    
    read -p "请选择要恢复的备份 [0-$((${#backups[@]}-1))]: " selection
    
    if [ -z "$selection" ] || [ "$selection" -ge "${#backups[@]}" ]; then
        log_error "无效的选择"
        return 1
    fi
    
    echo "${backups[$selection]}"
}

# 恢复数据库
restore_database() {
    log_step "恢复数据库"
    
    local db_backup=$(select_backup "数据库" "db_backup_*.sql.gz")
    
    if [ -z "$db_backup" ]; then
        return 1
    fi
    
    log_warn "⚠️  警告：这将覆盖当前数据库中的所有数据！"
    read -p "确认要恢复数据库吗？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消数据库恢复"
        return 0
    fi
    
    log_info "解压备份文件..."
    gunzip -c $db_backup > /tmp/restore.sql
    
    log_info "恢复数据库..."
    cd $PROJECT_DIR
    
    if docker compose exec -T mysql mysql \
        -u root \
        -p$MYSQL_ROOT_PASSWORD \
        ocr_system < /tmp/restore.sql; then
        
        log_info "✅ 数据库恢复完成"
        rm /tmp/restore.sql
    else
        log_error "❌ 数据库恢复失败"
        rm /tmp/restore.sql
        exit 1
    fi
}

# 恢复 MinIO 数据
restore_minio() {
    log_step "恢复 MinIO 数据"
    
    local minio_backup=$(select_backup "MinIO" "minio_backup_*.tar.gz")
    
    if [ -z "$minio_backup" ]; then
        return 1
    fi
    
    log_warn "⚠️  警告：这将覆盖当前 MinIO 中的所有数据！"
    read -p "确认要恢复 MinIO 数据吗？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消 MinIO 数据恢复"
        return 0
    fi
    
    log_info "停止 MinIO 服务..."
    cd $PROJECT_DIR
    docker compose stop minio
    
    log_info "恢复 MinIO 数据..."
    cat $minio_backup | docker compose run --rm -T minio tar xzf - -C /
    
    log_info "启动 MinIO 服务..."
    docker compose start minio
    
    log_info "✅ MinIO 数据恢复完成"
}

# 恢复配置文件
restore_config() {
    log_step "恢复配置文件"
    
    local config_backup=$(select_backup "配置文件" "config_backup_*.tar.gz")
    
    if [ -z "$config_backup" ]; then
        return 1
    fi
    
    log_warn "⚠️  警告：这将覆盖当前的配置文件！"
    read -p "确认要恢复配置文件吗？(yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "取消配置文件恢复"
        return 0
    fi
    
    log_info "恢复配置文件..."
    cd $PROJECT_DIR
    tar xzf $config_backup
    
    log_info "✅ 配置文件恢复完成"
}

# 主菜单
main_menu() {
    echo -e "${BLUE}"
    echo "================================================"
    echo "   OCR 系统数据恢复工具"
    echo "================================================"
    echo -e "${NC}"
    
    list_backups
    
    echo ""
    echo "请选择恢复操作:"
    echo "  1) 恢复数据库"
    echo "  2) 恢复 MinIO 数据"
    echo "  3) 恢复配置文件"
    echo "  4) 全部恢复"
    echo "  0) 退出"
    echo ""
    
    read -p "请选择 [0-4]: " choice
    
    case $choice in
        1)
            restore_database
            ;;
        2)
            restore_minio
            ;;
        3)
            restore_config
            ;;
        4)
            restore_database
            restore_minio
            restore_config
            log_info "🎉 全部恢复完成，请重启服务："
            log_info "   cd $PROJECT_DIR && docker compose restart"
            ;;
        0)
            log_info "退出恢复工具"
            exit 0
            ;;
        *)
            log_error "无效的选择"
            exit 1
            ;;
    esac
}

# 运行主菜单
main_menu

