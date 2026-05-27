<template>
  <div class="agent-detail-container">
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <p>加载智能体详情...</p>
      </div>
    </div>

    <div v-else-if="agent" class="agent-detail">
      <!-- 返回按钮 -->
      <div class="back-navigation">
        <button @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i>
          返回智能体列表
        </button>
      </div>

      <!-- 智能体头部信息 -->
      <div class="agent-header">
        <div class="agent-avatar-large">
          <i 
            :class="agent.icon || 'fas fa-robot'" 
            :style="{ color: getThemeColor(agent.color_theme) }"
          ></i>
        </div>
        
        <div class="agent-info">
          <div class="agent-title">
            <h1>{{ agent.display_name }}</h1>
            <span :class="['status-badge', agent.status]">
              {{ getStatusText(agent.status) }}
            </span>
          </div>
          
          <p class="agent-description">{{ agent.description }}</p>
          
          <div class="agent-meta">
            <div class="meta-item">
              <i class="fas fa-tag"></i>
              <span>{{ getCategoryText(agent.category) }}</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-star"></i>
              <span>{{ agent.popularity_score.toFixed(1) }} 分</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-calendar"></i>
              <span>{{ formatDate(agent.created_at) }} 创建</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-code-branch"></i>
              <span>版本 {{ agent.version }}</span>
            </div>
          </div>
        </div>

        <div class="agent-actions">
          <button 
            class="btn btn-primary btn-large"
            @click="executeAgent"
          >
            <i class="fas fa-play"></i>
            执行任务
          </button>
          <button 
            class="btn btn-secondary"
            @click="toggleFavorite"
          >
            <i :class="isFavorite ? 'fas fa-heart' : 'far fa-heart'"></i>
            {{ isFavorite ? '已收藏' : '收藏' }}
          </button>
        </div>
      </div>

      <!-- 详细信息标签页 -->
      <div class="detail-tabs">
        <nav class="tab-nav">
          <button 
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab-btn', { active: activeTab === tab.key }]"
            @click="activeTab = tab.key"
          >
            <i :class="tab.icon"></i>
            {{ tab.label }}
          </button>
        </nav>

        <div class="tab-content">
          <!-- 基本信息 -->
          <div v-show="activeTab === 'basic'" class="tab-panel">
            <div class="info-grid">
              <div class="info-card">
                <h3>
                  <i class="fas fa-cogs"></i>
                  核心能力
                </h3>
                <div class="capabilities-list">
                  <div 
                    v-for="capability in agent.capabilities"
                    :key="capability"
                    class="capability-item"
                  >
                    <i class="fas fa-check-circle"></i>
                    <span>{{ capability }}</span>
                  </div>
                </div>
              </div>

              <div class="info-card">
                <h3>
                  <i class="fas fa-download"></i>
                  支持的输入类型
                </h3>
                <div class="input-types">
                  <span 
                    v-for="inputType in agent.supported_inputs"
                    :key="inputType"
                    class="type-tag input-tag"
                  >
                    {{ inputType }}
                  </span>
                </div>
              </div>

              <div class="info-card">
                <h3>
                  <i class="fas fa-upload"></i>
                  输出结果类型
                </h3>
                <div class="output-types">
                  <span 
                    v-for="outputType in agent.supported_outputs"
                    :key="outputType"
                    class="type-tag output-tag"
                  >
                    {{ outputType }}
                  </span>
                </div>
              </div>

              <div class="info-card">
                <h3>
                  <i class="fas fa-brain"></i>
                  AI 模型信息
                </h3>
                <div class="model-info">
                  <div class="model-item">
                    <label>模型类型：</label>
                    <span>{{ agent.ai_model }}</span>
                  </div>
                  <div class="model-item">
                    <label>创建者：</label>
                    <span>{{ agent.created_by_name || '系统' }}</span>
                  </div>
                  <div class="model-item">
                    <label>是否公开：</label>
                    <span>{{ agent.is_public ? '是' : '否' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 统计数据 -->
          <div v-show="activeTab === 'statistics'" class="tab-panel">
            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-tasks"></i>
                </div>
                <div class="stat-info">
                  <h4>{{ statistics.total_tasks || 0 }}</h4>
                  <p>总任务数</p>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-percentage"></i>
                </div>
                <div class="stat-info">
                  <h4>{{ ((statistics.success_rate || 0) * 100).toFixed(1) }}%</h4>
                  <p>成功率</p>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-clock"></i>
                </div>
                <div class="stat-info">
                  <h4>{{ formatExecutionTime(statistics.average_execution_time) }}</h4>
                  <p>平均执行时间</p>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-heart"></i>
                </div>
                <div class="stat-info">
                  <h4>{{ (statistics.recent_feedback_avg || 0).toFixed(1) }}</h4>
                  <p>用户评分</p>
                </div>
              </div>
            </div>

            <!-- 任务状态分布图表 -->
            <div class="chart-section">
              <h3>任务状态分布</h3>
              <div class="status-chart">
                <div 
                  v-for="status in statusDistribution"
                  :key="status.status"
                  class="status-item"
                >
                  <div class="status-bar">
                    <div 
                      class="status-fill"
                      :style="{ 
                        width: `${(status.count / maxStatusCount) * 100}%`,
                        backgroundColor: getStatusColor(status.status)
                      }"
                    ></div>
                  </div>
                  <div class="status-info">
                    <span class="status-name">{{ getStatusText(status.status) }}</span>
                    <span class="status-count">{{ status.count }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 使用指南 -->
          <div v-show="activeTab === 'guide'" class="tab-panel">
            <div class="guide-content">
              <div class="guide-section">
                <h3>
                  <i class="fas fa-play-circle"></i>
                  如何使用
                </h3>
                <ol class="guide-steps">
                  <li>点击"执行任务"按钮开始</li>
                  <li>填写任务标题和描述</li>
                  <li>根据智能体类型提供相应的输入数据</li>
                  <li>等待智能体处理并获得结果</li>
                </ol>
              </div>

              <div class="guide-section">
                <h3>
                  <i class="fas fa-lightbulb"></i>
                  使用建议
                </h3>
                <ul class="guide-tips">
                  <li>请提供准确详细的输入信息以获得更好的结果</li>
                  <li>对于大型数据文件，建议先进行预处理</li>
                  <li>复杂任务可能需要较长的执行时间，请耐心等待</li>
                  <li>如遇到问题，可查看任务执行日志进行排查</li>
                </ul>
              </div>

              <div class="guide-section">
                <h3>
                  <i class="fas fa-exclamation-triangle"></i>
                  注意事项
                </h3>
                <ul class="guide-warnings">
                  <li>确保上传的文件格式符合要求</li>
                  <li>敏感数据请在本地处理后再上传</li>
                  <li>大文件上传可能需要较长时间</li>
                  <li>建议在网络状况良好时使用</li>
                </ul>
              </div>

              <div v-if="agent.prompt_template" class="guide-section">
                <h3>
                  <i class="fas fa-code"></i>
                  提示词模板
                </h3>
                <div class="prompt-template">
                  <pre>{{ agent.prompt_template }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- 任务历史 -->
          <div v-show="activeTab === 'history'" class="tab-panel">
            <div class="task-history">
              <div class="history-header">
                <h3>最近任务</h3>
                <button 
                  class="btn btn-secondary"
                  @click="refreshTaskHistory"
                >
                  <i class="fas fa-sync"></i>
                  刷新
                </button>
              </div>

              <div v-if="taskHistory.length === 0" class="empty-history">
                <i class="fas fa-history"></i>
                <p>暂无任务历史</p>
              </div>

              <div v-else class="task-list">
                <div 
                  v-for="task in taskHistory"
                  :key="task.id"
                  class="task-item"
                  @click="viewTaskDetail(task)"
                >
                  <div class="task-info">
                    <h4>{{ task.title }}</h4>
                    <p>{{ task.description || '无描述' }}</p>
                    <div class="task-meta">
                      <span>{{ formatDate(task.created_at) }}</span>
                      <span>{{ formatExecutionTime(task.execution_time) }}</span>
                    </div>
                  </div>
                  <div class="task-status">
                    <span :class="['task-status-badge', task.status]">
                      {{ getStatusText(task.status) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 任务执行对话框 -->
    <TaskExecutionModal 
      v-if="showTaskModal"
      :agent="agent"
      @close="showTaskModal = false"
      @task-created="handleTaskCreated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import apiClient from '@/utils/api'
import TaskExecutionModal from '@/components/TaskExecutionModal.vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const agent = ref(null)
const loading = ref(true)
const activeTab = ref('basic')
const statistics = ref({})
const taskHistory = ref([])
const showTaskModal = ref(false)
const isFavorite = ref(false)

// 标签页配置
const tabs = [
  { key: 'basic', label: '基本信息', icon: 'fas fa-info-circle' },
  { key: 'statistics', label: '使用统计', icon: 'fas fa-chart-bar' },
  { key: 'guide', label: '使用指南', icon: 'fas fa-book' },
  { key: 'history', label: '任务历史', icon: 'fas fa-history' }
]

// 计算属性
const statusDistribution = computed(() => {
  return statistics.value.status_distribution || []
})

const maxStatusCount = computed(() => {
  const counts = statusDistribution.value.map(item => item.count)
  return Math.max(...counts, 1)
})

// 方法
const fetchAgentDetail = async () => {
  try {
    loading.value = true
    const agentId = route.params.id
    
    // 获取智能体详情
    const agentResponse = await apiClient.get(`/smart-agent/agents/${agentId}/`)
    agent.value = agentResponse.data
    
    // 获取统计数据
    const statsResponse = await apiClient.get(`/smart-agent/agents/${agentId}/statistics/`)
    statistics.value = statsResponse.data
    
    // 获取任务历史
    await fetchTaskHistory()
    
  } catch (error) {
    console.error('获取智能体详情失败:', error)
    // 这里可以添加错误处理
  } finally {
    loading.value = false
  }
}

const fetchTaskHistory = async () => {
  try {
    const agentId = route.params.id
    const response = await apiClient.get(`/smart-agent/tasks/?agent_id=${agentId}`)
    taskHistory.value = response.data.results || response.data
  } catch (error) {
    console.error('获取任务历史失败:', error)
  }
}

const refreshTaskHistory = () => {
  fetchTaskHistory()
}

const executeAgent = () => {
  showTaskModal.value = true
}

const handleTaskCreated = (task) => {
  console.log('任务已创建:', task)
  router.push({ name: 'agent-tasks' })
}

const toggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  // 这里可以添加收藏/取消收藏的API调用
}

const viewTaskDetail = (task) => {
  router.push({ name: 'task-detail', params: { id: task.id } })
}

const goBack = () => {
  router.push({ name: 'smart-agents' })
}

// 辅助函数
const getThemeColor = (theme) => {
  const colors = {
    blue: '#3498db',
    green: '#27ae60',
    orange: '#f39c12',
    purple: '#9b59b6',
    red: '#e74c3c',
    teal: '#1abc9c'
  }
  return colors[theme] || colors.blue
}

const getStatusText = (status) => {
  const statusMap = {
    active: '活跃',
    inactive: '非活跃',
    maintenance: '维护中',
    deprecated: '已弃用',
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const getStatusColor = (status) => {
  const colorMap = {
    pending: '#f39c12',
    running: '#3498db',
    completed: '#27ae60',
    failed: '#e74c3c',
    cancelled: '#95a5a6'
  }
  return colorMap[status] || '#95a5a6'
}

const getCategoryText = (category) => {
  const categoryMap = {
    data_analysis: '数据分析',
    property_prediction: '性质预测',
    process_optimization: '工艺优化',
    knowledge_extraction: '知识抽取',
    decision_support: '决策支持',
    formula_generation: '配方生成'
  }
  return categoryMap[category] || category
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatExecutionTime = (seconds) => {
  if (!seconds || seconds === 0) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

// 生命周期
onMounted(() => {
  fetchAgentDetail()
})
</script>

<style scoped>
.agent-detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
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

.back-navigation {
  margin-bottom: 2rem;
}

.back-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateX(-5px);
}

.agent-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 2rem;
  display: flex;
  align-items: center;
  gap: 2rem;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
}

.agent-avatar-large {
  width: 100px;
  height: 100px;
  border-radius: 25px;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  flex-shrink: 0;
}

.agent-info {
  flex: 1;
}

.agent-title {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.agent-title h1 {
  margin: 0;
  font-size: 2rem;
  color: #2c3e50;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  font-weight: 600;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.agent-description {
  color: #7f8c8d;
  line-height: 1.6;
  margin-bottom: 1rem;
  font-size: 1.1rem;
}

.agent-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.meta-item i {
  color: #95a5a6;
}

.agent-actions {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.btn-large {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.detail-tabs {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
}

.tab-nav {
  display: flex;
  background: #f8f9fa;
  padding: 0;
}

.tab-btn {
  flex: 1;
  padding: 1rem;
  border: none;
  background: none;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: #7f8c8d;
  font-weight: 500;
}

.tab-btn:hover {
  background: #e9ecef;
}

.tab-btn.active {
  background: white;
  color: #667eea;
  font-weight: 600;
  box-shadow: inset 0 -3px 0 #667eea;
}

.tab-content {
  padding: 2rem;
}

.tab-panel {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 2rem;
}

.info-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 1.5rem;
}

.info-card h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.capabilities-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.capability-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #2c3e50;
}

.capability-item i {
  color: #27ae60;
}

.input-types,
.output-types {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.type-tag {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
}

.input-tag {
  background: #e8f4fd;
  color: #2980b9;
}

.output-tag {
  background: #d4edda;
  color: #155724;
}

.model-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.model-item {
  display: flex;
  justify-content: space-between;
}

.model-item label {
  font-weight: 600;
  color: #7f8c8d;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 15px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
  opacity: 0.8;
}

.stat-info h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.5rem;
}

.stat-info p {
  margin: 0;
  opacity: 0.9;
}

.chart-section {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 1.5rem;
}

.status-chart {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.status-bar {
  flex: 1;
  height: 20px;
  background: #ecf0f1;
  border-radius: 10px;
  overflow: hidden;
}

.status-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.status-info {
  display: flex;
  justify-content: space-between;
  width: 150px;
  font-size: 0.9rem;
}

.status-name {
  color: #2c3e50;
}

.status-count {
  font-weight: 600;
  color: #7f8c8d;
}

.guide-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.guide-section h3 {
  margin: 0 0 1rem 0;
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.guide-steps,
.guide-tips,
.guide-warnings {
  margin: 0;
  padding-left: 1.5rem;
  line-height: 1.6;
}

.guide-steps li {
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.guide-tips li {
  margin-bottom: 0.5rem;
  color: #27ae60;
}

.guide-warnings li {
  margin-bottom: 0.5rem;
  color: #e67e22;
}

.prompt-template {
  background: #2c3e50;
  color: #ecf0f1;
  border-radius: 10px;
  padding: 1rem;
  overflow-x: auto;
}

.prompt-template pre {
  margin: 0;
  font-family: 'Consolas', 'Monaco', monospace;
  white-space: pre-wrap;
  line-height: 1.4;
}

.task-history {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.empty-history {
  text-align: center;
  color: #7f8c8d;
  padding: 3rem;
}

.empty-history i {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-item:hover {
  background: #e9ecef;
  transform: translateX(5px);
}

.task-info h4 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.task-info p {
  margin: 0 0 0.5rem 0;
  color: #7f8c8d;
}

.task-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #95a5a6;
}

.task-status-badge {
  padding: 0.5rem 1rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
}

.task-status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.task-status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.task-status-badge.running {
  background: #d1ecf1;
  color: #0c5460;
}

/* 通用按钮样式 */
.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  text-decoration: none;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.btn-secondary {
  background: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background: #d5dbdb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .agent-detail-container {
    padding: 1rem;
  }
  
  .agent-header {
    flex-direction: column;
    text-align: center;
  }
  
  .agent-meta {
    justify-content: center;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .tab-nav {
    flex-wrap: wrap;
  }
  
  .tab-btn {
    flex: none;
    min-width: 50%;
  }
}
</style>