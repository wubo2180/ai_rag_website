<template>
  <div class="process-optimization-page-wrapper">
    <NavigationSidebar />
    <div class="process-optimization-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="back-navigation">
        <button @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
      </div>

      <div class="header-content">
        <div class="agent-icon">
          <i class="fas fa-cogs"></i>
        </div>
        <div class="header-info">
          <h1>工艺优化</h1>
          <p>优化工艺参数，提升生产效率</p>
        </div>
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
          <div class="form-group">
            <label for="product_performance">
              <i class="fas fa-chart-line"></i>
              产品性能要求
              <span class="required">*</span>
            </label>
            <textarea
              id="product_performance"
              v-model="formData.product_performance"
              placeholder="例如：高导电性、耐高温、循环寿命>1000次"
              rows="3"
              required
            ></textarea>
            <small class="field-hint">请描述产品的核心性能指标和要求</small>
          </div>

          <div class="form-group">
            <label for="target_application_scenario">
              <i class="fas fa-bullseye"></i>
              目标应用场景
              <span class="required">*</span>
            </label>
            <textarea
              id="target_application_scenario"
              v-model="formData.target_application_scenario"
              placeholder="例如：锂电池电解质材料，用于消费电子"
              rows="3"
              required
            ></textarea>
            <small class="field-hint">请说明产品的具体应用领域和使用场景</small>
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
      <div class="history-list">
        <div
          v-for="item in historyList"
          :key="item.id"
          class="history-item"
          @click="loadHistory(item)"
        >
          <div class="history-info">
            <div class="history-title">{{ item.title }}</div>
            <div class="history-date">{{ formatDate(item.created_at) }}</div>
          </div>
          <i class="fas fa-chevron-right"></i>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { marked } from 'marked'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()

// 表单数据
const formData = ref({
  product_performance: '',
  target_application_scenario: '',
  cost_consideration: '',
  environmental_requirements: ''
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

// 提交表单
const submitForm = async () => {
  loading.value = true
  showResult.value = true
  streaming.value = true
  streamingAnswer.value = ''
  result.value = ''

  try {
    // 调用后端API（流式响应）
    const response = await fetch(`${API_BASE}/process-optimization/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // 如果需要认证，添加token
        // 'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        product_performance: formData.value.product_performance,
        target_application_scenario: formData.value.target_application_scenario,
        cost_consideration: formData.value.cost_consideration,
        environmental_requirements: formData.value.environmental_requirements
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 处理流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()

      if (done) {
        streaming.value = false
        result.value = streamingAnswer.value
        resultTime.value = new Date()
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.event === 'task_created') {
              console.log('任务已创建:', data.task_id)
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
    }

    // 保存到历史记录
    saveToHistory()

  } catch (error) {
    console.error('请求失败:', error)
    alert('请求失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.value = {
    product_performance: '',
    target_application_scenario: '',
    cost_consideration: '',
    environmental_requirements: ''
  }
}

// 新建优化
const newOptimization = () => {
  showResult.value = false
  streamingAnswer.value = ''
  result.value = ''
  conversationId.value = ''
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
const saveToHistory = () => {
  const historyItem = {
    id: Date.now(),
    title: `${formData.value.target_application_scenario.substring(0, 30)}...`,
    inputs: { ...formData.value },
    result: streamingAnswer.value,
    conversation_id: conversationId.value,
    created_at: new Date()
  }

  const history = JSON.parse(localStorage.getItem('optimization_history') || '[]')
  history.unshift(historyItem)

  // 只保留最近20条
  if (history.length > 20) {
    history.pop()
  }

  localStorage.setItem('optimization_history', JSON.stringify(history))
  loadHistoryList()
}

// 加载历史记录列表
const loadHistoryList = () => {
  const history = JSON.parse(localStorage.getItem('optimization_history') || '[]')
  historyList.value = history
}

// 加载历史记录
const loadHistory = (item) => {
  formData.value = { ...item.inputs }
  result.value = item.result
  conversationId.value = item.conversation_id
  resultTime.value = new Date(item.created_at)
  showResult.value = true
  streaming.value = false
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

// 组件挂载时加载历史记录
onMounted(() => {
  loadHistoryList()
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
  margin-bottom: 30px;
}

.back-navigation {
  margin-bottom: 20px;
}

.back-btn {
  background: none;
  border: none;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 4px;
  transition: all 0.3s;
}

.back-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 30px;
  border-radius: 12px;
  color: white;
}

.agent-icon {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}

.header-info h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 600;
}

.header-info p {
  margin: 0;
  opacity: 0.9;
  font-size: 16px;
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

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.history-item:hover {
  transform: translateX(4px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.history-info {
  flex: 1;
}

.history-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.history-date {
  font-size: 12px;
  color: #999;
}

.history-item i {
  color: #ccc;
}

@media (max-width: 900px) {
  .summary-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .insight-board {
    grid-template-columns: 1fr;
  }
}
</style>