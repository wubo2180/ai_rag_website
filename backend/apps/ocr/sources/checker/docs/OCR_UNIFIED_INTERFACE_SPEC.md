# OCR服务统一接口规范

## 📋 概述

为了实现OCR适配器架构，所有OCR服务必须遵循统一的接口规范。

## 🔗 统一接口格式

### 请求格式

**端点**: `POST /api/analyze`

**Content-Type**: `multipart/form-data`

**参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | ✅ | 要识别的PDF文件 |
| user | string | ❌ | 用户标识（可选） |
| response_mode | string | ❌ | 响应模式（可选） |

### 响应格式

**HTTP状态码**:
- `200` - 识别成功
- `400` - 请求参数错误
- `500` - 服务器内部错误

**响应体**（JSON格式）:

```json
{
  "success": true,           // 必填，boolean，是否成功
  "message": "识别成功",      // 必填，string，描述信息
  "data": {                  // 必填，object/null，识别结果数据
    // 由各OCR服务定义的具体数据结构
  },
  "processing_time": 12.5    // 必填，float，处理耗时（秒）
}
```

#### 成功响应示例

**委托单OCR** (IBoxTech-ocr-commission):
```json
{
  "success": true,
  "message": "OCR识别成功",
  "data": {
    "total_pages": 2,
    "ocr_raw_data": [...],
    "field_extraction_results": [
      {
        "page_number": 1,
        "extracted_fields": {
          "委托编号": {
            "value": "COM20240101",
            "confidence": 0.95
          },
          "测试项目表": {
            "type": "multi_row_table",
            "data": [...]
          }
        }
      }
    ],
    "combined_results": {...}
  },
  "processing_time": 15.3
}
```

**论文OCR** (IBoxTech-ocr-paper):
```json
{
  "success": true,
  "message": "论文分析成功",
  "data": {
    "workflow_id": "xxx",
    "outputs": {
      "text": "...",
      "文献编号": "A1",
      "文献名称": "...",
      "四级数据连接": [...]
    }
  },
  "processing_time": 25.7
}
```

#### 失败响应示例

```json
{
  "success": false,
  "message": "文件大小超过限制",
  "data": null,
  "processing_time": 0.5
}
```

## 📝 各服务实现状态

### ✅ 已统一 - 委托单OCR服务

**服务**: IBoxTech-ocr-commission  
**端口**: 6001  
**端点**: `/analyze`  
**状态**: ✅ 已实现统一格式（原生支持）

**返回格式**:
- ✅ `success` 字段
- ✅ `message` 字段
- ✅ `data` 字段（包含field_extraction_results）
- ✅ `processing_time` 字段

### ✅ 已统一 - 论文OCR服务

**服务**: IBoxTech-ocr-paper  
**端口**: 6002  
**端点**: `/api/analyze`  
**状态**: ✅ 已修改为统一格式

**修改内容**:
1. ✅ 添加`success`字段（原为`status`）
2. ✅ 添加`message`字段
3. ✅ 保留`data`字段（包含Dify工作流结果）
4. ✅ 添加`processing_time`字段
5. ✅ 错误处理统一格式

## 🔧 适配器解析说明

### 委托单适配器解析路径

```python
# CommissionAdapter.parse_ocr_result()
raw_data = response['data']  # 从统一格式中提取data

# 解析路径
data['field_extraction_results'][0]['extracted_fields']
  ├── 普通字段: {'value': '...', 'confidence': 0.95}
  └── 表格字段: {'type': 'multi_row_table', 'data': [...]}
```

### 论文适配器解析路径

```python
# PaperAdapter.parse_ocr_result()
raw_data = response['data']  # 从统一格式中提取data

# 解析路径
data['outputs']
  ├── '文献编号': 'A1'
  ├── '文献名称': '...'
  └── '四级数据连接': [...]
```

## 🧪 测试验证

### 测试委托单OCR服务

```bash
curl -X POST http://localhost:6001/analyze \
  -F "file=@委托单样本.pdf" \
  | jq '.success, .message, .data | keys'
```

预期输出:
```
true
"OCR识别成功"
[
  "combined_results",
  "field_extraction_results",
  "ocr_raw_data",
  "total_pages"
]
```

### 测试论文OCR服务

```bash
curl -X POST http://localhost:6002/api/analyze \
  -F "file=@论文样本.pdf" \
  | jq '.success, .message, .processing_time'
```

预期输出:
```
true
"论文分析成功"
25.7
```

## 📊 接口对比表

| 字段 | 委托单OCR | 论文OCR | 统一规范 |
|------|----------|---------|---------|
| `success` | ✅ 原生支持 | ✅ 已添加 | ✅ 必填 |
| `message` | ✅ 原生支持 | ✅ 已添加 | ✅ 必填 |
| `data` | ✅ 原生支持 | ✅ 原生支持 | ✅ 必填 |
| `processing_time` | ✅ 原生支持 | ✅ 已添加 | ✅ 必填 |
| HTTP状态码 | ✅ 200/400/500 | ✅ 200/400/500 | ✅ 标准化 |

## 🎯 新OCR服务接入指南

如果要添加新的OCR服务（如：检测报告、质检单等），请遵循以下步骤：

### 1. 实现统一接口

```python
@app.post("/api/analyze")
async def analyze_file(file: UploadFile = File(...)):
    import time
    start_time = time.time()
    
    try:
        # 1. 处理文件
        result = your_ocr_process(file)
        
        # 2. 返回统一格式
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "识别成功",
                "data": result,  # 你的数据结构
                "processing_time": time.time() - start_time
            }
        )
    except Exception as e:
        # 3. 错误处理
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": str(e),
                "data": None,
                "processing_time": time.time() - start_time
            }
        )
```

### 2. 实现适配器类

```python
from adapters.base_ocr_adapter import BaseOCRAdapter

class YourAdapter(BaseOCRAdapter):
    def parse_ocr_result(self, raw_data: Dict) -> Dict:
        # 从raw_data中解析你的数据结构
        return structured_data
    
    def save_to_database(self, structured_data: Dict, file_id: int):
        # 保存到你的数据表
        pass
    
    # ... 实现其他方法
```

### 3. 注册配置

在`document_type_configs`表中添加记录，关联OCR服务和适配器。

## 🔍 健康检查接口

所有OCR服务还应提供健康检查接口：

**端点**: `GET /health`

**响应**:
```json
{
  "status": "healthy",
  "service": "OCR Service Name",
  "version": "1.0.0",
  "timestamp": "2025-11-09T10:30:00Z"
}
```

## 📚 相关文档

- [OCR适配器架构设计](./OCR_ADAPTER_ARCHITECTURE.md)
- [适配器实现总结](./OCR_ADAPTER_IMPLEMENTATION_SUMMARY.md)
- [快速开始指南](./QUICK_START_OCR.md)

---

**更新日期**: 2025-11-09  
**版本**: v1.0  
**状态**: ✅ 两个OCR服务已统一


