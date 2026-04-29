# 动态表单（DynamicForm）使用指南

## 📋 概述

DynamicForm 是一个通用的动态表单组件，可以根据 JSON 配置自动生成表单。主要用于在**文件类型配置**中预览和测试表单布局。

**位置**：
- 组件：`frontend/src/components/DynamicForm/index.vue`
- 使用位置：`frontend/src/views/FileTypeConfig/index.vue`

**特性**：
- ✅ 配置驱动，无需编写代码
- ✅ 支持10+种字段类型
- ✅ 内置表单验证
- ✅ 支持分组和自定义布局
- ✅ 响应式设计，支持移动端

---

## 🚀 快速开始

### 1. 进入文件类型配置页面

访问：**系统配置 → 文件类型配置管理**

### 2. 编辑配置或创建新配置

点击"编辑"或"添加文件类型配置"

### 3. 切换到"表单配置"标签页

### 4. 编写 form_config JSON

可以：
- 手动编写 JSON
- 点击"查看示例"复制模板
- 点击"预览表单"实时查看效果

---

## 📖 配置格式

### 基本结构

```json
{
  "labelWidth": "120px",       // 标签宽度
  "labelPosition": "right",    // 标签位置：left/right/top
  "sections": [                // 表单分组数组
    {
      "title": "基本信息",     // 分组标题
      "description": "描述文字", // 分组描述（可选）
      "fields": [              // 字段数组
        {
          "name": "title",     // 字段名（必填）
          "label": "标题",     // 字段标签（必填）
          "type": "text",      // 字段类型（必填）
          "required": true,    // 是否必填
          "span": 24           // 栅格占位（1-24）
        }
      ]
    }
  ]
}
```

---

## 🎨 支持的字段类型

### 1. 文本输入（text）

```json
{
  "name": "title",
  "label": "标题",
  "type": "text",
  "required": true,
  "span": 24,
  "placeholder": "请输入标题",
  "maxLength": 100,
  "pattern": "^[A-Za-z0-9]+$",
  "patternMessage": "只能包含字母和数字"
}
```

**属性说明**：
- `maxLength`: 最大字符数
- `pattern`: 正则表达式验证
- `patternMessage`: 验证失败提示

### 2. 多行文本（textarea）

```json
{
  "name": "description",
  "label": "描述",
  "type": "textarea",
  "rows": 4,
  "span": 24,
  "placeholder": "请输入描述",
  "maxLength": 500
}
```

### 3. 数字输入（number）

```json
{
  "name": "age",
  "label": "年龄",
  "type": "number",
  "min": 0,
  "max": 150,
  "step": 1,
  "precision": 0,
  "span": 12
}
```

**属性说明**：
- `min/max`: 最小/最大值
- `step`: 步长
- `precision`: 精度（小数位数）

### 4. 下拉选择（select）

```json
{
  "name": "status",
  "label": "状态",
  "type": "select",
  "required": true,
  "span": 12,
  "multiple": false,
  "clearable": true,
  "options": [
    { "label": "草稿", "value": "draft" },
    { "label": "已提交", "value": "submitted" }
  ]
}
```

**属性说明**：
- `options`: 选项数组（必填）
- `multiple`: 是否多选
- `clearable`: 是否可清空

### 5. 日期选择（date）

```json
{
  "name": "created_date",
  "label": "创建日期",
  "type": "date",
  "required": true,
  "span": 12,
  "format": "YYYY-MM-DD",
  "valueFormat": "YYYY-MM-DD"
}
```

### 6. 日期时间选择（datetime）

```json
{
  "name": "created_at",
  "label": "创建时间",
  "type": "datetime",
  "span": 12,
  "format": "YYYY-MM-DD HH:mm:ss"
}
```

### 7. 开关（switch）

```json
{
  "name": "enabled",
  "label": "是否启用",
  "type": "switch",
  "span": 12,
  "activeText": "是",
  "inactiveText": "否"
}
```

### 8. 单选框（radio）

```json
{
  "name": "priority",
  "label": "优先级",
  "type": "radio",
  "span": 12,
  "options": [
    { "label": "高", "value": "high" },
    { "label": "中", "value": "medium" },
    { "label": "低", "value": "low" }
  ]
}
```

### 9. 复选框（checkbox）

```json
{
  "name": "tags",
  "label": "标签",
  "type": "checkbox",
  "span": 24,
  "options": [
    { "label": "重要", "value": "important" },
    { "label": "紧急", "value": "urgent" }
  ]
}
```

### 10. 滑块（slider）

```json
{
  "name": "progress",
  "label": "进度",
  "type": "slider",
  "span": 12,
  "min": 0,
  "max": 100,
  "step": 1,
  "showInput": true
}
```

### 11. 评分（rate）

```json
{
  "name": "score",
  "label": "评分",
  "type": "rate",
  "span": 12,
  "max": 5,
  "showText": true,
  "texts": ["极差", "失望", "一般", "满意", "惊喜"]
}
```

---

## 🔧 通用字段属性

所有字段类型都支持以下属性：

| 属性 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| `name` | String | ✅ | 字段名称 | `"title"` |
| `label` | String | ✅ | 字段标签 | `"标题"` |
| `type` | String | ✅ | 字段类型 | `"text"` |
| `required` | Boolean | ❌ | 是否必填 | `true` |
| `span` | Number | ❌ | 栅格占位（1-24） | `12` |
| `placeholder` | String | ❌ | 占位提示 | `"请输入"` |
| `disabled` | Boolean | ❌ | 是否禁用 | `false` |
| `defaultValue` | Any | ❌ | 默认值 | `""` |
| `tip` | String | ❌ | 字段提示信息 | `"提示文字"` |

---

## 📐 布局配置

### 栅格系统

使用 24 栅格系统，通过 `span` 属性控制字段宽度：

```json
{
  "fields": [
    { "name": "field1", "span": 24 },  // 占满一行
    { "name": "field2", "span": 12 },  // 半行
    { "name": "field3", "span": 12 },  // 半行
    { "name": "field4", "span": 8 },   // 三分之一
    { "name": "field5", "span": 8 },
    { "name": "field6", "span": 8 }
  ]
}
```

### 表单分组

使用 `sections` 将字段分组：

```json
{
  "sections": [
    {
      "title": "基本信息",
      "description": "填写基本信息",
      "fields": [...]
    },
    {
      "title": "详细信息",
      "fields": [...]
    }
  ]
}
```

---

## ✅ 验证规则

### 1. 必填验证

```json
{
  "required": true
}
```

### 2. 长度验证

```json
{
  "minLength": 3,
  "maxLength": 20
}
```

### 3. 正则验证

```json
{
  "pattern": "^[A-Z0-9]+$",
  "patternMessage": "只能包含大写字母和数字"
}
```

### 4. 数值范围

```json
{
  "type": "number",
  "min": 0,
  "max": 100
}
```

---

## 💡 使用示例

### 完整示例：用户注册表单

```json
{
  "labelWidth": "100px",
  "labelPosition": "right",
  "sections": [
    {
      "title": "账号信息",
      "fields": [
        {
          "name": "username",
          "label": "用户名",
          "type": "text",
          "required": true,
          "span": 12,
          "placeholder": "请输入用户名",
          "minLength": 3,
          "maxLength": 20,
          "pattern": "^[a-zA-Z0-9_]+$",
          "patternMessage": "只能包含字母、数字和下划线"
        },
        {
          "name": "email",
          "label": "邮箱",
          "type": "text",
          "required": true,
          "span": 12,
          "placeholder": "请输入邮箱",
          "pattern": "^[\\w-\\.]+@[\\w-]+\\.[a-z]{2,}$",
          "patternMessage": "邮箱格式不正确"
        },
        {
          "name": "phone",
          "label": "手机号",
          "type": "text",
          "required": true,
          "span": 12,
          "placeholder": "请输入手机号",
          "pattern": "^1[3-9]\\d{9}$",
          "patternMessage": "手机号格式不正确"
        },
        {
          "name": "age",
          "label": "年龄",
          "type": "number",
          "span": 12,
          "min": 18,
          "max": 100
        }
      ]
    },
    {
      "title": "个人信息",
      "fields": [
        {
          "name": "gender",
          "label": "性别",
          "type": "radio",
          "span": 12,
          "options": [
            { "label": "男", "value": "male" },
            { "label": "女", "value": "female" }
          ]
        },
        {
          "name": "birthday",
          "label": "生日",
          "type": "date",
          "span": 12,
          "format": "YYYY-MM-DD"
        },
        {
          "name": "interests",
          "label": "兴趣爱好",
          "type": "checkbox",
          "span": 24,
          "options": [
            { "label": "阅读", "value": "reading" },
            { "label": "运动", "value": "sports" },
            { "label": "音乐", "value": "music" },
            { "label": "旅游", "value": "travel" }
          ]
        },
        {
          "name": "bio",
          "label": "个人简介",
          "type": "textarea",
          "span": 24,
          "rows": 4,
          "maxLength": 200,
          "placeholder": "请简单介绍一下自己"
        }
      ]
    }
  ]
}
```

---

## 🎯 在文件类型配置中使用

### 使用流程

1. **访问配置页面**
   - 导航：系统配置 → 文件类型配置管理

2. **编辑或新建配置**
   - 点击"编辑"或"添加文件类型配置"

3. **切换到"表单配置"标签页**

4. **编写 form_config**
   - 直接编写 JSON
   - 或点击"查看示例"使用模板

5. **预览表单**
   - 点击"预览表单"按钮
   - 在弹窗中查看实际渲染效果
   - 测试表单验证

6. **保存配置**
   - 确认无误后保存

### 预览功能

**预览对话框提供**：
- ✅ 实时渲染表单
- ✅ 测试所有字段类型
- ✅ 测试表单验证
- ✅ 查看表单数据输出

**测试步骤**：
1. 填写表单字段
2. 点击"测试表单验证"
3. 查看验证结果
4. 在浏览器控制台查看表单数据

---

## 🔄 与硬编码组件的对比

| 特性 | 硬编码组件 | 动态表单 |
|------|-----------|---------|
| **开发方式** | 手写Vue组件 | JSON配置 |
| **修改方式** | 改代码 | 改配置 |
| **复杂度** | 可支持任意复杂逻辑 | 受限于支持的字段类型 |
| **扩展性** | 低 | 高 |
| **适用场景** | 复杂表单、特殊交互 | 标准表单、快速原型 |
| **当前使用** | CommissionForm、PaperForm | 试验功能 |

---

## 🚦 当前状态与未来规划

### ✅ 已完成
- [x] 创建 DynamicForm 组件
- [x] 支持10+种字段类型
- [x] 表单验证机制
- [x] 在配置页面集成预览功能
- [x] 提供示例和文档

### 🎯 适用场景
1. **快速原型**：测试新文件类型的表单布局
2. **简单表单**：字段较少、无复杂交互的表单
3. **学习测试**：了解动态表单的工作原理

### ⚠️ 限制
1. **不支持复杂交互**：如子表添加/删除、字段联动
2. **不支持自定义组件**：只能使用预定义的字段类型
3. **当前为试验功能**：CommissionForm和PaperForm仍使用硬编码方式

### 📅 未来可能
- 如果需要频繁添加新文件类型 → 考虑完全迁移到动态表单
- 如果仅有少数文件类型 → 保持硬编码方式
- 混合模式：简单表单用动态，复杂表单用硬编码

---

## ❓ 常见问题

### Q: 动态表单能完全替代 CommissionForm 吗？
**A**: 目前不能。CommissionForm 有复杂的子表操作（test_items、special_tests）、自定义校验逻辑等，动态表单暂不支持。

### Q: 如何支持新的字段类型？
**A**: 需要在 `DynamicForm/index.vue` 组件中添加相应的模板和逻辑。

### Q: 预览表单的数据会保存吗？
**A**: 不会。预览功能只用于测试，不会保存数据。

### Q: 生产环境能用吗？
**A**: 可以，但建议先在测试环境充分测试。当前主要作为原型工具。

---

## 📚 参考资源

- **组件代码**: `frontend/src/components/DynamicForm/index.vue`
- **使用示例**: `frontend/src/views/FileTypeConfig/index.vue`
- **Element Plus 表单文档**: https://element-plus.org/zh-CN/component/form.html

---

**最后更新**: 2025-11-15  
**版本**: v1.0.0  
**状态**: ✅ 试验功能，可用于测试

