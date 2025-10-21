# Documents 页面滚动问题修复

## 问题描述
访问 `http://localhost:3000/documents` 时，页面无法下拉滚动。

## 问题原因

### 1. App.vue 布局限制
```css
.main-content {
  overflow: hidden; /* 阻止了滚动 */
}
```

### 2. Documents.vue 缺少滚动配置
```css
.documents-container {
  /* 没有设置 height 和 overflow */
}
```

## 解决方案

### 修改 1: App.vue
**文件**: `frontend/src/App.vue`

**修改前**:
```css
.main-content {
  flex: 1;
  overflow: hidden; /* 移除滚动，让子组件自己处理 */
  width: 100%;
  height: 100%;
}
```

**修改后**:
```css
.main-content {
  flex: 1;
  overflow: auto; /* 允许滚动 */
  width: 100%;
  height: 100%;
}
```

### 修改 2: Documents.vue
**文件**: `frontend/src/views/Documents.vue`

**修改前**:
```css
.documents-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}
```

**修改后**:
```css
.documents-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}
```

## 效果
- ✅ 页面内容超出视口时可以垂直滚动
- ✅ 保持横向不滚动（防止横向溢出）
- ✅ 导航栏固定，内容区域可滚动
- ✅ 响应式布局正常工作

## 测试建议
1. 访问 http://localhost:3000/documents
2. 添加多个分类和文件夹，使内容超出一屏
3. 验证页面可以正常滚动
4. 检查其他页面（如知识图谱）是否受影响

## 注意事项
- 修改了全局布局 (`App.vue`)，可能影响其他页面
- 如果其他页面出现滚动问题，需要在对应组件中单独处理
- 建议测试所有路由页面，确保布局正常
