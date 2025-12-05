<template>
  <div class="agent-tasks-page-wrapper">
    <NavigationSidebar />
    <div class="agent-tasks-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1 class="page-title">
            <i class="fas fa-tasks"></i>
            我的任务
          </h1>
          <p class="page-description">管理和监控您的智能体任务执行情况</p>
        </div>

        <!-- 筛选和操作 -->
        <div class="task-filters">
          <div class="filter-group">
            <label>状态筛选：</label>
            <select v-model="statusFilter" @change="fetchTasks">
              <option value="">全部</option>
              <option value="pending">等待中</option>
              <option value="running">执行中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
              <option value="cancelled">已取消</option>
            </select>
          </div>

          <div class="filter-group">
            <label>智能体：</label>
            <select v-model="agentFilter" @change="fetchTasks">
              <option value="">全部智能体</option>
              <option v-for="agent in agents" :key="agent.id" :value="agent.id">
                {{ agent.display_name }}
              </option>
            </select>
          </div>

          <button class="btn btn-primary" @click="fetchTasks">
            <i class="fas fa-sync"></i>
            刷新
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-container">
        <div class="loading-spinner">
          <i class="fas fa-spinner fa-spin"></i>
          <p>加载任务列表...</p>
        </div>
      </div>

      <!-- 任务列表 -->
      <div v-else class="tasks-container">
        <div v-if="tasks.length === 0" class="empty-state">
          <i class="fas fa-clipboard-list"></i>
          <h3>暂无任务</h3>
          <p>您还没有创建任何智能体任务</p>
          <router-link to="/agents" class="btn btn-primary">
            <i class="fas fa-plus"></i>
            创建任务
          </router-link>
        </div>

        <div v-else class="task-grid">
          <div
            v-for="task in tasks"
            :key="task.id"
            class="task-card"
            @click="viewTaskDetail(task)"
          >
            <!-- 任务头部 -->
            <div class="task-header">
              <div class="task-info">
                <h3 class="task-title">{{ task.title }}</h3>
                <p class="agent-name">
                  <i class="fas fa-robot"></i>
                  {{ task.agent_name }}
                </p>
              </div>

              <div class="task-status">
                <span :class="['status-badge', task.status]">
                  <i :class="getStatusIcon(task.status)"></i>
                  {{ getStatusText(task.status) }}
                </span>
              </div>
            </div>

            <!-- 任务描述 -->
            <div class="task-description">
              <p>{{ task.description || '暂无描述' }}</p>
            </div>

            <!-- 进度条 -->
            <div
              v-if="task.status === 'running' && task.progress"
              class="progress-section"
            >
              <div class="progress-label">
                <span>执行进度</span>
                <span>{{ (task.progress || 0).toFixed(0) }}%</span>
              </div>
              <div class="progress-bar">
                <div
                  class="progress-fill"
                  :style="{ width: `${task.progress || 0}%` }"
                ></div>
              </div>
            </div>

            <!-- 任务统计 -->
            <div class="task-stats">
              <div class="stat-item">
                <i class="fas fa-calendar-plus"></i>
                <span>{{ formatDate(task.created_at) }}</span>
              </div>

              <div v-if="task.started_at" class="stat-item">
                <i class="fas fa-play"></i>
                <span>{{ formatDate(task.started_at) }}</span>
              </div>

              <div v-if="task.completed_at" class="stat-item">
                <i class="fas fa-check"></i>
                <span>{{ formatDate(task.completed_at) }}</span>
              </div>

              <div v-if="task.execution_time" class="stat-item">
                <i class="fas fa-clock"></i>
                <span>{{ formatDuration(task.execution_time) }}</span>
              </div>
            </div>

            <!-- 错误信息 -->
            <div
              v-if="task.status === 'failed' && task.error_message"
              class="error-section"
            >
              <div class="error-header">
                <i class="fas fa-exclamation-triangle"></i>
                <span>执行错误</span>
              </div>
              <p class="error-message">{{ task.error_message }}</p>
            </div>

            <!-- 任务操作 -->
            <div class="task-actions">
              <button
                v-if="task.status === 'completed'"
                class="btn btn-success btn-sm"
                @click.stop="viewResults(task)"
              >
                <i class="fas fa-eye"></i>
                查看结果
              </button>

              <button
                v-if="task.status === 'running'"
                class="btn btn-info btn-sm"
                @click.stop="viewProgress(task)"
              >
                <i class="fas fa-list"></i>
                执行详情
              </button>

              <button
                v-if="['pending', 'running'].includes(task.status)"
                class="btn btn-warning btn-sm"
                @click.stop="cancelTask(task)"
              >
                <i class="fas fa-stop"></i>
                取消
              </button>

              <button
                v-if="task.status === 'failed'"
                class="btn btn-danger btn-sm"
                @click.stop="retryTask(task)"
              >
                <i class="fas fa-redo"></i>
                重试
              </button>

              <button
                class="btn btn-secondary btn-sm"
                @click.stop="deleteTask(task)"
              >
                <i class="fas fa-trash"></i>
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 任务详情对话框 -->
      <TaskDetailModal
        v-if="showDetailModal"
        :task="selectedTask"
        @close="showDetailModal = false"
        @task-updated="handleTaskUpdated"
      />

      <!-- 任务结果对话框 -->
      <TaskResultModal
        v-if="showResultModal"
        :task="selectedTask"
        @close="showResultModal = false"
      />
    </div>
  </div>
</template>

<script setup>
  import NavigationSidebar from '@/components/NavigationSidebar.vue'
  import { ref, onMounted, onUnmounted, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import apiClient from '@/utils/api'

  import TaskDetailModal from '@/components/TaskDetailModal.vue'
  import TaskResultModal from '@/components/TaskResultModal.vue'

  const router = useRouter()

  // 响应式数据
  const tasks = ref([])
  const agents = ref([])
  const loading = ref(true)
  const statusFilter = ref('')
  const agentFilter = ref('')
  const selectedTask = ref(null)
  const showDetailModal = ref(false)
  const showResultModal = ref(false)

  // 方法
  const fetchTasks = async () => {
    try {
      loading.value = true

      const params = new URLSearchParams()
      if (statusFilter.value) params.append('status', statusFilter.value)
      if (agentFilter.value) params.append('agent_id', agentFilter.value)

      const response = await apiClient.get(
        `/smart-agent/tasks/?${params.toString()}`
      )
      tasks.value = response.data.results || response.data || []
      loading.value = false
    } catch (error) {
      console.error('获取任务列表失败:', error)
      // API失败时使用mock数据作为fallback
      tasks.value = [
        {
          id: 'mock-1',
          title: '示例任务 (API连接失败)',
          description: '当前显示的是示例数据，因为无法连接到后端API',
          status: 'pending',
          agent_name: '示例智能体',
          created_at: new Date().toISOString(),
          progress: 0,
        },
      ]
      loading.value = false
    }
  }

  const fetchAgents = async () => {
    try {
      const response = await apiClient.get('/smart-agent/agents/')
      agents.value = response.data.results || response.data || []
    } catch (error) {
      console.error('获取智能体列表失败:', error)
      // API失败时使用mock数据作为fallback
      agents.value = [
        { id: 'mock-1', display_name: '示例智能体1 (API连接失败)' },
        { id: 'mock-2', display_name: '示例智能体2 (API连接失败)' },
      ]
    }
  }

  const viewTaskDetail = (task) => {
    selectedTask.value = task
    showDetailModal.value = true
  }

  const viewResults = (task) => {
    selectedTask.value = task
    showResultModal.value = true
  }

  const viewProgress = (task) => {
    selectedTask.value = task
    showDetailModal.value = true
  }

  const cancelTask = async (task) => {
    if (!confirm('确定要取消这个任务吗？')) return

    try {
      await apiClient.post(`/smart-agent/tasks/${task.id}/cancel/`)
      await fetchTasks() // 刷新列表
    } catch (error) {
      console.error('取消任务失败:', error)
    }
  }

  const retryTask = async (task) => {
    if (!confirm('确定要重试这个任务吗？')) return

    try {
      // 创建新任务（复制原任务参数）
      const payload = {
        title: `重试 - ${task.title}`,
        description: task.description,
        input_data: task.input_data,
      }

      const response = await apiClient.post(
        `/smart-agent/agents/${task.agent}/execute/`,
        payload
      )
      await fetchTasks() // 刷新列表
    } catch (error) {
      console.error('重试任务失败:', error)
    }
  }

  const deleteTask = async (task) => {
    if (!confirm('确定要删除这个任务吗？此操作无法撤销。')) return

    try {
      await apiClient.delete(`/smart-agent/tasks/${task.id}/`)
      await fetchTasks() // 刷新列表
    } catch (error) {
      console.error('删除任务失败:', error)
    }
  }

  const handleTaskUpdated = () => {
    fetchTasks() // 刷新任务列表
  }

  // 辅助函数
  const getStatusIcon = (status) => {
    const iconMap = {
      pending: 'fas fa-clock',
      running: 'fas fa-spinner fa-spin',
      completed: 'fas fa-check-circle',
      failed: 'fas fa-times-circle',
      cancelled: 'fas fa-ban',
    }
    return iconMap[status] || 'fas fa-question-circle'
  }

  const getStatusText = (status) => {
    const statusMap = {
      pending: '等待中',
      running: '执行中',
      completed: '已完成',
      failed: '失败',
      cancelled: '已取消',
    }
    return statusMap[status] || status
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    const date = new Date(dateString)
    const now = new Date()
    const diffTime = now - date
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) {
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
      })
    } else if (diffDays < 7) {
      return `${diffDays}天前`
    } else {
      return date.toLocaleDateString('zh-CN', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      })
    }
  }

  const formatDuration = (seconds) => {
    if (!seconds || seconds === 0) return '-'
    if (seconds < 60) return `${seconds.toFixed(1)}s`
    if (seconds < 3600)
      return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
    return `${Math.floor(seconds / 3600)}h ${Math.floor(
      (seconds % 3600) / 60
    )}m`
  }

  // 生命周期
  let refreshInterval = null

  onMounted(async () => {
    try {
      await Promise.all([fetchTasks(), fetchAgents()])

      // 设置定时刷新（对于运行中的任务）
      refreshInterval = setInterval(() => {
        const runningTasks = tasks.value.filter(
          (task) => task.status === 'running'
        )
        if (runningTasks.length > 0) {
          fetchTasks()
        }
      }, 10000) // 每10秒刷新一次，避免过于频繁
    } catch (error) {
      console.error('AgentTasks 初始化失败:', error)
    }
  })

  // 组件销毁时清理定时器
  onUnmounted(() => {
    if (refreshInterval) {
      clearInterval(refreshInterval)
      refreshInterval = null
    }
  })
</script>

<style scoped>
  .agent-tasks-page-wrapper {
    display: flex;
    height: 100vh;
  }

  .agent-tasks-container {
    flex: 1;
    overflow-y: auto;
    min-height: 100vh;
    /* background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); */
    padding: 2rem;
  }

  .page-header {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  }

  .header-content {
    text-align: center;
    margin-bottom: 2rem;
  }

  .page-title {
    font-size: 2.5rem;
    font-weight: 700;
    color: #2c3e50;
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
  }

  .page-title i {
    color: #667eea;
  }

  .page-description {
    font-size: 1.1rem;
    color: #7f8c8d;
    margin: 0;
  }

  .task-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: center;
    justify-content: center;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .filter-group label {
    font-weight: 600;
    color: #2c3e50;
  }

  .filter-group select {
    padding: 0.5rem 1rem;
    border: 2px solid #ecf0f1;
    border-radius: 10px;
    outline: none;
    transition: border-color 0.3s ease;
  }

  .filter-group select:focus {
    border-color: #667eea;
  }

  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
  }

  .loading-spinner {
    text-align: center;
    color: white;
  }

  .loading-spinner i {
    font-size: 3rem;
    margin-bottom: 1rem;
  }

  .empty-state {
    text-align: center;
    color: white;
    padding: 4rem 2rem;
  }

  .empty-state i {
    font-size: 4rem;
    margin-bottom: 1rem;
    opacity: 0.7;
  }

  .empty-state h3 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }

  .task-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 2rem;
  }

  .task-card {
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
    border: 1px solid rgba(255, 255, 255, 0.18);
  }

  .task-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 40px rgba(31, 38, 135, 0.5);
  }

  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 1rem;
  }

  .task-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #2c3e50;
    margin: 0 0 0.5rem 0;
  }

  .agent-name {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #7f8c8d;
    font-size: 0.9rem;
    margin: 0;
  }

  .status-badge {
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .status-badge.pending {
    background: #fff3cd;
    color: #856404;
  }

  .status-badge.running {
    background: #d1ecf1;
    color: #0c5460;
  }

  .status-badge.completed {
    background: #d4edda;
    color: #155724;
  }

  .status-badge.failed {
    background: #f8d7da;
    color: #721c24;
  }

  .status-badge.cancelled {
    background: #e2e3e5;
    color: #383d41;
  }

  .task-description {
    margin-bottom: 1rem;
  }

  .task-description p {
    color: #7f8c8d;
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .progress-section {
    margin-bottom: 1rem;
  }

  .progress-label {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.9rem;
    color: #2c3e50;
  }

  .progress-bar {
    height: 8px;
    background: #ecf0f1;
    border-radius: 4px;
    overflow: hidden;
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, #667eea, #764ba2);
    transition: width 0.5s ease;
  }

  .task-stats {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-bottom: 1rem;
  }

  .stat-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #7f8c8d;
    font-size: 0.8rem;
  }

  .stat-item i {
    color: #95a5a6;
    width: 12px;
  }

  .error-section {
    background: #f8d7da;
    border: 1px solid #f5c6cb;
    border-radius: 10px;
    padding: 1rem;
    margin-bottom: 1rem;
  }

  .error-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: #721c24;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .error-message {
    color: #721c24;
    font-size: 0.9rem;
    margin: 0;
    line-height: 1.4;
  }

  .task-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.3s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    text-decoration: none;
    font-size: 0.8rem;
  }

  .btn-sm {
    padding: 0.4rem 0.8rem;
    font-size: 0.75rem;
  }

  .btn-primary {
    background: #667eea;
    color: white;
  }

  .btn-success {
    background: #27ae60;
    color: white;
  }

  .btn-info {
    background: #3498db;
    color: white;
  }

  .btn-warning {
    background: #f39c12;
    color: white;
  }

  .btn-danger {
    background: #e74c3c;
    color: white;
  }

  .btn-secondary {
    background: #95a5a6;
    color: white;
  }

  .btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .agent-tasks-container {
      padding: 1rem;
    }

    .task-grid {
      grid-template-columns: 1fr;
    }

    .task-header {
      flex-direction: column;
      align-items: flex-start;
      gap: 1rem;
    }

    .task-stats {
      grid-template-columns: 1fr;
    }

    .task-actions {
      justify-content: center;
    }
  }
</style>
