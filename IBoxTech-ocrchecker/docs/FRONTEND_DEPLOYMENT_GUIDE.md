# 前端部署指南

## 🎯 前端独立部署

本指南专门针对**只部署前端**的场景（后端已经在其他服务器运行）。

---

## 📋 准备工作

### 系统要求
- Linux 服务器（Ubuntu/CentOS）
- Node.js 18+ 或 Nginx（至少需要其中一个）
- 如果使用 Docker：需要安装 Docker

### 确认后端地址
- 后端 API 地址：`http://your-backend-server:5000`
- 确保前端服务器能访问后端

---

## 🚀 部署方式选择

### 方式 1：使用 Nginx 部署（推荐）

这是**最常用的生产环境部署方式**。

#### 步骤 1：安装 Node.js 和 npm

```bash
# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# CentOS/RHEL
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# 验证安装
node --version  # 应该是 v18.x 或更高
npm --version
```

#### 步骤 2：上传项目代码到服务器

```bash
# 方式 A：使用 Git 克隆
cd /opt
git clone <your-repository-url> IBoxTech-ocrchecker-frontend
cd IBoxTech-ocrchecker-frontend/frontend

# 方式 B：使用 scp 上传
# 在本地执行：
scp -r /local/path/IBoxTech-ocrchecker/frontend user@server:/opt/frontend
# 然后在服务器上：
cd /opt/frontend
```

#### 步骤 3：配置后端 API 地址

编辑 `vite.config.js`，修改后端 API 代理地址：

```bash
vi vite.config.js
```

找到 `proxy` 配置部分，修改为您的后端地址：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-server:5000',  // ← 修改为实际后端地址
      changeOrigin: true,
      secure: false
    }
  }
}
```

或者，如果您的 Nginx 会统一处理代理，可以跳过此步骤。

#### 步骤 4：安装依赖

```bash
# 使用国内镜像源加速
npm config set registry https://registry.npmmirror.com

# 安装依赖
npm install

# 如果遇到依赖冲突，使用：
npm install --legacy-peer-deps
```

#### 步骤 5：构建生产版本

```bash
# 构建前端项目
npm run build

# 构建完成后，dist 目录包含所有静态文件
ls -lh dist/
```

#### 步骤 6：安装和配置 Nginx

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y nginx

# CentOS/RHEL
sudo yum install -y nginx

# 启动 Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

#### 步骤 7：配置 Nginx

创建 Nginx 配置文件：

```bash
sudo vi /etc/nginx/sites-available/ocr-frontend
```

**配置内容：**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 修改为您的域名或服务器IP
    
    # 网站根目录（指向构建输出目录）
    root /opt/IBoxTech-ocrchecker-frontend/frontend/dist;
    index index.html;
    
    # 日志
    access_log /var/log/nginx/ocr_frontend_access.log;
    error_log /var/log/nginx/ocr_frontend_error.log;
    
    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript image/svg+xml;
    
    # 静态资源缓存（JS、CSS、图片等）
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        add_header Vary Accept-Encoding;
        access_log off;
    }
    
    # API请求代理到后端
    location /api/ {
        # 修改为您的后端服务器地址
        proxy_pass http://your-backend-server:5000;
        
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
    
    # 前端路由处理（Vue Router history 模式）
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma "no-cache";
        add_header Expires "0";
    }
    
    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    
    # 隐藏Nginx版本信息
    server_tokens off;
    
    # 错误页面
    error_page 404 /index.html;
    error_page 500 502 503 504 /50x.html;
    location = /50x.html {
        root /usr/share/nginx/html;
    }
}
```

**⚠️ 重要：请修改以下配置项**
- `server_name`: 您的域名或服务器IP
- `root`: 前端构建文件的实际路径
- `proxy_pass`: 后端服务器的实际地址

#### 步骤 8：启用配置并重启 Nginx

```bash
# Ubuntu/Debian - 启用站点配置
sudo ln -s /etc/nginx/sites-available/ocr-frontend /etc/nginx/sites-enabled/

# 测试配置文件
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
```

#### 步骤 9：配置防火墙

```bash
# Ubuntu - 使用 ufw
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# CentOS - 使用 firewalld
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

#### 步骤 10：验证部署

```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 访问前端
curl http://localhost

# 或在浏览器访问
# http://your-server-ip
```

✅ **部署完成！** 浏览器访问 `http://your-server-ip` 即可使用系统。

---

### 方式 2：使用 Docker 部署（简单快速）

如果您的服务器已安装 Docker，这是最简单的方式。

#### 步骤 1：准备项目文件

```bash
# 上传前端目录到服务器
cd /opt
# 假设您已经上传了 frontend 目录
cd /opt/IBoxTech-ocrchecker/frontend
```

#### 步骤 2：修改 Nginx 配置

编辑 `nginx.conf`，修改后端 API 代理地址：

```bash
vi nginx.conf
```

找到 `location /api/` 部分，修改：

```nginx
location /api/ {
    # 修改为您的后端服务器地址
    proxy_pass http://your-backend-server:5000;
    
    # ... 其他配置保持不变
}
```

#### 步骤 3：构建 Docker 镜像

```bash
# 构建前端镜像
docker build -t ocr-frontend:latest .

# 查看镜像
docker images | grep ocr-frontend
```

#### 步骤 4：运行容器

```bash
# 运行前端容器
docker run -d \
  --name ocr-frontend \
  --restart unless-stopped \
  -p 80:80 \
  ocr-frontend:latest

# 查看容器状态
docker ps | grep ocr-frontend

# 查看日志
docker logs -f ocr-frontend
```

#### 步骤 5：验证部署

```bash
# 检查容器状态
docker ps

# 访问前端
curl http://localhost

# 查看日志
docker logs ocr-frontend
```

✅ **Docker 部署完成！**

---

### 方式 3：直接使用 Node.js 运行（开发/测试用）

**⚠️ 不推荐用于生产环境**，但适合快速测试。

```bash
# 进入前端目录
cd /opt/IBoxTech-ocrchecker/frontend

# 安装依赖
npm install

# 修改 vite.config.js 中的后端地址（见方式1的步骤3）
vi vite.config.js

# 运行开发服务器（不推荐生产环境）
npm run dev -- --host 0.0.0.0 --port 80

# 或者使用 preview 模式（需要先构建）
npm run build
npm run preview -- --host 0.0.0.0 --port 80
```

---

## 🔧 配置 HTTPS（可选但推荐）

### 使用 Let's Encrypt 免费 SSL 证书

#### 步骤 1：安装 Certbot

```bash
# Ubuntu/Debian
sudo apt-get install -y certbot python3-certbot-nginx

# CentOS/RHEL
sudo yum install -y certbot python3-certbot-nginx
```

#### 步骤 2：获取 SSL 证书

```bash
# 自动配置 Nginx 和获取证书
sudo certbot --nginx -d your-domain.com

# 或者手动获取证书
sudo certbot certonly --standalone -d your-domain.com
```

#### 步骤 3：配置自动续期

```bash
# 测试续期
sudo certbot renew --dry-run

# Certbot 会自动添加续期任务到 crontab
# 查看：
sudo crontab -l | grep certbot
```

#### 步骤 4：Nginx HTTPS 配置（如果手动获取证书）

```bash
sudo vi /etc/nginx/sites-available/ocr-frontend
```

添加 HTTPS 配置：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

# HTTPS 主服务
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers off;
    
    # 其他配置同上...
    root /opt/IBoxTech-ocrchecker-frontend/frontend/dist;
    
    # ... 其余配置
}
```

```bash
# 重启 Nginx
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📝 快速部署命令（一键复制执行）

### 使用 Nginx 部署（推荐）

```bash
# 1. 安装 Node.js 和 Nginx
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs nginx

# 2. 进入前端目录（假设项目在 /opt）
cd /opt/IBoxTech-ocrchecker/frontend

# 3. 安装依赖
npm config set registry https://registry.npmmirror.com
npm install

# 4. 构建项目
npm run build

# 5. 配置 Nginx（需要手动编辑配置文件，见上文）
sudo vi /etc/nginx/sites-available/ocr-frontend
# 复制上面的 Nginx 配置，修改 server_name 和 proxy_pass

# 6. 启用配置
sudo ln -s /etc/nginx/sites-available/ocr-frontend /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 7. 配置防火墙
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 8. 访问测试
curl http://localhost
```

### 使用 Docker 部署

```bash
# 1. 进入前端目录
cd /opt/IBoxTech-ocrchecker/frontend

# 2. 修改 nginx.conf 中的后端地址
vi nginx.conf
# 修改 proxy_pass http://your-backend-server:5000;

# 3. 构建镜像
docker build -t ocr-frontend:latest .

# 4. 运行容器
docker run -d \
  --name ocr-frontend \
  --restart unless-stopped \
  -p 80:80 \
  ocr-frontend:latest

# 5. 查看状态
docker ps | grep ocr-frontend
docker logs -f ocr-frontend
```

---

## 🔄 更新前端

### Nginx 部署更新

```bash
# 1. 进入前端目录
cd /opt/IBoxTech-ocrchecker/frontend

# 2. 拉取最新代码（如使用 Git）
git pull origin main

# 3. 重新安装依赖（如有 package.json 变更）
npm install

# 4. 重新构建
npm run build

# 5. Nginx 会自动使用新的构建文件，无需重启
# 但如果想清除浏览器缓存，可以重启 Nginx
sudo systemctl restart nginx
```

### Docker 部署更新

```bash
# 1. 进入前端目录
cd /opt/IBoxTech-ocrchecker/frontend

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建镜像
docker build -t ocr-frontend:latest .

# 4. 停止并删除旧容器
docker stop ocr-frontend
docker rm ocr-frontend

# 5. 启动新容器
docker run -d \
  --name ocr-frontend \
  --restart unless-stopped \
  -p 80:80 \
  ocr-frontend:latest

# 6. 清理旧镜像
docker image prune -f
```

---

## 🛠️ 配置说明

### 关键配置文件

#### 1. `vite.config.js` - 开发环境后端代理

仅在开发模式（`npm run dev`）时生效：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://your-backend-server:5000',  // 后端地址
      changeOrigin: true,
      secure: false
    }
  }
}
```

#### 2. `nginx.conf` - Docker 部署的 Nginx 配置

用于 Docker 容器内的 Nginx：

```nginx
location /api/ {
    proxy_pass http://your-backend-server:5000;  # 后端地址
    # ... 其他配置
}
```

#### 3. `/etc/nginx/sites-available/ocr-frontend` - 系统 Nginx 配置

用于直接在服务器上安装的 Nginx：

```nginx
root /opt/IBoxTech-ocrchecker-frontend/frontend/dist;  # 构建输出目录

location /api/ {
    proxy_pass http://your-backend-server:5000;  # 后端地址
    # ... 其他配置
}
```

### 环境变量配置（可选）

如果需要在构建时注入环境变量，创建 `.env.production` 文件：

```bash
vi .env.production
```

```bash
# 后端 API 地址（如果前端代码中使用）
VITE_API_BASE_URL=http://your-backend-server:5000/api

# 其他配置
VITE_APP_TITLE=OCR数据识别系统
VITE_APP_VERSION=1.0.0
```

然后在代码中使用：
```javascript
const apiBaseUrl = import.meta.env.VITE_API_BASE_URL
```

---

## ✅ 验证部署

### 1. 检查构建文件

```bash
# 确认 dist 目录存在且包含文件
ls -lh /opt/IBoxTech-ocrchecker/frontend/dist/

# 应该包含：
# - index.html
# - assets/ (JS、CSS文件)
# - favicon.ico
```

### 2. 检查 Nginx 配置

```bash
# 测试配置文件语法
sudo nginx -t

# 应该显示：
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 3. 检查服务状态

```bash
# Nginx 状态
sudo systemctl status nginx

# 端口监听
sudo netstat -tulpn | grep :80
```

### 4. 浏览器访问测试

访问以下地址：
- `http://your-server-ip` - 应该能看到登录页面
- `http://your-server-ip/api/health` - 应该返回后端健康状态（如果配置了代理）

### 5. 功能测试

1. 打开浏览器开发者工具（F12）
2. 检查 Console 是否有错误
3. 检查 Network 标签页，确认 API 请求正确发送到后端
4. 尝试登录系统
5. 上传测试文件

---

## 🐛 常见问题排查

### 问题 1：页面无法访问

```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 检查端口是否被占用
sudo netstat -tulpn | grep :80

# 重启 Nginx
sudo systemctl restart nginx
```

### 问题 2：页面空白或 404

```bash
# 检查 dist 目录是否存在
ls -lh /opt/IBoxTech-ocrchecker/frontend/dist/

# 如果不存在，重新构建
cd /opt/IBoxTech-ocrchecker/frontend
npm run build

# 检查 Nginx root 配置是否正确
sudo nginx -T | grep root
```

### 问题 3：API 请求失败（CORS 错误）

**浏览器 Console 显示：**
```
Access to XMLHttpRequest at 'http://backend:5000/api/...' has been blocked by CORS policy
```

**解决方法：**

确保 Nginx 正确代理了 `/api/` 请求：

```bash
# 检查 Nginx 配置
sudo nginx -T | grep -A 10 "location /api"

# 应该包含 proxy_pass 配置
```

或者确保后端启用了 CORS（后端应该已配置）：

```python
# backend/app/__init__.py
CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### 问题 4：静态资源 404

**浏览器 Console 显示：**
```
GET http://your-domain.com/assets/index-abc123.js net::ERR_FILE_NOT_FOUND
```

**解决方法：**

检查 `vite.config.js` 中的 `base` 配置：

```javascript
export default defineConfig({
  base: '/',  // 确保是 '/' 而不是其他路径
  // ...
})
```

重新构建：
```bash
npm run build
```

### 问题 5：路由刷新后 404

**症状：** 直接访问 `http://domain.com/login` 返回 404

**解决方法：**

确保 Nginx 配置了前端路由处理：

```nginx
location / {
    try_files $uri $uri/ /index.html;  # ← 这行很重要
}
```

### 问题 6：上传大文件失败

**浏览器显示：** 413 Request Entity Too Large

**解决方法：**

修改 Nginx 配置，增加上传大小限制：

```nginx
location /api/ {
    client_max_body_size 100M;  # ← 添加这行
    proxy_pass http://your-backend-server:5000;
    # ...
}
```

重启 Nginx：
```bash
sudo systemctl restart nginx
```

---

## 📊 性能优化建议

### 1. 启用 Gzip 压缩

Nginx 配置中已包含 Gzip 压缩配置，确保已启用：

```nginx
gzip on;
gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
```

### 2. 启用浏览器缓存

静态资源设置长期缓存：

```nginx
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 使用 CDN（可选）

将静态资源上传到 CDN，修改 `vite.config.js`：

```javascript
build: {
  rollupOptions: {
    output: {
      assetFileNames: 'assets/[name]-[hash].[ext]',
      // 可以配置上传到 CDN 的逻辑
    }
  }
}
```

---

## 📁 目录结构说明

```
frontend/
├── dist/                    # 构建输出目录（部署这个）
│   ├── index.html
│   ├── assets/
│   │   ├── index-[hash].js
│   │   ├── index-[hash].css
│   │   └── ...
│   └── favicon.ico
├── src/                     # 源代码
├── public/                  # 公共资源
├── nginx.conf              # Docker Nginx 配置
├── Dockerfile              # Docker 构建文件
├── vite.config.js          # Vite 配置
├── package.json            # 依赖配置
└── package-lock.json
```

**部署时只需要 `dist/` 目录的内容！**

---

## 🚀 一键部署脚本

创建一个简单的部署脚本：

```bash
vi deploy-frontend.sh
```

```bash
#!/bin/bash
# 前端一键部署脚本

set -e

FRONTEND_DIR="/opt/IBoxTech-ocrchecker/frontend"
BACKEND_API="http://your-backend-server:5000"  # ← 修改为实际后端地址

echo "========================================="
echo "OCR 前端部署脚本"
echo "========================================="

# 1. 进入前端目录
echo "进入前端目录..."
cd $FRONTEND_DIR

# 2. 安装依赖
echo "安装依赖..."
npm config set registry https://registry.npmmirror.com
npm install

# 3. 构建项目
echo "构建项目..."
npm run build

# 4. 检查构建结果
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    echo "✅ 构建成功"
    echo "构建文件大小: $(du -sh dist/)"
else
    echo "❌ 构建失败"
    exit 1
fi

# 5. 配置 Nginx（如果不存在）
if [ ! -f "/etc/nginx/sites-available/ocr-frontend" ]; then
    echo "创建 Nginx 配置..."
    sudo tee /etc/nginx/sites-available/ocr-frontend > /dev/null <<EOF
server {
    listen 80;
    server_name _;
    
    root $FRONTEND_DIR/dist;
    index index.html;
    
    access_log /var/log/nginx/ocr_frontend_access.log;
    error_log /var/log/nginx/ocr_frontend_error.log;
    
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
    
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /api/ {
        proxy_pass $BACKEND_API;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 600s;
        client_max_body_size 100M;
    }
    
    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
    
    sudo ln -s /etc/nginx/sites-available/ocr-frontend /etc/nginx/sites-enabled/
fi

# 6. 重启 Nginx
echo "重启 Nginx..."
sudo nginx -t
sudo systemctl restart nginx

# 7. 完成
echo ""
echo "========================================="
echo "✅ 前端部署完成！"
echo "========================================="
echo "访问地址: http://$(hostname -I | awk '{print $1}')"
echo "后端地址: $BACKEND_API"
echo ""
echo "常用命令："
echo "  查看日志: sudo tail -f /var/log/nginx/ocr_frontend_access.log"
echo "  重启服务: sudo systemctl restart nginx"
echo "========================================="
```

```bash
# 设置执行权限
chmod +x deploy-frontend.sh

# 运行部署
sudo ./deploy-frontend.sh
```

---

## 📋 部署检查清单

部署完成后，请逐一检查：

- [ ] Node.js 已安装（`node --version`）
- [ ] npm 依赖已安装（`npm list` 无错误）
- [ ] 前端项目已构建（`dist/` 目录存在）
- [ ] Nginx 已安装并运行（`systemctl status nginx`）
- [ ] Nginx 配置正确（`nginx -t` 通过）
- [ ] 后端 API 地址配置正确
- [ ] 防火墙已开放 80/443 端口
- [ ] 浏览器可以访问前端页面
- [ ] 浏览器 Console 无错误
- [ ] API 请求能正确发送到后端
- [ ] 登录功能正常
- [ ] 文件上传功能正常
- [ ] PDF 预览功能正常
- [ ] OCR 识别功能正常

---

## 🆘 故障处理

### 完全重新部署

如果遇到问题，可以完全重新部署：

```bash
# 1. 清理旧文件
cd /opt/IBoxTech-ocrchecker/frontend
rm -rf dist node_modules

# 2. 重新安装和构建
npm install
npm run build

# 3. 重启 Nginx
sudo systemctl restart nginx

# 4. 清除浏览器缓存
# 在浏览器中按 Ctrl+Shift+R 强制刷新
```

### 回滚到旧版本

如果使用 Git：

```bash
# 查看历史版本
git log --oneline

# 回滚到指定版本
git checkout <commit-hash>

# 重新构建
npm install
npm run build

# 重启服务
sudo systemctl restart nginx
```

---

## 📞 快速帮助

### 查看 Nginx 日志

```bash
# 访问日志
sudo tail -f /var/log/nginx/ocr_frontend_access.log

# 错误日志
sudo tail -f /var/log/nginx/ocr_frontend_error.log
```

### 查看 Docker 日志（如使用 Docker）

```bash
# 实时日志
docker logs -f ocr-frontend

# 最近 100 行日志
docker logs --tail=100 ocr-frontend
```

### 重启服务

```bash
# Nginx 部署
sudo systemctl restart nginx

# Docker 部署
docker restart ocr-frontend
```

---

## 🎯 推荐部署方式总结

| 场景 | 推荐方式 | 优点 |
|------|---------|------|
| 生产环境 | Nginx + 构建文件 | 性能最好，稳定性高 |
| 快速部署 | Docker | 部署简单，环境一致 |
| 开发测试 | npm run dev | 热更新，调试方便 |

**生产环境强烈推荐使用 Nginx 方式！**

---

**更新时间：** 2025-11-25  
**适用版本：** 1.0.0

