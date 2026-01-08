<template><template>

  <div class="process-optimization-page-wrapper">  <div class="process-optimization-container">

    <NavigationSidebar />    <!-- 页面头部 -->

    <div class="process-optimization-container">    <div class="page-header">

      <!-- 页面头部 -->      <div class="back-navigation">

      <div class="page-header">        <button @click="goBack" class="back-btn">

        <div class="back-navigation">          <i class="fas fa-arrow-left"></i>

          <button @click="goBack" class="back-btn">          返回

            <i class="fas fa-arrow-left"></i>        </button>

            返回      </div>

          </button>      

        </div>      <div class="header-content">

                <div class="agent-icon">

        <div class="header-content">          <i class="fas fa-cogs"></i>

          <div class="agent-icon">        </div>

            <i class="fas fa-cog"></i>        <div class="header-info">

          </div>          <h1>工艺优化</h1>

          <div class="header-info">          <p>优化工艺参数，提升生产效率</p>

            <h1>工艺优化智能体</h1>        </div>

            <p>基于多维数据分析,提供智能化的工艺参数优化建议</p>      </div>

          </div>    </div>

        </div>

      </div>    <!-- 输入表单 -->

    <div class="form-section">

      <!-- 输入表单 -->      <div class="form-card">

      <div class="form-section">        <h2>

        <div class="form-card">          <i class="fas fa-edit"></i>

          <h2>          输入参数

            <i class="fas fa-edit"></i>        </h2>

            输入参数        

          </h2>        <form @submit.prevent="submitForm">

                    <div class="form-group">

          <form @submit.prevent="submitForm">            <label for="product_performance">

            <div class="form-group">              <i class="fas fa-chart-line"></i>

              <label for="optimization_targets">              产品性能要求

                <i class="fas fa-bullseye"></i>              <span class="required">*</span>

                优化目标            </label>

                <span class="required">*</span>            <textarea

              </label>              id="product_performance"

              <textarea              v-model="formData.product_performance"

                id="optimization_targets"              placeholder="例如：高导电性、耐高温、循环寿命>1000次"

                v-model="formData.optimization_targets"              rows="3"

                placeholder="例如:提高产品良率、降低能耗、缩短生产周期"              required

                rows="3"            ></textarea>

                required            <small class="field-hint">请描述产品的核心性能指标和要求</small>

              ></textarea>          </div>

              <small class="field-hint">请描述您希望达成的优化目标</small>

            </div>          <div class="form-group">

            <label for="target_application_scenario">

            <div class="form-group">              <i class="fas fa-bullseye"></i>

              <label for="process_parameters">              目标应用场景

                <i class="fas fa-sliders-h"></i>              <span class="required">*</span>

                工艺参数            </label>

                <span class="required">*</span>            <textarea

              </label>              id="target_application_scenario"

              <textarea              v-model="formData.target_application_scenario"

                id="process_parameters"              placeholder="例如：锂电池电解质材料，用于消费电子"

                v-model="formData.process_parameters"              rows="3"

                placeholder="例如:温度范围180-220°C、压力0.5-1.0MPa、反应时间2-4小时"              required

                rows="3"            ></textarea>

                required            <small class="field-hint">请说明产品的具体应用领域和使用场景</small>

              ></textarea>          </div>

              <small class="field-hint">请提供当前的工艺参数范围</small>

            </div>          <div class="form-group">

            <label for="cost_consideration">

            <div class="form-group">              <i class="fas fa-dollar-sign"></i>

              <label for="material_product_data">              成本考量

                <i class="fas fa-cube"></i>              <span class="required">*</span>

                材料与产品数据            </label>

                <span class="required">*</span>            <textarea

              </label>              id="cost_consideration"

              <textarea              v-model="formData.cost_consideration"

                id="material_product_data"              placeholder="例如：单公斤成本控制在 200 元以内"

                v-model="formData.material_product_data"              rows="2"

                placeholder="例如:原材料成分、产品规格、关键性能指标"              required

                rows="3"            ></textarea>

                required            <small class="field-hint">请明确成本预算和控制要求</small>

              ></textarea>          </div>

              <small class="field-hint">请说明材料特性和产品要求</small>

            </div>          <div class="form-group">

            <label for="environmental_requirements">

            <div class="form-group">              <i class="fas fa-leaf"></i>

              <label for="environmental_real_time_data">              环保要求

                <i class="fas fa-thermometer-half"></i>              <span class="required">*</span>

                环境与实时数据            </label>

                <span class="required">*</span>            <textarea

              </label>              id="environmental_requirements"

              <textarea              v-model="formData.environmental_requirements"

                id="environmental_real_time_data"              placeholder="例如：符合 RoHS/REACH，无卤、低VOC 排放"

                v-model="formData.environmental_real_time_data"              rows="2"

                placeholder="例如:车间温湿度、设备状态、生产批次数据"              required

                rows="2"            ></textarea>

                required            <small class="field-hint">请说明环保标准和合规要求</small>

              ></textarea>          </div>

              <small class="field-hint">请提供环境条件和实时监测数据</small>

            </div>          <div class="form-actions">

            <button 

            <div class="form-group">              type="button" 

              <label for="knowledge_constraints">              class="btn btn-secondary"

                <i class="fas fa-book"></i>              @click="resetForm"

                知识与约束              :disabled="loading"

                <span class="required">*</span>            >

              </label>              <i class="fas fa-redo"></i>

              <textarea              重置

                id="knowledge_constraints"            </button>

                v-model="formData.knowledge_constraints"            <button 

                placeholder="例如:行业标准、安全规范、设备限制"              type="submit" 

                rows="2"              class="btn btn-primary"

                required              :disabled="loading"

              ></textarea>            >

              <small class="field-hint">请说明需要遵守的约束条件</small>              <i class="fas fa-paper-plane" v-if="!loading"></i>

            </div>              <i class="fas fa-spinner fa-spin" v-else></i>

              {{ loading ? '分析中...' : '开始优化' }}

            <div class="form-group">            </button>

              <label for="historical_data">          </div>

                <i class="fas fa-history"></i>        </form>

                历史数据      </div>

                <span class="required">*</span>    </div>

              </label>

              <textarea    <!-- 结果显示区域 -->

                id="historical_data"    <div v-if="showResult" class="result-section">

                v-model="formData.historical_data"      <div class="result-card">

                placeholder="例如:过往批次的工艺参数和结果、问题记录"        <h2>

                rows="2"          <i class="fas fa-lightbulb"></i>

                required          优化建议

              ></textarea>        </h2>

              <small class="field-hint">请提供历史生产数据作为参考</small>        

            </div>        <!-- 流式输出显示 -->

        <div v-if="streaming" class="streaming-output">

            <div class="form-group">          <div class="typing-indicator">

              <label for="cost_consideration">            <span></span>

                <i class="fas fa-dollar-sign"></i>            <span></span>

                所需成本            <span></span>

                <span class="required">*</span>          </div>

              </label>          <div class="stream-content" v-html="formatMarkdown(streamingAnswer)"></div>

              <textarea        </div>

                id="cost_consideration"

                v-model="formData.cost_consideration"        <!-- 完整结果显示 -->

                placeholder="例如:预算限制、成本控制目标"        <div v-else class="result-content">

                rows="2"          <div class="result-text" v-html="formatMarkdown(result)"></div>

                required          

              ></textarea>          <div class="result-meta">

              <small class="field-hint">请明确成本预算和控制要求</small>            <div class="meta-item">

            </div>              <i class="fas fa-clock"></i>

              <span>{{ formatDate(resultTime) }}</span>

            <div class="form-group">            </div>

              <label for="environmental_requirements">            <div class="meta-item">

                <i class="fas fa-leaf"></i>              <i class="fas fa-comment"></i>

                环保要求              <span>会话 ID: {{ conversationId }}</span>

                <span class="required">*</span>            </div>

              </label>          </div>

              <textarea

                id="environmental_requirements"          <div class="result-actions">

                v-model="formData.environmental_requirements"            <button 

                placeholder="例如:排放标准、废弃物处理要求、环保认证"              class="btn btn-outline"

                rows="2"              @click="copyResult"

                required            >

              ></textarea>              <i class="fas fa-copy"></i>

              <small class="field-hint">请说明环保标准和合规要求</small>              复制结果

            </div>            </button>

            <button 

            <div class="form-group">              class="btn btn-outline"

              <label for="expected_performance">              @click="downloadResult"

                <i class="fas fa-chart-line"></i>            >

                期待性能提升              <i class="fas fa-download"></i>

                <span class="required">*</span>              下载报告

              </label>            </button>

              <textarea            <button 

                id="expected_performance"              class="btn btn-primary"

                v-model="formData.expected_performance"              @click="newOptimization"

                placeholder="例如:良率提升10%、能耗降低15%、周期缩短20%"            >

                rows="2"              <i class="fas fa-plus"></i>

                required              新建优化

              ></textarea>            </button>

              <small class="field-hint">请描述期望达到的性能改进目标</small>          </div>

            </div>        </div>

      </div>

            <div class="form-actions">    </div>

              <button 

                type="button"     <!-- 历史记录（可选） -->

                class="btn btn-secondary"    <div v-if="historyList.length > 0" class="history-section">

                @click="resetForm"      <h2>

                :disabled="loading"        <i class="fas fa-history"></i>

              >        历史记录

                <i class="fas fa-redo"></i>      </h2>

                重置      <div class="history-list">

              </button>        <div 

              <button           v-for="item in historyList" 

                type="submit"           :key="item.id"

                class="btn btn-primary"          class="history-item"

                :disabled="loading"          @click="loadHistory(item)"

              >        >

                <i class="fas fa-paper-plane" v-if="!loading"></i>          <div class="history-info">

                <i class="fas fa-spinner fa-spin" v-else></i>            <div class="history-title">{{ item.title }}</div>

                {{ loading ? '分析中...' : '开始优化分析' }}            <div class="history-date">{{ formatDate(item.created_at) }}</div>

              </button>          </div>

            </div>          <i class="fas fa-chevron-right"></i>

          </form>        </div>

        </div>      </div>

      </div>    </div>

  </div>

      <!-- 结果显示区域 --></template>

      <div v-if="showResult" class="result-section">

        <div class="result-card"><script setup>

          <h2>import { ref, onMounted } from 'vue'

            <i class="fas fa-lightbulb"></i>import { useRouter } from 'vue-router'

            优化建议import axios from 'axios'

          </h2>import { marked } from 'marked'

          

          <!-- 流式输出显示 -->const router = useRouter()

          <div v-if="streaming" class="streaming-output">

            <div class="typing-indicator">// 表单数据

              <span></span>const formData = ref({

              <span></span>  product_performance: '',

              <span></span>  target_application_scenario: '',

            </div>  cost_consideration: '',

            <div class="stream-content" v-html="formatMarkdown(streamingAnswer)"></div>  environmental_requirements: ''

          </div>})



          <!-- 完整结果显示 -->// 状态管理

          <div v-else class="result-content">const loading = ref(false)

            <div class="result-text" v-html="formatMarkdown(result)"></div>const showResult = ref(false)

            const streaming = ref(false)

            <div class="result-meta">const streamingAnswer = ref('')

              <div class="meta-item">const result = ref('')

                <i class="fas fa-clock"></i>const conversationId = ref('')

                <span>{{ formatDate(resultTime) }}</span>const messageId = ref('')

              </div>const resultTime = ref(null)

              <div class="meta-item" v-if="conversationId">const historyList = ref([])

                <i class="fas fa-comment"></i>

                <span>会话 ID: {{ conversationId }}</span>// Dify API 配置 - 现在改用后端API

              </div>const API_BASE = '/api/smart-agent'  // 使用后端代理

            </div>

// 提交表单

            <div class="result-actions">const submitForm = async () => {

              <button   loading.value = true

                class="btn btn-outline"  showResult.value = true

                @click="copyResult"  streaming.value = true

              >  streamingAnswer.value = ''

                <i class="fas fa-copy"></i>  result.value = ''

                复制结果  

              </button>  try {

              <button     // 调用后端API（流式响应）

                class="btn btn-outline"    const response = await fetch(`${API_BASE}/process-optimization/stream/`, {

                @click="downloadResult"      method: 'POST',

              >      headers: {

                <i class="fas fa-download"></i>        'Content-Type': 'application/json',

                下载报告        // 如果需要认证，添加token

              </button>        // 'Authorization': `Bearer ${localStorage.getItem('token')}`

              <button       },

                class="btn btn-primary"      body: JSON.stringify({

                @click="newOptimization"        product_performance: formData.value.product_performance,

              >        target_application_scenario: formData.value.target_application_scenario,

                <i class="fas fa-plus"></i>        cost_consideration: formData.value.cost_consideration,

                新建优化        environmental_requirements: formData.value.environmental_requirements

              </button>      })

            </div>    })

          </div>

        </div>    if (!response.ok) {

      </div>      throw new Error(`HTTP error! status: ${response.status}`)

    }

      <!-- 历史记录 -->

      <div v-if="historyList.length > 0" class="history-section">    // 处理流式响应

        <h2>    const reader = response.body.getReader()

          <i class="fas fa-history"></i>    const decoder = new TextDecoder()

          历史记录

        </h2>    while (true) {

        <div class="history-list">      const { done, value } = await reader.read()

          <div       

            v-for="item in historyList"       if (done) {

            :key="item.id"        streaming.value = false

            class="history-item"        result.value = streamingAnswer.value

            @click="loadHistory(item)"        resultTime.value = new Date()

          >        break

            <div class="history-info">      }

              <div class="history-title">{{ item.title }}</div>

              <div class="history-date">{{ formatDate(item.created_at) }}</div>      const chunk = decoder.decode(value, { stream: true })

            </div>      const lines = chunk.split('\n')

            <i class="fas fa-chevron-right"></i>

          </div>      for (const line of lines) {

        </div>        if (line.startsWith('data: ')) {

      </div>          try {

    </div>            const data = JSON.parse(line.slice(6))

  </div>            

</template>            if (data.event === 'task_created') {

              console.log('任务已创建:', data.task_id)

<script setup>            } else if (data.event === 'message' || data.event === 'agent_message') {

import { ref, onMounted } from 'vue'              if (data.answer) {

import { useRouter } from 'vue-router'                streamingAnswer.value += data.answer

import { marked } from 'marked'              }

import NavigationSidebar from '@/components/NavigationSidebar.vue'            } else if (data.event === 'message_end' || data.event === 'agent_message_end') {

              conversationId.value = data.conversation_id || ''

const router = useRouter()              messageId.value = data.id || ''

            } else if (data.event === 'agent_thought') {

// 表单数据              console.log('Agent 思考:', data.thought)

const formData = ref({            } else if (data.event === 'error') {

  optimization_targets: '',              console.error('错误:', data.message)

  process_parameters: '',              alert('处理失败: ' + (data.message || data.errors?.join(', ') || '未知错误'))

  material_product_data: '',            } else if (data.event === 'done') {

  environmental_real_time_data: '',              console.log('流式响应完成')

  knowledge_constraints: '',            }

  historical_data: '',          } catch (e) {

  cost_consideration: '',            console.error('解析JSON失败:', e)

  environmental_requirements: '',          }

  expected_performance: ''        }

})      }

    }

// 状态管理

const loading = ref(false)    // 保存到历史记录

const showResult = ref(false)    saveToHistory()

const streaming = ref(false)

const streamingAnswer = ref('')  } catch (error) {

const result = ref('')    console.error('请求失败:', error)

const conversationId = ref('')    alert('请求失败: ' + error.message)

const messageId = ref('')  } finally {

const resultTime = ref(null)    loading.value = false

const historyList = ref([])  }

}

// API配置

const API_BASE = '/api/smart-agent'// 重置表单

const resetForm = () => {

// 提交表单  formData.value = {

const submitForm = async () => {    product_performance: '',

  loading.value = true    target_application_scenario: '',

  showResult.value = true    cost_consideration: '',

  streaming.value = true    environmental_requirements: ''

  streamingAnswer.value = ''  }

  result.value = ''}

  

  try {// 新建优化

    // 调用后端API（流式响应）const newOptimization = () => {

    const response = await fetch(`${API_BASE}/process-optimization/stream/`, {  showResult.value = false

      method: 'POST',  streamingAnswer.value = ''

      headers: {  result.value = ''

        'Content-Type': 'application/json',  conversationId.value = ''

      },  resetForm()

      body: JSON.stringify(formData.value)}

    })

// 复制结果

    if (!response.ok) {const copyResult = () => {

      throw new Error(`HTTP error! status: ${response.status}`)  navigator.clipboard.writeText(result.value)

    }    .then(() => {

      alert('已复制到剪贴板')

    // 处理流式响应    })

    const reader = response.body.getReader()    .catch(err => {

    const decoder = new TextDecoder()      console.error('复制失败:', err)

    })

    while (true) {}

      const { done, value } = await reader.read()

      // 下载结果

      if (done) {const downloadResult = () => {

        streaming.value = false  const blob = new Blob([result.value], { type: 'text/plain;charset=utf-8' })

        result.value = streamingAnswer.value  const url = URL.createObjectURL(blob)

        resultTime.value = new Date()  const a = document.createElement('a')

        break  a.href = url

      }  a.download = `工艺优化建议_${new Date().toISOString().slice(0, 10)}.txt`

  a.click()

      const chunk = decoder.decode(value, { stream: true })  URL.revokeObjectURL(url)

      const lines = chunk.split('\n')}



      for (const line of lines) {// 保存到历史记录

        if (line.startsWith('data: ')) {const saveToHistory = () => {

          try {  const historyItem = {

            const data = JSON.parse(line.slice(6))    id: Date.now(),

                title: `${formData.value.target_application_scenario.substring(0, 30)}...`,

            if (data.event === 'task_created') {    inputs: { ...formData.value },

              console.log('任务已创建:', data.task_id)    result: streamingAnswer.value,

            } else if (data.event === 'message' || data.event === 'agent_message') {    conversation_id: conversationId.value,

              if (data.answer) {    created_at: new Date()

                streamingAnswer.value += data.answer  }

              }  

            } else if (data.event === 'message_end' || data.event === 'agent_message_end') {  const history = JSON.parse(localStorage.getItem('optimization_history') || '[]')

              conversationId.value = data.conversation_id || ''  history.unshift(historyItem)

              messageId.value = data.id || ''  

            } else if (data.event === 'agent_thought') {  // 只保留最近20条

              console.log('Agent 思考:', data.thought)  if (history.length > 20) {

            } else if (data.event === 'error') {    history.pop()

              console.error('错误:', data.message)  }

              alert('处理失败: ' + (data.message || data.errors?.join(', ') || '未知错误'))  

            } else if (data.event === 'done') {  localStorage.setItem('optimization_history', JSON.stringify(history))

              console.log('流式响应完成')  loadHistoryList()

            }}

          } catch (e) {

            console.error('解析JSON失败:', e)// 加载历史记录列表

          }const loadHistoryList = () => {

        }  const history = JSON.parse(localStorage.getItem('optimization_history') || '[]')

      }  historyList.value = history

    }}



    // 保存到历史记录// 加载历史记录

    saveToHistory()const loadHistory = (item) => {

  formData.value = { ...item.inputs }

  } catch (error) {  result.value = item.result

    console.error('请求失败:', error)  conversationId.value = item.conversation_id

    alert('请求失败: ' + error.message)  resultTime.value = new Date(item.created_at)

  } finally {  showResult.value = true

    loading.value = false  streaming.value = false

  }}

}

// Markdown 格式化

// 重置表单const formatMarkdown = (text) => {

const resetForm = () => {  if (!text) return ''

  formData.value = {  return marked(text)

    optimization_targets: '',}

    process_parameters: '',

    material_product_data: '',// 格式化日期

    environmental_real_time_data: '',const formatDate = (date) => {

    knowledge_constraints: '',  if (!date) return ''

    historical_data: '',  const d = new Date(date)

    cost_consideration: '',  return d.toLocaleString('zh-CN')

    environmental_requirements: '',}

    expected_performance: ''

  }// 返回上一页

}const goBack = () => {

  router.go(-1)

// 新建优化}

const newOptimization = () => {

  showResult.value = false// 组件挂载时加载历史记录

  streamingAnswer.value = ''onMounted(() => {

  result.value = ''  loadHistoryList()

  conversationId.value = ''})

  resetForm()</script>

}

<style scoped>

// 复制结果.process-optimization-container {

const copyResult = () => {  max-width: 1200px;

  navigator.clipboard.writeText(result.value)  margin: 0 auto;

    .then(() => {  padding: 20px;

      alert('已复制到剪贴板')}

    })

    .catch(err => {.page-header {

      console.error('复制失败:', err)  margin-bottom: 30px;

    })}

}

.back-navigation {

// 下载结果  margin-bottom: 20px;

const downloadResult = () => {}

  const blob = new Blob([result.value], { type: 'text/plain;charset=utf-8' })

  const url = URL.createObjectURL(blob).back-btn {

  const a = document.createElement('a')  background: none;

  a.href = url  border: none;

  a.download = `工艺优化报告_${new Date().toISOString().slice(0, 10)}.txt`  color: #666;

  a.click()  font-size: 14px;

  URL.revokeObjectURL(url)  cursor: pointer;

}  display: flex;

  align-items: center;

// 保存到历史记录  gap: 8px;

const saveToHistory = () => {  padding: 8px 12px;

  const historyItem = {  border-radius: 4px;

    id: Date.now(),  transition: all 0.3s;

    title: `${formData.value.optimization_targets.substring(0, 30)}...`,}

    inputs: { ...formData.value },

    result: streamingAnswer.value,.back-btn:hover {

    conversation_id: conversationId.value,  background: #f5f5f5;

    created_at: new Date()  color: #333;

  }}

  

  const history = JSON.parse(localStorage.getItem('process_optimization_history') || '[]').header-content {

  history.unshift(historyItem)  display: flex;

    align-items: center;

  // 只保留最近20条  gap: 20px;

  if (history.length > 20) {  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

    history.pop()  padding: 30px;

  }  border-radius: 12px;

    color: white;

  localStorage.setItem('process_optimization_history', JSON.stringify(history))}

  loadHistoryList()

}.agent-icon {

  width: 80px;

// 加载历史记录列表  height: 80px;

const loadHistoryList = () => {  background: rgba(255, 255, 255, 0.2);

  const history = JSON.parse(localStorage.getItem('process_optimization_history') || '[]')  border-radius: 50%;

  historyList.value = history  display: flex;

}  align-items: center;

  justify-content: center;

// 加载历史记录  font-size: 36px;

const loadHistory = (item) => {}

  formData.value = { ...item.inputs }

  result.value = item.result.header-info h1 {

  conversationId.value = item.conversation_id  margin: 0 0 8px 0;

  resultTime.value = new Date(item.created_at)  font-size: 32px;

  showResult.value = true  font-weight: 600;

  streaming.value = false}

}

.header-info p {

// Markdown格式化  margin: 0;

const formatMarkdown = (text) => {  opacity: 0.9;

  if (!text) return ''  font-size: 16px;

  return marked(text)}

}

.form-section,

// 格式化日期.result-section,

const formatDate = (date) => {.history-section {

  if (!date) return ''  margin-bottom: 30px;

  const d = new Date(date)}

  return d.toLocaleString('zh-CN')

}.form-card,

.result-card {

// 返回上一页  background: white;

const goBack = () => {  border-radius: 12px;

  router.go(-1)  padding: 30px;

}  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);

}

// 组件挂载时加载历史记录

onMounted(() => {.form-card h2,

  loadHistoryList().result-card h2 {

})  margin: 0 0 24px 0;

</script>  font-size: 20px;

  font-weight: 600;

<style scoped>  display: flex;

.process-optimization-page-wrapper {  align-items: center;

  display: flex;  gap: 10px;

  height: 100vh;  color: #333;

}}



.process-optimization-container {.form-group {

  flex: 1;  margin-bottom: 24px;

  overflow-y: auto;}

  max-width: 1200px;

  margin: 0 auto;.form-group label {

  padding: 20px;  display: flex;

}  align-items: center;

  gap: 8px;

.page-header {  margin-bottom: 8px;

  margin-bottom: 30px;  font-weight: 500;

}  color: #555;

}

.back-navigation {

  margin-bottom: 20px;.required {

}  color: #e74c3c;

}

.back-btn {

  background: none;.form-group textarea {

  border: none;  width: 100%;

  color: #666;  padding: 12px;

  font-size: 14px;  border: 1px solid #ddd;

  cursor: pointer;  border-radius: 8px;

  display: flex;  font-size: 14px;

  align-items: center;  font-family: inherit;

  gap: 8px;  resize: vertical;

  padding: 8px 12px;  transition: all 0.3s;

  border-radius: 4px;}

  transition: all 0.3s;

}.form-group textarea:focus {

  outline: none;

.back-btn:hover {  border-color: #667eea;

  background: #f5f5f5;  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);

  color: #333;}

}

.field-hint {

.header-content {  display: block;

  display: flex;  margin-top: 4px;

  align-items: center;  font-size: 12px;

  gap: 20px;  color: #999;

  background: linear-gradient(135deg, #20bf6b 0%, #26de81 100%);}

  padding: 30px;

  border-radius: 12px;.form-actions {

  color: white;  display: flex;

}  gap: 12px;

  justify-content: flex-end;

.agent-icon {  margin-top: 30px;

  width: 80px;}

  height: 80px;

  background: rgba(255, 255, 255, 0.2);.btn {

  border-radius: 50%;  padding: 12px 24px;

  display: flex;  border: none;

  align-items: center;  border-radius: 8px;

  justify-content: center;  font-size: 14px;

  font-size: 36px;  font-weight: 500;

}  cursor: pointer;

  display: inline-flex;

.header-info h1 {  align-items: center;

  margin: 0 0 8px 0;  gap: 8px;

  font-size: 32px;  transition: all 0.3s;

  font-weight: 600;}

}

.btn:disabled {

.header-info p {  opacity: 0.6;

  margin: 0;  cursor: not-allowed;

  opacity: 0.9;}

  font-size: 16px;

}.btn-primary {

  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

.form-section,  color: white;

.result-section,}

.history-section {

  margin-bottom: 30px;.btn-primary:hover:not(:disabled) {

}  transform: translateY(-2px);

  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);

.form-card,}

.result-card {

  background: white;.btn-secondary {

  border-radius: 12px;  background: #f5f5f5;

  padding: 30px;  color: #666;

  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);}

}

.btn-secondary:hover:not(:disabled) {

.form-card h2,  background: #e5e5e5;

.result-card h2 {}

  margin: 0 0 24px 0;

  font-size: 20px;.btn-outline {

  font-weight: 600;  background: white;

  display: flex;  color: #667eea;

  align-items: center;  border: 1px solid #667eea;

  gap: 10px;}

  color: #333;

}.btn-outline:hover {

  background: #667eea;

.form-group {  color: white;

  margin-bottom: 24px;}

}

.streaming-output {

.form-group label {  position: relative;

  display: flex;}

  align-items: center;

  gap: 8px;.typing-indicator {

  margin-bottom: 8px;  display: inline-flex;

  font-weight: 500;  align-items: center;

  color: #555;  gap: 4px;

}  margin-bottom: 12px;

}

.required {

  color: #e74c3c;.typing-indicator span {

}  width: 8px;

  height: 8px;

.form-group textarea {  background: #667eea;

  width: 100%;  border-radius: 50%;

  padding: 12px;  animation: typing 1.4s infinite;

  border: 1px solid #ddd;}

  border-radius: 8px;

  font-size: 14px;.typing-indicator span:nth-child(2) {

  font-family: inherit;  animation-delay: 0.2s;

  resize: vertical;}

  transition: all 0.3s;

}.typing-indicator span:nth-child(3) {

  animation-delay: 0.4s;

.form-group textarea:focus {}

  outline: none;

  border-color: #20bf6b;@keyframes typing {

  box-shadow: 0 0 0 3px rgba(32, 191, 107, 0.1);  0%, 60%, 100% {

}    transform: translateY(0);

  }

.field-hint {  30% {

  display: block;    transform: translateY(-10px);

  margin-top: 4px;  }

  font-size: 12px;}

  color: #999;

}.stream-content,

.result-text {

.form-actions {  line-height: 1.8;

  display: flex;  color: #333;

  gap: 12px;  font-size: 15px;

  justify-content: flex-end;}

  margin-top: 30px;

}.result-text :deep(h1),

.result-text :deep(h2),

.btn {.result-text :deep(h3) {

  padding: 12px 24px;  margin-top: 20px;

  border: none;  margin-bottom: 10px;

  border-radius: 8px;  color: #222;

  font-size: 14px;}

  font-weight: 500;

  cursor: pointer;.result-text :deep(code) {

  display: inline-flex;  background: #f5f5f5;

  align-items: center;  padding: 2px 6px;

  gap: 8px;  border-radius: 4px;

  transition: all 0.3s;  font-family: 'Consolas', monospace;

}}



.btn:disabled {.result-text :deep(pre) {

  opacity: 0.6;  background: #f5f5f5;

  cursor: not-allowed;  padding: 16px;

}  border-radius: 8px;

  overflow-x: auto;

.btn-primary {}

  background: linear-gradient(135deg, #20bf6b 0%, #26de81 100%);

  color: white;.result-meta {

}  display: flex;

  gap: 20px;

.btn-primary:hover:not(:disabled) {  margin-top: 20px;

  transform: translateY(-2px);  padding-top: 20px;

  box-shadow: 0 4px 12px rgba(32, 191, 107, 0.4);  border-top: 1px solid #eee;

}  font-size: 13px;

  color: #999;

.btn-secondary {}

  background: #f5f5f5;

  color: #666;.meta-item {

}  display: flex;

  align-items: center;

.btn-secondary:hover:not(:disabled) {  gap: 6px;

  background: #e5e5e5;}

}

.result-actions {

.btn-outline {  display: flex;

  background: white;  gap: 12px;

  color: #20bf6b;  margin-top: 20px;

  border: 1px solid #20bf6b;}

}

.history-section h2 {

.btn-outline:hover {  margin-bottom: 16px;

  background: #20bf6b;  font-size: 18px;

  color: white;  display: flex;

}  align-items: center;

  gap: 8px;

.streaming-output {}

  position: relative;

}.history-list {

  display: grid;

.typing-indicator {  gap: 12px;

  display: inline-flex;}

  align-items: center;

  gap: 4px;.history-item {

  margin-bottom: 12px;  background: white;

}  border-radius: 8px;

  padding: 16px;

.typing-indicator span {  display: flex;

  width: 8px;  align-items: center;

  height: 8px;  justify-content: space-between;

  background: #20bf6b;  cursor: pointer;

  border-radius: 50%;  transition: all 0.3s;

  animation: typing 1.4s infinite;  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);

}}



.typing-indicator span:nth-child(2) {.history-item:hover {

  animation-delay: 0.2s;  transform: translateX(4px);

}  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);

}

.typing-indicator span:nth-child(3) {

  animation-delay: 0.4s;.history-info {

}  flex: 1;

}

@keyframes typing {

  0%, 60%, 100% {.history-title {

    transform: translateY(0);  font-weight: 500;

  }  color: #333;

  30% {  margin-bottom: 4px;

    transform: translateY(-10px);}

  }

}.history-date {

  font-size: 12px;

.stream-content,  color: #999;

.result-text {}

  line-height: 1.8;

  color: #333;.history-item i {

  font-size: 15px;  color: #ccc;

}}

</style>

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
