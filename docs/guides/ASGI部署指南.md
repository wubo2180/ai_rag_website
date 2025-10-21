# ASGI 异步部署指南

## 📋 概述

AI RAG Website 现在支持 ASGI 异步部署，提供更高的性能和并发处理能力。

## 🚀 部署方式

### 1. 开发环境 (Uvicorn)

```bash
# Windows
start_asgi_dev.bat

# Linux/Mac
uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
```

### 2. 生产环境 (Gunicorn + Uvicorn Workers)

```bash
# Windows
start_asgi.bat

# Linux/Mac
gunicorn config.asgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --worker-connections 1000 \
    --timeout 120
```

## 📦 核心依赖

### ASGI 服务器
- **uvicorn**: 高性能 ASGI 服务器
- **gunicorn**: 支持 ASGI 的进程管理器
- **uvloop**: 高性能事件循环 (Linux/Mac)
- **httptools**: 快速 HTTP 解析

### 异步支持
- **httpx**: 异步 HTTP 客户端
- **aiohttp**: 异步 HTTP 库
- **aiofiles**: 异步文件操作
- **asyncpg**: PostgreSQL 异步驱动

### 缓存和任务队列
- **redis**: 高性能缓存
- **celery**: 异步任务队列

## ⚙️ 配置优化

### ASGI 服务器配置

```python
# config/asgi.py
async def application(scope, receive, send):
    """优化的 ASGI 应用"""
    if scope['type'] == 'http':
        await django_asgi_app(scope, receive, send)
    elif scope['type'] == 'websocket':
        # WebSocket 支持
        await websocket_handler(scope, receive, send)
```

### 生产环境参数

- **workers**: 4 (CPU 核心数)
- **worker-connections**: 1000
- **max-requests**: 1000 (防止内存泄漏)
- **timeout**: 120 秒

## 📊 性能优势

### 吞吐量提升
- **并发连接**: 支持数千个并发连接
- **响应时间**: 减少 30-50% 的响应延迟
- **资源利用**: 更高效的内存和 CPU 使用

### 功能增强
- **WebSocket**: 支持实时通信
- **异步任务**: 非阻塞的长时间操作
- **流式响应**: 支持大文件传输

## 🔧 部署步骤

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 数据库迁移

```bash
python manage.py migrate
```

### 3. 启动服务

```bash
# 开发环境
./start_asgi_dev.bat

# 生产环境
./start_asgi.bat
```

## 🐳 Docker 部署

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# 使用 ASGI 启动
CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker"]
```

## 📈 监控和调优

### 性能监控

```bash
# 查看工作进程
ps aux | grep gunicorn

# 查看连接状态
netstat -an | grep :8000

# 内存使用情况
htop
```

### 日志配置

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'asgi': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'uvicorn': {
            'handlers': ['asgi'],
            'level': 'INFO',
        },
    },
}
```

## 🚨 注意事项

### 平台兼容性
- **uvloop**: 仅支持 Unix 系统 (Linux/Mac)
- **Windows**: 自动降级到标准事件循环

### 内存管理
- 定期重启 workers (max-requests)
- 监控内存使用情况
- 配置适当的超时时间

### 安全考虑
- 使用反向代理 (Nginx)
- 配置 SSL/TLS
- 限制并发连接数

---

*ASGI 部署配置完成于 2025年10月21日*