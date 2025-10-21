# AI RAG 系统快速配置说明

## 首次使用步骤

### 1. 安装依赖
```bash
# 运行依赖安装脚本
install_deps.bat

# 或手动安装：
cd backend
pip install -r requirements.txt
python manage.py migrate

cd ../frontend  
npm install
```

### 2. 启动开发服务器
```bash
# 一键启动（推荐）
start_dev.bat

# 或手动启动：
# 终端1 - 后端
cd backend
python manage.py runserver

# 终端2 - 前端  
cd frontend
npm run dev
```

### 3. 访问系统
- 前端开发: http://localhost:3000/
- 后端API: http://127.0.0.1:8000/
- 管理后台: http://127.0.0.1:8000/admin/

## 主要功能

✅ **智能聊天** - AI对话问答  
✅ **文档管理** - 上传、分类、搜索文档  
✅ **用户系统** - 注册、登录、会话管理  
✅ **多模型支持** - 支持多种AI模型切换  

## 环境要求

- Python 3.8+
- Node.js 16+ 
- 现代浏览器 (Chrome/Firefox/Safari/Edge)

## 常用命令

```bash
# 创建管理员
cd backend
python manage.py createsuperuser

# 重置数据库
python manage.py flush
python manage.py migrate

# 前端构建
cd frontend
npm run build

# 查看API文档
# 访问: http://127.0.0.1:8000/api/
```

## 故障排除

**端口占用**: 修改端口号或关闭占用进程  
**依赖错误**: 重新运行 install_deps.bat  
**静态文件**: 确保运行了 npm run build  
**数据库**: 删除db.sqlite3后重新migrate  

---

🚀 **开始使用**: 运行 `start_dev.bat` 一键启动！