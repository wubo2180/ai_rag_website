# Django RAG 项目 Docker 部署指南

## 📋 目录

- [前提条件](#前提条件)
- [快速开始](#快速开始)
- [详细步骤](#详细步骤)
- [配置说明](#配置说明)
- [常用命令](#常用命令)
- [故障排除](#故障排除)
- [生产环境优化](#生产环境优化)

---

## 前提条件

在开始之前，确保服务器上已安装：

- **Docker**: 版本 20.10 或更高
- **Docker Compose**: 版本 1.29 或更高
- **Git**: 用于克隆代码

### 安装 Docker (Ubuntu/Debian)

```bash
# 更新包索引
sudo apt-get update

# 安装必要的包
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# 添加 Docker 仓库
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"

# 安装 Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version

# 将当前用户添加到 docker 组（可选）
sudo usermod -aG docker $USER
# 需要重新登录才能生效
```

---

## 快速开始

### 1. 克隆项目

```bash
git clone <your-repository-url>
cd django-rag-website
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env
```

**必须修改的配置**:
```env
SECRET_KEY=生成一个随机的密钥
DB_PASSWORD=设置一个强密码
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DIFY_API_KEY=your-dify-api-key
DIFY_BASE_URL=http://your-dify-server/v1
```

### 3. 构建并启动服务

```bash
# 构建镜像
docker-compose build

# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 4. 访问应用

- **应用地址**: http://your-server-ip
- **管理后台**: http://your-server-ip/admin
  - 默认用户名: `admin`
  - 默认密码: `admin123` (⚠️ 请立即修改)

---

## 详细步骤

### 项目结构

```
django-rag-website/
├── Dockerfile              # Django 应用的 Docker 镜像定义
├── docker-compose.yml      # 多容器编排配置
├── docker-entrypoint.sh    # 容器启动脚本
├── .dockerignore          # Docker 构建时忽略的文件
├── .env.example           # 环境变量模板
├── requirements.txt        # Python 依赖
├── nginx/                 # Nginx 配置
│   ├── nginx.conf         # 主配置
│   └── conf.d/
│       └── default.conf   # 站点配置
├── config/                # Django 配置
├── apps/                  # Django 应用
└── manage.py
```

### 服务说明

#### 1. **db** - PostgreSQL 数据库
- **镜像**: `postgres:15-alpine`
- **端口**: 5432 (仅内部访问)
- **数据持久化**: `postgres_data` 卷

#### 2. **web** - Django 应用
- **基于**: Python 3.11
- **端口**: 8000 (仅内部访问)
- **服务器**: Gunicorn (3 workers)
- **数据持久化**: `static_volume`, `media_volume`

#### 3. **nginx** - Web 服务器/反向代理
- **镜像**: `nginx:alpine`
- **端口**: 80 (HTTP), 443 (HTTPS)
- **功能**: 
  - 静态文件服务
  - 反向代理到 Django
  - Gzip 压缩
  - 缓存控制

---

## 配置说明

### 环境变量 (.env)

```env
# ===== Django 核心配置 =====
# 调试模式 (生产环境必须为 False)
DEBUG=False

# 密钥 (必须修改为随机字符串)
SECRET_KEY=your-secret-key-here-please-change

# 允许的主机名（逗号分隔）
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# ===== 数据库配置 =====
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=strong-password-here  # ⚠️ 修改为强密码
DB_HOST=db
DB_PORT=5432

# ===== Dify API 配置 =====
# Dify API 密钥
DIFY_API_KEY=app-K9fjgkD8JbNrNfTH2ECIv4jw

# Dify API 地址
DIFY_BASE_URL=http://host.docker.internal/v1

# 默认模型
DIFY_DEFAULT_MODEL=通义千问

# 可用模型列表
AVAILABLE_AI_MODELS=deepseek深度思考,通义千问,腾讯混元,豆包,Kimi,GPT-5,Claude4,Gemini2.5,Grok-4,Llama4
```

### 生成 SECRET_KEY

```bash
# Python 方式
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 或使用 openssl
openssl rand -base64 50
```

---

## 常用命令

### Docker Compose 命令

```bash
# 启动所有服务（后台运行）
docker-compose up -d

# 启动并查看日志
docker-compose up

# 停止所有服务
docker-compose down

# 停止并删除所有数据（⚠️ 危险操作）
docker-compose down -v

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f              # 所有服务
docker-compose logs -f web          # 仅 Django
docker-compose logs -f db           # 仅数据库
docker-compose logs -f nginx        # 仅 Nginx

# 重启服务
docker-compose restart              # 所有服务
docker-compose restart web          # 仅 Django

# 重新构建并启动
docker-compose up -d --build
```

### Django 管理命令

```bash
# 进入 Django 容器
docker-compose exec web bash

# 在容器内执行 Django 命令
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic
docker-compose exec web python manage.py shell

# 查看数据库
docker-compose exec db psql -U postgres -d rag_db
```

### 数据库备份与恢复

```bash
# 备份数据库
docker-compose exec db pg_dump -U postgres rag_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 恢复数据库
docker-compose exec -T db psql -U postgres rag_db < backup_20241013_120000.sql

# 备份数据卷
docker run --rm -v django-rag-website_postgres_data:/data -v $(pwd):/backup ubuntu tar czf /backup/postgres_backup.tar.gz /data
```

---

## 故障排除

### 常见问题

#### 1. 容器无法启动

```bash
# 查看详细错误信息
docker-compose logs web

# 检查容器状态
docker-compose ps

# 重新构建镜像
docker-compose build --no-cache
docker-compose up -d
```

#### 2. 数据库连接失败

```bash
# 检查数据库是否就绪
docker-compose exec db pg_isready

# 查看数据库日志
docker-compose logs db

# 检查环境变量
docker-compose exec web env | grep DB_
```

#### 3. 静态文件404

```bash
# 重新收集静态文件
docker-compose exec web python manage.py collectstatic --noinput

# 检查 Nginx 配置
docker-compose exec nginx nginx -t

# 重启 Nginx
docker-compose restart nginx
```

#### 4. Dify API 连接失败

```bash
# 检查 Dify 配置
docker-compose exec web env | grep DIFY

# 测试连接
docker-compose exec web python manage.py shell
>>> from apps.ai_service.services import ai_service
>>> ai_service.generate_response("测试", "test_user")
```

#### 5. 权限问题

```bash
# 修复文件权限
sudo chown -R 1000:1000 .

# 重启容器
docker-compose restart
```

### 查看日志级别

在 `config/settings.py` 中调整日志级别：

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR
    },
}
```

---

## 生产环境优化

### 1. HTTPS 配置

创建 `nginx/conf.d/ssl.conf`:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ... 其他配置与 default.conf 相同
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

更新 `docker-compose.yml`:

```yaml
nginx:
  volumes:
    - ./nginx/ssl:/etc/nginx/ssl:ro
```

### 2. 使用 Let's Encrypt

```bash
# 安装 certbot
sudo apt-get install certbot

# 获取证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书到项目
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
```

### 3. 自动备份

创建 `backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 备份数据库
docker-compose exec -T db pg_dump -U postgres rag_db > $BACKUP_DIR/db_$DATE.sql

# 备份媒体文件
tar czf $BACKUP_DIR/media_$DATE.tar.gz media/

# 删除30天前的备份
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

添加到 crontab:
```bash
0 2 * * * /path/to/backup.sh
```

### 4. 监控和告警

使用 Docker 健康检查：

```yaml
web:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

### 5. 性能优化

#### 增加 Gunicorn Workers

在 `Dockerfile` 中:
```dockerfile
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2"]
```

Worker 数量建议：`(2 × CPU cores) + 1`

#### 启用 Redis 缓存

添加到 `docker-compose.yml`:

```yaml
redis:
  image: redis:alpine
  container_name: django_rag_redis
  restart: always
  networks:
    - django_network
```

更新 Django 配置:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
    }
}
```

---

## 维护任务

### 定期任务

1. **每日**:
   - 查看日志: `docker-compose logs --tail=100`
   - 检查磁盘空间: `df -h`

2. **每周**:
   - 数据库备份验证
   - 更新 Docker 镜像: `docker-compose pull && docker-compose up -d`

3. **每月**:
   - 清理未使用的 Docker 资源:
     ```bash
     docker system prune -a
     ```
   - 检查安全更新

### 更新应用

```bash
# 1. 拉取最新代码
git pull

# 2. 重新构建
docker-compose build

# 3. 停止服务
docker-compose down

# 4. 启动新版本
docker-compose up -d

# 5. 检查日志
docker-compose logs -f
```

---

## 安全建议

1. ✅ 修改所有默认密码
2. ✅ 使用强 SECRET_KEY
3. ✅ 启用 HTTPS
4. ✅ 定期备份数据
5. ✅ 限制端口暴露（只开放 80/443）
6. ✅ 使用防火墙（UFW/iptables）
7. ✅ 定期更新系统和 Docker 镜像
8. ✅ 监控日志异常行为

---

## 支持

如有问题，请查看：
- Django 日志: `docker-compose logs web`
- Nginx 日志: `docker-compose logs nginx`
- 数据库日志: `docker-compose logs db`

或提交 Issue 到项目仓库。

---

## 许可证

[添加你的许可证信息]
