# Django RAG Website

## 项目简介
该项目是一个基于Django框架的大模型RAG（Retrieval-Augmented Generation）网站，旨在提供用户账户管理、聊天功能和知识库管理。项目使用Django的MVC架构，支持数据库连接和静态文件处理。

## 项目结构
```
django-rag-website
├── manage.py
├── requirements.txt
├── config
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps
│   ├── __init__.py
│   ├── accounts
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── migrations
│   │       └── __init__.py
│   ├── chat
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   └── migrations
│   │       └── __init__.py
│   └── knowledge
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       └── migrations
│           └── __init__.py
├── templates
│   ├── base.html
│   ├── chat
│   │   └── index.html
│   └── knowledge
│       └── index.html
├── static
│   ├── css
│   │   └── style.css
│   ├── js
│   │   └── main.js
│   └── images
├── utils
│   ├── __init__.py
│   ├── llm_client.py
│   └── vector_store.py
└── README.md
```

## 安装依赖
在项目根目录下运行以下命令以安装所需的Python包：
```
pip install -r requirements.txt
```

## 数据库配置
在`config/settings.py`中配置数据库连接信息，确保数据库服务已启动并可访问。

## 启动项目
使用以下命令启动开发服务器：
```
python manage.py runserver
```

## 贡献
欢迎任何形式的贡献！请提交问题或拉取请求。

## 许可证
该项目遵循MIT许可证。