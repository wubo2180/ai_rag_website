# 📝 Dify输出格式化说明

## 功能概述

聊天界面现已支持完整的Markdown格式化，包括：
- ✅ 美观的表格渲染
- ✅ 代码块语法高亮
- ✅ 标题、列表、引用
- ✅ 链接、图片、强调文本
- ✅ 自动换行和段落分隔

## 支持的Markdown语法

### 1. 表格 (Tables)

Dify输出示例：
```markdown
| 模型名称 | 提供商 | 特点 |
|---------|--------|------|
| GPT-5 | OpenAI | 强大的通用能力 |
| Claude4 | Anthropic | 长文本处理 |
| 通义千问 | 阿里云 | 中文优化 |
```

渲染效果：
- 渐变色表头（紫色渐变）
- 斑马纹行（交替背景色）
- 悬停高亮效果
- 圆角阴影美化

### 2. 代码块 (Code Blocks)

支持语法高亮的语言：
```python
def hello_world():
    print("Hello, Dify!")
    return True
```

```javascript
const greeting = () => {
    console.log("Hello from JavaScript");
};
```

```sql
SELECT * FROM users 
WHERE created_at > '2025-01-01';
```

特性：
- 深色主题代码块（GitHub风格）
- 自动语法高亮
- 等宽字体显示
- 水平滚动支持

### 3. 标题 (Headings)

```markdown
# 一级标题 - 带下划线
## 二级标题 - 带下划线
### 三级标题
#### 四级标题
```

### 4. 列表 (Lists)

**无序列表：**
```markdown
- 项目1
- 项目2
  - 子项目2.1
  - 子项目2.2
```

**有序列表：**
```markdown
1. 第一步
2. 第二步
3. 第三步
```

### 5. 文本强调

```markdown
**粗体文字**
*斜体文字*
~~删除线~~
`行内代码`
```

### 6. 引用 (Blockquotes)

```markdown
> 这是一个引用块
> 可以包含多行内容
```

效果：
- 左侧蓝色边框
- 浅灰色背景
- 斜体文字

### 7. 分割线

```markdown
---
```

### 8. 链接和图片

```markdown
[链接文字](https://example.com)
![图片描述](https://example.com/image.jpg)
```

## 在Dify工作流中使用

### 方法1：在文本输出节点中直接使用Markdown

```
您好！以下是数据分析结果：

## 销售数据统计

| 月份 | 销售额 | 增长率 |
|------|--------|--------|
| 1月  | 100万  | -      |
| 2月  | 120万  | 20%    |
| 3月  | 150万  | 25%    |

### 关键发现

1. **销售额持续增长**
2. 2月增长率达到**20%**
3. 需要关注3月的高增长

### 建议代码实现

\`\`\`python
def calculate_growth(current, previous):
    return ((current - previous) / previous) * 100
\`\`\`
```

### 方法2：使用变量拼接

在Dify工作流中：
```
{{table_header}}
{{table_rows}}

{{analysis_text}}

{{code_block}}
```

### 方法3：使用LLM直接生成Markdown格式

提示词示例：
```
请用Markdown格式输出分析结果，包括：
1. 使用表格展示数据
2. 使用标题分隔章节
3. 使用代码块展示代码示例
4. 使用列表总结要点
```

## 实现细节

### 使用的库
1. **marked.js** (v11.1.1) - Markdown解析和渲染
2. **highlight.js** (v11.9.0) - 代码语法高亮
3. **DOMPurify** (v3.0.6) - XSS防护

### 配置选项
```javascript
marked.setOptions({
    breaks: true,      // 支持换行
    gfm: true,         // GitHub风格Markdown
    tables: true,      // 支持表格
    highlight: function(code, lang) {
        // 自动代码高亮
    }
});
```

### 安全性
- 使用DOMPurify清理HTML
- 白名单标签和属性
- 防止XSS攻击
- 安全的链接处理

## CSS样式特性

### 表格样式
- 🎨 紫色渐变表头
- 🦓 斑马纹行样式
- ✨ 悬停效果
- 📦 圆角和阴影

### 代码块样式
- 🌙 深色主题（类似VS Code）
- 🎯 语法高亮
- 📏 等宽字体
- 📱 响应式设计

### 排版优化
- 📖 合适的行高和间距
- 🔤 清晰的字体层级
- 🎨 协调的颜色方案
- 💫 平滑的过渡效果

## 测试示例

发送以下消息测试格式化：

```
请用表格形式展示三个AI模型的对比，包括名称、优点和价格
```

```
写一段Python代码实现快速排序
```

```
用列表形式总结项目管理的5个关键步骤
```

## 常见问题

**Q: 表格不显示怎么办？**
A: 确保Markdown表格语法正确，每行用`|`分隔，表头下方要有分隔线

**Q: 代码高亮不工作？**
A: 检查代码块是否用三个反引号包裹，并指定语言类型

**Q: 如何处理长表格？**
A: 表格会自动适应容器宽度，超长内容会自动换行

## 更新日志

### v1.0 (2025-10-12)
- ✅ 集成Markdown渲染
- ✅ 添加表格美化样式
- ✅ 实现代码语法高亮
- ✅ 增加XSS防护
- ✅ 优化排版和样式

---

**提示**: 在Dify工作流中使用Markdown格式输出，可以获得最佳的展示效果！
