# Django RAG 项目 - 部署文档索引

欢迎！这是 Django RAG 项目的部署文档中心。根据你的需求选择对应的文档。

---

## 🎯 我应该看哪个文档？

### 📘 快速开始

**我想快速了解项目并本地测试**  
👉 [README_DOCKER.md](README_DOCKER.md) - 3分钟快速部署到本地

**我需要常用命令参考**  
👉 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 命令速查表

---

### 🏭 生产部署

**我使用宝塔面板（推荐新手）**  
👉 [BAOTA_DEPLOYMENT.md](BAOTA_DEPLOYMENT.md) - 🔥 宝塔面板可视化部署（10分钟完成）

**我要使用命令行手动部署**  
👉 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 完整的生产部署指南  
👉 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 部署前检查清单

**我已经部署过，需要更新应用**  
👉 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 查看"更新部署"章节

---

### 🔧 技术细节

**我想深入了解 Docker 配置**  
👉 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Docker 详细文档

**我需要自定义配置**  
👉 查看 `.env.production` - 环境变量模板  
👉 查看 `docker-compose.prod.yml` - 生产配置

---

## 📚 文档列表

### 核心文档

| 文档 | 描述 | 适用场景 |
|------|------|---------|
| [README_DOCKER.md](README_DOCKER.md) | Docker 快速开始 | 本地测试、快速上手 |
| [BAOTA_DEPLOYMENT.md](BAOTA_DEPLOYMENT.md) | 🔥 宝塔面板部署 | 可视化部署、新手友好 |
| [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) | 生产部署完整指南 | 命令行手动部署 |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 快速参考手册 | 日常运维、故障排除 |
| [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) | Docker 详细文档 | 深入理解 Docker 配置 |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | 部署检查清单 | 部署前验证 |

### 配置文件

| 文件 | 描述 | 说明 |
|------|------|------|
| `.env.example` | 环境变量示例（本地） | 本地开发使用 |
| `.env.production` | 环境变量模板（生产） | 生产环境模板 |
| `docker-compose.yml` | Docker 基础配置 | 适用所有环境 |
| `docker-compose.prod.yml` | 生产环境覆盖配置 | 生产优化设置 |
| `Dockerfile` | Django 镜像定义 | 容器构建脚本 |

### 脚本工具

| 脚本 | 功能 | 使用方法 |
|------|------|---------|
| `deploy.sh` | 一键部署工具 | `./deploy.sh start` |
| `scripts/backup.sh` | 数据库备份 | `bash scripts/backup.sh` |
| `scripts/restore.sh` | 数据库恢复 | `bash scripts/restore.sh <file>` |
| `scripts/monitor.sh` | 健康监控 | `bash scripts/monitor.sh` |
| `scripts/deploy_production.sh` | 生产部署 | `bash scripts/deploy_production.sh` |

### Nginx 配置

| 文件 | 描述 |
|------|------|
| `nginx/nginx.conf` | Nginx 主配置 |
| `nginx/conf.d/default.conf` | HTTP 站点配置 |
| `nginx/conf.d/ssl.conf.template` | HTTPS 配置模板 |

---

## 🚀 典型部署流程

### 1️⃣ 本地测试（5 分钟）

```bash
# 克隆项目
git clone <repo-url>
cd django-rag-website

# 配置环境
cp .env.example .env
nano .env  # 修改必要配置

# 启动服务
docker compose up -d

# 访问 http://localhost:8080
```

📖 详细步骤：[README_DOCKER.md](README_DOCKER.md)

---

### 2️⃣ 生产部署（30 分钟）

```bash
# 1. 服务器准备
ssh root@your-server
# 安装 Docker，配置防火墙

# 2. 部署应用
git clone <repo-url>
cd django-rag-website
cp .env.production .env
nano .env  # 修改生产配置

# 3. 一键部署
bash scripts/deploy_production.sh

# 4. 配置域名和 HTTPS（可选）
# 添加 DNS 记录
# 获取 SSL 证书
# 更新 Nginx 配置
```

📖 详细步骤：[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md)  
✅ 检查清单：[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

---

### 2️⃣-B 宝塔面板部署（10 分钟，推荐新手）

```bash
# 1. 安装宝塔面板
wget -O install.sh https://download.bt.cn/install/install_6.0.sh && bash install.sh

# 2. 访问面板
浏览器打开: http://your-server-ip:8888

# 3. 在宝塔面板中：
- 安装 Docker（软件商店）
- 上传项目文件（文件管理器）
- 配置 .env 文件
- 启动 Docker 容器
- 添加网站（反向代理到 8080）
- 申请 SSL 证书（一键申请）

# 完成！访问 https://your-domain.com
```

📖 详细步骤：[BAOTA_DEPLOYMENT.md](BAOTA_DEPLOYMENT.md) 🔥 新手推荐

---

### 3️⃣ 日常维护

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f web

# 备份数据库
bash scripts/backup.sh

# 健康检查
bash scripts/monitor.sh

# 更新应用
git pull
bash scripts/deploy_production.sh
```

📖 命令参考：[QUICK_REFERENCE.md](QUICK_REFERENCE.md)

---

## 🔍 常见场景导航

### 我遇到了问题...

**容器无法启动**  
→ [QUICK_REFERENCE.md - 故障排除 - 容器无法启动](QUICK_REFERENCE.md#容器无法启动)

**数据库连接失败**  
→ [QUICK_REFERENCE.md - 故障排除 - 数据库连接失败](QUICK_REFERENCE.md#数据库连接失败)

**静态文件 404**  
→ [QUICK_REFERENCE.md - 故障排除 - 静态文件 404](QUICK_REFERENCE.md#静态文件-404)

**SSL 证书问题**  
→ [PRODUCTION_DEPLOYMENT.md - 步骤 5: 配置 HTTPS](PRODUCTION_DEPLOYMENT.md#步骤-5-配置-https)

**性能问题**  
→ [PRODUCTION_DEPLOYMENT.md - 步骤 6: 性能优化](PRODUCTION_DEPLOYMENT.md#步骤-6-性能优化)

---

### 我想要...

**配置自动备份**  
→ [PRODUCTION_DEPLOYMENT.md - 步骤 7: 监控和维护](PRODUCTION_DEPLOYMENT.md#步骤-7-监控和维护)

**启用 HTTPS**  
→ [PRODUCTION_DEPLOYMENT.md - 步骤 5: 配置 HTTPS](PRODUCTION_DEPLOYMENT.md#步骤-5-配置-https)

**添加 Redis 缓存**  
→ [PRODUCTION_DEPLOYMENT.md - 步骤 6: 性能优化](PRODUCTION_DEPLOYMENT.md#步骤-6-性能优化)

**设置监控告警**  
→ [scripts/monitor.sh](scripts/monitor.sh)

**恢复数据库**  
→ [scripts/restore.sh](scripts/restore.sh)

---

## 📊 文档结构图

```
部署文档
├── 快速开始
│   ├── README_DOCKER.md          # 3分钟快速部署
│   └── QUICK_REFERENCE.md        # 常用命令
│
├── 生产部署
│   ├── PRODUCTION_DEPLOYMENT.md  # 完整部署指南
│   ├── DEPLOYMENT_CHECKLIST.md   # 检查清单
│   └── docker-compose.prod.yml   # 生产配置
│
├── 技术细节
│   ├── DOCKER_DEPLOYMENT.md      # Docker 详解
│   ├── Dockerfile               # 镜像定义
│   └── nginx/                   # Web 服务器配置
│
└── 运维工具
    └── scripts/
        ├── backup.sh            # 数据库备份
        ├── restore.sh           # 数据库恢复
        ├── monitor.sh           # 健康监控
        └── deploy_production.sh # 一键部署
```

---

## 🎓 学习路径

### 新手路径

1. 阅读 [README_DOCKER.md](README_DOCKER.md) - 了解基础
2. 本地运行 Docker 环境 - 熟悉操作
3. 查看 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 学习常用命令
4. 阅读 [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - 了解部署要点

### 进阶路径

1. 阅读 [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 完整流程
2. 理解 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - 技术细节
3. 研究配置文件 - 自定义配置
4. 实践部署脚本 - 自动化运维

---

## 💡 提示和最佳实践

### ✅ 推荐做法

- 📝 **新手优先选择宝塔面板** - 可视化操作，降低出错率
- 🧪 **先在本地测试** - 确保配置正确
- 💾 **定期备份数据** - 宝塔面板可一键设置自动备份
- 📊 **持续监控** - 宝塔内置监控，或使用监控脚本
- 📚 **记录变更** - 维护部署日志

### ⚙️ 部署方式选择建议

**选择宝塔面板，如果你：**
- ✅ 是新手或对 Linux 命令不熟悉
- ✅ 需要快速部署（10分钟）
- ✅ 想要可视化管理界面
- ✅ 项目规模较小（个人或小团队）
- ✅ 预算有限（宝塔免费版已够用）

**选择命令行部署，如果你：**
- ✅ 熟悉 Linux 和 Docker
- ✅ 需要精细化控制
- ✅ 企业级大型项目
- ✅ 需要自动化 CI/CD
- ✅ 对性能有极致要求

### ⚠️ 常见错误

- ❌ 生产环境 `DEBUG=True` - 安全风险
- ❌ 使用默认密钥 - 容易被攻击
- ❌ 没有配置备份 - 数据丢失风险
- ❌ 忽略日志检查 - 错过早期问题
- ❌ 不测试恢复流程 - 紧急时无法恢复

---

## 📞 获取帮助

### 在线资源

- **项目仓库**: <your-repo-url>
- **问题反馈**: 在 GitHub 提交 Issue
- **文档更新**: 查看最新版本文档

### 社区支持

- **Django 文档**: https://docs.djangoproject.com/
- **Docker 文档**: https://docs.docker.com/
- **宝塔面板文档**: https://www.bt.cn/bbs/forum-39-1.html
- **Stack Overflow**: 搜索相关问题

### 紧急情况

**使用宝塔面板：**
1. 登录宝塔面板查看容器状态
2. 在线查看日志
3. 使用计划任务运行监控脚本

**使用命令行：**
1. 查看日志: `docker compose logs -f`
2. 运行监控: `bash scripts/monitor.sh`
3. 参考故障排除章节

---

## 🔄 文档更新

**最后更新**: 2025-10-13  
**版本**: 1.1（新增宝塔面板部署）  
**维护者**: 项目团队

如发现文档问题，请提交 Issue 或 PR。

---

## 🎉 开始你的部署之旅

选择适合你的文档，开始部署吧！

- � **新手推荐**：[BAOTA_DEPLOYMENT.md](BAOTA_DEPLOYMENT.md) - 宝塔面板可视化部署
- �🚀 **快速体验**：[README_DOCKER.md](README_DOCKER.md) - 本地测试
- 🏭 **命令行部署**：[PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - 完整手动部署
- ⚡ **命令速查**：[QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 日常运维

祝你部署顺利！💪
