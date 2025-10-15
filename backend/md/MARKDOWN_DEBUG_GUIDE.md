# 🔍 Markdown格式化问题诊断指南

## 问题症状
Dify返回的结果没有格式化输出，表格、代码块等显示为纯文本。

## 诊断步骤

### 1. 测试Markdown渲染库是否正常工作

访问测试页面：
```
http://127.0.0.1:8000/chat/markdown-test/
```

**检查项**:
- ✅ 所有库显示"已加载"
- ✅ 点击"测试表格"显示渲染后的表格
- ✅ 点击"测试代码"显示语法高亮的代码

**如果测试页面正常**:
→ 说明库本身没问题，问题在聊天页面的集成

**如果测试页面异常**:
→ CDN加载问题，检查网络连接

### 2. 检查浏览器控制台

打开聊天页面 `http://127.0.0.1:8000/chat/`

按 `F12` 打开开发者工具，查看Console标签

**应该看到**:
```
Marked库加载状态: ✅ 已加载
Highlight.js加载状态: ✅ 已加载
DOMPurify加载状态: ✅ 已加载
```

**如果显示"❌ 未加载"**:
→ CDN资源加载失败

**解决方法**:
1. 检查网络连接
2. 尝试访问CDN直接链接测试：
   - https://cdn.jsdelivr.net/npm/marked@11.1.1/marked.min.js
   - https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/highlight.min.js
3. 如果无法访问，考虑使用本地文件或其他CDN

### 3. 测试AI响应

发送消息后，在控制台应该看到：
```
开始渲染Markdown，内容长度: xxx
内容预览: ...
Markdown渲染完成，HTML长度: xxx
✅ HTML已清理并插入
✅ 代码高亮应用完成
```

**如果没有这些日志**:
→ addMessage函数可能走了其他分支

**如果有错误日志**:
→ 查看具体错误信息

### 4. 检查Dify返回的内容格式

在控制台查看"内容预览"，检查Dify是否真的返回了Markdown格式：

**正确的Markdown格式**:
```markdown
| 列1 | 列2 |
|-----|-----|
| A   | B   |
```

**如果Dify返回的是纯文本**:
```
列1  列2
A    B
```
→ 需要在Dify工作流中配置输出Markdown格式

## 常见问题和解决方案

### Q1: 库显示"已加载"但渲染没效果

**可能原因**: 
- Dify返回的不是Markdown格式
- 内容被当作用户消息处理（纯文本）

**解决方法**:
1. 检查控制台的"内容预览"
2. 确认Dify输出是Markdown格式
3. 在Dify提示词中明确要求：
```
请用Markdown格式回答，使用表格展示数据，使用代码块展示代码
```

### Q2: CDN加载失败

**症状**: 库显示"❌ 未加载"

**解决方法A**: 使用备用CDN

编辑 `templates/chat/index.html`:
```html
<!-- 使用unpkg作为备用 -->
<script src="https://unpkg.com/marked@11.1.1/marked.min.js"></script>
<script src="https://unpkg.com/@highlightjs/cdn-assets@11.9.0/highlight.min.js"></script>
<script src="https://unpkg.com/dompurify@3.0.6/dist/purify.min.js"></script>
```

**解决方法B**: 下载到本地

1. 下载库文件到 `static/js/`:
   - marked.min.js
   - highlight.min.js
   - purify.min.js

2. 修改引用：
```html
{% load static %}
<script src="{% static 'js/marked.min.js' %}"></script>
<script src="{% static 'js/highlight.min.js' %}"></script>
<script src="{% static 'js/purify.min.js' %}"></script>
```

### Q3: 表格显示但样式不对

**症状**: 表格是表格，但没有渐变色、斑马纹等

**原因**: CSS样式未应用

**检查**:
1. 在开发者工具中检查表格元素
2. 查看是否有 `.message.ai .message-content table` 样式
3. 检查CSS是否被其他样式覆盖

**解决**: 确保CSS在 `<style>` 标签中，且在页面底部没有被覆盖

### Q4: 代码块没有语法高亮

**症状**: 代码块显示但是纯白色背景

**原因**: 
- highlight.js CSS未加载
- 代码块没有指定语言

**解决**:
1. 确认CSS链接存在：
```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/highlightjs/cdn-release@11.9.0/build/styles/github.min.css">
```

2. 在Dify中使用代码块时指定语言：
````markdown
```python
def hello():
    print("Hello!")
```
````

### Q5: 只有部分内容被格式化

**症状**: 表格渲染了，但代码块没有

**检查**: 
1. 查看控制台是否有警告
2. 检查Markdown语法是否正确

**常见语法错误**:

❌ 错误：
````
| 列1 | 列2
|---|---
| A | B
````

✅ 正确：
```markdown
| 列1 | 列2 |
|-----|-----|
| A   | B   |
```

## 调试技巧

### 1. 使用测试Markdown

在聊天中发送：
```
请帮我测试Markdown渲染：

| 名称 | 数值 |
|------|------|
| 测试 | 100  |

代码测试：
```python
print("test")
```

**粗体** 和 *斜体*
```

### 2. 查看生成的HTML

在控制台运行：
```javascript
// 获取最后一条AI消息的HTML
const lastAI = document.querySelector('.message.ai:last-child .message-content');
console.log(lastAI.innerHTML);
```

### 3. 手动测试渲染

在控制台运行：
```javascript
const testMarkdown = '| A | B |\n|---|---|\n| 1 | 2 |';
const html = marked.parse(testMarkdown);
console.log(html);
```

## 验证清单

运行聊天应用前，确认：

- [ ] 浏览器控制台显示所有库"已加载"
- [ ] 测试页面表格正常渲染
- [ ] 测试页面代码正常高亮
- [ ] 聊天页面发送消息时有渲染日志
- [ ] Dify工作流配置为输出Markdown格式
- [ ] 提示词中包含"使用Markdown格式回答"

## 推荐的Dify提示词配置

在Dify的系统提示词中添加：

```
你是一个专业的AI助手。请遵循以下格式规则：

1. 使用Markdown格式回答所有问题
2. 数据展示使用表格：
   | 列名1 | 列名2 |
   |------|------|
   | 值1  | 值2  |

3. 代码展示使用代码块，指定语言：
   ```python
   code here
   ```

4. 要点使用列表：
   - 要点1
   - 要点2

5. 章节使用标题：
   ## 主要内容
   ### 子内容
```

## 获取帮助

如果以上步骤都无法解决问题：

1. 导出浏览器控制台的完整日志
2. 截图当前显示效果
3. 提供Dify返回的原始内容
4. 检查Django服务器日志

---

**更新时间**: 2025-10-12
**状态**: 已添加详细调试日志和测试页面
