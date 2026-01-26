# 工艺优化智能体API文档

## 架构说明

```
前端 (Vue.js)
    ↓
后端 smart_agent/process_optimization_views.py (业务逻辑层)
    ↓
后端 smart_agent/process_optimization_business.py (服务层)
    ↓
后端 ai_service/process_optimization_service.py (Dify API调用层)
    ↓
Dify 平台
```

## API接口说明

### 1. 提交工艺优化任务（流式响应）

**接口地址:** `POST /api/smart-agent/process-optimization/stream/`

**请求头:**
```
Content-Type: application/json
Authorization: Bearer {token}  # 可选，如果需要认证
```

**请求体:**
```json
{
  "product_performance": "高导电性、耐高温、循环寿命>1000次",
  "target_application_scenario": "锂电池电解质材料，用于消费电子",
  "cost_consideration": "单公斤成本控制在 200 元以内",
  "environmental_requirements": "符合 RoHS/REACH，无卤、低VOC 排放",
  "title": "工艺优化任务标题（可选）",
  "description": "任务描述（可选）"
}
```

**响应格式:** Server-Sent Events (SSE)

**响应事件类型:**

1. **任务创建事件**
```javascript
data: {"event": "task_created", "task_id": "uuid"}
```

2. **消息片段事件**
```javascript
data: {"event": "message", "answer": "部分回答内容..."}
```

3. **消息结束事件**
```javascript
data: {"event": "message_end", "conversation_id": "...", "id": "..."}
```

4. **Agent思考事件**
```javascript
data: {"event": "agent_thought", "thought": "Agent正在思考..."}
```

5. **错误事件**
```javascript
data: {"event": "error", "message": "错误信息"}
```

6. **完成事件**
```javascript
data: {"event": "done"}
```

**前端示例代码:**
```javascript
const response = await fetch('/api/smart-agent/process-optimization/stream/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    product_performance: "...",
    target_application_scenario: "...",
    cost_consideration: "...",
    environmental_requirements: "..."
  })
})

const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break
  
  const chunk = decoder.decode(value)
  const lines = chunk.split('\n')
  
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6))
      // 处理不同事件
      if (data.event === 'message') {
        console.log(data.answer)
      }
    }
  }
}
```

### 2. 提交工艺优化任务（阻塞响应）

**接口地址:** `POST /api/smart-agent/process-optimization/submit/`

**请求头和请求体:** 同流式接口

**响应格式:** JSON

**成功响应:**
```json
{
  "success": true,
  "message": "优化完成",
  "task_id": "uuid",
  "task": {
    "id": "uuid",
    "title": "任务标题",
    "status": "completed",
    "created_at": "2025-12-10T10:00:00Z",
    ...
  },
  "result": {
    "answer": "完整的优化建议...",
    "conversation_id": "...",
    "message_id": "..."
  }
}
```

**失败响应:**
```json
{
  "success": false,
  "message": "优化失败",
  "task_id": "uuid",
  "error": "错误信息"
}
```

### 3. 获取历史记录

**接口地址:** `GET /api/smart-agent/process-optimization/history/`

**权限:** 需要认证

**查询参数:**
- `limit`: 返回数量限制（默认20，最大100）

**响应:**
```json
{
  "success": true,
  "count": 10,
  "tasks": [
    {
      "id": "uuid",
      "title": "任务标题",
      "status": "completed",
      "input_data": {...},
      "created_at": "2025-12-10T10:00:00Z",
      ...
    }
  ]
}
```

### 4. 获取任务详情

**接口地址:** `GET /api/smart-agent/process-optimization/task/{task_id}/`

**权限:** 需要认证

**响应:**
```json
{
  "success": true,
  "task": {
    "id": "uuid",
    "title": "任务标题",
    "status": "completed",
    "input_data": {...},
    "created_at": "2025-12-10T10:00:00Z",
    ...
  }
}
```

## 测试方法

### 1. 使用curl测试

**流式接口:**
```bash
curl -X POST http://localhost:8000/api/smart-agent/process-optimization/stream/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_performance": "高导电性",
    "target_application_scenario": "锂电池",
    "cost_consideration": "200元/kg",
    "environmental_requirements": "RoHS/REACH"
  }' \
  --no-buffer
```

**阻塞接口:**
```bash
curl -X POST http://localhost:8000/api/smart-agent/process-optimization/submit/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_performance": "高导电性",
    "target_application_scenario": "锂电池",
    "cost_consideration": "200元/kg",
    "environmental_requirements": "RoHS/REACH"
  }'
```

### 2. 使用Python测试

参考 `test/test_process_optimization_api.py` 文件

### 3. 前端测试

访问: `http://localhost:5173/process-optimization`

## 配置说明

### 环境变量

在 `.env` 文件或系统环境变量中配置:

```bash
# Dify工艺优化API配置
DIFY_PROCESS_API_BASE=http://172.20.46.18:8088/v1
DIFY_PROCESS_API_KEY=app-tz7Fg3RuCXG6EE99kwADJJ6N
```

### Django Settings

如果不使用环境变量,可以在 `settings.py` 中配置:

```python
# Dify配置
DIFY_PROCESS_API_BASE = 'http://172.20.46.18:8088/v1'
DIFY_PROCESS_API_KEY = 'app-tz7Fg3RuCXG6EE99kwADJJ6N'
```

## 错误处理

### 常见错误

1. **验证错误 (400)**
```json
{
  "success": false,
  "errors": ["缺少必填字段: product_performance"]
}
```

2. **认证错误 (401)**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

3. **权限错误 (403)**
```json
{
  "detail": "You do not have permission to perform this action."
}
```

4. **任务不存在 (404)**
```json
{
  "success": false,
  "error": "任务不存在或无权访问"
}
```

5. **服务器错误 (500)**
```json
{
  "success": false,
  "error": "内部服务器错误"
}
```

## 日志记录

所有API调用都会记录日志,包括:
- 请求参数
- 响应状态
- 错误信息
- 执行时间

查看日志:
```bash
tail -f backend/logs/django.log
```

## 性能优化

1. **流式响应**: 使用SSE减少等待时间
2. **异步处理**: 考虑使用Celery进行异步任务处理
3. **缓存**: 可以缓存相似的查询结果
4. **限流**: 使用Django的限流中间件防止滥用

## 安全建议

1. **认证**: 生产环境必须启用认证
2. **HTTPS**: 使用HTTPS加密传输
3. **输入验证**: 严格验证所有输入参数
4. **速率限制**: 限制每个用户的请求频率
5. **API密钥**: 定期轮换Dify API密钥

## 监控指标

建议监控以下指标:
- API响应时间
- 成功/失败率
- 并发请求数
- Dify API调用次数
- 任务完成时间

## 后续优化建议

1. 添加任务队列(Celery)
2. 添加结果缓存(Redis)
3. 添加API版本控制
4. 添加WebSocket支持
5. 添加更详细的统计分析
