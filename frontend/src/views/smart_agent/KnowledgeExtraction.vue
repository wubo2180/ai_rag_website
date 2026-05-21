<template>
  <div class="knowledge-extraction-page-wrapper">
    <NavigationSidebar />
    <div class="knowledge-extraction-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="back-navigation">
        <button @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
      </div>
      <div class="header-content">
        <h1 class="page-title">
          <i class="fas fa-book-open"></i>
          知识抽取智能体
        </h1>
        <p class="page-description">
          从文档中智能提取结构化知识，支持PDF、Word、文本等多种格式
        </p>

        <div class="header-tags">
          <span class="tag-item"><i class="fas fa-file-alt"></i> 多格式解析</span>
          <span class="tag-item"><i class="fas fa-table"></i> 结构化表格</span>
          <span class="tag-item"><i class="fas fa-sitemap"></i> 图谱友好</span>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <div class="overview-strip">
        <div class="overview-card" v-for="item in overviewCards" :key="item.title">
          <div class="overview-icon"><i :class="item.icon"></i></div>
          <div class="overview-body">
            <div class="overview-title">{{ item.title }}</div>
            <div class="overview-desc">{{ item.desc }}</div>
          </div>
        </div>
      </div>

      <div class="workflow-strip">
        <div class="workflow-item" v-for="(step, idx) in workflowSteps" :key="step.title">
          <div class="workflow-index">{{ idx + 1 }}</div>
          <div class="workflow-text">
            <div class="workflow-title">{{ step.title }}</div>
            <div class="workflow-desc">{{ step.desc }}</div>
          </div>
        </div>
      </div>

      <div class="content-grid">
        <div class="workbench-column">
          <!-- 文件上传区域 -->
          <div class="upload-section">
            <div class="upload-card">
          <div class="panel-head">
            <h2><i class="fas fa-upload"></i> 文档上传与抽取配置</h2>
            <p>建议优先上传结构清晰文档，并在结果中检查编号与单位字段。</p>
          </div>

          <div class="upload-tips">
            <span v-for="(tip, idx) in uploadTips" :key="idx">{{ tip }}</span>
          </div>

          <div class="upload-area" 
               :class="{ 'drag-over': isDragOver }"
               @drop="handleDrop"
               @dragover="handleDragOver"
               @dragleave="handleDragLeave"
               @click="triggerFileInput">
            
            <div v-if="!uploadedFile" class="upload-placeholder">
              <i class="fas fa-cloud-upload-alt"></i>
              <h3>拖拽文件到此处或点击上传</h3>
              <p>支持 PDF, DOC, DOCX, TXT, MD 格式，最大 10MB</p>
              <button class="btn btn-primary">选择文件</button>
            </div>

            <div v-else class="uploaded-file">
              <div class="file-info">
                <i :class="getFileIcon(uploadedFile.name)"></i>
                <div class="file-details">
                  <h4>{{ uploadedFile.name }}</h4>
                  <p>{{ formatFileSize(uploadedFile.size) }}</p>
                </div>
                <button class="btn btn-secondary btn-sm" @click.stop="removeFile">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>

          <input 
            ref="fileInput"
            type="file"
            accept=".pdf,.doc,.docx,.txt,.md"
            @change="handleFileSelect"
            style="display: none"
          />

          <!-- 处理按钮 -->
          <div class="action-buttons" v-if="uploadedFile">
            <button 
              class="btn btn-primary btn-lg"
              @click="processFile"
              :disabled="processing"
            >
              <i class="fas fa-cog" :class="{ 'fa-spin': processing }"></i>
              {{ processing ? '处理中...' : '开始知识抽取' }}
            </button>
          </div>
            </div>
          </div>

          <!-- 结果显示区域 -->
          <div class="results-section" v-if="hasResults || processing">
            <div class="results-card">
          <div class="results-header">
            <h2>
              <i class="fas fa-lightbulb"></i>
              抽取结果
            </h2>
            <div class="results-stats" v-if="extractionResult">
              <span class="stat-item">
                <i class="fas fa-clock"></i>
                处理时间: {{ formatTime(extractionResult.elapsed_time) }}
              </span>
              <span class="stat-item">
                <i class="fas fa-list"></i>
                条目数: {{ getItemCount() }}
              </span>
            </div>
          </div>

          <!-- 加载状态 -->
          <div v-if="processing" class="loading-container">
            <div class="loading-spinner">
              <i class="fas fa-spinner fa-spin"></i>
              <p>正在分析文档，提取知识...</p>
              <div class="progress-steps">
                <div class="step" :class="{ active: currentStep >= 1 }">
                  <i class="fas fa-upload"></i>
                  <span>上传文件</span>
                </div>
                <div class="step" :class="{ active: currentStep >= 2 }">
                  <i class="fas fa-search"></i>
                  <span>分析内容</span>
                </div>
                <div class="step" :class="{ active: currentStep >= 3 }">
                  <i class="fas fa-brain"></i>
                  <span>知识抽取</span>
                </div>
                <div class="step" :class="{ active: currentStep >= 4 }">
                  <i class="fas fa-check"></i>
                  <span>完成</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 结果内容 -->
          <div v-else-if="extractionResult" class="results-content">
              <div class="summary-dashboard">
                <div class="summary-kpi-card" v-for="item in extractionSummaryKpis" :key="item.label">
                  <div class="summary-kpi-label">{{ item.label }}</div>
                  <div class="summary-kpi-value">{{ item.value }}</div>
                  <div class="summary-kpi-note">{{ item.note }}</div>
                </div>
              </div>

              <div class="summary-checklist">
                <h3><i class="fas fa-clipboard-list"></i> 抽取后建议动作</h3>
                <ul>
                  <li v-for="(item, idx) in extractionChecklist" :key="idx">{{ item }}</li>
                </ul>
              </div>

            <!-- JSON格式结果 -->
            <div v-if="Array.isArray(extractionResult.extracted_knowledge)" class="json-results">
              <div class="view-toggle">
                <button 
                  :class="['toggle-btn', { active: viewMode === 'cards' }]"
                  @click="viewMode = 'cards'"
                >
                  <i class="fas fa-th-large"></i>
                  卡片视图
                </button>
                <button 
                  :class="['toggle-btn', { active: viewMode === 'table' }]"
                  @click="viewMode = 'table'"
                >
                  <i class="fas fa-table"></i>
                  表格视图
                </button>
                <button 
                  :class="['toggle-btn', { active: viewMode === 'json' }]"
                  @click="viewMode = 'json'"
                >
                  <i class="fas fa-code"></i>
                  JSON视图
                </button>
              </div>

              <!-- 卡片视图 -->
              <div v-if="viewMode === 'cards'" class="cards-view">
                <div 
                  v-for="(item, index) in extractionResult.extracted_knowledge"
                  :key="index"
                  class="knowledge-card"
                >
                  <div class="card-header">
                    <h3>条目 {{ index + 1 }}</h3>
                    <span class="card-index">#{{ index + 1 }}</span>
                  </div>
                  <div class="card-content">
                    <div 
                      v-for="(value, key) in item"
                      :key="key"
                      class="field-group"
                    >
                      <label class="field-label">{{ key }}</label>
                      <div class="field-value">{{ value }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 表格视图 -->
              <div v-if="viewMode === 'table'" class="table-view">
                <div class="table-container">
                  <table class="results-table">
                    <thead>
                      <tr>
                        <th>#</th>
                        <th v-for="key in getTableHeaders()" :key="key">{{ key }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr 
                        v-for="(item, index) in extractionResult.extracted_knowledge"
                        :key="index"
                      >
                        <td class="index-cell">{{ index + 1 }}</td>
                        <td 
                          v-for="key in getTableHeaders()" 
                          :key="key"
                          class="data-cell"
                        >
                          {{ item[key] || '-' }}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- JSON视图 -->
              <div v-if="viewMode === 'json'" class="json-view">
                <pre class="json-content">{{ JSON.stringify(extractionResult.extracted_knowledge, null, 2) }}</pre>
              </div>
            </div>

            <!-- 文本格式结果 -->
            <div v-else class="text-results">
              <div class="text-content">
                <pre>{{ extractionResult.extracted_knowledge }}</pre>
              </div>
            </div>
            
            <!-- 材料属性表格 -->
            <div class="materials-table-section" v-if="showMaterialsTable">
              <div class="materials-table-header">
                <h3>
                  <i class="fas fa-table"></i>
                  材料属性表格
                </h3>
                <button class="btn btn-primary btn-sm" @click="addTableRow">
                  <i class="fas fa-plus"></i>
                  添加行
                </button>
              </div>
              <div class="table-container">
                <table class="materials-table">
                  <thead>
                    <tr>
                      <!-- 文献部分 -->
                      <th colspan="2" class="merged-header">文献</th>
                      <!-- 原材料部分 -->
                      <th colspan="3" class="merged-header">原材料（Materials）</th>
                      <!-- 中间体部分 -->
                      <th colspan="2" class="merged-header">中间体（Intermediates）</th>
                      <!-- 中间体组成 -->
                      <th class="merged-header">中间体组成（Intermediate Compositions）</th>
                      <!-- 性能参数大类 -->
                      <th colspan="3" class="merged-header">性能（Properties）</th>
                      <!-- 备注和操作 -->
                      <th class="merged-header">性能趋势</th>
                      <th class="merged-header">操作</th>
                    </tr>
                    <tr>
                      <!-- 子表头 -->
                      <th>文献编号（Article ID）</th>
                      <th>文献名称（Article Name）</th>
                      <th>材料编号（Material ID）</th>
                      <th>原材料名称（Material Name）</th>
                      <th>CAS号（CAS Number）</th>
                      <th>中间体编号（Intermediate ID）</th>
                      <th>中间体名称（Intermediate Name）</th>
                      <th></th>
                      <th>性能编号（Property ID）</th>
                      <th>性能名称（Property Name）</th>
                      <th>性能值（Property Value）</th>
                      <th></th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, index) in materialsTableData" :key="index">
                      <td><input v-model="row.articleId" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.articleName" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.materialId" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.materialName" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.casNumber" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.intermediateId" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.intermediateName" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.intermediateComp" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.propertyId" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.propertyName" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.propertyValue" class="table-input" @input="handleTableDataChange"></td>
                      <td><input v-model="row.propertyTrend" class="table-input" @input="handleTableDataChange"></td>
                      <td>
                        <button class="btn btn-danger btn-sm" @click="removeTableRow(index)">
                          <i class="fas fa-trash"></i>
                          删除
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 操作按钮 -->
              <div class="result-actions">
                <button class="btn btn-primary" @click="exportResults">
                  <i class="fas fa-download"></i>
                  导出结果
                </button>
                <button class="btn btn-secondary" @click="clearResults">
                  <i class="fas fa-refresh"></i>
                  重新处理
                </button>
                <button class="btn btn-info" @click="copyToClipboard">
                  <i class="fas fa-copy"></i>
                  复制结果
                </button>
                <button class="btn btn-warning" @click="toggleMaterialsTable">
                  <i class="fas fa-table"></i>
                  {{ showMaterialsTable ? '隐藏材料表格' : '显示材料表格' }}
                </button>
              </div>
          </div>

          <!-- 错误显示 -->
          <div v-else-if="errorMessage" class="error-container">
            <div class="error-content">
              <i class="fas fa-exclamation-triangle"></i>
              <h3>处理失败</h3>
              <p>{{ errorMessage }}</p>
              <button class="btn btn-primary" @click="clearResults">
                <i class="fas fa-refresh"></i>
                重试
              </button>
            </div>
          </div>
            </div>
          </div>
        </div>

        <aside class="history-panel">
          <div class="history-card">
            <div class="history-header">
              <h3><i class="fas fa-history"></i> 抽取文档历史</h3>
              <button class="btn btn-secondary btn-sm" @click="clearExtractionHistory" :disabled="!extractionHistory.length">
                清空
              </button>
            </div>

            <div v-if="extractionHistory.length === 0" class="history-empty">
              <i class="fas fa-folder-open"></i>
              <p>暂无抽取历史</p>
            </div>

            <ul v-else class="history-list">
              <li v-for="item in extractionHistory" :key="item.id" class="history-item">
                <div class="history-item-top">
                  <span class="history-name" :title="item.file_name">{{ item.file_name }}</span>
                  <span class="history-status" :class="item.status">{{ item.status === 'success' ? '成功' : '失败' }}</span>
                </div>
                <div class="history-meta">
                  <span>{{ item.file_type }}</span>
                  <span>{{ item.file_size_label }}</span>
                </div>
                <div class="history-meta">
                  <span>条目 {{ item.item_count }}</span>
                  <span>耗时 {{ item.elapsed_time_label }}</span>
                </div>
                <div class="history-time">{{ formatHistoryTime(item.extracted_at) }}</div>
              </li>
            </ul>
          </div>
        </aside>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '@/utils/api'
import { ElMessage } from 'element-plus'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()

// 响应式数据
const uploadedFile = ref(null)
const isDragOver = ref(false)
const processing = ref(false)
const currentStep = ref(1)
const extractionResult = ref(null)
const errorMessage = ref('')
const viewMode = ref('cards')
const fileInput = ref(null)
const extractionHistory = ref([])
const showMaterialsTable = ref(false) // 默认不显示材料属性表格，避免影响页面加载性能
const materialsTableData = ref([ // 材料属性表格数据，仅初始化一行
  {
    articleId: '', // 文献编号
    articleName: '', // 文献名称
    materialId: '', // 材料编号
    materialName: '', // 原材料名称
    casNumber: '', // CAS号
    intermediateId: '', // 中间体编号
    intermediateName: '', // 中间体名称
    intermediateComp: '', // 中间体组成
    propertyId: '', // 性能编号
    propertyName: '', // 性能名称
    propertyValue: '', // 性能值
    propertyTrend: '' // 性能趋势
  }
])

// 计算属性
const hasResults = computed(() => {
  return extractionResult.value || errorMessage.value
})

const extractionSummaryKpis = computed(() => {
  const knowledge = extractionResult.value?.extracted_knowledge
  const itemCount = Array.isArray(knowledge) ? knowledge.length : (knowledge ? 1 : 0)
  const fields = Array.isArray(knowledge) && knowledge.length ? Object.keys(knowledge[0]).length : 0
  const elapsed = extractionResult.value?.elapsed_time ? `${extractionResult.value.elapsed_time.toFixed(1)}s` : '-'
  return [
    { label: '抽取条目数', value: `${itemCount}`, note: '结构化结果规模' },
    { label: '字段覆盖数', value: `${fields}`, note: '每条数据主要字段' },
    { label: '处理耗时', value: elapsed, note: '本次抽取耗时' },
    { label: '结果状态', value: itemCount ? '完成' : '空结果', note: '建议复核关键字段' }
  ]
})

const extractionChecklist = [
  '优先检查文献编号、材料编号和性能值是否完整。',
  '对关键性能字段执行单位统一与格式清洗。',
  '将异常值样本标记后再进入图谱或建模流程。',
  '导出前先切换到表格视图进行抽样复核。'
]

const overviewCards = [
  { title: '文档智能解析', desc: '自动识别段落、表格和关键字段', icon: 'fas fa-file-signature' },
  { title: '知识结构化', desc: '提取实体、属性、关系并标准化输出', icon: 'fas fa-project-diagram' },
  { title: '结果可视审阅', desc: '支持卡片/表格/JSON 多视图核验', icon: 'fas fa-eye' },
  { title: '数据可回填', desc: '可在材料属性表中编辑并同步结果', icon: 'fas fa-pen-square' }
]

const workflowSteps = [
  { title: '上传文档', desc: '支持 PDF / DOCX / TXT / MD' },
  { title: '自动抽取', desc: '执行实体识别与属性归类' },
  { title: '人工复核', desc: '按表格视图检查关键字段' },
  { title: '导出应用', desc: '用于知识图谱和下游建模' }
]

const uploadTips = [
  '建议文档包含清晰标题与字段名',
  '表格数据建议保留单位列',
  '同类字段建议统一命名',
  '抽取后优先核验编号与数值'
]

const EXTRACTION_HISTORY_KEY = 'knowledge_extraction_history_v1'
const HISTORY_USER_ID = 'web_user'

const getFileTypeLabel = (filename = '') => {
  const extension = filename.split('.').pop()?.toLowerCase()
  const typeMap = {
    pdf: 'PDF',
    doc: 'DOC',
    docx: 'DOCX',
    txt: 'TXT',
    md: 'MD'
  }
  return typeMap[extension] || (extension ? extension.toUpperCase() : 'FILE')
}

const loadExtractionHistoryFromLocal = () => {
  try {
    const raw = localStorage.getItem(EXTRACTION_HISTORY_KEY)
    extractionHistory.value = raw ? JSON.parse(raw) : []
  } catch (error) {
    extractionHistory.value = []
  }
}

const persistExtractionHistory = () => {
  localStorage.setItem(EXTRACTION_HISTORY_KEY, JSON.stringify(extractionHistory.value))
}

const normalizeHistoryItem = (item) => ({
  id: item.id || `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
  file_name: item.file_name || '-',
  file_type: item.file_type || getFileTypeLabel(item.file_name || ''),
  file_size: Number(item.file_size || 0),
  file_size_label: item.file_size_label || formatFileSize(Number(item.file_size || 0)),
  extracted_at: item.extracted_at || item.created_at || new Date().toISOString(),
  status: item.status || 'failed',
  item_count: Number(item.item_count || 0),
  elapsed_time: item.elapsed_time,
  elapsed_time_label: item.elapsed_time_label || (item.elapsed_time ? formatTime(item.elapsed_time) : '-'),
  error_message: item.error_message || ''
})

const fetchExtractionHistoryFromServer = async () => {
  const response = await apiClient.get('/ai-service/knowledge-extraction-history/', {
    params: {
      user_id: HISTORY_USER_ID,
      limit: 30
    }
  })

  const items = response?.data?.data?.items || []
  extractionHistory.value = items.map(normalizeHistoryItem)
  persistExtractionHistory()
}

const loadExtractionHistory = async () => {
  try {
    await fetchExtractionHistoryFromServer()
  } catch (error) {
    loadExtractionHistoryFromLocal()
  }
}

const appendLocalExtractionHistory = ({ status, elapsedTime = null, itemCount = 0, error = '' }) => {
  const file = uploadedFile.value
  if (!file) return

  const item = normalizeHistoryItem({
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    file_name: file.name,
    file_type: getFileTypeLabel(file.name),
    file_size: file.size,
    file_size_label: formatFileSize(file.size),
    extracted_at: new Date().toISOString(),
    status,
    item_count: itemCount,
    elapsed_time: elapsedTime,
    elapsed_time_label: elapsedTime ? formatTime(elapsedTime) : '-',
    error_message: error
  })

  extractionHistory.value = [item, ...extractionHistory.value].slice(0, 30)
  persistExtractionHistory()
}

const syncHistoryAfterExtraction = async (fallbackPayload) => {
  try {
    await fetchExtractionHistoryFromServer()
  } catch (error) {
    appendLocalExtractionHistory(fallbackPayload)
  }
}

const clearExtractionHistory = async () => {
  try {
    await apiClient.delete('/ai-service/knowledge-extraction-history/', {
      params: {
        user_id: HISTORY_USER_ID
      }
    })
    extractionHistory.value = []
    persistExtractionHistory()
    ElMessage.success('抽取历史已清空')
  } catch (error) {
    extractionHistory.value = []
    persistExtractionHistory()
    ElMessage.warning('后端清空失败，已清空本地历史')
  }
}

const formatHistoryTime = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

// 方法
const triggerFileInput = () => {
  fileInput.value?.click()
}

const handleFileSelect = (event) => {
  const files = event.target.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

const handleDrop = (event) => {
  event.preventDefault()
  isDragOver.value = false
  
  const files = event.dataTransfer.files
  if (files && files.length > 0) {
    handleFile(files[0])
  }
}

const handleDragOver = (event) => {
  event.preventDefault()
  isDragOver.value = true
}

const handleDragLeave = () => {
  isDragOver.value = false
}

const handleFile = (file) => {
  // 检查文件类型
  const allowedTypes = ['application/pdf', 'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'text/markdown']
  
  const allowedExtensions = ['.pdf', '.doc', '.docx', '.txt', '.md']
  const fileExtension = '.' + file.name.split('.').pop().toLowerCase()
  
  if (!allowedTypes.includes(file.type) && !allowedExtensions.includes(fileExtension)) {
    ElMessage.error('不支持的文件格式，请上传 PDF, DOC, DOCX, TXT 或 MD 文件')
    return
  }
  
  // 检查文件大小 (10MB)
  const maxSize = 10 * 1024 * 1024
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }
  
  uploadedFile.value = file
  clearResults()
}

const removeFile = () => {
  uploadedFile.value = null
  if (fileInput.value) {
    fileInput.value.value = ''
  }
  clearResults()
}

const processFile = async () => {
  if (!uploadedFile.value) {
    ElMessage.error('请先上传文件')
    return
  }
  
  processing.value = true
  errorMessage.value = ''
  currentStep.value = 1
  
  try {
    const formData = new FormData()
    formData.append('file', uploadedFile.value)
  formData.append('user_id', HISTORY_USER_ID)
    
    // 模拟处理步骤
    currentStep.value = 2
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    currentStep.value = 3
    
    const response = await apiClient.post('/ai-service/knowledge-extraction/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 120000 // 2分钟超时
    })
    
    currentStep.value = 4
    
    if (response.data.status === 'success') {
      extractionResult.value = response.data.data
      // 如果是文本格式结果，尝试解析JSON并填充到表格
      if (typeof extractionResult.value.extracted_knowledge === 'string') {
        parseTextToTableData(extractionResult.value.extracted_knowledge)
      }
      await syncHistoryAfterExtraction({
        status: 'success',
        elapsedTime: extractionResult.value?.elapsed_time,
        itemCount: getItemCount()
      })
      ElMessage.success('知识抽取完成！')
    } else {
      throw new Error(response.data.message || '处理失败')
    }
    
  } catch (error) {
    console.error('知识抽取失败:', error)
    errorMessage.value = error.response?.data?.message || error.message || '处理失败，请重试'
    await syncHistoryAfterExtraction({
      status: 'failed',
      error: errorMessage.value
    })
    ElMessage.error(errorMessage.value)
  } finally {
    processing.value = false
  }
}

const parseTextToTableData = (textContent) => {
  try {
    // 使用正则表达式匹配JSON结构
    const headerRegex = /"([^"]+)":\s*(\{|\[)/g
    const subHeaderRegex = /"([^"]+)":\s*"([^"]+)"/g
    
    const headers = new Set()
    const tableData = []
    let currentRow = {}
    let currentHeader = ''
    
    // 第一次扫描：收集所有可能的表头
    let headerMatch
    while ((headerMatch = headerRegex.exec(textContent)) !== null) {
      headers.add(headerMatch[1])
    }
    
    // 第二次扫描：提取子表头和数据
    let subHeaderMatch
    while ((subHeaderMatch = subHeaderRegex.exec(textContent)) !== null) {
      const subHeader = subHeaderMatch[1]
      const value = subHeaderMatch[2]
      
      // 检查是否是重复字段（表示新行开始）
      if (currentRow[subHeader] && Object.keys(currentRow).length > 0) {
        // 添加当前行到表格数据
        tableData.push({...currentRow})
        // 重置当前行
        currentRow = {}
      }
      
      // 设置值到当前行
      currentRow[subHeader] = value
    }
    
    // 添加最后一行
    if (Object.keys(currentRow).length > 0) {
      tableData.push(currentRow)
    }
    
    // 将提取的数据映射到材料表格格式
    const mappedData = tableData.map(row => {
      // 创建一个新的表格行对象，使用当前表格的字段结构
      const newRow = {
        articleId: '', articleName: '', materialId: '', materialName: '', 
        casNumber: '', intermediateId: '', intermediateName: '', intermediateComp: '',
        propertyId: '', propertyName: '', propertyValue: '', propertyTrend: ''
      }
      
      // 映射提取的数据到表格字段
      Object.keys(row).forEach(key => {
        // 根据字段名智能映射
        const lowerKey = key.toLowerCase()
        
        // 文献相关字段映射
        if (lowerKey.includes('article') || lowerKey.includes('文献') || lowerKey.includes('paper') || lowerKey.includes('论文')) {
          if (lowerKey.includes('id') || lowerKey.includes('编号') || lowerKey.includes('no')) {
            newRow.articleId = row[key]
          } else if (lowerKey.includes('name') || lowerKey.includes('title') || lowerKey.includes('标题')) {
            newRow.articleName = row[key]
          } else {
            // 默认为文献名称
            if (!newRow.articleName) {
              newRow.articleName = row[key]
            }
          }
        }
        // 材料相关字段映射
        else if (lowerKey.includes('material') || lowerKey.includes('材料') || lowerKey.includes('compound') || lowerKey.includes('化合物')) {
          if (lowerKey.includes('id') || lowerKey.includes('编号') || lowerKey.includes('no')) {
            newRow.materialId = row[key]
          } else if (lowerKey.includes('name') || lowerKey.includes('title') || lowerKey.includes('名称')) {
            newRow.materialName = row[key]
          } else {
            // 默认为材料名称
            if (!newRow.materialName) {
              newRow.materialName = row[key]
            }
          }
        }
        // CAS号映射
        else if (lowerKey.includes('cas') || lowerKey.includes('casno') || lowerKey.includes('cas号')) {
          newRow.casNumber = row[key]
        }
        // 中间体相关字段映射
        else if (lowerKey.includes('intermediate') || lowerKey.includes('中间体') || lowerKey.includes('component') || lowerKey.includes('组分')) {
          if (lowerKey.includes('id') || lowerKey.includes('编号') || lowerKey.includes('no')) {
            newRow.intermediateId = row[key]
          } else if (lowerKey.includes('name') || lowerKey.includes('名称')) {
            newRow.intermediateName = row[key]
          } else if (lowerKey.includes('comp') || lowerKey.includes('组成') || lowerKey.includes('composition') || lowerKey.includes('成分')) {
            newRow.intermediateComp = row[key]
          } else {
            // 默认为中间体名称
            if (!newRow.intermediateName) {
              newRow.intermediateName = row[key]
            }
          }
        }
        // 性能相关字段映射
        else if (lowerKey.includes('property') || lowerKey.includes('性能') || lowerKey.includes('parameter') || lowerKey.includes('参数')) {
          if (lowerKey.includes('id') || lowerKey.includes('编号') || lowerKey.includes('no')) {
            newRow.propertyId = row[key]
          } else if (lowerKey.includes('value') || lowerKey.includes('值')) {
            newRow.propertyValue = row[key]
          } else if (lowerKey.includes('trend') || lowerKey.includes('趋势') || lowerKey.includes('direction')) {
            newRow.propertyTrend = row[key]
          } else if (lowerKey.includes('name') || lowerKey.includes('名称') || lowerKey.includes('type')) {
            newRow.propertyName = row[key]
          } else {
            // 默认为性能值
            if (!newRow.propertyValue) {
              newRow.propertyValue = row[key]
            } else if (!newRow.propertyName) {
              newRow.propertyName = row[key]
            }
          }
        }
        // 额外的性能趋势映射
        else if (lowerKey.includes('direction') || lowerKey.includes('变化') || lowerKey.includes('change')) {
          newRow.propertyTrend = row[key]
        }
        // 额外的通用字段映射
        else {
          // 如果没有匹配的字段，尝试放入最可能的位置
          if (!newRow.articleName && (lowerKey.includes('title') || lowerKey.includes('标题'))) {
            newRow.articleName = row[key]
          } else if (!newRow.materialName && (lowerKey.includes('compound') || lowerKey.includes('化合物'))) {
            newRow.materialName = row[key]
          } else if (!newRow.intermediateName && (lowerKey.includes('component') || lowerKey.includes('组分'))) {
            newRow.intermediateName = row[key]
          } else if (!newRow.intermediateComp && (lowerKey.includes('composition') || lowerKey.includes('成分') || lowerKey.includes('content'))) {
            newRow.intermediateComp = row[key]
          } else if (!newRow.propertyValue && !isNaN(parseFloat(row[key]))) {
            // 如果是数值，放入性能值
            newRow.propertyValue = row[key]
          } else if (!newRow.propertyName) {
            // 最后尝试放入性能名称
            newRow.propertyName = row[key]
          }
        }
      })
      
      return newRow
    })
    
    // 如果有有效的数据，更新表格
    if (mappedData.length > 0) {
      materialsTableData.value = mappedData
      showMaterialsTable.value = true
      ElMessage.info(`已从文本中提取 ${mappedData.length} 条数据并填充到表格中`)
    }
  } catch (error) {
    console.error('解析文本到表格数据失败:', error)
    // 不显示错误，因为这只是一个辅助功能
  }
}

const clearResults = () => {
  extractionResult.value = null
  errorMessage.value = ''
  currentStep.value = 1
}

const getFileIcon = (filename) => {
  const extension = filename.split('.').pop().toLowerCase()
  const iconMap = {
    pdf: 'fas fa-file-pdf text-red-500',
    doc: 'fas fa-file-word text-blue-500',
    docx: 'fas fa-file-word text-blue-500',
    txt: 'fas fa-file-alt text-gray-500',
    md: 'fas fa-file-code text-green-500'
  }
  return iconMap[extension] || 'fas fa-file'
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatTime = (seconds) => {
  if (!seconds) return '-'
  return seconds.toFixed(1) + 's'
}

const getItemCount = () => {
  if (!extractionResult.value?.extracted_knowledge) return 0
  if (Array.isArray(extractionResult.value.extracted_knowledge)) {
    return extractionResult.value.extracted_knowledge.length
  }
  return 1
}

const getTableHeaders = () => {
  if (!extractionResult.value?.extracted_knowledge || 
      !Array.isArray(extractionResult.value.extracted_knowledge) ||
      extractionResult.value.extracted_knowledge.length === 0) {
    return []
  }
  return Object.keys(extractionResult.value.extracted_knowledge[0])
}

const exportResults = () => {
  if (!extractionResult.value) return
  
  const dataStr = JSON.stringify(extractionResult.value.extracted_knowledge, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `knowledge_extraction_${new Date().getTime()}.json`
  link.click()
  URL.revokeObjectURL(url)
}

const copyToClipboard = async () => {
  if (!extractionResult.value) return
  
  try {
    const textToCopy = JSON.stringify(extractionResult.value.extracted_knowledge, null, 2)
    await navigator.clipboard.writeText(textToCopy)
    ElMessage.success('结果已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }
}

// 添加新行到材料属性表格
const addTableRow = () => {
  materialsTableData.value.push({
    articleId: '', // 文献编号
    articleName: '', // 文献名称
    materialId: '', // 材料编号
    materialName: '', // 原材料名称
    casNumber: '', // CAS号
    intermediateId: '', // 中间体编号
    intermediateName: '', // 中间体名称
    intermediateComp: '', // 中间体组成
    propertyId: '', // 性能编号
    propertyName: '', // 性能名称
    propertyValue: '', // 性能值
    propertyTrend: '' // 性能趋势
  })
}

const removeTableRow = (index) => {
  if (materialsTableData.value.length > 1) {
    materialsTableData.value.splice(index, 1)
    ElMessage.success('行已删除')
  } else {
    ElMessage.warning('至少保留一行数据')
    // 清空当前行数据
    materialsTableData.value[0] = {
      articleId: '', // 文献编号
      articleName: '', // 文献名称
      materialId: '', // 材料编号
      materialName: '', // 原材料名称
      casNumber: '', // CAS号
      intermediateId: '', // 中间体编号
      intermediateName: '', // 中间体名称
      intermediateComp: '', // 中间体组成
      propertyId: '', // 性能编号
      propertyName: '', // 性能名称
      propertyValue: '', // 性能值
      propertyTrend: '' // 性能趋势
    }
  }
}


// 智能字段匹配函数：将表格字段映射到JSON字段
const smartFieldMatching = (jsonKeys, tableField) => {
  if (!jsonKeys || jsonKeys.length === 0) return null;
  
  const lowerTableField = tableField.toLowerCase();
  
  // 为每个JSON字段计算匹配分数
  const matchedField = jsonKeys.map(jsonKey => {
    const lowerJsonKey = jsonKey.toLowerCase();
    let score = 0;
    
    // 精确匹配
    if (lowerJsonKey === lowerTableField) {
      score = 10;
    } 
    // 部分匹配
    else if (lowerJsonKey.includes(lowerTableField) || lowerTableField.includes(lowerJsonKey)) {
      score = 5;
    }
    
    // 基于字段类型的匹配
    if (lowerTableField.includes('articleid') || lowerTableField.includes('文献编号')) {
      if (lowerJsonKey.includes('article') && lowerJsonKey.includes('id')) {
        score += 8;
      } else if (lowerJsonKey.includes('article')) {
        score += 4;
      }
    }
    
    if (lowerTableField.includes('articlename') || lowerTableField.includes('文献名称')) {
      if (lowerJsonKey.includes('article') && (lowerJsonKey.includes('name') || !lowerJsonKey.includes('id'))) {
        score += 8;
      }
    }
    
    if (lowerTableField.includes('materialid') || lowerTableField.includes('材料编号')) {
      if (lowerJsonKey.includes('material') && lowerJsonKey.includes('id')) {
        score += 8;
      } else if (lowerJsonKey.includes('material')) {
        score += 4;
      }
    }
    
    if (lowerTableField.includes('materialname') || lowerTableField.includes('材料名称')) {
      if (lowerJsonKey.includes('material') && (lowerJsonKey.includes('name') || !lowerJsonKey.includes('id'))) {
        score += 8;
      }
    }
    
    if (lowerTableField.includes('casnumber') || lowerTableField.includes('cas号')) {
      if (lowerJsonKey.includes('cas')) {
        score += 10;
      }
    }
    
    if (lowerTableField.includes('intermediateid') || lowerTableField.includes('中间体编号')) {
      if (lowerJsonKey.includes('intermediate') && lowerJsonKey.includes('id')) {
        score += 8;
      } else if (lowerJsonKey.includes('intermediate')) {
        score += 4;
      }
    }
    
    if (lowerTableField.includes('intermediatename') || lowerTableField.includes('中间体名称')) {
      if (lowerJsonKey.includes('intermediate') && (lowerJsonKey.includes('name') || !lowerJsonKey.includes('id'))) {
        score += 8;
      }
    }
    
    if (lowerTableField.includes('intermediatecomp') || lowerTableField.includes('中间体组成')) {
      if (lowerJsonKey.includes('intermediate') && (lowerJsonKey.includes('comp') || lowerJsonKey.includes('组成'))) {
        score += 10;
      } else if (lowerJsonKey.includes('intermediate')) {
        score += 5;
      }
    }
    
    if (lowerTableField.includes('propertyid') || lowerTableField.includes('性能编号')) {
      if (lowerJsonKey.includes('property') && lowerJsonKey.includes('id')) {
        score += 8;
      } else if (lowerJsonKey.includes('property')) {
        score += 4;
      }
    }
    
    if (lowerTableField.includes('propertyname') || lowerTableField.includes('性能名称')) {
      if (lowerJsonKey.includes('property') && (lowerJsonKey.includes('name') || !lowerJsonKey.includes('id'))) {
        score += 8;
      }
    }
    
    if (lowerTableField.includes('propertyvalue') || lowerTableField.includes('性能值')) {
      if (lowerJsonKey.includes('property') && (lowerJsonKey.includes('value') || lowerJsonKey.includes('值'))) {
        score += 10;
      } else if (lowerJsonKey.includes('property')) {
        score += 5;
      }
    }
    
    if (lowerTableField.includes('propertytrend') || lowerTableField.includes('性能趋势')) {
      if (lowerJsonKey.includes('property') && (lowerJsonKey.includes('trend') || lowerJsonKey.includes('趋势'))) {
        score += 10;
      } else if (lowerJsonKey.includes('property')) {
        score += 5;
      }
    }
    
    return { key: jsonKey, score };
  }) // 找到分数最高的JSON字段
  .filter(item => item.score > 0)
  .sort((a, b) => b.score - a.score)[0];
  
  return matchedField ? matchedField.key : null;
};

// 更新JSON数据从表格数据
const updateJsonDataFromTable = () => {
  if (!extractionResult.value) return
  
  let updatedData = null;
  
  // 如果extracted_knowledge是数组
  if (Array.isArray(extractionResult.value.extracted_knowledge)) {
    updatedData = materialsTableData.value.map((tableRow, index) => {
      // 获取原始JSON对象或创建新对象
      const originalJson = index < extractionResult.value.extracted_knowledge.length 
        ? {...extractionResult.value.extracted_knowledge[index]} 
        : {};
      
      // 更新表格数据到JSON对象
      Object.keys(tableRow).forEach(tableField => {
        if (tableRow[tableField] !== '') {
          // 使用smartFieldMatching找到对应的JSON字段
          const jsonField = smartFieldMatching(Object.keys(originalJson), tableField);
          if (jsonField) {
            originalJson[jsonField] = tableRow[tableField];
          }
        }
      });
      
      return originalJson;
    });
  } 
  // 如果extracted_knowledge是单个对象
  else if (extractionResult.value.extracted_knowledge && typeof extractionResult.value.extracted_knowledge === 'object') {
    updatedData = {...extractionResult.value.extracted_knowledge};
    
    // 只处理第一行数据
    if (materialsTableData.value.length > 0) {
      const tableRow = materialsTableData.value[0];
      
      Object.keys(tableRow).forEach(tableField => {
        if (tableRow[tableField] !== '') {
          // 使用smartFieldMatching找到对应的JSON字段
          const jsonField = smartFieldMatching(Object.keys(updatedData), tableField);
          if (jsonField) {
            updatedData[jsonField] = tableRow[tableField];
          }
        }
      });
    }
  }
  else {
    // 如果是字符串或其他类型，创建新的数据结构
    updatedData = materialsTableData.value.map(tableRow => {
      const newJson = {};
      
      Object.keys(tableRow).forEach(tableField => {
        if (tableRow[tableField] !== '') {
          // 根据表格字段名生成对应的JSON字段名
          // 移除驼峰命名中的大写字母，添加下划线
          const jsonField = tableField.replace(/([A-Z])/g, '_$1').toLowerCase();
          newJson[jsonField] = tableRow[tableField];
        }
      });
      
      return newJson;
    });
  }
  
  // 更新extracted_knowledge
  if (updatedData) {
    // 如果只有一行数据且原始数据不是数组，保持为对象
    if (updatedData.length === 1 && !Array.isArray(extractionResult.value.extracted_knowledge)) {
      extractionResult.value.extracted_knowledge = updatedData[0];
    } else {
      extractionResult.value.extracted_knowledge = updatedData;
    }
  }
  
  // 确保视图更新
  // 使用Vue的响应式API确保数据变化被检测到
  extractionResult.value = { ...extractionResult.value };
};

// 监听表格数据变化
const handleTableDataChange = () => {
  updateJsonDataFromTable();
};

// 切换材料属性表格显示/隐藏
const toggleMaterialsTable = () => {
  showMaterialsTable.value = !showMaterialsTable.value
  ElMessage.info(showMaterialsTable.value ? '材料属性表格已显示' : '材料属性表格已隐藏')
}

const goBack = () => {
  router.push({ name: 'SmartAgents' })
}

onMounted(async () => {
  await loadExtractionHistory()
})
</script>

<style scoped>
.knowledge-extraction-page-wrapper {
  display: flex;
  height: 100vh;
  background: #f3f6fb;
}

.knowledge-extraction-container {
  flex: 1;
  overflow-y: auto;
  min-height: 100vh;
  width: 100%;
  background: radial-gradient(circle at 10% -10%, #eef2ff 0%, #f7f9fc 42%, #f4f7fb 100%);
  padding: 28px 30px 36px;
  box-sizing: border-box;
}

.page-header {
  width: 100%;
  margin: 0 0 22px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.97), rgba(246, 249, 255, 0.95));
  border-radius: 22px;
  padding: 28px 30px;
  box-shadow: 0 10px 28px rgba(16, 24, 40, 0.08);
  border: 1px solid #e8ecf8;
  text-align: center;
}

.back-navigation {
  display: flex;
  justify-content: flex-start;
  margin-bottom: 14px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid #e6ecfb;
  color: #4b5563;
  font-size: 13px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.25s ease;
}

.back-btn:hover {
  background: #fff;
  color: #1f2937;
  border-color: #cfdaf8;
}

.page-title {
  font-size: 42px;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: #1f2b4a;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.page-title i {
  color: #5d74ff;
}

.page-description {
  font-size: 17px;
  color: #65708a;
  margin: 0;
}

.header-tags {
  margin-top: 14px;
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-item {
  background: #f2f5ff;
  border: 1px solid #dce5ff;
  color: #44517a;
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 12px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.main-content {
  width: 100%;
  margin: 0;
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 2.2fr) minmax(280px, 0.9fr);
  gap: 16px;
  align-items: start;
}

.workbench-column {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.overview-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.overview-card {
  background: #fff;
  border: 1px solid #e8edf8;
  border-radius: 12px;
  padding: 10px;
  display: flex;
  gap: 10px;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.05);
}

.overview-icon {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: #eef3ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
}

.overview-title {
  font-size: 13px;
  font-weight: 700;
  color: #1f2b4a;
}

.overview-desc {
  font-size: 12px;
  color: #64748b;
  margin-top: 2px;
}

.workflow-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.workflow-item {
  border: 1px solid #e5ebfb;
  background: linear-gradient(180deg, #fbfcff 0%, #f7f9ff 100%);
  border-radius: 12px;
  padding: 10px;
  display: flex;
  gap: 10px;
}

.workflow-index {
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #5f79ff;
  color: #fff;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}

.workflow-title {
  font-size: 13px;
  font-weight: 700;
  color: #1e293b;
}

.workflow-desc {
  font-size: 12px;
  color: #64748b;
}

/* 上传区域 */
.upload-section {
  grid-row: auto;
}

.upload-card {
  background: #ffffff;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  border: 1px solid #e9edf7;
}

.panel-head {
  margin-bottom: 12px;
}

.panel-head h2 {
  margin: 0;
  color: #1f2b4a;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.upload-tips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
}

.upload-tips span {
  background: #f5f7ff;
  border: 1px solid #e2e8f7;
  color: #475569;
  border-radius: 8px;
  padding: 4px 8px;
  font-size: 12px;
}

.upload-area {
  border: 2px dashed #ccd6f6;
  border-radius: 16px;
  padding: 44px 26px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: linear-gradient(180deg, #fbfcff 0%, #f7f9ff 100%);
}

.upload-area:hover {
  border-color: #5f79ff;
  box-shadow: 0 8px 20px rgba(95, 121, 255, 0.15);
  transform: translateY(-2px);
}

.upload-area.drag-over {
  border-color: #5f79ff;
  background: linear-gradient(180deg, #eef3ff 0%, #eaf0ff 100%);
  transform: scale(1.02);
}

.upload-placeholder i {
  font-size: 48px;
  color: #5f79ff;
  margin-bottom: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 84px;
  border-radius: 999px;
  background: rgba(95, 121, 255, 0.12);
}

.upload-placeholder h3 {
  font-size: 32px;
  color: #1f2b4a;
  margin-bottom: 8px;
}

.upload-placeholder p {
  color: #6a7693;
  margin-bottom: 22px;
  font-size: 15px;
}

.uploaded-file {
  display: flex;
  justify-content: center;
  align-items: center;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #fff;
  padding: 14px 18px;
  border-radius: 12px;
  border: 1px solid #e7ebf6;
  box-shadow: 0 6px 16px rgba(17, 24, 39, 0.06);
}

.file-info i {
  font-size: 2rem;
}

.file-details h4 {
  margin: 0;
  color: #2c3e50;
}

.file-details p {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.action-buttons {
  margin-top: 20px;
  text-align: center;
}

/* 结果区域 */
.results-section {
  grid-row: auto;
}

.history-panel {
  position: sticky;
  top: 14px;
}

.history-card {
  background: #fff;
  border-radius: 16px;
  padding: 14px;
  border: 1px solid #e7ecf8;
  box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
  max-height: calc(100vh - 42px);
  overflow-y: auto;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.history-header h3 {
  margin: 0;
  font-size: 15px;
  color: #1f2b4a;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.history-empty {
  border: 1px dashed #d8e0f5;
  border-radius: 10px;
  padding: 24px 12px;
  text-align: center;
  color: #94a3b8;
}

.history-empty i {
  font-size: 22px;
  margin-bottom: 6px;
}

.history-empty p {
  margin: 0;
  font-size: 13px;
}

.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 8px;
}

.history-item {
  border: 1px solid #e8edf8;
  border-radius: 10px;
  padding: 10px;
  background: #fcfdff;
}

.history-item-top {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.history-name {
  font-size: 13px;
  font-weight: 700;
  color: #334155;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.history-status {
  font-size: 11px;
  border-radius: 999px;
  padding: 2px 8px;
  border: 1px solid #dbeafe;
  color: #1d4ed8;
  background: #eff6ff;
  flex-shrink: 0;
}

.history-status.failed {
  color: #b91c1c;
  background: #fef2f2;
  border-color: #fecaca;
}

.history-meta {
  display: flex;
  justify-content: space-between;
  color: #64748b;
  font-size: 12px;
  margin-top: 4px;
}

.history-time {
  margin-top: 6px;
  font-size: 11px;
  color: #94a3b8;
}

.results-card {
  background: #fff;
  border-radius: 18px;
  padding: 24px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  border: 1px solid #e9edf7;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid #ecf0f6;
}

.results-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #1f2b4a;
  margin: 0;
}

.results-header i {
  color: #5f79ff;
}

.results-stats {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.summary-dashboard {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
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
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
  margin: 4px 0;
}

.summary-kpi-note {
  font-size: 12px;
  color: #94a3b8;
}

.summary-checklist {
  border: 1px solid #e8edf7;
  border-radius: 10px;
  padding: 10px 12px;
  margin-bottom: 12px;
  background: #fff;
}

.summary-checklist h3 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 8px;
}

.summary-checklist ul {
  margin: 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.75;
  font-size: 13px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  color: #51607f;
  font-size: 13px;
  background: #f4f7ff;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid #e4eafc;
}

.loading-container {
  text-align: center;
  padding: 3rem;
}

.loading-spinner i {
  font-size: 3rem;
  color: #5f79ff;
  margin-bottom: 1rem;
}

.loading-spinner p {
  font-size: 1.05rem;
  color: #30405f;
  margin-bottom: 2rem;
}

.progress-steps {
  display: flex;
  justify-content: center;
  gap: 2rem;
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  opacity: 0.3;
  transition: all 0.3s ease;
}

.step.active {
  opacity: 1;
  color: #5f79ff;
}

.step i {
  font-size: 1.5rem;
}

/* 视图切换 */
.view-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  justify-content: center;
}

.toggle-btn {
  padding: 8px 14px;
  border: 1px solid #dfe6fa;
  background: #fff;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #47587d;
  font-weight: 600;
}

.toggle-btn:hover {
  border-color: #5f79ff;
  color: #3048ce;
}

.toggle-btn.active {
  background: linear-gradient(135deg, #5f79ff 0%, #725cff 100%);
  color: white;
  border-color: transparent;
  box-shadow: 0 8px 18px rgba(95, 121, 255, 0.28);
}

/* 卡片视图 */
.cards-view {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.knowledge-card {
  background: #fff;
  border-radius: 14px;
  padding: 1.25rem;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  border: 1px solid #e9edf8;
  transition: all 0.25s ease;
}

.knowledge-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 24px rgba(15, 23, 42, 0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #ecf0f1;
}

.card-header h3 {
  margin: 0;
  color: #1f2b4a;
}

.card-index {
  background: linear-gradient(135deg, #5f79ff 0%, #725cff 100%);
  color: white;
  padding: 0.25rem 0.5rem;
  border-radius: 12px;
  font-size: 0.8rem;
}

.field-group {
  margin-bottom: 1rem;
}

.field-label {
  display: block;
  font-weight: 600;
  color: #32476d;
  margin-bottom: 0.3rem;
  font-size: 0.9rem;
}

.field-value {
  background: #f8faff;
  padding: 0.75rem;
  border-radius: 8px;
  border-left: 3px solid #5f79ff;
  font-size: 0.95rem;
  line-height: 1.5;
}

/* 表格视图 */
.table-container {
  overflow-x: auto;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
}

.results-table th {
  background: linear-gradient(135deg, #5f79ff 0%, #725cff 100%);
  color: white;
  padding: 12px;
  text-align: left;
  font-weight: 600;
  position: sticky;
  top: 0;
  z-index: 1;
}

.results-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #ecf0f1;
}

.results-table tbody tr:nth-child(odd) {
  background: #fcfdff;
}

.index-cell {
  background: #f4f7ff;
  font-weight: 600;
  color: #5f79ff;
  text-align: center;
  width: 60px;
}

.data-cell {
  max-width: 200px;
  word-break: break-word;
}

/* JSON视图 */
.json-view {
  background: #1f2937;
  border-radius: 10px;
  overflow: hidden;
}

.json-content {
  padding: 1.5rem;
  margin: 0;
  color: #a0aec0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
  overflow-x: auto;
}

/* 文本结果 */
.text-results {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
}

.text-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  color: #2c3e50;
}

/* 操作按钮 */
.result-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  justify-content: center;
  flex-wrap: wrap;
}

/* 错误显示 */
.error-container {
  text-align: center;
  padding: 3rem;
}

.error-content i {
  font-size: 4rem;
  color: #e74c3c;
  margin-bottom: 1rem;
}

.error-content h3 {
  color: #e74c3c;
  margin-bottom: 1rem;
}

.error-content p {
  color: #7f8c8d;
  margin-bottom: 2rem;
}

/* 通用按钮样式 */
.btn {
  padding: 10px 16px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  box-shadow: 0 5px 12px rgba(17, 24, 39, 0.08);
}

.btn-primary {
  background: linear-gradient(135deg, #5f79ff 0%, #725cff 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.01);
  box-shadow: 0 10px 20px rgba(95, 121, 255, 0.28);
}

.btn-primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #eef2f8;
  color: #2f3f61;
}

.btn-secondary:hover {
  background: #e1e8f4;
  transform: translateY(-2px);
}

.btn-info {
  background: linear-gradient(135deg, #3ea7ff 0%, #2f8be9 100%);
  color: white;
}

.btn-info:hover {
  box-shadow: 0 10px 20px rgba(62, 167, 255, 0.26);
  transform: translateY(-2px);
}

.btn-warning {
  background: linear-gradient(135deg, #ffbf47 0%, #ff9b2f 100%);
  color: #fff;
}

.btn-warning:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(255, 162, 66, 0.25);
}

.btn-danger {
  background: linear-gradient(135deg, #ff6f6f 0%, #ff4d4f 100%);
  color: #fff;
}

.btn-danger:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(255, 77, 79, 0.28);
}

.btn-lg {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.btn-sm {
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
}

/* 材料属性表格样式 */
.materials-table-section {
  margin-top: 2rem;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.06);
  border: 1px solid #e9edf7;
}

.materials-table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #ecf0f1;
}

.materials-table-header h3 {
  margin: 0;
  color: #1f2b4a;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.materials-table-header i {
  color: #5f79ff;
}

.materials-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.materials-table th {
  background: linear-gradient(135deg, #5f79ff 0%, #725cff 100%);
  color: white;
  padding: 0.75rem 0.5rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid #5f79ff;
}

.materials-table th.merged-header {
  background: #5269f6;
  font-size: 0.85rem;
  padding: 0.5rem;
}

.materials-table td {
  padding: 0.5rem;
  border: 1px solid #ecf0f1;
  text-align: center;
}

.materials-table tbody tr:nth-child(odd) {
  background: #fbfdff;
}

.table-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d7deef;
  border-radius: 4px;
  font-size: 0.9rem;
  box-sizing: border-box;
  transition: border-color 0.3s ease;
}

.table-input:focus {
  outline: none;
  border-color: #5f79ff;
  box-shadow: 0 0 0 3px rgba(95, 121, 255, 0.2);
}

.table-actions {
  margin-top: 1.5rem;
  text-align: center;
}

/* 响应式表格样式 */
@media (max-width: 1200px) {
  .materials-table {
    font-size: 0.8rem;
  }
  
  .table-input {
    font-size: 0.8rem;
    padding: 0.3rem;
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .knowledge-extraction-container {
    padding: 1rem;
  }

  .content-grid {
    grid-template-columns: 1fr;
  }

  .history-panel {
    position: static;
  }

  .history-card {
    max-height: none;
  }

  .overview-strip,
  .workflow-strip {
    grid-template-columns: 1fr;
  }

  .page-header {
    padding: 20px 16px;
  }

  .page-title {
    font-size: 30px;
  }

  .upload-placeholder h3 {
    font-size: 24px;
  }
  
  .upload-area {
    padding: 2rem 1rem;
  }
  
  .cards-view {
    grid-template-columns: 1fr;
  }
  
  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .summary-dashboard {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  
  .result-actions {
    flex-direction: column;
  }
  
  .progress-steps {
    flex-direction: column;
    gap: 1rem;
  }
  
  .step {
    flex-direction: row;
    justify-content: center;
  }
}
</style>