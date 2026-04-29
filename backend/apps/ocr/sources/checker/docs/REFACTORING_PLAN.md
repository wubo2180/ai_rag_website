# OCR系统通用化重构方案

## 📋 项目背景

当前系统针对"委托单"类型文件专门设计，需要重构成通用的多文件类型处理系统，以支持"论文"等新文件类型。

## 🎯 重构目标

1. **通用化架构**：支持任意文件类型的动态配置
2. **配置驱动**：通过配置文件定义文件类型的处理方式
3. **向后兼容**：保持现有委托单功能正常工作
4. **易扩展**：添加新文件类型时无需修改核心代码

## 🏗️ 架构设计

### 1. 文件类型配置系统

#### 1.1 FileTypeConfig 模型
```
file_type_configs 表:
- type_code: 类型代码（如 'commission', 'paper'）
- type_name: 类型名称（如 '委托单', '论文'）
- ocr_model_api: OCR模型API地址
- storage_table_basic: 基本信息存储表名
- form_config: 表单配置（JSON）
- field_mapping: 字段映射配置（JSON）
```

#### 1.2 预置配置示例

**委托单类型配置：**
```json
{
  "type_code": "commission",
  "type_name": "委托单",
  "ocr_model_api": "/api/ocr/commission",
  "storage_table_basic": "commission_basic",
  "storage_table_items": "test_items",
  "storage_table_details": "special_tests",
  "form_config": {
    "sections": [
      {
        "title": "基本信息",
        "fields": [
          {"name": "commission_number", "label": "委托编号", "type": "text", "required": true},
          {"name": "commissioner", "label": "委托人", "type": "text"}
        ]
      }
    ]
  }
}
```

**论文类型配置：**
```json
{
  "type_code": "paper",
  "type_name": "论文",
  "ocr_model_api": "/api/ocr/paper",
  "storage_table_basic": "paper_basic",
  "form_config": {
    "sections": [
      {
        "title": "论文信息",
        "fields": [
          {"name": "paper_title", "label": "论文标题", "type": "text", "required": true},
          {"name": "author", "label": "作者", "type": "text"}
        ]
      }
    ]
  }
}
```

### 2. 后端架构重构

#### 2.1 通用数据模型

**DocumentBasic 模型** - 通用文档存储
```python
class DocumentBasic(db.Model):
    id: 主键
    file_id: 文件ID
    file_type_code: 文件类型代码（关联 FileTypeConfig）
    document_number: 文档唯一编号
    basic_data: 基本数据（JSON格式）
    items_data: 子项目数据（JSON格式）
    details_data: 详细数据（JSON格式）
```

**优点：**
- 单表存储所有类型文档的核心数据
- JSON字段灵活存储不同结构的数据
- 通过 file_type_code 区分文件类型

**保留现有表：**
- commission_basic、test_items、special_tests 等表继续使用
- 作为 DocumentBasic 的补充，存储结构化数据

#### 2.2 统一API接口

**统一识别接口：**
```
POST /api/documents/recognize
Body: {
  "file_id": 123,
  "file_type_code": "commission" // 或 "paper"
}
```

**统一获取接口：**
```
GET /api/documents/{document_id}?type=commission
```

**统一保存接口：**
```
PUT /api/documents/{document_id}
Body: {
  "basic_data": {...},
  "items_data": [...],
  "details_data": [...]
}
```

#### 2.3 服务层重构

**DocumentService** - 通用文档服务
```python
class DocumentService:
    def process_document(file_id, file_type_code):
        # 1. 获取文件类型配置
        config = FileTypeConfig.query.filter_by(type_code=file_type_code).first()
        
        # 2. 调用对应的OCR服务
        ocr_result = self._call_ocr_service(config.ocr_model_api, file_id)
        
        # 3. 映射数据
        mapped_data = self._map_data(ocr_result, config.field_mapping)
        
        # 4. 保存到对应的表
        document = self._save_to_storage(mapped_data, config)
        
        return document
```

**SpecificDocumentService** - 特定文档服务（继承）
```python
class CommissionDocumentService(DocumentService):
    def _save_to_storage(self, mapped_data, config):
        # 委托单特有的保存逻辑
        # 保存到 commission_basic, test_items, special_tests
        pass

class PaperDocumentService(DocumentService):
    def _save_to_storage(self, mapped_data, config):
        # 论文特有的保存逻辑
        # 保存到 paper_basic 等表
        pass
```

### 3. 前端架构重构

#### 3.1 动态表单组件

**FormRenderer.vue** - 表单渲染器
```vue
<template>
  <div class="form-renderer">
    <div v-for="section in formConfig.sections" :key="section.title">
      <h4>{{ section.title }}</h4>
      <el-form>
        <el-form-item 
          v-for="field in section.fields" 
          :key="field.name"
          :label="field.label"
          :required="field.required"
        >
          <el-input 
            v-if="field.type === 'text'" 
            v-model="formData[field.name]" 
          />
          <el-select 
            v-else-if="field.type === 'select'"
            v-model="formData[field.name]"
          >
            <el-option 
              v-for="option in field.options"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>
```

#### 3.2 特定表单组件

**CommissionForm.vue** - 委托单表单（现有）
```vue
<template>
  <div class="commission-form">
    <!-- 现有委托单表单内容 -->
  </div>
</template>
```

**PaperForm.vue** - 论文表单（新增）
```vue
<template>
  <div class="paper-form">
    <el-form :model="paperData">
      <el-form-item label="论文标题">
        <el-input v-model="paperData.title" />
      </el-form-item>
      <el-form-item label="作者">
        <el-input v-model="paperData.author" />
      </el-form-item>
    </el-form>
  </div>
</template>
```

#### 3.3 识别页面重构

**FileRecognize/index.vue** - 修改后
```vue
<template>
  <div class="file-review-container">
    <!-- 顶部工具栏 -->
    <div class="review-toolbar">
      <!-- 文件类型选择器 -->
      <el-select v-model="currentFileType" @change="onFileTypeChange">
        <el-option label="委托单" value="commission" />
        <el-option label="论文" value="paper" />
      </el-select>
      
      <el-button @click="startOcrRecognize">
        OCR识别
      </el-button>
    </div>

    <!-- 主内容区域 -->
    <div class="review-content">
      <!-- 左侧数据编辑区域 - 动态加载表单 -->
      <div class="data-panel">
        <!-- 方案1: 使用动态表单渲染器 -->
        <FormRenderer 
          v-if="useFormRenderer"
          :form-config="fileTypeConfig.form_config"
          :form-data="documentData"
          @update="updateDocumentData"
        />
        
        <!-- 方案2: 使用特定表单组件 -->
        <component 
          v-else
          :is="currentFormComponent"
          :document-data="documentData"
          @update="updateDocumentData"
        />
      </div>
      
      <!-- 右侧PDF预览 -->
      <div class="pdf-panel">
        <PdfViewer :file-id="fileId" />
      </div>
    </div>
  </div>
</template>

<script>
import CommissionForm from './components/CommissionForm.vue'
import PaperForm from './components/PaperForm.vue'
import FormRenderer from '@/components/FormRenderer.vue'

export default {
  components: {
    CommissionForm,
    PaperForm,
    FormRenderer
  },
  data() {
    return {
      currentFileType: 'commission',
      fileTypeConfig: null,
      documentData: {}
    }
  },
  computed: {
    currentFormComponent() {
      const componentMap = {
        'commission': 'CommissionForm',
        'paper': 'PaperForm'
      }
      return componentMap[this.currentFileType]
    }
  },
  async mounted() {
    // 加载文件类型配置
    await this.loadFileTypeConfig()
  },
  methods: {
    async loadFileTypeConfig() {
      const res = await api.get(`/file-type-configs/${this.currentFileType}`)
      this.fileTypeConfig = res.data
    },
    
    async startOcrRecognize() {
      const res = await api.post('/documents/recognize', {
        file_id: this.fileId,
        file_type_code: this.currentFileType
      })
      this.documentData = res.data
    }
  }
}
</script>
```

## 🔄 迁移策略

### 阶段1：建立新架构（不影响现有功能）
1. 创建 `FileTypeConfig` 和 `DocumentBasic` 表
2. 创建委托单类型配置记录
3. 创建通用API接口（与现有接口并存）

### 阶段2：前端适配
1. 创建 `FormRenderer` 动态表单组件
2. 将现有委托单表单提取为 `CommissionForm` 组件
3. 修改 `FileRecognize` 页面支持组件切换

### 阶段3：后端服务重构
1. 创建 `DocumentService` 通用服务
2. 创建 `CommissionDocumentService` 继承通用服务
3. 统一API调用新服务

### 阶段4：添加论文类型
1. 创建论文类型配置记录
2. 创建 `PaperForm` 组件
3. 创建 `PaperDocumentService`
4. 测试论文文件处理流程

### 阶段5：数据迁移（可选）
1. 将现有委托单数据复制到 `DocumentBasic` 表
2. 逐步废弃旧API，统一使用新API

## 💡 实施建议

### 方案A：渐进式重构（推荐）
- 优点：风险低，现有功能不受影响
- 缺点：代码会暂时存在新旧两套系统

### 方案B：一次性重构
- 优点：架构统一，代码清晰
- 缺点：风险高，需要大量测试

## 📝 下一步行动

请确认以下问题：

1. **重构方式**：选择方案A（渐进式）还是方案B（一次性）？
2. **表单方式**：使用动态表单渲染器还是特定表单组件？
3. **数据存储**：使用通用JSON存储还是保留专用表结构？
4. **迁移范围**：是否需要迁移现有委托单数据到新架构？

确认后，我将开始实施重构。建议先在 `paper-checker` 分支实现，测试通过后再合并到主分支。


