<template>
  <div class="smart-agents-page-wrapper">
    <NavigationSidebar />

    <div class="smart-agents-container">
      <div class="page-content">
        <!-- 页面头部 -->
        <div class="page-header">
          <div class="header-content">
            <div>
              <h1 class="page-title"><i class="fas fa-robot"></i> AI智能体</h1>
              <p class="page-description">探索专业的 AI 智能体，为材料科学研究提供智能化解决方案</p>
            </div>

            <div class="search-filters">
              <div class="search-box">
                <i class="fas fa-search"></i>
                <input v-model="searchQuery" type="text" placeholder="搜索智能体..." @input="handleSearch" />
              </div>

              <button class="filter-btn-all" @click="selectCategory('')">全部分类</button>
            </div>
          </div>

          <div v-if="loadError" class="error-banner">
            {{ loadError }}（已切换到本地兜底数据）
          </div>

          <div class="category-cards">
            <div
              v-for="category in categories"
              :key="category.value"
              :class="['category-card', { active: selectedCategory === category.value }]"
              @click="selectCategory(category.value)">
              <div class="card-icon">{{ category.icon || '🤖' }}</div>
              <div class="card-content">
                <div class="card-title">{{ category.label }}</div>
                <div class="card-description">{{ category.description }}</div>
                <div class="card-stats"><span class="agent-count">{{ getCategoryCount(category.value) }}</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="tasks-dashboard-section">
          <div class="dashboard-kpis">
            <div class="kpi-card">
              <div class="kpi-label">任务总数</div>
              <div class="kpi-value">{{ dashboardStats.total }}</div>
              <div class="kpi-sub">全部任务</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">运行中</div>
              <div class="kpi-value">{{ dashboardStats.running }}</div>
              <div class="kpi-sub">实时任务负载</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">完成率</div>
              <div class="kpi-value">{{ dashboardStats.successRate }}%</div>
              <div class="kpi-sub">completed / total</div>
            </div>
            <div class="kpi-card">
              <div class="kpi-label">平均耗时</div>
              <div class="kpi-value">{{ dashboardStats.avgDuration }}</div>
              <div class="kpi-sub">仅统计有耗时数据</div>
            </div>
          </div>

          <div class="dashboard-panels">
            <div class="dashboard-panel cockpit-main">
              <h3><i class="fas fa-bullseye"></i> 任务状态态势</h3>
              <div ref="statusDonutChartRef" class="dashboard-chart"></div>
              <div class="status-legend">
                <div v-for="item in statusDistribution" :key="item.status" class="legend-item">
                  <span class="legend-dot" :style="{ background: getStatusColor(item.status) }"></span>
                  <span class="legend-name">{{ getStatusText(item.status) }}</span>
                  <span class="legend-value">{{ item.count }} / {{ item.percent }}%</span>
                </div>
              </div>
            </div>

            <div class="dashboard-panel cockpit-main">
              <h3><i class="fas fa-wave-square"></i> 近7天任务趋势</h3>
              <div ref="trendLineChartRef" class="dashboard-chart"></div>
              <div class="trend-summary">
                <div class="trend-pill">近7天总量：{{ recentSevenDayTotal }}</div>
                <div class="trend-pill">峰值日：{{ peakDay.label || '-' }}（{{ peakDay.count }}）</div>
              </div>
            </div>

            <div class="dashboard-panel cockpit-side">
              <h3><i class="fas fa-robot"></i> 常用智能体 TOP5</h3>
              <div v-if="topAgentUsage.length === 0" class="panel-empty">暂无数据</div>
              <div v-else>
                <div v-for="(agent, idx) in topAgentUsage" :key="`${agent.name}-${idx}`" class="agent-rank-row">
                  <div class="rank-index">#{{ idx + 1 }}</div>
                  <div class="rank-name">{{ agent.name }}</div>
                  <div class="rank-count">{{ agent.count }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 智能体列表 -->
        <div v-if="loading" class="loading-container">
          <div class="loading-spinner">加载中...</div>
        </div>

        <div v-else class="agents-grid">
          <div v-if="filteredAgents.length === 0" class="empty-state">
            <i class="fas fa-sitemap"></i>
            <h3>未找到匹配的智能体</h3>
            <p>尝试调整搜索关键词或切换分类。</p>
          </div>

          <div v-for="agent in filteredAgents" :key="agent.id" class="agent-card">
            <div class="agent-header">
              <div style="display:flex; gap:12px; align-items:center">
                <div class="agent-avatar">
                  <i :class="agent.iconClass || 'fas fa-robot'"></i>
                </div>
                <div>
                  <div class="agent-name">{{ agent.displayName }}</div>
                  <div class="agent-description">{{ agent.description }}</div>
                </div>
              </div>

              <div class="agent-status">
                <div :class="['status-badge', agent.active ? 'active' : 'inactive']">{{ agent.active ? '在线' : '离线' }}</div>
                <div class="popularity-score">★ {{ agent.popularity }}</div>
              </div>
            </div>

            <div class="agent-info">
              <div class="capabilities">
                <span v-for="(c, idx) in agent.capabilities.slice(0,4)" :key="idx" class="capability-tag">{{ c }}</span>
                <span v-if="agent.capabilities.length>4" class="more-capabilities">+{{ agent.capabilities.length - 4 }}</span>
              </div>

              <div class="agent-stats">
                <div class="stat-item"><i class="fas fa-clock"></i> 最近更新：{{ agent.lastUpdated }}</div>
                <div class="stat-item"><i class="fas fa-users"></i> 使用次数：{{ agent.usage || 0 }}</div>
              </div>

              <div class="agent-actions">
                <button class="btn btn-primary" @click.stop="openAgent(agent)">启动</button>
                <button class="btn btn-secondary" @click.stop="viewDetails(agent)">详情</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import apiClient from '@/utils/api'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()
const API_BASE = '/smart-agent'

const searchQuery = ref('')
const selectedCategory = ref('')
const loading = ref(true)
const loadError = ref('')
const agents = ref([])
const tasks = ref([])
const statusDonutChartRef = ref(null)
const trendLineChartRef = ref(null)

let statusDonutChart = null
let trendLineChart = null

const categories = ref([
  { label: '全部', value: '', description: '所有智能体', icon: '✨' },
  { label: '数据分析', value: 'data_analysis', description: '数据可视化与分析', icon: '📊' },
  { label: '配方生成', value: 'formula_generation', description: '材料配方建议', icon: '⚗️' },
  { label: '工艺优化', value: 'process_optimization', description: '工艺与流程优化', icon: '🛠️' },
  { label: '知识抽取', value: 'knowledge_extraction', description: '结构化提取与知识构建', icon: '🧠' },
  { label: '性质预测', value: 'property_prediction', description: '性质建模与预测', icon: '📈' },
  { label: '决策支持', value: 'decision_support', description: '实验决策与路线建议', icon: '🧭' },
])

const requiredDemoAgents = [
  {
    id: 'demo-formula',
    displayName: '配方生成智能体',
    description: '用于材料配方建议与成本平衡设计。',
    category: 'formula_generation',
    active: true,
    popularity: 4.8,
    capabilities: ['配方建议', '成本估算', '性能预测'],
    lastUpdated: '刚刚',
    usage: 0,
    iconClass: 'fas fa-flask'
  },
  {
    id: 'demo-process',
    displayName: '工艺优化智能体',
    description: '用于生产参数优化与工艺窗口推荐。',
    category: 'process_optimization',
    active: true,
    popularity: 4.6,
    capabilities: ['工艺参数建议', '风险提示'],
    lastUpdated: '刚刚',
    usage: 0,
    iconClass: 'fas fa-cogs'
  },
  {
    id: 'demo-analysis',
    displayName: '数据分析智能体',
    description: '用于实验数据分析和可视化洞察。',
    category: 'data_analysis',
    active: true,
    popularity: 4.7,
    capabilities: ['图表分析', '异常识别'],
    lastUpdated: '刚刚',
    usage: 0,
    iconClass: 'fas fa-chart-line'
  },
  {
    id: 'demo-extract',
    displayName: '知识抽取智能体',
    description: '用于文献知识抽取与结构化整理。',
    category: 'knowledge_extraction',
    active: true,
    popularity: 4.5,
    capabilities: ['实体抽取', '关系抽取'],
    lastUpdated: '刚刚',
    usage: 0,
    iconClass: 'fas fa-brain'
  },
  {
    id: 'demo-property',
    displayName: '性质预测智能体',
    description: '用于材料性质估计、趋势分析和误差评估。',
    category: 'property_prediction',
    active: true,
    popularity: 4.4,
    capabilities: ['性质预测', '误差分析', '候选筛选'],
    lastUpdated: '刚刚',
    usage: 0,
    iconClass: 'fas fa-chart-area'
  },
  {
    id: 'demo-decision',
    displayName: '决策支持智能体',
    description: '用于多目标权衡、方案排序和实验优先级建议。',
    category: 'decision_support',
    active: true,
    popularity: 4.3,
    capabilities: ['策略推荐', '多目标评分', '风险提示'],
    lastUpdated: '刚刚',
    usage: 0,
    iconClass: 'fas fa-compass'
  }
]

const ensureRequiredAgents = (list) => {
  const normalized = Array.isArray(list) ? [...list] : []
  const existingCategories = new Set(normalized.map((a) => a.category))

  requiredDemoAgents.forEach((demo) => {
    if (!existingCategories.has(demo.category)) {
      normalized.push({ ...demo })
    }
  })

  return normalized
}

const normalizeAgent = (raw) => {
  const cap = Array.isArray(raw?.capabilities)
    ? raw.capabilities
    : typeof raw?.capabilities === 'string'
      ? [raw.capabilities]
      : []

  return {
    id: raw.id,
    displayName: raw.display_name || raw.name || '未命名智能体',
    description: raw.description || '暂无描述',
    category: raw.category || 'other',
    active: (raw.status || '').toLowerCase() === 'active',
    popularity: Number(raw.popularity_score || 0),
    capabilities: cap,
    lastUpdated: formatRelativeTime(raw.updated_at || raw.created_at),
    usage: raw.usage_count || 0,
    iconClass: raw.icon || 'fas fa-robot'
  }
}

async function fetchAgents() {
  loading.value = true
  loadError.value = ''
  try {
    const response = await apiClient.get(`${API_BASE}/agents/`)
    const list = response.data?.results || response.data || []
  const normalized = list.map(normalizeAgent)
  agents.value = ensureRequiredAgents(normalized)

    // 追加后端返回但前端预设不存在的分类（避免“被删掉”的分类不显示）
    const preset = new Set(categories.value.map((c) => c.value))
    const dynamicCategories = [...new Set(agents.value.map((a) => a.category).filter(Boolean))]
    dynamicCategories.forEach((key) => {
      if (!preset.has(key)) {
        categories.value.push({ label: key, value: key, description: '后端动态分类', icon: '🧩' })
      }
    })
  } catch (error) {
    console.error('获取智能体列表失败:', error)
    loadError.value = '后端接口暂不可用'
    agents.value = ensureRequiredAgents([])
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  // 保留输入联动点，当前由 computed 自动过滤
}

function selectCategory(val) {
  selectedCategory.value = val
}

function getCategoryCount(val) {
  if (!val) return agents.value.length
  return agents.value.filter(a => a.category === val).length
}

function openAgent(agent) {
  const routeMap = {
    formula_generation: '/formula-generation',
    process_optimization: '/process-optimization',
    data_analysis: '/data-analysis',
    knowledge_extraction: '/knowledge-extraction',
    property_prediction: '/property-prediction',
    decision_support: '/decision-support'
  }
  const path = routeMap[agent.category]
  if (path) {
    router.push(path)
    return
  }
  router.push(`/agents/${agent.id}`)
}

function viewDetails(agent) {
  router.push(`/agents/${agent.id}`)
}

function formatRelativeTime(dateValue) {
  if (!dateValue) return '未知'
  const date = new Date(dateValue)
  if (Number.isNaN(date.getTime())) return '未知'

  const diffMs = Date.now() - date.getTime()
  const hour = 3600 * 1000
  const day = 24 * hour

  if (diffMs < hour) return '1小时内'
  if (diffMs < day) return `${Math.floor(diffMs / hour)} 小时前`
  if (diffMs < 7 * day) return `${Math.floor(diffMs / day)} 天前`
  return date.toLocaleDateString('zh-CN')
}

const filteredAgents = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  return agents.value.filter(a => {
    const matchCategory = selectedCategory.value ? a.category === selectedCategory.value : true
    const matchQuery = !q || a.displayName.toLowerCase().includes(q) || a.description.toLowerCase().includes(q)
    return matchCategory && matchQuery
  })
})

const dashboardStats = computed(() => {
  const total = tasks.value.length
  const running = tasks.value.filter((t) => t.status === 'running').length
  const completed = tasks.value.filter((t) => t.status === 'completed').length
  const withDuration = tasks.value.filter((t) => Number(t.execution_time) > 0)
  const avgSec = withDuration.length
    ? withDuration.reduce((sum, t) => sum + Number(t.execution_time || 0), 0) /
      withDuration.length
    : 0

  return {
    total,
    running,
    successRate: total ? ((completed / total) * 100).toFixed(1) : '0.0',
    avgDuration: avgSec ? formatDuration(avgSec) : '-'
  }
})

const statusDistribution = computed(() => {
  const total = tasks.value.length || 1
  const statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
  return statuses.map((status) => {
    const count = tasks.value.filter((t) => t.status === status).length
    return {
      status,
      count,
      percent: Number(((count / total) * 100).toFixed(1))
    }
  })
})

const topAgentUsage = computed(() => {
  const usageMap = new Map()
  tasks.value.forEach((task) => {
    const key = task.agent_name || '未知智能体'
    usageMap.set(key, (usageMap.get(key) || 0) + 1)
  })
  return [...usageMap.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
})

const recentDailyTrend = computed(() => {
  const days = 7
  const now = new Date()
  const bucket = []

  for (let i = days - 1; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(now.getDate() - i)
    const label = `${d.getMonth() + 1}/${d.getDate()}`
    const start = new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime()
    const end = start + 24 * 60 * 60 * 1000
    const count = tasks.value.filter((t) => {
      const ts = new Date(t.created_at).getTime()
      return ts >= start && ts < end
    }).length
    bucket.push({ label, count })
  }

  return bucket
})

const recentSevenDayTotal = computed(() => {
  return recentDailyTrend.value.reduce((sum, item) => sum + item.count, 0)
})

const peakDay = computed(() => {
  if (!recentDailyTrend.value.length) {
    return { label: '-', count: 0 }
  }
  return recentDailyTrend.value.reduce((max, item) =>
    item.count > max.count ? item : max
  )
})

const getStatusColor = (status) => {
  const colorMap = {
    pending: '#f59e0b',
    running: '#38bdf8',
    completed: '#22c55e',
    failed: '#ef4444',
    cancelled: '#94a3b8'
  }
  return colorMap[status] || '#a78bfa'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

const renderStatusDonutChart = () => {
  if (!statusDonutChartRef.value) return

  if (!statusDonutChart) {
    statusDonutChart = echarts.init(statusDonutChartRef.value)
  }

  const chartData = statusDistribution.value
    .filter((item) => item.count > 0)
    .map((item) => ({
      name: getStatusText(item.status),
      value: item.count,
      itemStyle: { color: getStatusColor(item.status) }
    }))

  const finalData = chartData.length
    ? chartData
    : [
        {
          name: '暂无数据',
          value: 1,
          itemStyle: { color: 'rgba(148, 163, 184, 0.35)' }
        }
      ]

  statusDonutChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: ['56%', '76%'],
        center: ['50%', '50%'],
        padAngle: 2,
        avoidLabelOverlap: true,
        label: {
          show: true,
          color: '#334155',
          formatter: '{d}%'
        },
        labelLine: {
          show: true,
          lineStyle: { color: 'rgba(148, 163, 184, 0.8)' }
        },
        itemStyle: {
          borderRadius: 8,
          borderColor: '#ffffff',
          borderWidth: 2
        },
        data: finalData
      }
    ]
  })
}

const renderTrendLineChart = () => {
  if (!trendLineChartRef.value) return

  if (!trendLineChart) {
    trendLineChart = echarts.init(trendLineChartRef.value)
  }

  const labels = recentDailyTrend.value.map((item) => item.label)
  const values = recentDailyTrend.value.map((item) => item.count)

  trendLineChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: 24,
      right: 16,
      top: 20,
      bottom: 28,
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: labels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.5)' } },
      axisLabel: { color: '#64748b' }
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.18)' } },
      axisLabel: { color: '#64748b' }
    },
    series: [
      {
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#38bdf8', width: 3 },
        itemStyle: { color: '#38bdf8' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(56, 189, 248, 0.45)' },
            { offset: 1, color: 'rgba(56, 189, 248, 0.02)' }
          ])
        },
        data: values
      }
    ]
  })
}

const renderDashboardCharts = async () => {
  await nextTick()
  renderStatusDonutChart()
  renderTrendLineChart()
}

const disposeDashboardCharts = () => {
  if (statusDonutChart) {
    statusDonutChart.dispose()
    statusDonutChart = null
  }
  if (trendLineChart) {
    trendLineChart.dispose()
    trendLineChart = null
  }
}

const resizeDashboardCharts = () => {
  statusDonutChart?.resize()
  trendLineChart?.resize()
}

async function fetchTasksOverview() {
  try {
    const response = await apiClient.get(`${API_BASE}/tasks/`)
    tasks.value = response.data?.results || response.data || []
  } catch (error) {
    console.error('获取任务统计数据失败:', error)
    tasks.value = []
  } finally {
    await renderDashboardCharts()
  }
}

onMounted(() => {
  Promise.all([fetchAgents(), fetchTasksOverview()])
  window.addEventListener('resize', resizeDashboardCharts)
})

onUnmounted(() => {
  window.removeEventListener('resize', resizeDashboardCharts)
  disposeDashboardCharts()
})

watch([statusDistribution, recentDailyTrend], () => {
  renderDashboardCharts()
})
</script>

<style scoped>
  .smart-agents-page-wrapper {
    display: flex;
    min-height: 100dvh;
    background: #f6f8fb;
    width: 100%;
  }

  .smart-agents-container {
    flex: 1;
    overflow-y: auto;
    min-height: 100dvh;
    width: 100%;
    padding: clamp(14px, 2vw, 28px) clamp(12px, 2vw, 24px) 32px;
    box-sizing: border-box;
    display: flex;
    justify-content: stretch;
  }

  .smart-agents-container > .page-content {
    width: 100%;
    max-width: none;
  }

  .tasks-dashboard-section {
    margin-bottom: 18px;
  }

  .dashboard-kpis {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.9rem;
    margin-bottom: 0.9rem;
  }

  .kpi-card {
    background: linear-gradient(145deg, #ffffff, #f8fafc);
    border-radius: 14px;
    border: 1px solid #dbe5f1;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08), inset 0 1px 0 #ffffff;
    padding: 0.9rem 1rem;
  }

  .kpi-label {
    font-size: 0.8rem;
    color: #64748b;
  }

  .kpi-value {
    margin: 0.25rem 0;
    font-size: 1.55rem;
    font-weight: 700;
    color: #0f172a;
  }

  .kpi-sub {
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .dashboard-panels {
    display: grid;
    grid-template-columns: 1.1fr 1.3fr 0.9fr;
    gap: 0.9rem;
  }

  .dashboard-panel {
    background: linear-gradient(155deg, #ffffff, #f8fafc);
    border-radius: 14px;
    border: 1px solid #dbe5f1;
    box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
    padding: 0.9rem 1rem;
  }

  .dashboard-panel h3 {
    margin: 0 0 0.8rem;
    font-size: 0.95rem;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 0.45rem;
  }

  .cockpit-main {
    min-height: 360px;
  }

  .cockpit-side {
    min-height: 360px;
  }

  .dashboard-chart {
    height: 220px;
    width: 100%;
  }

  .status-legend {
    margin-top: 0.3rem;
    display: grid;
    gap: 0.4rem;
  }

  .legend-item {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.78rem;
  }

  .legend-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    box-shadow: 0 0 6px rgba(59, 130, 246, 0.3);
  }

  .legend-name {
    color: #334155;
  }

  .legend-value {
    color: #0f172a;
    font-weight: 600;
  }

  .trend-summary {
    margin-top: 0.6rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
  }

  .trend-pill {
    padding: 0.28rem 0.55rem;
    border-radius: 999px;
    border: 1px solid #cbd5e1;
    background: #f8fafc;
    color: #475569;
    font-size: 0.72rem;
  }

  .agent-rank-row {
    display: grid;
    grid-template-columns: 34px 1fr 36px;
    align-items: center;
    gap: 0.4rem;
    padding: 0.32rem 0;
    border-bottom: 1px dashed #dbe5f1;
  }

  .agent-rank-row:last-child {
    border-bottom: none;
  }

  .rank-index {
    color: #4f46e5;
    font-weight: 700;
    font-size: 0.78rem;
  }

  .rank-name {
    color: #334155;
    font-size: 0.8rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .rank-count {
    color: #0f172a;
    font-weight: 700;
    font-size: 0.78rem;
    text-align: right;
  }

  .panel-empty {
    color: #94a3b8;
    font-size: 0.8rem;
  }

  .page-header {
    background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(250,250,255,0.98));
    border-radius: 12px;
    padding: 20px 20px 16px;
    margin-bottom: 18px;
    box-shadow: 0 8px 20px rgba(30,41,59,0.06);
    border: 1px solid #eef3fb;
  }

  .header-content {
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 12px;
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .error-banner {
    margin: 8px 0 12px;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 0.88rem;
    background: #fff7ed;
    color: #9a3412;
    border: 1px solid #fed7aa;
  }

  .page-title { font-size: 1.6rem; font-weight: 700; color: #0f172a; margin: 0; display:flex; align-items:center; gap:12px }
  .page-title i { color:#4f46e5 }
  .page-description { font-size: 0.95rem; color: #475569; margin: 6px 0 0 }

  .search-filters { display:flex; gap:14px; align-items:center; flex-wrap:wrap }
  .search-box { position:relative; width:min(420px, 100%); min-width:220px }
  .search-box i { position:absolute; left:12px; top:50%; transform:translateY(-50%); color:#94a3b8 }
  .search-box input { width:100%; padding:10px 12px 10px 36px; border:1px solid #e6eef9; border-radius:999px; background:#fff; box-sizing:border-box }

  .category-cards { display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-top:12px; width:100% }
  .category-card { background:#fff; border-radius:12px; padding:12px; cursor:pointer; display:flex; gap:12px; border:1px solid #f1f5f9; box-shadow:0 6px 20px rgba(15,23,42,0.04); transition:transform .22s ease, box-shadow .22s ease }
  .category-card:hover { transform:translateY(-6px) }
  .category-card.active { background:linear-gradient(90deg,#eef2ff,#f8faff); border-color:#e0e7ff }
  .card-icon { width:48px; height:48px; border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; background:#fbfdff }
  .card-title { font-size:1rem; font-weight:700; margin:0 }
  .card-description { font-size:0.85rem; color:#64748b; margin-top:4px }

  .agents-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap:16px; margin-top:18px; width:100% }
  .agent-card { background:#fff; border-radius:12px; padding:14px; border:1px solid #eef3fb; box-shadow:0 6px 24px rgba(15,23,42,0.04); transition:transform .18s ease }
  .agent-card:hover { transform:translateY(-6px); box-shadow:0 14px 36px rgba(15,23,42,0.08) }
  .agent-header { display:flex; justify-content:space-between; gap:12px; align-items:flex-start }
  .agent-avatar { width:52px; height:52px; border-radius:12px; background:#fbfdff; display:flex; align-items:center; justify-content:center; font-size:1.25rem }
  .agent-avatar i { color:#4f46e5 }
  .agent-name { font-size:1.05rem; font-weight:700; margin-bottom:6px }
  .agent-description { color:#64748b; font-size:0.95rem; line-height:1.4; margin-bottom:10px; max-height:3.2em; overflow:hidden }
  .capabilities { display:flex; flex-wrap:wrap; gap:6px }
  .capability-tag { background:#eef6ff; color:#2563eb; padding:4px 8px; border-radius:999px; font-size:0.78rem }
  .more-capabilities { background:#f8f9fa; color:#6c757d; padding:4px 8px; border-radius:999px }
  .agent-stats { display:flex; flex-wrap:wrap; gap:12px; align-items:center; color:#64748b; font-size:0.82rem }
  .agent-actions { display:flex; gap:8px; margin-top:12px }
  .btn { padding:8px 12px; border-radius:8px; font-weight:700; cursor:pointer; border:none }
  .btn-primary { background:#4f46e5; color:#fff }
  .btn-secondary { background:#fff; color:#334155; border:1px solid #e6eef9 }

  .empty-state { text-align:center; color:#64748b; padding:2rem 1rem }

  .loading-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 180px;
    color: #475569;
  }

  .loading-spinner {
    font-weight: 600;
  }

  @media (max-width: 980px) {
    .smart-agents-container { padding:16px }
    .header-content { flex-direction:column; align-items:flex-start }
    .search-filters { width:100%; justify-content:space-between }
    .category-cards { grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); }
    .dashboard-kpis { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .dashboard-panels { grid-template-columns: 1fr; }
  }

  @media (max-width: 640px) {
    .smart-agents-container { padding: 12px; }
    .search-box { width:100% }
    .category-cards { grid-template-columns: 1fr }
    .agents-grid { grid-template-columns: 1fr }
    .agent-actions { flex-direction: column; }
  }
</style>
