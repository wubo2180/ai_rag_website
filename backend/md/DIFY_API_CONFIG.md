# Dify API 集成配置说明

## 已完成的配置

### 1. Settings 配置 (config/settings.py)
```python
# Dify API 配置
DIFY_API_KEY = 'app-K9fjgkD8JbNrNfTH2ECIv4jw'
DIFY_BASE_URL = 'http://localhost/v1'
DIFY_DEFAULT_MODEL = '通义千问'

# 可用模型列表
AVAILABLE_AI_MODELS = [
    'deepseek深度思考',
    '通义千问',
    '腾讯混元',
    '豆包',
    'Kimi',
    'GPT-5',
    'Claude4',
    'Gemini2.5',
    'Grok-4',
    'Llama4'
]
```

### 2. AI Service 模块 (apps/ai_service/services.py)
- 创建了 `AIService` 类
- 实现了 `generate_response()` 方法
- 正确配置了 Dify API 调用格式：
  - URL: `http://localhost/v1/chat-messages`
  - Headers: `Authorization: Bearer app-K9fjgkD8JbNrNfTH2ECIv4jw`
  - Payload 包含 `inputs.largeModel` 参数

### 3. Chat Views 更新 (apps/chat/views.py)
- `chat_api()`: 接收用户消息和模型选择，调用 Dify API
- `get_available_models()`: 返回可用模型列表
- `test_ai_connection()`: 测试 Dify API 连接

### 4. URL 配置 (apps/chat/urls.py)
```python
path('api/', views.chat_api, name='chat_api'),
path('api/models/', views.get_available_models, name='get_models'),
path('api/test/', views.test_ai_connection, name='test_ai'),
```

### 5. 前端界面 (templates/chat/index.html)
- 添加了模型选择下拉框
- 页面加载时自动获取可用模型列表
- 发送消息时包含选中的模型参数
- 显示当前选中的模型状态

## API 请求格式

### 发送消息到 Dify
```javascript
POST /chat/api/
{
    "message": "你好",
    "session_id": "optional_session_id",
    "model": "通义千问"
}
```

### 获取可用模型
```javascript
GET /chat/api/models/
```

### 测试连接
```javascript
GET /chat/api/test/
```

## 使用流程

1. 用户在聊天页面选择AI模型
2. 输入问题并点击发送
3. 前端将消息和模型参数发送到 `/chat/api/`
4. Django后端调用 `ai_service.generate_response()`
5. AI Service 调用 Dify API (`http://localhost/v1/chat-messages`)
6. 返回响应并保存到数据库
7. 前端显示AI回复

## 注意事项

1. **确保 Dify 服务运行在 http://localhost/v1**
2. **API Key 必须正确**: `app-K9fjgkD8JbNrNfTH2ECIv4jw`
3. **模型名称必须使用中文**: 如 "通义千问"、"deepseek深度思考" 等
4. **Dify API 要求在 inputs 中传递 largeModel 参数**
5. **conversation_id 必须是 UUID 格式**:
   - 第一次对话时不传 conversation_id，Dify会创建新会话并返回UUID
   - 后续对话传递Dify返回的 conversation_id (存储在 ChatSession.dify_conversation_id)
   - 不能传递数据库的整数ID，会导致 400 错误

## 会话ID处理机制

- **数据库会话ID**: ChatSession.id (整数，用于前端标识)
- **Dify会话ID**: ChatSession.dify_conversation_id (UUID字符串，用于Dify API)
- **流程**:
  1. 创建新会话时，dify_conversation_id 为空
  2. 首次调用Dify API时不传conversation_id
  3. Dify返回conversation_id（UUID格式）
  4. 保存到 ChatSession.dify_conversation_id
  5. 后续消息使用保存的dify_conversation_id

## 测试方法

1. 启动 Django 服务器
2. 访问 http://127.0.0.1:8000/chat/
3. 选择一个模型（默认是"通义千问"）
4. 输入问题并发送
5. 检查是否收到 Dify API 的响应

## 故障排查

如果遇到问题，可以：
1. 访问 `/chat/api/test/` 测试连接
2. 检查 Django 日志查看详细错误信息
3. 确认 Dify 服务正常运行
4. 验证 API Key 是否正确
