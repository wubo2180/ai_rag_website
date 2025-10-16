# AI RAG 智能问答系统

## 🎯 项目简介

AI RAG智能问答系统是一个现代化的知识问答平台，结合了检索增强生成（RAG）技术和多种AI大模型，为用户提供智能、准确的问答服务。系统支持文档上传、知识管理、实时聊天等功能，适用于企业知识库、客户服务、学术研究等多种场景。

## ⭐ 核心功能

### 🤖 智能对话系统
- **多模型支持**: 集成通义千问、GPT、Claude、Gemini等主流AI模型
- **会话管理**: 支持多轮对话，自动保存聊天历史
- **实时响应**: 流式输出，提供更好的交互体验
- **上下文理解**: 基于历史对话提供连贯的回答

### 📚 文档知识管理
- **文档上传**: 支持PDF、Word、TXT等多种文档格式
- **智能分类**: 自动识别文档类型，支持自定义分类
- **全文搜索**: 快速检索文档内容，精准定位信息
- **权限控制**: 支持文档访问权限设置和分享管理

### 👥 用户系统
- **用户注册/登录**: 安全的身份认证机制
- **会话隔离**: 每个用户独立的对话空间
- **历史记录**: 完整保存用户的聊天记录和文档操作
- **个人设置**: 自定义AI模型偏好和界面设置

### 🎨 现代化界面
- **响应式设计**: 完美适配桌面端和移动端
- **Material Design**: 采用Element Plus组件，界面美观易用
- **深色模式**: 支持明暗主题切换
- **实时更新**: 页面无刷新更新，流畅的用户体验

### 🔗 开放API接口
- **RESTful API**: 标准化的接口设计
- **认证授权**: JWT令牌认证，安全可靠
- **API文档**: 完整的接口文档和调用示例
- **第三方集成**: 易于集成到现有系统中

## 🏗️ 技术架构

一个基于Django后端和Vue.js前端的智能问答系统，采用前后端分离架构，具备高可用、易扩展的特点。

## 系统架构

- **后端**: Django 5.2.7 + Django REST Framework
- **前端**: Vue.js 3 + Element Plus + Vite
- **数据库**: SQLite (开发环境)
- **AI服务**: 集成Dify API，支持多种AI模型

## 功能特性

- 🤖 智能聊天对话
- 📄 文档上传与管理 
- 👤 用户认证与会话管理
- 🔍 文档搜索与分类
- 📱 响应式现代化UI界面
- 🔗 RESTful API接口

## 本地启动说明

### 环境要求

- Python 3.8+
- Node.js 16+
- npm 或 yarn

### 1. 克隆项目

```bash
git clone [项目地址]
cd ai_rag_website
```

### 2. 后端启动

#### 2.1 进入后端目录
```bash
cd backend
```

#### 2.2 创建虚拟环境（推荐）
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

#### 2.3 安装依赖
```bash
pip install -r requirements.txt
```

#### 2.4 数据库初始化
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 2.5 创建超级用户（可选）
```bash
python manage.py createsuperuser
```

#### 2.6 启动后端服务
```bash
python manage.py runserver
```

✅ 后端服务将在 http://127.0.0.1:8000/ 启动

### 3. 前端启动

#### 3.1 新开终端，进入前端目录
```bash
cd frontend
```

#### 3.2 安装依赖
```bash
npm install
# 或者
yarn install
```

#### 3.3 启动开发服务器
```bash
npm run dev
# 或者
yarn dev
```

✅ 前端服务将在 http://localhost:3000/ 启动

### 4. 访问应用

- **前端应用**: http://localhost:3000/
- **后端API**: http://127.0.0.1:8000/api/
- **后端管理后台**: http://127.0.0.1:8000/admin/

## 生产环境部署

### 构建前端
```bash
cd frontend
npm run build
```

### 配置Django静态文件
构建完成后，Django会自动从 `frontend/dist/` 目录提供静态文件服务。

生产环境访问: http://127.0.0.1:8000/

## API 接口说明

### 主要API端点

- **聊天API**: `POST /api/chat/chat/`
- **会话管理**: `GET/POST /api/chat/sessions/`
- **文档管理**: `GET/POST /api/documents/`
- **用户认证**: `POST /api/auth/login/`
- **可用模型**: `GET /api/chat/models/`

### 聊天API示例

```json
POST /api/chat/chat/
{
    "message": "你好，请介绍一下这个系统",
    "session_id": 20,  // 可选，不提供则创建新会话
    "model": "通义千问"  // 可选，使用指定AI模型
}
```

## 目录结构

```
ai_rag_website/
├── backend/                 # Django后端
│   ├── config/             # 项目配置
│   ├── apps/               # 应用模块
│   │   ├── accounts/       # 用户认证
│   │   ├── chat/          # 聊天功能
│   │   ├── documents/     # 文档管理
│   │   ├── knowledge/     # 知识库
│   │   └── ai_service/    # AI服务集成
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # Vue.js前端
│   ├── src/
│   │   ├── components/    # 组件
│   │   ├── views/         # 页面
│   │   ├── stores/        # 状态管理
│   │   └── utils/         # 工具函数
│   ├── dist/              # 构建输出
│   ├── package.json
│   └── vite.config.js
└── README.md              # 本文件
```

## 常见问题

### 1. 静态文件无法加载
确保运行了 `npm run build` 并且Django的静态文件配置正确。

### 2. CORS错误
检查Django的CORS设置，确保前端域名在允许列表中。

### 3. AI服务连接失败
检查AI服务配置，确保API密钥和服务地址正确。

### 4. 数据库错误
重新运行迁移命令：
```bash
python manage.py makemigrations
python manage.py migrate
```

## 开发说明

- 后端开发服务器支持热重载
- 前端支持热模块替换(HMR)
- API文档可通过Django REST Framework浏览器界面查看
- 推荐使用虚拟环境隔离Python依赖

## 技术栈详情

- **Django**: Web框架
- **Django REST Framework**: API框架
- **Vue.js 3**: 前端框架
- **Element Plus**: UI组件库
- **Vite**: 前端构建工具
- **Pinia**: 状态管理
- **Axios**: HTTP客户端

---

如有问题，请查看控制台输出或联系开发团队。