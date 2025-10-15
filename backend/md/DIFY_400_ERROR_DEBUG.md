# Dify API 400 错误诊断指南

## 问题描述
收到错误: `400 Client Error: BAD REQUEST for url: http://localhost/v1/chat-messages`

## 可能的原因

### 1. Dify 工作流配置问题 ⭐ **最可能的原因**

Dify 工作流可能没有正确配置 `inputs` 参数。

**解决方案：**
1. 打开 Dify 后台: http://localhost
2. 进入对应的应用
3. 点击 **API 访问** 或 **API 文档**
4. 查看 API 请求示例
5. 检查是否需要 `inputs` 参数

**两种可能的配置：**

#### 方案 A: 不需要 inputs 参数
如果 Dify API 文档显示不需要 `inputs` 参数，修改代码：

打开 `apps/ai_service/services.py`，找到这段代码：
```python
# 尝试添加 inputs 参数（如果 Dify 工作流需要）
# 注意：这取决于你的 Dify 工作流配置
# 如果工作流不需要 inputs 参数，请注释掉下面这段
if model:
    payload['inputs'] = {'largeModel': model}
```

将其注释掉：
```python
# 尝试添加 inputs 参数（如果 Dify 工作流需要）
# 注意：这取决于你的 Dify 工作流配置
# 如果工作流不需要 inputs 参数，请注释掉下面这段
# if model:
#     payload['inputs'] = {'largeModel': model}
```

#### 方案 B: inputs 参数名称不匹配
如果 Dify 工作流需要 inputs 参数，但字段名不是 `largeModel`：

1. 在 Dify 工作流中查看输入变量的名称
2. 修改代码中的字段名：

```python
if model:
    payload['inputs'] = {'你的字段名': model}  # 替换为实际的字段名
```

### 2. API 密钥错误

检查 `config/settings.py` 中的 API 密钥：
```python
DIFY_API_KEY = 'app-K9fjgkD8JbNrNfTH2ECIv4jw'
```

确保这个密钥与 Dify 后台显示的完全一致。

### 3. Dify 服务未启动

检查 Dify 是否正在运行：
```bash
# 访问 Dify 管理界面
http://localhost

# 或者检查 Docker 容器状态
docker ps | findstr dify
```

### 4. URL 配置错误

检查 `config/settings.py` 中的 URL：
```python
DIFY_BASE_URL = 'http://localhost/v1'
```

确保端口和路径正确。

## 调试步骤

### 步骤 1: 查看详细错误日志

修改后的代码会在控制台显示详细的错误信息。刷新浏览器并重新发送消息，查看 Django 控制台输出。

### 步骤 2: 检查 Dify API 文档

1. 打开 Dify 后台
2. 进入你的应用
3. 点击 **API 访问**
4. 查看 **API 请求示例**
5. 复制正确的请求格式

### 步骤 3: 测试最简单的请求

临时修改 `apps/ai_service/services.py`，使用最简单的 payload：

```python
payload = {
    'query': message,
    'response_mode': 'blocking',
    'user': user_id
}
# 暂时注释掉 inputs 和 conversation_id
```

如果这个可以工作，再逐步添加其他参数。

### 步骤 4: 使用 Postman 或 curl 测试

使用 curl 直接测试 Dify API：

```bash
curl -X POST http://localhost/v1/chat-messages \
  -H "Authorization: Bearer app-K9fjgkD8JbNrNfTH2ECIv4jw" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你好",
    "response_mode": "blocking",
    "user": "test_user"
  }'
```

观察返回结果，确定正确的请求格式。

## 当前代码修改

已经做了以下修改：

1. ✅ 添加了详细的错误日志输出
2. ✅ 改进了异常处理
3. ✅ 将 `inputs` 参数设为可选
4. ✅ 记录完整的请求 payload

## 下一步操作

1. **查看 Django 控制台输出**
   - 找到包含 "Dify API错误详情" 的日志
   - 复制完整的错误信息

2. **根据错误信息调整代码**
   - 如果提示缺少参数，添加该参数
   - 如果提示参数格式错误，检查 Dify 文档

3. **联系我反馈**
   - 提供完整的错误日志
   - 提供 Dify API 文档截图（如果可能）

## 常见错误信息对照

| 错误信息 | 可能原因 | 解决方案 |
|---------|---------|---------|
| `inputs.largeModel is required` | 工作流需要此参数但未提供 | 确保代码中添加了此参数 |
| `Invalid conversation_id` | conversation_id 格式错误 | 检查是否为 UUID 格式 |
| `Unauthorized` | API 密钥错误 | 检查 settings.py 中的 API_KEY |
| `Not Found` | URL 或应用不存在 | 检查 BASE_URL 和应用状态 |

---

💡 **提示**: 最快的诊断方法是查看 Django 控制台的详细日志输出！
