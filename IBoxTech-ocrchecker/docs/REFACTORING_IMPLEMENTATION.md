# OCR系统重构实施方案（最终确认版）

## ✅ 确认的重构方案

### 1. 重构方式
**渐进式重构** - 新旧系统并存，待新系统稳定后移除旧系统

### 2. 表单实现
**动态表单渲染器** - 使用第三方JSON配置生成表单库

#### 推荐的第三方表单库：

**方案1: FormCreate (推荐⭐⭐⭐⭐⭐)**
- 官网：http://www.form-create.com/
- 特点：
  - ✅ Vue 3完美支持
  - ✅ Element Plus深度集成
  - ✅ JSON配置驱动
  - ✅ 支持自定义组件
  - ✅ 中文文档完善
  - ✅ 轻量级，学习成本低
- 安装：`npm install @form-create/element-ui`

示例配置：
```json
{
  "fields": [
    {
      "type": "input",
      "field": "commission_number",
      "title": "委托编号",
      "props": {
        "placeholder": "请输入委托编号"
      },
      "validate": [
        {"required": true, "message": "请输入委托编号"}
      ]
    }
  ]
}
```

**方案2: Formily (阿里开源)**
- 官网：https://formilyjs.org/
- 特点：
  - ✅ 阿里出品，企业级
  - ✅ 功能强大，支持复杂场景
  - ✅ TypeScript支持好
  - ⚠️ 学习曲线较陡
  - ⚠️ 文档较复杂

**方案3: VFormRender**
- 特点：
  - ✅ 可视化设计器
  - ✅ 开箱即用
  - ⚠️ 定制性相对较弱

**建议：使用 FormCreate**
原因：最适合我们的场景，轻量级，易上手，Element Plus原生支持

### 3. 数据存储方案
**混合存储模式**

#### 委托单（现有类型）
- ✅ 保留专用表结构
  - `commission_basic` - 基本信息
  - `test_items` - 测试项目
  - `special_tests` - 特殊测试
- ✅ 现有数据不迁移
- ✅ 继续使用现有API和服务

#### 论文（新类型）
- ✅ 使用通用表 `document_basic`
- ✅ JSON字段存储数据
- ✅ 使用新的统一API

#### 文件类型配置
- ✅ 所有类型统一配置在 `file_type_configs` 表

### 4. 架构设计

```
┌─────────────────────────────────────────────────┐
│              前端 (Vue 3)                        │
├─────────────────────────────────────────────────┤
│  FileRecognize 页面                              │
│  ├── 文件类型选择器                              │
│  ├── 左侧表单区域                                │
│  │   ├── [委托单] CommissionForm (现有组件)      │
│  │   └── [论文] FormCreate动态表单              │
│  └── 右侧PDF预览区域                             │
└─────────────────────────────────────────────────┘
                     ↓ HTTP API
┌─────────────────────────────────────────────────┐
│              后端 (Flask)                        │
├─────────────────────────────────────────────────┤
│  统一API层                                       │
│  └── /api/documents/recognize                   │
│      ├── 委托单 → CommissionDocumentService     │
│      └── 论文 → DocumentService (通用)          │
├─────────────────────────────────────────────────┤
│  数据层                                          │
│  ├── [委托单] commission_basic                  │
│  │            test_items                        │
│  │            special_tests                     │
│  └── [论文] document_basic                      │
│  └── [配置] file_type_configs                   │
└─────────────────────────────────────────────────┘
```

## 🚀 实施步骤

### Phase 1: 基础架构搭建 (当前)
- [x] 创建 `FileTypeConfig` 模型
- [x] 创建 `DocumentBasic` 模型
- [ ] 注册新模型到系统
- [ ] 创建数据库迁移脚本

### Phase 2: 后端服务层
- [ ] 创建 `DocumentService` 通用服务
- [ ] 创建统一API接口 `/api/documents/*`
- [ ] 实现委托单类型配置初始化

### Phase 3: 前端集成FormCreate
- [ ] 安装 FormCreate 库
- [ ] 创建 `DynamicForm` 组件封装
- [ ] 修改 `FileRecognize` 页面支持动态切换

### Phase 4: 论文类型实现
- [ ] 创建论文类型配置
- [ ] 实现论文OCR识别API
- [ ] 创建论文表单配置JSON
- [ ] 测试论文文件处理流程

### Phase 5: 测试与优化
- [ ] 委托单功能回归测试
- [ ] 论文功能完整测试
- [ ] 性能优化
- [ ] 文档完善

### Phase 6: 旧系统移除（稳定后）
- [ ] 将委托单也迁移到统一API
- [ ] 移除旧的API接口
- [ ] 代码清理

## 📝 文件类型配置示例

### 委托单配置
```json
{
  "type_code": "commission",
  "type_name": "委托单",
  "type_description": "检测委托测试申请单",
  "ocr_model_api": "/api/external-ocr/recognize",
  "ocr_model_type": "external",
  "storage_table_basic": "commission_basic",
  "storage_table_items": "test_items",
  "storage_table_details": "special_tests",
  "form_component": "CommissionForm",
  "use_dynamic_form": false,
  "is_active": true
}
```

### 论文配置
```json
{
  "type_code": "paper",
  "type_name": "论文",
  "type_description": "学术论文检测",
  "ocr_model_api": "/api/ocr/paper",
  "ocr_model_type": "internal",
  "storage_table_basic": "document_basic",
  "form_config": {
    "fields": [
      {
        "type": "input",
        "field": "paper_title",
        "title": "论文标题",
        "validate": [{"required": true, "message": "请输入论文标题"}]
      },
      {
        "type": "input",
        "field": "author",
        "title": "作者",
        "validate": [{"required": true}]
      },
      {
        "type": "input",
        "field": "institution",
        "title": "所属机构"
      },
      {
        "type": "date",
        "field": "publish_date",
        "title": "发表日期"
      },
      {
        "type": "input",
        "field": "keywords",
        "title": "关键词",
        "props": {"placeholder": "多个关键词用逗号分隔"}
      },
      {
        "type": "textarea",
        "field": "abstract",
        "title": "摘要",
        "props": {"rows": 5}
      }
    ]
  },
  "use_dynamic_form": true,
  "is_active": true
}
```

## 🎯 当前优先级

1. **立即执行**：
   - 注册新模型
   - 创建数据库表
   - 安装FormCreate

2. **本周完成**：
   - 实现统一API接口
   - 集成FormCreate到前端
   - 创建委托单类型配置

3. **下周完成**：
   - 实现论文类型完整流程
   - 测试和优化

## ⚠️ 注意事项

1. **向后兼容**：确保现有委托单功能不受影响
2. **数据安全**：新旧系统数据隔离，互不影响
3. **逐步迁移**：先验证新系统稳定性，再考虑迁移旧功能
4. **文档同步**：及时更新API文档和使用说明

---

**准备开始实施！** 🚀


