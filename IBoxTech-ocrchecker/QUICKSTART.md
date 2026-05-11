# 🚀 快速启动指南

本指南将帮助您在5分钟内快速搭建并运行OCR数据识别系统。

## 📋 准备工作

### 系统要求
- 操作系统：Linux/macOS/Windows 10+
- Python 3.8+
- Node.js 16+
- 至少4GB内存
- 至少20GB可用磁盘空间

### 依赖服务
在开始之前，请确保以下服务已安装并运行：

#### MySQL 8.0+
```bash
# Ubuntu/Debian
sudo apt-get install mysql-server

# macOS
brew install mysql

# 启动服务
sudo systemctl start mysql   # Linux
brew services start mysql    # macOS
```

#### Redis (可选，推荐)
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# 启动服务
sudo systemctl start redis   # Linux
brew services start redis    # macOS
```

## ⚡ 一键安装

### 步骤1：下载项目

```bash
git clone https://github.com/your-org/IBoxTech-data.git
cd IBoxTech-data
```

### 步骤2：运行安装脚本

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

安装脚本会自动：
- ✅ 检查系统依赖
- ✅ 创建Python虚拟环境
- ✅ 安装后端Python依赖
- ✅ 安装前端Node.js依赖
- ✅ 创建配置文件模板
- ✅ 初始化数据库

### 步骤3：配置数据库

编辑后端配置文件：
```bash
cp backend/env_example.txt backend/.env
nano backend/.env  # 或使用其他编辑器
```

修改数据库配置：
```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_DB=ocr_system
```

### 步骤4：初始化数据库

```bash
# 登录MySQL创建数据库
mysql -u root -p
```

```sql
CREATE DATABASE ocr_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;
```

```bash
# 运行数据库初始化脚本
cd backend
source venv/bin/activate
python migrations/init_database.py
```

### 步骤5：启动服务

打开两个终端窗口：

**终端1 - 启动后端服务：**
```bash
./scripts/start-backend.sh
```
等待看到：`* Running on http://0.0.0.0:5000`

**终端2 - 启动前端服务：**
```bash
./scripts/start-frontend.sh
```
等待看到：`Local: http://localhost:5173/`

## 🌐 访问系统

### 打开浏览器
访问：http://localhost:5173

### 使用默认账户登录
- **管理员**: 用户名 `admin`，密码 `admin123`
- **普通用户**: 用户名 `testuser`，密码 `test123`

## 🎯 快速体验

### 1. 上传文件
1. 登录后点击"文件上传"
2. 拖拽PDF文件到上传区域
3. 点击"开始上传"

### 2. OCR识别
1. 在文件管理页面找到刚上传的文件
2. 点击"开始处理"按钮
3. 等待OCR识别完成

### 3. 数据核对
1. 识别完成后，点击"核对"按钮
2. 在左侧编辑识别结果
3. 右侧预览PDF文档
4. 点击"保存修改"

## 🐳 Docker快速部署

如果您偏好使用Docker（需要先安装Docker和Docker Compose）：

```bash
# 1. 克隆项目
git clone https://github.com/your-org/IBoxTech-data.git
cd IBoxTech-data

# 2. 一键启动所有服务
docker-compose up -d

# 3. 等待服务启动完成（约1-2分钟）
docker-compose ps

# 4. 访问系统
# 前端: http://localhost:8080
# 后端: http://localhost:5000
```

## 🔧 故障排除

### 常见问题和解决方案

#### 1. 数据库连接失败
```bash
# 检查MySQL是否运行
systemctl status mysql

# 检查端口是否被占用
netstat -tulpn | grep :3306

# 测试数据库连接
mysql -u root -p -e "SELECT 1;"
```

#### 2. 端口被占用
```bash
# 查看端口占用情况
lsof -i :5000  # 后端端口
lsof -i :5173  # 前端端口

# 杀死占用进程
kill -9 <PID>
```

#### 3. Python虚拟环境问题
```bash
# 重新创建虚拟环境
rm -rf backend/venv
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Node.js依赖问题
```bash
# 清除缓存重新安装
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### 5. OCR识别失败
```bash
# 检查PaddleOCR模型是否正确下载
ls -la backend/models/

# 检查日志文件
tail -f backend/logs/app.log
```

## ⚙️ 高级配置

### 启用GPU加速（可选）

如果您有NVIDIA GPU并已安装CUDA：

```bash
# 编辑配置文件
nano backend/.env
```

```bash
# 设置GPU加速
OCR_USE_GPU=true
```

### 配置MinIO对象存储

系统默认使用本地文件存储。如果需要使用MinIO：

1. 安装MinIO服务
2. 在配置文件中设置MinIO连接信息
3. 重启后端服务

### 性能调优

#### 数据库优化
```sql
# 在MySQL中执行
SET GLOBAL innodb_buffer_pool_size = 1G;
SET GLOBAL query_cache_size = 256M;
```

#### Redis缓存配置
```bash
# 编辑redis配置
sudo nano /etc/redis/redis.conf

# 设置内存限制
maxmemory 1gb
maxmemory-policy allkeys-lru
```

## 📚 下一步

现在您已经成功启动了OCR数据识别系统！建议您：

1. 📖 阅读 [用户手册](USER_MANUAL.md) 了解详细功能
2. 🔧 查看 [INSTALLATION.md](INSTALLATION.md) 进行生产环境部署
3. 🚀 参考 [DEPLOYMENT.md](DEPLOYMENT.md) 进行性能优化
4. 🐛 如遇问题，请查看 [Issues](https://github.com/your-org/IBoxTech-data/issues)

## 📞 获取帮助

- 📧 技术支持：support@iboxtech.com
- 💬 QQ群：123456789
- 📝 在线文档：https://docs.iboxtech.com
- 🐛 问题反馈：https://github.com/your-org/IBoxTech-data/issues

---

✨ **恭喜！** 您已经成功启动了OCR数据识别系统，开始您的智能文档处理之旅吧！
