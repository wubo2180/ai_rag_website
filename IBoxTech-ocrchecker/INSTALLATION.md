# OCR数据识别系统安装指南

本文档提供OCR数据识别系统的详细安装和配置指南。

## 系统要求

### 硬件要求
- **CPU**: 4核心以上推荐
- **内存**: 8GB以上推荐
- **存储**: 50GB以上可用空间
- **网络**: 稳定的互联网连接

### 软件要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+
- **Python**: 3.8 或更高版本
- **Node.js**: 16.0 或更高版本
- **MySQL**: 8.0 或更高版本
- **Redis**: 6.0 或更高版本（可选，用于缓存和任务队列）
- **MinIO**: 最新版本（对象存储）

## 快速安装

### 自动化安装（推荐）

1. **下载项目**
```bash
git clone <repository-url>
cd IBoxTech-data
```

2. **运行安装脚本**
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

安装脚本将自动：
- 检查系统依赖
- 创建Python虚拟环境
- 安装后端依赖
- 安装前端依赖
- 创建配置文件
- 初始化数据库

### 手动安装

如果自动安装遇到问题，可以按以下步骤手动安装。

#### 1. 准备环境

**安装Python 3.8+**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# macOS
brew install python@3.9

# CentOS/RHEL
sudo yum install python3 python3-pip
```

**安装Node.js 16+**
```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# macOS
brew install node

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs
```

**安装MySQL 8.0+**
```bash
# Ubuntu/Debian
sudo apt-get install mysql-server mysql-client

# macOS
brew install mysql

# CentOS/RHEL
sudo yum install mysql-server mysql
```

**安装Redis (可选)**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# CentOS/RHEL
sudo yum install redis
```

#### 2. 安装后端依赖

```bash
cd backend

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# Linux/macOS
source venv/bin/activate
# Windows
venv\\Scripts\\activate

# 升级pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt
```

#### 3. 安装前端依赖

```bash
cd ../frontend

# 安装依赖
npm install

# 或使用yarn
yarn install
```

#### 4. 配置数据库

**创建数据库**
```sql
CREATE DATABASE ocr_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'ocr_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON ocr_system.* TO 'ocr_user'@'localhost';
FLUSH PRIVILEGES;
```

#### 5. 配置应用

**后端配置**
```bash
cd backend
cp env_example.txt .env
# 编辑.env文件配置数据库连接等信息
```

**前端配置**
```bash
cd frontend
cp .env.example .env
# 编辑.env文件配置API地址等信息
```

#### 6. 初始化数据库

```bash
cd backend
source venv/bin/activate
python migrations/init_database.py
```

## Docker部署

### 使用Docker Compose（推荐）

1. **确保安装了Docker和Docker Compose**
```bash
docker --version
docker-compose --version
```

2. **启动所有服务**
```bash
docker-compose up -d
```

这将启动以下服务：
- MySQL数据库
- Redis缓存
- MinIO对象存储
- 后端API服务
- 前端Web服务
- Nginx反向代理

3. **查看服务状态**
```bash
docker-compose ps
```

4. **查看日志**
```bash
docker-compose logs -f
```

### 单独构建镜像

**构建后端镜像**
```bash
cd backend
docker build -t ocr-backend .
```

**构建前端镜像**
```bash
cd frontend
docker build -t ocr-frontend .
```

## 配置详解

### 后端配置 (.env)

```bash
# 基本配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key

# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=ocr_user
MYSQL_PASSWORD=your_password
MYSQL_DB=ocr_system

# MinIO配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_BUCKET_NAME=ocr-files
MINIO_SECURE=false

# Redis配置
REDIS_URL=redis://localhost:6379/0

# OCR配置
OCR_USE_GPU=false
OCR_LANGUAGE=ch
OCR_MODEL_DIR=./models

# 文件上传配置
MAX_CONTENT_LENGTH=104857600  # 100MB
```

### 前端配置 (.env)

```bash
# API配置
VITE_API_BASE_URL=http://localhost:5000/api

# 应用配置
VITE_APP_TITLE=OCR数据识别系统
VITE_APP_VERSION=1.0.0

# 文件上传配置
VITE_MAX_FILE_SIZE=104857600
VITE_ALLOWED_FILE_TYPES=.pdf,.jpg,.jpeg,.png,.tiff
```

## 启动服务

### 开发环境

**启动后端**
```bash
./scripts/start-backend.sh
# 或者
cd backend
source venv/bin/activate
python app.py
```

**启动前端**
```bash
./scripts/start-frontend.sh
# 或者
cd frontend
npm run dev
```

### 生产环境

**使用Docker Compose**
```bash
docker-compose -f docker-compose.prod.yml up -d
```

**使用systemd服务**

创建服务文件：
```bash
sudo nano /etc/systemd/system/ocr-backend.service
```

```ini
[Unit]
Description=OCR Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/backend
Environment=PATH=/path/to/backend/venv/bin
ExecStart=/path/to/backend/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable ocr-backend
sudo systemctl start ocr-backend
```

## 验证安装

1. **检查后端服务**
```bash
curl http://localhost:5000/api/health
```

2. **检查前端服务**
访问 http://localhost:5173

3. **登录测试**
- 管理员账户：admin / admin123
- 测试账户：testuser / test123

## 常见问题

### 1. 数据库连接失败
- 检查MySQL服务是否启动
- 验证数据库用户名和密码
- 确认数据库已创建

### 2. Redis连接失败
- 检查Redis服务是否启动
- 验证Redis连接配置

### 3. MinIO连接失败
- 检查MinIO服务是否启动
- 验证访问密钥配置

### 4. OCR模型加载失败
- 检查网络连接
- 确认模型下载路径

### 5. 端口占用
- 修改配置文件中的端口号
- 或停止占用端口的其他服务

## 性能调优

### 数据库优化
```sql
-- 设置合适的缓冲区大小
SET GLOBAL innodb_buffer_pool_size = 2G;

-- 优化查询缓存
SET GLOBAL query_cache_size = 256M;
SET GLOBAL query_cache_type = ON;
```

### Redis配置
```bash
# 在redis.conf中设置
maxmemory 1gb
maxmemory-policy allkeys-lru
```

### Nginx配置
```nginx
# 启用gzip压缩
gzip on;
gzip_types text/plain application/json application/javascript text/css;

# 设置缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 监控和日志

### 应用日志
- 后端日志：`backend/logs/app.log`
- 前端日志：浏览器控制台

### 系统监控
访问 http://localhost:5000/api/health 查看系统状态

### 数据库监控
```sql
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads%';
```

## 备份和恢复

### 数据库备份
```bash
mysqldump -u ocr_user -p ocr_system > backup_$(date +%Y%m%d).sql
```

### MinIO数据备份
```bash
mc mirror minio/ocr-files /path/to/backup/files/
```

### 恢复数据
```bash
mysql -u ocr_user -p ocr_system < backup_20240115.sql
```

## 安全配置

### SSL/TLS配置
参见 `deployment/nginx/ssl/` 目录下的配置文件

### 防火墙设置
```bash
# 只开放必要端口
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 22
sudo ufw enable
```

### 定期安全更新
```bash
# Ubuntu/Debian
sudo apt-get update && sudo apt-get upgrade

# CentOS/RHEL
sudo yum update
```

有问题请参考 [故障排除指南](TROUBLESHOOTING.md) 或提交Issue。
