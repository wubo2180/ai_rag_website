# IBoxTech OCR Commission API - 接口文档

## 接口概览

本服务提供 PDF 文档的 OCR 识别和字段提取功能。

### 基础信息
- **服务名称**: IBoxTech OCR Commission API
- **版本**: 1.0.0
- **默认端口**: 6001
- **基础URL**: http://localhost:6001

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
    "service": "IBoxTech OCR Commission API",
    "version": "1.0.0"
}
```

**字段说明**:
- `status` (string, 必需): 服务状态
- `timestamp` (string, 必需): 当前时间戳（ISO 8601格式）
- `service` (string, 可选): 服务名称
- `version` (string, 可选): 服务版本

---

### 2. OCR 分析

**接口地址**: `POST /api/analyze`

**描述**: 上传 PDF 文件进行 OCR 识别和字段提取

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
    "message": "成功处理 2 页PDF文档",
    "data": {
        "total_pages": 2,
        "ocr_raw_data": [
            {
                "page_number": 1,
                "dt_polys": [...],
                "rec_res": [...]
            }
        ],
        "field_extraction_results": [
            {
                "page_number": 1,
                "extracted_fields": {...}
            }
        ],
        "combined_results": {
            "combined_timestamp": "2025-11-11T10:30:00.123456",
            "total_pages": 2,
            "combined_ocr_data": {...},
            "combined_field_data": {...}
        }
    },
    "processing_time": 3.45
}
```

**字段说明**:
- `success` (boolean): 处理是否成功
- `message` (string): 处理结果信息
- `data` (object): 分析结果数据
  - `total_pages` (integer): PDF 总页数
  - `ocr_raw_data` (array): 各页 OCR 原始数据
  - `field_extraction_results` (array): 各页字段提取结果
  - `combined_results` (object): 多页合并结果
- `processing_time` (float): 处理耗时（秒）

**错误响应**:
```json
{
    "success": false,
    "message": "错误描述",
    "data": {
        "total_pages": 0,
        "ocr_raw_data": [],
        "field_extraction_results": [],
        "combined_results": null
    },
    "processing_time": 0.12
}
```

---

## 使用示例

### Python

#### 健康检查
```python
import requests

response = requests.get("http://localhost:6001/health")
print(response.json())
```

#### OCR 分析
```python
import requests
import json

# 准备文件和参数
files = {
    'file': ('document.pdf', open('document.pdf', 'rb'), 'application/pdf')
}

data = {
    'user': 'user_123',
    'token': 'your_token',
    'response_mode': 'blocking',
    'extra': json.dumps({"priority": "high"})
}

# 发送请求
response = requests.post(
    "http://localhost:6001/api/analyze",
    files=files,
    data=data
)

result = response.json()
print(f"处理成功: {result['success']}")
print(f"总页数: {result['data']['total_pages']}")
print(f"处理时间: {result['processing_time']}秒")
```

### cURL

#### 健康检查
```bash
curl http://localhost:6001/health
```

#### OCR 分析
```bash
curl -X POST http://localhost:6001/api/analyze \
  -F "file=@document.pdf" \
  -F "user=user_123" \
  -F "token=your_token" \
  -F "response_mode=blocking" \
  -F 'extra={"priority":"high"}'
```

---

## 测试

使用提供的测试脚本进行接口测试：

```bash
# 测试健康检查和根接口
python test_api.py

# 测试完整功能（包括文件上传）
python test_api.py /path/to/your/test.pdf
```

---

## 启动服务

```bash
python api_server.py
```

服务启动后：
- API 服务: http://localhost:6001
- 交互式文档: http://localhost:6001/docs
- 替代文档: http://localhost:6001/redoc

---

## 更新记录

### 版本 1.0.0 (2025-11-11)
- ✅ 将 `/analyze` 接口更名为 `/api/analyze`
- ✅ 添加 `user`, `token`, `response_mode`, `extra` 可选参数
- ✅ 统一返回格式：`{success, message, data, processing_time}`
- ✅ 更新 `/health` 接口，返回 `status` 和 `timestamp` 字段
- ✅ 添加请求参数日志记录



