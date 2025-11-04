<template>
  <div class="knowledge-extraction-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <i class="fas fa-book-open"></i>
          知识抽取智能体
        </h1>
        <p class="page-description">
          从文档中智能提取结构化知识，支持PDF、Word、文本等多种格式
        </p>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 文件上传区域 -->
      <div class="upload-section">
        <div class="upload-card">
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
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import apiClient from '@/utils/api'
import { ElMessage } from 'element-plus'

// 响应式数据
const uploadedFile = ref(null)
const isDragOver = ref(false)
const processing = ref(false)
const currentStep = ref(1)
const extractionResult = ref(null)
const errorMessage = ref('')
const viewMode = ref('cards')
const fileInput = ref(null)

// 计算属性
const hasResults = computed(() => {
  return extractionResult.value || errorMessage.value
})

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
    formData.append('user_id', 'web_user')
    
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
      ElMessage.success('知识抽取完成！')
    } else {
      throw new Error(response.data.message || '处理失败')
    }
    
  } catch (error) {
    console.error('知识抽取失败:', error)
    errorMessage.value = error.response?.data?.message || error.message || '处理失败，请重试'
    ElMessage.error(errorMessage.value)
  } finally {
    processing.value = false
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
</script>

<style scoped>
.knowledge-extraction-container {
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
  text-align: center;
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

.main-content {
  display: grid;
  grid-template-columns: 1fr;
  gap: 2rem;
}

/* 上传区域 */
.upload-section {
  grid-row: 1;
}

.upload-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.upload-area {
  border: 3px dashed #ddd;
  border-radius: 15px;
  padding: 3rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.upload-area:hover {
  border-color: #667eea;
  background: #f0f8ff;
}

.upload-area.drag-over {
  border-color: #667eea;
  background: #e6f3ff;
  transform: scale(1.02);
}

.upload-placeholder i {
  font-size: 4rem;
  color: #667eea;
  margin-bottom: 1rem;
}

.upload-placeholder h3 {
  font-size: 1.5rem;
  color: #2c3e50;
  margin-bottom: 0.5rem;
}

.upload-placeholder p {
  color: #7f8c8d;
  margin-bottom: 2rem;
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
  background: white;
  padding: 1rem 1.5rem;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
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
  margin-top: 2rem;
  text-align: center;
}

/* 结果区域 */
.results-section {
  grid-row: 2;
}

.results-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #ecf0f1;
}

.results-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #2c3e50;
  margin: 0;
}

.results-header i {
  color: #f39c12;
}

.results-stats {
  display: flex;
  gap: 1rem;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.loading-container {
  text-align: center;
  padding: 3rem;
}

.loading-spinner i {
  font-size: 3rem;
  color: #667eea;
  margin-bottom: 1rem;
}

.loading-spinner p {
  font-size: 1.2rem;
  color: #2c3e50;
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
  color: #667eea;
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
  padding: 0.5rem 1rem;
  border: 2px solid #ecf0f1;
  background: white;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.toggle-btn:hover {
  border-color: #667eea;
}

.toggle-btn.active {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* 卡片视图 */
.cards-view {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.knowledge-card {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  border: 1px solid #ecf0f1;
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
  color: #2c3e50;
}

.card-index {
  background: #667eea;
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
  color: #34495e;
  margin-bottom: 0.3rem;
  font-size: 0.9rem;
}

.field-value {
  background: #f8f9fa;
  padding: 0.75rem;
  border-radius: 8px;
  border-left: 3px solid #667eea;
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
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.results-table th {
  background: #667eea;
  color: white;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
}

.results-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #ecf0f1;
}

.index-cell {
  background: #f8f9fa;
  font-weight: 600;
  color: #667eea;
  text-align: center;
  width: 60px;
}

.data-cell {
  max-width: 200px;
  word-break: break-word;
}

/* JSON视图 */
.json-view {
  background: #2d3748;
  border-radius: 8px;
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
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
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
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background: #d5dbdb;
  transform: translateY(-2px);
}

.btn-info {
  background: #3498db;
  color: white;
}

.btn-info:hover {
  background: #2980b9;
  transform: translateY(-2px);
}

.btn-lg {
  padding: 1rem 2rem;
  font-size: 1.1rem;
}

.btn-sm {
  padding: 0.5rem 0.75rem;
  font-size: 0.9rem;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .knowledge-extraction-container {
    padding: 1rem;
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