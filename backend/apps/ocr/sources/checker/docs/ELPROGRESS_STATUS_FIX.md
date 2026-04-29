# ElProgress Status 属性修复

## 问题描述

浏览器控制台出现以下警告：
```
Invalid prop: validation failed for prop "status". 
Expected one of ["", "success", "exception", "warning"], 
got value "uploading".
```

## 根本原因

Element Plus 的 `<el-progress>` 组件的 `status` 属性只接受以下值：
- `""` (空字符串) - 默认蓝色进度条
- `"success"` - 绿色进度条
- `"exception"` - 红色进度条
- `"warning"` - 黄色进度条

但代码中使用了 `"uploading"` 和 `"error"`，这些都不是有效值。

## 修复内容

### 1. 修改 `frontend/src/stores/app.js`

**修改前**:
```javascript
uploadProgress: {
  show: false,
  percentage: 0,
  status: 'uploading' // ❌ 无效值
}

showUploadProgress() {
  this.uploadProgress.status = 'uploading' // ❌
}

updateUploadProgress(percentage, status = 'uploading') { // ❌
  this.uploadProgress.status = status
}
```

**修改后**:
```javascript
uploadProgress: {
  show: false,
  percentage: 0,
  status: '' // ✅ 有效值（默认蓝色）
}

showUploadProgress() {
  this.uploadProgress.status = '' // ✅ 上传中使用空字符串
}

updateUploadProgress(percentage, status = '') { // ✅
  this.uploadProgress.status = status
  // status 可选值: '' (默认), 'success', 'exception', 'warning'
}
```

### 2. 修改 `frontend/src/views/FileUpload/index.vue`

**修改前**:
```javascript
appStore.updateUploadProgress(0, 'error') // ❌ 无效值
```

**修改后**:
```javascript
appStore.updateUploadProgress(0, 'exception') // ✅ 有效值
```

## 状态值对应关系

| 场景 | 使用的 status 值 | 进度条颜色 |
|------|----------------|-----------|
| 上传中 | `''` (空字符串) | 蓝色 |
| 上传成功 | `'success'` | 绿色 |
| 上传失败 | `'exception'` | 红色 |
| 警告 | `'warning'` | 黄色 |

## 验证

修复后，浏览器控制台将不再出现 `Invalid prop` 警告。

进度条的视觉效果：
- **上传中**: 蓝色进度条（使用默认样式）
- **上传完成**: 绿色进度条，显示 ✓
- **上传失败**: 红色进度条，显示 ✗

## 相关文件

- `frontend/src/stores/app.js` - Pinia store 定义
- `frontend/src/views/FileUpload/index.vue` - 文件上传页面
- `frontend/src/components/Layout/index.vue` - 头部布局（显示进度条）

## 参考文档

Element Plus Progress 组件文档: https://element-plus.org/zh-CN/component/progress.html

---

**修复日期**: 2025-11-05  
**状态**: ✅ 已完成


