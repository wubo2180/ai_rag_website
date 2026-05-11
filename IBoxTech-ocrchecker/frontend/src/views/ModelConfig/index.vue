<template>
  <div class="model-config-page">
    <el-card class="header-card">
      <div class="page-header">
        <div class="header-left">
          <h2>模型配置管理</h2>
          <p class="description">管理OCR识别模型配置，支持不同文件类型使用不同模型</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 模型列表 -->
    <el-card class="content-card">
      <div class="filter-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索模型名称或描述"
          clearable
          style="width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="statusFilter"
          placeholder="模型状态"
          clearable
          style="width: 150px"
        >
          <el-option label="全部" value="" />
          <el-option label="已启用" value="true" />
          <el-option label="已禁用" value="false" />
        </el-select>

        <el-select
          v-model="typeFilter"
          placeholder="文件类型"
          clearable
          style="width: 150px"
        >
          <el-option label="全部" value="" />
          <el-option label="委托单" value="委托单" />
          <el-option label="论文" value="论文" />
          <el-option label="通用" value="null" />
        </el-select>
      </div>

      <el-table
        v-loading="loading"
        :data="filteredModels"
        style="width: 100%"
      >
        <el-table-column prop="name" label="模型名称" min-width="150">
          <template #default="{ row }">
            <div class="model-name-cell">
              <span>{{ row.name }}</span>
              <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="file_type" label="文件类型" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.file_type" size="small">{{ row.file_type }}</el-tag>
            <el-tag v-else type="info" size="small">通用</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column prop="api_url" label="API地址" min-width="200" show-overflow-tooltip />

        <el-table-column prop="timeout" label="超时" width="80" align="center">
          <template #default="{ row }">
            {{ row.timeout }}s
          </template>
        </el-table-column>

        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="editModel(row)"
            >
              编辑
            </el-button>
            <el-button
              v-if="!row.is_default"
              type="success"
              size="small"
              link
              @click="setAsDefault(row)"
            >
              设为默认
            </el-button>
            <el-button
              v-if="!row.is_default"
              type="danger"
              size="small"
              link
              @click="deleteModel(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '添加模型' : '编辑模型'"
      width="600px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="模型名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入模型名称" />
        </el-form-item>

        <el-form-item label="API地址" prop="api_url">
          <el-input v-model="form.api_url" placeholder="http://localhost:6001/analyze" />
        </el-form-item>

        <el-form-item label="文件类型" prop="file_type">
          <el-select v-model="form.file_type" placeholder="选择文件业务类型" clearable style="width: 100%">
            <el-option label="委托单" value="委托单" />
            <el-option label="论文" value="论文" />
            <el-option label="通用（适用所有类型）" :value="null" />
          </el-select>
          <div class="form-tip">留空或选择"通用"表示适用于所有文件业务类型</div>
        </el-form-item>

        <el-form-item label="模型描述">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模型描述"
          />
        </el-form-item>

        <el-form-item label="超时时间" prop="timeout">
          <el-input-number
            v-model="form.timeout"
            :min="30"
            :max="600"
            :step="30"
            style="width: 100%"
          />
          <div class="form-tip">单位：秒，建议120-180秒</div>
        </el-form-item>

        <el-form-item label="设为默认">
          <el-switch v-model="form.is_default" />
          <div class="form-tip">默认模型会在没有指定模型时自动使用</div>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitForm">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { modelConfigsApi } from '@/api/model-configs'

const loading = ref(false)
const models = ref([])
const searchKeyword = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

const dialogVisible = ref(false)
const dialogMode = ref('create')
const submitting = ref(false)
const formRef = ref()

const form = reactive({
  id: null,
  name: '',
  api_url: '',
  file_type: null,
  description: '',
  timeout: 120,
  is_default: false,
  is_active: true
})

const rules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  api_url: [
    { required: true, message: '请输入API地址', trigger: 'blur' },
    { type: 'url', message: '请输入正确的URL格式', trigger: 'blur' }
  ],
  timeout: [
    { required: true, message: '请设置超时时间', trigger: 'blur' }
  ]
}

// 过滤后的模型列表
const filteredModels = computed(() => {
  let result = models.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(m =>
      m.name.toLowerCase().includes(keyword) ||
      (m.description && m.description.toLowerCase().includes(keyword))
    )
  }

  // 状态过滤
  if (statusFilter.value !== '') {
    const isActive = statusFilter.value === 'true'
    result = result.filter(m => m.is_active === isActive)
  }

  // 类型过滤
  if (typeFilter.value !== '') {
    if (typeFilter.value === 'null') {
      result = result.filter(m => m.file_type === null)
    } else {
      result = result.filter(m => m.file_type === typeFilter.value)
    }
  }

  return result
})

// 获取模型列表
const fetchModels = async () => {
  try {
    loading.value = true
    console.log('🔍 开始获取模型配置列表...')
    const response = await modelConfigsApi.getAll()
    console.log('📦 API响应:', response)
    if (response.data && response.data.success) {
      models.value = response.data.data
      console.log('✅ 模型列表加载成功:', models.value)
    } else {
      console.warn('⚠️ API返回success=false:', response)
      ElMessage.warning(response.data?.message || '获取模型列表失败')
    }
  } catch (error) {
    console.error('❌ 获取模型列表失败:', error)
    ElMessage.error('获取模型列表失败')
  } finally {
    loading.value = false
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 编辑模型
const editModel = (model) => {
  dialogMode.value = 'edit'
  Object.assign(form, {
    id: model.id,
    name: model.name,
    api_url: model.api_url,
    file_type: model.file_type,
    description: model.description,
    timeout: model.timeout,
    is_default: model.is_default,
    is_active: model.is_active
  })
  dialogVisible.value = true
}

// 设为默认
const setAsDefault = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定将"${model.name}"设为默认模型吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await modelConfigsApi.update(model.id, { is_default: true })
    if (response.data && response.data.success) {
      ElMessage.success('设置成功')
      await fetchModels()
    } else {
      ElMessage.error(response.data?.message || '设置失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('设置默认模型失败:', error)
      ElMessage.error(error.message || '设置失败')
    }
  }
}

// 删除模型
const deleteModel = async (model) => {
  try {
    await ElMessageBox.confirm(
      `确定删除模型"${model.name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await modelConfigsApi.delete(model.id)
    if (response.data && response.data.success) {
      ElMessage.success('删除成功')
      await fetchModels()
    } else {
      ElMessage.error(response.data?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除模型失败:', error)
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitting.value = true

    const data = {
      name: form.name,
      api_url: form.api_url,
      file_type: form.file_type,
      description: form.description,
      timeout: form.timeout,
      is_default: form.is_default,
      is_active: form.is_active
    }

    let response
    if (dialogMode.value === 'create') {
      response = await modelConfigsApi.create(data)
    } else {
      response = await modelConfigsApi.update(form.id, data)
    }

    if (response.data && response.data.success) {
      ElMessage.success(dialogMode.value === 'create' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      await fetchModels()
    } else {
      ElMessage.error(response.data?.message || '操作失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('提交失败:', error)
      ElMessage.error(error.message || '操作失败')
    }
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: '',
    api_url: '',
    file_type: null,
    description: '',
    timeout: 120,
    is_default: false,
    is_active: true
  })
  formRef.value?.clearValidate()
}

onMounted(() => {
  fetchModels()
})
</script>

<style lang="scss" scoped>
.model-config-page {
  padding: $spacing-lg;

  .header-card {
    margin-bottom: $spacing-lg;

    .page-header {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-left {
        h2 {
          margin: 0 0 $spacing-sm 0;
          font-size: 24px;
          font-weight: 500;
        }

        .description {
          margin: 0;
          color: $text-color-secondary;
          font-size: 14px;
        }
      }
    }
  }

  .content-card {
    .filter-bar {
      display: flex;
      gap: $spacing-md;
      margin-bottom: $spacing-lg;
    }

    .model-name-cell {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
    }
  }

  .form-tip {
    font-size: 12px;
    color: $text-color-secondary;
    margin-top: 4px;
  }
}
</style>

