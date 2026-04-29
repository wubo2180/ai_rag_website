# 生产环境部署完整指南

## 📋 部署前检查清单

### 系统要求
- [ ] 服务器操作系统：Linux (推荐 Ubuntu 20.04+ 或 CentOS 8+)
- [ ] Docker Engine: 20.10+
- [ ] Docker Compose: 2.0+
- [ ] Git
- [ ] 最低硬件配置：4核 CPU，8GB RAM，50GB 磁盘空间
- [ ] 推荐硬件配置：8核 CPU，16GB RAM，200GB SSD

### 网络要求
- [ ] 服务器需要访问外网（下载依赖和镜像）
- [ ] 开放端口：80 (HTTP), 443 (HTTPS)
- [ ] 域名已解析到服务器IP（如需要）

### 数据准备
- [ ] 备份现有数据（如有）
- [ ] 准备 SSL 证书（生产环境推荐）
- [ ] 准备外部 OCR 服务地址（委托单和论文识别服务）

---

## 🚀 部署步骤

### 步骤 1：安装 Docker 和 Docker Compose

#### Ubuntu/Debian
```bash
# 更新软件包索引
sudo apt-get update

# 安装必要的依赖
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 设置稳定版仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
sudo docker --version
sudo docker compose version
```

#### CentOS/RHEL
```bash
# 安装必要的依赖
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker Engine
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker

# 验证安装
sudo docker --version
sudo docker compose version
```

#### 添加当前用户到 docker 组（可选，避免每次使用 sudo）
```bash
sudo usermod -aG docker $USER
# 重新登录使组权限生效
```

---

### 步骤 2：获取项目代码

```bash
# 克隆项目（如使用 Git）
git clone <your-repository-url> /opt/IBoxTech-ocrchecker
cd /opt/IBoxTech-ocrchecker

# 或者上传项目文件到服务器
# scp -r /local/path/IBoxTech-ocrchecker user@server:/opt/
```

---

### 步骤 3：配置生产环境变量

#### 3.1 创建后端环境变量文件

```bash
# 复制环境变量模板
cp backend/env_example.txt backend/.env

# 编辑环境变量
vi backend/.env
```

**生产环境 `.env` 配置示例：**

```bash
# ==================== 应用配置 ====================
FLASK_ENV=production
SECRET_KEY=YOUR_VERY_LONG_RANDOM_SECRET_KEY_CHANGE_THIS_123456789
JWT_SECRET_KEY=YOUR_JWT_SECRET_KEY_ALSO_VERY_LONG_AND_RANDOM_987654321

# ==================== 数据库配置 ====================
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=ocr_user
MYSQL_PASSWORD=YOUR_SECURE_MYSQL_PASSWORD
MYSQL_DB=ocr_system

# ==================== MinIO对象存储配置 ====================
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=YOUR_MINIO_ACCESS_KEY
MINIO_SECRET_KEY=YOUR_MINIO_SECRET_KEY_VERY_LONG
MINIO_BUCKET_NAME=ocr-files
MINIO_SECURE=false

# ==================== Redis配置 ====================
REDIS_URL=redis://redis:6379/0

# ==================== OCR配置 ====================
OCR_MODEL_DIR=/app/models
OCR_USE_GPU=false
OCR_LANGUAGE=ch

# 外部OCR服务地址（根据实际部署修改）
OCR_COMMISSION_SERVICE_URL=http://your-commission-ocr-service:6001
OCR_PAPER_SERVICE_URL=http://your-paper-ocr-service:6002
OCR_COMMISSION_TIMEOUT=300
OCR_PAPER_TIMEOUT=300
OCR_DEFAULT_USER=system

# ==================== 日志配置 ====================
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

**⚠️ 安全提示：**
- ✅ 请务必修改所有默认密码和密钥
- ✅ 使用强密码（至少32位随机字符）
- ✅ 不要将 `.env` 文件提交到版本控制

**生成随机密钥的方法：**
```bash
# 生成 SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 生成 JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
```

#### 3.2 修改 docker-compose.yml

```bash
vi docker-compose.yml
```

**需要修改的关键配置：**

```yaml
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: YOUR_SECURE_ROOT_PASSWORD  # ← 修改这里
      MYSQL_PASSWORD: YOUR_SECURE_MYSQL_PASSWORD      # ← 修改这里
  
  minio:
    environment:
      MINIO_ROOT_USER: YOUR_MINIO_ACCESS_KEY          # ← 修改这里
      MINIO_ROOT_PASSWORD: YOUR_MINIO_SECRET_KEY      # ← 修改这里
  
  backend:
    environment:
      SECRET_KEY: YOUR_VERY_LONG_RANDOM_SECRET_KEY    # ← 修改这里
      JWT_SECRET_KEY: YOUR_JWT_SECRET_KEY             # ← 修改这里
      MYSQL_PASSWORD: YOUR_SECURE_MYSQL_PASSWORD      # ← 与上面保持一致
      MINIO_ACCESS_KEY: YOUR_MINIO_ACCESS_KEY         # ← 与上面保持一致
      MINIO_SECRET_KEY: YOUR_MINIO_SECRET_KEY         # ← 与上面保持一致
      # 修改外部OCR服务地址
      OCR_COMMISSION_SERVICE_URL: http://your-commission-ocr-service:6001
      OCR_PAPER_SERVICE_URL: http://your-paper-ocr-service:6002
```

---

### 步骤 4：创建部署目录结构

```bash
# 创建必要的目录
mkdir -p deployment/nginx
mkdir -p deployment/mysql
mkdir -p deployment/logs
mkdir -p deployment/backups

# 设置权限
chmod 755 deployment
chmod 755 deployment/nginx
chmod 755 deployment/mysql
chmod 777 deployment/logs
chmod 700 deployment/backups
```

---

### 步骤 5：配置 Nginx（可选，用于 SSL 和域名）

如果需要配置域名和 HTTPS，创建 Nginx 配置：

```bash
vi deployment/nginx/nginx.conf
```

**Nginx 配置示例：**

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Let's Encrypt 验证目录
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    # 其他请求重定向到 HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS 主服务
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # 日志
    access_log /var/log/nginx/ocr_access.log;
    error_log /var/log/nginx/ocr_error.log;
    
    # 前端静态文件
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # API 代理
    location /api/ {
        proxy_pass http://backend:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # 超时配置（OCR识别可能耗时较长）
        proxy_read_timeout 600s;
        proxy_connect_timeout 600s;
        proxy_send_timeout 600s;
        
        # 文件上传大小限制
        client_max_body_size 100M;
    }
}
```

#### 获取 SSL 证书（使用 Let's Encrypt）

```bash
# 安装 certbot
sudo apt-get install -y certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 证书会保存在：
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem

# 复制到项目目录
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/nginx/ssl/
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/nginx/ssl/
```

---

### 步骤 6：初始化数据库脚本

创建数据库初始化脚本：

```bash
vi deployment/mysql/init.sql
```

```sql
-- 创建数据库
CREATE DATABASE IF NOT EXISTS ocr_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE ocr_system;

-- 设置时区
SET time_zone = '+08:00';

-- 后续的表创建将由 Flask-Migrate 自动处理
```

---

### 步骤 7：构建和启动服务

#### 7.1 构建 Docker 镜像

```bash
# 构建所有镜像
sudo docker compose build

# 或分别构建
sudo docker compose build backend
sudo docker compose build frontend
```

#### 7.2 启动所有服务

```bash
# 启动所有服务（后台运行）
sudo docker compose up -d

# 查看服务状态
sudo docker compose ps

# 查看日志
sudo docker compose logs -f
```

**预期输出：**
```
NAME              IMAGE                    STATUS
ocr-mysql         mysql:8.0                Up
ocr-redis         redis:7-alpine           Up
ocr-minio         minio/minio:latest       Up
ocr-backend       iboxtech-backend:latest  Up
ocr-frontend      iboxtech-frontend:latest Up
ocr-nginx         nginx:alpine             Up (可选)
```

---

### 步骤 8：初始化数据库和创建管理员

#### 8.1 运行数据库迁移

```bash
# 进入后端容器
sudo docker compose exec backend bash

# 初始化数据库迁移
flask db init  # 如果已有 migrations 目录，跳过此步

# 创建迁移脚本
flask db migrate -m "Initial migration"

# 应用迁移
flask db upgrade

# 退出容器
exit
```

#### 8.2 创建管理员用户

**方法 1：使用 Python 脚本创建**

```bash
sudo docker compose exec backend python - <<'EOF'
from app.models.user import User
from app import db, create_app

app = create_app()
with app.app_context():
    # 检查管理员是否已存在
    existing_admin = User.query.filter_by(username='admin').first()
    if existing_admin:
        print('管理员用户已存在')
    else:
        # 创建管理员用户
        admin = User(
            username='admin',
            email='admin@iboxtech.com',
            real_name='系统管理员',
            role='admin'
        )
        admin.set_password('Admin@2025')  # 请修改为强密码
        db.session.add(admin)
        db.session.commit()
        print('✅ 管理员用户创建成功')
        print('用户名: admin')
        print('密码: Admin@2025 (请登录后立即修改)')
EOF
```

**方法 2：使用后端 API 创建**

```bash
# 启动服务后，使用 curl 调用注册 API
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@iboxtech.com",
    "password": "Admin@2025",
    "real_name": "系统管理员",
    "role": "admin"
  }'
```

---

### 步骤 9：配置 MinIO

```bash
# 访问 MinIO 控制台
# http://your-server-ip:9001

# 使用配置的账号登录
# 用户名: YOUR_MINIO_ACCESS_KEY
# 密码: YOUR_MINIO_SECRET_KEY

# 或使用命令行配置
sudo docker compose exec minio mc alias set local http://localhost:9000 YOUR_MINIO_ACCESS_KEY YOUR_MINIO_SECRET_KEY

# 创建存储桶
sudo docker compose exec minio mc mb local/ocr-files

# 设置存储桶为私有（默认）
sudo docker compose exec minio mc anonymous set none local/ocr-files
```

---

### 步骤 10：验证部署

#### 10.1 健康检查

```bash
# 检查后端健康状态
curl http://localhost:5000/api/health

# 预期输出：
# {"status": "healthy", "database": "connected", "minio": "connected"}

# 检查前端访问
curl http://localhost:80

# 检查所有容器状态
sudo docker compose ps
```

#### 10.2 功能测试

1. **访问前端界面**
   - 浏览器访问：http://your-server-ip:80 或 https://your-domain.com
   
2. **登录系统**
   - 用户名：`admin`
   - 密码：`Admin@2025`（或您设置的密码）

3. **测试文件上传**
   - 上传一个测试 PDF 文件
   - 检查是否成功保存到 MinIO

4. **测试 OCR 识别**
   - 选择文件类型（委托单或论文）
   - 点击识别
   - 检查识别结果是否正常显示

5. **测试数据保存**
   - 修改识别结果
   - 点击"保存入库"
   - 在数据管理页面查看是否保存成功

---

## 🔒 安全加固

### 1. 修改默认密码

```bash
# 数据库 root 密码
sudo docker compose exec mysql mysql -u root -p
ALTER USER 'root'@'%' IDENTIFIED BY 'NEW_SECURE_PASSWORD';
FLUSH PRIVILEGES;

# 系统管理员密码
# 登录系统后，在"个人中心"修改密码
```

### 2. 配置防火墙

```bash
# 使用 ufw (Ubuntu)
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw enable

# 禁止直接访问内部服务端口
sudo ufw deny 3306/tcp     # MySQL
sudo ufw deny 6379/tcp     # Redis
sudo ufw deny 9000/tcp     # MinIO
```

### 3. 设置文件权限

```bash
# 后端日志目录
sudo chown -R 1000:1000 backend/logs
sudo chmod 755 backend/logs

# 确保敏感文件不可读
sudo chmod 600 backend/.env
sudo chmod 600 deployment/nginx/ssl/*.key
```

### 4. 启用 SELinux/AppArmor（可选）

```bash
# CentOS/RHEL - 配置 SELinux
sudo setenforce 1
sudo setsebool -P httpd_can_network_connect 1

# Ubuntu - 配置 AppArmor
sudo systemctl enable apparmor
sudo systemctl start apparmor
```

---

## 📊 监控和日志

### 1. 查看实时日志

```bash
# 所有服务日志
sudo docker compose logs -f

# 特定服务日志
sudo docker compose logs -f backend
sudo docker compose logs -f frontend
sudo docker compose logs -f mysql

# 查看最近的 100 行日志
sudo docker compose logs --tail=100 backend
```

### 2. 配置日志轮转

创建日志轮转配置：

```bash
sudo vi /etc/logrotate.d/docker-ocr
```

```
/home/h3c/workspace/IBoxTech-ocrchecker/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    sharedscripts
    postrotate
        docker compose restart backend > /dev/null 2>&1 || true
    endscript
}

/home/h3c/workspace/IBoxTech-ocrchecker/deployment/nginx/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 nginx nginx
    sharedscripts
    postrotate
        docker compose exec nginx nginx -s reload > /dev/null 2>&1 || true
    endscript
}
```

### 3. 系统资源监控

```bash
# 查看容器资源使用情况
sudo docker stats

# 查看磁盘使用
sudo docker system df

# 查看卷使用情况
sudo docker volume ls
sudo docker volume inspect iboxtech-ocrchecker_mysql_data
```

---

## 💾 数据备份和恢复

### 1. 自动备份脚本

创建备份脚本：

```bash
sudo vi /opt/backup-ocr-system.sh
```

```bash
#!/bin/bash
# OCR系统自动备份脚本

# 配置
BACKUP_DIR="/opt/backups/ocr-system"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=7

# 创建备份目录
mkdir -p $BACKUP_DIR

# 1. 备份 MySQL 数据库
echo "开始备份数据库..."
sudo docker compose exec -T mysql mysqldump \
    -u root \
    -pYOUR_SECURE_ROOT_PASSWORD \
    --single-transaction \
    --quick \
    --lock-tables=false \
    ocr_system > $BACKUP_DIR/db_backup_$DATE.sql

gzip $BACKUP_DIR/db_backup_$DATE.sql
echo "✅ 数据库备份完成: db_backup_$DATE.sql.gz"

# 2. 备份 MinIO 数据
echo "开始备份 MinIO 数据..."
sudo docker compose exec -T minio tar czf - /data > $BACKUP_DIR/minio_backup_$DATE.tar.gz
echo "✅ MinIO 数据备份完成: minio_backup_$DATE.tar.gz"

# 3. 备份配置文件
echo "开始备份配置文件..."
tar czf $BACKUP_DIR/config_backup_$DATE.tar.gz \
    backend/.env \
    docker-compose.yml \
    deployment/nginx/nginx.conf
echo "✅ 配置文件备份完成: config_backup_$DATE.tar.gz"

# 4. 清理旧备份
echo "清理 $RETENTION_DAYS 天前的备份..."
find $BACKUP_DIR -name "*.gz" -type f -mtime +$RETENTION_DAYS -delete
echo "✅ 清理完成"

# 5. 备份完成通知
echo "========================================="
echo "备份完成时间: $(date)"
echo "备份目录: $BACKUP_DIR"
echo "========================================="
```

```bash
# 设置执行权限
sudo chmod +x /opt/backup-ocr-system.sh

# 测试备份脚本
sudo /opt/backup-ocr-system.sh
```

### 2. 设置定时备份（Crontab）

```bash
# 编辑 crontab
sudo crontab -e

# 添加定时任务（每天凌晨 2 点备份）
0 2 * * * /opt/backup-ocr-system.sh >> /var/log/ocr-backup.log 2>&1
```

### 3. 数据恢复

```bash
# 恢复数据库
sudo docker compose exec -T mysql mysql \
    -u root \
    -pYOUR_SECURE_ROOT_PASSWORD \
    ocr_system < /opt/backups/ocr-system/db_backup_YYYYMMDD_HHMMSS.sql

# 恢复 MinIO 数据
sudo docker compose stop minio
sudo docker compose exec -T minio tar xzf - -C / < /opt/backups/ocr-system/minio_backup_YYYYMMDD_HHMMSS.tar.gz
sudo docker compose start minio
```

---

## 🔄 更新和维护

### 1. 更新应用代码

```bash
# 备份当前版本
sudo /opt/backup-ocr-system.sh

# 拉取最新代码
cd /opt/IBoxTech-ocrchecker
git pull origin main

# 重新构建镜像
sudo docker compose build

# 停止服务
sudo docker compose down

# 启动新版本
sudo docker compose up -d

# 运行数据库迁移（如有）
sudo docker compose exec backend flask db upgrade

# 验证服务
sudo docker compose ps
curl http://localhost:5000/api/health
```

### 2. 滚动更新（零停机）

如果需要零停机更新，可以使用多实例部署：

```bash
# 启动新版本的第二个实例
sudo docker compose up -d --scale backend=2

# 等待新实例就绪
sleep 30

# 移除旧实例
sudo docker compose up -d --scale backend=1 --no-recreate
```

### 3. 清理 Docker 资源

```bash
# 清理未使用的镜像
sudo docker image prune -a

# 清理未使用的卷
sudo docker volume prune

# 清理未使用的网络
sudo docker network prune

# 完整清理（谨慎使用）
sudo docker system prune -a --volumes
```

---

## 📈 性能优化

### 1. MySQL 优化

修改 `docker-compose.yml`，添加 MySQL 配置：

```yaml
mysql:
  command: >
    --default-authentication-plugin=mysql_native_password
    --character-set-server=utf8mb4
    --collation-server=utf8mb4_unicode_ci
    --innodb-buffer-pool-size=2G
    --innodb-log-file-size=256M
    --max-connections=500
    --slow-query-log=1
    --slow-query-log-file=/var/log/mysql/slow.log
    --long-query-time=2
```

### 2. Redis 优化

```yaml
redis:
  command: >
    redis-server
    --appendonly yes
    --maxmemory 1gb
    --maxmemory-policy allkeys-lru
    --save 900 1
    --save 300 10
    --save 60 10000
```

### 3. 后端优化

修改 `docker-compose.yml`，使用 Gunicorn 运行 Flask：

```yaml
backend:
  command: >
    gunicorn
    --bind 0.0.0.0:5000
    --workers 4
    --threads 2
    --timeout 300
    --access-logfile /app/logs/access.log
    --error-logfile /app/logs/error.log
    app:app
```

需要在 `backend/requirements.txt` 添加：
```
gunicorn==21.2.0
```

### 4. 前端优化

前端已通过 Vite 构建优化：
- ✅ 代码分割
- ✅ Tree Shaking
- ✅ 资源压缩
- ✅ Gzip 压缩
- ✅ 静态资源缓存

---

## 🛡️ 故障排查

### 常见问题和解决方案

#### 1. 容器无法启动

```bash
# 查看详细日志
sudo docker compose logs [service-name]

# 检查配置文件
sudo docker compose config

# 重新构建
sudo docker compose build --no-cache [service-name]
sudo docker compose up -d
```

#### 2. 数据库连接失败

```bash
# 检查 MySQL 容器状态
sudo docker compose ps mysql

# 进入 MySQL 容器检查
sudo docker compose exec mysql bash
mysql -u root -p
SHOW DATABASES;
SELECT user, host FROM mysql.user;

# 检查网络连接
sudo docker compose exec backend ping mysql
```

#### 3. MinIO 无法访问

```bash
# 检查 MinIO 容器
sudo docker compose ps minio

# 查看 MinIO 日志
sudo docker compose logs minio

# 检查存储桶
sudo docker compose exec minio mc ls local/
```

#### 4. OCR 识别失败

```bash
# 检查后端日志
sudo docker compose logs backend | grep OCR

# 检查外部 OCR 服务是否可访问
sudo docker compose exec backend curl -I http://your-commission-ocr-service:6001/health
sudo docker compose exec backend curl -I http://your-paper-ocr-service:6002/health

# 检查环境变量
sudo docker compose exec backend env | grep OCR
```

#### 5. 前端页面无法访问

```bash
# 检查前端容器
sudo docker compose ps frontend

# 检查 Nginx 配置
sudo docker compose exec frontend nginx -t

# 重启前端服务
sudo docker compose restart frontend
```

#### 6. 内存不足

```bash
# 查看内存使用
free -h
sudo docker stats

# 增加 swap（临时方案）
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## 📝 维护命令速查

### 服务管理

```bash
# 启动所有服务
sudo docker compose up -d

# 停止所有服务
sudo docker compose down

# 重启特定服务
sudo docker compose restart backend

# 查看服务状态
sudo docker compose ps

# 查看资源使用
sudo docker stats
```

### 日志管理

```bash
# 实时查看日志
sudo docker compose logs -f

# 查看特定服务日志
sudo docker compose logs -f backend

# 查看最近 100 行日志
sudo docker compose logs --tail=100 backend

# 导出日志
sudo docker compose logs backend > backend.log
```

### 数据库管理

```bash
# 进入数据库
sudo docker compose exec mysql mysql -u root -p ocr_system

# 备份数据库
sudo docker compose exec mysql mysqldump -u root -p ocr_system > backup.sql

# 恢复数据库
sudo docker compose exec -T mysql mysql -u root -p ocr_system < backup.sql
```

### 容器管理

```bash
# 进入容器 shell
sudo docker compose exec backend bash
sudo docker compose exec frontend sh

# 查看容器配置
sudo docker inspect ocr-backend

# 重启容器
sudo docker compose restart backend
```

---

## 🎯 性能基准

### 预期性能指标

| 指标 | 目标值 |
|------|--------|
| API 响应时间 | < 100ms |
| 文件上传速度 | > 10MB/s |
| OCR 识别时间（委托单） | < 30s |
| OCR 识别时间（论文） | < 60s |
| 并发用户数 | 100+ |
| 数据库查询时间 | < 50ms |

### 性能测试

```bash
# 使用 ab (Apache Bench) 测试 API
ab -n 1000 -c 10 http://localhost:5000/api/health

# 使用 wrk 测试
wrk -t12 -c400 -d30s http://localhost:5000/api/health
```

---

## 🆘 应急预案

### 服务宕机恢复

```bash
# 1. 快速重启
sudo docker compose restart

# 2. 如果无法恢复，完全重启
sudo docker compose down
sudo docker compose up -d

# 3. 如果还是失败，从备份恢复
sudo /opt/restore-from-backup.sh
```

### 数据损坏恢复

```bash
# 1. 停止服务
sudo docker compose down

# 2. 恢复数据库
sudo docker compose up -d mysql
sudo docker compose exec -T mysql mysql -u root -p ocr_system < /opt/backups/ocr-system/db_backup_latest.sql

# 3. 恢复 MinIO
sudo docker compose up -d minio
# 手动恢复或重新上传文件

# 4. 启动所有服务
sudo docker compose up -d
```

---

## 📞 技术支持

### 获取支持

1. **查看文档**
   - `/docs` 目录下的各种技术文档
   - `README.md` 快速开始指南

2. **收集诊断信息**
   ```bash
   # 生成诊断报告
   sudo docker compose ps > diagnostic.txt
   sudo docker compose logs >> diagnostic.txt
   sudo docker version >> diagnostic.txt
   sudo docker compose version >> diagnostic.txt
   uname -a >> diagnostic.txt
   free -h >> diagnostic.txt
   df -h >> diagnostic.txt
   ```

3. **联系技术支持**
   - 提供诊断报告
   - 描述问题现象
   - 说明复现步骤

---

## ✅ 部署完成检查表

部署完成后，请逐一检查：

- [ ] 所有 Docker 容器都在运行（`docker compose ps`）
- [ ] 数据库连接正常（`curl http://localhost:5000/api/health`）
- [ ] MinIO 可访问（`http://localhost:9001`）
- [ ] 前端页面可访问（`http://your-server-ip` 或域名）
- [ ] 管理员账户可登录
- [ ] 文件上传功能正常
- [ ] OCR 识别功能正常（委托单和论文）
- [ ] 数据保存到数据库正常
- [ ] 数据查询和展示正常
- [ ] 备份脚本配置完成
- [ ] 日志轮转配置完成
- [ ] 防火墙规则配置完成
- [ ] SSL 证书配置完成（生产环境）
- [ ] 修改了所有默认密码
- [ ] 外部 OCR 服务连接正常

---

## 📚 相关文档

- `DEPLOYMENT.md` - 部署指南
- `QUICKSTART.md` - 快速开始
- `README.md` - 项目说明
- `docs/NEW_SYSTEM_STARTUP_GUIDE.md` - 新系统启动指南
- `docs/OCR_UNIFIED_INTERFACE_SPEC.md` - OCR 接口规范

---

**部署日期：** 2025-11-25  
**系统版本：** 1.0.0  
**维护人员：** IBoxTech 团队

