# 论文OCR新格式适配修复报告

## 问题描述

论文OCR服务返回的数据结构发生了变化，导致 `PaperAdapter` 无法正确解析，出现"缺少文献编号、缺少文献名称"的错误。

## 根本原因

### 1. 数据结构变化

**旧格式（扁平结构）：**
```json
{
  "文献编号": "A1",
  "文献名称": "...",
  "四级数据连接": [
    {
      "材料编号": "A1M1",
      "原材料名称": "...",
      "中间体编号": "A1I1",
      "性能": [...]
    }
  ]
}
```

**新格式（嵌套结构 + 双语字段名）：**
```json
{
  "文献": {
    "文献编号（Article ID）": "A2",
    "文献名称（Article Name）": "...",
    "四级数据连接（4-level Data Linkage）": [
      {
        "原材料（Materials）": {
          "材料编号（Material ID）": "A2M1",
          "原材料名称（Material Name）": "...",
          "CAS号（CAS Number）": ""
        },
        "中间体（Intermediates）": {
          "中间体编号（Intermediate ID）": "A2I1",
          "中间体名称（Intermediate Name）": "..."
        },
        "中间体组成（Intermediate Compositions）": "...",
        "性能（Properties）": [
          {
            "性能编号（Property ID）": "A2P1",
            "性能名称（Property Name）": "...",
            "性能值（Property Value）": "..."
          }
        ]
      }
    ],
    "性能趋势": "..."
  }
}
```

### 2. Markdown 代码块标记

OCR服务返回的 `text` 字段包含了 markdown 代码块标记：

```
"text": "```json\n{\n  \"文献\": {...}\n}\n```"
```

这导致 JSON 解析失败。

## 解决方案

### 修改文件

**文件：** `backend/app/adapters/paper_adapter.py`

### 1. 添加 Markdown 清理方法

```python
def _clean_markdown_code_block(self, text: str) -> str:
    """
    清理markdown代码块标记
    
    例如:
    ```json
    {"文献": {...}}
    ```
    
    转换为:
    {"文献": {...}}
    """
    import re
    
    text = text.strip()
    
    # 去除开头的 ```json 或 ``` 标记（可能带换行）
    text = re.sub(r'^```(?:json)?\s*\n?', '', text)
    
    # 去除结尾的 ``` 标记（可能带换行）
    text = re.sub(r'\n?```\s*$', '', text)
    
    return text.strip()
```

### 2. 更新解析逻辑

在 `parse_ocr_result` 方法中，解析 `text` 字段前先清理 markdown 标记：

```python
elif isinstance(text_output, str):
    # 清理可能的markdown代码块标记
    cleaned_text = self._clean_markdown_code_block(text_output)
    if cleaned_text != text_output:
        self.log_info("✂️ 检测到并清理了markdown代码块标记")
        self.log_info(f"清理前长度: {len(text_output)}, 清理后长度: {len(cleaned_text)}")
    
    parsed_output = json.loads(cleaned_text)
    self.log_info("✅ 成功解析JSON字符串")
```

### 3. 重构 `_extract_from_dict` 方法

支持多种字段名格式（双语字段名）：

```python
def _extract_from_dict(self, data_dict: Dict, structured_data: Dict):
    """从字典中提取论文数据（支持多种格式）"""
    
    # 检查是否有顶层的"文献"包装对象（新格式）
    if '文献' in data_dict and isinstance(data_dict['文献'], dict):
        self.log_info("📦 发现'文献'包装对象，提取内部数据")
        paper_data = data_dict['文献']
    else:
        paper_data = data_dict
    
    # 提取文献编号（支持多种字段名）
    article_id_keys = ['文献编号（Article ID）', '文献编号', 'article_id']
    for key in article_id_keys:
        if key in paper_data:
            structured_data['article_id'] = paper_data[key] or ''
            break
    
    # 提取文献名称（支持多种字段名）
    article_name_keys = ['文献名称（Article Name）', '文献名称', 'article_name']
    for key in article_name_keys:
        if key in paper_data:
            structured_data['article_name'] = paper_data[key] or ''
            break
    
    # 提取四级数据连接（支持多种字段名）
    hierarchical_keys = ['四级数据连接（4-level Data Linkage）', '四级数据连接', 'hierarchical_data']
    for key in hierarchical_keys:
        if key in paper_data:
            hierarchical_list = paper_data[key]
            if isinstance(hierarchical_list, list):
                # 转换新格式的嵌套结构为扁平化结构
                normalized_data = self._normalize_hierarchical_data(hierarchical_list)
                structured_data['hierarchical_data'] = normalized_data
            break
```

### 4. 新增 `_normalize_hierarchical_data` 方法

将嵌套的材料/中间体数据结构转换为扁平化结构：

```python
def _normalize_hierarchical_data(self, hierarchical_list: List[Dict]) -> List[Dict]:
    """
    将嵌套的材料/中间体数据结构转换为扁平化结构
    """
    normalized = []
    
    for item in hierarchical_list:
        normalized_item = {}
        
        # 检查是否是新格式（嵌套结构）
        if '原材料（Materials）' in item or '中间体（Intermediates）' in item:
            # 提取材料信息
            materials = item.get('原材料（Materials）', {})
            if isinstance(materials, dict):
                normalized_item['材料编号'] = materials.get('材料编号（Material ID）', '')
                normalized_item['原材料名称'] = materials.get('原材料名称（Material Name）', '')
                normalized_item['CAS号'] = materials.get('CAS号（CAS Number）', '')
            
            # 提取中间体信息
            intermediates = item.get('中间体（Intermediates）', {})
            if isinstance(intermediates, dict):
                normalized_item['中间体编号'] = intermediates.get('中间体编号（Intermediate ID）', '')
                normalized_item['中间体名称'] = intermediates.get('中间体名称（Intermediate Name）', '')
            
            # 提取中间体组成
            normalized_item['中间体组成'] = item.get('中间体组成（Intermediate Compositions）', '')
            
            # 提取性能数据
            properties = item.get('性能（Properties）', [])
            if isinstance(properties, list):
                normalized_properties = []
                for prop in properties:
                    normalized_prop = {
                        '性能编号': prop.get('性能编号（Property ID）', ''),
                        '性能名称': prop.get('性能名称（Property Name）', ''),
                        '性能值': prop.get('性能值（Property Value）', '')
                    }
                    normalized_properties.append(normalized_prop)
                normalized_item['性能'] = normalized_properties
        else:
            # 旧格式（扁平结构），直接使用
            normalized_item = item
        
        normalized.append(normalized_item)
    
    return normalized
```

## 测试验证

### 测试数据

文献编号: A2
文献名称: Soft Composite Gels with High Toughness and Low Thermal Resistance...
材料组数: 2组
性能数据: 14条
预期数据库记录: 17条（1篇文献 + 2个材料 + 14个性能）

### 预期日志输出

```
[INFO] 发现文本输出，类型: str, 长度: 2345
[INFO] ✂️ 检测到并清理了markdown代码块标记
[INFO] 清理前长度: 2345, 清理后长度: 2312
[INFO] ✅ 成功解析JSON字符串
[INFO] 解析后的字典键: ['文献']
[INFO] 🔍 _extract_from_dict 输入字典的键: ['文献']
[INFO] 📦 发现'文献'包装对象，提取内部数据
[INFO] 📌 提取文献编号 (键:'文献编号（Article ID）'): '' -> 'A2'
[INFO] 📌 提取文献名称 (键:'文献名称（Article Name）'): '' -> 'Soft Composite Gels...'
[INFO] 📌 找到层次数据键: '四级数据连接（4-level Data Linkage）'
[INFO] 🔄 处理第 1 个材料/中间体数据
[INFO]   📦 检测到新格式（嵌套结构）
[INFO]     ✓ 材料编号: A2M1
[INFO]     ✓ 中间体编号: A2I1
[INFO]     ✓ 性能数据: 7 条
[INFO] 🔄 处理第 2 个材料/中间体数据
[INFO]   📦 检测到新格式（嵌套结构）
[INFO]     ✓ 材料编号: A2M2
[INFO]     ✓ 中间体编号: A2I2
[INFO]     ✓ 性能数据: 7 条
[INFO] ✅ 提取到 2 个材料/中间体数据
[INFO] ✅ 解析完成 - 文献ID: A2, 文献名称: Soft Composite Gels..., 材料/中间体数: 2
[INFO] 数据验证通过
[INFO] 论文数据保存成功，文献ID: A2
```

## 兼容性

### 向后兼容

新的解析逻辑**同时支持**旧格式和新格式：

1. **旧格式（扁平结构）：** 直接提取字段
2. **新格式（嵌套结构）：** 先解包"文献"对象，再提取字段
3. **双语字段名：** 按优先级匹配多种字段名

### 字段名匹配优先级

1. 双语格式：`文献编号（Article ID）`
2. 纯中文：`文献编号`
3. 纯英文：`article_id`

## 部署说明

### 1. 重启后端服务

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/backend
# 停止旧服务
pkill -f "python.*run.py"

# 启动新服务
nohup python run.py > ../logs/backend.log 2>&1 &
```

### 2. 验证修复

1. 上传一个PDF论文文件
2. 触发OCR识别
3. 检查日志，确认：
   - 成功清理markdown标记
   - 成功提取"文献"对象
   - 成功解析双语字段名
   - 成功保存到数据库

### 3. 检查数据库

```sql
-- 查看最新的论文记录
SELECT * FROM paper_articles ORDER BY id DESC LIMIT 1;

-- 查看材料/中间体记录
SELECT * FROM paper_material_intermediates 
WHERE article_id = (SELECT id FROM paper_articles ORDER BY id DESC LIMIT 1);

-- 查看性能记录
SELECT * FROM paper_properties 
WHERE article_id = (SELECT id FROM paper_articles ORDER BY id DESC LIMIT 1);
```

## 影响范围

- **修改文件：** `backend/app/adapters/paper_adapter.py`
- **影响功能：** 论文OCR结果解析和保存
- **风险等级：** 低（向后兼容）

## 相关文件

- `parse_selected_ocr.py` - 用于分析和验证OCR结果格式
- `test_markdown_clean.py` - 测试markdown清理功能

---

**修复日期：** 2025-11-11
**版本：** v1.1.0

