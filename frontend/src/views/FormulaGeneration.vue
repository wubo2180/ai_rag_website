<template>
  <div class="formula-generation-page-wrapper">
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
          <h1>配方生成</h1>
          <p>根据输入参数生成材料配方建议</p>
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
              {{ loading ? '分析中...' : '开始生成配方' }}
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
          <div class="result-text" v-html="formatMarkdown(result)"></div>
          
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

    <!-- 历史记录（可选） -->
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

// Dify API 配置 - 现在改用后端API
const API_BASE = '/api/smart-agent'  // 使用后端代理

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
  a.download = `产品配方生成_${new Date().toISOString().slice(0, 10)}.txt`
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
.formula-generation-page-wrapper {
  display: flex;
  height: 100vh;
}

.process-optimization-container {
  flex: 1;
  overflow-y: auto;
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
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
</style>
