# 数据库表创建SQL - 使用说明

## 📄 文件说明

已生成SQL文件：`backend/migrations/create_document_tables.sql`

包含以下内容：
1. ✅ `file_type_configs` 表创建语句
2. ✅ `document_basic` 表创建语句
3. ✅ 委托单类型配置初始化数据
4. ✅ 论文类型配置初始化数据

---

## 🗄️ 表结构说明

### 1. file_type_configs（文件类型配置表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键ID |
| type_code | VARCHAR(50) | 类型代码（唯一）：commission、paper |
| type_name | VARCHAR(100) | 类型名称：委托单、论文 |
| type_description | TEXT | 类型描述 |
| ocr_model_api | VARCHAR(200) | OCR模型API地址 |
| ocr_model_type | VARCHAR(50) | 模型类型：internal/external |
| ocr_config | JSON | OCR配置参数 |
| storage_table_basic | VARCHAR(100) | 基本信息存储表名 |
| storage_table_items | VARCHAR(100) | 子项目存储表名 |
| storage_table_details | VARCHAR(100) | 详情存储表名 |
| form_config | JSON | 表单配置（字段定义） |
| form_component | VARCHAR(200) | 前端表单组件路径 |
| field_mapping | JSON | 字段映射规则 |
| validation_rules | JSON | 数据验证规则 |
| is_active | TINYINT(1) | 是否启用 |
| sort_order | INT | 排序序号 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**索引：**
- PRIMARY KEY (id)
- UNIQUE KEY uk_type_code (type_code)
- KEY idx_is_active (is_active)
- KEY idx_sort_order (sort_order)

### 2. document_basic（通用文档数据表）

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | INT | 主键ID |
| file_id | INT | 文件ID（外键→files.id） |
| file_type_code | VARCHAR(50) | 文件类型代码（外键→file_type_configs.type_code） |
| document_number | VARCHAR(100) | 文档编号（唯一） |
| basic_data | JSON | 基本数据（JSON格式） |
| items_data | JSON | 子项目数据（JSON格式） |
| details_data | JSON | 详细数据（JSON格式） |
| ocr_raw_data | TEXT | OCR原始识别数据 |
| ocr_confidence | VARCHAR(10) | 平均置信度 |
| status | VARCHAR(20) | 文档状态 |
| review_status | VARCHAR(20) | 审核状态 |
| reviewer_id | INT | 审核人ID（外键→users.id） |
| reviewed_at | DATETIME | 审核时间 |
| review_comments | TEXT | 审核意见 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

**索引：**
- PRIMARY KEY (id)
- UNIQUE KEY uk_document_number (document_number)
- KEY idx_file_id (file_id)
- KEY idx_file_type_code (file_type_code)
- KEY idx_status (status)
- KEY idx_review_status (review_status)
- KEY idx_reviewer_id (reviewer_id)
- KEY idx_created_at (created_at)

**外键约束：**
- fk_document_file: file_id → files(id) ON DELETE CASCADE
- fk_document_file_type: file_type_code → file_type_configs(type_code) ON DELETE RESTRICT
- fk_document_reviewer: reviewer_id → users(id) ON DELETE SET NULL

---

## 📦 执行方式

### 方式1：直接执行SQL文件（推荐用于生产环境）

```bash
# 方式1-1: 命令行执行
mysql -u用户名 -p -D ocr_system < backend/migrations/create_document_tables.sql

# 方式1-2: MySQL命令行内执行
mysql> USE ocr_system;
mysql> SOURCE /path/to/backend/migrations/create_document_tables.sql;
```

### 方式2：Python脚本执行（推荐用于开发环境）

```bash
# 切换到backend目录
cd backend

# 执行迁移脚本
python migrations/create_document_tables.py
python migrations/create_paper_config.py
```

### 方式3：分步执行（用于调试）

```sql
-- 步骤1: 创建file_type_configs表
CREATE TABLE IF NOT EXISTS `file_type_configs` (...);

-- 步骤2: 创建document_basic表
CREATE TABLE IF NOT EXISTS `document_basic` (...);

-- 步骤3: 插入委托单配置
INSERT INTO `file_type_configs` (...) VALUES (...);

-- 步骤4: 插入论文配置
INSERT INTO `file_type_configs` (...) VALUES (...);
```

---

## ✅ 验证执行结果

### 1. 检查表是否创建成功

```sql
-- 查看表
SHOW TABLES LIKE 'file_type_configs';
SHOW TABLES LIKE 'document_basic';

-- 查看表结构
DESC file_type_configs;
DESC document_basic;
```

### 2. 检查初始化数据

```sql
-- 查看文件类型配置
SELECT 
    type_code,
    type_name,
    type_description,
    ocr_model_type,
    storage_table_basic,
    is_active,
    sort_order
FROM file_type_configs
ORDER BY sort_order;

-- 预期结果：
-- +-------------+-----------+------------------+----------------+----------------------+-----------+------------+
-- | type_code   | type_name | type_description | ocr_model_type | storage_table_basic  | is_active | sort_order |
-- +-------------+-----------+------------------+----------------+----------------------+-----------+------------+
-- | commission  | 委托单     | 检测委托测试申请单 | external       | commission_basic     |         1 |          1 |
-- | paper       | 论文      | 学术论文检测分析   | internal       | document_basic       |         1 |          2 |
-- +-------------+-----------+------------------+----------------+----------------------+-----------+------------+
```

### 3. 检查JSON字段内容

```sql
-- 查看委托单的form_config
SELECT 
    type_code,
    JSON_PRETTY(form_config) as form_config
FROM file_type_configs
WHERE type_code = 'commission';

-- 查看论文的form_config（查看表单字段数量）
SELECT 
    type_code,
    JSON_LENGTH(form_config->'$.sections') as section_count,
    JSON_LENGTH(form_config->'$.sections[0].fields') as first_section_fields
FROM file_type_configs
WHERE type_code = 'paper';
```

---

## 🔧 常见问题

### Q1: 执行SQL时报错：外键约束失败

**原因：** `files` 或 `users` 表不存在

**解决：** 确保已经创建了这些表，或者暂时注释掉外键约束：

```sql
-- 注释掉这些行：
-- CONSTRAINT `fk_document_file` FOREIGN KEY ...
-- CONSTRAINT `fk_document_file_type` FOREIGN KEY ...
-- CONSTRAINT `fk_document_reviewer` FOREIGN KEY ...
```

### Q2: JSON字段插入失败

**原因：** MySQL版本过低（需要5.7.8+）

**解决：** 升级MySQL版本或将JSON字段改为TEXT类型

### Q3: 中文显示乱码

**原因：** 字符集设置不正确

**解决：** 确保使用 utf8mb4 字符集：

```sql
ALTER TABLE file_type_configs CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE document_basic CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 📊 数据示例

### 委托单配置（commission）

```json
{
  "type_code": "commission",
  "storage_table_basic": "commission_basic",
  "storage_table_items": "test_items",
  "storage_table_details": "special_tests",
  "form_component": "CommissionForm",
  "use_dynamic_form": false
}
```

### 论文配置（paper）

```json
{
  "type_code": "paper",
  "storage_table_basic": "document_basic",
  "form_config": {
    "use_dynamic_form": true,
    "sections": [
      {"title": "基本信息", "fields": [...]},
      {"title": "作者信息", "fields": [...]},
      {"title": "发表信息", "fields": [...]},
      {"title": "内容信息", "fields": [...]},
      {"title": "质量评估", "fields": [...]},
      {"title": "备注信息", "fields": [...]}
    ]
  }
}
```

---

## 🎯 下一步

执行完SQL后，可以：

1. ✅ 通过API测试配置：`GET /api/file-type-configs`
2. ✅ 测试文档识别：`POST /api/documents/recognize`
3. ✅ 在前端集成动态表单组件
4. ✅ 端到端测试完整流程

---

**文件位置：** `backend/migrations/create_document_tables.sql`  
**生成时间：** 2025-11-05  
**字符集：** utf8mb4  
**引擎：** InnoDB


