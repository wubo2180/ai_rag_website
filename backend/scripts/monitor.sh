#!/bin/bash

################################################################################
# 系统监控脚本
# 用途: 监控服务健康状态、资源使用情况
# 使用: ./monitor.sh [--email your@email.com]
################################################################################

set -e

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOMAIN="${DOMAIN:-http://localhost:8080}"
ALERT_EMAIL="${ALERT_EMAIL:-}"

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
}

send_alert() {
    local subject="$1"
    local message="$2"
    
    if [ -n "$ALERT_EMAIL" ] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$ALERT_EMAIL"
        log_info "告警邮件已发送到: $ALERT_EMAIL"
    fi
}

cd "$PROJECT_DIR"

echo "================================"
echo "  系统监控检查"
echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================"
echo

# 1. 检查网站可访问性
echo "1. 网站可访问性检查"
if curl -f -s -o /dev/null -w "%{http_code}" "$DOMAIN" | grep -q "200\|301\|302"; then
    log_info "网站可访问: $DOMAIN"
else
    log_error "网站无法访问: $DOMAIN"
    send_alert "【告警】网站无法访问" "网站 $DOMAIN 无法访问，请立即检查"
fi
echo

# 2. 检查 Docker 容器状态
echo "2. Docker 容器状态"
if command -v docker &> /dev/null; then
    CONTAINERS=$(docker compose ps -q 2>/dev/null)
    if [ -z "$CONTAINERS" ]; then
        log_error "没有运行中的容器"
        send_alert "【告警】容器停止" "所有 Docker 容器都已停止"
    else
        DOWN_CONTAINERS=0
        while IFS= read -r container; do
            NAME=$(docker inspect --format='{{.Name}}' "$container" | sed 's/\///')
            STATUS=$(docker inspect --format='{{.State.Status}}' "$container")
            
            if [ "$STATUS" = "running" ]; then
                log_info "$NAME: 运行中"
            else
                log_error "$NAME: $STATUS"
                DOWN_CONTAINERS=$((DOWN_CONTAINERS + 1))
            fi
        done <<< "$CONTAINERS"
        
        if [ $DOWN_CONTAINERS -gt 0 ]; then
            send_alert "【告警】容器停止" "$DOWN_CONTAINERS 个容器停止运行"
        fi
    fi
else
    log_warn "Docker 未安装或不可用"
fi
echo

# 3. 检查磁盘空间
echo "3. 磁盘空间检查"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
DISK_AVAILABLE=$(df -h / | awk 'NR==2 {print $4}')

if [ "$DISK_USAGE" -lt 70 ]; then
    log_info "磁盘使用率: $DISK_USAGE% (剩余: $DISK_AVAILABLE)"
elif [ "$DISK_USAGE" -lt 85 ]; then
    log_warn "磁盘使用率: $DISK_USAGE% (剩余: $DISK_AVAILABLE)"
else
    log_error "磁盘使用率: $DISK_USAGE% (剩余: $DISK_AVAILABLE)"
    send_alert "【告警】磁盘空间不足" "磁盘使用率已达 $DISK_USAGE%"
fi
echo

# 4. 检查内存使用
echo "4. 内存使用检查"
if command -v free &> /dev/null; then
    MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100)}')
    MEM_AVAILABLE=$(free -h | grep Mem | awk '{print $7}')
    
    if [ "$MEM_USAGE" -lt 70 ]; then
        log_info "内存使用率: $MEM_USAGE% (可用: $MEM_AVAILABLE)"
    elif [ "$MEM_USAGE" -lt 85 ]; then
        log_warn "内存使用率: $MEM_USAGE% (可用: $MEM_AVAILABLE)"
    else
        log_error "内存使用率: $MEM_USAGE% (可用: $MEM_AVAILABLE)"
        send_alert "【告警】内存不足" "内存使用率已达 $MEM_USAGE%"
    fi
else
    log_warn "无法检查内存使用"
fi
echo

# 5. 检查 CPU 负载
echo "5. CPU 负载检查"
if command -v uptime &> /dev/null; then
    LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    CPU_COUNT=$(nproc)
    
    log_info "1分钟平均负载: $LOAD_AVG (CPU核心数: $CPU_COUNT)"
    
    # 负载超过 CPU 核心数的 80% 时告警
    LOAD_THRESHOLD=$(echo "$CPU_COUNT * 0.8" | bc)
    if (( $(echo "$LOAD_AVG > $LOAD_THRESHOLD" | bc -l) )); then
        log_warn "CPU 负载较高"
        send_alert "【告警】CPU负载高" "1分钟平均负载: $LOAD_AVG，CPU核心数: $CPU_COUNT"
    fi
else
    log_warn "无法检查 CPU 负载"
fi
echo

# 6. 检查数据库连接
echo "6. 数据库连接检查"
if docker compose ps | grep -q "django_rag_db.*Up"; then
    if docker compose exec -T db pg_isready -U postgres &> /dev/null; then
        log_info "数据库连接正常"
    else
        log_error "数据库连接失败"
        send_alert "【告警】数据库连接失败" "PostgreSQL 数据库无法连接"
    fi
else
    log_error "数据库容器未运行"
fi
echo

# 7. 检查最近的错误日志
echo "7. 应用错误日志检查（最近5分钟）"
if docker compose ps | grep -q "django_rag_web.*Up"; then
    ERROR_COUNT=$(docker compose logs --since=5m web 2>/dev/null | grep -i "error\|exception\|critical" | wc -l)
    
    if [ "$ERROR_COUNT" -eq 0 ]; then
        log_info "未发现错误日志"
    elif [ "$ERROR_COUNT" -lt 10 ]; then
        log_warn "发现 $ERROR_COUNT 条错误日志"
    else
        log_error "发现 $ERROR_COUNT 条错误日志"
        send_alert "【告警】应用错误频繁" "最近5分钟发现 $ERROR_COUNT 条错误日志"
    fi
else
    log_warn "Web 容器未运行，无法检查日志"
fi
echo

# 8. 检查 SSL 证书（如果配置了）
echo "8. SSL 证书检查"
if [ -d "/etc/letsencrypt/live" ]; then
    # 查找证书目录
    CERT_DIRS=$(find /etc/letsencrypt/live -maxdepth 1 -type d ! -path /etc/letsencrypt/live)
    
    if [ -n "$CERT_DIRS" ]; then
        while IFS= read -r cert_dir; do
            DOMAIN_NAME=$(basename "$cert_dir")
            CERT_FILE="$cert_dir/cert.pem"
            
            if [ -f "$CERT_FILE" ]; then
                EXPIRY_DATE=$(openssl x509 -enddate -noout -in "$CERT_FILE" | cut -d= -f2)
                EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
                NOW_EPOCH=$(date +%s)
                DAYS_LEFT=$(( ($EXPIRY_EPOCH - $NOW_EPOCH) / 86400 ))
                
                if [ "$DAYS_LEFT" -gt 30 ]; then
                    log_info "$DOMAIN_NAME: 证书有效 (剩余 $DAYS_LEFT 天)"
                elif [ "$DAYS_LEFT" -gt 7 ]; then
                    log_warn "$DOMAIN_NAME: 证书即将过期 (剩余 $DAYS_LEFT 天)"
                else
                    log_error "$DOMAIN_NAME: 证书即将过期 (剩余 $DAYS_LEFT 天)"
                    send_alert "【告警】SSL证书即将过期" "$DOMAIN_NAME 的证书将在 $DAYS_LEFT 天后过期"
                fi
            fi
        done <<< "$CERT_DIRS"
    else
        log_info "未配置 SSL 证书"
    fi
else
    log_info "未配置 Let's Encrypt 证书"
fi
echo

# 9. 检查备份状态
echo "9. 备份检查"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
if [ -d "$BACKUP_DIR" ]; then
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | head -n 1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LATEST_BACKUP")) / 86400 ))
        BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
        
        if [ "$BACKUP_AGE" -eq 0 ]; then
            log_info "最新备份: 今天 ($BACKUP_SIZE)"
        elif [ "$BACKUP_AGE" -eq 1 ]; then
            log_info "最新备份: 昨天 ($BACKUP_SIZE)"
        elif [ "$BACKUP_AGE" -lt 3 ]; then
            log_info "最新备份: $BACKUP_AGE 天前 ($BACKUP_SIZE)"
        else
            log_warn "最新备份: $BACKUP_AGE 天前 ($BACKUP_SIZE)"
            send_alert "【警告】备份过时" "最新数据库备份是 $BACKUP_AGE 天前"
        fi
    else
        log_warn "未找到备份文件"
        send_alert "【警告】没有备份" "备份目录中没有找到数据库备份文件"
    fi
else
    log_warn "备份目录不存在: $BACKUP_DIR"
fi
echo

echo "================================"
echo "  检查完成"
echo "================================"
