# 论文删除功能说明和优化

## 功能位置

按照用户建议，**删除功能和保存功能在同一个文件和类中**：

**文件：** `backend/app/services/paper_service.py`  
**类：** `PaperService`

### PaperService 类的所有方法

| 方法名 | 功能 | 类型 |
|--------|------|------|
| `save_paper_data()` | 保存论文数据 | 写操作 |
| `get_paper_by_article_id()` | 根据文献编号获取数据 | 读操作 |
| `get_paper_by_file_id()` | 根据文件ID获取数据 | 读操作 |
| `get_paper_hierarchical_data()` | 获取层次化数据 | 读操作 |
| `get_paper_hierarchical_data_by_file_id()` | 根据文件ID获取层次化数据 | 读操作 |
| `update_paper_data()` | 更新论文数据 | 写操作 |
| **`delete_paper()`** | **删除论文数据** | **写操作** |
| `update_review_status()` | 更新审核状态 | 写操作 |

✅ 所有数据操作（CRUD）都在同一个类中，符合单一职责原则。

## 级联删除机制

### 数据库关系

```
PaperArticle (文献)
  │
  ├─ material_intermediates → PaperMaterialIntermediate (材料/中间体)
  │                              │
  │                              └─ properties → PaperProperty (性能数据)
  │
  └─ properties → PaperProperty (性能数据)
```

### 级联删除配置

#### 1. PaperArticle → PaperMaterialIntermediate

**文件：** `backend/app/models/paper_article.py` (第48-51行)

```python
material_intermediates = relationship('PaperMaterialIntermediate', 
                                     backref='article', 
                                     lazy='dynamic',
                                     cascade='all, delete-orphan')
```

#### 2. PaperArticle → PaperProperty

**文件：** `backend/app/models/paper_article.py` (第52-55行)

```python
properties = relationship('PaperProperty', 
                         backref='article', 
                         lazy='dynamic',
                         cascade='all, delete-orphan')
```

#### 3. PaperMaterialIntermediate → PaperProperty

**文件：** `backend/app/models/paper_material_intermediate.py` (第60-64行)

```python
properties = relationship('PaperProperty', 
                         backref='material_intermediate', 
                         lazy='dynamic',
                         cascade='all, delete-orphan',
                         foreign_keys='PaperProperty.material_intermediate_id')
```

### Cascade 选项说明

- **`all`**: 所有操作都级联（包括 save, merge, delete, etc.）
- **`delete-orphan`**: 当子对象不再关联到父对象时自动删除

这意味着：
- ✅ 删除 `PaperArticle` → 自动删除所有 `PaperMaterialIntermediate`
- ✅ 删除 `PaperMaterialIntermediate` → 自动删除关联的 `PaperProperty`
- ✅ 一次删除操作，清理所有相关数据

## 删除方法实现

### 完整代码

**文件：** `backend/app/services/paper_service.py`

```python
def delete_paper(self, article_id):
    """
    删除论文数据（级联删除材料和性能数据）
    
    级联删除顺序：
    1. PaperArticle (文献记录)
    2. └─ PaperMaterialIntermediate (材料/中间体) [自动级联]
    3.    └─ PaperProperty (性能数据) [自动级联]
    
    Args:
        article_id: 文献编号
    
    Returns:
        dict: {
            'success': bool,
            'message': str
        }
    """
    try:
        logger.info(f"[PaperService] 开始删除论文数据: {article_id}")
        
        # 1. 查找文献记录
        article = PaperArticle.query.filter_by(article_id=article_id).first()
        
        if not article:
            logger.warning(f"[PaperService] 文献不存在: {article_id}")
            return {
                'success': False,
                'message': f'文献编号 {article_id} 不存在'
            }
        
        # 2. 统计关联数据（用于日志）
        material_count = article.material_intermediates.count()
        property_count = article.properties.count()
        
        logger.info(f"[PaperService] 文献 {article_id} 关联数据统计:")
        logger.info(f"  - 材料/中间体: {material_count} 条")
        logger.info(f"  - 性能数据: {property_count} 条")
        
        # 3. 删除文献记录（级联删除关联数据）
        db.session.delete(article)
        db.session.commit()
        
        logger.info(f"[PaperService] 论文数据已删除: {article_id}")
        logger.info(f"[PaperService] 级联删除了 {material_count} 条材料/中间体记录")
        logger.info(f"[PaperService] 级联删除了 {property_count} 条性能数据记录")
        
        return {
            'success': True,
            'message': f'论文数据已删除（包含 {material_count} 条材料/中间体和 {property_count} 条性能数据）'
        }
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"[PaperService] 删除论文数据失败: {str(e)}", exc_info=True)
        return {
            'success': False,
            'message': f'删除失败：{str(e)}'
        }
```

### 优化内容

#### 1. 详细的日志输出

删除前记录关联数据的数量：
```python
material_count = article.material_intermediates.count()
property_count = article.properties.count()

logger.info(f"[PaperService] 文献 {article_id} 关联数据统计:")
logger.info(f"  - 材料/中间体: {material_count} 条")
logger.info(f"  - 性能数据: {property_count} 条")
```

删除后确认：
```python
logger.info(f"[PaperService] 级联删除了 {material_count} 条材料/中间体记录")
logger.info(f"[PaperService] 级联删除了 {property_count} 条性能数据记录")
```

#### 2. 清晰的文档注释

说明级联删除的顺序和机制：
```python
"""
删除论文数据（级联删除材料和性能数据）

级联删除顺序：
1. PaperArticle (文献记录)
2. └─ PaperMaterialIntermediate (材料/中间体) [自动级联]
3.    └─ PaperProperty (性能数据) [自动级联]
"""
```

#### 3. 友好的返回消息

返回时包含删除的数据统计：
```python
return {
    'success': True,
    'message': f'论文数据已删除（包含 {material_count} 条材料/中间体和 {property_count} 条性能数据）'
}
```

## 调用方式

### API 端点

**文件：** `backend/app/api/papers.py`

```python
@api_bp.route('/papers/<article_id>', methods=['DELETE'])
@jwt_required()
def delete_paper(article_id):
    """删除论文数据"""
    try:
        # 权限检查：只有管理员可以删除
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin():
            return jsonify({
                'success': False,
                'message': '权限不足：只有管理员可以删除论文数据'
            }), 403
        
        paper_service = PaperService()
        result = paper_service.delete_paper(article_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
    
    except Exception as e:
        logger.error(f"删除论文数据失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500
```

### 权限控制

- ✅ 需要登录（`@jwt_required()`）
- ✅ 只有管理员可以删除（`@admin_required` 或手动检查）

## 日志输出示例

### 成功删除

```
[INFO] [PaperService] 开始删除论文数据: A2
[INFO] [PaperService] 文献 A2 关联数据统计:
[INFO]   - 材料/中间体: 3 条
[INFO]   - 性能数据: 8 条
[INFO] [PaperService] 论文数据已删除: A2
[INFO] [PaperService] 级联删除了 3 条材料/中间体记录
[INFO] [PaperService] 级联删除了 8 条性能数据记录
```

### 文献不存在

```
[INFO] [PaperService] 开始删除论文数据: A99
[WARNING] [PaperService] 文献不存在: A99
```

### 删除失败

```
[INFO] [PaperService] 开始删除论文数据: A2
[INFO] [PaperService] 文献 A2 关联数据统计:
[INFO]   - 材料/中间体: 3 条
[INFO]   - 性能数据: 8 条
[ERROR] [PaperService] 删除论文数据失败: (IntegrityError) ...
```

## SQL 验证

### 删除前查询

```sql
-- 查看文献及其关联数据
SELECT 
    pa.article_id,
    pa.article_name,
    COUNT(DISTINCT pmi.id) as material_count,
    COUNT(DISTINCT pp.id) as property_count
FROM paper_articles pa
LEFT JOIN paper_material_intermediates pmi ON pa.article_id = pmi.article_id
LEFT JOIN paper_properties pp ON pa.article_id = pp.article_id
WHERE pa.article_id = 'A2'
GROUP BY pa.article_id;
```

### 删除操作

```python
paper_service = PaperService()
result = paper_service.delete_paper('A2')
```

### 删除后验证

```sql
-- 验证文献已删除
SELECT * FROM paper_articles WHERE article_id = 'A2';
-- 结果：0 rows

-- 验证材料/中间体已删除
SELECT * FROM paper_material_intermediates WHERE article_id = 'A2';
-- 结果：0 rows

-- 验证性能数据已删除
SELECT * FROM paper_properties WHERE article_id = 'A2';
-- 结果：0 rows
```

## 测试用例

### 测试 1：正常删除

```python
# 前置条件：文献 A2 存在，有 3 条材料和 8 条性能数据
result = paper_service.delete_paper('A2')

# 预期结果
assert result['success'] == True
assert '3 条材料/中间体' in result['message']
assert '8 条性能数据' in result['message']
```

### 测试 2：删除不存在的文献

```python
result = paper_service.delete_paper('A999')

# 预期结果
assert result['success'] == False
assert '不存在' in result['message']
```

### 测试 3：级联删除验证

```python
# 删除前
article = PaperArticle.query.filter_by(article_id='A2').first()
assert article is not None
assert article.material_intermediates.count() > 0
assert article.properties.count() > 0

# 执行删除
result = paper_service.delete_paper('A2')
assert result['success'] == True

# 删除后
article = PaperArticle.query.filter_by(article_id='A2').first()
assert article is None  # 文献已删除

# 验证关联数据也被删除
materials = PaperMaterialIntermediate.query.filter_by(article_id='A2').all()
assert len(materials) == 0  # 材料已删除

properties = PaperProperty.query.filter_by(article_id='A2').all()
assert len(properties) == 0  # 性能数据已删除
```

## 数据一致性保证

### 事务回滚

如果删除过程中发生错误，事务会回滚：

```python
except Exception as e:
    db.session.rollback()  # 回滚所有更改
    logger.error(f"[PaperService] 删除论文数据失败: {str(e)}", exc_info=True)
    return {
        'success': False,
        'message': f'删除失败：{str(e)}'
    }
```

这确保数据库始终处于一致状态。

## 相关文件

- **服务类：** `backend/app/services/paper_service.py`
- **API 端点：** `backend/app/api/papers.py`
- **数据模型：**
  - `backend/app/models/paper_article.py`
  - `backend/app/models/paper_material_intermediate.py`
  - `backend/app/models/paper_property.py`

## 总结

✅ **保存和删除功能在同一个类中**（`PaperService`），便于维护  
✅ **使用数据库级联删除**，无需手动删除关联数据  
✅ **详细的日志输出**，方便调试和审计  
✅ **事务保护**，确保数据一致性  
✅ **权限控制**，只有管理员可以删除  
✅ **友好的返回消息**，包含删除的数据统计

---

**文档时间：** 2025-11-12  
**功能状态：** ✅ 已实现并优化  
**符合用户建议：** ✅ 删除和保存在同一个类中











