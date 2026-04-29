# 本地CMap配置完成

## ✅ 配置完成

### 📁 文件结构

```
frontend/public/
└── cmaps/                    # CMap字符映射文件
    ├── Adobe-GB1-*.bcmap     # 中文GB编码
    ├── GBK-*.bcmap           # GBK编码
    ├── UniGB-*.bcmap         # Unicode GB映射
    └── ...                   # 共169个文件
```

### 🔧 配置内容

**文件**: `frontend/src/components/PdfViewer/index.vue`

```javascript
const loadingTask = pdfjsLib.getDocument({
  url: props.url,
  // ✅ 使用本地托管的CMap文件
  cMapUrl: '/cmaps/',
  cMapPacked: true,
  // ✅ 启用所有字体相关功能
  disableFontFace: false,
  disableRange: false,
  disableStream: false,
  disableWorker: false,
  verbosity: 0
})
```

### 🎯 优势

使用本地CMap的好处：

1. **✅ 无CORS问题**
   - 不需要跨域请求
   - 完全避免CORS错误

2. **✅ 加载速度快**
   - 本地文件，无网络延迟
   - 不依赖外部CDN

3. **✅ 稳定可靠**
   - 不受CDN故障影响
   - 不受网络环境限制

4. **✅ 离线可用**
   - 内网环境可正常使用
   - 无需互联网连接

### 📊 CMap文件统计

- **总文件数**: 169个
- **文件大小**: 约10MB
- **关键中文CMap**:
  - `GBK-EUC-H.bcmap` - GBK编码（水平）
  - `GB-EUC-H.bcmap` - GB编码（水平）
  - `UniGB-UTF16-H.bcmap` - Unicode GB映射
  - `Adobe-GB1-*.bcmap` - Adobe GB字符集

### 🧪 测试验证

#### 1. 检查文件访问

在浏览器中直接访问：
```
http://172.20.46.18:5173/cmaps/GBK-EUC-H.bcmap
```

应该能直接下载该文件（约20KB）

#### 2. 检查Network请求

1. 打开浏览器开发者工具
2. Network标签
3. 筛选 "bcmap"
4. 刷新PDF预览页面

**应该看到**：
```
Request URL: http://172.20.46.18:5173/cmaps/GBK-EUC-H.bcmap
Status: 200 OK
Type: application/octet-stream
Size: ~20KB
```

#### 3. 检查中文显示

打开包含中文的PDF，中文应该正常显示：
```
✅ 双组分缩合型有机硅电子灌封胶的制备
✅ NEW CHEMICAL MATERIALS
✅ 2015年4月
```

### 🔍 故障排查

#### 问题1: 404错误

**错误**: `GET http://172.20.46.18:5173/cmaps/GBK-EUC-H.bcmap 404 (Not Found)`

**原因**: Vite开发服务器没有正确提供public目录文件

**解决**:
```bash
# 检查文件是否存在
ls /home/h3c/workspace/IBoxTech-ocrchecker/frontend/public/cmaps/

# 重启Vite开发服务器
npm run dev
```

#### 问题2: 仍然有CORS错误

**原因**: 可能缓存了旧配置

**解决**:
1. 清除浏览器缓存（Ctrl + Shift + Delete）
2. 硬刷新页面（Ctrl + F5）
3. 关闭并重新打开浏览器

#### 问题3: 中文仍显示为方块

**可能原因**:
1. CMap文件损坏 → 重新下载
2. PDF本身没有嵌入字体 → 这是PDF源文件问题
3. 浏览器缓存 → 清除缓存重试

**检查步骤**:
```bash
# 1. 检查CMap文件完整性
ls -lh /home/h3c/workspace/IBoxTech-ocrchecker/frontend/public/cmaps/ | head -20

# 2. 检查关键文件是否存在
file /home/h3c/workspace/IBoxTech-ocrchecker/frontend/public/cmaps/GBK-EUC-H.bcmap
```

### 📦 生产环境部署

#### Nginx配置

如果使用Nginx部署，确保static文件正确配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
    }
    
    # CMap文件缓存配置
    location /cmaps/ {
        root /var/www/html;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 构建打包

确保CMap文件被正确打包：

```bash
# 构建生产版本
npm run build

# 检查dist目录
ls -la dist/cmaps/

# 应该包含169个.bcmap文件
```

### 🔄 更新CMap文件

如果需要更新到新版本：

```bash
cd /home/h3c/workspace/IBoxTech-ocrchecker/frontend/public

# 备份旧版本
mv cmaps cmaps.backup

# 下载新版本
npm install pdfjs-dist@latest
cp -r node_modules/pdfjs-dist/cmaps ./

# 验证文件数量
ls cmaps/ | wc -l  # 应该是169个文件
```

### 📝 维护检查清单

定期检查：

- [ ] CMap文件完整性（169个文件）
- [ ] 文件权限（可读）
- [ ] Web服务器配置（正确提供static文件）
- [ ] 浏览器控制台（无404错误）
- [ ] PDF预览功能（中文显示正常）

### 🎉 配置完成

**当前状态**：
- ✅ CMap文件已下载（169个文件）
- ✅ 配置已更新（使用本地路径）
- ✅ 无CORS依赖
- ✅ 准备就绪

**下一步**：
1. 刷新浏览器（Ctrl + F5）
2. 重新打开PDF预览
3. 检查中文是否正常显示
4. 查看浏览器控制台，确认无错误

---

**配置完成时间**: 2025-11-08
**CMap来源**: pdfjs-dist@3.11.174
**部署位置**: `/home/h3c/workspace/IBoxTech-ocrchecker/frontend/public/cmaps/`
**配置文件**: `frontend/src/components/PdfViewer/index.vue`

