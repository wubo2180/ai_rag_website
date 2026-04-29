# 论文表单组件使用指南

## 📦 组件信息

**组件路径**: `frontend/src/components/PaperForm/index.vue`

**组件名称**: `PaperForm`

**功能**: 用于论文数据的录入和编辑，支持层次化的四级数据结构（文献 → 材料/中间体 → 性能）

---

## 🎯 组件特性

### 1. **层次化数据结构**
- 文献基本信息（文献编号、名称、性能趋势）
- 材料/中间体信息（可动态添加/删除）
- 性能数据（每个材料可有多个性能数据）

### 2. **交互功能**
- ✅ 动态添加/删除材料
- ✅ 动态添加/删除性能数据
- ✅ 表单验证（必填字段、格式校验）
- ✅ 只读模式（用于查看）
- ✅ 双向数据绑定（v-model）

### 3. **美观UI**
- 卡片式布局
- 清晰的层级分隔
- 表格形式展示性能数据
- 响应式设计

---

## 📝 Props 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `modelValue` | Object | `{}` | 表单数据（v-model） |
| `readonly` | Boolean | `false` | 是否只读模式 |

---

## 🔧 Events 事件

| 事件名 | 参数 | 说明 |
|--------|------|------|
| `update:modelValue` | `formData` | 表单数据变化时触发 |
| `validate` | `isValid` | 表单验证结果 |

---

## 📊 数据格式

### 输入数据格式 (modelValue)

```javascript
{
  article_id: 'A1',
  article_name: '双组分缩合型有机硅电子灌封胶的制备及其导热阻燃性能研究',
  performance_trend: '1、添加γ－氨丙基三乙氧基硅烷缩短封灌胶表干时间...',
  hierarchical_data: [
    {
      material_id: 'A1M1',
      material_name: 'α，ω－二羟基聚二甲基硅氧烷，黏度4000MPa·s',
      cas_number: '',
      intermediate_id: 'A1I1',
      intermediate_name: 'A组分：107基础胶+α-氧化铝+氢氧化镁+二甲基硅油',
      intermediate_composition: 'A1I1：A1I2=10：1（质量比）',
      properties: [
        {
          property_id: 'A1P1',
          property_name: '粘度／黏度 MPa·S',
          property_value: '1900'
        },
        {
          property_id: 'A1P2',
          property_name: '热导率（Thermal Conductivity） W/(m·K)',
          property_value: '0.826'
        }
      ]
    }
  ]
}
```

---

## 🚀 使用示例

### 示例1：基本使用（编辑模式）

```vue
<template>
  <div class="page-container">
    <PaperForm
      v-model="paperData"
      @validate="handleValidate"
    />
    
    <div class="button-group">
      <el-button @click="handleReset">重置</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import PaperForm from '@/components/PaperForm/index.vue'
import { createPaper, updatePaper } from '@/api/papers'

const paperFormRef = ref(null)
const paperData = ref({
  article_id: '',
  article_name: '',
  performance_trend: '',
  hierarchical_data: []
})

const handleValidate = (isValid) => {
  console.log('表单验证结果:', isValid)
}

const handleSave = async () => {
  // 验证表单
  const isValid = await paperFormRef.value.validate()
  if (!isValid) {
    return
  }
  
  try {
    const response = await createPaper({
      file_id: 123, // 当前文件ID
      ...paperData.value
    })
    
    if (response.data.success) {
      ElMessage.success('保存成功')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  }
}

const handleReset = () => {
  paperFormRef.value.resetForm()
}
</script>
```

### 示例2：只读模式（查看）

```vue
<template>
  <div class="view-container">
    <PaperForm
      v-model="paperData"
      :readonly="true"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PaperForm from '@/components/PaperForm/index.vue'
import { getPaperByFileId } from '@/api/papers'

const paperData = ref({})

onMounted(async () => {
  // 加载论文数据
  const response = await getPaperByFileId(123)
  if (response.data.success) {
    paperData.value = response.data.data
  }
})
</script>
```

### 示例3：在识别页面中使用

```vue
<template>
  <div class="file-recognize-container">
    <!-- 左侧数据编辑区域 -->
    <div class="data-panel">
      <div class="panel-header">
        <h3>{{ documentTypeName }}数据</h3>
      </div>
      
      <!-- 根据文件类型显示不同表单 -->
      <component
        :is="currentFormComponent"
        ref="formRef"
        v-model="formData"
        :readonly="false"
      />
      
      <!-- 操作按钮 -->
      <div class="action-buttons">
        <el-button
          type="primary"
          :loading="isRecognizing"
          @click="startOcrRecognize"
        >
          <el-icon><MagicStick /></el-icon>
          OCR识别
        </el-button>
        
        <el-button
          type="success"
          :disabled="!hasOcrData"
          :loading="isSaving"
          @click="saveToDatabase"
        >
          <el-icon><Check /></el-icon>
          保存入库
        </el-button>
      </div>
    </div>
    
    <!-- 右侧PDF预览区域 -->
    <div class="pdf-panel">
      <!-- PDF预览组件 -->
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import PaperForm from '@/components/PaperForm/index.vue'
import CommissionForm from '@/components/CommissionForm/index.vue'
import { getFileById } from '@/api/files'
import { getPaperByFileId, createPaper } from '@/api/papers'

const route = useRoute()
const fileId = computed(() => route.params.id)

const formRef = ref(null)
const currentFile = ref(null)
const formData = ref({})
const isRecognizing = ref(false)
const isSaving = ref(false)
const hasOcrData = ref(false)

// 根据文件类型决定使用哪个表单组件
const currentFormComponent = computed(() => {
  if (!currentFile.value) return null
  
  const docType = currentFile.value.document_type_code
  switch (docType) {
    case 'paper':
      return PaperForm
    case 'commission':
      return CommissionForm
    default:
      return null
  }
})

const documentTypeName = computed(() => {
  const docType = currentFile.value?.document_type_code
  const typeMap = {
    'paper': '论文',
    'commission': '委托单'
  }
  return typeMap[docType] || '文档'
})

// 加载文件信息
const loadFileInfo = async () => {
  try {
    const response = await getFileById(fileId.value)
    if (response.data.success) {
      currentFile.value = response.data.data
      
      // 如果有已保存的数据，加载它
      if (currentFile.value.document_type_code === 'paper') {
        await loadPaperData()
      }
    }
  } catch (error) {
    ElMessage.error('加载文件信息失败')
  }
}

// 加载论文数据
const loadPaperData = async () => {
  try {
    const response = await getPaperByFileId(fileId.value)
    if (response.data.success) {
      formData.value = response.data.data
      hasOcrData.value = true
    }
  } catch (error) {
    // 没有数据是正常的
    console.log('暂无论文数据')
  }
}

// OCR识别
const startOcrRecognize = async () => {
  isRecognizing.value = true
  try {
    // TODO: 调用OCR API
    ElMessage.success('OCR识别完成')
    hasOcrData.value = true
  } catch (error) {
    ElMessage.error('OCR识别失败')
  } finally {
    isRecognizing.value = false
  }
}

// 保存到数据库
const saveToDatabase = async () => {
  // 验证表单
  const isValid = await formRef.value.validate()
  if (!isValid) {
    return
  }
  
  isSaving.value = true
  try {
    const response = await createPaper({
      file_id: fileId.value,
      ...formData.value
    })
    
    if (response.data.success) {
      ElMessage.success('保存成功')
    }
  } catch (error) {
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  loadFileInfo()
})
</script>
```

---

## 🎨 组件方法 (defineExpose)

可以通过 `ref` 调用以下方法：

### `validate()`
验证表单

```javascript
const isValid = await formRef.value.validate()
```

### `resetForm()`
重置表单

```javascript
formRef.value.resetForm()
```

### `getFormData()`
获取表单数据

```javascript
const data = formRef.value.getFormData()
```

---

## 🔍 验证规则

### 文献编号格式
- 格式：大写字母 + 数字
- 示例：`A1`, `B12`, `C999`
- 正则：`/^[A-Z]\d+$/`

### 材料编号格式
- 格式：文献编号 + `M` + 数字
- 示例：`A1M1`, `A1M2`
- 正则：`/^[A-Z]\d+M\d+$/`

### 中间体编号格式
- 格式：文献编号 + `I` + 数字
- 示例：`A1I1`, `A1I2`
- 正则：`/^[A-Z]\d+I\d+$/`

### 性能编号格式
- 格式：文献编号 + `P` + 数字
- 示例：`A1P1`, `A1P2`
- 正则：`/^[A-Z]\d+P\d+$/`

---

## 🎨 样式定制

组件使用 SCSS 编写样式，可以通过以下方式自定义：

```vue
<style lang="scss">
// 修改卡片背景色
.paper-form .form-section {
  background: #f0f2f5 !important;
}

// 修改标题颜色
.paper-form .section-header h3 {
  color: #1890ff !important;
}

// 修改表格样式
.paper-form .properties-table {
  // 自定义样式
}
</style>
```

---

## 📋 完整API集成示例

```javascript
// api/papers.js
import request from '@/utils/request'

export function createPaper(data) {
  return request({
    url: '/papers',
    method: 'post',
    data
  })
}

export function getPaperByFileId(fileId) {
  return request({
    url: `/papers/by-file/${fileId}`,
    method: 'get',
    params: { include_details: true }
  })
}

export function updatePaper(articleId, data) {
  return request({
    url: `/papers/${articleId}`,
    method: 'put',
    data
  })
}
```

---

## 🐛 常见问题

### Q1: 为什么添加材料后数据没有保存？

A: 确保在保存前调用 `validate()` 方法，并且至少添加一个材料和必填字段。

### Q2: 如何禁用某些字段？

A: 使用 `:readonly="true"` 属性，或者在特定字段上使用 `:disabled="true"`。

### Q3: 如何自定义验证规则？

A: 修改组件内的 `rules` 对象，添加自定义验证规则。

### Q4: 性能数据表格如何排序？

A: 表格已包含序号列，数据按添加顺序显示。可以手动调整 `properties` 数组顺序。

---

## 📦 依赖

- Vue 3.3+
- Element Plus 2.3+
- Composition API

---

**创建日期**: 2025-11-06  
**组件版本**: v1.0  
**状态**: ✅ 开发完成，待测试


