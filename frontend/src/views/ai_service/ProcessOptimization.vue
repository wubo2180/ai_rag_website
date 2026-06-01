<template>
  <div class="process-optimization-page-wrapper">
    <NavigationSidebar />
    <div class="process-optimization-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-main">
        <button @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
        <div>
          <h1>工艺优化智能体</h1>
          <p>优化工艺参数，提升生产效率</p>
        </div>
      </div>
      <div class="header-actions">
  <button type="button" class="action-btn secondary" @click="loadDemoOptimization">载入 Demo 看板</button>
        <button type="button" class="action-btn ghost" @click="clearAll">清空结果</button>
      </div>
    </div>

    <!-- 输入表单 -->
    <div class="form-section">
      <div class="form-card">
        <h2>
          <i class="fas fa-edit"></i>
          输入参数
        </h2>

        <form @submit.prevent="submitForm">
          <div class="base-input-grid">
          <div class="form-group">
            <label for="optimization_targets">
              <i class="fas fa-chart-line"></i>
              优化目标
              <span class="required">*</span>
            </label>
            <textarea
              id="optimization_targets"
              v-model="formData.optimization_targets"
              placeholder="例如：将致密度提升至3.5 g/cm³以上，同时能耗下降10%"
              rows="3"
              required
            ></textarea>
            <small class="field-hint">请描述需要优化或提升的关键性能指标</small>
          </div>

          <div class="form-group">
            <label for="material_product_data">
              <i class="fas fa-cubes"></i>
              材料与产品规格
              <span class="required">*</span>
            </label>
            <textarea
              id="material_product_data"
              v-model="formData.material_product_data"
              placeholder="例如：氧化铝陶瓷生坯，初始密度2.6 g/cm³，平均粒径0.5μm"
              rows="3"
              required
            ></textarea>
            <small class="field-hint">填写材料体系、初始状态与产品规格信息</small>
          </div>

          <div class="form-group">
            <label for="process_parameters">
              <i class="fas fa-sliders-h"></i>
              可调工艺参数
              <span class="required">*</span>
            </label>
            <textarea
              id="process_parameters"
              v-model="formData.process_parameters"
              placeholder="例如：烧结温度1400~1600°C，保温60~180分钟，升温速率2~10°C/分钟"
              rows="3"
              required
            ></textarea>
            <small class="field-hint">请列出可调参数及其允许范围</small>
          </div>

          <div class="form-group">
            <label for="knowledge_constraints">
              <i class="fas fa-book"></i>
              知识与约束
              <span class="required">*</span>
            </label>
            <textarea
              id="knowledge_constraints"
              v-model="formData.knowledge_constraints"
              placeholder="例如：温度超过1550°C可能导致晶粒异常长大"
              rows="3"
              required
            ></textarea>
            <small class="field-hint">填写工艺、物化机制与生产限制条件</small>
          </div>

          <div class="form-group">
            <label for="cost_consideration">
              <i class="fas fa-dollar-sign"></i>
              成本考量
              <span class="required">*</span>
            </label>
            <textarea
              id="cost_consideration"
              v-model="formData.cost_consideration"
              placeholder="例如：单公斤成本控制在 200 元以内"
              rows="2"
              required
            ></textarea>
            <small class="field-hint">请明确成本预算和控制要求</small>
          </div>

          <div class="form-group">
            <label for="environmental_requirements">
              <i class="fas fa-leaf"></i>
              环保要求
              <span class="required">*</span>
            </label>
            <textarea
              id="environmental_requirements"
              v-model="formData.environmental_requirements"
              placeholder="例如：符合 RoHS/REACH，无卤、低VOC 排放"
              rows="2"
              required
            ></textarea>
            <small class="field-hint">请说明环保标准和合规要求</small>
          </div>

          <div class="form-group">
            <label for="environmental_real_time_data">
              <i class="fas fa-cloud-sun"></i>
              环境与实时数据
            </label>
            <textarea
              id="environmental_real_time_data"
              v-model="formData.environmental_real_time_data"
              placeholder="可选：温湿度、设备状态、实时偏差等"
              rows="2"
            ></textarea>
            <small class="field-hint">可选，用于结合在线工况做优化</small>
          </div>

          <div class="form-group">
            <label for="historical_data">
              <i class="fas fa-history"></i>
              历史数据
            </label>
            <textarea
              id="historical_data"
              v-model="formData.historical_data"
              placeholder="可选：上一批次参数与结果、历史实验记录"
              rows="2"
            ></textarea>
            <small class="field-hint">可选，建议填写历史参数-结果映射</small>
          </div>

          <div class="form-group">
            <label for="expected_performance">
              <i class="fas fa-flag-checkered"></i>
              预期性能
            </label>
            <textarea
              id="expected_performance"
              v-model="formData.expected_performance"
              placeholder="可选：期望密度、良率、能耗、成本等目标值"
              rows="2"
            ></textarea>
            <small class="field-hint">可选，用于量化对比推荐方案效果</small>
          </div>
          </div>

          <div class="form-actions">
            <button
              type="button"
              class="btn btn-secondary"
              @click="resetForm"
              :disabled="loading"
            >
              <i class="fas fa-redo"></i>
              重置
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              <i class="fas fa-paper-plane" v-if="!loading"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              {{ loading ? '分析中...' : '开始优化' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 结果显示区域 -->
    <div v-if="showResult" class="result-section">
      <div class="result-card">
        <h2>
          <i class="fas fa-lightbulb"></i>
          优化建议
        </h2>

        <!-- 流式输出显示 -->
        <div v-if="streaming" class="streaming-output">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div class="stream-content" v-html="formatMarkdown(streamingAnswer)"></div>
        </div>

        <!-- 完整结果显示 -->
        <div v-else class="result-content">
          <div class="summary-kpi-grid">
            <div class="summary-kpi-card" v-for="item in optimizationSummary" :key="item.label">
              <div class="summary-kpi-label">{{ item.label }}</div>
              <div class="summary-kpi-value">{{ item.value }}</div>
              <div class="summary-kpi-note">{{ item.note }}</div>
            </div>
          </div>

          <div class="result-text" v-html="formatMarkdown(result)"></div>

          <div class="insight-board">
            <div class="insight-col">
              <h3><i class="fas fa-table"></i> 建议工艺参数表</h3>
              <div class="table-wrap">
                <table class="rich-table">
                  <thead>
                    <tr>
                      <th>参数项</th>
                      <th>当前值</th>
                      <th>建议区间</th>
                      <th>收益</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, idx) in processParameterRows" :key="idx">
                      <td>{{ row.name }}</td>
                      <td>{{ row.current }}</td>
                      <td>{{ row.recommend }}</td>
                      <td>{{ row.benefit }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="insight-col">
              <h3><i class="fas fa-clipboard-check"></i> 风险与验证清单</h3>
              <ul class="checklist">
                <li v-for="(item, idx) in riskChecklist" :key="idx">{{ item }}</li>
              </ul>
            </div>
          </div>

          <div class="result-meta">
            <div class="meta-item">
              <i class="fas fa-clock"></i>
              <span>{{ formatDate(resultTime) }}</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-comment"></i>
              <span>会话 ID: {{ conversationId }}</span>
            </div>
            <div class="meta-item validity-select-item" :class="{ disabled: !currentHistoryId }">
              <i class="fas fa-clipboard-check"></i>
              <label for="process-validity-status">是否有效配方</label>
              <select
                id="process-validity-status"
                v-model="currentValidityStatus"
                :disabled="!currentHistoryId"
              >
                <option value="pending">待确认</option>
                <option value="valid">有效</option>
                <option value="invalid">无效</option>
              </select>
            </div>
          </div>

          <div class="result-actions">
            <button
              class="btn btn-outline"
              @click="copyResult"
            >
              <i class="fas fa-copy"></i>
              复制结果
            </button>
            <button
              class="btn btn-outline"
              @click="downloadResult"
            >
              <i class="fas fa-download"></i>
              下载报告
            </button>
            <button
              class="btn btn-primary"
              @click="newOptimization"
            >
              <i class="fas fa-plus"></i>
              新建优化
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录 -->
    <div v-if="historyList.length > 0" class="history-section">
      <h2>
        <i class="fas fa-history"></i>
        历史记录
      </h2>
      <div class="history-table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>配方简要</th>
              <th>时间</th>
              <th>任务状态</th>
              <th>是否有效配方</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedHistoryList"
              :key="item.id"
              class="history-row"
            >
              <td class="history-id">{{ item.id }}</td>
              <td class="history-brief">{{ item.brief }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
              <td>
                <span :class="['task-status-badge', `status-${getTaskStatus(item)}`]">
                  {{ getTaskStatusLabel(item) }}
                </span>
              </td>
              <td>
                <span :class="['valid-badge', `status-${getValidityStatus(item)}`]">
                  {{ getValidityLabel(item) }}
                </span>
              </td>
              <td>
                <button class="history-view-btn" type="button" @click="openHistoryDetail(item)">
                  进入查看
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="totalHistoryPages > 1" class="history-pagination">
        <button class="page-btn" :disabled="historyPage === 1" @click="goToHistoryPage(historyPage - 1)">上一页</button>
        <button
          v-for="page in historyPageNumbers"
          :key="`history-page-${page}`"
          :class="['page-btn', { active: page === historyPage }]"
          @click="goToHistoryPage(page)"
        >
          {{ page }}
        </button>
        <button class="page-btn" :disabled="historyPage === totalHistoryPages" @click="goToHistoryPage(historyPage + 1)">下一页</button>
        <span class="page-summary">第 {{ historyPage }} / {{ totalHistoryPages }} 页</span>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()

// 表单数据
const formData = ref({
  optimization_targets: '',
  process_parameters: '',
  material_product_data: '',
  knowledge_constraints: '',
  cost_consideration: '',
  environmental_requirements: '',
  environmental_real_time_data: '',
  historical_data: '',
  expected_performance: ''
})

// 状态管理
const loading = ref(false)
const showResult = ref(false)
const streaming = ref(false)
const streamingAnswer = ref('')
const result = ref('')
const conversationId = ref('')
const messageId = ref('')
const resultTime = ref(null)
const historyList = ref([])
const historyPage = ref(1)
const historyPageSize = 6
const currentHistoryId = ref(null)
const HISTORY_STORAGE_KEY = 'process_optimization_history'
const LOCAL_TASK_STORAGE_KEY = 'smart_agent_local_tasks'
const RUNNING_STATUS_SYNC_INTERVAL_MS = 10000
let runningStatusSyncTimer = null
let isSyncing = false

const getAuthToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || ''

const totalHistoryPages = computed(() => Math.max(1, Math.ceil(historyList.value.length / historyPageSize)))
const paginatedHistoryList = computed(() => {
  const start = (historyPage.value - 1) * historyPageSize
  return historyList.value.slice(start, start + historyPageSize)
})

const historyPageNumbers = computed(() => {
  const pages = []
  for (let page = 1; page <= totalHistoryPages.value; page += 1) {
    pages.push(page)
  }
  return pages
})

const currentHistoryRecord = computed(() => {
  if (!currentHistoryId.value) return null
  return historyList.value.find((item) => item?.id === currentHistoryId.value) || null
})

const currentValidityStatus = computed({
  get() {
    return currentHistoryRecord.value ? getValidityStatus(currentHistoryRecord.value) : 'pending'
  },
  set(nextStatus) {
    updateHistoryValidity(currentHistoryId.value, nextStatus)
  }
})

const optimizationSummary = ref([
  { label: '预计良率提升', value: '+6.8%', note: '建议窗口下的估算值' },
  { label: '单位成本变化', value: '-4.2%', note: '原料与能耗综合测算' },
  { label: '工艺稳定性评分', value: 'A-', note: '基于历史波动评估' },
  { label: '中试建议优先级', value: 'P1', note: '建议优先执行验证' }
])

const processParameterRows = ref([
  { name: '反应温度', current: '720℃', recommend: '700~715℃', benefit: '副反应降低、收率提升' },
  { name: '保温时长', current: '4.0h', recommend: '3.2~3.6h', benefit: '缩短节拍并降低能耗' },
  { name: '搅拌转速', current: '320 rpm', recommend: '350~380 rpm', benefit: '混合均匀性提升' },
  { name: '进料速率', current: '1.8 kg/min', recommend: '1.5~1.6 kg/min', benefit: '减少局部过饱和' }
])

const riskChecklist = ref([
  '先做 3 批次小试验证建议窗口，比较粒径分布稳定性。',
  '对关键温控点加装校验，避免温度漂移导致质量波动。',
  '按建议速率逐步降负荷，观察是否出现结块和堵塞。',
  '同步记录能耗与良率，确认成本收益是否达到预期。'
])

// Dify API 配置 - 现在改用后端API
const API_BASE = '/api/smart-agent'

const loadDemoOptimization = () => {
  formData.value = {
    optimization_targets: '将良率提升至 96% 以上，并降低单位能耗 8% 以上',
    process_parameters: '烧结温度 1380~1500℃；保温 80~160 分钟；升温速率 2~8 ℃/min',
    material_product_data: '氧化铝陶瓷基材，初始密度 2.7 g/cm³，平均粒径 0.8 μm',
    knowledge_constraints: '温度高于 1480℃ 易引发晶粒粗化；保温过长导致能耗显著上升',
    cost_consideration: '总制造成本控制在当前基线的 95% 以内',
    environmental_requirements: '满足 RoHS 与 REACH，降低碳排放强度',
    environmental_real_time_data: '环境温度 24℃，湿度 52%，设备温控偏差 ±3℃',
    historical_data: '近 12 批次良率均值 91.8%，异常批次主要出现在高温高湿时段',
    expected_performance: '目标良率 ≥ 96%，单位能耗 ≤ 1.1 kWh/kg，质量波动降低 20%'
  }
  showResult.value = true
  streaming.value = false
  streamingAnswer.value = ''
  currentHistoryId.value = null
  result.value = '### Demo 工艺优化建议\n\n建议采用“中温区稳态 + 缩短保温 + 升温速率分段控制”的方案，以兼顾良率、能耗与工艺稳定性。\n\n- 将核心温度窗口收敛到 **1430~1460℃**，避免晶粒粗化风险。\n- 保温时长建议控制在 **95~120 分钟**，优先验证 105 分钟工况。\n- 升温速率采用“低温慢升、高温缓升”分段策略，降低热冲击。\n\n建议先进行 3 批次小试并同步记录良率、能耗和缺陷率。'
  conversationId.value = 'demo-process-optimization'
  resultTime.value = new Date()
}

const clearAll = () => {
  showResult.value = false
  streaming.value = false
  streamingAnswer.value = ''
  result.value = ''
  conversationId.value = ''
  messageId.value = ''
  currentHistoryId.value = null
  resultTime.value = null
}

// 提交表单
const submitForm = async () => {
  const inputSnapshot = { ...formData.value }
  const taskId = `process-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const taskCreatedAt = new Date()
  const createdHistory = saveToHistory({
    inputsSnapshot: inputSnapshot,
    taskId,
    taskStatus: 'pending',
    resultText: '任务已提交，正在分析工艺参数，请稍候...',
    createdAt: taskCreatedAt
  })

  upsertLocalTask({
    id: taskId,
    agent_name: '工艺优化智能体',
    title: `${(inputSnapshot.optimization_targets || '工艺优化任务').slice(0, 30)}...`,
    status: 'pending',
    category: 'process_optimization',
    created_at: taskCreatedAt.toISOString(),
    started_at: taskCreatedAt.toISOString(),
    completed_at: null,
    execution_time: 0
  })

  loading.value = true
  showResult.value = true
  streaming.value = true
  streamingAnswer.value = ''
  currentHistoryId.value = createdHistory?.id || null
  result.value = ''
  resetForm()

  try {
  const token = getAuthToken()
    // 调用后端API（流式响应）
    const response = await fetch(`${API_BASE}/process-optimization/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token
          ? { Authorization: `Bearer ${token}` }
          : {})
      },
      credentials: 'include',
      body: JSON.stringify({
        optimization_targets: inputSnapshot.optimization_targets,
        process_parameters: inputSnapshot.process_parameters,
        material_product_data: inputSnapshot.material_product_data,
        knowledge_constraints: inputSnapshot.knowledge_constraints,
        cost_consideration: inputSnapshot.cost_consideration,
        environmental_requirements: inputSnapshot.environmental_requirements,
        environmental_real_time_data: inputSnapshot.environmental_real_time_data,
        historical_data: inputSnapshot.historical_data,
        expected_performance: inputSnapshot.expected_performance,
        client_task_id: taskId
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    if (createdHistory?.id) {
      updateHistoryTaskStatus(createdHistory.id, 'running')
    }
    upsertLocalTask({
      id: taskId,
      status: 'running',
      category: 'process_optimization',
      agent_name: '工艺优化智能体'
    })
    // 处理流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        // 处理缓冲区中剩余的完整行
        buffer += ''
        let lines = buffer.split('\n')
        buffer = '' // 清空缓冲区
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))

              if (data.event === 'task_created') {
                console.log('任务已创建:', data.task_id)
                const backendTaskId = String(data.task_id || '')
                if (backendTaskId && createdHistory?.id) {
                  const target = historyList.value.find((item) => item?.id === createdHistory.id)
                  if (target) {
                    target.backend_task_id = backendTaskId
                    target.task_id = taskId
                    persistHistoryList()
                  }
                  upsertLocalTask({
                    id: taskId,
                    backend_task_id: backendTaskId,
                    category: 'process_optimization',
                    agent_name: '工艺优化智能体'
                  })
                }
              } else if (data.event === 'message' || data.event === 'agent_message') {
                if (data.answer) {
                  streamingAnswer.value += data.answer
                }
              } else if (data.event === 'message_end' || data.event === 'agent_message_end') {
                conversationId.value = data.conversation_id || ''
                messageId.value = data.id || ''
              } else if (data.event === 'agent_thought') {
                console.log('Agent 思考:', data.thought)
              } else if (data.event === 'error') {
                console.error('错误:', data.message)
                alert('处理失败: ' + (data.message || data.errors?.join(', ') || '未知错误'))
              } else if (data.event === 'done') {
                console.log('流式响应完成')
              }
            } catch (e) {
              console.error('解析JSON失败:', e)
            }
          }
        }

        streaming.value = false
        result.value = streamingAnswer.value
        resultTime.value = new Date()

        if (createdHistory?.id) {
          const target = historyList.value.find((item) => item?.id === createdHistory.id)
          if (target) {
            target.result = streamingAnswer.value
            target.conversation_id = conversationId.value
            target.task_id = taskId
          }
          updateHistoryTaskStatus(createdHistory.id, 'completed')
        }

        upsertLocalTask({
          id: taskId,
          status: 'completed',
          category: 'process_optimization',
          agent_name: '工艺优化智能体',
          completed_at: new Date().toISOString(),
          execution_time: Math.max(1, Math.round((Date.now() - taskCreatedAt.getTime()) / 1000))
        })
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      buffer += chunk
      let lines = buffer.split('\n')
      // 保留最后一行（可能是不完整的）
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.event === 'task_created') {
              console.log('任务已创建:', data.task_id)
              const backendTaskId = String(data.task_id || '')
              if (backendTaskId && createdHistory?.id) {
                const target = historyList.value.find((item) => item?.id === createdHistory.id)
                if (target) {
                  target.backend_task_id = backendTaskId
                  target.task_id = taskId
                  persistHistoryList()
                }
                upsertLocalTask({
                  id: taskId,
                  backend_task_id: backendTaskId,
                  category: 'process_optimization',
                  agent_name: '工艺优化智能体'
                })
              }
            } else if (data.event === 'message' || data.event === 'agent_message') {
              if (data.answer) {
                streamingAnswer.value += data.answer
              }
            } else if (data.event === 'message_end' || data.event === 'agent_message_end') {
              conversationId.value = data.conversation_id || ''
              messageId.value = data.id || ''
            } else if (data.event === 'agent_thought') {
              console.log('Agent 思考:', data.thought)
            } else if (data.event === 'error') {
              console.error('错误:', data.message)
              alert('处理失败: ' + (data.message || data.errors?.join(', ') || '未知错误'))
            } else if (data.event === 'done') {
              console.log('流式响应完成')
            }
          } catch (e) {
            // 只在不是空行时打印错误，避免因半包导致的误报
            if (line.trim() !== '') {
              console.error('解析JSON失败:', e, line)
            }
          }
        }
      }
    }
    }

  } catch (error) {
    console.error('请求失败:', error)
    if (createdHistory?.id) {
      updateHistoryTaskStatus(createdHistory.id, 'failed')
    }

    upsertLocalTask({
      id: taskId,
      status: 'failed',
      category: 'process_optimization',
      agent_name: '工艺优化智能体',
      completed_at: new Date().toISOString(),
      execution_time: Math.max(1, Math.round((Date.now() - taskCreatedAt.getTime()) / 1000))
    })
    alert('请求失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.value = {
    optimization_targets: '',
    process_parameters: '',
    material_product_data: '',
    knowledge_constraints: '',
    cost_consideration: '',
    environmental_requirements: '',
    environmental_real_time_data: '',
    historical_data: '',
    expected_performance: ''
  }
}

// 新建优化
const newOptimization = () => {
  showResult.value = false
  streamingAnswer.value = ''
  result.value = ''
  conversationId.value = ''
  currentHistoryId.value = null
  resetForm()
}

// 复制结果
const copyResult = () => {
  navigator.clipboard.writeText(result.value)
    .then(() => {
      alert('已复制到剪贴板')
    })
    .catch(err => {
      console.error('复制失败:', err)
    })
}

// 下载结果
const downloadResult = () => {
  const blob = new Blob([result.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `工艺优化建议_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// 保存到历史记录
const saveToHistory = ({
  inputsSnapshot = null,
  taskId = '',
  taskStatus = 'pending',
  resultText = '',
  createdAt = new Date()
} = {}) => {
  const baseInputs = inputsSnapshot ? { ...inputsSnapshot } : { ...formData.value }
  const brief = (baseInputs.optimization_targets || resultText || result.value || streamingAnswer.value || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 60)
  const historyItem = {
    id: Date.now(),
    title: `${(baseInputs.optimization_targets || '工艺优化').substring(0, 30)}...`,
    brief: brief || '未提取到工艺优化简要',
    inputs: baseInputs,
    result: resultText || result.value || streamingAnswer.value,
    conversation_id: conversationId.value,
    created_at: createdAt,
    task_id: taskId || `process-${Date.now()}`,
    task_status: taskStatus,
    validity_status: 'pending',
    is_valid_formula: false,
  }

  const history = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]')
  history.unshift(historyItem)

  // 只保留最近20条
  if (history.length > 20) {
    history.pop()
  }

  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history))
  loadHistoryList()
  currentHistoryId.value = historyItem.id
  return historyItem
}

const normalizeValidityStatus = (item, fallbackValid = false) => {
  const rawStatus = String(item?.validity_status || '').trim().toLowerCase()
  if (['pending', 'valid', 'invalid'].includes(rawStatus)) {
    return rawStatus
  }
  if (typeof item?.is_valid_formula === 'boolean') {
    return item.is_valid_formula ? 'valid' : 'pending'
  }
  return fallbackValid ? 'valid' : 'pending'
}

const getValidityStatus = (item) => normalizeValidityStatus(item)

const getValidityLabel = (item) => {
  const status = getValidityStatus(item)
  if (status === 'valid') return '有效'
  if (status === 'invalid') return '无效'
  return '待确认'
}

const normalizeBackendHistoryItem = (task) => {
  const inputData = task?.input_data || {}
  const outputData = task?.output_data || {}
  const answerText = outputData?.answer || ''
  const fallbackBrief = (inputData?.optimization_targets || task?.title || answerText || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 60)

  return {
    id: String(task?.id || `history-${Date.now()}`),
    title: task?.title || '工艺优化任务',
    brief: task?.brief_summary || fallbackBrief || '未提取到工艺优化简要',
    inputs: inputData,
    result: answerText,
    conversation_id: outputData?.conversation_id || '',
    created_at: task?.created_at || new Date().toISOString(),
    task_id: String(inputData?.client_task_id || task?.id || ''),
    backend_task_id: String(task?.id || ''),
    task_status: getTaskStatus({ task_status: task?.status }),
    validity_status: normalizeValidityStatus({ validity_status: task?.validity_status }),
    is_valid_formula: normalizeValidityStatus({ validity_status: task?.validity_status }) === 'valid',
    created_by_name: task?.created_by_name || ''
  }
}

const getTaskStatus = (item) => {
  const raw = String(item?.task_status || '').trim().toLowerCase()
  if (['pending', 'running', 'completed', 'failed'].includes(raw)) {
    return raw
  }
  return 'pending'
}

const getTaskStatusLabel = (item) => {
  const status = getTaskStatus(item)
  if (status === 'running') return '执行中'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  return '等待中'
}

const readLocalTasks = () => {
  const data = JSON.parse(localStorage.getItem(LOCAL_TASK_STORAGE_KEY) || '[]')
  return Array.isArray(data) ? data : []
}

const writeLocalTasks = (list) => {
  localStorage.setItem(LOCAL_TASK_STORAGE_KEY, JSON.stringify(Array.isArray(list) ? list : []))
}

const upsertLocalTask = (taskRecord) => {
  if (!taskRecord?.id) return
  const tasks = readLocalTasks()
  const idx = tasks.findIndex((item) => item?.id === taskRecord.id)
  if (idx >= 0) {
    tasks[idx] = { ...tasks[idx], ...taskRecord }
  } else {
    tasks.unshift(taskRecord)
  }
  writeLocalTasks(tasks.slice(0, 500))
}

const persistHistoryList = () => {
  localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(historyList.value || []))
}

// 加载历史记录列表
const loadHistoryList = async () => {
  const token = getAuthToken()
  const authHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }

  // 读取本地缓存
  const localHistory = (() => {
    try {
      const arr = JSON.parse(localStorage.getItem(HISTORY_STORAGE_KEY) || '[]')
      return Array.isArray(arr) ? arr : []
    } catch {
      return []
    }
  })()

  // 读取本地 pending/running 任务
  const localPendingRunning = localHistory.filter(
    (item) => ['pending', 'running'].includes(getTaskStatus(item))
  )

  try {
    const response = await fetch(`${API_BASE}/process-optimization/history/?limit=100`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include'
    })

    if (response.ok) {
      const payload = await response.json()
      const remoteTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
      let backendList = remoteTasks.map((task) => normalizeBackendHistoryItem(task))

      // 用 client_task_id 或 task_id 对账，合并本地 pending/running 记录
      const backendClientTaskIds = new Set(
        backendList.map((item) => String(item.inputs?.client_task_id || item.task_id || item.id))
      )
const formatMarkdown = (text) => {
  if (!text) return ''
  // 禁用 HTML 标签，防止 XSS
  const html = marked.parse(text, { mangle: false, headerIds: false, breaks: true, gfm: true, sanitize: false })
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
}
  const html = marked.parse(text, { mangle: false, headerIds: false })
  return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } })
}
            )
        ),
        ...backendList
      ]
      historyList.value = mergedList
      persistHistoryList()
      if (historyPage.value > totalHistoryPages.value) {
        historyPage.value = totalHistoryPages.value
      }
      return
    }
  } catch (error) {
    console.warn('加载后端工艺历史失败:', error)
    // 回退到本地缓存
    historyList.value = localHistory
    if (historyPage.value > totalHistoryPages.value) {
      historyPage.value = totalHistoryPages.value
    }
    return
  }
  // 如果完全失败，保留本地缓存
  historyList.value = localHistory
  if (historyPage.value > totalHistoryPages.value) {
    historyPage.value = totalHistoryPages.value
  }
}
          !backendClientIds.has(String(item.inputs?.client_task_id || item.task_id || item.id))
      )
      // 合并并去重
      const mergedList = [...localPending, ...backendList]
      historyList.value = mergedList
      persistHistoryList()
      if (historyPage.value > totalHistoryPages.value) {
        historyPage.value = totalHistoryPages.value
      }
      return
    }
  } catch (error) {
    console.warn('加载后端工艺历史失败:', error)
    // 回退到本地缓存
    historyList.value = localHistory
    if (historyPage.value > totalHistoryPages.value) {
      historyPage.value = totalHistoryPages.value
    }
    return
  }
  // 若未命中 try/catch，回退到本地缓存
  historyList.value = localHistory
  if (historyPage.value > totalHistoryPages.value) {
    historyPage.value = totalHistoryPages.value
  }
}
  try {
    const response = await fetch(`${API_BASE}/process-optimization/history/?limit=100`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include'
    })

    if (response.ok) {
      const payload = await response.json()
      const remoteTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
      remoteMapped = remoteTasks.map((task) => normalizeBackendHistoryItem(task))
    }
  } catch (error) {
    console.warn('加载后端工艺历史失败，回退本地历史:', error)
  }
const syncRunningHistoryStatus = async () => {
  if (isSyncing) return
  isSyncing = true
  try {
    const runningHistory = historyList.value.filter((item) => ['pending', 'running'].includes(getTaskStatus(item)))
    if (!runningHistory.length) return
    await loadHistoryList()
  } finally {
    isSyncing = false
  }
}
    const key = String(item?.backend_task_id || item?.id || item?.task_id || '')
    return key && !remoteKeySet.has(key)
  })

  historyList.value = [...remoteMapped, ...localOnly].sort((a, b) => {
    return new Date(b?.created_at || 0).getTime() - new Date(a?.created_at || 0).getTime()
  })
  persistHistoryList()

  if (historyPage.value > totalHistoryPages.value) {
    historyPage.value = totalHistoryPages.value
  }
}

const goToHistoryPage = (page) => {
  if (page < 1 || page > totalHistoryPages.value) return
  historyPage.value = page
}

const updateHistoryValidity = (targetId, nextStatus) => {
  if (!targetId) return
  if (!['pending', 'valid', 'invalid'].includes(nextStatus)) return
  const target = historyList.value.find((record) => record?.id === targetId)
  if (!target) return
  target.validity_status = nextStatus
  target.is_valid_formula = nextStatus === 'valid'
  persistHistoryList()

  const backendTaskId = String(target?.backend_task_id || target?.id || '').trim()
  if (!backendTaskId) return

  const token = getAuthToken()
  const authHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }

  fetch(`${API_BASE}/tasks/${backendTaskId}/`, {
    method: 'PATCH',
    headers: authHeaders,
    credentials: 'include',
    body: JSON.stringify({ validity_status: nextStatus })
  }).catch((error) => {
    console.warn('回写有效性到后端失败:', error)
  })
}

const updateHistoryTaskStatus = (targetId, nextStatus) => {
  if (!targetId || !['pending', 'running', 'completed', 'failed'].includes(nextStatus)) return
  const target = historyList.value.find((record) => record?.id === targetId)
  if (!target) return
  target.task_status = nextStatus
  persistHistoryList()
}

const openHistoryDetail = (item) => {
  if (!item) return
  currentHistoryId.value = item.id
  loadHistory(item)
}

// 加载历史记录
const loadHistory = (item) => {
  formData.value = { ...item.inputs }
  result.value = item.result
  conversationId.value = item.conversation_id
  resultTime.value = new Date(item.created_at)
  showResult.value = true
  streaming.value = false
  currentHistoryId.value = item?.id || null
}

// Markdown 格式化
const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

// 返回上一页
const goBack = () => {
  router.go(-1)
}

const syncRunningHistoryStatus = async () => {
  const runningHistory = historyList.value.filter((item) => ['pending', 'running'].includes(getTaskStatus(item)))
  if (!runningHistory.length) return
  await loadHistoryList()
}

// 组件挂载时加载历史记录
onMounted(async () => {
  await loadHistoryList()
  await syncRunningHistoryStatus()
  runningStatusSyncTimer = setInterval(() => {
    syncRunningHistoryStatus()
  }, RUNNING_STATUS_SYNC_INTERVAL_MS)
})

onUnmounted(() => {
  if (runningStatusSyncTimer) {
    clearInterval(runningStatusSyncTimer)
    runningStatusSyncTimer = null
  }
})
</script>

<style scoped>
.process-optimization-page-wrapper {
  display: flex;
  min-height: 100dvh;
  width: 100%;
}

.process-optimization-container {
  flex: 1;
  overflow-y: auto;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: clamp(12px, 2vw, 24px);
  box-sizing: border-box;
}

.page-header {
  background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(250,250,255,0.98));
  border-radius: 12px;
  padding: 16px 18px;
  margin-bottom: 18px;
  box-shadow: 0 8px 20px rgba(30,41,59,0.06);
  border: 1px solid #eef3fb;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.back-btn {
  border: 1px solid #e2e8f0;
  background: #f8fafc;
  color: #334155;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 8px;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #eef2ff;
  border-color: #c7d2fe;
}

.page-header h1 {
  margin: 0 0 6px;
  color: #0f172a;
}

.page-header p {
  margin: 0;
  color: #667085;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  border: 1px solid #d0d5dd;
  border-radius: 10px;
  background: #fff;
  color: #344054;
  padding: 8px 12px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.action-btn.secondary {
  background: #eef2ff;
  border-color: #c7d2fe;
  color: #4338ca;
}

.action-btn.ghost {
  background: #f8fafc;
}

.form-section,
.result-section,
.history-section {
  margin-bottom: 30px;
}

.form-card,
.result-card {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.form-card h2,
.result-card h2 {
  margin: 0 0 24px 0;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
}

.form-group {
  margin-bottom: 24px;
}

.base-input-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.required {
  color: #e74c3c;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.3s;
}

.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.field-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 30px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e5e5;
}

.btn-outline {
  background: white;
  color: #667eea;
  border: 1px solid #667eea;
}

.btn-outline:hover {
  background: #667eea;
  color: white;
}

.streaming-output {
  position: relative;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.stream-content,
.result-text {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
}

.result-text :deep(h1),
.result-text :deep(h2),
.result-text :deep(h3) {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #222;
}

.result-text :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
}

.result-text :deep(pre) {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.result-meta {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  font-size: 13px;
  color: #999;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.validity-select-item {
  gap: 8px;
}

.validity-select-item label {
  color: #334155;
  font-size: 13px;
}

.validity-select-item select {
  border: 1px solid #d5deee;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 13px;
  background: #fff;
  color: #1f2937;
}

.validity-select-item.disabled {
  opacity: 0.65;
}

.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.summary-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-kpi-card {
  background: linear-gradient(180deg, #f8faff 0%, #ffffff 100%);
  border: 1px solid #e2e8f7;
  border-radius: 10px;
  padding: 10px 12px;
}

.summary-kpi-label {
  font-size: 12px;
  color: #64748b;
}

.summary-kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 4px 0;
}

.summary-kpi-note {
  font-size: 12px;
  color: #94a3b8;
}

.insight-board {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
}

.insight-col {
  border: 1px solid #e8edf7;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.insight-col h3 {
  margin: 0 0 10px;
  font-size: 15px;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-wrap {
  overflow-x: auto;
}

.rich-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
}

.rich-table th,
.rich-table td {
  border-bottom: 1px solid #e9edf5;
  padding: 8px 10px;
  text-align: left;
}

.rich-table th {
  position: sticky;
  top: 0;
  background: #f4f7ff;
  color: #334155;
  font-weight: 600;
}

.rich-table tbody tr:nth-child(odd) {
  background: #fcfdff;
}

.checklist {
  margin: 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.75;
  font-size: 13px;
}

.history-section h2 {
  margin-bottom: 16px;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-table-wrap {
  overflow-x: auto;
  border: 1px solid #e8edf7;
  border-radius: 10px;
  background: #fff;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  border: 1px solid #e8edf5;
  padding: 10px;
  text-align: left;
  font-size: 13px;
  vertical-align: middle;
}

.history-table th {
  background: #f6f9ff;
  color: #334155;
  font-weight: 600;
}

.history-row {
  transition: background 0.2s;
}

.history-row:hover {
  background: #fff;
}

.history-id {
  width: 120px;
  color: #334155;
  font-weight: 600;
}

.history-brief {
  max-width: 480px;
  color: #0f172a;
}

.valid-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  user-select: none;
}

.task-status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  user-select: none;
}

.task-status-badge.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.task-status-badge.status-running {
  background: #e0f2fe;
  color: #075985;
}

.task-status-badge.status-completed {
  background: #dcfce7;
  color: #166534;
}

.task-status-badge.status-failed {
  background: #fee2e2;
  color: #991b1b;
}

.valid-badge.status-valid {
  background: #dcfce7;
  color: #166534;
}

.valid-badge.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.valid-badge.status-invalid {
  background: #fee2e2;
  color: #991b1b;
}

.history-view-btn {
  border: 1px solid #c9d8f5;
  background: #eef4ff;
  color: #1d4ed8;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.history-view-btn:hover {
  background: #dbeafe;
}

.history-pagination {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.page-btn {
  border: 1px solid #d5deee;
  background: #fff;
  color: #334155;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
}

.page-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-summary {
  margin-left: 8px;
  color: #64748b;
  font-size: 12px;
}

@media (max-width: 900px) {
  .summary-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .base-input-grid {
    grid-template-columns: 1fr;
  }

  .insight-board {
    grid-template-columns: 1fr;
  }
}
</style>