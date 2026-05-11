# 文档索引

本目录包含 IBoxTech-ocrchecker 项目的技术文档。

## 📚 重要文档快速导航

### 🚀 快速开始
- **[NEW_SYSTEM_STARTUP_GUIDE.md](./NEW_SYSTEM_STARTUP_GUIDE.md)** - 新系统启动指南
- **[QUICK_START_OCR.md](./QUICK_START_OCR.md)** - OCR快速开始指南

### 🏗️ 架构设计
- **[OCR_ADAPTER_ARCHITECTURE.md](./OCR_ADAPTER_ARCHITECTURE.md)** - OCR适配器架构设计
- **[OCR_UNIFIED_INTERFACE_SPEC.md](./OCR_UNIFIED_INTERFACE_SPEC.md)** - OCR统一接口规范
- **[FILE_TYPE_DISTINCTION_SOLUTION.md](./FILE_TYPE_DISTINCTION_SOLUTION.md)** - 文件类型区分解决方案

### 🔄 迁移指南
- **[OCR_ASYNC_MIGRATION_GUIDE.md](./OCR_ASYNC_MIGRATION_GUIDE.md)** ⭐ - OCR异步任务迁移指南（最新）
  - 从同步OCR迁移到异步任务的完整指南
  - 包含代码标注位置、迁移计划、参考实现
  - 当前状态：阶段1完成，进入阶段2稳定期观察

### 🛠️ 实现总结
- **[OCR_ADAPTER_IMPLEMENTATION_SUMMARY.md](./OCR_ADAPTER_IMPLEMENTATION_SUMMARY.md)** - OCR适配器实现总结
- **[REFACTORING_COMPLETE_REPORT.md](./REFACTORING_COMPLETE_REPORT.md)** - 重构完成报告
- **[FILE_REVIEW_REFACTOR_SUMMARY.md](./FILE_REVIEW_REFACTOR_SUMMARY.md)** - 文件核对重构总结

### 📝 功能实现
- **[PAPER_IMPLEMENTATION_SUMMARY.md](./PAPER_IMPLEMENTATION_SUMMARY.md)** - 论文功能实现总结
- **[COMMISSION_FORM_COMPLETE.md](./COMMISSION_FORM_COMPLETE.md)** - 委托单表单完成文档
- **[FILE_TYPE_SUPPORT_IMPLEMENTATION.md](./FILE_TYPE_SUPPORT_IMPLEMENTATION.md)** - 文件类型支持实现

### 🐛 问题修复
- **[PDF_CHINESE_FONT_ISSUE.md](./PDF_CHINESE_FONT_ISSUE.md)** - PDF中文字体问题
- **[PDF_TEXT_DISPLAY_FIX.md](./PDF_TEXT_DISPLAY_FIX.md)** - PDF文本显示修复
- **[ELPROGRESS_STATUS_FIX.md](./ELPROGRESS_STATUS_FIX.md)** - ElProgress状态修复

### 🔌 外部接口
- **[EXTERNAL_OCR_API_SPEC.md](./EXTERNAL_OCR_API_SPEC.md)** - 外部OCR API规范
- **[OCR_INTERFACE_UNIFICATION_REPORT.md](./OCR_INTERFACE_UNIFICATION_REPORT.md)** - OCR接口统一报告

### 💾 数据存储
- **[PAPER_DATA_STORAGE_3TABLES.md](./PAPER_DATA_STORAGE_3TABLES.md)** - 论文数据三表存储方案

---

## 📅 最近更新

| 日期 | 文档 | 说明 |
|------|------|------|
| 2025-11-14 | OCR_ASYNC_MIGRATION_GUIDE.md | 新增OCR异步任务迁移指南 |
| - | REFACTORING_COMPLETE_REPORT.md | 重构完成报告 |
| - | FILE_REVIEW_REFACTOR_SUMMARY.md | 文件核对重构总结 |

---

## 🔍 按主题查找

### OCR相关
- OCR_ASYNC_MIGRATION_GUIDE.md ⭐
- OCR_ADAPTER_ARCHITECTURE.md
- OCR_UNIFIED_INTERFACE_SPEC.md
- EXTERNAL_OCR_API_SPEC.md
- QUICK_START_OCR.md
- OCR_DISABLE_SUMMARY.md

### 表单组件
- COMMISSION_FORM_COMPLETE.md
- PAPER_FORM_COMPLETE.md
- PAPER_FORM_USAGE.md

### 页面重构
- RECOGNIZE_PAGE_REFACTOR_COMPLETE.md
- FILE_REVIEW_REFACTOR_SUMMARY.md
- RECOGNIZE_PAGE_REFACTOR_GUIDE.md

### PDF处理
- PDF_CHINESE_FONT_ISSUE.md
- PDF_TEXT_DISPLAY_FIX.md
- PDF_CORS_FIX.md
- LOCAL_CMAP_CONFIG.md

### 系统重构
- REFACTORING_COMPLETE_REPORT.md
- REFACTORING_IMPLEMENTATION.md
- REFACTORING_PLAN.md
- REFACTORING_PROGRESS.md

---

## 📖 文档编写规范

1. **使用Markdown格式**
2. **文件名使用大写和下划线**，如 `FEATURE_NAME_DOC.md`
3. **包含以下部分**：
   - 概述
   - 背景/问题
   - 解决方案
   - 实现细节
   - 使用示例
   - 注意事项
4. **更新本索引文件**，添加新文档链接

---

## 🆘 获取帮助

如果找不到需要的文档，请：
1. 检查代码中的注释（特别是带 `@deprecated` 和 `TODO` 的）
2. 查看相关文件的实现示例
3. 参考本索引的主题分类

---

**最后更新**: 2025-11-14

