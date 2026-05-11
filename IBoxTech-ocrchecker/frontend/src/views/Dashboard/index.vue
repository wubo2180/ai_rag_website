<template>
  <div class="dashboard-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">仪表盘</h1>
        <p class="page-subtitle">欢迎回来，{{ authStore.displayName }}</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/upload')">
          <el-icon><Upload /></el-icon>
          上传文件
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon total-files">
          <el-icon><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ dashboardData.totalFiles }}</div>
          <div class="stat-label">总文件数</div>
        </div>
        <div class="stat-trend" v-if="trends.totalFiles !== 0">
          <el-icon :class="['trend-icon', trends.totalFiles > 0 ? 'positive' : 'negative']">
            <CaretTop v-if="trends.totalFiles > 0" />
            <CaretBottom v-else />
          </el-icon>
          <span class="trend-text">{{ trends.totalFiles > 0 ? '+' : '' }}{{ trends.totalFiles }}%</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon pending-files">
          <el-icon><Clock /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ dashboardData.pendingFiles }}</div>
          <div class="stat-label">未处理文件数</div>
        </div>
        <div class="stat-trend" v-if="trends.pendingFiles !== 0">
          <el-icon :class="['trend-icon', trends.pendingFiles < 0 ? 'positive' : 'negative']">
            <CaretTop v-if="trends.pendingFiles < 0" />
            <CaretBottom v-else />
          </el-icon>
          <span class="trend-text">{{ trends.pendingFiles > 0 ? '+' : '' }}{{ trends.pendingFiles }}%</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon reviewed-files">
          <el-icon><Select /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ dashboardData.reviewedFiles }}</div>
          <div class="stat-label">已核对文件数</div>
        </div>
        <div class="stat-trend" v-if="trends.reviewedFiles !== 0">
          <el-icon :class="['trend-icon', trends.reviewedFiles > 0 ? 'positive' : 'negative']">
            <CaretTop v-if="trends.reviewedFiles > 0" />
            <CaretBottom v-else />
          </el-icon>
          <span class="trend-text">{{ trends.reviewedFiles > 0 ? '+' : '' }}{{ trends.reviewedFiles }}%</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon file-types">
          <el-icon><FolderOpened /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-number">{{ dashboardData.fileTypes }}</div>
          <div class="stat-label">文件类型数</div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="dashboard-content">
      <div class="content-left">
        <!-- 最近文件 -->
        <div class="dashboard-card">
          <div class="card-header">
            <h3 class="card-title">最近上传</h3>
            <el-link type="primary" @click="$router.push('/files')">查看全部</el-link>
          </div>
          <div class="card-content">
            <div v-if="loading.recentFiles" class="loading-container">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else-if="recentFiles.length === 0" class="empty-state">
              <el-icon class="empty-icon"><Document /></el-icon>
              <p class="empty-text">暂无文件</p>
            </div>
            <div v-else class="file-list">
              <div
                v-for="file in recentFiles"
                :key="file.id"
                class="file-item"
                @click="viewFile(file)"
              >
                <div class="file-icon">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="file-info">
                  <div class="file-name">{{ file.filename }}</div>
                  <div class="file-meta">
                    {{ formatFileSize(file.file_size) }} • {{ formatTime(file.created_at) }}
                  </div>
                </div>
                <div class="file-status">
                  <el-tag
                    :type="getStatusType(file.ocr_status)"
                    size="small"
                  >
                    {{ getStatusText(file.ocr_status) }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 处理队列 -->
        <div class="dashboard-card">
          <div class="card-header">
            <h3 class="card-title">处理队列</h3>
            <el-badge :value="processingQueue.length" :hidden="processingQueue.length === 0">
              <el-icon><Clock /></el-icon>
            </el-badge>
          </div>
          <div class="card-content">
            <div v-if="loading.processingQueue" class="loading-container">
              <el-skeleton :rows="2" animated />
            </div>
            <div v-else-if="processingQueue.length === 0" class="empty-state">
              <el-icon class="empty-icon"><CircleCheckFilled /></el-icon>
              <p class="empty-text">暂无处理任务</p>
            </div>
            <div v-else class="queue-list">
              <div
                v-for="item in processingQueue"
                :key="item.id"
                class="queue-item"
                @click="viewFile(item)"
              >
                <div class="file-icon">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="queue-info">
                  <div class="queue-name">{{ item.filename }}</div>
                  <div class="queue-meta">
                    {{ formatFileSize(item.file_size) }} • {{ formatTime(item.created_at) }}
                  </div>
                </div>
                <div class="queue-status">
                  <el-tag
                    type="warning"
                    size="small"
                  >
                    {{ item.status_text }}
                  </el-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="content-right">
        <!-- 系统状态 -->
        <div class="dashboard-card">
          <div class="card-header">
            <h3 class="card-title">系统状态</h3>
            <el-tag :type="systemStatus.type" size="small">
              {{ systemStatus.text }}
            </el-tag>
          </div>
          <div class="card-content">
            <div class="system-metrics">
              <div class="metric-item">
                <div class="metric-label">CPU使用率</div>
                <div class="metric-value">
                  <el-progress
                    :percentage="systemStatus.cpu"
                    :color="getProgressColor(systemStatus.cpu)"
                    :stroke-width="8"
                  />
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-label">内存使用率</div>
                <div class="metric-value">
                  <el-progress
                    :percentage="systemStatus.memory"
                    :color="getProgressColor(systemStatus.memory)"
                    :stroke-width="8"
                  />
                </div>
              </div>
              <div class="metric-item">
                <div class="metric-label">存储空间</div>
                <div class="metric-value">
                  <el-progress
                    :percentage="systemStatus.storage"
                    :color="getProgressColor(systemStatus.storage)"
                    :stroke-width="8"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>


        <!-- 活动日志 -->
        <div class="dashboard-card">
          <div class="card-header">
            <h3 class="card-title">最近活动</h3>
            <el-link type="primary" @click="$router.push('/logs')">查看全部</el-link>
          </div>
          <div class="card-content">
            <div v-if="loading.activities" class="loading-container">
              <el-skeleton :rows="3" animated />
            </div>
            <div v-else class="activity-list">
              <div
                v-for="activity in recentActivities"
                :key="activity.id"
                class="activity-item"
              >
                <div class="activity-icon">
                  <el-icon>
                    <component :is="getActivityIcon(activity.type)" />
                  </el-icon>
                </div>
                <div class="activity-content">
                  <div class="activity-text">{{ activity.description }}</div>
                  <div class="activity-time">{{ formatTime(activity.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { filesApi } from '@/api/files'
import { dashboardApi } from '@/api/dashboard'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)

const authStore = useAuthStore()

// 响应式数据
const loading = reactive({
  recentFiles: false,
  processingQueue: false,
  activities: false,
  statistics: false,
  systemStatus: false
})

const dashboardData = reactive({
  totalFiles: 0,
  pendingFiles: 0,
  reviewedFiles: 0,
  fileTypes: 0
})

const trends = reactive({
  totalFiles: 0,
  pendingFiles: 0,
  reviewedFiles: 0
})

const recentFiles = ref([])
const processingQueue = ref([])
const recentActivities = ref([])

const systemStatus = reactive({
  type: 'info',
  text: '加载中...',
  cpu: 0,
  memory: 0,
  storage: 0
})

const quickActions = ref([
  {
    name: 'upload',
    label: '上传文件',
    type: 'primary',
    icon: 'Upload'
  },
  {
    name: 'batch-process',
    label: '批量处理',
    type: 'success',
    icon: 'Operation'
  },
  {
    name: 'export-data',
    label: '导出数据',
    type: 'info',
    icon: 'Download'
  },
  {
    name: 'settings',
    label: '系统设置',
    type: 'warning',
    icon: 'Setting'
  }
])

// 方法
const fetchStatistics = async () => {
  try {
    loading.statistics = true
    
    // 获取文件统计
    const filesResponse = await filesApi.getFiles({ page: 1, per_page: 1 })
    if (filesResponse.data.success) {
      dashboardData.totalFiles = filesResponse.data.data.total
    }
    
    // 获取未处理文件数（pending状态）
    const pendingResponse = await filesApi.getFiles({ status: 'pending', page: 1, per_page: 1 })
    if (pendingResponse.data.success) {
      dashboardData.pendingFiles = pendingResponse.data.data.total || 0
    }
    
    // 获取已核对文件数（review_status为completed）
    const reviewedResponse = await filesApi.getFiles({ review_status: 'completed', page: 1, per_page: 1 })
    if (reviewedResponse.data.success) {
      dashboardData.reviewedFiles = reviewedResponse.data.data.total || 0
    }
    
    // 获取文件类型数
    const { fileTypeConfigsApi } = await import('@/api/file-type-configs')
    const typesResponse = await fileTypeConfigsApi.getAll()
    if (typesResponse.data.success) {
      dashboardData.fileTypes = typesResponse.data.data.filter(t => t.is_active).length
    }
    
    // 计算趋势（简化处理）
    trends.totalFiles = 0
    trends.pendingFiles = 0
    trends.reviewedFiles = 0
    
  } catch (error) {
    console.error('获取统计数据失败:', error)
  } finally {
    loading.statistics = false
  }
}

const fetchSystemStatus = async () => {
  try {
    loading.systemStatus = true
    const response = await dashboardApi.getSystemStatus()
    if (response.data.success) {
      const data = response.data.data
      systemStatus.type = data.type
      systemStatus.text = data.text
      systemStatus.cpu = data.cpu
      systemStatus.memory = data.memory
      systemStatus.storage = data.storage
    }
  } catch (error) {
    console.error('获取系统状态失败:', error)
  } finally {
    loading.systemStatus = false
  }
}

const refreshData = async () => {
  await Promise.all([
    fetchStatistics(),
    fetchSystemStatus(),
    fetchRecentFiles(),
    fetchProcessingQueue(),
    fetchRecentActivities()
  ])
}

const fetchRecentFiles = async () => {
  try {
    loading.recentFiles = true
    const response = await filesApi.getFiles({ page: 1, per_page: 5 })
    if (response.data.success) {
      recentFiles.value = response.data.data.files
    }
  } catch (error) {
    console.error('获取最近文件失败:', error)
  } finally {
    loading.recentFiles = false
  }
}

const fetchProcessingQueue = async () => {
  try {
    loading.processingQueue = true
    const response = await filesApi.getFiles({ 
      page: 1, 
      per_page: 10,
      status: 'processing'
    })
    if (response.data.success) {
      // 直接使用真实数据，不添加随机进度
      processingQueue.value = response.data.data.files.map(file => ({
        ...file,
        status_text: file.ocr_status === 'processing' ? '正在识别中...' : '待处理'
      }))
    }
  } catch (error) {
    console.error('获取处理队列失败:', error)
  } finally {
    loading.processingQueue = false
  }
}

const fetchRecentActivities = async () => {
  try {
    loading.activities = true
    // 获取最近的文件操作记录（使用真实文件数据）
    const response = await filesApi.getFiles({ 
      page: 1, 
      per_page: 10  // 获取最近10个文件
    })
    
    if (response.data.success) {
      const files = response.data.data.files
      
      // 将文件操作转换为活动日志
      recentActivities.value = files.map((file, index) => {
        let type = 'upload'
        let description = `上传了文件 ${file.filename}`
        
        // 根据文件状态判断活动类型
        if (file.ocr_status === 'completed') {
          type = 'process'
          description = `完成了文件 ${file.filename} 的识别`
        } else if (file.ocr_status === 'processing') {
          type = 'process'
          description = `正在处理文件 ${file.filename}`
        } else if (file.review_status === 'completed') {
          type = 'review'
          description = `完成了文件 ${file.filename} 的核对`
        } else if (file.review_status === 'in_progress') {
          type = 'review'
          description = `正在核对文件 ${file.filename}`
        }
        
        return {
          id: file.id,
          type,
          description,
          created_at: file.updated_at || file.created_at
        }
      }).slice(0, 5)  // 只显示最近5条
    }
  } catch (error) {
    console.error('获取活动日志失败:', error)
    recentActivities.value = []
  } finally {
    loading.activities = false
  }
}

const viewFile = (file) => {
  // 跳转到文件详情页面
  window.open(`/review/${file.id}`, '_blank')
}

const handleQuickAction = (action) => {
  switch (action.name) {
    case 'upload':
      $router.push('/upload')
      break
    case 'batch-process':
      // 批量处理逻辑
      break
    case 'export-data':
      // 导出数据逻辑
      break
    case 'settings':
      // 系统设置逻辑
      break
  }
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

const getProgressColor = (percentage) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

const getActivityIcon = (type) => {
  const iconMap = {
    upload: 'Upload',
    process: 'Operation',
    review: 'View',
    download: 'Download'
  }
  return iconMap[type] || 'InfoFilled'
}

const formatTime = (time) => {
  return dayjs(time).fromNow()
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

// 生命周期
onMounted(() => {
  refreshData()
  
  // 定时刷新数据
  const timer = setInterval(() => {
    fetchProcessingQueue()
  }, 30000) // 30秒刷新一次处理队列
  
  onUnmounted(() => {
    clearInterval(timer)
  })
})
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: $spacing-lg;
  background: $bg-color-page;
  min-height: calc(100vh - 60px);
  max-width: 100%;
  overflow-x: hidden;
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

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: $spacing-lg;
  margin-bottom: $spacing-lg;
}

.stat-card {
  background: $bg-color-white;
  border-radius: $border-radius-large;
  padding: $spacing-lg;
  box-shadow: $box-shadow-base;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  
  .stat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    @include flex-center;
    
    .el-icon {
      font-size: 24px;
      color: white;
    }
    
    &.total-files {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    &.pending-files {
      background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    &.reviewed-files {
      background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    }
    
    &.file-types {
      background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
    }
  }
  
  .stat-content {
    flex: 1;
    
    .stat-number {
      font-size: 24px;
      font-weight: 600;
      color: $text-color-primary;
      line-height: 1.2;
    }
    
    .stat-label {
      font-size: 12px;
      color: $text-color-secondary;
      margin-top: 4px;
    }
  }
  
  .stat-trend {
    display: flex;
    align-items: center;
    gap: 4px;
    
    .trend-icon {
      font-size: 12px;
      
      &.positive {
        color: $color-success;
      }
      
      &.negative {
        color: $color-danger;
      }
    }
    
    .trend-text {
      font-size: 12px;
      font-weight: 500;
    }
  }
}

.dashboard-content {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(0, 1fr);
  gap: $spacing-lg;
  width: 100%;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
}

.content-left,
.content-right {
  min-width: 0;  // 允许grid子元素缩小
}

.dashboard-card {
  background: $bg-color-white;
  border-radius: $border-radius-large;
  box-shadow: $box-shadow-base;
  margin-bottom: $spacing-lg;
  overflow: hidden;
  min-width: 0;  // 允许卡片缩小
  width: 100%;  // 确保卡片占满容器
  
  .card-header {
    @include flex-between;
    padding: $spacing-lg;
    border-bottom: 1px solid $border-color-lighter;
    
    .card-title {
      font-size: 16px;
      font-weight: 500;
      color: $text-color-primary;
      margin: 0;
    }
  }
  
  .card-content {
    padding: $spacing-lg;
    overflow-x: auto;  // 如果内容过宽，显示横向滚动条
  }
}

.file-list {
  width: 100%;  // 确保列表占满容器宽度
  
  .file-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-sm;
    border-radius: $border-radius-base;
    cursor: pointer;
    transition: $transition-base;
    width: 100%;  // 确保项目占满列表宽度
    box-sizing: border-box;  // 包含padding在宽度内
    
    &:hover {
      background: $bg-color-hover;
    }
    
    .file-icon {
      width: 40px;
      height: 40px;
      background: $bg-color-light;
      border-radius: $border-radius-base;
      flex-shrink: 0;  // 防止图标缩小
      @include flex-center;
      
      .el-icon {
        font-size: 18px;
        color: $text-color-secondary;
      }
    }
    
    .file-info {
      flex: 1;
      min-width: 0;  // 允许flex子元素缩小
      overflow: hidden;  // 隐藏溢出内容
      
      .file-name {
        font-size: 14px;
        color: $text-color-primary;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        width: 100%;  // 确保宽度为100%
      }
      
      .file-meta {
        font-size: 12px;
        color: $text-color-secondary;
        margin-top: 4px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
    }
    
    .file-status {
      flex-shrink: 0;  // 防止状态标签缩小
      margin-left: $spacing-sm;
    }
  }
}

.queue-list {
  .queue-item {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    padding: $spacing-sm;
    border-radius: $border-radius-base;
    cursor: pointer;
    transition: $transition-base;
    margin-bottom: $spacing-sm;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    &:hover {
      background: $bg-color-hover;
    }
    
    .file-icon {
      width: 32px;
      height: 32px;
      background: $bg-color-light;
      border-radius: $border-radius-base;
      flex-shrink: 0;
      @include flex-center;
      
      .el-icon {
        font-size: 16px;
        color: $text-color-secondary;
      }
    }
    
    .queue-info {
      flex: 1;
      min-width: 0;
      overflow: hidden;
      
      .queue-name {
        font-size: 12px;
        color: $text-color-primary;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      
      .queue-meta {
        font-size: 11px;
        color: $text-color-secondary;
        margin-top: 2px;
      }
    }
    
    .queue-status {
      flex-shrink: 0;
    }
  }
}

.system-metrics {
  .metric-item {
    margin-bottom: $spacing-md;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .metric-label {
      font-size: 12px;
      color: $text-color-secondary;
      margin-bottom: $spacing-xs;
    }
    
    .metric-value {
      .el-progress {
        :deep(.el-progress__text) {
          font-size: 12px;
        }
      }
    }
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $spacing-sm;
  
  .action-btn {
    width: 100%;
    height: 40px;
    justify-content: center;
    
    .el-icon {
      margin-right: $spacing-xs;
    }
  }
}

.activity-list {
  .activity-item {
    display: flex;
    align-items: flex-start;
    gap: $spacing-md;
    margin-bottom: $spacing-md;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .activity-icon {
      width: 32px;
      height: 32px;
      background: $bg-color-light;
      border-radius: 50%;
      @include flex-center;
      flex-shrink: 0;
      
      .el-icon {
        font-size: 14px;
        color: $text-color-secondary;
      }
    }
    
    .activity-content {
      flex: 1;
      
      .activity-text {
        font-size: 13px;
        color: $text-color-primary;
        line-height: 1.4;
      }
      
      .activity-time {
        font-size: 11px;
        color: $text-color-placeholder;
        margin-top: 4px;
      }
    }
  }
}

.empty-state {
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

.loading-container {
  padding: $spacing-md;
}
</style>
