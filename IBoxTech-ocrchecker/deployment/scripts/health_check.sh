#!/bin/bash
# OCR系统健康检查脚本
# 用于监控系统运行状态

set -e

PROJECT_DIR="/opt/IBoxTech-ocrchecker"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
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

log_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

# 检查容器状态
check_containers() {
    log_header "容器运行状态"
    
    cd $PROJECT_DIR
    
    local services=("mysql" "redis" "minio" "backend" "frontend")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        if docker compose ps $service | grep -q "Up"; then
            log_info "$service 容器运行正常"
        else
            log_error "$service 容器未运行"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        log_info "所有容器运行正常"
    else
        log_error "部分容器运行异常，请检查日志"
        return 1
    fi
}

# 检查后端 API
check_backend() {
    log_header "后端 API 健康检查"
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/health); then
        if [ "$response" = "200" ]; then
            log_info "后端 API 响应正常 (HTTP $response)"
            
            # 获取详细健康信息
            health_data=$(curl -s http://localhost:5000/api/health)
            echo "   $health_data"
        else
            log_error "后端 API 响应异常 (HTTP $response)"
            return 1
        fi
    else
        log_error "无法连接到后端 API"
        return 1
    fi
}

# 检查前端服务
check_frontend() {
    log_header "前端服务健康检查"
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80); then
        if [ "$response" = "200" ] || [ "$response" = "304" ]; then
            log_info "前端服务响应正常 (HTTP $response)"
        else
            log_warn "前端服务响应异常 (HTTP $response)"
        fi
    else
        log_error "无法连接到前端服务"
        return 1
    fi
}

# 检查数据库连接
check_database() {
    log_header "数据库连接检查"
    
    cd $PROJECT_DIR
    
    if docker compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} -e "SELECT 1" > /dev/null 2>&1; then
        log_info "数据库连接正常"
        
        # 获取数据库统计
        local db_stats=$(docker compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD:-rootpassword} ocr_system -e "
            SELECT 
                (SELECT COUNT(*) FROM files) as files_count,
                (SELECT COUNT(*) FROM paper_articles) as papers_count,
                (SELECT COUNT(*) FROM commission_forms) as commissions_count,
                (SELECT COUNT(*) FROM users) as users_count;
        " 2>/dev/null | tail -n 1)
        
        log_info "数据库统计: $db_stats"
    else
        log_error "数据库连接失败"
        return 1
    fi
}

# 检查 MinIO 服务
check_minio() {
    log_header "MinIO 服务检查"
    
    if response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/minio/health/live); then
        if [ "$response" = "200" ]; then
            log_info "MinIO 服务运行正常 (HTTP $response)"
            
            # 检查存储桶
            cd $PROJECT_DIR
            if docker compose exec minio mc ls local/ocr-files > /dev/null 2>&1; then
                log_info "存储桶 ocr-files 可访问"
            else
                log_warn "存储桶 ocr-files 不可访问"
            fi
        else
            log_error "MinIO 服务响应异常 (HTTP $response)"
            return 1
        fi
    else
        log_error "无法连接到 MinIO 服务"
        return 1
    fi
}

# 检查 Redis 服务
check_redis() {
    log_header "Redis 服务检查"
    
    cd $PROJECT_DIR
    
    if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
        log_info "Redis 服务运行正常"
        
        # 获取 Redis 信息
        local redis_info=$(docker compose exec -T redis redis-cli INFO | grep -E "used_memory_human|connected_clients")
        echo "   $redis_info"
    else
        log_error "Redis 服务连接失败"
        return 1
    fi
}

# 检查磁盘空间
check_disk_space() {
    log_header "磁盘空间检查"
    
    local disk_usage=$(df -h / | tail -n 1 | awk '{print $5}' | sed 's/%//')
    
    if [ $disk_usage -lt 80 ]; then
        log_info "磁盘使用率: ${disk_usage}% (正常)"
    elif [ $disk_usage -lt 90 ]; then
        log_warn "磁盘使用率: ${disk_usage}% (需要关注)"
    else
        log_error "磁盘使用率: ${disk_usage}% (严重警告)"
    fi
    
    echo ""
    df -h / | head -n 1
    df -h / | tail -n 1
}

# 检查内存使用
check_memory() {
    log_header "内存使用检查"
    
    local mem_total=$(free -m | grep Mem | awk '{print $2}')
    local mem_used=$(free -m | grep Mem | awk '{print $3}')
    local mem_percent=$((mem_used * 100 / mem_total))
    
    if [ $mem_percent -lt 80 ]; then
        log_info "内存使用率: ${mem_percent}% (${mem_used}MB / ${mem_total}MB)"
    elif [ $mem_percent -lt 90 ]; then
        log_warn "内存使用率: ${mem_percent}% (${mem_used}MB / ${mem_total}MB)"
    else
        log_error "内存使用率: ${mem_percent}% (${mem_used}MB / ${mem_total}MB)"
    fi
    
    echo ""
    free -h
}

# 检查 Docker 资源
check_docker_resources() {
    log_header "Docker 容器资源使用"
    
    cd $PROJECT_DIR
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 检查外部 OCR 服务
check_external_ocr() {
    log_header "外部 OCR 服务检查"
    
    cd $PROJECT_DIR
    
    # 从环境变量读取 OCR 服务地址
    local commission_url=$(docker compose exec backend env | grep OCR_COMMISSION_SERVICE_URL | cut -d'=' -f2 | tr -d '\r')
    local paper_url=$(docker compose exec backend env | grep OCR_PAPER_SERVICE_URL | cut -d'=' -f2 | tr -d '\r')
    
    # 检查委托单 OCR 服务
    if [ -n "$commission_url" ]; then
        if docker compose exec backend curl -s -o /dev/null -w "%{http_code}" ${commission_url}/health | grep -q "200"; then
            log_info "委托单 OCR 服务运行正常: $commission_url"
        else
            log_error "委托单 OCR 服务无法访问: $commission_url"
        fi
    else
        log_warn "未配置委托单 OCR 服务地址"
    fi
    
    # 检查论文 OCR 服务
    if [ -n "$paper_url" ]; then
        if docker compose exec backend curl -s -o /dev/null -w "%{http_code}" ${paper_url}/health | grep -q "200"; then
            log_info "论文 OCR 服务运行正常: $paper_url"
        else
            log_error "论文 OCR 服务无法访问: $paper_url"
        fi
    else
        log_warn "未配置论文 OCR 服务地址"
    fi
}

# 生成健康报告
generate_report() {
    local report_file="/tmp/ocr_health_report_$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "OCR 系统健康检查报告"
        echo "生成时间: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "========================================="
        echo ""
        
        check_containers
        check_backend
        check_frontend
        check_database
        check_minio
        check_redis
        check_disk_space
        check_memory
        check_docker_resources
        check_external_ocr
        
    } | tee $report_file
    
    log_info "报告已保存到: $report_file"
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "================================================"
    echo "   OCR 系统健康检查"
    echo "================================================"
    echo -e "${NC}"
    
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "项目目录不存在: $PROJECT_DIR"
        exit 1
    fi
    
    local exit_code=0
    
    check_containers || exit_code=1
    check_backend || exit_code=1
    check_frontend || exit_code=1
    check_database || exit_code=1
    check_minio || exit_code=1
    check_redis || exit_code=1
    check_disk_space || exit_code=1
    check_memory || exit_code=1
    check_docker_resources || exit_code=1
    check_external_ocr || exit_code=1
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        log_info "========================================="
        log_info "✅ 系统健康检查通过"
        log_info "========================================="
    else
        log_error "========================================="
        log_error "❌ 系统存在问题，请检查日志"
        log_error "========================================="
    fi
    
    exit $exit_code
}

# 运行
main

