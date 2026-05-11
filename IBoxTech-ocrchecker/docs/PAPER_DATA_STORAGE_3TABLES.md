# 论文数据存储方案 - 三表关系型结构

## 📊 表结构设计

### 总体架构

```
paper_articles (文献表)
    ├── file_id → files.id
    ├── article_id (PK, 如: A1)
    └── article_name
    
paper_material_intermediates (材料/中间体表)
    ├── article_id → paper_articles.article_id
    ├── material_id (PK, 如: A1M1)
    ├── material_name, cas_number
    ├── intermediate_id (如: A1I1)
    ├── intermediate_name, intermediate_composition
    └── parent_id (自关联，可选)
    
paper_properties (性能表)
    ├── material_intermediate_id → paper_material_intermediates.id
    ├── article_id → paper_articles.article_id
    ├── property_id (PK, 如: A1P1)
    ├── property_name
    └── property_value
```

---

## 🎯 设计亮点

### 1. **材料和中间体合并到一张表**

**理由**：
- 它们都是文献的"实体"，只是类型不同
- 共享大部分字段（编号、名称、描述）
- 避免多表JOIN，提高查询性能

**实现方式**：
- 用 `entity_type` 字段区分类型（`material` / `intermediate`）
- 材料字段：`material_id`, `material_name`, `cas_number`
- 中间体字段：`intermediate_id`, `intermediate_name`, `intermediate_composition`
- 一条记录可以同时包含材料和中间体信息（如您的数据结构）

### 2. **支持灵活的层级关系**

**parent_id 字段用途**：
- 可以表示材料和中间体之间的从属关系
- 可以表示中间体之间的组合关系
- 可选字段，不强制使用

**示例**：
```sql
-- 材料 A1M1 属于中间体 A1I1
material (A1M1) → parent_id = A1I1_record_id

-- 或者扁平化存储（不使用parent_id）
material (A1M1) + intermediate (A1I1) → 同一条记录
```

### 3. **冗余字段优化查询**

`paper_properties` 表中的 `article_id`：
- 虽然可以通过 `material_intermediate_id` → `article_id` 两次JOIN获取
- 但直接存储可以减少JOIN，提高性能
- 适合"按文献查询所有性能"的常见场景

---

## 📝 数据存储示例

### 您的原始数据

```json
{
  "文献编号": "A1",
  "文献名称": "双组分缩合型有机硅电子灌封胶...",
  "四级数据连接": [
    {
      "材料编号": "A1M1",
      "原材料名称": "α，ω－二羟基聚二甲基硅氧烷...",
      "中间体编号": "A1I1",
      "中间体名称": "A组分：107基础胶+...",
      "性能": [
        {"性能编号": "A1P1", "性能名称": "粘度", "性能值": "1900"}
      ]
    }
  ]
}
```

### 存储到数据库

#### Table 1: `paper_articles`

| id | file_id | article_id | article_name | performance_trend |
|----|---------|------------|--------------|-------------------|
| 1  | 123     | A1         | 双组分缩合型有机硅... | 1、添加γ－氨丙基... |

#### Table 2: `paper_material_intermediates`

| id | article_id | material_id | material_name | cas_number | intermediate_id | intermediate_name | intermediate_composition | sort_order |
|----|------------|-------------|---------------|------------|-----------------|-------------------|--------------------------|------------|
| 1  | A1         | A1M1        | α，ω－二羟基... | ""         | A1I1            | A组分：107基础胶... | A1I1：A1I2=10：1 | 1 |
| 2  | A1         | A1M2        | α－氧化铝... | 1344-28-1  | A1I2            | B组分：甲基三甲氧基... | A1I1：A1I2=10：1 | 2 |

#### Table 3: `paper_properties`

| id | material_intermediate_id | article_id | property_id | property_name | property_value | sort_order |
|----|--------------------------|------------|-------------|---------------|----------------|------------|
| 1  | 1                        | A1         | A1P1        | 粘度 MPa·S    | 1900           | 1 |
| 2  | 1                        | A1         | A1P2        | 热导率 W/(m·K) | 0.826          | 2 |
| 3  | 1                        | A1         | A1P4        | 拉伸强度 MPa  | 0.73           | 4 |
| 8  | 2                        | A1         | A1P8        | 粘度 MPa·S    | ""             | 8 |

---

## 🔍 常用查询示例

### 1. 获取完整的文献数据（所有层级）

```sql
SELECT 
  a.article_id,
  a.article_name,
  mi.material_id,
  mi.material_name,
  mi.intermediate_id,
  mi.intermediate_name,
  p.property_id,
  p.property_name,
  p.property_value
FROM paper_articles a
LEFT JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
LEFT JOIN paper_properties p ON mi.id = p.material_intermediate_id
WHERE a.article_id = 'A1'
ORDER BY mi.sort_order, p.sort_order;
```

### 2. 搜索包含特定材料的文献

```sql
SELECT 
  a.article_id,
  a.article_name,
  mi.material_name,
  mi.cas_number
FROM paper_articles a
JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
WHERE mi.material_name LIKE '%氧化铝%';
```

### 3. 搜索特定性能数据

```sql
SELECT 
  a.article_name,
  mi.material_name,
  p.property_name,
  p.property_value
FROM paper_articles a
JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
JOIN paper_properties p ON mi.id = p.material_intermediate_id
WHERE p.property_name LIKE '%热导率%'
  AND p.property_value != '';
```

### 4. 统计分析

```sql
-- 统计每篇文献的材料数和性能测试数
SELECT 
  a.article_id,
  a.article_name,
  COUNT(DISTINCT mi.id) AS material_count,
  COUNT(DISTINCT p.id) AS property_count
FROM paper_articles a
LEFT JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
LEFT JOIN paper_properties p ON mi.id = p.material_intermediate_id
GROUP BY a.article_id;

-- 统计最常测试的性能类型
SELECT 
  p.property_name,
  COUNT(*) AS test_count,
  COUNT(CASE WHEN p.property_value != '' THEN 1 END) AS has_value_count
FROM paper_properties p
GROUP BY p.property_name
ORDER BY test_count DESC;
```

---

## ⚡ 性能优化

### 已创建的索引

```sql
-- paper_articles
- PRIMARY KEY (id)
- UNIQUE KEY uk_article_id (article_id)
- KEY idx_file_id (file_id)

-- paper_material_intermediates
- PRIMARY KEY (id)
- UNIQUE KEY uk_material_id (material_id)
- KEY idx_article_id (article_id)
- KEY idx_intermediate_id (intermediate_id)

-- paper_properties
- PRIMARY KEY (id)
- UNIQUE KEY uk_property_id (property_id)
- KEY idx_material_intermediate_id (material_intermediate_id)
- KEY idx_article_id (article_id)
```

### 可选优化

```sql
-- 1. 全文搜索（如果需要模糊搜索文献标题）
ALTER TABLE paper_articles 
ADD FULLTEXT INDEX ft_article_name (article_name);

-- 2. CAS号唯一索引（如果CAS号不重复）
ALTER TABLE paper_material_intermediates 
ADD UNIQUE INDEX uk_cas_number (cas_number);

-- 3. 复合索引（优化常见的联合查询）
CREATE INDEX idx_article_material 
ON paper_material_intermediates (article_id, material_id);

CREATE INDEX idx_article_property 
ON paper_properties (article_id, property_name);
```

---

## 🔄 与通用表的集成

### 在 `file_type_configs` 中配置

```sql
UPDATE file_type_configs
SET 
  storage_table_basic = 'paper_articles',
  storage_table_items = 'paper_material_intermediates',
  storage_table_details = 'paper_properties'
WHERE type_code = 'paper';
```

### 在代码中的使用

```python
# backend/app/services/paper_service.py

class PaperService:
    """论文数据处理服务"""
    
    def save_paper_data(self, file_id, ocr_result):
        """保存OCR识别的论文数据到关系型表"""
        
        # 1. 保存文献基本信息
        article = PaperArticle(
            file_id=file_id,
            article_id=ocr_result['article_id'],
            article_name=ocr_result['article_name'],
            performance_trend=ocr_result.get('performance_trend')
        )
        db.session.add(article)
        db.session.flush()  # 获取 article.id
        
        # 2. 保存材料/中间体
        for idx, item in enumerate(ocr_result['hierarchical_data']):
            mi = PaperMaterialIntermediate(
                article_id=article.article_id,
                material_id=item['material_id'],
                material_name=item['material_name'],
                cas_number=item.get('cas_number'),
                intermediate_id=item.get('intermediate_id'),
                intermediate_name=item.get('intermediate_name'),
                intermediate_composition=item.get('intermediate_composition'),
                sort_order=idx + 1
            )
            db.session.add(mi)
            db.session.flush()  # 获取 mi.id
            
            # 3. 保存性能数据
            for p_idx, prop in enumerate(item.get('properties', [])):
                property_record = PaperProperty(
                    material_intermediate_id=mi.id,
                    article_id=article.article_id,
                    property_id=prop['property_id'],
                    property_name=prop['property_name'],
                    property_value=prop.get('property_value', ''),
                    sort_order=p_idx + 1
                )
                db.session.add(property_record)
        
        db.session.commit()
        return article.to_dict()
```

---

## 📋 与方案1（JSON）的对比

| 特性 | 方案1 (JSON) | 方案2 (3表关系型) |
|------|--------------|------------------|
| **查询性能** | ⚠️ 较慢（需要JSON函数） | ✅ 快速（索引优化） |
| **复杂查询** | ⚠️ 困难 | ✅ 简单（SQL JOIN） |
| **灵活性** | ✅ 高（结构可变） | ⚠️ 低（需要改表） |
| **数据完整性** | ⚠️ 应用层控制 | ✅ 数据库约束 |
| **开发工作量** | ✅ 小 | ⚠️ 大 |
| **适合场景** | 结构变化频繁 | 结构稳定、查询多 |

---

## 🚀 下一步

1. **执行SQL脚本创建表**：
   ```bash
   mysql -u root -p ocr_db < backend/migrations/create_paper_tables.sql
   ```

2. **创建SQLAlchemy模型**：
   - `backend/app/models/paper_article.py`
   - `backend/app/models/paper_material_intermediate.py`
   - `backend/app/models/paper_property.py`

3. **创建服务层**：
   - `backend/app/services/paper_service.py`

4. **创建API接口**：
   - `backend/app/api/papers.py`

5. **更新前端表单**：
   - 支持嵌套表格（材料-性能）

---

**创建日期**: 2025-11-06  
**表结构版本**: v1.0  
**状态**: ✅ 设计完成，待实现



