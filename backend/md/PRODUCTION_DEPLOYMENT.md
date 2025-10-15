# 生产环境部署指南

本指南将帮助你将 Django RAG 应用部署到生产服务器。

## 📋 目录

- [服务器要求](#服务器要求)
- [部署前准备](#部署前准备)
- [步骤 1: 服务器初始化](#步骤-1-服务器初始化)
- [步骤 2: 安装 Docker 环境](#步骤-2-安装-docker-环境)
- [步骤 3: 部署应用](#步骤-3-部署应用)
- [步骤 4: 配置域名](#步骤-4-配置域名)
- [步骤 5: 配置 HTTPS](#步骤-5-配置-https)
- [步骤 6: 性能优化](#步骤-6-性能优化)
- [步骤 7: 监控和维护](#步骤-7-监控和维护)
- [安全检查清单](#安全检查清单)
- [故障排除](#故障排除)

---

## 服务器要求

### 最低配置
- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 20GB SSD
- **操作系统**: Ubuntu 20.04/22.04 LTS 或 CentOS 7/8
- **网络**: 公网 IP 地址

### 推荐配置
- **CPU**: 4 核心
- **内存**: 8GB RAM
- **存储**: 50GB SSD
- **带宽**: 5Mbps+

### 推荐云服务商
- 阿里云 ECS
- 腾讯云 CVM
- AWS EC2
- DigitalOcean Droplet
- Vultr

---

## 部署前准备

### 1. 准备域名
- 购买域名（阿里云、腾讯云、GoDaddy 等）
- 准备 DNS 解析

### 2. 准备服务器
- 购买云服务器
- 获取 root 或 sudo 权限
- 记录服务器公网 IP

### 3. 本地准备
- 确保代码已提交到 Git 仓库（GitHub、GitLab、Gitee）
- 备份本地数据

---

## 步骤 1: 服务器初始化

### 1.1 连接服务器

```bash
# SSH 连接到服务器
ssh root@your-server-ip

# 或使用密钥
ssh -i /path/to/key.pem root@your-server-ip
```

### 1.2 更新系统

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# CentOS/RHEL
sudo yum update -y
```

### 1.3 创建部署用户

```bash
# 创建用户
sudo adduser deploy

# 添加到 sudo 组
sudo usermod -aG sudo deploy

# 切换到 deploy 用户
su - deploy
```

### 1.4 配置防火墙

```bash
# Ubuntu (UFW)
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status

# CentOS (firewalld)
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 1.5 安装基础工具

```bash
# Ubuntu/Debian
sudo apt install -y git curl wget vim

# CentOS/RHEL
sudo yum install -y git curl wget vim
```

---

## 步骤 2: 安装 Docker 环境

### 2.1 安装 Docker

#### Ubuntu

```bash
# 卸载旧版本
sudo apt remove docker docker-engine docker.io containerd runc

# 安装依赖
sudo apt install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

# 添加 Docker 官方 GPG 密钥
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# 设置仓库
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录使组权限生效
exit
su - deploy
```

#### CentOS

```bash
# 卸载旧版本
sudo yum remove docker docker-client docker-client-latest docker-common docker-latest docker-latest-logrotate docker-logrotate docker-engine

# 安装 yum-utils
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动 Docker
sudo systemctl start docker
sudo systemctl enable docker

# 添加用户到 docker 组
sudo usermod -aG docker $USER
```

### 2.2 验证 Docker 安装

```bash
docker --version
docker compose version

# 测试运行
docker run hello-world
```

### 2.3 配置 Docker 镜像加速（可选，国内推荐）

```bash
# 创建配置文件
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://mirror.ccs.tencentyun.com",
    "https://registry.docker-cn.com",
    "https://docker.mirrors.ustc.edu.cn"
  ]
}
EOF

# 重启 Docker
sudo systemctl daemon-reload
sudo systemctl restart docker
```

---

## 步骤 3: 部署应用

### 3.1 克隆代码

```bash
# 创建项目目录
mkdir -p ~/projects
cd ~/projects

# 克隆仓库
git clone <your-repo-url> django-rag-website
cd django-rag-website

# 或者使用 SCP 上传
# 本地执行:
# scp -r ./django-rag-website deploy@your-server-ip:~/projects/
```

### 3.2 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量
nano .env  # 或使用 vim .env
```

**重要：修改以下配置项**

```bash
# Django 设置
DEBUG=False  # 生产环境必须为 False
SECRET_KEY=<生成一个新的随机密钥>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip

# 数据库配置
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=<设置一个强密码>
DB_HOST=db
DB_PORT=5432

# Dify API 配置
DIFY_API_KEY=<你的 Dify API 密钥>
DIFY_BASE_URL=<你的 Dify 服务地址>
DIFY_DEFAULT_MODEL=通义千问

# 可用的 AI 模型列表
AVAILABLE_AI_MODELS=deepseek深度思考,通义千问,腾讯混元,豆包,Kimi,GPT-5,Claude4,Gemini2.5,Grok-4,Llama4
```

### 3.3 生成 SECRET_KEY

```bash
# 在服务器上生成 SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 将输出的密钥复制到 .env 文件的 SECRET_KEY
```

### 3.4 启动应用

```bash
# 构建并启动容器
docker compose up -d --build

# 查看启动日志
docker compose logs -f

# 等待所有服务启动（按 Ctrl+C 退出日志查看）
```

### 3.5 验证部署

```bash
# 检查容器状态
docker compose ps

# 所有容器应该都是 "Up" 状态

# 测试访问
curl http://localhost:8080

# 查看 Django 日志
docker compose logs web

# 查看数据库状态
docker compose exec db pg_isready -U postgres
```

---

## 步骤 4: 配置域名

### 4.1 DNS 解析

在你的域名服务商（阿里云、腾讯云等）控制台添加 A 记录：

| 记录类型 | 主机记录 | 记录值 | TTL |
|---------|---------|--------|-----|
| A | @ | your-server-ip | 600 |
| A | www | your-server-ip | 600 |

### 4.2 等待 DNS 生效

```bash
# 测试 DNS 解析（本地电脑执行）
ping your-domain.com
nslookup your-domain.com

# 通常需要 5-30 分钟生效
```

### 4.3 更新 Nginx 配置

编辑 `nginx/conf.d/default.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # 其他配置保持不变...
}
```

### 4.4 重启 Nginx

```bash
docker compose restart nginx
```

---

## 步骤 5: 配置 HTTPS

### 5.1 安装 Certbot

```bash
# Ubuntu
sudo apt install -y certbot

# CentOS
sudo yum install -y certbot
```

### 5.2 停止 Nginx 容器（临时）

```bash
docker compose stop nginx
```

### 5.3 获取 SSL 证书

```bash
# 使用 Certbot standalone 模式
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# 按照提示输入邮箱地址
# 同意服务条款

# 证书将保存在:
# /etc/letsencrypt/live/your-domain.com/fullchain.pem
# /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 5.4 更新 docker-compose.yml

```yaml
  nginx:
    image: nginx:alpine
    container_name: django_rag_nginx
    restart: always
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - static_volume:/app/staticfiles:ro
      - media_volume:/app/media:ro
      # 添加 SSL 证书挂载
      - /etc/letsencrypt:/etc/letsencrypt:ro
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web
    networks:
      - django_network
```

### 5.5 创建 HTTPS Nginx 配置

创建 `nginx/conf.d/ssl.conf`：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS 服务器
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL 证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # 安全头
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # 客户端上传大小限制
    client_max_body_size 100M;

    # 静态文件
    location /static/ {
        alias /app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # 媒体文件
    location /media/ {
        alias /app/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # 代理到 Django
    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health/ {
        access_log off;
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

### 5.6 删除旧配置并重启

```bash
# 备份旧配置
mv nginx/conf.d/default.conf nginx/conf.d/default.conf.bak

# 重启服务
docker compose up -d

# 测试 HTTPS 访问
curl https://your-domain.com
```

### 5.7 配置证书自动续期

```bash
# 编辑 crontab
sudo crontab -e

# 添加以下行（每天凌晨 2 点检查并续期）
0 2 * * * certbot renew --quiet --post-hook "docker compose -f /home/deploy/projects/django-rag-website/docker-compose.yml restart nginx"
```

---

## 步骤 6: 性能优化

### 6.1 调整 Gunicorn Workers

编辑 `Dockerfile`，根据服务器 CPU 核心数调整：

```dockerfile
# 推荐公式: workers = (2 × CPU核心数) + 1
# 2核: 5 workers
# 4核: 9 workers

CMD ["gunicorn", "--workers=5", "--bind=0.0.0.0:8000", "config.wsgi:application"]
```

### 6.2 启用 Gzip 压缩

已在 `nginx/nginx.conf` 中配置：

```nginx
gzip on;
gzip_vary on;
gzip_proxied any;
gzip_comp_level 6;
gzip_types text/plain text/css text/xml text/javascript application/json application/javascript application/xml+rss;
```

### 6.3 配置 Redis 缓存（可选）

**docker-compose.yml 添加 Redis 服务：**

```yaml
  redis:
    image: redis:7-alpine
    container_name: django_rag_redis
    restart: always
    volumes:
      - redis_data:/data
    networks:
      - django_network
    command: redis-server --appendonly yes

volumes:
  postgres_data:
  static_volume:
  media_volume:
  redis_data:  # 添加
```

**requirements.txt 添加：**

```
django-redis==5.3.0
```

**settings.py 配置缓存：**

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://redis:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Session 使用 Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 6.4 数据库连接池优化

**requirements.txt 添加：**

```
django-db-pool==1.0.4
```

**settings.py 配置：**

```python
DATABASES = {
    'default': {
        'ENGINE': 'dj_db_conn_pool.backends.postgresql',  # 改用连接池
        # ... 其他配置保持不变
        'CONN_MAX_AGE': 600,
        'POOL_OPTIONS': {
            'POOL_SIZE': 10,
            'MAX_OVERFLOW': 20,
        }
    }
}
```

---

## 步骤 7: 监控和维护

### 7.1 配置日志

创建 `docker-compose.override.yml`（生产环境配置）：

```yaml
version: '3.8'

services:
  web:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  db:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
  
  nginx:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 7.2 数据库备份脚本

创建 `scripts/backup.sh`：

```bash
#!/bin/bash

# 数据库备份脚本
BACKUP_DIR="/home/deploy/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/db_backup_$DATE.sql"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 执行备份
docker compose exec -T db pg_dump -U postgres rag_db > $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 删除 7 天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "备份完成: $BACKUP_FILE.gz"
```

设置权限和定时任务：

```bash
chmod +x scripts/backup.sh

# 添加到 crontab（每天凌晨 3 点备份）
crontab -e
# 添加:
0 3 * * * /home/deploy/projects/django-rag-website/scripts/backup.sh >> /home/deploy/logs/backup.log 2>&1
```

### 7.3 监控脚本

创建 `scripts/monitor.sh`：

```bash
#!/bin/bash

# 简单的健康检查脚本
DOMAIN="https://your-domain.com"
EMAIL="your-email@example.com"

# 检查网站是否可访问
if ! curl -f -s -o /dev/null -w "%{http_code}" $DOMAIN | grep -q "200"; then
    echo "网站无法访问: $DOMAIN" | mail -s "网站告警" $EMAIL
fi

# 检查容器状态
DOWN_CONTAINERS=$(docker compose ps | grep -v "Up" | grep -v "NAME" | wc -l)
if [ $DOWN_CONTAINERS -gt 0 ]; then
    echo "有容器停止运行" | mail -s "Docker 容器告警" $EMAIL
fi

# 检查磁盘空间
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    echo "磁盘使用率超过 80%: $DISK_USAGE%" | mail -s "磁盘空间告警" $EMAIL
fi
```

### 7.4 查看实时日志

```bash
# 所有服务日志
docker compose logs -f

# 只看 Django 日志
docker compose logs -f web

# 最近 100 行
docker compose logs --tail=100 web

# 查看错误日志
docker compose logs web | grep ERROR
```

### 7.5 常用管理命令

```bash
# 进入 Django 容器
docker compose exec web bash

# 执行 Django 管理命令
docker compose exec web python manage.py shell
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py migrate

# 查看容器资源使用
docker stats

# 重启服务
docker compose restart web
docker compose restart nginx

# 更新代码并重新部署
git pull
docker compose up -d --build

# 备份数据库
docker compose exec db pg_dump -U postgres rag_db > backup.sql

# 恢复数据库
cat backup.sql | docker compose exec -T db psql -U postgres rag_db
```

---

## 安全检查清单

### 部署前检查

- [ ] `DEBUG=False` 已设置
- [ ] `SECRET_KEY` 已更改为随机密钥
- [ ] 数据库密码使用强密码
- [ ] `ALLOWED_HOSTS` 正确配置
- [ ] HTTPS 已启用
- [ ] 防火墙已配置
- [ ] SSH 密钥登录（禁用密码登录）
- [ ] 定期备份已配置
- [ ] 日志轮转已配置

### 运行时检查

- [ ] 所有容器正常运行
- [ ] SSL 证书有效且自动续期
- [ ] 数据库定期备份
- [ ] 磁盘空间充足（>20%）
- [ ] 内存使用正常（<80%）
- [ ] 日志没有持续错误

### 定期维护

- [ ] 每周检查日志
- [ ] 每月更新系统和 Docker
- [ ] 每月检查备份可用性
- [ ] 每季度检查安全更新
- [ ] 每季度进行灾难恢复演练

---

## 故障排除

### 问题 1: 容器无法启动

```bash
# 查看详细日志
docker compose logs web

# 检查配置文件
docker compose config

# 重新构建
docker compose down
docker compose up -d --build
```

### 问题 2: 数据库连接失败

```bash
# 检查数据库容器
docker compose ps db

# 测试数据库连接
docker compose exec db pg_isready -U postgres

# 查看数据库日志
docker compose logs db

# 进入容器检查
docker compose exec db psql -U postgres -c "\l"
```

### 问题 3: 静态文件 404

```bash
# 重新收集静态文件
docker compose exec web python manage.py collectstatic --noinput

# 检查 Nginx 配置
docker compose exec nginx nginx -t

# 重启 Nginx
docker compose restart nginx
```

### 问题 4: 内存不足

```bash
# 查看内存使用
free -h
docker stats

# 优化措施：
# 1. 减少 Gunicorn workers
# 2. 限制容器内存
# 3. 升级服务器配置
```

### 问题 5: SSL 证书过期

```bash
# 手动续期
sudo certbot renew

# 检查证书状态
sudo certbot certificates

# 重启 Nginx
docker compose restart nginx
```

### 问题 6: 性能缓慢

```bash
# 检查资源使用
docker stats
top

# 查看慢查询
docker compose exec db psql -U postgres -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# 优化措施：
# 1. 启用 Redis 缓存
# 2. 优化数据库查询
# 3. 启用 CDN
# 4. 增加 Gunicorn workers
```

---

## 快速命令参考

```bash
# 部署/更新
git pull && docker compose up -d --build

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f web

# 重启服务
docker compose restart

# 备份数据库
docker compose exec db pg_dump -U postgres rag_db > backup_$(date +%Y%m%d).sql

# 进入容器
docker compose exec web bash

# 停止服务
docker compose down

# 完全清理（危险！）
docker compose down -v
```

---

## 获取帮助

- **项目文档**: [README.md](README.md)
- **Docker 文档**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **问题反馈**: 提交 Issue 到 GitHub 仓库

---

## 总结

完成以上步骤后，你的 Django RAG 应用应该已经成功部署到生产环境！

**关键检查点：**
1. ✅ 服务器环境配置完成
2. ✅ Docker 和应用运行正常
3. ✅ 域名解析和 HTTPS 配置
4. ✅ 备份和监控系统运行
5. ✅ 安全措施全部启用

**推荐的部署流程：**
1. 在测试服务器完整走一遍流程
2. 验证所有功能正常
3. 准备回滚方案
4. 在生产服务器部署
5. 持续监控 24-48 小时

祝部署顺利！🚀
