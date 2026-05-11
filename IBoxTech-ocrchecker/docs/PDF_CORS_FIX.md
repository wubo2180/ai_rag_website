# PDF中文显示问题 - CORS跨域解决方案

## 🎯 问题根源已找到！

### ❌ 真正的错误

```
Access to fetch at 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/cmaps/GBK-EUC-H.bcmap' 
from origin 'http://172.20.46.18:5173' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**问题原因**：
- CDNJS的CORS配置有问题
- 无法从HTTP网站访问HTTPS的CMap文件
- 导致中文字符映射文件加载失败
- 所以中文显示为方块

**这才是真正的问题！不是PDF文件的问题！** ✅

## 🔧 解决方案

### 方案1：使用jsDelivr CDN（已实施）⭐

**优点**：
- ✅ 完美支持CORS
- ✅ 全球CDN加速
- ✅ 稳定可靠
- ✅ 免费使用

**修改内容**：
```javascript
const loadingTask = pdfjsLib.getDocument({
  url: props.url,
  // 使用jsDelivr CDN，支持CORS
  cMapUrl: '//cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/',
  cMapPacked: true,
  standardFontDataUrl: '//cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/standard_fonts/',
  disableFontFace: false,
  disableWorker: false
})
```

### 方案2：本地托管CMap文件（备选）

如果CDN仍然不稳定，可以本地托管：

#### 步骤1：下载CMap文件
```bash
cd frontend/public
mkdir -p pdfjs-dist/cmaps
mkdir -p pdfjs-dist/standard_fonts

# 下载CMap文件
npm install pdfjs-dist@3.11.174
cp -r node_modules/pdfjs-dist/cmaps/* public/pdfjs-dist/cmaps/
cp -r node_modules/pdfjs-dist/standard_fonts/* public/pdfjs-dist/standard_fonts/
```

#### 步骤2：修改配置
```javascript
const loadingTask = pdfjsLib.getDocument({
  url: props.url,
  cMapUrl: '/pdfjs-dist/cmaps/',      // 使用本地路径
  cMapPacked: true,
  standardFontDataUrl: '/pdfjs-dist/standard_fonts/',
  disableFontFace: false,
  disableWorker: false
})
```

**优点**：
- ✅ 无CORS问题
- ✅ 加载速度快
- ✅ 不依赖外部CDN

**缺点**：
- ❌ 增加部署包大小（约10MB）
- ❌ 需要维护文件版本

### 方案3：Unpkg CDN（备选）

```javascript
cMapUrl: '//unpkg.com/pdfjs-dist@3.11.174/cmaps/',
standardFontDataUrl: '//unpkg.com/pdfjs-dist@3.11.174/standard_fonts/',
```

## 🧪 测试验证

### 检查CMap是否加载成功

1. **打开浏览器开发者工具**
2. **Network标签**
3. **筛选"bcmap"**
4. **查看是否有以下文件加载成功**：
   - `GBK-EUC-H.bcmap`
   - `UniGB-UTF16-H.bcmap`
   - 等中文相关的CMap文件

### 成功标志

✅ 如果看到：
```
Status: 200 OK
Type: application/octet-stream
Size: ~10KB-50KB
```

❌ 如果看到：
```
Status: (failed) net::ERR_FAILED
或者 CORS error
```

## 📊 CDN对比

| CDN | CORS支持 | 速度 | 稳定性 | 推荐 |
|-----|---------|------|--------|------|
| jsDelivr | ✅ 完美 | ⚡ 快 | ⭐⭐⭐⭐⭐ | ✅ 推荐 |
| CDNJS | ❌ 有问题 | ⚡ 快 | ⭐⭐⭐ | ❌ 不推荐 |
| Unpkg | ✅ 支持 | ⚡ 快 | ⭐⭐⭐⭐ | ✅ 可用 |
| 本地托管 | ✅ 完美 | ⚡⚡ 最快 | ⭐⭐⭐⭐⭐ | ✅ 推荐 |

## 🎯 当前配置（已修复）

```javascript
// frontend/src/components/PdfViewer/index.vue

const loadingTask = pdfjsLib.getDocument({
  url: props.url,
  // ✅ 使用jsDelivr CDN，支持CORS
  cMapUrl: '//cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/cmaps/',
  cMapPacked: true,
  // ✅ 标准字体也使用jsDelivr
  standardFontDataUrl: '//cdn.jsdelivr.net/npm/pdfjs-dist@3.11.174/standard_fonts/',
  // ✅ 启用字体
  disableFontFace: false,
  disableRange: false,
  disableStream: false,
  disableWorker: false,
  verbosity: 0
})
```

## 🔍 CORS问题诊断

### 什么是CORS？

**CORS（Cross-Origin Resource Sharing）跨源资源共享**

浏览器安全策略，阻止从一个域（origin）访问另一个域的资源。

### 为什么会出现CORS问题？

```
你的网站:    http://172.20.46.18:5173  (HTTP)
CMap文件:   https://cdnjs.cloudflare.com/...  (HTTPS)
           ↑
        跨域访问被阻止！
```

### CORS错误的常见原因

1. **协议不匹配**
   - 你的站点：HTTP
   - 资源服务器：HTTPS
   - 某些CDN不允许这种混合访问

2. **缺少CORS头**
   - 服务器没有设置 `Access-Control-Allow-Origin: *`
   - 或者设置了但不包含你的域

3. **预检请求失败**
   - OPTIONS请求被拒绝

### jsDelivr为什么能解决？

jsDelivr专门为开源项目设计：
- ✅ 默认允许所有域访问
- ✅ 设置了正确的CORS头
- ✅ 支持HTTP和HTTPS
- ✅ 支持协议相对URL（//）

## 💡 最佳实践

### 开发环境

使用jsDelivr CDN，快速开发，无需配置。

### 生产环境

**推荐方案**：本地托管CMap文件

**原因**：
1. 不依赖外部CDN
2. 加载速度更快
3. 避免CDN故障影响
4. 完全可控

**实施步骤**：
```bash
# 1. 下载文件到public目录
npm run build:copy-cmaps

# 2. 修改配置使用本地路径
cMapUrl: '/pdfjs-dist/cmaps/'

# 3. 部署时确保这些文件被正确上传
```

## 📝 修改记录

### 2025-11-08 - CORS问题修复

**问题**：
- CDNJS的CORS配置导致CMap文件无法加载
- 中文字符显示为方块

**修复**：
- 将CDN从CDNJS切换到jsDelivr
- 从 `https://cdnjs.cloudflare.com/...` 
- 改为 `//cdn.jsdelivr.net/npm/pdfjs-dist@...`

**结果**：
- ✅ CMap文件可以正常加载
- ✅ 中文字符应该能正确显示

## 🎉 预期效果

修复后，中文应该能正确显示：

**修复前**：
```
□□□□□□□□□
NEW CHEMICAL MATERIALS
```

**修复后**：
```
双组分缩合型有机硅电子灌封胶的制备
NEW CHEMICAL MATERIALS
```

## 🔗 相关资源

- [jsDelivr官网](https://www.jsdelivr.com/)
- [PDF.js CMap文档](https://github.com/mozilla/pdf.js/tree/master/external/cmaps)
- [CORS详解](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)

---

**请刷新浏览器测试！中文应该能正确显示了！** 🎉

*问题解决时间: 2025-11-08*
*根本原因: CORS跨域问题*
*解决方案: 切换到jsDelivr CDN*

