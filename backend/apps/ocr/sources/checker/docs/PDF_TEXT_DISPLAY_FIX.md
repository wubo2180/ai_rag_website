# PDF预览文字显示不全问题修复

## 🔍 问题描述

用户反馈：PDF预览时有些文字看不见，怀疑是字体问题。

## 🎯 可能的原因

### 1. CMap字体映射问题 ⭐（最可能）
PDF.js需要CMap文件来正确渲染中文等特殊字符。如果CMap加载失败，会导致这些字符无法显示。

### 2. Canvas分辨率不足
在高DPI屏幕上，如果canvas分辨率设置不当，文字可能会模糊或显示不全。

### 3. PDF字体嵌入问题
某些PDF文件可能没有正确嵌入字体，或使用了特殊字体。

### 4. 缩放比例不合适
默认缩放可能导致某些文字被裁切。

## ✅ 已实施的修复

### 修复1：添加标准字体支持

**文件**: `frontend/src/components/PdfViewer/index.vue`

**修改**:
```javascript
const loadingTask = pdfjsLib.getDocument({
  url: props.url,
  cMapUrl: '//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/',
  cMapPacked: true,
  standardFontDataUrl: '//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/standard_fonts/',  // ✅ 新增
  disableWorker: false,
  verbosity: 0  // ✅ 新增：减少日志输出
})
```

**作用**: 
- 加载PDF标准字体数据，确保常用字体能正确显示
- 特别是处理未嵌入字体的PDF文件

### 修复2：提高Canvas渲染质量

**修改前**:
```javascript
canvas.width = viewport.width
canvas.height = viewport.height
```

**修改后**:
```javascript
// 提高canvas分辨率以获得更清晰的文字
const outputScale = window.devicePixelRatio || 1
canvas.width = viewport.width * outputScale
canvas.height = viewport.height * outputScale
canvas.style.width = viewport.width + 'px'
canvas.style.height = viewport.height + 'px'

// 缩放context以匹配高分辨率
context.scale(outputScale, outputScale)
```

**作用**:
- 根据设备像素比（devicePixelRatio）调整canvas分辨率
- 在高DPI屏幕（如Retina显示器）上，提供更清晰的文字渲染
- 避免文字模糊或显示不全

### 修复3：优化渲染参数

```javascript
const renderContext = {
  canvasContext: context,
  viewport: viewport,
  enableWebGL: false,              // ✅ 禁用WebGL（某些情况下会导致渲染问题）
  renderInteractiveForms: false    // ✅ 禁用交互表单渲染（提高性能）
}
```

## 🧪 测试验证

### 测试步骤

1. **清除浏览器缓存**
```bash
Ctrl + Shift + Delete（Chrome/Edge）
Command + Shift + Delete（Mac）
```

2. **刷新页面**
```bash
Ctrl + F5（硬刷新）
```

3. **测试不同PDF文件**
- ✅ 中文PDF
- ✅ 英文PDF
- ✅ 混合语言PDF
- ✅ 扫描件PDF
- ✅ 带表格的PDF

4. **测试不同缩放级别**
- 50%、75%、100%、125%、150%、200%

5. **检查浏览器控制台**
查看是否有CMap加载错误：
```
Failed to load resource: net::ERR_FAILED
cmaps/UniGB-UTF16-H
```

## 📊 问题排查清单

如果问题仍然存在，请检查：

### 1. 网络连接
- [ ] CDN是否可访问（cdnjs.cloudflare.com）
- [ ] CMap文件是否加载成功
- [ ] Standard fonts是否加载成功

**检查方法**:
打开浏览器开发者工具 → Network标签 → 筛选"cmaps"和"standard_fonts"

### 2. PDF文件本身
- [ ] PDF是否损坏
- [ ] PDF是否有密码保护
- [ ] PDF字体是否正确嵌入

**检查方法**:
用Adobe Acrobat或其他PDF阅读器打开，查看是否正常显示

### 3. 浏览器兼容性
- [ ] 浏览器版本是否过旧
- [ ] 是否启用了硬件加速
- [ ] Canvas API是否被禁用

**推荐浏览器**:
- Chrome 90+
- Edge 90+
- Firefox 88+
- Safari 14+

### 4. 特定文字问题
- [ ] 是否只有特定文字看不见（如中文、日文、韩文）
- [ ] 是否所有文字都看不见
- [ ] 放大后是否能看见

## 🔧 高级解决方案

### 方案1：本地托管CMap文件

如果CDN不稳定，可以下载CMap到本地：

```bash
# 下载CMap文件
cd frontend/public
mkdir cmaps standard_fonts
# 下载文件到对应目录
```

修改配置：
```javascript
cMapUrl: '/cmaps/',
standardFontDataUrl: '/standard_fonts/'
```

### 方案2：调整默认缩放

如果文字总是被裁切，修改默认缩放：

```javascript
const scale = ref(1.5)  // 从1.2改为1.5
```

### 方案3：强制重新渲染

添加强制刷新按钮：
```javascript
const forceRerender = async () => {
  await updateVisiblePages()
  ElMessage.success('PDF已重新渲染')
}
```

## 📝 配置说明

### PDF.js配置项

| 配置项 | 作用 | 推荐值 |
|--------|------|--------|
| `cMapUrl` | CMap文件路径 | CDN或本地路径 |
| `cMapPacked` | 使用压缩的CMap | `true` |
| `standardFontDataUrl` | 标准字体路径 | CDN或本地路径 |
| `disableWorker` | 禁用Web Worker | `false`（使用Worker） |
| `verbosity` | 日志级别 | `0`（生产环境） |

### Canvas渲染配置

| 配置项 | 作用 | 推荐值 |
|--------|------|--------|
| `outputScale` | 输出缩放比例 | `devicePixelRatio` |
| `enableWebGL` | 启用WebGL | `false`（更稳定） |
| `renderInteractiveForms` | 渲染表单 | `false`（提高性能） |

## 🎯 预期效果

修复后应该能够：
- ✅ 正确显示所有中文字符
- ✅ 正确显示英文、数字、符号
- ✅ 在高DPI屏幕上文字清晰
- ✅ 不同缩放级别下文字完整
- ✅ 特殊字体正确渲染

## 🔗 相关资源

- [PDF.js官方文档](https://mozilla.github.io/pdf.js/)
- [PDF.js GitHub](https://github.com/mozilla/pdf.js)
- [CMap Files说明](https://github.com/mozilla/pdf.js/tree/master/external/cmaps)

## 📞 如果问题仍未解决

请提供以下信息：

1. **浏览器信息**
   - 浏览器类型和版本
   - 操作系统

2. **PDF文件信息**
   - 文件大小
   - 页数
   - 是否能用其他PDF阅读器正常打开

3. **浏览器控制台截图**
   - Console标签
   - Network标签

4. **问题截图**
   - 显示不全的具体位置
   - 缩放级别

---

*修复完成时间: 2025-11-08*
*修改文件: `frontend/src/components/PdfViewer/index.vue`*

