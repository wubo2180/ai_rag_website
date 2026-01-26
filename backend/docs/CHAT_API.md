# Chat API 接口文档

## 📋 基础信息

| 项目         | 说明                                     |
| ------------ | ---------------------------------------- |
| 基础路径     | `/api/chat/`                             |
| 认证方式     | JWT Bearer Token（部分接口允许匿名访问） |
| Content-Type | `application/json`                       |
| 响应格式     | JSON                                     |

---

## 🔐 认证说明

需要认证的接口需在请求头中添加：

```
Authorization: Bearer <access_token>
```

---

## 📚 接口列表

### 1. 会话管理

#### 1.1 获取会话列表

获取当前登录用户的所有聊天会话。

**请求**

```http
GET /api/chat/sessions/
```

**权限**: 🔒 需要登录

**查询参数**

| 参数      | 类型    | 必填 | 默认值 | 说明             |
| --------- | ------- | ---- | ------ | ---------------- |
| page      | integer | 否   | 1      | 页码             |
| page_size | integer | 否   | 10     | 每页数量，最大50 |

**响应示例**

```json
{
  "count": 25,
  "next": "http://example.com/api/chat/sessions/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "关于Python的问题",
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T11:00:00Z",
      "dify_conversation_id": "conv_abc123"
    },
    {
      "id": 2,
      "title": "Vue.js组件开发",
      "created_at": "2025-01-14T09:00:00Z",
      "updated_at": "2025-01-14T10:30:00Z",
      "dify_conversation_id": "conv_def456"
    }
  ]
}
```

---

#### 1.2 创建新会话

创建一个新的聊天会话。

**请求**

```http
POST /api/chat/sessions/
```

**权限**: 🔒 需要登录

**请求体**

```json
{
  "title": "新对话标题"
}
```

| 参数  | 类型   | 必填 | 说明                  |
| ----- | ------ | ---- | --------------------- |
| title | string | 是   | 会话标题，最大100字符 |

**响应示例**

```json
{
  "id": 3,
  "title": "新对话标题",
  "created_at": "2025-01-22T12:00:00Z",
  "updated_at": "2025-01-22T12:00:00Z",
  "dify_conversation_id": null
}
```

---

#### 1.3 获取会话详情

获取指定会话的详细信息。

**请求**

```http
GET /api/chat/sessions/{id}/
```

**权限**: 🔒 需要登录（只能访问自己的会话）

**路径参数**

| 参数 | 类型    | 说明   |
| ---- | ------- | ------ |
| id   | integer | 会话ID |

**响应示例**

```json
{
  "id": 1,
  "title": "关于Python的问题",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "dify_conversation_id": "conv_abc123"
}
```

---

#### 1.4 更新会话

更新会话信息（如标题）。

**请求**

```http
PUT /api/chat/sessions/{id}/
PATCH /api/chat/sessions/{id}/
```

**权限**: 🔒 需要登录

**请求体**

```json
{
  "title": "更新后的标题"
}
```

**响应示例**

```json
{
  "id": 1,
  "title": "更新后的标题",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-22T12:30:00Z",
  "dify_conversation_id": "conv_abc123"
}
```

---

#### 1.5 删除会话

删除指定的聊天会话及其所有消息。

**请求**

```http
DELETE /api/chat/sessions/{id}/
```

**权限**: 🔒 需要登录

**路径参数**

| 参数 | 类型    | 说明   |
| ---- | ------- | ------ |
| id   | integer | 会话ID |

**响应示例**

```json
{
  "success": true,
  "message": "会话已删除"
}
```

---

#### 1.6 重命名会话

重命名指定的聊天会话。

**请求**

```http
POST /api/chat/sessions/{session_id}/rename/
```

**权限**: 🔒 需要登录

**路径参数**

| 参数       | 类型    | 说明   |
| ---------- | ------- | ------ |
| session_id | integer | 会话ID |

**请求体**

```json
{
  "title": "新的会话标题"
}
```

| 参数  | 类型   | 必填 | 说明                |
| ----- | ------ | ---- | ------------------- |
| title | string | 是   | 新标题，最大100字符 |

**成功响应**

```json
{
  "success": true,
  "title": "新的会话标题",
  "message": "重命名成功"
}
```

**错误响应**

```json
{
  "error": "会话标题不能为空"
}
```

```json
{
  "error": "标题长度不能超过100个字符"
}
```

---

### 2. 聊天历史

#### 2.1 获取会话聊天历史

获取指定会话的所有聊天消息记录。

**请求**

```http
GET /api/chat/sessions/{session_id}/history/
```

**权限**: 🌐 允许匿名访问（登录用户只能访问自己的会话）

**路径参数**

| 参数       | 类型    | 说明   |
| ---------- | ------- | ------ |
| session_id | integer | 会话ID |

**响应示例**

```json
{
  "id": 1,
  "title": "关于Python的问题",
  "user": "username",
  "dify_conversation_id": "conv_abc123",
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T11:00:00Z",
  "messages": [
    {
      "id": 1,
      "content": "Python如何读取文件？",
      "is_user": true,
      "timestamp": "2025-01-15T10:30:00Z"
    },
    {
      "id": 2,
      "content": "在Python中，您可以使用open()函数来读取文件...",
      "is_user": false,
      "timestamp": "2025-01-15T10:30:05Z"
    }
  ]
}
```

---

### 3. 聊天对话

#### 3.1 发送消息（标准模式）

发送用户消息并获取AI回复。

**请求**

```http
POST /api/chat/chat/
```

**权限**: 🌐 允许匿名访问

**请求体**

```json
{
  "message": "请介绍一下Python的特点",
  "session_id": 1,
  "model": "通义千问"
}
```

| 参数       | 类型    | 必填  | 说明                       |
| ---------- | ------- | ----- | -------------------------- |
| message    | string  | ✅ 是 | 用户消息内容               |
| session_id | integer | 否    | 会话ID，不提供则创建新会话 |
| model      | string  | 否    | AI模型名称                 |

**成功响应**

```json
{
  "success": true,
  "session_id": "1",
  "conversation_id": "conv_abc123",
  "user_message": {
    "id": 1,
    "content": "请介绍一下Python的特点",
    "is_user": true,
    "timestamp": "2025-01-22T10:30:00Z"
  },
  "ai_message": {
    "id": 2,
    "content": "Python是一种高级编程语言，具有以下特点：\n1. 简洁易读...",
    "is_user": false,
    "timestamp": "2025-01-22T10:30:05Z"
  },
  "response": "Python是一种高级编程语言，具有以下特点：\n1. 简洁易读...",
  "model": "通义千问",
  "dify_success": true
}
```

**错误响应**

```json
{
  "success": false,
  "error": "AI服务错误: 连接超时",
  "session_id": "1",
  "response": "抱歉，AI服务暂时不可用。错误信息：连接超时"
}
```

---

#### 3.2 发送消息（函数视图版本）

传统的聊天API接口。

**请求**

```http
POST /api/chat/send/
```

**权限**: 🌐 允许匿名访问（CSRF豁免）

**请求体**

```json
{
  "message": "你好",
  "session_id": 1,
  "model": "通义千问"
}
```

| 参数       | 类型    | 必填  | 说明         |
| ---------- | ------- | ----- | ------------ |
| message    | string  | ✅ 是 | 用户消息内容 |
| session_id | integer | 否    | 会话ID       |
| model      | string  | 否    | AI模型名称   |

**响应示例**

```json
{
  "success": true,
  "response": "你好！有什么可以帮助你的吗？",
  "session_id": 1,
  "message_id": 15,
  "model": "通义千问",
  "error": null
}
```

---

### 4. AI模型管理

#### 4.1 获取可用模型列表

获取系统支持的AI模型列表。

**请求**

```http
GET /api/chat/models/
```

**权限**: 🌐 允许匿名访问

**响应示例**

```json
{
  "models": [
    { "value": "通义千问", "label": "通义千问" },
    { "value": "deepseek", "label": "DeepSeek" },
    { "value": "gpt4", "label": "GPT-4" },
    { "value": "claude", "label": "Claude" }
  ],
  "default_model": "通义千问"
}
```

---

#### 4.2 获取可用模型（函数视图版本）

**请求**

```http
GET /api/chat/available-models/
```

**权限**: 🌐 允许匿名访问

**响应示例**

```json
{
  "success": true,
  "models": [
    { "value": "通义千问", "label": "通义千问" },
    { "value": "deepseek", "label": "DeepSeek" }
  ]
}
```

---

### 5. 测试接口

#### 5.1 测试AI服务连接

测试与AI服务的连接状态。

**请求**

```http
GET /api/chat/test/
```

**权限**: 🌐 允许匿名访问

**成功响应**

```json
{
  "success": true,
  "message": "AI服务连接正常",
  "response": "你好！有什么可以帮助你的吗？",
  "error": null
}
```

**失败响应**

```json
{
  "success": false,
  "message": "AI服务连接失败",
  "response": "",
  "error": "连接超时"
}
```

---

### 6. 微信小程序专用接口

#### 6.1 微信小程序SSE流式聊天

专为微信小程序设计的Server-Sent Events流式聊天接口。

**请求**

```http
POST /api/chat/wechat/stream/
```

**权限**: 🌐 允许匿名访问

**请求体**

```json
{
  "message": "用户消息内容",
  "session_id": "会话ID（可选）",
  "model": "模型名称（可选）",
  "user_id": "微信用户标识（可选）"
}
```

| 参数       | 类型   | 必填  | 说明                                   |
| ---------- | ------ | ----- | -------------------------------------- |
| message    | string | ✅ 是 | 用户消息内容                           |
| session_id | string | 否    | 会话ID，不提供则创建新会话             |
| model      | string | 否    | AI模型名称                             |
| user_id    | string | 否    | 微信用户标识，默认为"wechat_anonymous" |

**响应格式**: Server-Sent Events (SSE)

**响应头**

```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
Access-Control-Allow-Origin: *
```

**SSE数据流示例**

```
data: {"session_id": "123", "conversation_id": "abc"}

data: {"content": "你"}

data: {"content": "好"}

data: {"content": "！"}

data: {"content": "有什么"}

data: {"content": "可以帮助"}

data: {"content": "你的吗？"}

data: {"done": true, "message_id": "xxx"}

data: [DONE]

```

**错误响应（SSE格式）**

```
data: {"error": "消息不能为空"}

data: [DONE]

```

---

## ⚠️ 错误码说明

| HTTP状态码 | 说明                                     |
| ---------- | ---------------------------------------- |
| 200        | 请求成功                                 |
| 400        | 请求参数错误（消息为空、JSON格式错误等） |
| 401        | 未认证（需要登录但未提供有效Token）      |
| 403        | 无权限访问（会话属于其他用户）           |
| 404        | 资源不存在（会话不存在）                 |
| 405        | 不支持的请求方法                         |
| 500        | 服务器内部错误（AI服务不可用等）         |

---

## 📝 通用错误响应格式

```json
{
  "error": "错误描述信息"
}
```

或

```json
{
  "success": false,
  "error": "错误描述信息"
}
```

---

## 💡 使用示例

### JavaScript/前端调用示例

#### 发送聊天消息

```javascript
const response = await fetch('/api/chat/chat/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  },
  body: JSON.stringify({
    message: '你好，请介绍一下这个系统',
    model: '通义千问',
  }),
})

const data = await response.json()
if (data.success) {
  console.log('AI回复:', data.response)
} else {
  console.error('错误:', data.error)
}
```

#### 获取会话列表

```javascript
const response = await fetch('/api/chat/sessions/', {
  method: 'GET',
  headers: {
    Authorization: `Bearer ${accessToken}`,
  },
})

const data = await response.json()
console.log('会话列表:', data.results)
```

#### 微信小程序SSE流式调用

```javascript
// 微信小程序中使用 requestTask 处理SSE
const requestTask = wx.request({
  url: 'https://your-domain.com/api/chat/wechat/stream/',
  method: 'POST',
  enableChunked: true, // 启用分块传输
  header: {
    'Content-Type': 'application/json',
  },
  data: {
    message: '详细解释量子计算',
    user_id: 'wx_user_123',
  },
})

requestTask.onChunkReceived(function (res) {
  const chunk = new TextDecoder().decode(res.data)
  // 解析SSE数据
  const lines = chunk.split('\n')
  lines.forEach((line) => {
    if (line.startsWith('data: ')) {
      const data = line.slice(6)
      if (data === '[DONE]') {
        console.log('流式响应完成')
      } else {
        const json = JSON.parse(data)
        if (json.content) {
          console.log('收到内容:', json.content)
        }
      }
    }
  })
})
```

### Python调用示例

```python
import requests

# 发送聊天消息
response = requests.post(
    'http://localhost:8000/api/chat/chat/',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    },
    json={
        'message': '你好',
        'model': '通义千问'
    }
)

data = response.json()
print(f"AI回复: {data['response']}")
```

### cURL调用示例

```bash
# 发送聊天消息
curl -X POST http://localhost:8000/api/chat/chat/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{"message": "你好", "model": "通义千问"}'

# 获取会话列表
curl -X GET http://localhost:8000/api/chat/sessions/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# 获取可用模型
curl -X GET http://localhost:8000/api/chat/models/
```

---

## 📌 注意事项

1. **会话管理**: 如果发送消息时不提供 `session_id`，系统会自动创建新会话
2. **消息限制**: 消息内容不能为空
3. **标题限制**: 会话标题最大长度为100个字符
4. **分页默认值**: 会话列表默认每页10条，最大50条
5. **匿名访问**: 部分接口支持匿名访问，但匿名用户的会话数据可能会丢失
6. **SSE格式**: 微信小程序接口使用标准SSE格式，每个数据块以 `data: ` 开头，以 `\n\n` 结束
7. **CORS**: 微信小程序接口已配置跨域支持

---

## 🔄 版本历史

| 版本 | 日期       | 说明                            |
| ---- | ---------- | ------------------------------- |
| v1.0 | 2025-01-22 | 初始版本，包含完整的聊天API文档 |
