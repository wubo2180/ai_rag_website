<template>
  <div class="file-management-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">文件管理</h1>
        <p class="page-subtitle">管理已上传的文件和查看处理状态</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshFiles">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="$router.push('/upload')">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文件名..."
          clearable
          @input="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-model="fileTypeFilter"
          placeholder="文件类型"
          clearable
          @change="handleFilter"
          class="file-type-filter"
        >
          <el-option label="全部类型" value="" />
          <el-option
            v-for="type in fileTypes"
            :key="type.type_code"
            :label="type.type_name"
            :value="type.type_code"
          />
        </el-select>
        
        <el-select
          v-model="statusFilter"
          placeholder="处理状态"
          clearable
          @change="handleFilter"
          class="status-filter"
        >
          <el-option label="全部状态" value="" />
          <el-option label="待处理" value="pending" />
          <el-option label="处理中" value="processing" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          @change="handleFilter"
          class="date-filter"
        />
      </div>
      
      <div class="filter-right">
        <el-button-group>
          <el-button
            :type="viewMode === 'table' ? 'primary' : ''"
            @click="setViewMode('table')"
          >
            <el-icon><List /></el-icon>
            列表
          </el-button>
          <el-button
            :type="viewMode === 'grid' ? 'primary' : ''"
            @click="setViewMode('grid')"
          >
            <el-icon><Grid /></el-icon>
            网格
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedFiles.length > 0" class="batch-actions">
      <div class="batch-info">
        <span>已选择 {{ selectedFiles.length }} 个文件</span>
      </div>
      <div class="batch-buttons">
        <el-button @click="batchAssign">
          <el-icon><User /></el-icon>
          批量分配
        </el-button>
        <el-button @click="batchStartProcess">
          <el-icon><Operation /></el-icon>
          批量处理
        </el-button>
        <el-button @click="batchDownload">
          <el-icon><Download /></el-icon>
          批量下载
        </el-button>
        <el-button type="danger" @click="batchDelete">
          <el-icon><Delete /></el-icon>
          批量删除
        </el-button>
      </div>
    </div>

    <!-- 文件列表/网格 -->
    <div class="file-content">
      <!-- 表格视图 -->
      <el-card v-if="viewMode === 'table'" class="table-card">
        <el-table
          :data="fileList"
          v-loading="loading"
          @selection-change="handleSelectionChange"
          @sort-change="handleSortChange"
        >
          <el-table-column type="selection" width="55" />
          
          <el-table-column label="文件名" min-width="250" sortable="custom" prop="filename">
            <template #default="{ row }">
              <div class="file-cell">
                <el-icon class="file-icon">
                  <component :is="getFileIcon(row)" />
                </el-icon>
                <div class="file-info">
                  <div class="file-name" :title="row.filename">
                    {{ row.filename }}
                  </div>
                  <div class="file-meta">
                    {{ formatFileSize(row.file_size) }} • {{ row.page_count || 0 }} 页
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="状态" width="260">
            <template #default="{ row }">
              <div class="status-column">
                <el-tag :type="getStatusType(row.ocr_status)" size="small">
                  <el-icon v-if="row.ocr_status === 'processing'" class="is-loading">
                    <Loading />
                  </el-icon>
                  <el-icon v-else-if="row.ocr_status === 'completed'">
                    <Check />
                  </el-icon>
                  <el-icon v-else-if="row.ocr_status === 'failed'">
                    <Close />
                  </el-icon>
                  {{ getStatusText(row.ocr_status) }}
                </el-tag>
                
                <!-- 如果是委托单文件，显示额外标识 -->
                <el-tooltip
                  v-if="isCommissionFile(row) && row.ocr_status === 'completed'"
                  content="委托测试申请单已处理完成"
                  placement="top"
                >
                  <el-tag type="success" size="small" effect="dark" style="margin-left: 4px;">
                    <el-icon><Document /></el-icon>
                    委托单
                  </el-tag>
                </el-tooltip>
                
                <!-- 核对状态标识 -->
                <el-tooltip
                  v-if="row.review_status === 'completed'"
                  content="文件已完成核对"
                  placement="top"
                >
                  <el-tag type="success" size="small" effect="plain" style="margin-left: 4px;">
                    <el-icon><CircleCheck /></el-icon>
                    已核对
                  </el-tag>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="审核人员" width="150">
            <template #default="{ row }">
              <div v-if="row.assignment" class="assignee-cell">
                <el-tooltip :content="`分配人: ${row.assignment.assigner_name}`" placement="top">
                  <el-tag type="primary" size="small">
                    <el-icon><User /></el-icon>
                    {{ row.assignment.assignee_name }}
                  </el-tag>
                </el-tooltip>
              </div>
              <span v-else class="empty-text">未分配</span>
            </template>
          </el-table-column>
          
          <el-table-column label="上传时间" width="180" sortable="custom" prop="created_at">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="处理时间" width="180">
            <template #default="{ row }">
              {{ row.ocr_completed_at ? formatTime(row.ocr_completed_at) : '-' }}
            </template>
          </el-table-column>
          
          <el-table-column label="标签" width="150">
            <template #default="{ row }">
              <div class="tags-cell">
                <el-tag
                  v-for="tag in row.tags?.slice(0, 2)"
                  :key="tag"
                  size="small"
                  class="tag-item"
                >
                  {{ tag }}
                </el-tag>
                <el-tag
                  v-if="row.tags?.length > 2"
                  size="small"
                  type="info"
                >
                  +{{ row.tags.length - 2 }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="240" fixed="right">
            <template #default="{ row }">
              <div class="action-buttons">
                <!-- 识别按钮：用于未识别或识别失败的文件 -->
                <el-button
                  v-if="row.ocr_status === 'pending' || row.ocr_status === 'failed'"
                  type="primary"
                  size="small"
                  :disabled="processingFileIds.has(row.id)"
                  :loading="processingFileIds.has(row.id)"
                  @click="recognizeFile(row)"
                >
                  <el-icon><MagicStick /></el-icon>
                  {{ processingFileIds.has(row.id) ? '处理中' : '识别' }}
                </el-button>
                <!-- 核对按钮：用于已识别的文件 -->
                <el-button
                  v-else
                  type="primary"
                  size="small"
                  :disabled="processingFileIds.has(row.id)"
                  @click="reviewFile(row)"
                >
                  <el-icon><View /></el-icon>
                  核对
                </el-button>
                <el-dropdown 
                  @command="(cmd) => handleAction(cmd, row)"
                  :disabled="processingFileIds.has(row.id)"
                >
                  <el-button 
                    size="small"
                    :disabled="processingFileIds.has(row.id)"
                  >
                    更多
                    <el-icon><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item 
                        command="process"
                        :disabled="processingFileIds.has(row.id)"
                      >
                        <el-icon><Operation /></el-icon>
                        识别处理
                      </el-dropdown-item>
                      <el-dropdown-item command="download">
                        <el-icon><Download /></el-icon>
                        下载
                      </el-dropdown-item>
                      <el-dropdown-item command="preview">
                        <el-icon><View /></el-icon>
                        预览
                      </el-dropdown-item>
                      <el-dropdown-item command="edit">
                        <el-icon><Edit /></el-icon>
                        编辑信息
                      </el-dropdown-item>
                      <el-dropdown-item 
                        command="delete" 
                        divided
                        :disabled="processingFileIds.has(row.id)"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 网格视图 -->
      <div v-else class="grid-view">
        <div v-if="loading" class="loading-grid">
          <el-skeleton
            v-for="i in 8"
            :key="i"
            :loading="true"
            animated
            class="skeleton-card"
          >
            <template #template>
              <el-skeleton-item variant="image" class="skeleton-image" />
              <el-skeleton-item variant="text" />
              <el-skeleton-item variant="text" />
            </template>
          </el-skeleton>
        </div>
        
        <div v-else class="file-grid">
          <div
            v-for="file in fileList"
            :key="file.id"
            :class="['file-card', { 'selected': selectedFiles.includes(file) }]"
            @click="toggleSelection(file)"
          >
            <div class="card-header">
              <el-checkbox
                :model-value="selectedFiles.includes(file)"
                @change="toggleSelection(file)"
                @click.stop
              />
              <el-dropdown @command="(cmd) => handleAction(cmd, file)">
                <el-button type="text" size="small">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="recognize">
                      <el-icon><MagicStick /></el-icon>
                      识别
                    </el-dropdown-item>
                    <el-dropdown-item command="process">识别处理</el-dropdown-item>
                    <el-dropdown-item command="review">核对</el-dropdown-item>
                    <el-dropdown-item command="download">下载</el-dropdown-item>
                    <el-dropdown-item command="delete">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
            
            <div class="card-preview">
              <el-icon class="preview-icon">
                <component :is="getFileIcon(file)" />
              </el-icon>
            </div>
            
            <div class="card-content">
              <div class="file-title" :title="file.filename">
                {{ file.filename }}
              </div>
              <div class="file-details">
                <div class="detail-item">
                  <span>大小: {{ formatFileSize(file.file_size) }}</span>
                </div>
                <div class="detail-item">
                  <span>页数: {{ file.page_count || 0 }}</span>
                </div>
                <div class="detail-item">
                  <el-tag :type="getStatusType(file.ocr_status)" size="small">
                    {{ getStatusText(file.ocr_status) }}
                  </el-tag>
                </div>
              </div>
              <div class="file-time">
                {{ formatTime(file.created_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <!-- 编辑文件信息对话框 -->
    <el-dialog
      v-model="editDialog.visible"
      title="编辑文件信息"
      width="500px"
    >
      <el-form
        ref="editFormRef"
        :model="editDialog.form"
        label-width="80px"
      >
        <el-form-item label="描述">
          <el-input
            v-model="editDialog.form.description"
            type="textarea"
            :rows="3"
            placeholder="输入文件描述"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-input
            v-model="editDialog.form.tagsInput"
            placeholder="输入标签，用逗号分隔"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="editDialog.saving"
          @click="saveFileInfo"
        >
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量分配对话框 -->
    <el-dialog
      v-model="assignDialog.visible"
      title="批量分配文件"
      width="500px"
    >
      <div class="assign-dialog-content">
        <div class="assign-info">
          <el-icon><InfoFilled /></el-icon>
          <span>将为 <strong>{{ selectedFiles.length }}</strong> 个文件分配核对人员</span>
        </div>
        
        <el-form
          ref="assignFormRef"
          :model="assignDialog.form"
          label-width="100px"
        >
          <el-form-item label="核对人员" prop="assigneeId" required>
            <el-select
              v-model="assignDialog.form.assigneeId"
              placeholder="请选择核对人员"
              style="width: 100%"
              filterable
              v-loading="assignDialog.loadingUsers"
            >
              <el-option
                v-for="user in assignDialog.userList"
                :key="user.id"
                :label="`${user.real_name || user.username} (${user.email})`"
                :value="user.id"
              >
                <div class="user-option">
                  <span class="user-name">{{ user.real_name || user.username }}</span>
                  <span class="user-email">{{ user.email }}</span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="优先级">
            <el-radio-group v-model="assignDialog.form.priority">
              <el-radio label="low">低</el-radio>
              <el-radio label="normal">普通</el-radio>
              <el-radio label="high">高</el-radio>
              <el-radio label="urgent">紧急</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item label="备注">
            <el-input
              v-model="assignDialog.form.notes"
              type="textarea"
              :rows="3"
              placeholder="请输入备注信息（可选）"
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="assignDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="assignDialog.assigning"
          @click="submitBatchAssign"
        >
          确认分配
        </el-button>
      </template>
    </el-dialog>

    <!-- 模型选择对话框 -->
    <el-dialog
      v-model="modelDialog.visible"
      title="选择识别模型"
      width="500px"
    >
      <div class="model-dialog-content">
        <div class="model-info">
          <el-icon><Setting /></el-icon>
          <span>为文件 <strong>{{ modelDialog.currentFile?.filename }}</strong> 选择识别模型</span>
        </div>
        
        <el-form label-width="80px">
          <el-form-item label="选择模型" required>
            <el-radio-group v-model="modelDialog.selectedModelId">
              <div
                v-for="model in modelDialog.models"
                :key="model.id"
                class="model-option"
              >
                <el-radio :label="model.id">
                  <div class="model-details">
                    <div class="model-name">
                      {{ model.name }}
                      <el-tag v-if="model.is_default" size="small" type="success">默认</el-tag>
                    </div>
                    <div class="model-description">{{ model.description }}</div>
                    <div class="model-meta">
                      <span class="model-url">{{ model.api_url }}</span>
                      <span class="model-timeout">超时: {{ model.timeout }}s</span>
                    </div>
                  </div>
                </el-radio>
              </div>
            </el-radio-group>
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="modelDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="modelDialog.loading"
          @click="confirmModelSelection"
        >
          开始处理
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { debounce } from 'lodash-es'
import { useAppStore } from '@/stores/app'
import { filesApi } from '@/api/files'
import { recognizeApi } from '@/api/recognize'
import { usersApi } from '@/api/users'
import { modelConfigsApi } from '@/api/model-configs'
import { fileTypeConfigsApi } from '@/api/file-type-configs'
import { useAuthStore } from '@/stores/auth'
import {
  ElMessage,
  ElMessageBox,
  ElNotification
} from 'element-plus'
import {
  Check,
  Close,
  Loading,
  Document,
  Download,
  View,
  Edit,
  Delete,
  MoreFilled,
  FolderOpened,
  Picture,
  Document as DocumentIcon,
  VideoPlay,
  Files,
  Operation,
  ArrowDown,
  User,
  InfoFilled,
  CircleCheck,
  Setting,
  MagicStick,
  Search,
  Refresh,
  List,
  Grid,
  Upload
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()

// 响应式数据
const loading = ref(false)
const fileList = ref([])
const selectedFiles = ref([])
const viewMode = ref('table')

// 处理中的文件ID集合（用于禁用按钮）
const processingFileIds = ref(new Set())

// 文件类型列表
const fileTypes = ref([])

// 搜索和筛选
const searchKeyword = ref('')
const fileTypeFilter = ref('')
const statusFilter = ref('')
const dateRange = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

// 编辑对话框
const editDialog = reactive({
  visible: false,
  saving: false,
  currentFile: null,
  form: {
    description: '',
    tagsInput: ''
  }
})

const editFormRef = ref()

// 批量分配对话框
const assignDialog = reactive({
  visible: false,
  assigning: false,
  loadingUsers: false,
  userList: [],
  form: {
    assigneeId: null,
    priority: 'normal',
    notes: ''
  }
})

const assignFormRef = ref()

// 模型选择对话框
const modelDialog = reactive({
  visible: false,
  loading: false,
  models: [],
  selectedModelId: null,
  currentFile: null
})

// 方法
const fetchFiles = async () => {
  try {
    loading.value = true
    
    const params = {
      page: pagination.page,
      per_page: pagination.pageSize
    }
    
    if (searchKeyword.value) {
      params.search = searchKeyword.value
    }
    
    if (fileTypeFilter.value) {
      params.document_type = fileTypeFilter.value
    }
    
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    
    if (dateRange.value?.length === 2) {
      params.start_date = dayjs(dateRange.value[0]).toISOString()
      params.end_date = dayjs(dateRange.value[1]).toISOString()
    }
    
    console.log('[文件列表] 请求参数:', params)
    
    const response = await filesApi.getFiles(params)
    
    console.log('[文件列表] 响应数据:', response.data)
    
    if (response.data.success) {
      fileList.value = response.data.data.files
      pagination.total = response.data.data.total
      
      console.log('[文件列表] 文件数量:', fileList.value.length)
      console.log('[文件列表] 第一个文件:', fileList.value[0])
    }
    
  } catch (error) {
    console.error('获取文件列表失败:', error)
    ElMessage.error('获取文件列表失败')
  } finally {
    loading.value = false
  }
}

const refreshFiles = () => {
  fetchFiles()
}

const handleSearch = debounce(() => {
  pagination.page = 1
  fetchFiles()
}, 500)

const handleFilter = () => {
  pagination.page = 1
  fetchFiles()
}

const setViewMode = (mode) => {
  viewMode.value = mode
}

const handleSelectionChange = (selection) => {
  selectedFiles.value = selection
}

const handleSortChange = ({ prop, order }) => {
  // 处理排序
  fetchFiles()
}

const handlePageChange = (page) => {
  pagination.page = page
  fetchFiles()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchFiles()
}

const toggleSelection = (file) => {
  const index = selectedFiles.value.indexOf(file)
  if (index > -1) {
    selectedFiles.value.splice(index, 1)
  } else {
    selectedFiles.value.push(file)
  }
}

// 判断是否为委托单文件
const isCommissionFile = (file) => {
  if (!file.filename) return false
  
  const commissionKeywords = [
    '委托单', '委托测试', '申请单', '品质部', 
    '原材料委托', 'IBTC', 'IBoxTech'
  ]
  
  const filename = file.filename.toLowerCase()
  return commissionKeywords.some(keyword => 
    filename.includes(keyword.toLowerCase())
  )
}

const reviewFile = (file) => {
  window.open(`/review/${file.id}`, '_blank')
}

// 跳转到识别页面
const recognizeFile = (file) => {
  window.open(`/recognize/${file.id}`, '_blank')
}

const handleAction = async (command, file) => {
  switch (command) {
    case 'recognize':
      recognizeFile(file)
      break
    case 'review':
      reviewFile(file)
      break
    case 'process':
      await startProcessing(file)
      break
    case 'download':
      await downloadFile(file)
      break
    case 'preview':
      await previewFile(file)
      break
    case 'edit':
      editFileInfo(file)
      break
    case 'delete':
      await deleteFile(file)
      break
  }
}

const startProcessing = async (file) => {
  try {
    // 根据文件的业务类型获取可用模型
    const modelResponse = await modelConfigsApi.getForFile(file.file_type || '未知')
    
    if (modelResponse.success && modelResponse.data.models && modelResponse.data.models.length > 1) {
      // 有多个模型可选，显示选择对话框
      modelDialog.currentFile = file
      modelDialog.models = modelResponse.data.models
      modelDialog.selectedModelId = modelResponse.data.default_model?.id
      modelDialog.visible = true
    } else {
      // 只有一个模型或使用默认模型，直接处理
      await processFile(file, modelResponse.data.default_model?.id)
    }
  } catch (error) {
    console.error('获取模型配置失败:', error)
    // 如果获取模型失败，仍然尝试使用默认模型处理
    await processFile(file, null)
  }
}

// 实际执行文件处理（使用异步任务API）
const processFile = async (file, modelId = null) => {
  let pollInterval = null
  
  try {
    // 添加到处理中集合
    processingFileIds.value.add(file.id)
    
    const isReprocessing = file.ocr_status === 'completed'
    const processingMsg = isReprocessing ? '重新识别处理中，请稍候...' : '开始识别处理，请稍候...'
    
    const loadingMessage = ElMessage.info({
      message: '正在创建OCR识别任务...',
      duration: 0,
      showClose: true
    })
    
    console.log('📄 [processFile] 开始识别，文件ID:', file.id)
    console.log('📑 [processFile] 文档类型:', file.document_type_code)
    
    // 创建异步OCR任务
    const apiResponse = await recognizeApi.recognize(file.id)
    const response = apiResponse.data
    
    if (!response.success) {
      loadingMessage.close()
      ElMessage.error(response.message || 'OCR识别任务创建失败')
      processingFileIds.value.delete(file.id)
      return
    }
    
    const taskId = response.data.task_id
    console.log('✅ [processFile] 任务已创建，task_id:', taskId)
    
    loadingMessage.close()
    
    // 显示处理中消息
    const processingMessage = ElMessage.info({
      message: processingMsg,
      duration: 0,
      showClose: true
    })
    
    // 轮询任务状态
    let pollCount = 0
    const maxPolls = 120
    
    const pollTask = new Promise((resolve, reject) => {
      pollInterval = setInterval(async () => {
        pollCount++
        
        try {
          console.log(`⏱️ [processFile] 开始第 ${pollCount} 次轮询...`)
          
          const taskResponse = await recognizeApi.getTaskStatus(taskId)
          const task = taskResponse.data.data.task
          
          console.log(`📊 [processFile] 任务状态: ${task.status}`)
          
          if (task.status === 'completed') {
            clearInterval(pollInterval)
            resolve(task)
          } else if (task.status === 'failed') {
            clearInterval(pollInterval)
            reject(new Error(task.error_message || '识别处理失败'))
          } else if (pollCount >= maxPolls) {
            clearInterval(pollInterval)
            reject(new Error('识别处理超时'))
          }
        } catch (error) {
          console.error(`❌ [processFile] 轮询失败:`, error)
          // 继续轮询，不要因为单次失败就中断
        }
      }, 1000)
    })
    
    const result = await pollTask
    processingMessage.close()
    
    console.log('✅ [processFile] 识别完成！', result)
    
    // 显示成功消息
    setTimeout(() => {
      const successMsg = isReprocessing ? '文件重新识别处理完成！' : '文件识别处理完成！'
      ElMessage.success(successMsg)
      
      // 刷新文件列表
      fetchFiles()
    }, 100)
    
  } catch (error) {
    console.error('❌ [processFile] 识别处理失败:', error)
    ElMessage.error(error.message || '识别处理失败')
  } finally {
    // 从处理中集合移除
    processingFileIds.value.delete(file.id)
    if (pollInterval) {
      clearInterval(pollInterval)
    }
  }
}

// 确认模型选择并开始处理
const confirmModelSelection = async () => {
  if (!modelDialog.selectedModelId) {
    ElMessage.warning('请选择一个模型')
    return
  }
  
  modelDialog.visible = false
  await processFile(modelDialog.currentFile, modelDialog.selectedModelId)
  
  // 重置对话框
  modelDialog.currentFile = null
  modelDialog.models = []
  modelDialog.selectedModelId = null
}

const downloadFile = async (file) => {
  try {
    const response = await filesApi.downloadFile(file.id)
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = file.filename
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    ElMessage.error('下载失败')
  }
}

const previewFile = async (file) => {
  try {
    const response = await filesApi.getPreviewUrl(file.id)
    if (response.data.success) {
      window.open(response.data.data.url, '_blank')
    }
  } catch (error) {
    console.error('预览失败:', error)
    ElMessage.error('预览失败')
  }
}

const editFileInfo = (file) => {
  editDialog.currentFile = file
  editDialog.form.description = file.description || ''
  editDialog.form.tagsInput = file.tags?.join(', ') || ''
  editDialog.visible = true
}

const saveFileInfo = async () => {
  try {
    editDialog.saving = true
    
    const tags = editDialog.form.tagsInput
      .split(',')
      .map(tag => tag.trim())
      .filter(tag => tag)
    
    const response = await filesApi.updateFile(editDialog.currentFile.id, {
      description: editDialog.form.description,
      tags: tags
    })
    
    if (response.data.success) {
      ElMessage.success('保存成功')
      editDialog.visible = false
      await fetchFiles()
    }
    
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    editDialog.saving = false
  }
}

const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(
      `确认删除文件 "${file.filename}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const response = await filesApi.deleteFile(file.id)
    if (response.data.success) {
      ElMessage.success('删除成功')
      await fetchFiles()
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
      ElMessage.error('删除失败')
    }
  }
}

const batchStartProcess = async () => {
  const pendingFiles = selectedFiles.value.filter(file => file.ocr_status === 'pending')
  if (pendingFiles.length === 0) {
    ElMessage.warning('没有可处理的文件')
    return
  }
  
  try {
    for (const file of pendingFiles) {
      await startProcessing(file)
    }
    selectedFiles.value = []
  } catch (error) {
    console.error('批量处理失败:', error)
  }
}

const batchDownload = () => {
  selectedFiles.value.forEach(file => {
    downloadFile(file)
  })
}

const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确认删除选中的 ${selectedFiles.value.length} 个文件吗？`,
      '批量删除',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    for (const file of selectedFiles.value) {
      await filesApi.deleteFile(file.id)
    }
    
    ElMessage.success('批量删除成功')
    selectedFiles.value = []
    await fetchFiles()
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

// 批量分配
const batchAssign = async () => {
  // 获取用户列表
  assignDialog.loadingUsers = true
  try {
    const response = await usersApi.getUsers({ per_page: 100 })
    if (response.data.success) {
      assignDialog.userList = response.data.data.users
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
    return
  } finally {
    assignDialog.loadingUsers = false
  }
  
  // 重置表单
  assignDialog.form = {
    assigneeId: null,
    priority: 'normal',
    notes: ''
  }
  
  assignDialog.visible = true
}

// 提交批量分配
const submitBatchAssign = async () => {
  const form = assignFormRef.value
  if (!form) return

  // 验证
  if (!assignDialog.form.assigneeId) {
    ElMessage.warning('请选择核对人员')
    return
  }

  try {
    assignDialog.assigning = true
    
    const fileIds = selectedFiles.value.map(file => file.id)
    
    console.log('[批量分配] 开始分配')
    console.log('  - 文件ID:', fileIds)
    console.log('  - 审核人ID:', assignDialog.form.assigneeId)
    console.log('  - 优先级:', assignDialog.form.priority)
    console.log('  - 备注:', assignDialog.form.notes)
    
    // 调用批量分配API
    const response = await filesApi.batchAssignFiles({
      file_ids: fileIds,
      assignee_id: assignDialog.form.assigneeId,
      priority: assignDialog.form.priority,
      notes: assignDialog.form.notes
    })
    
    console.log('[批量分配] API响应:', response.data)
    
    if (response.data.success) {
      ElMessage.success(`成功分配 ${fileIds.length} 个文件`)
      assignDialog.visible = false
      selectedFiles.value = []
      await fetchFiles()
    } else {
      ElMessage.error(response.data.message || '分配失败')
    }

  } catch (error) {
    console.error('[批量分配] 失败:', error)
    console.error('[批量分配] 错误详情:', error.response?.data)
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('批量分配失败: ' + (error.message || '未知错误'))
    }
  } finally {
    assignDialog.assigning = false
  }
}

const getFileIcon = (file) => {
  const extension = file.filename.split('.').pop()?.toLowerCase()
  const iconMap = {
    pdf: 'Document',
    jpg: 'Picture',
    jpeg: 'Picture',
    png: 'Picture',
    gif: 'Picture',
    tiff: 'Picture'
  }
  return iconMap[extension] || 'Document'
}

const getStatusType = (status) => {
  const statusMap = {
    pending: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || '未知'
}

const formatFileSize = (size) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  let fileSize = size
  
  while (fileSize >= 1024 && index < units.length - 1) {
    fileSize /= 1024
    index++
  }
  
  return `${fileSize.toFixed(1)} ${units[index]}`
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

// 获取文件类型列表
const fetchFileTypes = async () => {
  try {
    const response = await fileTypeConfigsApi.getAll()
    if (response.data && response.data.success) {
      // 只显示启用的文件类型
      fileTypes.value = response.data.data.filter(type => type.is_active)
      console.log('[文件列表] 文件类型列表:', fileTypes.value)
    }
  } catch (error) {
    console.error('获取文件类型列表失败:', error)
    // 不显示错误提示，因为这不是关键功能
  }
}

// 生命周期
onMounted(() => {
  fetchFiles()
  fetchFileTypes()
})
</script>

<style lang="scss" scoped>
.file-management-container {
  padding: $spacing-lg;
  background: $bg-color-page;
  min-height: calc(100vh - 60px);
}

.page-header {
  @include flex-between;
  margin-bottom: $spacing-lg;
  
  .header-content {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: $text-color-primary;
      margin: 0 0 $spacing-xs;
    }
    
    .page-subtitle {
      font-size: 14px;
      color: $text-color-secondary;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: $spacing-sm;
  }
}

.filter-bar {
  @include flex-between;
  margin-bottom: $spacing-lg;
  padding: $spacing-md;
  background: $bg-color-white;
  border-radius: $border-radius-large;
  box-shadow: $box-shadow-base;
  
  .filter-left {
    display: flex;
    gap: $spacing-md;
    
    .search-input {
      width: 250px;
    }
    
    .file-type-filter {
      width: 140px;
    }
    
    .status-filter {
      width: 120px;
    }
    
    .date-filter {
      width: 300px;
    }
  }
}

.batch-actions {
  @include flex-between;
  margin-bottom: $spacing-lg;
  padding: $spacing-md;
  background: rgba($color-primary, 0.1);
  border-radius: $border-radius-base;
  border: 1px solid rgba($color-primary, 0.3);
  
  .batch-info {
    font-size: 14px;
    color: $color-primary;
  }
  
  .batch-buttons {
    display: flex;
    gap: $spacing-sm;
  }
}

.file-content {
  margin-bottom: $spacing-lg;
}

.table-card {
  .file-cell {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    
    .file-icon {
      font-size: 24px;
      color: $text-color-secondary;
    }
    
    .file-info {
      .file-name {
        font-size: 14px;
        color: $text-color-primary;
        @include text-ellipsis;
      }
      
      .file-meta {
        font-size: 12px;
        color: $text-color-placeholder;
        margin-top: 2px;
      }
    }
  }
  
  .tags-cell {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    
    .tag-item {
      margin: 0;
    }
  }
  
  .action-buttons {
    display: flex;
    gap: $spacing-xs;
  }
}

.grid-view {
  .loading-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: $spacing-lg;
    
    .skeleton-card {
      .skeleton-image {
        height: 160px;
        margin-bottom: $spacing-md;
      }
    }
  }
  
  .file-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: $spacing-lg;
    
    .file-card {
      background: $bg-color-white;
      border-radius: $border-radius-large;
      box-shadow: $box-shadow-base;
      transition: all 0.3s ease;
      cursor: pointer;
      
      &:hover {
        box-shadow: $box-shadow-light;
        transform: translateY(-2px);
      }
      
      &.selected {
        border: 2px solid $color-primary;
      }
      
      .card-header {
        @include flex-between;
        padding: $spacing-md;
      }
      
      .card-preview {
        @include flex-center;
        height: 120px;
        background: $bg-color-lighter;
        margin: 0 $spacing-md $spacing-md;
        border-radius: $border-radius-base;
        
        .preview-icon {
          font-size: 48px;
          color: $text-color-placeholder;
        }
      }
      
      .card-content {
        padding: 0 $spacing-md $spacing-md;
        
        .file-title {
          font-size: 14px;
          font-weight: 500;
          color: $text-color-primary;
          margin-bottom: $spacing-sm;
          @include text-ellipsis;
        }
        
        .file-details {
          margin-bottom: $spacing-sm;
          
          .detail-item {
            font-size: 12px;
            color: $text-color-secondary;
            margin-bottom: 4px;
            
            &:last-child {
              margin-bottom: 0;
            }
          }
        }
        
        .file-time {
          font-size: 11px;
          color: $text-color-placeholder;
        }
      }
    }
  }
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: $spacing-lg;
}

// 状态列样式
.status-column {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-wrap: nowrap;  // 不换行，保持在一行

  .el-tag {
    display: flex;
    align-items: center;
    gap: 4px;
    white-space: nowrap;  // 确保标签内容不换行

    .el-icon {
      font-size: 12px;
    }
  }
}

// 响应式设计
@include respond-to(lg) {
  .filter-bar {
    flex-direction: column;
    gap: $spacing-md;
    
    .filter-left,
    .filter-right {
      width: 100%;
    }
    
    .filter-left {
      flex-wrap: wrap;
    }
  }
}

@include respond-to(sm) {
  .file-management-container {
    padding: $spacing-sm;
  }
  
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-md;
    
    .header-actions {
      width: 100%;
      
      .el-button {
        flex: 1;
      }
    }
  }
  
  .filter-left {
    .search-input,
    .status-filter,
    .date-filter {
      width: 100% !important;
    }
  }
  
  .batch-actions {
    flex-direction: column;
    gap: $spacing-md;
    
    .batch-buttons {
      .el-button {
        flex: 1;
      }
    }
  }
}

// 批量分配对话框样式
.assign-dialog-content {
  .assign-info {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: $spacing-md;
    background: $bg-color-lighter;
    border-radius: $border-radius-base;
    margin-bottom: $spacing-lg;
    
    .el-icon {
      font-size: 18px;
      color: $color-primary;
    }
    
    span {
      font-size: 14px;
      color: $text-color-regular;
      
      strong {
        color: $color-primary;
        font-weight: 600;
      }
    }
  }
  
  .user-option {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .user-name {
      font-size: 14px;
      color: $text-color-primary;
      font-weight: 500;
    }
    
    .user-email {
      font-size: 12px;
      color: $text-color-secondary;
    }
  }
}

// 审核人员单元格样式
.assignee-cell {
  display: flex;
  align-items: center;
  
  .el-tag {
    display: flex;
    align-items: center;
    gap: 4px;
  }
}

.empty-text {
  font-size: 12px;
  color: $text-color-placeholder;
}

// 模型选择对话框样式
.model-dialog-content {
  .model-info {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 20px;
    padding: 12px;
    background-color: $bg-color-lighter;
    border-radius: 4px;
    
    .el-icon {
      color: $color-primary;
      font-size: 18px;
    }
  }
  
  .model-option {
    margin-bottom: 16px;
    padding: 12px;
    border: 1px solid $border-color-base;
    border-radius: 4px;
    transition: all 0.2s;
    
    &:hover {
      border-color: $color-primary;
      background-color: $bg-color-lighter;
    }
    
    .el-radio {
      width: 100%;
      
      ::v-deep(.el-radio__label) {
        width: 100%;
      }
    }
    
    .model-details {
      .model-name {
        font-weight: 500;
        margin-bottom: 4px;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      
      .model-description {
        font-size: 12px;
        color: $text-color-secondary;
        margin-bottom: 8px;
      }
      
      .model-meta {
        display: flex;
        gap: 12px;
        font-size: 12px;
        color: $text-color-placeholder;
        
        .model-url {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .model-timeout {
          flex-shrink: 0;
        }
      }
    }
  }
}

// 响应式设计
@include respond-to(lg) {
  .filter-bar {
    flex-direction: column;
    gap: $spacing-md;
    
    .filter-left {
      flex-direction: column;
      width: 100%;
      
      .search-input,
      .status-filter,
      .date-filter {
        width: 100%;
      }
    }
  }
  
  .batch-actions {
    flex-direction: column;
    
    .batch-buttons {
      width: 100%;
      
      .el-button {
        flex: 1;
      }
    }
  }
}
</style>
