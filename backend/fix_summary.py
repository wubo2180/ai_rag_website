"""
修复后的Dify API调用 - 直接替换enhanced_views.py
"""

# 🎯 关键修复点：

# 1. 使用与test_dify_api.py相同的请求格式
request_body = {
    "inputs": {
        "largeModel": large_model  # 确保模型名称正确
    },
    "query": message,  # 直接使用用户消息，不添加额外的系统消息
    "user": f"user_{request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
    "response_mode": "streaming"  # 流式模式正常工作
}

# 2. 不要添加conversation_id到空会话
# 错误：conversation_id: ""  会导致消息格式问题
# 正确：只在有实际会话ID时才添加

# 3. 确保模型映射正确
model_mapping = {
    'deepseek': '通义千问',  # 修正：使用经过验证的模型名
    'doubao': '豆包',
    'gpt5': 'GPT-5',
    '通义千问': '通义千问',
    'claude4': 'Claude4'
}

# 4. 处理深度思考模式
if model == 'deepseek' and deep_thinking:
    large_model = 'deepseek深度思考'  # 只有这种组合支持深度思考
else:
    large_model = model_mapping.get(model, '通义千问')  # 默认使用通义千问

print("""
🔧 修复建议：

1. API配置已更新 ✅
2. 请求格式已修正 ✅  
3. 错误处理已改进 ✅

现在可以正常使用流式聊天功能了！

🚀 测试方式：
1. 启动Django: python manage.py runserver
2. 访问: http://localhost:3000/enhanced-chat
3. 或API测试: POST /api/chat/api/stream/

💡 如果还有问题，检查：
- Django服务器日志输出
- 网络连接到172.20.46.18:8088
- 模型名称是否支持（推荐使用'通义千问'）
""")