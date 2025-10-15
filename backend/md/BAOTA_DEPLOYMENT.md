# 宝塔面板部署指南

使用宝塔面板部署 Django RAG 项目，可以大大简化配置过程，无需手动配置 Nginx、SSL 等。

---

## 🎯 宝塔面板的优势

相比传统部署方式，使用宝塔面板可以：

- ✅ **无需手动配置 Nginx** - 可视化配置，一键添加网站
- ✅ **自动申请 SSL 证书** - Let's Encrypt 一键申请和续期
- ✅ **图形化界面管理** - 无需记忆复杂命令
- ✅ **内置监控和日志** - 实时查看服务器状态
- ✅ **一键安装环境** - Docker、数据库等一键安装
- ✅ **定时任务管理** - 可视化设置备份任务
- ✅ **文件管理** - 在线编辑配置文件

---

## 📋 目录

- [前期准备](#前期准备)
- [安装宝塔面板](#安装宝塔面板)
- [方案一：Docker 部署（推荐）](#方案一docker-部署推荐)
- [方案二：传统部署](#方案二传统部署)
- [配置 SSL 证书](#配置-ssl-证书)
- [设置定时备份](#设置定时备份)
- [性能监控](#性能监控)
- [常见问题](#常见问题)

---

## 前期准备

### 1. 服务器要求

- **操作系统**: CentOS 7+/Ubuntu 18.04+/Debian 10+
- **配置**: 最低 2核CPU + 4GB内存
- **纯净系统**: 建议使用全新安装的系统

### 2. 准备工作

- 服务器公网 IP
- 域名（可选，建议）
- SSH 连接工具（PuTTY、Xshell、或终端）

---

## 安装宝塔面板

### 1. 连接服务器

```bash
ssh root@your-server-ip
```

### 2. 一键安装宝塔面板

#### CentOS 安装命令

```bash
yum install -y wget && wget -O install.sh https://download.bt.cn/install/install_6.0.sh && sh install.sh ed8484bec
```

#### Ubuntu/Debian 安装命令

```bash
wget -O install.sh https://download.bt.cn/install/install-ubuntu_6.0.sh && sudo bash install.sh ed8484bec
```

安装过程约 3-5 分钟，安装完成后会显示：

```
==================================================================
Congratulations! Installed successfully!
==================================================================
外网面板地址: http://your-server-ip:8888/xxxxxxxx
内网面板地址: http://10.0.0.1:8888/xxxxxxxx
username: xxxxxxx
password: xxxxxxx
If you cannot access the panel,
release the following panel port [8888] in the security group
==================================================================
```

**重要**：记录下面板地址、用户名和密码！

### 3. 访问宝塔面板

1. 在浏览器访问: `http://your-server-ip:8888/xxxxxxxx`
2. 输入用户名和密码登录
3. 首次登录会要求绑定宝塔账号（可跳过）

### 4. 安全设置（重要）

登录后立即：

1. 点击左侧 **面板设置**
2. 修改面板端口（建议改为 8888 以外的端口）
3. 修改用户名和密码
4. 绑定域名（推荐）
5. 开启面板 SSL（推荐）

---

## 方案一：Docker 部署（推荐）

使用宝塔面板 + Docker 是最简单的部署方式。

### 步骤 1: 安装 Docker

1. 登录宝塔面板
2. 点击左侧 **软件商店**
3. 搜索 "Docker"
4. 点击 **安装**（免费）
5. 等待安装完成（约 2-3 分钟）

或者命令行安装：

```bash
# 在 SSH 中执行
docker -v  # 检查是否已安装
# 如未安装，宝塔会自动安装
```

### 步骤 2: 上传项目文件

#### 方法一：使用宝塔文件管理器（推荐新手）

1. 点击左侧 **文件**
2. 进入 `/www/wwwroot/`
3. 点击 **新建目录**，创建 `django-rag`
4. 点击 **上传**，上传项目压缩包
5. 解压文件

#### 方法二：使用 Git（推荐）

1. 点击左侧 **软件商店**
2. 搜索并安装 **Git**
3. 在 SSH 或宝塔终端执行：

```bash
cd /www/wwwroot
git clone <your-repo-url> django-rag
cd django-rag
```

### 步骤 3: 配置环境变量

1. 在宝塔文件管理器中找到项目目录
2. 复制 `.env.example` 为 `.env`
3. 点击 `.env` 文件，选择 **编辑**
4. 修改以下配置：

```env
DEBUG=False
SECRET_KEY=<点击生成按钮生成随机密钥>
ALLOWED_HOSTS=your-domain.com,your-server-ip
DB_PASSWORD=<设置强密码>
DIFY_API_KEY=<你的Dify密钥>
DIFY_BASE_URL=<Dify服务地址>
```

**生成 SECRET_KEY**：

在宝塔终端执行：
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 步骤 4: 启动 Docker 容器

#### 方法一：使用宝塔 Docker 管理器

1. 点击左侧 **Docker**
2. 切换到 **容器** 标签
3. 点击 **添加容器**
4. 选择 **Docker Compose**
5. 选择项目目录中的 `docker-compose.yml`
6. 点击 **启动**

#### 方法二：使用命令行

在宝塔终端执行：

```bash
cd /www/wwwroot/django-rag

# 启动服务
docker compose up -d

# 查看状态
docker compose ps

# 查看日志
docker compose logs -f
```

### 步骤 5: 配置反向代理

1. 点击左侧 **网站**
2. 点击 **添加站点**
3. 填写信息：
   - 域名：`your-domain.com`
   - 根目录：`/www/wwwroot/django-rag`（任意，不重要）
   - PHP版本：**纯静态**
4. 点击 **提交**

5. 找到刚创建的网站，点击 **设置**
6. 点击 **反向代理**
7. 点击 **添加反向代理**
8. 填写：
   - 代理名称：`Django RAG`
   - 目标URL：`http://127.0.0.1:8080`
   - 发送域名：`$host`
9. 点击 **保存**

### 步骤 6: 申请 SSL 证书

1. 在网站设置中，点击 **SSL**
2. 选择 **Let's Encrypt**
3. 勾选你的域名
4. 点击 **申请**
5. 等待申请完成（约 30 秒）
6. 开启 **强制 HTTPS**

**完成！** 现在访问 `https://your-domain.com` 即可。

---

## 方案二：传统部署

如果不使用 Docker，可以用传统方式部署。

### 步骤 1: 安装运行环境

1. 点击左侧 **软件商店**
2. 依次安装以下软件：
   - **Nginx** 1.20+
   - **Python 项目管理器**
   - **PostgreSQL** 15
   - **Redis**（可选）

### 步骤 2: 创建数据库

1. 点击左侧 **数据库**
2. 点击 **添加数据库**
3. 填写：
   - 数据库名：`rag_db`
   - 用户名：`postgres`
   - 密码：`<设置强密码>`
4. 点击 **提交**

### 步骤 3: 配置 Python 项目

1. 点击左侧 **网站**
2. 点击 **Python项目**
3. 点击 **添加项目**
4. 填写：
   - 项目名称：`django-rag`
   - 路径：`/www/wwwroot/django-rag`
   - Python版本：`Python 3.11`
   - 框架：`Django`
   - 启动方式：`Gunicorn`
   - 端口：`8000`
5. 点击 **提交**

### 步骤 4: 安装依赖

在项目设置中，点击 **模块**，安装依赖：

```
Django==4.2
djangorestframework==3.14.0
psycopg2-binary==2.9.6
requests==2.31.0
gunicorn==21.2.0
Pillow==10.0.0
```

### 步骤 5: 配置环境变量

在项目设置中，点击 **配置文件**，添加环境变量。

### 步骤 6: 启动项目

点击 **启动项目**，宝塔会自动：
- 执行数据库迁移
- 收集静态文件
- 启动 Gunicorn

---

## 配置 SSL 证书

### 方法一：Let's Encrypt（免费，推荐）

1. 进入网站设置
2. 点击 **SSL**
3. 选择 **Let's Encrypt**
4. 点击 **申请**
5. 自动续期已启用（宝塔自动处理）

### 方法二：其他证书

1. 如有付费证书，点击 **其他证书**
2. 粘贴证书内容
3. 点击 **保存**

---

## 设置定时备份

### 数据库备份

1. 点击左侧 **计划任务**
2. 点击 **添加计划任务**
3. 选择任务类型：**备份数据库**
4. 任务名称：`Django数据库备份`
5. 执行周期：**每天** `03:00`
6. 选择数据库：`rag_db`
7. 备份保留：`7` 天
8. 点击 **添加**

### 网站文件备份

1. 添加计划任务
2. 选择任务类型：**备份网站**
3. 任务名称：`Django文件备份`
4. 执行周期：**每周** 星期日 `02:00`
5. 选择网站：`your-domain.com`
6. 备份保留：`4` 周
7. 点击 **添加**

### 健康检查脚本

1. 添加计划任务
2. 选择任务类型：**Shell脚本**
3. 脚本内容：

```bash
#!/bin/bash
cd /www/wwwroot/django-rag
bash scripts/monitor.sh --email admin@example.com
```

4. 执行周期：**每小时**
5. 点击 **添加**

---

## 性能监控

### 使用宝塔监控

1. 点击左侧 **监控**
2. 查看：
   - CPU 使用率
   - 内存使用率
   - 磁盘 I/O
   - 网络流量

### 查看服务日志

1. 点击左侧 **文件**
2. 进入 `/www/wwwlogs/`
3. 查看 Nginx 访问日志和错误日志

### Docker 容器监控

1. 点击左侧 **Docker**
2. 查看容器状态和资源使用
3. 点击容器名可查看详细信息和日志

---

## 常见问题

### 1. 无法访问面板

**问题**：浏览器无法打开宝塔面板

**解决**：
1. 检查服务器防火墙：
   ```bash
   # CentOS
   firewall-cmd --permanent --add-port=8888/tcp
   firewall-cmd --reload
   
   # Ubuntu
   ufw allow 8888
   ```

2. 检查云服务商安全组（阿里云、腾讯云等）：
   - 放行 8888 端口
   - 放行 80 和 443 端口

### 2. Docker 容器无法启动

**问题**：`docker compose up` 失败

**解决**：
1. 在宝塔面板查看 Docker 日志
2. 检查端口占用：
   ```bash
   netstat -tunlp | grep 8080
   ```
3. 查看容器日志：
   ```bash
   docker compose logs web
   ```

### 3. SSL 证书申请失败

**问题**：Let's Encrypt 证书申请失败

**解决**：
1. 确保域名已正确解析到服务器
2. 检查 80 端口是否开放
3. 暂时关闭防火墙重试：
   ```bash
   systemctl stop firewalld  # CentOS
   # 或
   ufw disable  # Ubuntu
   ```
4. 申请成功后重新开启防火墙

### 4. 静态文件 404

**问题**：CSS、JS 等静态文件无法加载

**解决**：
1. 在宝塔文件管理器中执行：
   ```bash
   cd /www/wwwroot/django-rag
   docker compose exec web python manage.py collectstatic --noinput
   ```

2. 在网站设置 -> 配置文件中添加：
   ```nginx
   location /static/ {
       alias /www/wwwroot/django-rag/staticfiles/;
   }
   
   location /media/ {
       alias /www/wwwroot/django-rag/media/;
   }
   ```

### 5. 数据库连接失败

**问题**：应用无法连接数据库

**解决**：
1. 检查 Docker 容器网络：
   ```bash
   docker network ls
   docker network inspect django-rag-website_django_network
   ```

2. 确认 `.env` 中的数据库配置正确

3. 测试数据库连接：
   ```bash
   docker compose exec db pg_isready -U postgres
   ```

---

## 宝塔面板 vs 传统部署对比

| 功能 | 传统部署 | 宝塔面板部署 |
|-----|---------|------------|
| Nginx 配置 | 手动编辑配置文件 | ✅ 可视化配置 |
| SSL 证书 | 手动申请和配置 | ✅ 一键申请 |
| 定时备份 | 编写 crontab | ✅ 图形界面设置 |
| 日志查看 | 命令行查看 | ✅ 在线查看 |
| 文件管理 | SSH 或 FTP | ✅ 在线文件管理器 |
| 性能监控 | 需要额外工具 | ✅ 内置监控 |
| 学习成本 | 较高 | ✅ 低 |
| 灵活性 | 高 | 中 |

---

## 推荐配置

### 基础配置（2核4G）

- Docker 部署
- PostgreSQL 数据库
- Let's Encrypt SSL
- 每日自动备份

### 进阶配置（4核8G+）

基础配置 +
- Redis 缓存
- 负载均衡
- CDN 加速
- 实时监控告警

---

## 快速命令参考

虽然使用宝塔面板，但有时仍需要命令行操作：

```bash
# 进入项目目录
cd /www/wwwroot/django-rag

# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f web

# 重启服务
docker compose restart

# 进入容器
docker compose exec web bash

# 执行 Django 命令
docker compose exec web python manage.py shell
docker compose exec web python manage.py migrate

# 备份数据库
bash scripts/backup.sh

# 查看系统资源
top
free -h
df -h
```

---

## 总结

使用宝塔面板部署的优势：

✅ **简单快速** - 10 分钟完成基础部署  
✅ **可视化管理** - 无需记忆复杂命令  
✅ **自动化维护** - 自动备份、SSL 续期  
✅ **降低门槛** - 适合新手和小团队  
✅ **功能完善** - 监控、日志、文件管理一应俱全  

**建议使用场景**：

- 👍 小型项目和个人项目
- 👍 团队技术能力有限
- 👍 需要快速上线
- 👍 预算有限（使用免费版）

**不建议使用场景**：

- ❌ 大型企业级项目（需要更精细的控制）
- ❌ 对性能有极致要求
- ❌ 需要深度定制化

---

## 下一步

1. ✅ 完成部署后，访问 `https://your-domain.com`
2. ✅ 登录管理后台修改默认密码
3. ✅ 设置定时备份任务
4. ✅ 配置监控和告警
5. ✅ 优化性能（如启用 Redis）

**获取帮助**：
- 宝塔官方论坛：https://www.bt.cn/bbs
- 宝塔文档：https://www.bt.cn/bbs/forum-39-1.html
- 项目文档：[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

祝你部署顺利！🎉
