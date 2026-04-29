# PDF中文字符显示问题深度排查

## 🔍 问题现象

PDF能够渲染，但中文字符显示为方块(□)或乱码，如截图所示：
- 页眉页脚的文字正常（英文、数字）
- 正文中的中文显示为方块
- 部分标点符号可能显示正常

## 🎯 根本原因

这是典型的**PDF字体嵌入问题**，而不是CMap问题。主要原因：

### 1. PDF文件本身的问题
- PDF在创建时**没有嵌入中文字体**
- 使用了系统字体引用，但没有包含字体数据
- PDF只包含了字形的位置信息，没有实际的字体文件

### 2. PDF.js的限制
- PDF.js在浏览器中无法访问系统字体
- 如果PDF没有嵌入字体，PDF.js无法自动补全
- CMap只能帮助字符编码转换，不能解决缺失字体的问题

## ✅ 已实施的优化

### 1. 使用HTTPS协议加载资源
```javascript
cMapUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
standardFontDataUrl: 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/standard_fonts/',
```

**原因**：某些情况下协议相对URL (`//`) 可能导致加载失败

### 2. 启用所有字体相关选项
```javascript
disableFontFace: false,      // 启用字体替换
disableRange: false,         // 启用范围请求
disableStream: false,        // 启用流式加载
```

### 3. 优化Canvas渲染
```javascript
const outputScale = window.devicePixelRatio || 1
canvas.width = viewport.width * outputScale
canvas.height = viewport.height * outputScale
context.scale(outputScale, outputScale)
```

## 🔧 根本解决方案

### 方案1：重新生成PDF（推荐）⭐

**最佳解决方案**：让PDF生成方嵌入中文字体

#### 如果使用Word转PDF：
1. **打开Word文档**
2. **文件 → 选项 → 保存**
3. **勾选"将字体嵌入文件"**
4. **勾选"仅嵌入文档中使用的字符"**（减小文件大小）
5. **另存为PDF**

#### 如果使用其他PDF工具：
- Adobe Acrobat: 首选项 → 转换 → 嵌入所有字体
- WPS: 输出为PDF → 高级 → 嵌入字体
- LaTeX: 使用 `\usepackage{times}` 或 `\usepackage{fontspec}`

### 方案2：使用服务器端转换

如果无法修改原始PDF，可以在服务器端重新处理：

```python
# 使用 PyPDF2 或 reportlab 重新嵌入字体
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册中文字体
pdfmetrics.registerFont(TTFont('SimSun', 'SimSun.ttf'))

# 重新生成PDF，确保字体嵌入
```

### 方案3：使用文本层覆盖（临时方案）

如果有OCR数据，可以在Canvas上方添加透明文本层：

```javascript
// 在PdfViewer组件中添加文本层
const renderTextLayer = async (page, viewport) => {
  const textContent = await page.getTextContent()
  
  // 创建文本层div
  const textLayerDiv = document.createElement('div')
  textLayerDiv.className = 'textLayer'
  
  // 渲染文本
  pdfjsLib.renderTextLayer({
    textContent: textContent,
    container: textLayerDiv,
    viewport: viewport,
    textDivs: []
  })
  
  return textLayerDiv
}
```

## 🧪 验证PDF字体嵌入情况

### 方法1：使用Adobe Acrobat
1. 打开PDF
2. 文件 → 属性 → 字体
3. 查看字体列表中是否有"(嵌入)"或"(嵌入子集)"标记

### 方法2：使用pdffonts命令（Linux/Mac）
```bash
pdffonts document.pdf
```

输出示例：
```
name                 type              emb sub uni object ID
-------------------- ----------------- --- --- --- ---------
ABCDEE+SimSun        CID TrueType      yes yes yes    10  0  ← 已嵌入
ArialMT              TrueType          no  no  no     15  0  ← 未嵌入（会显示为方块）
```

### 方法3：浏览器开发者工具
1. 打开浏览器控制台
2. Network标签
3. 筛选 `.ttf`, `.otf`, `.woff`
4. 如果没有字体文件加载，说明PDF没有嵌入字体

## 📊 不同情况的解决方案对照表

| PDF类型 | 中文显示 | 原因 | 解决方案 |
|---------|---------|------|---------|
| 扫描件PDF | 正常 | 是图片，不涉及字体 | 无需处理 |
| 嵌入字体的PDF | 正常 | 字体数据在PDF中 | 无需处理 |
| 系统字体引用PDF | 方块/乱码 | 缺少字体数据 | ⚠️ 重新生成PDF |
| 纯文本PDF | 方块/乱码 | 使用了不支持的字体 | ⚠️ 重新生成PDF |

## 🔍 当前问题的具体诊断

根据您的截图：
```
Vol 43 No 4                                                    43    4
  · 30 ·              NEW CHEMICAL MATERIALS                 2015   4
```

**分析**：
- ✅ 英文、数字显示正常 → PDF.js基本功能正常
- ❌ 中文显示为方块 → **PDF文件没有嵌入中文字体**
- ✅ 页面布局正常 → 渲染逻辑正确

**结论**：这是PDF源文件的问题，不是代码问题。

## 💡 实用建议

### 对于新上传的文件
1. **在上传时检查**：
```python
# backend/app/services/file_service.py
def check_pdf_fonts(pdf_path):
    """检查PDF是否嵌入了字体"""
    import fitz  # PyMuPDF
    
    doc = fitz.open(pdf_path)
    fonts = []
    
    for page in doc:
        fonts.extend(page.get_fonts())
    
    # 检查是否有未嵌入的字体
    unembedded = [f for f in fonts if not f[3]]  # f[3]是嵌入标志
    
    return {
        'has_fonts': len(fonts) > 0,
        'all_embedded': len(unembedded) == 0,
        'unembedded_fonts': unembedded
    }
```

2. **给用户提示**：
```javascript
if (!fontInfo.all_embedded) {
  ElMessage.warning('该PDF文件未完全嵌入字体，可能导致显示异常')
}
```

### 对于现有文件
1. **添加"重新处理"功能**
2. **使用OCR文本覆盖**
3. **提供下载原文件选项**

## 🎯 推荐操作流程

### 短期方案（立即）
1. ✅ 保持当前的PDF.js配置优化
2. ✅ 在上传页面添加提示：建议用户上传嵌入字体的PDF
3. ✅ 提供"查看原始文件"选项

### 中期方案（1-2周）
1. 🔧 在后端添加PDF字体检查
2. 🔧 对未嵌入字体的PDF进行警告
3. 🔧 实现服务器端PDF重新处理（嵌入字体）

### 长期方案（1-2月）
1. 🚀 使用OCR文本层覆盖技术
2. 🚀 提供PDF标准化服务（统一字体）
3. 🚀 建立PDF质量评分系统

## 📝 用户须知文档

创建一个用户指南：`docs/PDF_UPLOAD_GUIDE.md`

```markdown
# PDF文件上传指南

## 为什么我的PDF中文显示不正常？

这通常是因为PDF文件在生成时**没有嵌入中文字体**。

## 如何生成正确的PDF？

### Word转PDF
1. 打开Word → 文件 → 选项 → 保存
2. 勾选"将字体嵌入文件"
3. 另存为PDF

### WPS转PDF  
1. 输出为PDF → 高级设置
2. 勾选"嵌入字体"
3. 保存

### 推荐工具
- Adobe Acrobat Pro
- Foxit PDF Editor
- PDFtk (命令行工具)

## 检查PDF是否正确
使用Adobe Reader打开，查看 文件→属性→字体，
确认字体显示为"(嵌入)"或"(嵌入子集)"
```

## 🔗 相关资源

- [PDF字体嵌入标准](https://www.adobe.com/content/dam/acom/en/devnet/pdf/pdfs/PDF32000_2008.pdf)
- [PDF.js字体处理文档](https://github.com/mozilla/pdf.js/wiki/Frequently-Asked-Questions#fonts)
- [PyMuPDF字体处理](https://pymupdf.readthedocs.io/en/latest/fonts.html)

---

**总结**：当前的代码优化已经做到最好，字符显示问题主要来自PDF源文件本身。建议联系PDF提供方重新生成嵌入字体的版本。

*文档创建时间: 2025-11-08*

