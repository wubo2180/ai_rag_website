# JSON字段与数据库字段对应说明

## 📋 概述

本文档详细说明了OCR提取的JSON字段如何映射到数据库表的字段。

- **源数据格式**: JSON（来自OCR结果的 `6.3_field_extraction_results.json`）
- **目标数据库表**: `commission_basic` (委托单基本信息表)
- **映射逻辑**: `backend/app/services/commission_direct_import_service.py`

---

## 🗂️ 字段映射表

### 1️⃣ 基本标识信息

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 表格编号 | `form_number` | String(50) | ✅ 是 | 表格编号（允许重复） |
| 委托编号 | `commission_number` | String(50) | ✅ 是 | **委托编号（唯一）** |
| 服务类型 | `service_type` | String(20) | ❌ 否 | 如：检测、校准等 |
| 是否需要报告 | `need_report` | String(10) | ❌ 否 | 如：是、否 |

**重要说明**：
- `commission_number` 是唯一索引，导入时会检查是否重复
- `form_number` 允许重复（同一表格可能有多页）

---

### 2️⃣ 委托信息

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 委托部门 | `commission_department` | String(50) | ❌ 否 | 委托单位/部门名称 |
| 委托人 | `commissioner` | String(30) | ❌ 否 | 委托人姓名 |
| 委托日期 | `commission_date` | Date | ❌ 否 | 日期格式（会自动解析） |
| 委托地址 | `commission_address` | String(200) | ❌ 否 | 委托单位地址 |

**日期解析支持格式**：
- `YYYY-MM-DD` (如：2023-06-25)
- `YYYY/MM/DD` (如：2023/06/25)
- `YYYY年MM月DD日` (如：2023年6月25日)
- `YYYYMMDD` (如：20230625)

---

### 3️⃣ 样品信息

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 样品名称 | `sample_name` | String(100) | ❌ 否 | 被测样品名称 |
| 样品数量 | `sample_quantity` | String(50) | ❌ 否 | 样品数量（字符串，如"3件"） |
| 样品代码 | `sample_code` | String(50) | ❌ 否 | 样品编码 |
| 样品批次 | `sample_batch` | String(50) | ❌ 否 | 样品批次号 |
| 样品批号 | `sample_batch` | String(50) | ❌ 否 | **同"样品批次"** |
| 送样时间 | `delivery_time` | DateTime | ❌ 否 | 样品送达时间 |
| 需求时间 | `required_time` | Date | ❌ 否 | 报告需求完成日期 |
| 余样处理 | `sample_disposal` | String(20) | ❌ 否 | 如：退样、销毁 |
| 样品储存方式 | `storage_method` | String(50) | ❌ 否 | 如：常温、冷藏 |

**注意**：
- `样品批次` 和 `样品批号` 映射到同一个数据库字段 `sample_batch`
- `送样时间` 为DateTime类型（日期+时间）
- `需求时间` 为Date类型（仅日期）

---

### 4️⃣ 测试信息

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 测试性质 | `test_nature` | String(50) | ❌ 否 | 如：委托测试、预约测试 |
| 测试说明 | `test_description` | Text | ❌ 否 | 测试详细说明 |
| 有无特殊条件 | `special_condition_flag` | String(10) | ❌ 否 | 是/否（布尔字段） |
| 条件详情 | `special_condition_detail` | String(200) | ❌ 否 | 特殊条件详细描述 |
| 特殊条件 | `special_condition_detail` | String(200) | ❌ 否 | **同"条件详情"** |

**布尔值解析**：
- ✅ **是**: `是`, `yes`, `y`, `1`, `true`, `√`, `✓`
- ❌ **否**: `否`, `no`, `n`, `0`, `false`, `×`, `✗`

---

### 5️⃣ 人员信息（手写识别字段）

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 测试员 | `tester` | String(30) | ❌ 否 | 测试人员姓名 |
| 数据复核人 | `data_reviewer` | String(30) | ❌ 否 | 数据复核人员姓名 |
| 复核日期 | `review_date` | Date | ❌ 否 | 数据复核日期 |

---

### 6️⃣ 审核检查项（单选字段）

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 申请单是否填写完整 | `form_complete` | String(10) | ❌ 否 | 是/否 |
| 样品实物信息是否一致 | `sample_info_consistent` | String(10) | ❌ 否 | 是/否 |
| 样品是否完好 | `sample_condition_ok` | String(10) | ❌ 否 | 是/否 |
| 其他 | `other_notes` | String(200) | ❌ 否 | 其他备注信息 |

---

### 7️⃣ 签名信息（手写识别字段）

| JSON字段名 | 数据库字段名 | 字段类型 | 是否必填 | 说明 |
|-----------|-------------|---------|---------|------|
| 送样人签名 | `delivery_person_signature` | String(100) | ❌ 否 | 送样人签名及日期 |
| 业务受理人签字 | `business_receiver_signature` | String(100) | ❌ 否 | 业务受理人签字及日期 |

---

### 8️⃣ 系统自动字段

| 字段名 | 字段类型 | 说明 |
|-------|---------|------|
| `id` | Integer | 主键ID（自增） |
| `created_at` | DateTime | 创建时间（自动填充） |
| `updated_at` | DateTime | 更新时间（自动更新） |

---

## 🔄 数据转换规则

### 日期类型转换

**支持的日期格式**：
```
2023-06-25
2023/06/25
20230625
2023年6月25日
2023年06月25日
```

**转换逻辑**：
- 自动识别并解析为标准日期格式
- 解析失败时值为 `NULL`

### 布尔类型转换

**"是"的表示**：
```
是, yes, y, 1, true, √, ✓
```

**"否"的表示**：
```
否, no, n, 0, false, ×, ✗
```

**转换结果**：
- 存储为字符串 `"是"` 或 `"否"`
- 其他值保持原样

### 字符串清理

所有字符串字段会自动：
1. 去除首尾空白
2. 压缩中间连续空白为单个空格
3. 如果为空，存储为 `NULL`

---

## 📊 完整映射示例

### JSON输入示例

```json
{
  "extracted_fields": {
    "委托编号": {
      "value": "IBTC20230625008",
      "type": "single_field"
    },
    "委托人": {
      "value": "饶毅",
      "type": "single_field"
    },
    "委托日期": {
      "value": "2023年6月25日",
      "type": "single_field"
    },
    "样品名称": {
      "value": "塑料原料",
      "type": "single_field"
    },
    "样品数量": {
      "value": "5件",
      "type": "single_field"
    },
    "测试性质": {
      "value": "委托测试",
      "type": "single_field"
    },
    "是否需要报告": {
      "value": "是",
      "type": "choice_field"
    }
  }
}
```

### 数据库存储结果

```sql
INSERT INTO commission_basic (
    commission_number,
    commissioner,
    commission_date,
    sample_name,
    sample_quantity,
    test_nature,
    need_report,
    created_at,
    updated_at
) VALUES (
    'IBTC20230625008',      -- 委托编号
    '饶毅',                  -- 委托人
    '2023-06-25',            -- 委托日期（已转换）
    '塑料原料',              -- 样品名称
    '5件',                   -- 样品数量
    '委托测试',              -- 测试性质
    '是',                    -- 是否需要报告
    NOW(),                   -- 创建时间
    NOW()                    -- 更新时间
);
```

---

## 🔍 JSON文件位置

OCR处理后的JSON文件路径格式：
```
{json_base_dir}/
└── multi_page_results/
    └── {pdf_filename_without_ext}/
        ├── page_1_results/
        │   └── steps/
        │       └── step06/
        │           └── 6.3_field_extraction_results.json  ⬅️ 提取这个文件
        ├── page_2_results/
        │   └── steps/
        │       └── step06/
        │           └── 6.3_field_extraction_results.json
        └── ...
```

**多页处理规则**：
- 如果同一字段在多个页面都有值，优先使用**非空值**
- 如果多个页面有不同的非空值，使用**第一个遇到的值**

---

## ⚠️ 重要注意事项

### 1. 唯一性约束

**`commission_number`（委托编号）必须唯一**：
- 导入前会检查是否已存在
- 如果已存在，返回错误：`委托编号 XXX 已存在`
- 建议在前端做好去重检查

### 2. 必填字段

虽然数据库层面只有 `form_number` 和 `commission_number` 是必填，但建议确保以下字段有值：
- ✅ **委托编号** (`commission_number`) - 唯一标识
- ✅ **表格编号** (`form_number`) - 业务编号
- 📝 **委托人** (`commissioner`) - 便于追溯
- 📝 **样品名称** (`sample_name`) - 业务关键信息

### 3. 字段长度限制

请注意以下字段的最大长度：
- 短文本字段 (10-50字符): 姓名、编号、类型等
- 中等文本字段 (100-200字符): 地址、描述等
- 长文本字段 (Text): `test_description` 无限制

超长内容会被截断！

### 4. 数据类型转换失败

如果日期、布尔值转换失败：
- 不会报错，字段值为 `NULL`
- 建议检查OCR识别质量

---

## 🛠️ 使用代码示例

### Python调用示例

```python
from services.commission_direct_import_service import CommissionDirectImportService

# 创建导入服务
service = CommissionDirectImportService()

# 导入单个PDF
result = service.import_single_pdf(
    pdf_path='/path/to/your.pdf',
    json_base_dir='/path/to/json_output'
)

if result['success']:
    print(f"✅ 导入成功!")
    print(f"   委托编号: {result['commission_number']}")
    print(f"   委托单ID: {result['commission_id']}")
    print(f"   提取字段数: {result['extracted_fields']}")
else:
    print(f"❌ 导入失败: {result['message']}")
```

### API调用示例

```bash
# 单个文件导入
curl -X POST http://localhost:5001/api/commissions/import/single \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "pdf_path": "/path/to/your.pdf",
    "json_base_dir": "/path/to/json_output"
  }'

# 响应示例
{
  "success": true,
  "message": "导入成功",
  "commission_number": "IBTC20230625008",
  "commission_id": 8,
  "pdf_filename": "测试中心品质部原材料委托单（OA) 2023年6月_第44页2.pdf",
  "extracted_fields": 13
}
```

---

## 📝 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2025-10-14 | 初始版本，完成基本字段映射 |

---

## 📞 技术支持

如有疑问，请查看：
- 导入服务实现: `backend/app/services/commission_direct_import_service.py`
- 数据模型定义: `backend/app/models/commission.py`
- API接口定义: `backend/app/api/commission.py`



