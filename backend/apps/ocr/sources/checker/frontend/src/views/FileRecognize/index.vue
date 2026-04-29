<template>
  <div class="file-recognize-container">
    <!-- 顶部工具栏 -->
    <div class="recognize-toolbar">
      <div class="toolbar-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/files' }">文件管理</el-breadcrumb-item>
          <el-breadcrumb-item>文件识别</el-breadcrumb-item>
          <el-breadcrumb-item v-if="currentFile">
            <el-tooltip 
              :content="currentFile.filename" 
              placement="bottom"
              :disabled="currentFile.filename.length <= 30"
            >
              <span class="filename-text">{{ truncateFilename(currentFile.filename) }}</span>
            </el-tooltip>
          </el-breadcrumb-item>
        </el-breadcrumb>
        
        <div v-if="currentFile" class="file-info">
          <!-- 文档类型标签 -->
          <el-tag type="primary" size="small">
            <el-icon><Document /></el-icon>
            {{ documentTypeName }}
          </el-tag>
          
          <el-tag :type="getOcrStatusType(currentFile.ocr_status)" size="small">
            {{ getOcrStatusText(currentFile.ocr_status) }}
          </el-tag>
          
          <span class="file-size">{{ formatFileSize(currentFile.file_size) }}</span>
          <span v-if="currentFile.uploader_name" class="file-uploader">
            上传者：{{ currentFile.uploader_name }}
          </span>
        </div>
      </div>
      
      <div class="toolbar-right">
        <!-- OCR识别按钮 -->
        <el-button
          type="primary"
          :loading="isRecognizing"
          :disabled="!currentFile"
          @click="handleOcrRecognizeClick"
        >
          <el-icon><MagicStick /></el-icon>
          {{ hasOcrData ? '重新识别' : 'OCR识别' }}
        </el-button>
        
        <!-- 视图模式切换 -->
        <el-button-group>
          <el-button
            :type="viewMode === 'split' ? 'primary' : ''"
            @click="setViewMode('split')"
          >
            <el-icon><Grid /></el-icon>
            分屏模式
          </el-button>
          <el-button
            :type="viewMode === 'data' ? 'primary' : ''"
            @click="setViewMode('data')"
          >
            <el-icon><List /></el-icon>
            数据模式
          </el-button>
          <el-button
            :type="viewMode === 'pdf' ? 'primary' : ''"
            @click="setViewMode('pdf')"
          >
            <el-icon><Document /></el-icon>
            文件模式
          </el-button>
        </el-button-group>
        
        <!-- 保存按钮 -->
        <el-button
          type="success"
          :disabled="!hasOcrData"
          :loading="isSaving"
          @click="saveToDatabase"
        >
          <el-icon><Check /></el-icon>
          保存入库
        </el-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="recognize-content" :class="`view-mode-${viewMode}`">
      <!-- 左侧数据编辑区域 -->
      <div v-if="viewMode !== 'pdf'" class="data-panel">
        <div class="panel-header">
          <h3>{{ documentTypeName }}数据</h3>
          <el-tag v-if="hasChanges" type="warning" size="small">
            <el-icon><Edit /></el-icon>
            已修改
          </el-tag>
        </div>
        
        <div class="panel-content">
          <!-- 加载状态 -->
          <div v-if="loading.formData" class="loading-container">
            <el-skeleton :rows="10" animated />
          </div>
          
          <!-- 无数据提示 -->
          <el-empty
            v-else-if="!formData"
            description="暂无数据，请先进行OCR识别"
            :image-size="150"
          >
            <el-button type="primary" @click="startOcrRecognize">
              <el-icon><MagicStick /></el-icon>
              开始识别
            </el-button>
          </el-empty>
          
          <!-- 根据文件类型动态渲染表单 -->
          <component
            v-else
            :is="currentFormComponent"
            ref="formRef"
            v-model="formData"
            :readonly="false"
            @validate="handleFormValidate"
          />
        </div>
      </div>

      <!-- 右侧文件预览区域 -->
      <div v-if="viewMode !== 'data'" class="preview-panel">
        <div class="panel-header">
          <h3>文件预览</h3>
        </div>
        
        <div class="panel-content">
          <PdfViewer
            v-if="pdfUrl"
            :url="pdfUrl"
            @ready="handlePdfReady"
          />
          <div v-else class="pdf-loading">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>加载PDF中...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, markRaw, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  MagicStick,
  Grid,
  List,
  Check,
  Edit,
  Loading
} from '@element-plus/icons-vue'

// 导入PdfViewer组件
import PdfViewer from '@/components/PdfViewer/index.vue'

// 动态导入表单组件
import PaperForm from '@/components/PaperForm/index.vue'
import CommissionForm from '@/components/CommissionForm/index.vue'

// API
import { filesApi } from '@/api/files'
import { recognizeApi } from '@/api/recognize'
import { documentsApi } from '@/api/documents'  // 统一文档API

const route = useRoute()
const router = useRouter()

// ==================== 响应式数据 ====================

const currentFile = ref(null)
const pdfUrl = ref('')
const viewMode = ref('split')
const formRef = ref(null)

const loading = reactive({
  fileData: false,
  formData: false,
  pdfUrl: false
})

const isRecognizing = ref(false)
const isSaving = ref(false)
const hasOcrData = ref(false)
const hasChanges = ref(false)

// 表单数据（通用）
const formData = ref(null)
const originalFormData = ref(null)

// ==================== 计算属性 ====================

// 文档类型名称
const documentTypeName = computed(() => {
  if (!currentFile.value) return '文档'
  
  const typeMap = {
    'paper': '论文',
    'commission': '委托单'
  }
  
  return typeMap[currentFile.value.document_type_code] || '文档'
})

// 当前使用的表单组件
const currentFormComponent = computed(() => {
  if (!currentFile.value) return null
  
  const docType = currentFile.value.document_type_code
  
  switch (docType) {
    case 'paper':
      return markRaw(PaperForm)
    case 'commission':
      return markRaw(CommissionForm)
    default:
      return null
  }
})

// OCR状态类型
const getOcrStatusType = (status) => {
  const typeMap = {
    'pending': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return typeMap[status] || 'info'
}

// OCR状态文本
const getOcrStatusText = (status) => {
  const textMap = {
    'pending': '待识别',
    'processing': '识别中',
    'completed': '已识别',
    'failed': '识别失败'
  }
  return textMap[status] || '未知'
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 截断文件名
const truncateFilename = (filename, maxLength = 30) => {
  if (!filename || filename.length <= maxLength) {
    return filename
  }
  
  // 获取文件扩展名
  const lastDotIndex = filename.lastIndexOf('.')
  const extension = lastDotIndex > 0 ? filename.substring(lastDotIndex) : ''
  const nameWithoutExt = lastDotIndex > 0 ? filename.substring(0, lastDotIndex) : filename
  
  // 计算可用于显示名称的长度（保留扩展名和省略号）
  const availableLength = maxLength - extension.length - 3 // 3 for '...'
  
  if (availableLength <= 0) {
    return filename.substring(0, maxLength - 3) + '...'
  }
  
  // 截断名称，保留扩展名
  return nameWithoutExt.substring(0, availableLength) + '...' + extension
}

// ==================== 方法 ====================

// 设置视图模式
const setViewMode = (mode) => {
  viewMode.value = mode
}

// 加载文件信息
const loadFileData = async (fileId) => {
  try {
    loading.fileData = true
    
    console.log(`\n${'='.repeat(60)}`)
    console.log('🔍 [loadFileData] 开始加载文件信息')
    console.log('📝 文件ID:', fileId)
    
    const response = await filesApi.getFileDetail(fileId)
    
    console.log('📡 API响应:', response)
    console.log('✅ 响应状态:', response.status)
    console.log('📦 响应数据:', response.data)
    
    if (response.data.success) {
      currentFile.value = response.data.data
      console.log('📄 文件信息:', currentFile.value)
      console.log('📑 文档类型:', currentFile.value.document_type_code)
      
      // 加载对应的表单数据
      await loadFormData(fileId)
    } else {
      console.error('❌ API返回失败:', response.data.message)
      throw new Error(response.data.message)
    }
  } catch (error) {
    console.error('❌ [loadFileData] 加载文件信息失败')
    console.error('❌ 错误类型:', error.constructor.name)
    console.error('❌ 错误信息:', error.message)
    console.error('❌ 错误详情:', error)
    console.error('❌ 错误堆栈:', error.stack)
    console.log(`${'='.repeat(60)}\n`)
    
    ElMessage.error('加载文件信息失败: ' + (error.message || '未知错误'))
    router.push('/files')
  } finally {
    loading.fileData = false
  }
}

// 统一加载文档数据（自动识别文档类型）
const loadFormData = async (fileId) => {
  try {
    loading.formData = true
    
    console.log('📋 开始加载文档数据, fileId:', fileId)
    
    // 使用统一接口获取数据
    const response = await documentsApi.getDocumentData(fileId)
    
    console.log('📦 统一API响应:', response.data)
    
    if (response.data.success) {
      const documentData = response.data.data
      const documentType = response.data.document_type
      
      console.log(`📄 文档类型: ${documentType}`)
      
      // 检查数据是否为 null 或 undefined
      if (!documentData) {
        console.log(`ℹ️ 暂无${documentType === 'paper' ? '论文' : '委托单'}数据（可能未识别）`)
        
        // 根据文档类型初始化空表单结构
        if (documentType === 'paper') {
          formData.value = {
            article_id: '',
            article_name: '',
            performance_trend: '',
            hierarchical_data: []
          }
        } else if (documentType === 'commission') {
          formData.value = {
            basic_info: {},
            test_items: [],
            special_tests: []
          }
        }
        
        hasOcrData.value = false
        return
      }
      
      // 根据文档类型处理数据
      if (documentType === 'paper') {
        // 论文数据：转换为前端表单格式
        console.log('📄 原始论文数据:', documentData)
        formData.value = convertPaperApiToForm(documentData)
        console.log('📝 转换后的表单数据:', formData.value)
      } else if (documentType === 'commission') {
        // 委托单数据：直接使用
        // 检查数据是否真的存在（不是空结构）
        const hasBasicInfo = documentData.basic_info && Object.keys(documentData.basic_info).length > 0
        const hasTestItems = documentData.test_items && documentData.test_items.length > 0
        const hasSpecialTests = documentData.special_tests && documentData.special_tests.length > 0
        
        if (hasBasicInfo || hasTestItems || hasSpecialTests) {
          formData.value = documentData
        } else {
          console.log('⚠️ 委托单数据为空结构')
          formData.value = {
            basic_info: {},
            test_items: [],
            special_tests: []
          }
          hasOcrData.value = false
          return
        }
      }
      
      originalFormData.value = JSON.parse(JSON.stringify(formData.value))
      hasOcrData.value = true
      console.log(`✅ ${documentType === 'paper' ? '论文' : '委托单'}数据加载成功`)
    } else {
      console.warn('⚠️ 文档数据获取失败:', response.data.message)
      hasOcrData.value = false
    }
    
  } catch (error) {
    console.error('❌ 加载文档数据异常:', error.message)
    console.log('🔍 错误详情:', error)
    hasOcrData.value = false
    // 不显示错误，因为可能是第一次识别，没有数据
  } finally {
    loading.formData = false
  }
}

// 加载PDF预览
const loadPdfUrl = async (fileId) => {
  try {
    loading.pdfUrl = true
    
    const response = await filesApi.getPreviewUrl(fileId)
    
    if (response.data.success) {
      let url = response.data.data.url
      
      // 如果是回退URL（通过后端下载接口），需要添加token参数
      if (response.data.data.fallback) {
        const token = localStorage.getItem('access_token')
        if (token) {
          url = `${url}?token=${token}&preview=true`
          console.log('📄 使用回退URL（带token）:', url)
        }
      } else {
        console.log('📄 使用MinIO预签名URL:', url)
      }
      
      pdfUrl.value = url
    }
  } catch (error) {
    console.error('加载PDF预览失败:', error)
  } finally {
    loading.pdfUrl = false
  }
}

// 处理OCR识别点击（添加确认逻辑）
const handleOcrRecognizeClick = async () => {
  // 如果已有OCR数据，提示用户确认是否重新识别
  if (hasOcrData.value) {
    try {
      await ElMessageBox.confirm(
        '当前已有识别数据，重新识别将覆盖现有数据。是否继续？',
        '确认重新识别',
        {
          confirmButtonText: '确认',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      // 用户确认后执行识别
      await startOcrRecognize()
    } catch {
      // 用户取消，不做任何操作
      console.log('用户取消了重新识别')
    }
  } else {
    // 没有数据，直接识别
    await startOcrRecognize()
  }
}

// OCR识别
const startOcrRecognize = async () => {
  let pollInterval = null
  let processingMessageInstance = null
  
  try {
    isRecognizing.value = true
    
    const loadingMessage = ElMessage.info({
      message: '正在创建OCR识别任务...',
      duration: 0,
      showClose: true
    })
    
    const fileId = route.params.fileId
    console.log('📄 [OCR] 开始识别，文件ID:', fileId)
    console.log('📑 [OCR] 文档类型:', currentFile.value.document_type_code)
    
    // 创建异步OCR任务
    const apiResponse = await recognizeApi.recognize(fileId)
    const response = apiResponse.data
    
    if (!response.success) {
      loadingMessage.close()
      ElMessage.error(response.message || 'OCR识别任务创建失败')
      isRecognizing.value = false
      return
    }
    
    const taskId = response.data.task_id
    console.log('✅ [OCR] 任务已创建，task_id:', taskId)
    
    loadingMessage.close()
    
    // 显示新的处理中消息（设置较短的 duration，不手动关闭）
    processingMessageInstance = ElMessage.info({
      message: 'OCR识别任务处理中...',
      duration: 0,  // 不自动关闭，等任务完成后手动处理
      showClose: true
    })
    
    // 轮询任务状态
    let pollCount = 0
    const maxPolls = 120
    
    // 使用 Promise 来处理轮询结果
    const pollTask = new Promise((resolve, reject) => {
      pollInterval = setInterval(async () => {
        pollCount++
        
        try {
          console.log(`⏱️ [OCR] 开始第 ${pollCount} 次轮询...`)
          const taskResponse = await recognizeApi.getTaskStatus(taskId)
          
          console.log('📡 [OCR] 轮询响应:', taskResponse)
          const task = taskResponse.data.data.task
          console.log(`🔄 [OCR] 轮询 ${pollCount}/${maxPolls}, 状态: ${task.status}`)
          
          if (task.status === 'completed') {
            clearInterval(pollInterval)
            pollInterval = null
            
            const ocrResult = taskResponse.data.data.ocr_result
            console.log('✅ [OCR] 识别完成！')
            
            if (ocrResult && ocrResult.structured_data) {
              console.log('✅ [OCR] 找到 structured_data')
            } else {
              console.warn('⚠️ [OCR] 没有找到 structured_data')
            }
            
            resolve({ success: true, data: ocrResult })
            
          } else if (task.status === 'failed') {
            clearInterval(pollInterval)
            pollInterval = null
            console.error('❌ [OCR] 任务失败:', task.error_message)
            reject(new Error(task.error_message || '未知错误'))
            
          } else if (pollCount >= maxPolls) {
            clearInterval(pollInterval)
            pollInterval = null
            console.warn('⏰ [OCR] 轮询超时')
            reject(new Error('OCR识别超时'))
          } else {
            console.log(`⏳ [OCR] 任务处理中... 进度: ${task.progress || 0}%`)
          }
          
        } catch (error) {
          clearInterval(pollInterval)
          pollInterval = null
          console.error('❌ [OCR] 查询任务状态失败:', error)
          reject(error)
        }
      }, 1000)
    })
    
    // 等待轮询完成
    const result = await pollTask
    
    // ⭐ 关键修改：先处理数据，再关闭消息
    // 处理OCR结果，自动填充表单
    await handleOcrResult(result.data)
    
    // ⭐ 使用 setTimeout 延迟关闭旧消息和显示新消息
    setTimeout(() => {
      // 关闭处理中的消息
      if (processingMessageInstance) {
        processingMessageInstance.close()
        processingMessageInstance = null
      }
      // 再延迟一点显示成功消息
      setTimeout(() => {
        ElMessage.success('OCR识别完成！')
        isRecognizing.value = false
      }, 50)
    }, 50)
    
  } catch (error) {
    console.error('OCR识别失败:', error)
    
    // 清理 interval
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
    
    // 使用 setTimeout 延迟关闭消息和显示错误
    setTimeout(() => {
      if (processingMessageInstance) {
        processingMessageInstance.close()
        processingMessageInstance = null
      }
      setTimeout(() => {
        if (error.message === 'OCR识别超时') {
          ElMessage.warning('OCR识别超时，请稍后刷新页面查看')
        } else {
          ElMessage.error('OCR识别失败：' + error.message)
        }
        isRecognizing.value = false
      }, 50)
    }, 50)
  }
}

// 处理OCR结果，自动填充表单
const handleOcrResult = async (ocrResult) => {
  try {
    console.log('🔍 [handleOcrResult] 接收到OCR结果:', ocrResult)
    console.log('🔍 [handleOcrResult] OCR结果类型:', typeof ocrResult)
    console.log('🔍 [handleOcrResult] OCR结果键:', ocrResult ? Object.keys(ocrResult) : 'null')
    
    const docType = currentFile.value.document_type_code
    console.log('📋 [handleOcrResult] 文档类型:', docType)
    
    if (docType === 'paper') {
      // 处理论文OCR结果
      console.log('📄 [handleOcrResult] 处理论文OCR结果')
      formData.value = convertPaperOcrToForm(ocrResult)
      console.log('📝 [handleOcrResult] 转换后的表单数据:', formData.value)
    } else if (docType === 'commission') {
      // 处理委托单OCR结果
      console.log('📋 [handleOcrResult] 处理委托单OCR结果')
      formData.value = convertCommissionOcrToForm(ocrResult)
      console.log('📝 [handleOcrResult] 转换后的表单数据:', formData.value)
    }
    
    originalFormData.value = JSON.parse(JSON.stringify(formData.value))
    hasOcrData.value = true
    hasChanges.value = false
    
    console.log('✅ OCR结果已填充到表单')
    console.log('📊 formData.value:', JSON.stringify(formData.value, null, 2))
    console.log('🎯 hasOcrData:', hasOcrData.value)
    
  } catch (error) {
    console.error('❌ 处理OCR结果失败:', error)
    console.error('❌ 错误堆栈:', error.stack)
    ElMessage.warning('OCR结果填充失败，请手动输入')
  }
}

// 转换论文OCR结果到表单格式
const convertPaperOcrToForm = (ocrResult) => {
  console.log('🔄 [convertPaperOcrToForm] 开始转换论文OCR结果')
  console.log('📦 [convertPaperOcrToForm] ocrResult:', ocrResult)
  
  // 检查OCR结果结构
  if (ocrResult && ocrResult.structured_data) {
    const data = ocrResult.structured_data
    console.log('✅ [convertPaperOcrToForm] 找到structured_data:', data)
    console.log('📋 [convertPaperOcrToForm] structured_data键:', Object.keys(data))
    console.log('📋 [convertPaperOcrToForm] hierarchical_data:', data.hierarchical_data)
    console.log('📋 [convertPaperOcrToForm] hierarchical_data类型:', typeof data.hierarchical_data)
    console.log('📋 [convertPaperOcrToForm] hierarchical_data是数组吗?', Array.isArray(data.hierarchical_data))
    
    // 转换hierarchical_data中的中文字段名为英文
    let mappedHierarchicalData = []
    
    if (data.hierarchical_data && Array.isArray(data.hierarchical_data)) {
      console.log('📋 [convertPaperOcrToForm] hierarchical_data长度:', data.hierarchical_data.length)
      
      if (data.hierarchical_data.length > 0) {
        console.log('📋 [convertPaperOcrToForm] 第一个元素原始数据:', data.hierarchical_data[0])
        console.log('📋 [convertPaperOcrToForm] 第一个元素的键:', Object.keys(data.hierarchical_data[0]))
      }
      
      // 字段映射：中文 -> 英文
      mappedHierarchicalData = data.hierarchical_data.map((item, index) => {
        console.log(`🔄 [convertPaperOcrToForm] 处理第 ${index + 1} 个材料/中间体`)
        
        const mappedItem = {
          material_id: item['材料编号'] || item['材料编号（Material ID）'] || '',
          material_name: item['原材料名称'] || item['原材料名称（Material Name）'] || '',
          cas_number: item['CAS号'] || item['CAS号（CAS Number）'] || '',
          intermediate_id: item['中间体编号'] || item['中间体编号（Intermediate ID）'] || '',
          intermediate_name: item['中间体名称'] || item['中间体名称（Intermediate Name）'] || '',
          intermediate_composition: item['中间体组成'] || item['中间体组成（Intermediate Compositions）'] || '',
          properties: []
        }
        
        // 转换性能数据
        const properties = item['性能'] || item['性能（Properties）'] || []
        if (Array.isArray(properties)) {
          mappedItem.properties = properties.map((prop, pIndex) => {
            const mappedProp = {
              property_id: prop['性能编号'] || prop['性能编号（Property ID）'] || '',
              property_name: prop['性能名称'] || prop['性能名称（Property Name）'] || '',
              property_value: prop['性能值'] || prop['性能值（Property Value）'] || ''
            }
            console.log(`  ✓ 性能 ${pIndex + 1}: ${mappedProp.property_id} - ${mappedProp.property_name}`)
            return mappedProp
          })
        }
        
        console.log(`  ✅ 映射完成: 材料 ${mappedItem.material_id}, 中间体 ${mappedItem.intermediate_id}, ${mappedItem.properties.length} 个性能`)
        return mappedItem
      })
      
      console.log('✅ [convertPaperOcrToForm] hierarchical_data映射完成，共', mappedHierarchicalData.length, '个元素')
    }
    
    const formResult = {
      article_id: data.article_id || '',
      article_name: data.article_name || '',
      performance_trend: data.performance_trend || '',
      hierarchical_data: mappedHierarchicalData
    }
    
    console.log('✅ [convertPaperOcrToForm] 转换结果:', formResult)
    console.log('📊 [convertPaperOcrToForm] 转换后hierarchical_data长度:', formResult.hierarchical_data.length)
    return formResult
  }
  
  console.warn('⚠️ [convertPaperOcrToForm] 未找到structured_data，返回空结构')
  
  // 默认空结构
  return {
    article_id: '',
    article_name: '',
    performance_trend: '',
    hierarchical_data: []
  }
}

// 转换委托单OCR结果到表单格式
const convertCommissionOcrToForm = (ocrResult) => {
  console.log('🔄 [convertCommissionOcrToForm] 开始转换委托单OCR结果')
  console.log('📦 [convertCommissionOcrToForm] ocrResult:', ocrResult)
  
  if (ocrResult && ocrResult.structured_data) {
    const data = ocrResult.structured_data
    console.log('✅ [convertCommissionOcrToForm] 找到structured_data:', data)
    console.log('📋 [convertCommissionOcrToForm] structured_data键:', Object.keys(data))
    console.log('📋 [convertCommissionOcrToForm] basic_info内容:', data.basic_info)
    console.log('📋 [convertCommissionOcrToForm] basic_info字段:', data.basic_info ? Object.keys(data.basic_info) : 'empty')
    
    // 字段映射：OCR中文字段名 -> 表单英文字段名
    const fieldMapping = {
      // 基本标识
      '表格编号': 'form_number',
      '委托编号': 'commission_number',
      '服务类型': 'service_type',
      
      // 项目信息
      '需要报告': 'need_report',
      '是否需要报告': 'need_report',
      '研发项目': 'project_number',
      '项目编号': 'project_number',
      '物料代码': 'material_number',
      '产品或原材料型号': 'product_number',
      '产品型号': 'product_number',
      
      // 样品信息
      '样品重量': 'sample_weight',
      '样品名称': 'sample_name',
      '样品数量': 'sample_quantity',
      '样品编号': 'sample_code',
      '样品代码': 'sample_code',
      '样品批号': 'sample_batch',
      '样品批次': 'sample_batch',
      '样品储存方式': 'storage_method',
      '贮存方法': 'storage_method',
      '样品处置': 'sample_disposal',
      '余样处理': 'sample_disposal',
      
      // 委托信息
      '委托部门': 'commission_department',
      '委托人': 'commissioner',
      '委托日期': 'commission_date',
      '委托地址': 'commission_address',
      
      // 时间相关
      '交货时间': 'delivery_time',
      '送样时间': 'delivery_time',
      '要求时间': 'required_time',
      '需求时间': 'required_time',
      '复核日期': 'review_date',
      
      // 测试相关
      '测试性质': 'test_nature',
      '测试说明': 'test_description',
      '测试员': 'tester',
      '数据复核人': 'data_reviewer',
      
      // 特殊条件
      '有无特殊条件': 'special_condition_flag',
      '特殊条件详情': 'special_condition_detail',
      '条件是': 'special_condition_detail',
      
      // 签字确认字段
      '送样人签名': 'delivery_person_signature',
      '业务受理人签字': 'business_handler_signature',
      '样品是否完好': 'sample_condition',
      '样品实物信息是否一致': 'sample_info_consistent',
      '申请单是否填写完整': 'form_complete',
      
      // 其他信息
      '其他备注': 'other_notes',
      '备注': 'other_notes',
      '备注信息': 'other_notes',
      
      // 其他字段（备用）
      '接收人签字': 'receiver_signature',
      '其他检查项': 'other_inspection',
      '样品完好': 'sample_intact',
      '填写完整': 'form_complete_flag'
    }
    
    // 转换basic_info字段名
    const mappedBasicInfo = {}
    
    // 定义表单中实际存在的字段列表
    const validFormFields = [
      'form_number', 'commission_number', 'service_type', 'need_report',
      'project_number', 'material_number', 'product_number', 'sample_weight',
      'commission_department', 'commissioner', 'commission_date', 'commission_address',
      'sample_name', 'sample_quantity', 'sample_code', 'sample_batch',
      'delivery_time', 'required_time', 'sample_disposal', 'storage_method',
      'test_nature', 'test_description', 'special_condition_flag', 'special_condition_detail',
      'tester', 'data_reviewer', 'review_date',
      // 新增：签字确认字段
      'delivery_person_signature', 'business_handler_signature', 
      'sample_condition', 'sample_info_consistent', 'form_complete',
      // 新增：其他信息
      'other_notes'
    ]
    
    if (data.basic_info && typeof data.basic_info === 'object') {
      console.log('🔄 [convertCommissionOcrToForm] 开始映射字段...')
      for (const [chineseName, value] of Object.entries(data.basic_info)) {
        const englishName = fieldMapping[chineseName] || chineseName
        
        // 只保留表单中存在的字段
        if (validFormFields.includes(englishName)) {
          mappedBasicInfo[englishName] = value
          console.log(`   ✅ 映射并保留: "${chineseName}" -> "${englishName}" = "${value}"`)
        } else if (fieldMapping[chineseName]) {
          console.log(`   ⚠️ 映射但跳过（表单无此字段）: "${chineseName}" -> "${englishName}" = "${value}"`)
        } else {
          console.log(`   ⚠️ 未映射且跳过: "${chineseName}" = "${value}"`)
        }
      }
    }
    
    const formResult = {
      basic_info: mappedBasicInfo,
      test_items: data.test_items || [],
      special_tests: data.special_tests || []
    }
    
    console.log('✅ [convertCommissionOcrToForm] 转换结果:', formResult)
    console.log('📊 [convertCommissionOcrToForm] 映射后的字段数:', Object.keys(formResult.basic_info).length)
    return formResult
  }
  
  console.warn('⚠️ [convertCommissionOcrToForm] 未找到structured_data，返回空结构')
  
  // 默认空结构
  return {
    basic_info: {},
    test_items: [],
    special_tests: []
  }
}

// 转换论文API数据到表单格式
const convertPaperApiToForm = (apiData) => {
  // 后端返回的是英文字段名，直接转换为表单格式
  return {
    article_id: apiData.article_id || '',
    article_name: apiData.article_name || '',
    performance_trend: apiData.performance_trend || '',
    hierarchical_data: (apiData.material_intermediates || []).map(item => ({
      material_id: item.material_id || '',
      material_name: item.material_name || '',
      cas_number: item.cas_number || '',
      intermediate_id: item.intermediate_id || '',
      intermediate_name: item.intermediate_name || '',
      intermediate_composition: item.intermediate_composition || '',
      properties: (item.properties || []).map(prop => ({
        property_id: prop.property_id || '',
        property_name: prop.property_name || '',
        property_value: prop.property_value || ''
      }))
    }))
  }
}

// 统一保存到数据库（自动识别文档类型）
const saveToDatabase = async () => {
  try {
    // 验证表单
    if (formRef.value) {
      const isValid = await formRef.value.validate()
      if (!isValid) {
        ElMessage.warning('请检查表单，确保所有必填项已填写')
        return
      }
    }
    
    // 确认保存
    await ElMessageBox.confirm(
      `确定要保存${documentTypeName.value}数据吗？`,
      '确认保存',
      {
        type: 'info',
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }
    )
    
    isSaving.value = true
    
    const fileId = route.params.fileId
    
    console.log('💾 开始保存文档数据, fileId:', fileId)
    
    // 使用统一接口保存OCR结果
    const response = await documentsApi.saveOcrResult(fileId, formData.value)
    
    if (response.data.success) {
      const documentType = response.data.document_type
      console.log(`✅ ${documentType === 'paper' ? '论文' : '委托单'}数据保存成功`)
      
      ElMessage.success('保存成功！')
      hasChanges.value = false
      
      // 刷新数据
      await loadFormData(fileId)
    } else {
      throw new Error(response.data.message || '保存失败')
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('❌ 保存失败:', error)
      ElMessage.error(error.response?.data?.message || error.message || '保存失败')
    }
  } finally {
    isSaving.value = false
  }
}

// 表单验证回调
const handleFormValidate = (isValid) => {
  console.log('表单验证结果:', isValid)
}

// PDF预览准备完成回调
const handlePdfReady = () => {
  console.log('✅ PDF预览加载完成')
}

// 监听表单数据变化
watch(
  () => formData.value,
  (newVal, oldVal) => {
    if (newVal && oldVal && originalFormData.value) {
      hasChanges.value = JSON.stringify(newVal) !== JSON.stringify(originalFormData.value)
    }
  },
  { deep: true }
)

// ==================== 生命周期 ====================

onMounted(async () => {
  const fileId = route.params.fileId
  
  if (!fileId) {
    ElMessage.error('缺少文件ID参数')
    router.push('/files')
    return
  }
  
  console.log('📄 识别页面加载，文件ID:', fileId)
  
  // 加载数据
  await loadFileData(fileId)
  await loadPdfUrl(fileId)
})
</script>

<style scoped lang="scss">
.file-recognize-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f0f2f5;

  .recognize-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px 24px;
    background: #fff;
    border-bottom: 1px solid #e4e7ed;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

    .toolbar-left {
      flex: 1;
      
      .filename-text {
        display: inline-block;
        max-width: 300px;
        cursor: help;
      }

      .file-info {
        margin-top: 12px;
        display: flex;
        gap: 12px;
        align-items: center;
        font-size: 14px;
        color: #606266;

        .file-size,
        .file-uploader {
          color: #909399;
        }
      }
    }

    .toolbar-right {
      display: flex;
      gap: 12px;
    }
  }

  .recognize-content {
    flex: 1;
    display: flex;
    overflow: hidden;

    &.view-mode-split {
      .data-panel {
        flex: 1;
      }
      .preview-panel {
        flex: 1;
      }
    }

    &.view-mode-data {
      .data-panel {
        flex: 1;
      }
      .preview-panel {
        display: none;
      }
    }

    &.view-mode-pdf {
      .data-panel {
        display: none;
      }
      .preview-panel {
        flex: 1;
      }
    }

    .data-panel,
    .preview-panel {
      background: #fff;
      box-shadow: 0 2px 2px rgba(0, 0, 0, 0.08);
      display: flex;
      flex-direction: column;
      overflow: hidden;

      .panel-header {
        padding: 16px 20px;
        border-bottom: 1px solid #e4e7ed;
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }

      .panel-content {
        flex: 1;
        overflow: hidden;
        position: relative;

        .pdf-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100%;
          color: #909399;

          .loading-icon {
            font-size: 48px;
            margin-bottom: 16px;
            animation: rotate 1s linear infinite;
          }

          @keyframes rotate {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }

          p {
            font-size: 14px;
            margin: 0;
          }
        }
      }
    }

    // 数据面板特殊样式 - 需要滚动
    .data-panel {
      .panel-content {
        overflow-y: auto;
        padding: 0px;
      }
    }

    // PDF预览面板特殊样式 - 不需要padding，让PdfViewer占满
    .preview-panel {
      .panel-content {
        overflow: hidden;
        padding: 0;
      }
    }
  }
}
</style>

