# OCR数据识别系统 - 部署指南

## 系统架构

系统采用前后端分离架构，包含以下组件：

- **前端**: Vue.js + Vite + Element Plus
- **后端**: Python Flask + SQLAlchemy
- **数据库**: MySQL 8.0
- **对象存储**: MinIO
- **缓存**: Redis
- **OCR引擎**: PaddleOCR
- **容器化**: Docker + Docker Compose

## 快速部署

### 1. 环境准备

确保服务器已安装：
- Docker (20.10+)
- Docker Compose (2.0+)
- Git

```bash
# CentOS/RHEL
sudo yum install -y docker docker-compose git

# Ubuntu/Debian  
sudo apt-get install -y docker.io docker-compose git

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd IBoxTech-data
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp backend/.env.example backend/.env

# 编辑配置文件
vim backend/.env
```

关键配置项：
```bash
# 数据库配置
MYSQL_HOST=mysql
MYSQL_USER=ocr_user
MYSQL_PASSWORD=your-secure-password
MYSQL_DB=ocr_system

# MinIO配置
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key

# JWT密钥
JWT_SECRET_KEY=your-jwt-secret-key

# OCR配置
OCR_USE_GPU=false
OCR_LANGUAGE=ch
```

### 4. 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 5. 初始化数据库

```bash
# 进入后端容器
docker-compose exec backend bash

# 创建数据库表
flask db upgrade

# 创建管理员用户
python -c "
from app.models.user import User
from app import db, create_app
app = create_app()
with app.app_context():
    admin = User(
        username='admin',
        email='admin@example.com', 
        password='admin123',
        real_name='系统管理员',
        role='admin'
    )
    db.session.add(admin)
    db.session.commit()
    print('管理员用户创建成功')
"
```

### 6. 访问系统

- 前端访问地址: http://localhost:8080
- 后端API地址: http://localhost:5000/api
- MinIO控制台: http://localhost:9001

默认管理员账户：
- 用户名: admin
- 密码: admin123

## 生产环境部署

### 1. SSL证书配置

```bash
# 创建SSL证书目录
mkdir -p deployment/nginx/ssl

# 将SSL证书文件放置到该目录
cp your-domain.crt deployment/nginx/ssl/
cp your-domain.key deployment/nginx/ssl/
```

### 2. 域名配置

修改 `deployment/nginx/nginx.conf`：

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/your-domain.crt;
    ssl_certificate_key /etc/nginx/ssl/your-domain.key;
    
    # SSL配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 其他配置...
}
```

### 3. 生产环境变量

```bash
# 更新docker-compose.yml中的环境变量
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-very-long-and-random
JWT_SECRET_KEY=your-production-jwt-secret-key

# 更新数据库密码
MYSQL_ROOT_PASSWORD=very-secure-root-password
MYSQL_PASSWORD=very-secure-user-password

# 更新MinIO密钥
MINIO_ROOT_USER=your-minio-admin
MINIO_ROOT_PASSWORD=very-secure-minio-password
```

### 4. 性能优化

#### 数据库优化
```sql
-- MySQL配置优化
# /etc/mysql/mysql.conf.d/mysqld.cnf
[mysqld]
innodb_buffer_pool_size = 2G
innodb_log_file_size = 256M
max_connections = 500
query_cache_size = 64M
```

#### Redis优化
```bash
# Redis配置
maxmemory 1gb
maxmemory-policy allkeys-lru
```

## 监控和维护

### 1. 日志管理

```bash
# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql

# 日志轮转配置
# /etc/logrotate.d/docker-compose
/var/lib/docker/containers/*/*.log {
    daily
    missingok
    rotate 7
    compress
    notifempty
    create 644 root root
}
```

### 2. 备份策略

```bash
#!/bin/bash
# backup.sh - 数据备份脚本

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup"

# 数据库备份
docker-compose exec mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD ocr_system > $BACKUP_DIR/db_backup_$DATE.sql

# MinIO数据备份
docker-compose exec minio mc mirror /data $BACKUP_DIR/minio_backup_$DATE/

# 清理旧备份（保留7天）
find $BACKUP_DIR -type f -mtime +7 -delete
```

### 3. 健康检查

```bash
#!/bin/bash
# health_check.sh - 健康检查脚本

# 检查服务状态
docker-compose ps

# 检查API响应
curl -f http://localhost:5000/api/health || echo "Backend API异常"

# 检查前端页面
curl -f http://localhost:8080 || echo "前端服务异常"

# 检查数据库连接
docker-compose exec mysql mysql -u ocr_user -p$MYSQL_PASSWORD -e "SELECT 1" ocr_system || echo "数据库连接异常"
```

## 故障排除

### 常见问题

1. **容器启动失败**
   ```bash
   # 检查日志
   docker-compose logs [service-name]
   
   # 重新构建镜像
   docker-compose build --no-cache [service-name]
   ```

2. **数据库连接失败**
   ```bash
   # 检查网络连接
   docker-compose exec backend ping mysql
   
   # 检查数据库状态
   docker-compose exec mysql mysql -u root -p -e "SHOW DATABASES;"
   ```

3. **OCR识别失败**
   ```bash
   # 检查PaddleOCR安装
   docker-compose exec backend python -c "import paddleocr; print('PaddleOCR正常')"
   
   # 检查模型文件
   docker-compose exec backend ls -la /app/models/
   ```

4. **文件上传失败**
   ```bash
   # 检查MinIO状态
   docker-compose exec minio mc admin info server local
   
   # 检查存储桶
   docker-compose exec minio mc ls local/
   ```

### 性能监控

建议安装以下监控工具：
- Prometheus + Grafana (系统监控)
- ELK Stack (日志分析)
- Jaeger (分布式追踪)

## 更新升级

```bash
# 拉取最新代码
git pull origin main

# 重新构建镜像
docker-compose build

# 停止服务
docker-compose down

# 备份数据
./backup.sh

# 启动新版本
docker-compose up -d

# 数据库迁移（如需要）
docker-compose exec backend flask db upgrade
```

## 技术支持

如遇到问题，请提供以下信息：
- 系统环境信息
- Docker和Docker Compose版本
- 错误日志内容
- 复现步骤

联系方式：[技术支持邮箱]
