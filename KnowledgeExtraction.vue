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
      // 如果是文本格式结果，尝试解析JSON并填充到表格
      if (typeof extractionResult.value.extracted_knowledge === 'string') {
        parseTextToTableData(extractionResult.value.extracted_knowledge)
      }
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

/* 材料属性表格样式 */
.materials-table-section {
  margin-top: 2rem;
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
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
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.materials-table-header i {
  color: #667eea;
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
  background: #667eea;
  color: white;
  padding: 0.75rem 0.5rem;
  text-align: center;
  font-weight: 600;
  font-size: 0.9rem;
  border: 1px solid #5a6fd8;
}

.materials-table th.merged-header {
  background: #5a6fd8;
  font-size: 0.85rem;
  padding: 0.5rem;
}

.materials-table td {
  padding: 0.5rem;
  border: 1px solid #ecf0f1;
  text-align: center;
}

.table-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.9rem;
  box-sizing: border-box;
  transition: border-color 0.3s ease;
}

.table-input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
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