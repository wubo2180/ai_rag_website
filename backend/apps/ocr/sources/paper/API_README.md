# IBoxTech OCR Paper API - 接口文档

## 接口概览

本服务提供基于 Dify 的论文分析功能，通过上传 PDF 文件进行智能分析。

### 基础信息
- **服务名称**: IBoxTech OCR Paper API
- **版本**: 1.0.0
- **默认端口**: 6002
- **基础URL**: http://localhost:6002

---

## API 接口

### 1. 健康检查

**接口地址**: `GET /health`

**描述**: 检查服务健康状态

**响应格式**:
```json
{
    "status": "healthy",
    "timestamp": "2025-11-11T10:30:00.123456",
    "service": "IBoxTech OCR Paper API",
    "version": "1.0.0",
    "dify_base_url": "https://api.dify.ai/v1"
}
```

**字段说明**:
- `status` (string, 必需): 服务状态
- `timestamp` (string, 必需): 当前时间戳（ISO 8601格式）
- `service` (string, 可选): 服务名称
- `version` (string, 可选): 服务版本
- `dify_base_url` (string, 可选): Dify API 基础地址

---

### 2. 论文分析

**接口地址**: `POST /api/analyze`

**描述**: 上传 PDF 文件进行论文分析（通过 Dify 工作流处理）

**请求参数** (multipart/form-data):

| 参数名 | 类型 | 必需 | 说明 |
|--------|------|------|------|
| file | File | 是 | 需要分析的 PDF 文件 |
| user | string | 否 | 用户标识 |
| token | string | 否 | 用户认证 token |
| response_mode | string | 否 | 响应模式：`blocking` 或 `streaming` (默认: blocking) |
| extra | string | 否 | 自定义参数（JSON字符串格式） |

**响应格式**:
```json
{
    "success": true,
    "message": "论文分析成功",
    "data": {
        "workflow_run_id": "...",
        "task_id": "...",
        "data": {
            "id": "...",
            "workflow_id": "...",
            "status": "succeeded",
            "outputs": {...},
            "error": null,
            "elapsed_time": 5.2,
            "total_tokens": 1234,
            "total_steps": 3,
            "created_at": 1731312000,
            "finished_at": 1731312005
        }
    },
    "processing_time": 6.78
}
```

**字段说明**:
- `success` (boolean): 处理是否成功
- `message` (string): 处理结果信息
- `data` (object): Dify 工作流返回的完整结果
- `processing_time` (float): 处理耗时（秒）

**错误响应**:
```json
{
    "success": false,
    "message": "错误描述",
    "data": null,
    "processing_time": 0.12
}
```

**常见错误**:
- 文件类型不支持
- 文件大小超过限制
- Dify 工作流执行失败

---

## 使用示例

### Python

#### 健康检查
```python
import requests

response = requests.get("http://localhost:6002/health")
print(response.json())
```

#### 论文分析
```python
import requests
import json

# 准备文件和参数
files = {
    'file': ('paper.pdf', open('paper.pdf', 'rb'), 'application/pdf')
}

data = {
    'user': 'researcher_001',
    'token': 'your_token',
    'response_mode': 'blocking',
    'extra': json.dumps({"priority": "high", "language": "en"})
}

# 发送请求
response = requests.post(
    "http://localhost:6002/api/analyze",
    files=files,
    data=data
)

result = response.json()
print(f"分析成功: {result['success']}")
print(f"处理时间: {result['processing_time']}秒")
print(f"分析结果: {result['data']}")
```

### cURL

#### 健康检查
```bash
curl http://localhost:6002/health
```

#### 论文分析
```bash
curl -X POST http://localhost:6002/api/analyze \
  -F "file=@paper.pdf" \
  -F "user=researcher_001" \
  -F "token=your_token" \
  -F "response_mode=blocking" \
  -F 'extra={"priority":"high","language":"en"}'
```

---

## 配置说明

服务通过 `config.yaml` 文件进行配置：

```yaml
api:
  host: "0.0.0.0"
  port: 6002
  debug: true
  enable_cors: true
  allowed_origins: ["*"]
  temp_upload_dir: "./temp_uploads"

dify:
  base_url: "https://api.dify.ai/v1"
  api_key: "your-dify-api-key"
  workflow_id: "your-workflow-id"
  upload:
    allowed_extensions: ["pdf", "txt", "doc", "docx"]
    max_file_size: 50  # MB
```

---

## 测试

使用提供的测试脚本进行接口测试：

```bash
# 测试健康检查和根接口
python test_api.py

# 测试完整功能（包括文件上传）
python test_api.py /path/to/your/paper.pdf
```

---

## 启动服务

```bash
python api_server.py
```

服务启动后：
- API 服务: http://localhost:6002
- 交互式文档: http://localhost:6002/docs
- 替代文档: http://localhost:6002/redoc

---

## 架构说明

本服务作为中间层，连接用户和 Dify 平台：

```
用户 → IBoxTech OCR Paper API → Dify 工作流 → 论文分析结果
```

**主要功能**:
1. 接收用户上传的 PDF 文件
2. 验证文件类型和大小
3. 将文件上传到 Dify 平台
4. 触发 Dify 工作流进行分析
5. 返回统一格式的分析结果

---

## 更新记录

### 版本 1.0.0 (2025-11-11)
- ✅ 移除 `/api/upload` 接口
- ✅ 移除 `/api/workflow/run` 接口
- ✅ 将原有功能整合为统一的 `/api/analyze` 接口
- ✅ 添加 `token` 和 `extra` 可选参数
- ✅ 统一返回格式：`{success, message, data, processing_time}`
- ✅ 更新 `/health` 接口，返回 `status` 和 `timestamp` 字段
- ✅ 添加请求参数日志记录
- ✅ 简化接口结构，提供一站式文件分析服务

---

## 相关项目

- **IBoxTech-ocr-commission**: 佣金单据 OCR 分析服务
- **IBoxTech-ocrchecker**: OCR 质量检查服务

所有服务遵循统一的接口规范，便于集成和管理。

