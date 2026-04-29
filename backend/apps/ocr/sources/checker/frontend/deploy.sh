#!/bin/bash
# 前端快速部署脚本

set -e

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

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $SCRIPT_DIR

echo -e "${BLUE}"
echo "================================================"
echo "   OCR 前端快速部署工具"
echo "================================================"
echo -e "${NC}"

# 步骤 1：检查 Node.js
log_step "步骤 1/6: 检查环境依赖"
if ! command -v node &> /dev/null; then
    log_error "Node.js 未安装"
    log_error "请先安装 Node.js 18+："
    log_error "  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -"
    log_error "  sudo apt-get install -y nodejs"
    exit 1
fi

log_info "✅ Node.js: $(node --version)"
log_info "✅ npm: $(npm --version)"

# 步骤 2：询问部署方式
log_step "步骤 2/6: 选择部署方式"
echo "请选择部署方式："
echo "  1) Nginx 部署（推荐，适合生产环境）"
echo "  2) Docker 部署（需要 Docker）"
echo "  3) 仅构建（不部署）"
echo ""
read -p "请选择 [1-3]: " deploy_method

# 步骤 3：询问后端地址
log_step "步骤 3/6: 配置后端 API 地址"
read -p "请输入后端 API 地址（例如：http://192.168.1.100:5000）: " backend_url

if [ -z "$backend_url" ]; then
    log_error "后端地址不能为空"
    exit 1
fi

log_info "后端地址: $backend_url"

# 步骤 4：安装依赖
log_step "步骤 4/6: 安装依赖"
log_info "使用国内镜像源..."
npm config set registry https://registry.npmmirror.com

if [ ! -d "node_modules" ]; then
    log_info "首次安装依赖，可能需要几分钟..."
    npm install
else
    log_info "更新依赖..."
    npm install
fi

log_info "✅ 依赖安装完成"

# 步骤 5：构建项目
log_step "步骤 5/6: 构建项目"
log_info "开始构建生产版本..."

npm run build

if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    log_info "✅ 构建成功"
    log_info "   构建目录: $(pwd)/dist"
    log_info "   文件大小: $(du -sh dist/ | cut -f1)"
else
    log_error "❌ 构建失败"
    exit 1
fi

# 步骤 6：部署
log_step "步骤 6/6: 部署"

case $deploy_method in
    1)
        # Nginx 部署
        log_info "使用 Nginx 部署..."
        
        # 检查 Nginx
        if ! command -v nginx &> /dev/null; then
            log_error "Nginx 未安装"
            log_error "请先安装 Nginx："
            log_error "  sudo apt-get install -y nginx"
            exit 1
        fi
        
        # 创建 Nginx 配置
        NGINX_CONFIG="/tmp/ocr-frontend.conf"
        cat > $NGINX_CONFIG <<EOF
server {
    listen 80;
    server_name _;
    
    root $SCRIPT_DIR/dist;
    index index.html;
    
    access_log /var/log/nginx/ocr_frontend_access.log;
    error_log /var/log/nginx/ocr_frontend_error.log;
    
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /api/ {
        proxy_pass $backend_url;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        client_max_body_size 100M;
    }
    
    location / {
        try_files \$uri \$uri/ /index.html;
        add_header Cache-Control "no-cache";
    }
    
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    server_tokens off;
}
EOF
        
        log_info "Nginx 配置文件已生成: $NGINX_CONFIG"
        log_info ""
        log_info "请执行以下命令完成部署："
        log_info ""
        echo -e "${YELLOW}  sudo cp $NGINX_CONFIG /etc/nginx/sites-available/ocr-frontend${NC}"
        echo -e "${YELLOW}  sudo ln -sf /etc/nginx/sites-available/ocr-frontend /etc/nginx/sites-enabled/${NC}"
        echo -e "${YELLOW}  sudo nginx -t${NC}"
        echo -e "${YELLOW}  sudo systemctl restart nginx${NC}"
        log_info ""
        
        read -p "是否现在执行以上命令？(yes/no): " exec_now
        if [ "$exec_now" = "yes" ]; then
            sudo cp $NGINX_CONFIG /etc/nginx/sites-available/ocr-frontend
            sudo ln -sf /etc/nginx/sites-available/ocr-frontend /etc/nginx/sites-enabled/
            sudo nginx -t
            sudo systemctl restart nginx
            log_info "✅ Nginx 部署完成"
        fi
        ;;
        
    2)
        # Docker 部署
        log_info "使用 Docker 部署..."
        
        if ! command -v docker &> /dev/null; then
            log_error "Docker 未安装"
            exit 1
        fi
        
        # 修改 nginx.conf 中的后端地址
        log_info "更新 nginx.conf 中的后端地址..."
        sed -i "s|proxy_pass http://backend:5000|proxy_pass $backend_url|g" nginx.conf
        
        # 构建镜像
        log_info "构建 Docker 镜像..."
        docker build -t ocr-frontend:latest .
        
        # 停止旧容器
        if docker ps -a | grep -q ocr-frontend; then
            log_info "停止旧容器..."
            docker stop ocr-frontend || true
            docker rm ocr-frontend || true
        fi
        
        # 启动新容器
        log_info "启动新容器..."
        docker run -d \
            --name ocr-frontend \
            --restart unless-stopped \
            -p 80:80 \
            ocr-frontend:latest
        
        log_info "✅ Docker 部署完成"
        
        # 显示容器状态
        sleep 2
        docker ps | grep ocr-frontend
        ;;
        
    3)
        # 仅构建
        log_info "仅构建模式，不进行部署"
        log_info "构建文件位于: $SCRIPT_DIR/dist/"
        log_info ""
        log_info "您可以手动部署："
        log_info "  1. 将 dist/ 目录复制到 Web 服务器"
        log_info "  2. 配置 Web 服务器指向 dist/ 目录"
        log_info "  3. 配置 API 代理到后端: $backend_url"
        ;;
        
    *)
        log_error "无效的选择"
        exit 1
        ;;
esac

# 完成
echo ""
log_step "🎉 部署流程完成！"

if [ "$deploy_method" != "3" ]; then
    SERVER_IP=$(hostname -I | awk '{print $1}')
    echo -e "${GREEN}访问地址:${NC}"
    echo -e "  http://$SERVER_IP"
    echo ""
    echo -e "${GREEN}后端地址:${NC}"
    echo -e "  $backend_url"
    echo ""
    echo -e "${YELLOW}提醒：${NC}"
    echo -e "  1. 确保后端服务 ($backend_url) 可访问"
    echo -e "  2. 如果使用域名，请配置 DNS 解析"
    echo -e "  3. 生产环境建议配置 HTTPS"
    echo -e "  4. 首次访问请使用管理员账户登录"
fi

