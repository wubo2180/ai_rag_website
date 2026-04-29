# 论文数据存储实现总结 - 三表方案

## ✅ 已完成的工作

### 1. 数据库表设计 ✅

创建了3张关系型数据表：

1. **`paper_articles`** - 论文文献表
   - 存储文献基本信息（编号、标题、性能趋势）
   - 关联文件和审核状态

2. **`paper_material_intermediates`** - 材料/中间体表（合并表）
   - 同时存储材料和中间体信息
   - 支持灵活的层级关系（parent_id）

3. **`paper_properties`** - 性能数据表
   - 存储各种性能测试数据
   - 关联到材料/中间体

**SQL文件**: `backend/migrations/create_paper_tables.sql`

---

### 2. SQLAlchemy 数据模型 ✅

创建了3个Python模型类：

1. **`PaperArticle`** (`backend/app/models/paper_article.py`)
   - 完整的ORM映射
   - `to_dict()` - 转换为字典
   - `to_hierarchical_dict()` - 转换为层次化JSON（符合前端格式）

2. **`PaperMaterialIntermediate`** (`backend/app/models/paper_material_intermediate.py`)
   - 材料和中间体的合并模型
   - 支持自关联（parent_id）

3. **`PaperProperty`** (`backend/app/models/paper_property.py`)
   - 性能数据模型
   - 冗余article_id字段优化查询

已在 `backend/app/models/__init__.py` 中注册

---

### 3. 服务层 ✅

创建了 **`PaperService`** (`backend/app/services/paper_service.py`)

**主要方法**：

```python
# 保存论文数据（从OCR结果）
save_paper_data(file_id, paper_data, user_id=None)

# 获取论文数据
get_paper_by_article_id(article_id, include_details=True)
get_paper_by_file_id(file_id, include_details=True)
get_paper_hierarchical_data(article_id)  # 返回JSON格式

# 更新论文数据
update_paper_data(article_id, paper_data, user_id=None)

# 删除论文数据
delete_paper(article_id)

# 审核管理
update_review_status(article_id, review_status, reviewer_id, review_comments)
```

**特性**：
- 完整的事务管理
- 详细的错误处理和日志
- 支持批量保存（材料→性能）
- 自动级联删除

---

### 4. API接口 ✅

创建了 **论文API** (`backend/app/api/papers.py`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/papers` | 创建论文数据 |
| GET | `/api/papers/<article_id>` | 获取论文（支持层次化格式） |
| GET | `/api/papers/by-file/<file_id>` | 根据文件ID获取论文 |
| PUT | `/api/papers/<article_id>` | 更新论文数据 |
| DELETE | `/api/papers/<article_id>` | 删除论文（管理员） |
| POST | `/api/papers/<article_id>/review` | 审核论文 |

已在 `backend/app/api/__init__.py` 中注册

---

### 5. 文档 ✅

创建了完整的文档：

- **`docs/PAPER_DATA_STORAGE_3TABLES.md`** - 详细的设计文档
  - 表结构说明
  - 数据存储示例
  - 常用查询示例
  - 性能优化建议
  - 与方案1对比

---

## 🚀 执行步骤

### 第1步：创建数据库表

```bash
# 连接到数据库
mysql -u root -p ocr_db

# 执行SQL脚本
source /home/h3c/workspace/IBoxTech-ocrchecker/backend/migrations/create_paper_tables.sql;

# 验证表创建
SHOW TABLES LIKE 'paper%';

# 查看示例数据
SELECT * FROM paper_articles;
SELECT * FROM paper_material_intermediates;
SELECT * FROM paper_properties;
```

**预期结果**：
- 3张表创建成功
- 有1条测试文献数据（A1）
- 有2条材料/中间体数据
- 有9条性能数据

---

### 第2步：重启后端服务

```bash
# 停止当前后端
ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}' | xargs kill

# 重新启动（查看是否有模型加载错误）
cd /home/h3c/workspace/IBoxTech-ocrchecker/backend
python app.py
```

**预期输出**：
```
 * Running on http://0.0.0.0:5000
 * Models loaded: ... PaperArticle, PaperMaterialIntermediate, PaperProperty ...
```

---

### 第3步：测试API

#### 3.1 创建论文数据

```bash
curl -X POST http://localhost:5000/api/papers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "file_id": 123,
    "article_id": "A2",
    "article_name": "测试论文标题",
    "performance_trend": "测试性能趋势",
    "hierarchical_data": [
      {
        "material_id": "A2M1",
        "material_name": "测试材料1",
        "cas_number": "123-45-6",
        "intermediate_id": "A2I1",
        "intermediate_name": "测试中间体1",
        "intermediate_composition": "A2I1:A2I2=1:1",
        "properties": [
          {
            "property_id": "A2P1",
            "property_name": "粘度 MPa·S",
            "property_value": "2000"
          }
        ]
      }
    ]
  }'
```

#### 3.2 获取论文数据（层次化格式）

```bash
curl -X GET "http://localhost:5000/api/papers/A2?format=hierarchical" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 3.3 根据文件ID获取论文

```bash
curl -X GET http://localhost:5000/api/papers/by-file/123 \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 📋 数据格式示例

### 输入格式（OCR结果 → API）

```json
{
  "file_id": 123,
  "article_id": "A1",
  "article_name": "双组分缩合型有机硅电子灌封胶的制备及其导热阻燃性能研究",
  "performance_trend": "1、添加γ－氨丙基三乙氧基硅烷缩短封灌胶表干时间...",
  "hierarchical_data": [
    {
      "material_id": "A1M1",
      "material_name": "α，ω－二羟基聚二甲基硅氧烷，黏度4000MPa·s",
      "cas_number": "",
      "intermediate_id": "A1I1",
      "intermediate_name": "A组分：107基础胶+α-氧化铝+氢氧化镁+二甲基硅油",
      "intermediate_composition": "A1I1：A1I2=10：1（质量比）",
      "properties": [
        {
          "property_id": "A1P1",
          "property_name": "粘度／黏度 MPa·S",
          "property_value": "1900"
        },
        {
          "property_id": "A1P2",
          "property_name": "热导率（Thermal Conductivity） W/(m·K)",
          "property_value": "0.826"
        }
      ]
    }
  ]
}
```

### 输出格式（API → 前端，层次化）

```json
{
  "success": true,
  "data": {
    "文献编号（Article ID）": "A1",
    "文献名称（Article Name）": "双组分缩合型...",
    "四级数据连接（4-level Data Linkage）": [
      {
        "材料编号（Material ID）": "A1M1",
        "原材料名称（Material Name）": "α，ω－二羟基聚二甲基硅氧烷...",
        "CAS号（CAS Number）": "",
        "中间体编号（Intermediate ID）": "A1I1",
        "中间体名称（Intermediate Name）": "A组分：...",
        "中间体组成（Intermediate Compositions）": "A1I1：A1I2=10：1",
        "性能（Properties）": [
          {
            "性能编号（Property ID）": "A1P1",
            "性能名称（Property Name）": "粘度／黏度 MPa·S",
            "性能值（Property Value）": "1900"
          }
        ]
      }
    ],
    "性能趋势": "..."
  }
}
```

---

## 🔧 常见问题排查

### 问题1：表创建失败

**症状**：`ERROR 1050: Table already exists`

**解决**：
```sql
-- 删除旧表
DROP TABLE IF EXISTS paper_properties;
DROP TABLE IF EXISTS paper_material_intermediates;
DROP TABLE IF EXISTS paper_articles;

-- 重新执行创建脚本
source /path/to/create_paper_tables.sql;
```

### 问题2：模型导入失败

**症状**：`ImportError: cannot import name 'PaperArticle'`

**解决**：
1. 检查文件路径是否正确
2. 检查 `__init__.py` 中的导入语句
3. 重启Python服务

### 问题3：外键约束失败

**症状**：`IntegrityError: Foreign key constraint fails`

**解决**：
- 确保 `file_id` 在 `files` 表中存在
- 确保 `article_id` 在插入子表前已在父表中创建

---

## 📊 下一步工作

### 1. 前端表单开发

创建 `PaperForm.vue` 组件：
- 支持层次化数据输入
- 材料/中间体动态添加
- 性能数据表格编辑

### 2. OCR集成

修改 OCR服务，将识别结果转换为论文数据格式：
```python
# 在 OCR 回调中
ocr_result = {...}  # OCR原始结果
paper_data = convert_ocr_to_paper_format(ocr_result)
paper_service.save_paper_data(file_id, paper_data)
```

### 3. 识别页面重构

让 `FileRecognize/index.vue` 根据文件类型显示对应表单：
- `commission` → CommissionForm
- `paper` → PaperForm

---

**创建日期**: 2025-11-06  
**状态**: ✅ 后端完成，待测试  
**下一步**: 执行SQL创建表 → 测试API → 前端集成



