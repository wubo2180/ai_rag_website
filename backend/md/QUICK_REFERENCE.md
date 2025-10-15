# 生产部署快速参考

## 🚀 快速部署流程

### 第一次部署

```bash
# 1. 连接到服务器
ssh user@your-server-ip

# 2. 安装 Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. 克隆代码
git clone <your-repo> django-rag-website
cd django-rag-website

# 4. 配置环境变量
cp .env.production .env
nano .env  # 修改必要的配置

# 5. 生成 SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 6. 一键部署
bash scripts/deploy_production.sh

# 7. 配置 SSL（可选）
sudo certbot certonly --standalone -d your-domain.com
# 修改 docker-compose.yml 挂载证书
# 使用 nginx/conf.d/ssl.conf.template 配置 HTTPS
docker compose restart nginx
```

### 更新部署

```bash
cd ~/projects/django-rag-website
bash scripts/deploy_production.sh
```

---

## 📝 常用命令

### 服务管理

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
docker compose logs -f web      # 只看 Django 日志
docker compose logs --tail=100  # 最近 100 行
```

### 数据库操作

```bash
# 备份数据库
bash scripts/backup.sh

# 恢复数据库
bash scripts/restore.sh /path/to/backup.sql.gz

# 进入数据库
docker compose exec db psql -U postgres rag_db

# 执行迁移
docker compose exec web python manage.py migrate

# 创建超级用户
docker compose exec web python manage.py createsuperuser
```

### 应用管理

```bash
# 进入 Django 容器
docker compose exec web bash

# Django Shell
docker compose exec web python manage.py shell

# 收集静态文件
docker compose exec web python manage.py collectstatic --noinput

# 清理 sessions
docker compose exec web python manage.py clearsessions
```

### 监控和诊断

```bash
# 运行健康检查
bash scripts/monitor.sh

# 查看资源使用
docker stats

# 查看容器详情
docker compose exec web ps aux
docker compose exec web df -h

# 查看 Django 错误
docker compose logs web | grep ERROR

# 测试网站可访问性
curl -I https://your-domain.com
```

---

## 🔧 配置文件位置

```
django-rag-website/
├── .env                          # 环境变量（不提交到 Git）
├── docker-compose.yml            # Docker 基础配置
├── docker-compose.prod.yml       # 生产环境覆盖配置
├── Dockerfile                    # Django 镜像定义
├── nginx/
│   ├── nginx.conf               # Nginx 主配置
│   └── conf.d/
│       ├── default.conf         # HTTP 配置
│       └── ssl.conf.template    # HTTPS 配置模板
└── scripts/
    ├── backup.sh                # 数据库备份
    ├── restore.sh               # 数据库恢复
    ├── monitor.sh               # 健康监控
    └── deploy_production.sh     # 一键部署
```

---

## 🔐 安全检查清单

### 部署前

- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` 已修改为随机值
- [ ] 数据库密码为强密码（16位+）
- [ ] `ALLOWED_HOSTS` 包含正确的域名
- [ ] `.env` 文件不在 Git 中
- [ ] 服务器防火墙已配置（80, 443, 22）
- [ ] SSH 使用密钥而非密码登录

### 部署后

- [ ] HTTPS 已启用
- [ ] SSL 证书自动续期已配置
- [ ] 数据库自动备份已配置
- [ ] 监控脚本已配置（crontab）
- [ ] 错误日志定期检查
- [ ] 修改默认管理员密码

---

## 📊 性能优化

### Gunicorn Workers 调整

编辑 `Dockerfile`，根据 CPU 核心数调整：

```dockerfile
# 公式: workers = (2 × CPU核心数) + 1
CMD ["gunicorn", "--workers=5", "--bind=0.0.0.0:8000", "config.wsgi:application"]
```

### 启用 Redis 缓存

1. 在 `docker-compose.yml` 添加 Redis 服务
2. 在 `requirements.txt` 添加 `django-redis`
3. 在 `settings.py` 配置缓存后端
4. 重新部署

### 数据库优化

```bash
# 进入数据库容器
docker compose exec db psql -U postgres rag_db

# 查看慢查询
SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;

# 分析表
ANALYZE;

# 重建索引
REINDEX DATABASE rag_db;
```

---

## 🆘 故障排除

### 容器无法启动

```bash
# 查看错误日志
docker compose logs web

# 检查配置
docker compose config

# 重新构建
docker compose down
docker compose build --no-cache
docker compose up -d
```

### 数据库连接失败

```bash
# 检查数据库状态
docker compose exec db pg_isready -U postgres

# 查看数据库日志
docker compose logs db

# 检查环境变量
docker compose exec web env | grep DB_
```

### 静态文件 404

```bash
# 重新收集静态文件
docker compose exec web python manage.py collectstatic --noinput --clear

# 检查 Nginx 配置
docker compose exec nginx nginx -t

# 检查文件权限
docker compose exec web ls -la /app/staticfiles/

# 重启 Nginx
docker compose restart nginx
```

### SSL 证书问题

```bash
# 检查证书状态
sudo certbot certificates

# 手动续期
sudo certbot renew

# 测试证书配置
docker compose exec nginx nginx -t

# 重新加载 Nginx
docker compose exec nginx nginx -s reload
```

### 内存不足

```bash
# 查看内存使用
free -h
docker stats

# 减少 Gunicorn workers
# 编辑 Dockerfile，减少 workers 数量

# 重启服务释放内存
docker compose restart
```

### 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理 Docker 资源
docker system prune -a

# 清理旧日志
find /var/log -name "*.log" -type f -size +100M -delete

# 清理旧备份
find ~/backups -name "*.sql.gz" -mtime +30 -delete
```

---

## 📅 定期维护任务

### 每日

- [ ] 检查服务运行状态
- [ ] 查看错误日志
- [ ] 验证备份完成

### 每周

- [ ] 审查访问日志
- [ ] 检查磁盘空间
- [ ] 更新系统包

### 每月

- [ ] 测试备份恢复
- [ ] 更新 Docker 镜像
- [ ] 检查 SSL 证书有效期
- [ ] 审查安全日志

### 每季度

- [ ] 灾难恢复演练
- [ ] 性能测试
- [ ] 安全审计
- [ ] 容量规划

---

## 🔗 有用的链接

- **完整部署指南**: [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)
- **Docker 文档**: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- **项目 README**: [README.md](README.md)
- **Docker 官方文档**: https://docs.docker.com/
- **Django 文档**: https://docs.djangoproject.com/
- **Let's Encrypt**: https://letsencrypt.org/

---

## 📞 紧急联系

如遇紧急问题：

1. 查看日志: `docker compose logs -f`
2. 运行监控: `bash scripts/monitor.sh`
3. 回滚到上一个版本
4. 从备份恢复数据库

**回滚命令**:

```bash
git checkout <previous-commit>
bash scripts/deploy_production.sh
```

**恢复数据库**:

```bash
bash scripts/restore.sh ~/backups/db_backup_<timestamp>.sql.gz
```
