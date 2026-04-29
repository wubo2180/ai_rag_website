<template>
  <div class="file-upload-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">文件上传</h1>
        <p class="page-subtitle">支持 PDF、JPG、PNG、TIFF 格式，单个文件最大 100MB</p>
      </div>
      <div class="header-actions">
        <el-button @click="clearAllFiles">
          <el-icon><Delete /></el-icon>
          清空列表
        </el-button>
        <el-button
          type="primary"
          :disabled="fileList.length === 0 || isUploading"
          :loading="isUploading"
          @click="startUpload"
        >
          <el-icon><Upload /></el-icon>
          {{ isUploading ? '上传中...' : '开始上传' }}
        </el-button>
      </div>
    </div>

    <!-- 上传区域 -->
    <div class="upload-section">
      <el-card class="upload-card">
        <el-upload
          ref="uploadRef"
          v-model:file-list="fileList"
          :auto-upload="false"
          :multiple="true"
          :accept="acceptedTypes"
          :before-upload="beforeUpload"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          drag
          class="upload-dragger"
        >
          <div class="upload-content">
            <el-icon class="upload-icon">
              <UploadFilled />
            </el-icon>
            <div class="upload-text">
              <p class="upload-title">将文件拖拽到此处，或<em>点击上传</em></p>
              <p class="upload-hint">
                支持扩展名：{{ acceptedExtensions.join(', ') }}
              </p>
            </div>
          </div>
        </el-upload>

        <!-- 批量操作栏 -->
        <div v-if="fileList.length > 0" class="batch-actions">
          <div class="batch-info">
            <span>已选择 {{ fileList.length }} 个文件</span>
            <span>总大小：{{ formatTotalSize() }}</span>
          </div>
          <div class="batch-controls">
            <el-select
              v-model="documentTypeCode"
              placeholder="请选择文档类型（必填）"
              class="batch-input"
              filterable
            >
              <el-option
                v-for="type in documentTypes"
                :key="type.type_code"
                :label="type.type_name"
                :value="type.type_code"
              >
                <span>{{ type.type_name }}</span>
                <span style="float: right; color: var(--el-text-color-secondary); font-size: 12px">
                  {{ type.type_code }}
                </span>
              </el-option>
            </el-select>
            <el-input
              v-model="batchDescription"
              placeholder="批次描述（可选）"
              class="batch-input"
            />
            <el-input
              v-model="batchTags"
              placeholder="标签，用逗号分隔（可选）"
              class="batch-input"
            />
          </div>
        </div>
      </el-card>
    </div>

    <!-- 文件列表 -->
    <div v-if="fileList.length > 0" class="file-list-section">
      <el-card class="file-list-card">
        <template #header>
          <div class="card-header">
            <h3>文件列表</h3>
            <div class="header-actions">
              <el-checkbox
                v-model="selectAll"
                :indeterminate="indeterminate"
                @change="handleSelectAll"
              >
                全选
              </el-checkbox>
            </div>
          </div>
        </template>

        <div class="file-list">
          <div
            v-for="(file, index) in fileList"
            :key="file.uid"
            :class="['file-item', { 'is-selected': file.selected }]"
          >
            <div class="file-checkbox">
              <el-checkbox
                v-model="file.selected"
                @change="handleFileSelect"
              />
            </div>

            <div class="file-icon">
              <el-icon>
                <component :is="getFileIcon(file)" />
              </el-icon>
            </div>

            <div class="file-info">
              <div class="file-name" :title="file.name">
                {{ file.name }}
              </div>
              <div class="file-meta">
                {{ formatFileSize(file.size) }} • {{ getFileType(file) }}
                <el-tag
                  v-if="file.status === 'ready'"
                  type="info"
                  size="small"
                >
                  待上传
                </el-tag>
                <el-tag
                  v-else-if="file.status === 'uploading'"
                  type="warning"
                  size="small"
                >
                  上传中
                </el-tag>
                <el-tag
                  v-else-if="file.status === 'success'"
                  type="success"
                  size="small"
                >
                  已上传
                </el-tag>
                <el-tag
                  v-else-if="file.status === 'fail'"
                  type="danger"
                  size="small"
                >
                  上传失败
                </el-tag>
              </div>
            </div>

            <div class="file-progress">
              <el-progress
                v-if="file.status === 'uploading'"
                :percentage="file.percentage || 0"
                :stroke-width="4"
              />
              <el-icon
                v-else-if="file.status === 'success'"
                class="success-icon"
              >
                <CircleCheckFilled />
              </el-icon>
              <el-icon
                v-else-if="file.status === 'fail'"
                class="error-icon"
              >
                <CircleCloseFilled />
              </el-icon>
            </div>

            <div class="file-actions">
              <el-dropdown
                @command="(command) => handleFileAction(command, file, index)"
              >
                <el-button type="text">
                  <el-icon><MoreFilled /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      v-if="file.status === 'fail'"
                      command="retry"
                    >
                      <el-icon><RefreshRight /></el-icon>
                      重试
                    </el-dropdown-item>
                    <el-dropdown-item command="preview">
                      <el-icon><View /></el-icon>
                      预览
                    </el-dropdown-item>
                    <el-dropdown-item command="remove" divided>
                      <el-icon><Delete /></el-icon>
                      移除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 上传历史 -->
    <div class="upload-history-section">
      <el-card class="history-card">
        <template #header>
          <div class="card-header">
            <h3>最近上传</h3>
            <el-link type="primary" @click="$router.push('/files')">
              查看全部
            </el-link>
          </div>
        </template>

        <div v-if="uploadHistory.length === 0" class="empty-history">
          <el-icon class="empty-icon"><Document /></el-icon>
          <p class="empty-text">暂无上传记录</p>
        </div>

        <div v-else class="history-list">
          <div
            v-for="item in uploadHistory"
            :key="item.id"
            class="history-item"
          >
            <div class="history-icon">
              <el-icon><Document /></el-icon>
            </div>
            <div class="history-info">
              <div class="history-name">{{ item.filename }}</div>
              <div class="history-meta">
                {{ formatFileSize(item.file_size) }} • {{ formatTime(item.created_at) }}
              </div>
            </div>
            <div class="history-status">
              <el-tag
                :type="getStatusType(item.ocr_status)"
                size="small"
              >
                {{ getStatusText(item.ocr_status) }}
              </el-tag>
            </div>
            <div class="history-actions">
              <el-button
                type="text"
                size="small"
                @click="viewFile(item)"
              >
                查看
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialog.visible"
      :title="previewDialog.file?.name"
      width="80%"
      :before-close="closePreview"
    >
      <div class="file-preview">
        <img
          v-if="previewDialog.type === 'image'"
          :src="previewDialog.url"
          alt="Preview"
          class="preview-image"
        />
        <div v-else class="preview-placeholder">
          <el-icon class="placeholder-icon"><Document /></el-icon>
          <p>此文件类型不支持预览</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { filesApi } from '@/api/files'
import { fileTypeConfigsApi } from '@/api/file-type-configs'
import { useAppStore } from '@/stores/app'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const appStore = useAppStore()

// 响应式数据
const uploadRef = ref()
const fileList = ref([])
const isUploading = ref(false)
const documentTypeCode = ref('')  // 新增：文档类型代码
const documentTypes = ref([])  // 新增：文档类型列表
const batchDescription = ref('')
const batchTags = ref('')

const selectAll = ref(false)
const indeterminate = ref(false)

const uploadHistory = ref([])

const previewDialog = reactive({
  visible: false,
  file: null,
  url: '',
  type: ''
})

// 配置
const acceptedExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']
const acceptedTypes = acceptedExtensions.join(',')
const maxFileSize = 100 * 1024 * 1024 // 100MB

// 计算属性
const selectedFiles = computed(() => {
  return fileList.value.filter(file => file.selected)
})

// 方法
const beforeUpload = (file) => {
  // 检查文件类型
  const extension = '.' + file.name.split('.').pop().toLowerCase()
  if (!acceptedExtensions.includes(extension)) {
    ElMessage.error(`不支持的文件类型：${extension}`)
    return false
  }

  // 检查文件大小
  if (file.size > maxFileSize) {
    ElMessage.error(`文件大小超过限制：${formatFileSize(maxFileSize)}`)
    return false
  }

  return true
}

const handleFileChange = (file, fileList) => {
  // 为新添加的文件设置默认状态
  if (file.status === 'ready') {
    file.selected = true
    updateSelectAllState()
  }
}

const handleFileRemove = (file, fileList) => {
  updateSelectAllState()
}

const handleSelectAll = (checked) => {
  fileList.value.forEach(file => {
    file.selected = checked
  })
  updateSelectAllState()
}

const handleFileSelect = () => {
  updateSelectAllState()
}

const updateSelectAllState = () => {
  const selected = fileList.value.filter(file => file.selected)
  selectAll.value = selected.length === fileList.value.length
  indeterminate.value = selected.length > 0 && selected.length < fileList.value.length
}

const startUpload = async () => {
  const selectedFiles = fileList.value.filter(file => file.selected && file.status === 'ready')
  
  if (selectedFiles.length === 0) {
    ElMessage.warning('请选择要上传的文件')
    return
  }

  // 检查是否选择了文档类型
  if (!documentTypeCode.value) {
    ElMessage.warning('请先选择文档类型')
    return
  }

  isUploading.value = true
  appStore.showUploadProgress()

  try {
    // 创建表单数据
    const formData = new FormData()
    
    selectedFiles.forEach(file => {
      formData.append('files', file.raw)
    })
    
    // 新增：添加文档类型代码
    formData.append('document_type_code', documentTypeCode.value)
    
    if (batchDescription.value) {
      formData.append('description', batchDescription.value)
    }
    
    if (batchTags.value) {
      formData.append('tags', batchTags.value)
    }

    // 上传文件
    const response = await filesApi.batchUploadFiles(formData, (progressEvent) => {
      const percentage = Math.round((progressEvent.loaded * 100) / progressEvent.total)
      appStore.updateUploadProgress(percentage)
      
      // 更新文件状态
      selectedFiles.forEach(file => {
        file.status = 'uploading'
        file.percentage = percentage
      })
    })

    if (response.data.success) {
      appStore.updateUploadProgress(100, 'success')
      
      // 更新文件状态
      const results = response.data.data.results
      selectedFiles.forEach((file, index) => {
        const result = results[index]
        if (result && result.success) {
          file.status = 'success'
          file.percentage = 100
        } else {
          file.status = 'fail'
          file.percentage = 0
        }
      })
      
      ElMessage.success(`成功上传 ${response.data.data.successful_uploads} 个文件`)
      
      // 刷新上传历史
      fetchUploadHistory()
      
      // 清空表单
      setTimeout(() => {
        documentTypeCode.value = ''
        batchDescription.value = ''
        batchTags.value = ''
      }, 2000)
      
    } else {
      throw new Error(response.data.message)
    }

  } catch (error) {
    console.error('上传失败:', error)
    appStore.updateUploadProgress(0, 'exception')  // 使用 'exception' 而不是 'error'
    
    // 更新失败文件状态
    selectedFiles.forEach(file => {
      file.status = 'fail'
      file.percentage = 0
    })
    
    ElMessage.error('上传失败：' + (error.message || '未知错误'))
    
  } finally {
    isUploading.value = false
    setTimeout(() => {
      appStore.hideUploadProgress()
    }, 3000)
  }
}

const clearAllFiles = () => {
  fileList.value = []
  selectAll.value = false
  indeterminate.value = false
  documentTypeCode.value = ''
  batchDescription.value = ''
  batchTags.value = ''
}

const handleFileAction = (command, file, index) => {
  switch (command) {
    case 'retry':
      file.status = 'ready'
      file.percentage = 0
      file.selected = true
      updateSelectAllState()
      break
    case 'preview':
      previewFile(file)
      break
    case 'remove':
      fileList.value.splice(index, 1)
      updateSelectAllState()
      break
  }
}

const previewFile = (file) => {
  const fileType = getFileType(file).toLowerCase()
  
  if (['jpg', 'jpeg', 'png', 'gif'].includes(fileType)) {
    previewDialog.type = 'image'
    previewDialog.url = URL.createObjectURL(file.raw)
  } else {
    previewDialog.type = 'unsupported'
    previewDialog.url = ''
  }
  
  previewDialog.file = file
  previewDialog.visible = true
}

const closePreview = () => {
  if (previewDialog.url && previewDialog.type === 'image') {
    URL.revokeObjectURL(previewDialog.url)
  }
  previewDialog.visible = false
  previewDialog.file = null
  previewDialog.url = ''
  previewDialog.type = ''
}

const fetchUploadHistory = async () => {
  try {
    const response = await filesApi.getFiles({ page: 1, per_page: 5 })
    if (response.data.success) {
      uploadHistory.value = response.data.data.files
    }
  } catch (error) {
    console.error('获取上传历史失败:', error)
  }
}

const viewFile = (file) => {
  window.open(`/review/${file.id}`, '_blank')
}

const getFileIcon = (file) => {
  const fileType = getFileType(file).toLowerCase()
  const iconMap = {
    pdf: 'Document',
    jpg: 'Picture',
    jpeg: 'Picture',
    png: 'Picture',
    gif: 'Picture',
    tiff: 'Picture'
  }
  return iconMap[fileType] || 'Document'
}

const getFileType = (file) => {
  return file.name.split('.').pop()?.toLowerCase() || ''
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

const formatTotalSize = () => {
  const totalSize = fileList.value.reduce((sum, file) => sum + file.size, 0)
  return formatFileSize(totalSize)
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

const formatTime = (time) => {
  return dayjs(time).fromNow()
}

// 新增：获取文档类型列表
const fetchDocumentTypes = async () => {
  try {
    const response = await fileTypeConfigsApi.getAll()
    if (response.data.success) {
      documentTypes.value = response.data.data
      
      // 如果只有一个类型，自动选择
      if (documentTypes.value.length === 1) {
        documentTypeCode.value = documentTypes.value[0].type_code
      }
    }
  } catch (error) {
    console.error('获取文档类型列表失败:', error)
    ElMessage.error('获取文档类型列表失败')
  }
}

// 生命周期
onMounted(() => {
  fetchDocumentTypes()
  fetchUploadHistory()
})

onBeforeUnmount(() => {
  // 清理预览URL
  if (previewDialog.url && previewDialog.type === 'image') {
    URL.revokeObjectURL(previewDialog.url)
  }
})
</script>

<style lang="scss" scoped>

.file-upload-container {
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

.upload-section {
  margin-bottom: $spacing-lg;
}

.upload-card {
  .upload-dragger {
    :deep(.el-upload-dragger) {
      width: 100%;
      height: 200px;
      border: 2px dashed $border-color-light;
      border-radius: $border-radius-large;
      background: $bg-color-lighter;
      transition: $transition-base;
      
      &:hover {
        border-color: $color-primary;
        background: rgba($color-primary, 0.05);
      }
      
      .upload-content {
        @include flex-center;
        flex-direction: column;
        height: 100%;
        
        .upload-icon {
          font-size: 48px;
          color: $text-color-placeholder;
          margin-bottom: $spacing-md;
        }
        
        .upload-text {
          text-align: center;
          
          .upload-title {
            font-size: 16px;
            color: $text-color-regular;
            margin: 0 0 $spacing-xs;
            
            em {
              color: $color-primary;
              font-style: normal;
            }
          }
          
          .upload-hint {
            font-size: 12px;
            color: $text-color-placeholder;
            margin: 0;
          }
        }
      }
    }
  }
  
  .batch-actions {
    margin-top: $spacing-lg;
    padding-top: $spacing-lg;
    border-top: 1px solid $border-color-lighter;
    
    .batch-info {
      display: flex;
      gap: $spacing-lg;
      margin-bottom: $spacing-md;
      font-size: 14px;
      color: $text-color-regular;
    }
    
    .batch-controls {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: $spacing-md;
      
      .batch-input {
        width: 100%;
      }
    }
  }
}

.file-list-section {
  margin-bottom: $spacing-lg;
}

.file-list-card {
  .card-header {
    @include flex-between;
    
    h3 {
      font-size: 16px;
      font-weight: 500;
      color: $text-color-primary;
      margin: 0;
    }
  }
}

.file-list {
  .file-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-md;
    border-radius: $border-radius-base;
    transition: $transition-base;
    
    &:hover {
      background: $bg-color-hover;
    }
    
    &.is-selected {
      background: rgba($color-primary, 0.05);
    }
    
    .file-checkbox {
      flex-shrink: 0;
    }
    
    .file-icon {
      width: 40px;
      height: 40px;
      background: $bg-color-light;
      border-radius: $border-radius-base;
      @include flex-center;
      flex-shrink: 0;
      
      .el-icon {
        font-size: 20px;
        color: $text-color-secondary;
      }
    }
    
    .file-info {
      flex: 1;
      min-width: 0;
      
      .file-name {
        font-size: 14px;
        color: $text-color-primary;
        @include text-ellipsis;
      }
      
      .file-meta {
        display: flex;
        align-items: center;
        gap: $spacing-sm;
        font-size: 12px;
        color: $text-color-secondary;
        margin-top: 4px;
        
        .el-tag {
          margin-left: $spacing-xs;
        }
      }
    }
    
    .file-progress {
      width: 120px;
      flex-shrink: 0;
      
      .success-icon {
        color: $color-success;
        font-size: 20px;
      }
      
      .error-icon {
        color: $color-danger;
        font-size: 20px;
      }
    }
    
    .file-actions {
      flex-shrink: 0;
    }
  }
}

.upload-history-section {
  .history-card {
    .card-header {
      @include flex-between;
      
      h3 {
        font-size: 16px;
        font-weight: 500;
        color: $text-color-primary;
        margin: 0;
      }
    }
  }
  
  .empty-history {
    text-align: center;
    padding: $spacing-xl;
    
    .empty-icon {
      font-size: 48px;
      color: $border-color-light;
      margin-bottom: $spacing-md;
    }
    
    .empty-text {
      font-size: 14px;
      color: $text-color-placeholder;
      margin: 0;
    }
  }
  
  .history-list {
    .history-item {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      padding: $spacing-md;
      border-radius: $border-radius-base;
      transition: $transition-base;
      
      &:hover {
        background: $bg-color-hover;
      }
      
      .history-icon {
        width: 32px;
        height: 32px;
        background: $bg-color-light;
        border-radius: $border-radius-base;
        @include flex-center;
        flex-shrink: 0;
        
        .el-icon {
          font-size: 16px;
          color: $text-color-secondary;
        }
      }
      
      .history-info {
        flex: 1;
        min-width: 0;
        
        .history-name {
          font-size: 14px;
          color: $text-color-primary;
          @include text-ellipsis;
        }
        
        .history-meta {
          font-size: 12px;
          color: $text-color-secondary;
          margin-top: 4px;
        }
      }
      
      .history-status {
        flex-shrink: 0;
      }
      
      .history-actions {
        flex-shrink: 0;
      }
    }
  }
}

.file-preview {
  text-align: center;
  
  .preview-image {
    max-width: 100%;
    max-height: 60vh;
    border-radius: $border-radius-base;
  }
  
  .preview-placeholder {
    padding: $spacing-xl;
    
    .placeholder-icon {
      font-size: 48px;
      color: $border-color-light;
      margin-bottom: $spacing-md;
    }
    
    p {
      font-size: 14px;
      color: $text-color-placeholder;
      margin: 0;
    }
  }
}

// 响应式设计
@include respond-to(lg) {
  .batch-controls {
    grid-template-columns: 1fr !important;
  }
}

@include respond-to(sm) {
  .file-upload-container {
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
  
  .file-item {
    .file-progress {
      width: 80px;
    }
  }
}
</style>
