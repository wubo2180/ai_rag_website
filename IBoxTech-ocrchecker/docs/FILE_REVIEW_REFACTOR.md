# 核对页面(FileReview)重构方案

## 📋 目标

重构核对页面，使其支持根据文件类型动态显示不同表单（委托单CommissionForm / 论文PaperForm）

## 🔍 当前状态

核对页面(FileReview)目前：
- ✅ 使用PdfViewer组件
- ✅ 支持OCR区域高亮和选择
- ❌ 硬编码委托单表单（约700行代码）
- ❌ 不支持其他文档类型

## 🎯 重构策略

### 核心思路

参考FileRecognize的重构方式：
1. 移除硬编码的委托单表单
2. 动态导入CommissionForm和PaperForm组件
3. 根据document_type_code渲染对应表单
4. 调整数据加载逻辑支持不同类型

### 主要改动

#### 1. 模板部分

**修改前**:
```vue
<div class="panel-content">
  <div v-if="loading.commissionData">...</div>
  <div v-else-if="commissionData">
    <!-- 700行硬编码的委托单表单 -->
  </div>
</div>
```

**修改后**:
```vue
<div class="panel-content">
  <div v-if="loading.formData">...</div>
  <component
    v-else-if="currentFormComponent && formData"
    :is="currentFormComponent"
    v-model="formData"
    :readonly="!isEditing"
    @update:modelValue="markAsChanged"
  />
  <div v-else>暂无数据</div>
</div>
```

#### 2. 脚本部分

**添加动态组件导入**:
```javascript
import PaperForm from '@/components/PaperForm/index.vue'
import CommissionForm from '@/components/CommissionForm/index.vue'
import { markRaw } from 'vue'
import { papersApi } from '@/api/papers'
```

**添加动态组件计算属性**:
```javascript
const currentFormComponent = computed(() => {
  if (!currentFile.value) return null
  
  const docType = currentFile.value.document_type_code
  console.log('🧩 当前文档类型:', docType)
  
  if (docType === 'paper') {
    return markRaw(PaperForm)
  } else if (docType === 'commission') {
    return markRaw(CommissionForm)
  }
  
  return markRaw(CommissionForm) // 默认委托单
})
```

**修改数据加载逻辑**:
```javascript
// 统一的formData
const formData = ref(null)
const loading = reactive({
  fileData: false,
  ocrData: false,
  formData: false,  // 替代commissionData loading
  saving: false
})

// 加载表单数据
const loadFormData = async (fileId) => {
  if (!currentFile.value) return
  
  const docType = currentFile.value.document_type_code
  
  if (docType === 'paper') {
    await loadPaperData(fileId)
  } else {
    await loadCommissionData(fileId)
  }
}

const loadPaperData = async (fileId) => {
  try {
    loading.formData = true
    const response = await papersApi.getPaperByFileId(fileId)
    if (response.data.success && response.data.data) {
      formData.value = response.data.data
    } else {
      formData.value = createEmptyPaperData()
    }
  } catch (error) {
    console.error('加载论文数据失败:', error)
    formData.value = createEmptyPaperData()
  } finally {
    loading.formData = false
  }
}

const loadCommissionData = async (fileId) => {
  try {
    loading.formData = true
    const response = await filesApi.getCommissionData(fileId)
    if (response.data.success && response.data.data) {
      formData.value = initializeCommissionData(response.data.data)
    } else {
      formData.value = initializeCommissionData({})
    }
  } catch (error) {
    console.error('加载委托数据失败:', error)
    formData.value = initializeCommissionData({})
  } finally {
    loading.formData = false
  }
}
```

**修改保存逻辑**:
```javascript
const saveChanges = async () => {
  try {
    isSaving.value = true
    const docType = currentFile.value?.document_type_code
    
    if (docType === 'paper') {
      await savePaperData()
    } else {
      await saveCommissionData()
    }
    
    isEditing.value = false
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}

const savePaperData = async () => {
  const fileId = route.params.fileId || route.params.id
  
  if (formData.value.文献编号) {
    // 更新
    await papersApi.updatePaper(formData.value.文献编号, formData.value)
  } else {
    // 创建
    await papersApi.createPaper({
      file_id: parseInt(fileId),
      ...formData.value
    })
  }
}

const saveCommissionData = async () => {
  const fileId = route.params.fileId || route.params.id
  const payload = {
    file_id: parseInt(fileId),
    commission_data: formData.value
  }
  await filesApi.updateCommissionData(fileId, payload)
}
```

## 📝 实施步骤

### 步骤1: 准备工作 ✅
-已完成分析当前实现

### 步骤2: 修改模板
1. ✅ 修改panel-header标题为动态
2. ⏳ 删除硬编码的委托单表单（line 132-836）
3. ⏳ 添加动态组件渲染

### 步骤3: 修改脚本
1. ⏳ 添加组件导入
2. ⏳ 添加currentFormComponent计算属性
3. ⏳ 修改数据状态（commissionData -> formData）
4. ⏳ 修改loadFormData逻辑
5. ⏳ 修改saveChanges逻辑
6. ⏳ 添加论文数据操作方法

### 步骤4: 测试
1. ⏳ 测试委托单核对功能
2. ⏳ 测试论文核对功能
3. ⏳ 测试保存功能
4. ⏳ 测试PDF高亮联动

## 🚨 注意事项

1. **保留核对功能**
   - PDF高亮功能要保留
   - OCR区域选择要保留
   - 完成核对功能要保留

2. **向后兼容**
   - 默认使用CommissionForm
   - 保持现有委托单功能不变

3. **数据结构**
   - CommissionForm使用现有commission_data结构
   - PaperForm使用paper_articles相关表

4. **API调用**
   - 委托单: filesApi.getCommissionData/updateCommissionData
   - 论文: papersApi.getPaperByFileId/updatePaper

## ✅ 预期效果

重构后：
- ✅ 支持委托单和论文两种类型
- ✅ 表单代码复用（CommissionForm/PaperForm）
- ✅ 代码量减少约700行
- ✅ 易于添加新类型
- ✅ 保留所有现有功能

---

*文档创建时间: 2025-11-08*

