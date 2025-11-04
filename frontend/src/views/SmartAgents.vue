<template>
  <div class="smart-agents-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <i class="fas fa-robot"></i>
          AI智能体
        </h1>
        <p class="page-description">
          探索专业的AI智能体，为材料科学研究提供智能化解决方案
        </p>
      </div>
      
      <!-- 搜索和筛选 -->
      <div class="search-filters">
        <div class="search-box">
          <i class="fas fa-search"></i>
          <input 
            v-model="searchQuery"
            type="text" 
            placeholder="搜索智能体..."
            @input="handleSearch"
          />
        </div>
        
        <div class="category-cards">
          <div 
            v-for="category in categories.slice(1)"
            :key="category.value"
            :class="['category-card', { active: selectedCategory === category.value }]"
            @click="selectCategory(category.value)"
          >
            <div class="card-icon">
              <i :class="category.icon"></i>
            </div>
            <div class="card-content">
              <h3 class="card-title">{{ category.label }}</h3>
              <p class="card-description">{{ getCategoryDescription(category.value) }}</p>
              <div class="card-stats">
                <span class="agent-count">{{ category.count || 0 }} 个智能体</span>
                <span class="popularity">⭐ 4.{{ Math.floor(Math.random() * 5) + 5 }}</span>
              </div>
            </div>
            <div class="card-arrow">
              <i class="fas fa-chevron-right"></i>
            </div>
          </div>
          
          <!-- 全部分类按钮 -->
          <div class="all-categories-btn">
            <button 
              :class="['filter-btn-all', { active: selectedCategory === 'all' }]"
              @click="selectCategory('all')"
            >
              <i class="fas fa-th-large"></i>
              查看全部 ({{ categories[0].count || 0 }})
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner">
        <i class="fas fa-spinner fa-spin"></i>
        <p>加载智能体中...</p>
      </div>
    </div>

    <!-- 智能体网格 -->
    <div v-else class="agents-grid">
      <div 
        v-for="agent in filteredAgents"
        :key="agent.id"
        class="agent-card"
        @click="openAgent(agent)"
      >
        <!-- 智能体头部 -->
        <div class="agent-header">
          <div class="agent-avatar">
            <i v-if="agent.icon" :class="agent.icon" :style="{ color: getThemeColor(agent.color_theme) }"></i>
            <i v-else class="fas fa-robot" :style="{ color: getThemeColor(agent.color_theme) }"></i>
          </div>
          <div class="agent-status">
            <span :class="['status-badge', agent.status]">
              {{ getStatusText(agent.status) }}
            </span>
            <div class="popularity-score">
              <i class="fas fa-star"></i>
              {{ agent.popularity_score.toFixed(1) }}
            </div>
          </div>
        </div>

        <!-- 智能体信息 -->
        <div class="agent-info">
          <h3 class="agent-name">{{ agent.display_name }}</h3>
          <p class="agent-description">{{ agent.description }}</p>
          
          <!-- 能力标签 -->
          <div class="capabilities">
            <span 
              v-for="capability in agent.capabilities.slice(0, 3)"
              :key="capability"
              class="capability-tag"
            >
              {{ capability }}
            </span>
            <span v-if="agent.capabilities.length > 3" class="more-capabilities">
              +{{ agent.capabilities.length - 3 }}
            </span>
          </div>

          <!-- 统计信息 -->
          <div class="agent-stats">
            <div class="stat-item">
              <i class="fas fa-tasks"></i>
              <span>{{ agent.task_count || 0 }} 任务</span>
            </div>
            <div class="stat-item">
              <i class="fas fa-chart-line"></i>
              <span>{{ (agent.success_rate * 100).toFixed(0) }}% 成功率</span>
            </div>
            <div class="stat-item">
              <i class="fas fa-clock"></i>
              <span>{{ formatTime(agent.average_execution_time) }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="agent-actions">
          <button 
            class="btn btn-primary"
            @click.stop="executeAgent(agent)"
          >
            <i class="fas fa-play"></i>
            执行任务
          </button>
          <button 
            class="btn btn-secondary"
            @click.stop="viewDetails(agent)"
          >
            <i class="fas fa-info-circle"></i>
            详情
          </button>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="!loading && filteredAgents.length === 0" class="empty-state">
      <i class="fas fa-robot"></i>
      <h3>暂无智能体</h3>
      <p>{{ searchQuery ? '没有找到匹配的智能体' : '还没有可用的智能体' }}</p>
    </div>

    <!-- 任务执行对话框 -->
    <TaskExecutionModal 
      v-if="showTaskModal"
      :agent="selectedAgent"
      @close="showTaskModal = false"
      @task-created="handleTaskCreated"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/utils/api'
import TaskExecutionModal from '@/components/TaskExecutionModal.vue'

const router = useRouter()

// 响应式数据
const agents = ref([])
const loading = ref(true)
const searchQuery = ref('')
const selectedCategory = ref('all')
const showTaskModal = ref(false)
const selectedAgent = ref(null)

// 分类选项
const categories = ref([
  { value: 'all', label: '全部', icon: 'fas fa-th-large', count: 0 },
  { value: 'data_analysis', label: '数据分析', icon: 'fas fa-chart-bar', count: 0 },
  { value: 'property_prediction', label: '性质预测', icon: 'fas fa-flask', count: 0 },
  { value: 'process_optimization', label: '工艺优化', icon: 'fas fa-cog', count: 0 },
  { value: 'knowledge_extraction', label: '知识抽取', icon: 'fas fa-book', count: 0 },
  { value: 'decision_support', label: '决策支持', icon: 'fas fa-lightbulb', count: 0 }
])

// 计算属性
const filteredAgents = computed(() => {
  let filtered = agents.value

  // 按分类筛选
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(agent => agent.category === selectedCategory.value)
  }

  // 按搜索关键词筛选
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(agent =>
      agent.display_name.toLowerCase().includes(query) ||
      agent.description.toLowerCase().includes(query) ||
      agent.capabilities.some(cap => cap.toLowerCase().includes(query))
    )
  }

  return filtered
})

// 方法
const fetchAgents = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/smart-agent/agents/')
    agents.value = response.data.results || response.data
    updateCategoryCounts()
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    // 这里可以添加错误提示
  } finally {
    loading.value = false
  }
}

const updateCategoryCounts = () => {
  const counts = {}
  agents.value.forEach(agent => {
    counts[agent.category] = (counts[agent.category] || 0) + 1
  })
  
  categories.value.forEach(category => {
    if (category.value === 'all') {
      category.count = agents.value.length
    } else {
      category.count = counts[category.value] || 0
    }
  })
}

const selectCategory = (category) => {
  // 如果点击的是知识抽取类别，直接跳转到知识抽取页面
  if (category === 'knowledge_extraction') {
    router.push({ name: 'KnowledgeExtraction' })
    return
  }
  
  selectedCategory.value = category
}

const handleSearch = () => {
  // 实时搜索已通过计算属性实现
}

const openAgent = (agent) => {
  console.log('点击智能体:', agent.display_name, 'ID:', agent.id)
  router.push({ name: 'AgentDetail', params: { id: agent.id } })
}

const executeAgent = (agent) => {
  selectedAgent.value = agent
  showTaskModal.value = true
}

const viewDetails = (agent) => {
  router.push({ name: 'AgentDetail', params: { id: agent.id } })
}

const handleTaskCreated = (task) => {
  // 任务创建成功后的处理
  console.log('任务已创建:', task)
  router.push({ name: 'agent-tasks' })
}

const getCategoryDescription = (category) => {
  const descriptions = {
    data_analysis: '分析材料数据，发现隐藏模式和趋势',
    property_prediction: '预测材料性能，优化设计方案',
    process_optimization: '优化工艺参数，提升生产效率',
    knowledge_extraction: '从文献中提取关键知识和信息',
    decision_support: '提供智能决策建议和风险评估'
  }
  return descriptions[category] || '专业的AI智能助手'
}

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
    deprecated: '已弃用'
  }
  return statusMap[status] || status
}

const formatTime = (seconds) => {
  if (!seconds || seconds === 0) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
}

// 生命周期
onMounted(() => {
  fetchAgents()
})
</script>

<style scoped>
.smart-agents-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 2rem;
}

.page-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
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

.search-filters {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.search-box {
  position: relative;
  max-width: 500px;
  margin: 0 auto;
}

.search-box i {
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: #95a5a6;
}

.search-box input {
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 3rem;
  border: 2px solid #ecf0f1;
  border-radius: 25px;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
}

.search-box input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 分类卡片样式 */
.category-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.category-card {
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
  display: flex;
  align-items: center;
  gap: 1rem;
  position: relative;
  overflow: hidden;
}

.category-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transform: scaleX(0);
  transition: transform 0.3s ease;
}

.category-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 16px 48px rgba(31, 38, 135, 0.3);
  border-color: #667eea;
}

.category-card:hover::before {
  transform: scaleX(1);
}

.category-card.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  transform: translateY(-8px);
  box-shadow: 0 16px 48px rgba(102, 126, 234, 0.4);
}

.category-card.active::before {
  transform: scaleX(1);
  background: rgba(255, 255, 255, 0.3);
}

.card-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: #667eea;
  flex-shrink: 0;
}

.category-card.active .card-icon {
  background: rgba(255, 255, 255, 0.2);
  color: white;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #2c3e50;
  margin: 0 0 0.5rem 0;
}

.category-card.active .card-title {
  color: white;
}

.card-description {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.category-card.active .card-description {
  color: rgba(255, 255, 255, 0.9);
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.agent-count {
  font-size: 0.8rem;
  color: #667eea;
  font-weight: 600;
}

.category-card.active .agent-count {
  color: rgba(255, 255, 255, 0.9);
}

.popularity {
  font-size: 0.8rem;
  color: #f39c12;
  font-weight: 500;
}

.card-arrow {
  color: #bdc3c7;
  transition: all 0.3s ease;
}

.category-card:hover .card-arrow {
  color: #667eea;
  transform: translateX(5px);
}

.category-card.active .card-arrow {
  color: white;
}

/* 全部分类按钮 */
.all-categories-btn {
  grid-column: 1 / -1;
  display: flex;
  justify-content: center;
  margin-top: 1rem;
}

.filter-btn-all {
  padding: 1rem 2rem;
  border: 2px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 25px;
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-btn-all:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
}

.filter-btn-all.active {
  background: rgba(255, 255, 255, 0.95);
  color: #667eea;
  border-color: white;
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

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
  gap: 2rem;
}

.agent-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 1.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
}

.agent-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 20px 40px rgba(31, 38, 135, 0.5);
}

.agent-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.agent-avatar {
  width: 60px;
  height: 60px;
  border-radius: 15px;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.agent-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.5rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-badge.active {
  background: #d4edda;
  color: #155724;
}

.status-badge.inactive {
  background: #f8d7da;
  color: #721c24;
}

.popularity-score {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #f39c12;
  font-weight: 600;
  font-size: 0.9rem;
}

.agent-info {
  margin-bottom: 1.5rem;
}

.agent-name {
  font-size: 1.3rem;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.agent-description {
  color: #7f8c8d;
  line-height: 1.5;
  margin-bottom: 1rem;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.capability-tag {
  background: #e8f4fd;
  color: #2980b9;
  padding: 0.3rem 0.6rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 500;
}

.more-capabilities {
  background: #f8f9fa;
  color: #6c757d;
  padding: 0.3rem 0.6rem;
  border-radius: 15px;
  font-size: 0.8rem;
}

.agent-stats {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #7f8c8d;
  font-size: 0.8rem;
}

.stat-item i {
  color: #95a5a6;
}

.agent-actions {
  display: flex;
  gap: 0.5rem;
}

.btn {
  flex: 1;
  padding: 0.75rem 1rem;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
  transform: translateY(-2px);
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

/* 响应式设计 */
@media (max-width: 768px) {
  .smart-agents-container {
    padding: 1rem;
  }
  
  .category-cards {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .category-card {
    padding: 1rem;
    flex-direction: column;
    text-align: center;
  }
  
  .card-icon {
    width: 50px;
    height: 50px;
    font-size: 1.5rem;
  }
  
  .card-stats {
    justify-content: center;
  }
  
  .agents-grid {
    grid-template-columns: 1fr;
  }
  
  .agent-stats {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .agent-actions {
    flex-direction: column;
  }
}

@media (max-width: 480px) {
  .category-cards {
    grid-template-columns: 1fr;
  }
  
  .category-card {
    padding: 1rem;
  }
  
  .card-title {
    font-size: 1rem;
  }
  
  .card-description {
    font-size: 0.85rem;
  }
}
</style>