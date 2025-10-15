"""
Django shell 测试脚本
在 Django shell 中运行此脚本来测试 Dify API
用法: python manage.py shell < test_dify_in_shell.py
"""
from apps.ai_service.services import ai_service
import json

print("=" * 60)
print("测试 Dify API 调用")
print("=" * 60)

# 测试1: 简单消息
print("\n测试1: 发送简单消息")
print("-" * 60)
result = ai_service.generate_response(
    message="你好",
    user_id="test_user",
    session_id=None,
    model="通义千问"
)

print(f"成功: {result.get('success')}")
print(f"响应: {result.get('response')}")
print(f"会话ID: {result.get('conversation_id')}")
print(f"消息ID: {result.get('message_id')}")
print(f"模型: {result.get('model')}")
if result.get('error'):
    print(f"错误: {result.get('error')}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
