"""
ASGI config for ai_rag_website project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from django.conf import settings

# 设置 Django 设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# 早期设置 Django
django.setup()

# 获取 Django ASGI 应用
django_asgi_app = get_asgi_application()

async def application(scope, receive, send):
    """
    ASGI 应用入口点
    支持 HTTP 和 WebSocket 协议
    """
    if scope['type'] == 'http':
        # 处理 HTTP 请求
        await django_asgi_app(scope, receive, send)
    elif scope['type'] == 'websocket':
        # 如果需要 WebSocket 支持，在这里添加处理逻辑
        # 目前直接拒绝 WebSocket 连接
        await send({
            'type': 'websocket.close',
            'code': 4000,
        })
    else:
        # 不支持的协议类型
        raise ValueError(f"Unknown scope type: {scope['type']}")

# 为了兼容性，也导出 django_asgi_app
__all__ = ['application', 'django_asgi_app']