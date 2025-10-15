# Django RAG 项目 - Docker 部署快速指南

> 📚 **更多文档**:
> - 🏭 **[生产环境部署指南](PRODUCTION_DEPLOYMENT.md)** - 完整的生产部署流程
> - ⚡ **[快速参考手册](QUICK_REFERENCE.md)** - 常用命令和故障排除
> - 🐳 **[Docker 详细文档](DOCKER_DEPLOYMENT.md)** - Docker 部署完整说明

## 🚀 3 分钟快速部署（本地测试）

### 前提条件
- 已安装 Docker 和 Docker Compose
- 服务器至少 2GB 内存

### 快速开始

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd django-rag-website

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，至少修改以下项:
# - SECRET_KEY（生成一个随机密钥）
# - DB_PASSWORD（设置数据库密码）
# - ALLOWED_HOSTS（添加你的域名）
# - DIFY_API_KEY 和 DIFY_BASE_URL（配置 Dify API）

# 3. 启动服务（使用部署脚本）
chmod +x deploy.sh
./deploy.sh start

# 或者手动启动
docker-compose up -d
```

### 访问应用

- **网站**: http://your-server-ip
- **管理后台**: http://your-server-ip/admin
  - 默认账号: `admin`
  - 默认密码: `admin123`
  - ⚠️ **请立即修改密码!**

## 📁 项目结构

```
├── Dockerfile                 # Django 应用镜像
├── docker-compose.yml         # 服务编排
├── docker-entrypoint.sh       # 启动脚本
├── deploy.sh                  # 部署工具（推荐使用）
├── .env.example               # 环境变量模板
├── nginx/                     # Nginx 配置
│   ├── nginx.conf
│   └── conf.d/default.conf
└── DOCKER_DEPLOYMENT.md       # 详细部署文档
```

## 🛠️ 常用命令

### 使用部署脚本（推荐）

```bash
./deploy.sh start      # 启动服务
./deploy.sh stop       # 停止服务
./deploy.sh restart    # 重启服务
./deploy.sh logs       # 查看日志
./deploy.sh status     # 查看状态
./deploy.sh backup     # 备份数据库
./deploy.sh rebuild    # 重新构建
./deploy.sh update     # 更新应用
./deploy.sh clean      # 清理资源
```

### 手动 Docker Compose 命令

```bash
docker-compose up -d               # 启动
docker-compose down                # 停止
docker-compose logs -f             # 查看日志
docker-compose ps                  # 查看状态
docker-compose restart             # 重启
docker-compose exec web bash      # 进入容器
```

## 🔧 配置说明

### 必须修改的环境变量

在 `.env` 文件中：

```env
# 生成随机密钥
SECRET_KEY=<使用下面的命令生成>

# 设置强密码
DB_PASSWORD=<设置一个强密码>

# 添加你的域名
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# 配置 Dify API
DIFY_API_KEY=<你的 Dify API 密钥>
DIFY_BASE_URL=<你的 Dify 服务地址>
```

### 生成 SECRET_KEY

```bash
# 方法 1: 使用 Python
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# 方法 2: 使用 OpenSSL
openssl rand -base64 50
```

## 📊 服务架构

```
┌─────────────┐
│   Nginx     │  (端口 80/443)
│  (反向代理) │
└──────┬──────┘
       │
┌──────▼──────┐     ┌──────────────┐
│   Django    │────▶│  PostgreSQL  │
│  (Gunicorn) │     │   (数据库)   │
└─────────────┘     └──────────────┘
    (端口 8000)          (端口 5432)
```

## 🔒 安全检查清单

- [ ] 修改默认的 `SECRET_KEY`
- [ ] 修改默认的数据库密码
- [ ] 修改默认的管理员密码
- [ ] 设置 `DEBUG=False`
- [ ] 配置 `ALLOWED_HOSTS`
- [ ] 启用 HTTPS（生产环境）
- [ ] 配置防火墙
- [ ] 定期备份数据

## 🐛 故障排除

### 容器无法启动
```bash
docker-compose logs web    # 查看错误日志
docker-compose ps          # 查看容器状态
```

### 数据库连接失败
```bash
docker-compose exec db pg_isready    # 检查数据库
docker-compose logs db               # 查看数据库日志
```

### 静态文件 404
```bash
docker-compose exec web python manage.py collectstatic --noinput
docker-compose restart nginx
```

### Dify API 无法连接
```bash
# 检查环境变量
docker-compose exec web env | grep DIFY

# 测试连接
docker-compose exec web python -c "import requests; print(requests.get('${DIFY_BASE_URL}').status_code)"
```

## 📖 详细文档

完整的部署和维护文档请参考: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

包含:
- 详细的安装步骤
- 生产环境配置
- HTTPS 配置
- 备份和恢复
- 性能优化
- 监控和日志
- 常见问题解决

## 🔄 更新应用

```bash
# 使用部署脚本（自动备份）
./deploy.sh update

# 手动更新
git pull                           # 拉取最新代码
docker-compose build               # 重新构建
docker-compose down                # 停止服务
docker-compose up -d               # 启动新版本
```

## 💾 数据备份

```bash
# 使用部署脚本
./deploy.sh backup

# 手动备份
docker-compose exec db pg_dump -U postgres rag_db > backup.sql
```

## 📞 获取帮助

- 查看日志: `docker-compose logs -f`
- 进入容器: `docker-compose exec web bash`
- 查看状态: `docker-compose ps`
- 部署文档: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)

## 📝 许可证

[添加你的许可证信息]
