# 外部OCR API接口规范

## 概述
系统已禁用内置的PaddleOCR功能，改为调用外部OCR API进行文本识别。本文档定义了外部OCR API应该遵循的接口规范。

## 已禁用的组件
- ✅ `OCRService` - 基础OCR服务（PaddleOCR）
- ✅ `CommissionOCRService` - 委托单专用OCR服务（PP-StructureV3 + PaddleOCR）
- ✅ `FileService.start_ocr_processing()` - 内置OCR处理流程

## API接口规范

### 1. OCR识别接口

**请求地址**: `POST /api/ocr/recognize`

**请求参数**:
```json
{
  "file_id": 123,                    // 文件ID（可选，用于关联系统中的文件）
  "file_url": "https://...",         // 文件URL（MinIO下载地址）或base64编码
  "document_type": "commission",     // 文档类型：commission(委托单), general(通用文档)
  "options": {
    "extract_tables": true,          // 是否提取表格
    "extract_forms": true,           // 是否识别表单
    "language": "ch"                 // 语言：ch(中文), en(英文)
  }
}
```

**响应格式**:
```json
{
  "success": true,
  "message": "OCR识别成功",
  "data": {
    "commission_number": "IBTC20240918013",  // 委托编号（仅委托单）
    "extracted_text": "完整文本内容...",
    "structured_data": {
      // 针对委托单的结构化数据
      "basic_info": {
        "commission_number": "IBTC20240918013",
        "commission_department": "品质部",
        "commissioner": "张三",
        "commission_date": "2024-09-18",
        "sample_name": "塑料样品",
        // ... 其他字段
      },
      "test_items": [
        {
          "test_item": "拉伸强度",
          "test_equipment": "万能试验机",
          "test_standard": "GB/T 1040",
          // ... 其他字段
        }
      ],
      "special_tests": [
        {
          "test_type": "ROHS",
          "element_name": "铅(Pb)",
          "standard_value": "≤1000ppm",
          // ... 其他字段
        }
      ]
    },
    "confidence": 0.95,                  // 整体识别置信度
    "processing_time_ms": 1234,          // 处理耗时(毫秒)
    "ocr_engine": "external_api_v1"      // OCR引擎标识
  }
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "OCR识别失败",
  "error": "FILE_NOT_FOUND",
  "error_detail": "无法下载指定的文件"
}
```

## 系统集成方式

### 方式1：通过API回调（推荐）

1. 系统上传文件到MinIO后，调用外部OCR API
2. 外部OCR API异步处理，完成后回调系统接口
3. 系统接收OCR结果并存储到数据库

**系统回调接口**: `POST /api/ocr/callback`

**回调参数**:
```json
{
  "file_id": 123,
  "ocr_result": {
    // OCR结果数据（同上述响应格式的data字段）
  }
}
```

### 方式2：直接导入（当前使用）

通过 `CommissionDirectImportService` 直接导入已处理好的JSON数据和PDF文件：

```python
from services.commission_direct_import_service import CommissionDirectImportService

service = CommissionDirectImportService()

# 导入单个文件
result = service.import_single_pdf(
    pdf_path="/path/to/file.pdf",
    json_base_dir="/path/to/json/dir",
    uploader_id=1
)

# 批量导入
result = service.import_multiple_pdfs(
    pdf_base_dir="/path/to/pdf/dir",
    json_base_dir="/path/to/json/dir",
    uploader_id=1
)
```

## 数据库字段映射

详细的JSON字段与数据库字段映射关系，请参考：
- [JSON_DATABASE_FIELD_MAPPING.md](../misc/JSON_DATABASE_FIELD_MAPPING.md)

## 外部OCR API实现建议

### 技术选型
- **通用OCR**: 百度OCR、腾讯OCR、阿里云OCR
- **表格识别**: 表格识别专用API
- **表单识别**: 自训练模型（基于LayoutLM、FormNet等）
- **委托单专用**: 针对委托单格式训练的专用模型

### 性能要求
- 单页处理时间: < 5秒
- 识别准确率: > 95%
- 并发处理能力: > 10 QPS
- 支持格式: PDF, JPG, PNG

### 安全要求
- 支持HTTPS
- API密钥认证
- 数据传输加密
- 处理后不保留原文件

## 测试用例

```bash
# 测试OCR回调接口
curl -X POST http://localhost:5001/api/ocr/callback \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "file_id": 5,
    "ocr_result": {
      "commission_number": "IBTC20240918013",
      "structured_data": { ... }
    }
  }'
```

## 注意事项

1. **禁用的功能**
   - 内置PaddleOCR引擎已完全禁用
   - PP-StructureV3表格识别已禁用
   - 自动OCR处理流程已禁用

2. **保留的功能**
   - 文件上传到MinIO ✅
   - 文件下载预览 ✅
   - 委托数据核对界面 ✅
   - 直接数据导入 ✅

3. **迁移建议**
   - 现有JSON数据可继续使用直接导入方式
   - 新文件通过外部API处理后再导入
   - 考虑实现API回调机制以支持异步处理

## 后续开发任务

- [ ] 实现外部OCR API调用模块
- [ ] 实现OCR结果回调接收接口
- [ ] 添加OCR结果验证和纠错机制
- [ ] 实现OCR处理队列管理
- [ ] 添加OCR处理监控和日志

