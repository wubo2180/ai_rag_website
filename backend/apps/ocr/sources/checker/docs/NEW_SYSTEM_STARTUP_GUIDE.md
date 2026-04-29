# 新系统启动指南

## 🚀 快速开始

本指南将帮助您完成从旧系统到新系统的平滑过渡。

---

## 📋 前置检查清单

在开始之前，请确认：

- [ ] 后端服务正在运行
- [ ] 前端服务正在运行
- [ ] MySQL数据库可访问
- [ ] 已有备份（可选但推荐）

---

## 🔧 第一步：数据库准备

### 1.1 执行SQL脚本

创建论文数据表：

```bash
# 连接到数据库
mysql -u root -p ocr_db

# 执行SQL脚本
source /home/h3c/workspace/IBoxTech-ocrchecker/backend/migrations/create_paper_tables.sql;

# 验证表创建
SHOW TABLES LIKE 'paper%';

# 应该看到3张表：
# - paper_articles
# - paper_material_intermediates
# - paper_properties

# 退出MySQL
exit;
```

**预期结果**：
```
+-----------------------------------+
| Tables_in_ocr_db (paper%)         |
+-----------------------------------+
| paper_articles                    |
| paper_material_intermediates      |
| paper_properties                  |
+-----------------------------------+
3 rows in set
```

### 1.2 添加文档类型字段（如果还没执行）

```bash
mysql -u root -p ocr_db

# 执行迁移脚本
source /home/h3c/workspace/IBoxTech-ocrchecker/backend/migrations/add_document_type_to_files.sql;

# 验证字段添加
DESC files;

# 应该看到 document_type_code 字段

exit;
```

---

## 🖥️ 第二步：替换识别页面

### 2.1 备份原文件

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend/src/views/FileRecognize

# 创建带时间戳的备份
cp index.vue index.vue.backup.$(date +%Y%m%d_%H%M%S)

# 验证备份成功
ls -lh index.vue.backup*
```

### 2.2 使用新版本

```bash
# 替换为重构后的文件
mv index.vue.refactored index.vue

echo "✅ 识别页面已更新"
```

### 2.3 验证文件

```bash
# 检查新文件是否正确
head -20 index.vue

# 应该看到类似：
# <template>
#   <div class="file-recognize-container">
#     <!-- 顶部工具栏 -->
#     ...
```

---

## 🔄 第三步：重启服务

### 3.1 重启后端（如有必要）

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/backend

# 停止当前后端
ps aux | grep "python.*app.py" | grep -v grep | awk '{print $2}' | xargs kill

# 重新启动
python app.py

# 预期输出：
# * Running on http://0.0.0.0:5000
# * Debug mode: on
```

### 3.2 重启前端

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend

# Ctrl+C 停止当前服务（如果正在运行）

# 重新启动
npm run dev

# 预期输出：
# VITE v4.4.9 ready in XXX ms
# ➜ Local:   http://localhost:3000/
```

---

## 🧪 第四步：测试新系统

### 测试1：上传论文文件 ⭐

#### 4.1 上传文件

1. 访问：`http://localhost:3000/upload`
2. 选择一个PDF文件
3. **重要**：在"文档类型"下拉框中选择 **"论文"**
4. 点击"开始上传"
5. 等待上传完成

**检查点**：
- ✅ 上传进度显示
- ✅ 上传成功提示
- ✅ 文件出现在文件列表中

#### 4.2 进入识别页面

1. 在文件列表中，找到刚上传的文件
2. 点击"识别"按钮（或操作菜单中的识别）
3. 进入识别页面

**检查点**：
- ✅ 页面标题显示 "论文数据"（不是"委托数据"）
- ✅ 顶部有"论文"标签
- ✅ 左侧显示论文表单（文献编号、文献名称等）

#### 4.3 OCR识别

1. 点击顶部的 **"OCR识别"** 按钮
2. 等待识别完成（会显示"正在处理..."）
3. 识别完成后，查看表单是否自动填充

**检查点**：
- ✅ OCR识别按钮变为"识别中"（loading状态）
- ✅ 识别完成后有成功提示
- ✅ 表单字段自动填充数据
- ✅ 文献编号、名称等字段有内容

#### 4.4 编辑和保存

1. 修改某些字段（如文献名称）
2. 顶部应显示"已修改"标签
3. 点击 **"保存入库"** 按钮
4. 确认保存

**检查点**：
- ✅ "已修改"标签显示
- ✅ 保存成功提示
- ✅ 刷新页面后数据仍然存在

#### 4.5 验证数据库

```bash
# 连接数据库
mysql -u root -p ocr_db

# 查询论文数据
SELECT * FROM paper_articles WHERE article_id = 'A1' LIMIT 1\G

# 查询材料数据
SELECT * FROM paper_material_intermediates WHERE article_id = 'A1' LIMIT 3\G

# 查询性能数据
SELECT * FROM paper_properties WHERE article_id = 'A1' LIMIT 5\G

exit;
```

**预期结果**：应该看到对应的数据记录

---

### 测试2：上传委托单文件

#### 4.6 上传委托单

1. 访问：`http://localhost:3000/upload`
2. 选择一个委托单PDF
3. **文档类型选择**：**"委托单"**
4. 上传

#### 4.7 识别委托单

1. 进入识别页面
2. **检查点**：
   - ✅ 页面标题显示 "委托单数据"
   - ✅ 左侧显示委托单表单（表格编号、委托编号等）
3. 点击"OCR识别"
4. 查看自动填充
5. 保存数据

---

## 🎯 第五步：功能验证

### 5.1 文档类型切换

测试系统能否正确识别不同的文档类型：

```
上传论文 → 识别页面显示 PaperForm ✅
上传委托单 → 识别页面显示 CommissionForm ✅
```

### 5.2 OCR自动填充

```
OCR识别 → 结果返回 → 表单自动填充 ✅
```

### 5.3 数据持久化

```
保存数据 → 刷新页面 → 数据正确显示 ✅
```

### 5.4 视图模式

测试三种视图模式：

```
分屏模式：表单 + 文件预览 ✅
数据模式：只显示表单 ✅
文件模式：只显示文件 ✅
```

---

## 📊 第六步：测试论文表单测试页面（可选）

```bash
# 访问测试页面
http://localhost:3000/paper-form-test
```

**测试内容**：
1. 点击"加载示例数据"
2. 查看表单填充
3. 添加/删除材料
4. 添加/删除性能数据
5. 点击"查看JSON"
6. 点击"验证并保存"

---

## ⚠️ 常见问题排查

### 问题1：识别页面显示空白

**可能原因**：
- 组件导入失败
- 文件类型未正确识别

**解决方案**：
```bash
# 检查浏览器控制台错误
F12 → Console

# 检查组件文件是否存在
ls -l /home/h3c/workspace/IBoxTech-ocrchecker/frontend/src/components/PaperForm/index.vue
ls -l /home/h3c/workspace/IBoxTech-ocrchecker/frontend/src/components/CommissionForm/index.vue
```

### 问题2：OCR识别失败

**检查后端日志**：
```bash
# 查看后端日志
tail -f /home/h3c/workspace/IBoxTech-ocrchecker/backend/logs/app.log

# 或查看终端输出
```

### 问题3：保存失败

**检查数据库连接**：
```bash
mysql -u root -p ocr_db -e "SELECT 1;"
```

**检查表是否存在**：
```bash
mysql -u root -p ocr_db -e "SHOW TABLES;"
```

### 问题4：文档类型显示为"文档"而不是"论文"或"委托单"

**原因**：`document_type_code` 未正确设置

**解决方案**：
```sql
-- 检查文件的文档类型
SELECT id, filename, document_type_code FROM files ORDER BY id DESC LIMIT 10;

-- 如果为空，手动更新
UPDATE files SET document_type_code = 'paper' WHERE id = <file_id>;
```

---

## 🔍 第七步：验证完整流程

### 完整的论文流程

```
1. 上传论文PDF (document_type_code = 'paper')
   ↓
2. 进入识别页面 → 显示PaperForm
   ↓
3. 点击OCR识别 → 任务创建 → 轮询状态
   ↓
4. 识别完成 → 表单自动填充
   ↓
5. 编辑数据（可选）
   ↓
6. 保存入库 → paper_articles, paper_material_intermediates, paper_properties
   ↓
7. 刷新页面 → 数据正确加载
   ↓
✅ 完成
```

### 完整的委托单流程

```
1. 上传委托单PDF (document_type_code = 'commission')
   ↓
2. 进入识别页面 → 显示CommissionForm
   ↓
3. 点击OCR识别
   ↓
4. 识别完成 → 表单自动填充
   ↓
5. 保存入库 → commission_basic, test_items, special_tests
   ↓
✅ 完成
```

---

## 📝 第八步：回滚方案（如遇问题）

如果新系统有问题，可以快速回滚：

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend/src/views/FileRecognize

# 找到最新的备份
ls -lt index.vue.backup* | head -1

# 回滚（替换 YYYYMMDD_HHMMSS 为实际时间戳）
cp index.vue.backup.YYYYMMDD_HHMMSS index.vue

# 重启前端
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend
npm run dev
```

---

## ✅ 成功标志

当您看到以下现象，说明新系统运行正常：

1. ✅ 上传页面能选择文档类型（论文/委托单）
2. ✅ 识别页面标题正确显示文档类型
3. ✅ 论文显示PaperForm，委托单显示CommissionForm
4. ✅ OCR识别能自动填充表单
5. ✅ 保存功能正常工作
6. ✅ 数据能正确持久化和加载
7. ✅ 三种视图模式都能正常切换

---

## 📚 相关文档

- **`docs/PAPER_FORM_USAGE.md`** - 论文表单使用指南
- **`docs/COMMISSION_FORM_COMPLETE.md`** - 委托单表单文档
- **`docs/RECOGNIZE_PAGE_REFACTOR_COMPLETE.md`** - 识别页面重构报告
- **`docs/PAPER_DATA_STORAGE_3TABLES.md`** - 数据库设计文档

---

## 🆘 需要帮助？

如果遇到问题：

1. **检查浏览器控制台**：F12 → Console
2. **检查后端日志**：查看终端输出
3. **检查数据库**：验证表和数据
4. **查看文档**：参考上述相关文档
5. **回滚系统**：使用备份文件恢复

---

## 🎉 开始使用

现在您可以按照上述步骤开始使用新系统了！

**推荐顺序**：
1. 第一步：数据库准备（15分钟）
2. 第二步：替换识别页面（5分钟）
3. 第三步：重启服务（5分钟）
4. 第四步：测试新系统（30分钟）
5. 第五步：功能验证（15分钟）

**总计时间**：约1小时

**建议**：
- 先测试论文流程（因为是新功能）
- 再测试委托单流程（验证兼容性）
- 遇到问题及时查看日志和文档

---

**更新日期**: 2025-11-06  
**状态**: ✅ 可立即执行  
**难度**: ⭐⭐ (中等)


