# 前端部署 - 快速开始 ⚡

## 🎯 最简单的部署方式（3步完成）

假设您的**后端已经部署**在 `http://192.168.1.100:5000`

### 方法 A：一键部署脚本（推荐）✨

```bash
# 1. 进入前端目录
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend

# 2. 运行部署脚本
./deploy.sh

# 3. 按提示操作：
#    - 选择部署方式：1（Nginx）或 2（Docker）
#    - 输入后端地址：http://192.168.1.100:5000
#    - 等待自动构建和部署完成
```

**完成！** 访问 `http://your-server-ip` 即可使用系统。

---

### 方法 B：手动 Nginx 部署（5步）

```bash
# 1. 安装 Node.js 和 Nginx
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs nginx

# 2. 进入前端目录并构建
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend
npm config set registry https://registry.npmmirror.com
npm install
npm run build

# 3. 创建 Nginx 配置
sudo tee /etc/nginx/sites-available/ocr-frontend > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;
    root /home/h3c/workspace/IBoxTech-ocrchecker/frontend/dist;
    index index.html;
    
    location /api/ {
        proxy_pass http://192.168.1.100:5000;  # ← 改成您的后端地址
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_read_timeout 600s;
        client_max_body_size 100M;
    }
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF

# 4. 启用配置
sudo ln -sf /etc/nginx/sites-available/ocr-frontend /etc/nginx/sites-enabled/
sudo nginx -t

# 5. 启动 Nginx
sudo systemctl restart nginx
```

**完成！** 访问 `http://your-server-ip`

---

### 方法 C：Docker 部署（3步）

```bash
# 1. 修改后端地址
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend
sed -i 's|http://backend:5000|http://192.168.1.100:5000|g' nginx.conf

# 2. 构建并运行
docker build -t ocr-frontend .
docker run -d --name ocr-frontend --restart unless-stopped -p 80:80 ocr-frontend

# 3. 查看状态
docker ps | grep ocr-frontend
docker logs -f ocr-frontend
```

**完成！** 访问 `http://your-server-ip`

---

## 🔍 验证部署

```bash
# 1. 检查服务是否运行
curl http://localhost

# 2. 检查后端连接（在浏览器开发者工具 Console 中查看）
# 应该没有 CORS 错误或连接失败

# 3. 尝试登录系统
```

---

## 🆘 遇到问题？

### 问题：页面空白

```bash
# 检查构建文件是否存在
ls -lh dist/

# 如果不存在，重新构建
npm run build
```

### 问题：API 请求失败

```bash
# 检查后端是否可访问
curl http://192.168.1.100:5000/api/health

# 检查 Nginx 配置中的 proxy_pass
sudo nginx -T | grep proxy_pass

# 重启 Nginx
sudo systemctl restart nginx
```

### 问题：端口被占用

```bash
# 查看谁占用了 80 端口
sudo netstat -tulpn | grep :80

# 修改为其他端口（比如 8080）
# Nginx: 修改配置文件中的 listen 80; 改为 listen 8080;
# Docker: docker run -p 8080:80 ...
```

---

## 📞 需要详细文档？

查看完整部署指南：
- `docs/FRONTEND_DEPLOYMENT_GUIDE.md` - 详细的前端部署指南
- `docs/PRODUCTION_DEPLOYMENT_GUIDE.md` - 完整系统部署指南

---

## ✅ 部署检查清单

- [ ] Node.js 已安装（`node -v`）
- [ ] 依赖已安装（`ls node_modules`）
- [ ] 项目已构建（`ls dist/index.html`）
- [ ] 后端地址已配置
- [ ] Nginx 或 Docker 已安装
- [ ] 防火墙已开放 80 端口
- [ ] 浏览器可访问前端页面
- [ ] 可以正常登录系统

---

**部署时间：** 约 10-15 分钟  
**难度：** ⭐⭐ (简单)

