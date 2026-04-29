<template>
  <div class="file-type-config-page">
    <el-card class="header-card">
      <div class="page-header">
        <div class="header-left">
          <h2>文件类型配置管理</h2>
          <p class="description">管理不同文件类型的OCR识别配置、存储表映射和适配器关联</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog">
            <el-icon><Plus /></el-icon>
            添加文件类型
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 配置列表 -->
    <el-card class="content-card">
      <div class="filter-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索类型代码或名称"
          clearable
          style="width: 300px"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="statusFilter"
          placeholder="状态"
          clearable
          style="width: 150px"
        >
          <el-option label="全部" value="" />
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>

        <el-button @click="fetchConfigs" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="filteredConfigs"
        style="width: 100%"
      >
        <el-table-column prop="type_code" label="类型代码" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.type_code }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="type_name" label="类型名称" width="120" />

        <el-table-column prop="type_description" label="描述" min-width="150" show-overflow-tooltip />

        <el-table-column label="OCR模型" min-width="150">
          <template #default="{ row }">
            <div v-if="row.model_config">
              <div class="model-info">
                {{ row.model_config.name }}
              </div>
              <div class="model-url">{{ row.model_config.api_url }}</div>
            </div>
            <el-tag v-else type="warning" size="small">未配置</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="适配器" width="150">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.adapter_class }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="存储表" min-width="180">
          <template #default="{ row }">
            <div class="storage-tables">
              <el-tag
                v-for="(tableName, index) in getStorageTableNames(row.storage_tables)"
                :key="index"
                size="small"
                class="table-tag"
              >
                {{ tableName }}
              </el-tag>
              <span v-if="!row.storage_tables || row.storage_tables.length === 0" class="empty-text">
                未配置
              </span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="sort_order" label="排序" width="80" align="center" />

        <el-table-column prop="is_active" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              @change="toggleActive(row)"
            />
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              link
              @click="viewConfig(row)"
            >
              查看
            </el-button>
            <el-button
              type="primary"
              size="small"
              link
              @click="editConfig(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              size="small"
              link
              @click="deleteConfig(row)"
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
      :title="dialogMode === 'create' ? '添加文件类型配置' : dialogMode === 'edit' ? '编辑文件类型配置' : '查看文件类型配置'"
      width="800px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        :disabled="dialogMode === 'view'"
      >
        <el-tabs v-model="activeTab">
          <!-- 基本信息 -->
          <el-tab-pane label="基本信息" name="basic">
            <el-form-item label="类型代码" prop="type_code">
              <el-input
                v-model="form.type_code"
                placeholder="如：commission、paper"
                :disabled="dialogMode === 'edit'"
              />
              <div class="form-tip">唯一标识符，创建后不可修改</div>
            </el-form-item>

            <el-form-item label="类型名称" prop="type_name">
              <el-input v-model="form.type_name" placeholder="如：委托单、论文" />
            </el-form-item>

            <el-form-item label="类型描述">
              <el-input
                v-model="form.type_description"
                type="textarea"
                :rows="3"
                placeholder="详细描述该文件类型的用途和特点"
              />
            </el-form-item>

            <el-form-item label="排序序号" prop="sort_order">
              <el-input-number
                v-model="form.sort_order"
                :min="0"
                :max="999"
                style="width: 100%"
              />
              <div class="form-tip">数字越小越靠前</div>
            </el-form-item>

            <el-form-item label="启用状态">
              <el-switch v-model="form.is_active" />
            </el-form-item>
          </el-tab-pane>

          <!-- OCR配置 -->
          <el-tab-pane label="OCR配置" name="ocr">
            <el-form-item label="关联模型" prop="model_config_id">
              <el-select
                v-model="form.model_config_id"
                placeholder="选择OCR模型"
                style="width: 100%"
                clearable
              >
                <el-option
                  v-for="model in modelConfigs"
                  :key="model.id"
                  :label="`${model.name} (${model.file_type || '通用'})`"
                  :value="model.id"
                >
                  <div class="model-option">
                    <span>{{ model.name }}</span>
                    <span class="model-url">{{ model.api_url }}</span>
                  </div>
                </el-option>
              </el-select>
              <div class="form-tip">选择该文件类型使用的OCR模型</div>
            </el-form-item>

            <el-form-item label="特定配置">
              <el-input
                v-model="ocrConfigStr"
                type="textarea"
                :rows="6"
                placeholder='可选，JSON格式，用于覆盖模型默认配置。例如：
{
  "language": "ch",
  "confidence_threshold": 0.85
}'
              />
              <div class="form-tip">JSON格式，覆盖模型的默认配置参数</div>
            </el-form-item>
          </el-tab-pane>

          <!-- 适配器配置 -->
          <el-tab-pane label="适配器配置" name="adapter">
            <el-form-item label="适配器类名" prop="adapter_class">
              <el-input
                v-model="form.adapter_class"
                placeholder="如：CommissionAdapter、PaperAdapter"
              />
              <div class="form-tip">必须是已存在的适配器类名</div>
            </el-form-item>

            <el-form-item label="适配器模块">
              <el-input
                v-model="form.adapter_module"
                placeholder="默认：adapters"
              />
              <div class="form-tip">适配器所在的模块路径</div>
            </el-form-item>
          </el-tab-pane>

          <!-- 存储表配置 -->
          <el-tab-pane label="存储表配置" name="storage">
            <div class="storage-tables-config">
              <div class="config-header">
                <span>选择该文件类型关联的数据表</span>
              </div>

              <el-form-item label="关联数据表" prop="storage_tables">
                <el-checkbox-group
                  v-model="form.storage_tables"
                  :disabled="dialogMode === 'view'"
                >
                  <div class="table-checkbox-grid">
                    <el-checkbox
                      v-for="table in databaseTables"
                      :key="table.name"
                      :label="table.name"
                      class="table-checkbox-item"
                    >
                      <div class="table-checkbox-content">
                        <span class="table-name">{{ table.name }}</span>
                        <span class="table-label">{{ table.label }}</span>
                      </div>
                    </el-checkbox>
                  </div>
                </el-checkbox-group>
                <div class="form-tip">
                  选择存储该文件类型数据的数据库表，支持多选
                </div>
              </el-form-item>

              <el-form-item label="已选择的表">
                <div class="selected-tables">
                  <el-tag
                    v-for="tableName in form.storage_tables"
                    :key="tableName"
                    class="table-tag"
                    :closable="dialogMode !== 'view'"
                    @close="removeTable(tableName)"
                  >
                    {{ tableName }}
                  </el-tag>
                  <span v-if="form.storage_tables.length === 0" class="empty-tip">
                    尚未选择任何表
                  </span>
                </div>
              </el-form-item>
            </div>
          </el-tab-pane>

          <!-- 表单配置 -->
          <el-tab-pane label="表单配置" name="form">
            <el-form-item label="表单组件">
              <el-input
                v-model="form.form_component"
                placeholder="如：CommissionForm、PaperForm"
              />
              <div class="form-tip">前端自定义表单组件路径（硬编码方式）</div>
            </el-form-item>

            <el-form-item label="表单配置">
              <div class="config-header">
                <el-button
                  type="primary"
                  size="small"
                  @click="previewForm"
                  :disabled="!formConfigStr.trim()"
                >
                  <el-icon><View /></el-icon>
                  预览表单
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  @click="showFormConfigExample"
                >
                  <el-icon><Document /></el-icon>
                  查看示例
                </el-button>
              </div>
              <el-input
                v-model="formConfigStr"
                type="textarea"
                :rows="8"
                placeholder="JSON格式的动态表单配置（试验功能）"
              />
              <div class="form-tip">
                <el-icon><InfoFilled /></el-icon>
                用于动态生成前端表单的JSON配置。点击"预览表单"测试配置效果。
              </div>
            </el-form-item>

            <el-form-item label="验证规则">
              <el-input
                v-model="validationRulesStr"
                type="textarea"
                :rows="6"
                placeholder="JSON格式的数据验证规则"
              />
              <div class="form-tip">数据验证规则配置</div>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">
          {{ dialogMode === 'view' ? '关闭' : '取消' }}
        </el-button>
        <el-button
          v-if="dialogMode !== 'view'"
          type="primary"
          :loading="submitting"
          @click="submitForm"
        >
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 表单预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="表单配置预览"
      width="900px"
      :close-on-click-modal="false"
    >
      <div class="preview-container">
        <el-alert
          title="动态表单预览"
          type="info"
          :closable="false"
          style="margin-bottom: 20px"
        >
          <template #default>
            这是根据 form_config JSON 配置动态生成的表单预览。
            您可以测试表单的布局、字段类型和验证规则。
          </template>
        </el-alert>

        <!-- 动态表单组件 -->
        <DynamicForm
          v-if="previewFormConfig"
          ref="previewFormRef"
          :config="previewFormConfig"
          v-model="previewFormData"
        />

        <el-empty
          v-else
          description="表单配置解析失败"
          :image-size="100"
        />
      </div>

      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="testFormValidation">
          测试表单验证
        </el-button>
      </template>
    </el-dialog>

    <!-- 表单配置示例对话框 -->
    <el-dialog
      v-model="exampleDialogVisible"
      title="表单配置示例"
      width="800px"
    >
      <el-tabs v-model="exampleTab">
        <el-tab-pane label="基础示例" name="basic">
          <div class="example-description">
            <p>基础表单示例，包含常用字段类型：</p>
            <ul>
              <li>文本输入（text）</li>
              <li>多行文本（textarea）</li>
              <li>下拉选择（select）</li>
              <li>日期选择（date）</li>
              <li>数字输入（number）</li>
            </ul>
          </div>
          <pre class="example-code">{{ basicExample }}</pre>
          <el-button type="primary" size="small" @click="useExample('basic')">
            使用此示例
          </el-button>
        </el-tab-pane>

        <el-tab-pane label="复杂示例" name="advanced">
          <div class="example-description">
            <p>包含更多字段类型和验证规则：</p>
            <ul>
              <li>开关（switch）</li>
              <li>单选框（radio）</li>
              <li>复选框（checkbox）</li>
              <li>滑块（slider）</li>
              <li>评分（rate）</li>
              <li>字段验证（pattern、minLength等）</li>
            </ul>
          </div>
          <pre class="example-code">{{ advancedExample }}</pre>
          <el-button type="primary" size="small" @click="useExample('advanced')">
            使用此示例
          </el-button>
        </el-tab-pane>

        <el-tab-pane label="字段说明" name="docs">
          <div class="field-docs">
            <h4>字段配置说明</h4>
            <el-table :data="fieldDocumentation" border>
              <el-table-column prop="property" label="属性" width="150" />
              <el-table-column prop="type" label="类型" width="100" />
              <el-table-column prop="description" label="说明" />
              <el-table-column prop="example" label="示例" width="150" />
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>

      <template #footer>
        <el-button @click="exampleDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Delete, View, Document, InfoFilled } from '@element-plus/icons-vue'
import { fileTypeConfigsApi } from '@/api/file-type-configs'
import DynamicForm from '@/components/DynamicForm/index.vue'

const loading = ref(false)
const configs = ref([])
const modelConfigs = ref([])
const databaseTables = ref([])  // 新增：数据库表列表
const searchKeyword = ref('')
const statusFilter = ref('')

const dialogVisible = ref(false)
const dialogMode = ref('create') // create | edit | view
const submitting = ref(false)
const formRef = ref()
const activeTab = ref('basic')

// JSON字符串字段
const ocrConfigStr = ref('')
const formConfigStr = ref('')
const validationRulesStr = ref('')

const form = reactive({
  id: null,
  type_code: '',
  type_name: '',
  type_description: '',
  model_config_id: null,
  ocr_config: null,
  storage_tables: [],
  adapter_class: '',
  adapter_module: 'adapters',
  form_config: null,
  form_component: '',
  validation_rules: null,
  is_active: true,
  sort_order: 0
})

const rules = {
  type_code: [
    { required: true, message: '请输入类型代码', trigger: 'blur' },
    { pattern: /^[a-z_]+$/, message: '只能包含小写字母和下划线', trigger: 'blur' }
  ],
  type_name: [
    { required: true, message: '请输入类型名称', trigger: 'blur' }
  ],
  adapter_class: [
    { required: true, message: '请输入适配器类名', trigger: 'blur' }
  ],
  sort_order: [
    { required: true, message: '请设置排序序号', trigger: 'blur' }
  ]
}

// 过滤后的配置列表
const filteredConfigs = computed(() => {
  let result = configs.value

  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(c =>
      c.type_code.toLowerCase().includes(keyword) ||
      c.type_name.toLowerCase().includes(keyword) ||
      (c.type_description && c.type_description.toLowerCase().includes(keyword))
    )
  }

  // 状态过滤
  if (statusFilter.value !== '') {
    result = result.filter(c => c.is_active === statusFilter.value)
  }

  return result
})

// 获取存储表名列表（兼容新旧格式）
const getStorageTableNames = (storageTables) => {
  if (!storageTables || !Array.isArray(storageTables)) {
    return []
  }
  
  // 新格式：字符串数组
  if (storageTables.length > 0 && typeof storageTables[0] === 'string') {
    return storageTables
  }
  
  // 旧格式：对象数组
  if (storageTables.length > 0 && typeof storageTables[0] === 'object') {
    return storageTables.map(t => t.table).filter(Boolean)
  }
  
  return []
}

// 获取配置列表
const fetchConfigs = async () => {
  try {
    loading.value = true
    const response = await fileTypeConfigsApi.getAll()
    if (response.data && response.data.success) {
      configs.value = response.data.data
      console.log('✅ 文件类型配置列表加载成功:', configs.value)
    } else {
      ElMessage.warning(response.data?.message || '获取配置列表失败')
    }
  } catch (error) {
    console.error('❌ 获取配置列表失败:', error)
    ElMessage.error('获取配置列表失败')
  } finally {
    loading.value = false
  }
}

// 获取模型配置列表
const fetchModelConfigs = async () => {
  try {
    const response = await fileTypeConfigsApi.getModelConfigs()
    if (response.data && response.data.success) {
      modelConfigs.value = response.data.data
    }
  } catch (error) {
    console.error('获取模型配置列表失败:', error)
  }
}

// 获取数据库表列表
const fetchDatabaseTables = async () => {
  try {
    const response = await fileTypeConfigsApi.getDatabaseTables()
    if (response.data && response.data.success) {
      databaseTables.value = response.data.data
      console.log('✅ 数据库表列表加载成功:', databaseTables.value)
    }
  } catch (error) {
    console.error('获取数据库表列表失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogMode.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 查看配置
const viewConfig = (config) => {
  dialogMode.value = 'view'
  loadFormData(config)
  dialogVisible.value = true
}

// 编辑配置
const editConfig = (config) => {
  dialogMode.value = 'edit'
  loadFormData(config)
  dialogVisible.value = true
}

// 加载表单数据
const loadFormData = (config) => {
  Object.assign(form, {
    id: config.id,
    type_code: config.type_code,
    type_name: config.type_name,
    type_description: config.type_description,
    model_config_id: config.model_config_id,
    ocr_config: config.ocr_config,
    // 新格式：storage_tables 是字符串数组
    storage_tables: Array.isArray(config.storage_tables) ? [...config.storage_tables] : [],
    adapter_class: config.adapter_class,
    adapter_module: config.adapter_module || 'adapters',
    form_config: config.form_config,
    form_component: config.form_component,
    validation_rules: config.validation_rules,
    is_active: config.is_active,
    sort_order: config.sort_order
  })

  // JSON字符串化
  ocrConfigStr.value = config.ocr_config ? JSON.stringify(config.ocr_config, null, 2) : ''
  formConfigStr.value = config.form_config ? JSON.stringify(config.form_config, null, 2) : ''
  validationRulesStr.value = config.validation_rules ? JSON.stringify(config.validation_rules, null, 2) : ''

  activeTab.value = 'basic'
}

// 切换启用状态
const toggleActive = async (config) => {
  try {
    const response = await fileTypeConfigsApi.toggleActive(config.id, config.is_active)
    if (response.data && response.data.success) {
      ElMessage.success(config.is_active ? '已启用' : '已禁用')
    } else {
      // 恢复状态
      config.is_active = !config.is_active
      ElMessage.error(response.data?.message || '操作失败')
    }
  } catch (error) {
    // 恢复状态
    config.is_active = !config.is_active
    console.error('切换状态失败:', error)
    ElMessage.error('操作失败')
  }
}

// 删除配置
const deleteConfig = async (config) => {
  try {
    await ElMessageBox.confirm(
      `确定删除文件类型配置"${config.type_name}"吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await fileTypeConfigsApi.delete(config.id)
    if (response.data && response.data.success) {
      ElMessage.success('删除成功')
      await fetchConfigs()
    } else {
      ElMessage.error(response.data?.message || '删除失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除配置失败:', error)
      ElMessage.error(error.message || '删除失败')
    }
  }
}

// 删除存储表（已废弃，保留以防兼容）
const addStorageTable = () => {
  // 不再需要，使用多选框
}

const removeStorageTable = (index) => {
  // 不再需要，使用多选框
}

// 移除选中的表
const removeTable = (tableName) => {
  const index = form.storage_tables.indexOf(tableName)
  if (index > -1) {
    form.storage_tables.splice(index, 1)
  }
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()

    // 验证存储表配置
    if (form.storage_tables.length === 0) {
      ElMessage.warning('请至少选择一个存储表')
      activeTab.value = 'storage'
      return
    }

    // 解析JSON字符串
    let ocrConfig = null
    let formConfig = null
    let validationRules = null

    if (ocrConfigStr.value.trim()) {
      try {
        ocrConfig = JSON.parse(ocrConfigStr.value)
      } catch (e) {
        ElMessage.error('OCR配置格式错误，请检查JSON格式')
        activeTab.value = 'ocr'
        return
      }
    }

    if (formConfigStr.value.trim()) {
      try {
        formConfig = JSON.parse(formConfigStr.value)
      } catch (e) {
        ElMessage.error('表单配置格式错误，请检查JSON格式')
        activeTab.value = 'form'
        return
      }
    }

    if (validationRulesStr.value.trim()) {
      try {
        validationRules = JSON.parse(validationRulesStr.value)
      } catch (e) {
        ElMessage.error('验证规则格式错误，请检查JSON格式')
        activeTab.value = 'form'
        return
      }
    }

    submitting.value = true

    const data = {
      type_code: form.type_code,
      type_name: form.type_name,
      type_description: form.type_description,
      model_config_id: form.model_config_id,
      ocr_config: ocrConfig,
      storage_tables: form.storage_tables,
      adapter_class: form.adapter_class,
      adapter_module: form.adapter_module,
      form_config: formConfig,
      form_component: form.form_component,
      validation_rules: validationRules,
      is_active: form.is_active,
      sort_order: form.sort_order
    }

    let response
    if (dialogMode.value === 'create') {
      response = await fileTypeConfigsApi.create(data)
    } else {
      response = await fileTypeConfigsApi.update(form.id, data)
    }

    if (response.data && response.data.success) {
      ElMessage.success(dialogMode.value === 'create' ? '创建成功' : '更新成功')
      dialogVisible.value = false
      await fetchConfigs()
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
    type_code: '',
    type_name: '',
    type_description: '',
    model_config_id: null,
    ocr_config: null,
    storage_tables: [],
    adapter_class: '',
    adapter_module: 'adapters',
    form_config: null,
    form_component: '',
    validation_rules: null,
    is_active: true,
    sort_order: 0
  })

  ocrConfigStr.value = ''
  formConfigStr.value = ''
  validationRulesStr.value = ''
  activeTab.value = 'basic'

  formRef.value?.clearValidate()
}

// ==================== 表单预览功能 ====================

// 预览对话框相关
const previewDialogVisible = ref(false)
const previewFormRef = ref(null)
const previewFormConfig = ref(null)
const previewFormData = ref({})

// 示例对话框相关
const exampleDialogVisible = ref(false)
const exampleTab = ref('basic')

// 预览表单
const previewForm = () => {
  try {
    const config = JSON.parse(formConfigStr.value)
    previewFormConfig.value = config
    previewFormData.value = {}
    previewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('表单配置JSON格式错误：' + error.message)
  }
}

// 测试表单验证
const testFormValidation = async () => {
  try {
    const valid = await previewFormRef.value.validate()
    if (valid) {
      ElMessage.success('表单验证通过！')
      console.log('表单数据：', previewFormData.value)
    }
  } catch (error) {
    ElMessage.warning('表单验证失败，请检查必填项')
  }
}

// 显示表单配置示例
const showFormConfigExample = () => {
  exampleDialogVisible.value = true
  exampleTab.value = 'basic'
}

// 使用示例
const useExample = (type) => {
  if (type === 'basic') {
    formConfigStr.value = JSON.stringify(basicExampleObj, null, 2)
  } else if (type === 'advanced') {
    formConfigStr.value = JSON.stringify(advancedExampleObj, null, 2)
  }
  exampleDialogVisible.value = false
  activeTab.value = 'form'
  ElMessage.success('示例已应用到表单配置')
}

// 基础示例对象
const basicExampleObj = {
  labelWidth: '120px',
  labelPosition: 'right',
  sections: [
    {
      title: '基本信息',
      description: '填写文档的基本信息',
      fields: [
        {
          name: 'title',
          label: '标题',
          type: 'text',
          required: true,
          span: 24,
          placeholder: '请输入标题',
          maxLength: 100
        },
        {
          name: 'code',
          label: '编号',
          type: 'text',
          required: true,
          span: 12,
          placeholder: '请输入编号',
          pattern: '^[A-Z0-9]+$',
          patternMessage: '只能包含大写字母和数字'
        },
        {
          name: 'status',
          label: '状态',
          type: 'select',
          required: true,
          span: 12,
          options: [
            { label: '草稿', value: 'draft' },
            { label: '已提交', value: 'submitted' },
            { label: '已完成', value: 'completed' }
          ]
        },
        {
          name: 'date',
          label: '日期',
          type: 'date',
          required: true,
          span: 12,
          format: 'YYYY-MM-DD'
        },
        {
          name: 'count',
          label: '数量',
          type: 'number',
          span: 12,
          min: 0,
          max: 999,
          step: 1
        },
        {
          name: 'description',
          label: '描述',
          type: 'textarea',
          span: 24,
          rows: 4,
          placeholder: '请输入描述信息',
          maxLength: 500
        }
      ]
    }
  ]
}

// 高级示例对象
const advancedExampleObj = {
  labelWidth: '120px',
  labelPosition: 'right',
  sections: [
    {
      title: '更多字段类型',
      fields: [
        {
          name: 'enabled',
          label: '是否启用',
          type: 'switch',
          span: 12,
          activeText: '是',
          inactiveText: '否'
        },
        {
          name: 'priority',
          label: '优先级',
          type: 'radio',
          span: 12,
          options: [
            { label: '高', value: 'high' },
            { label: '中', value: 'medium' },
            { label: '低', value: 'low' }
          ]
        },
        {
          name: 'tags',
          label: '标签',
          type: 'checkbox',
          span: 24,
          options: [
            { label: '重要', value: 'important' },
            { label: '紧急', value: 'urgent' },
            { label: '待处理', value: 'pending' }
          ]
        },
        {
          name: 'score',
          label: '评分',
          type: 'rate',
          span: 12,
          max: 5,
          showText: true
        },
        {
          name: 'progress',
          label: '进度',
          type: 'slider',
          span: 12,
          min: 0,
          max: 100,
          showInput: true
        }
      ]
    }
  ]
}

// 基础示例（显示用）
const basicExample = computed(() => JSON.stringify(basicExampleObj, null, 2))

// 高级示例（显示用）
const advancedExample = computed(() => JSON.stringify(advancedExampleObj, null, 2))

// 字段文档
const fieldDocumentation = [
  {
    property: 'name',
    type: 'String',
    description: '字段名称（必填）',
    example: 'title'
  },
  {
    property: 'label',
    type: 'String',
    description: '字段标签（必填）',
    example: '标题'
  },
  {
    property: 'type',
    type: 'String',
    description: '字段类型（必填）',
    example: 'text'
  },
  {
    property: 'required',
    type: 'Boolean',
    description: '是否必填',
    example: 'true'
  },
  {
    property: 'span',
    type: 'Number',
    description: '栅格占位（1-24）',
    example: '12'
  },
  {
    property: 'placeholder',
    type: 'String',
    description: '占位提示',
    example: '请输入标题'
  },
  {
    property: 'options',
    type: 'Array',
    description: 'select/radio/checkbox的选项',
    example: '[{label,value}]'
  },
  {
    property: 'min/max',
    type: 'Number',
    description: 'number/slider的最小/最大值',
    example: '0, 100'
  },
  {
    property: 'pattern',
    type: 'String',
    description: '正则验证',
    example: '^[A-Z0-9]+$'
  },
  {
    property: 'tip',
    type: 'String',
    description: '字段提示信息',
    example: '提示文本'
  }
]

// ==================== 页面初始化 ====================

onMounted(() => {
  fetchConfigs()
  fetchModelConfigs()
  fetchDatabaseTables()  // 新增：加载数据库表列表
})
</script>

<style lang="scss" scoped>
.file-type-config-page {
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

    .model-info {
      font-weight: 500;
      margin-bottom: 4px;
    }

    .model-url {
      font-size: 12px;
      color: $text-color-secondary;
    }

    .storage-tables {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;

      .table-tag {
        font-size: 12px;
      }
    }
  }

  .form-tip {
    font-size: 12px;
    color: $text-color-secondary;
    margin-top: 4px;
  }

  .model-option {
    display: flex;
    flex-direction: column;

    .model-url {
      font-size: 12px;
      color: $text-color-secondary;
      margin-top: 2px;
    }
  }

  .storage-tables-config {
    .config-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-md;
      padding-bottom: $spacing-sm;
      border-bottom: 1px solid #eee;
      font-weight: 500;
    }

    .table-checkbox-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: $spacing-sm;
      max-height: 400px;
      overflow-y: auto;
      padding: $spacing-sm;
      background: #f5f7fa;
      border-radius: 4px;
    }

    .table-checkbox-item {
      margin: 0 !important;
      padding: $spacing-sm;
      background: white;
      border-radius: 4px;
      transition: all 0.3s;

      &:hover {
        background: #e8f4ff;
      }

      .table-checkbox-content {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-left: 8px;

        .table-name {
          font-weight: 500;
          font-size: 13px;
          color: $text-color-primary;
        }

        .table-label {
          font-size: 12px;
          color: $text-color-secondary;
        }
      }
    }

    .table-tag {
      margin: 0 $spacing-xs $spacing-xs 0;
    }

    .selected-tables {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-xs;
      min-height: 32px;
      align-items: center;
    }

    .empty-tip {
      font-size: 12px;
      color: $text-color-secondary;
    }
  }
}

// 表单预览样式
.preview-container {
  .el-alert {
    margin-bottom: 20px;
  }
}

.config-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

// 示例对话框样式
.example-description {
  margin-bottom: 15px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;

  p {
    margin: 0 0 10px 0;
    font-weight: 500;
  }

  ul {
    margin: 0;
    padding-left: 20px;

    li {
      margin: 5px 0;
      color: $text-color-secondary;
    }
  }
}

.example-code {
  padding: 15px;
  background: #1e1e1e;
  color: #d4d4d4;
  border-radius: 4px;
  overflow-x: auto;
  font-family: 'Courier New', Courier, monospace;
  font-size: 13px;
  line-height: 1.6;
  max-height: 400px;
  margin-bottom: 15px;
}

.field-docs {
  h4 {
    margin: 0 0 15px 0;
    font-size: 16px;
    font-weight: 500;
  }
}
</style>

