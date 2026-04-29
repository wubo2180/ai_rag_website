# Nginx 重装指南（宝塔环境）

## 🎯 您的情况分析

- ✅ 服务器安装了宝塔面板
- ✅ Nginx 是通过宝塔安装的
- ⚠️ 当前 Nginx 状态：`inactive (dead)`
- ⚠️ 有 Docker Nginx 在运行（不能关闭）

---

## 🚀 推荐方案：不重装，直接用 Docker 部署

### 为什么不推荐重装？

1. ❌ 重装宝塔 Nginx 可能影响宝塔面板的其他功能
2. ❌ 宝塔 Nginx 和系统 Nginx 可能冲突
3. ❌ 配置复杂，容易出错
4. ✅ **Docker 部署更简单、更稳定、更易管理**

### Docker 部署步骤（5 分钟完成）

```bash
# 1. 进入前端目录
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend

# 2. 检查并修改后端地址
cat nginx.conf | grep proxy_pass

# 如果需要修改（请替换为您的实际后端地址）
sed -i 's|proxy_pass http://backend:5000|proxy_pass http://127.0.0.1:5001|g' nginx.conf

# 3. 构建 Docker 镜像
docker build -t ocr-frontend:latest .

# 4. 停止旧容器（如果存在）
docker stop ocr-frontend 2>/dev/null || true
docker rm ocr-frontend 2>/dev/null || true

# 5. 运行新容器
docker run -d \
  --name ocr-frontend \
  --restart unless-stopped \
  -p 8080:80 \
  ocr-frontend:latest

# 6. 验证部署
echo "容器状态："
docker ps | grep ocr-frontend

echo ""
echo "容器日志（按 Ctrl+C 退出）："
docker logs -f ocr-frontend
```

**完成！** 访问 `http://your-server-ip:8080`

---

## 🔧 如果坚持要重装 Nginx

### 方法 A：通过宝塔面板重装（最安全）

#### 步骤 1：访问宝塔面板

```bash
# 查看宝塔面板访问地址和端口
bt default
```

访问显示的地址，例如：`http://your-server-ip:8888/xxx`

#### 步骤 2：在面板中操作

1. 登录宝塔面板
2. 左侧菜单 → "软件商店"
3. 搜索 "Nginx"
4. 点击 "设置" 按钮
5. 点击 "卸载" 按钮
6. 等待卸载完成（1-2分钟）
7. 点击 "安装" 按钮
8. 选择版本（推荐 1.22）
9. 点击 "立即安装"
10. 等待安装完成（3-5分钟）

#### 步骤 3：验证

```bash
# 查看 Nginx 状态
sudo systemctl status nginx

# 应该显示 active (running)
```

---

### 方法 B：命令行重装宝塔 Nginx

```bash
# 1. 停止 Nginx 服务
sudo /etc/init.d/nginx stop

# 2. 备份现有配置（重要！）
sudo mkdir -p /tmp/nginx_config_backup
sudo cp -r /www/server/panel/vhost/nginx /tmp/nginx_config_backup/ 2>/dev/null || true
sudo cp -r /www/server/nginx/conf /tmp/nginx_config_backup/ 2>/dev/null || true

# 3. 卸载 Nginx
sudo rm -rf /www/server/nginx
sudo rm -f /etc/init.d/nginx
sudo rm -f /usr/sbin/nginx
sudo rm -f /usr/bin/nginx

# 4. 通过宝塔重新安装
# 方式 1：使用宝塔命令
bt install nginx

# 方式 2：通过宝塔面板 Web 界面安装（推荐）
bt default  # 查看面板地址，然后在浏览器中安装
```

---

### 方法 C：完全卸载宝塔 Nginx，安装系统 Nginx

**⚠️ 警告：** 这会影响宝塔面板的网站管理功能！

```bash
# 1. 备份配置
sudo mkdir -p /tmp/nginx_backup
sudo cp -r /www/server/panel/vhost/nginx /tmp/nginx_backup/ 2>/dev/null || true

# 2. 停止并卸载宝塔 Nginx
sudo /etc/init.d/nginx stop
sudo rm -rf /www/server/nginx
sudo rm -f /etc/init.d/nginx

# 3. 清理残留
sudo apt-get remove --purge nginx nginx-common nginx-full -y 2>/dev/null || true
sudo apt-get autoremove -y

# 4. 安装系统 Nginx
sudo apt-get update
sudo apt-get install -y nginx

# 5. 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# 6. 验证
sudo systemctl status nginx
nginx -v
```

---

## 📋 部署配置文件到宝塔

### 完整操作步骤

```bash
# 1. 创建宝塔虚拟主机配置目录
sudo mkdir -p /www/server/panel/vhost/nginx

# 2. 创建日志目录
sudo mkdir -p /www/wwwlogs

# 3. 复制配置文件
sudo cp /home/h3c/workspace/IBoxTech-ocrchecker/deployment/nginx/ocr-frontend-bt.conf \
        /www/server/panel/vhost/nginx/ocr-frontend.conf

# 4. 修改后端地址（如果需要）
sudo vi /www/server/panel/vhost/nginx/ocr-frontend.conf
# 找到 proxy_pass http://127.0.0.1:5001
# 改为您的实际后端地址

# 5. 构建前端项目
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend
npm install
npm run build

# 6. 验证构建结果
ls -lh dist/

# 7. 测试 Nginx 配置
sudo nginx -t

# 8. 重启 Nginx
sudo /etc/init.d/nginx restart
# 或
sudo systemctl restart nginx

# 9. 查看状态
sudo systemctl status nginx

# 10. 测试访问
curl http://localhost:8080
```

---

## 🎯 最简单的方案（推荐）

我给您准备了配置文件，**请按以下步骤操作**：

### 第 1 步：构建前端

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend
npm config set registry https://registry.npmmirror.com
npm install
npm run build
```

### 第 2 步：部署配置文件

```bash
# 创建目录
sudo mkdir -p /www/server/panel/vhost/nginx
sudo mkdir -p /www/wwwlogs

# 复制配置文件
sudo cp /home/h3c/workspace/IBoxTech-ocrchecker/deployment/nginx/ocr-frontend-bt.conf \
        /www/server/panel/vhost/nginx/ocr-frontend.conf

# 修改后端地址（请根据实际情况修改）
sudo sed -i 's|http://127.0.0.1:5001|http://YOUR_BACKEND_IP:5001|g' \
        /www/server/panel/vhost/nginx/ocr-frontend.conf
```

### 第 3 步：启动 Nginx

```bash
# 测试配置
sudo nginx -t

# 如果配置正确，启动 Nginx
sudo systemctl start nginx

# 查看状态
sudo systemctl status nginx
```

### 第 4 步：验证

```bash
# 检查 8080 端口是否监听
sudo netstat -tulpn | grep :8080

# 测试访问
curl http://localhost:8080

# 如果返回 HTML 内容，说明成功！
```

---

## 📝 快速复制命令（一键执行）

**请先告诉我您的后端地址**，然后我可以生成完整的一键部署命令。

例如，如果您的后端地址是 `http://127.0.0.1:5001`：

```bash
# 后端地址
BACKEND_URL="http://127.0.0.1:5001"

# 一键部署
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend && \
npm install && \
npm run build && \
sudo mkdir -p /www/server/panel/vhost/nginx /www/wwwlogs && \
sudo cp /home/h3c/workspace/IBoxTech-ocrchecker/deployment/nginx/ocr-frontend-bt.conf \
        /www/server/panel/vhost/nginx/ocr-frontend.conf && \
sudo sed -i "s|http://127.0.0.1:5001|$BACKEND_URL|g" \
        /www/server/panel/vhost/nginx/ocr-frontend.conf && \
sudo nginx -t && \
sudo systemctl start nginx && \
sudo systemctl status nginx
```

---

## ❓ 需要我帮您

请告诉我：

1. **您的后端服务地址是什么？**
   - `http://127.0.0.1:5001`（本机）
   - 还是其他地址？

2. **您想用哪个端口访问前端？**
   - `8080`（默认）
   - 还是其他端口？

告诉我这两个信息，我会给您生成**可以直接复制执行的完整命令**！🚀
