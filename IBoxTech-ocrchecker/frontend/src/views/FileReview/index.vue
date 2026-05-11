<template>
  <div class="file-review-container">
    <!-- 顶部工具栏 -->
    <div class="review-toolbar">
      <div class="toolbar-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/files' }">文件管理</el-breadcrumb-item>
          <el-breadcrumb-item>文件核对</el-breadcrumb-item>
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
          <el-tag :type="getOcrStatusType(currentFile.ocr_status)" size="small">
            {{ getOcrStatusText(currentFile.ocr_status) }}
          </el-tag>
          <el-tag v-if="currentFile.review_status === 'completed'" type="success" size="small">
            <el-icon><CircleCheck /></el-icon>
            已核对
          </el-tag>
          <el-tag v-else-if="currentFile.review_status === 'in_progress'" type="warning" size="small">
            核对中
          </el-tag>
          <el-tag v-else type="info" size="small">
            待核对
          </el-tag>
          <span class="file-size">{{ formatFileSize(currentFile.file_size) }}</span>
          <span class="file-pages">{{ currentFile.page_count || 0 }} 页</span>
          <span v-if="currentFile.uploader_name" class="file-uploader">
            上传者：{{ currentFile.uploader_name }}
          </span>
          <span v-if="currentFile.assignment && currentFile.assignment.assigned_to_name" class="file-reviewer">
            审核人：{{ currentFile.assignment.assigned_to_name }}
          </span>
        </div>
      </div>
      
      <div class="toolbar-right">
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
            PDF模式
          </el-button>
        </el-button-group>
        
        <el-button
          type="success"
          :disabled="!hasChanges"
          :loading="isSaving"
          @click="saveOCRChanges"
        >
          <el-icon><Check /></el-icon>
          保存修改
        </el-button>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="review-content" :class="`view-mode-${viewMode}`">
      <!-- 左侧数据编辑区域 -->
      <div v-if="viewMode !== 'pdf'" class="data-panel">
        <div class="panel-header">
          <h3>{{ getDocumentTypeName() }}数据</h3>
          <div class="header-actions">
            <el-button
              size="small"
              @click="refreshFormData"
              :loading="loading.formData"
            >
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button
              size="small"
              @click="exportData"
            >
              <el-icon><Download /></el-icon>
              导出
            </el-button>
            <el-button
              v-if="!isEditing"
              type="primary"
              size="small"
              @click="startEditing"
            >
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <template v-else>
              <el-button
                type="primary"
                size="small"
                @click="saveChanges"
                :loading="isSaving"
              >
                <el-icon><Check /></el-icon>
                保存
              </el-button>
              <el-button
                size="small"
                @click="cancelEditing"
              >
                <el-icon><Close /></el-icon>
                取消
              </el-button>
            </template>
          </div>
        </div>
        
        <div class="panel-content">
          <!-- 数据加载状态 -->
          <div v-if="loading.formData" class="loading-container">
            <el-skeleton :rows="8" animated />
          </div>
          
          <!-- 动态表单组件 -->
          <component
            v-else-if="currentFormComponent && formData"
            :is="currentFormComponent"
            v-model="formData"
            :readonly="!isEditing"
            @update:modelValue="markAsChanged"
          />
          
          <div v-else class="empty-data">
            <el-icon class="empty-icon"><Document /></el-icon>
            <p>暂无数据</p>
          </div>
        </div>
      </div>

      <!-- 右侧PDF预览区域 -->
      <div v-if="viewMode !== 'data'" class="pdf-panel">
        <div class="panel-header">
          <h3>PDF预览</h3>
          <div class="header-actions">
            <el-tooltip content="橙色高亮表示识别置信度低于80%的内容，需要重点关注" placement="bottom">
              <el-icon style="margin-right: 8px; color: #e6a23c;"><WarningFilled /></el-icon>
            </el-tooltip>
            <el-switch
              v-model="showHighlight"
              active-text="显示高亮"
              @change="toggleHighlight"
            />
          </div>
        </div>
        
        <div class="panel-content">
          <PdfViewer
            v-if="pdfUrl"
            :url="pdfUrl"
            :initial-page="currentPageData"
            :show-highlight="showHighlight"
            :ocr-regions="ocrRegions"
            :active-region-id="activeRegionId"
            @page-change="handlePageChange"
            @region-select="handleRegionSelect"
            @ready="handlePdfReady"
          />
          <div v-else class="pdf-loading">
            <el-icon class="loading-icon"><Loading /></el-icon>
            <p>加载PDF中...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部操作栏 -->
    <div class="review-footer">
      <div class="footer-left">
        <div v-if="commissionData && commissionData.ocr_result" class="ocr-stats">
          <div class="stat-item">
            <span class="stat-label">总字段数:</span>
            <span class="stat-value">{{ commissionData.ocr_result.total_fields || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">成功识别:</span>
            <span class="stat-value success">{{ commissionData.ocr_result.recognized_fields || 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">平均置信度:</span>
            <span class="stat-value">{{ commissionData.ocr_result.avg_confidence || '未知' }}</span>
          </div>
        </div>
      </div>
      
      <div class="footer-right">
        <el-button @click="goBack">返回列表</el-button>
        <el-button
          v-if="hasChanges"
          @click="resetChanges"
        >
          重置修改
        </el-button>
        <el-button
          type="success"
          :disabled="!canComplete"
          @click="completeReview"
        >
          <el-icon><CircleCheckFilled /></el-icon>
          完成核对
        </el-button>
      </div>
    </div>

    <!-- 变更历史对话框 -->
    <el-dialog
      v-model="historyDialog.visible"
      title="修改历史"
      width="800px"
    >
      <div class="history-list">
        <!-- 历史记录内容 -->
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, onBeforeUnmount, markRaw } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { filesApi } from '@/api/files'
import { documentsApi } from '@/api/documents'  // 统一文档API
import PdfViewer from '@/components/PdfViewer/index.vue'

// 动态导入表单组件
import PaperForm from '@/components/PaperForm/index.vue'
import CommissionForm from '@/components/CommissionForm/index.vue'
import { 
  ElMessage, 
  ElMessageBox,
  ElNotification 
} from 'element-plus'
import {
  Check,
  Edit,
  Close,
  Refresh,
  Download,
  Document,
  Grid,
  List,
  Operation,
  MagicStick,
  DocumentChecked,
  Plus,
  Delete,
  CircleCheck,
  CircleCheckFilled,
  WarningFilled
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

// 响应式数据
const currentFile = ref(null)
const pdfUrl = ref('')
const viewMode = ref('split')
const currentPageData = ref(1)
const showHighlight = ref(true)

const loading = reactive({
  fileData: false,
  ocrData: false,
  formData: false,  // 统一的表单数据加载状态
  saving: false
})

const isSaving = ref(false)
const hasChanges = ref(false)

// OCR数据
const ocrPages = ref([])
const currentPageOCR = ref(null)
const ocrRegions = ref({})
const activeRegionId = ref(null)

// 表单数据 (统一的formData，替代commissionData)
const formData = ref(null)
const originalFormData = ref(null)
const isEditing = ref(false)

// OCR编辑数据
const originalData = ref({
  table: [],
  form: {}
})
const editableTableData = ref([])
const editableFormData = ref({})

// 委托数据（用于显示OCR统计信息）
const commissionData = computed(() => {
  // 如果是委托单类型，返回formData，否则返回null
  if (currentFile.value?.document_type_code === 'commission' && formData.value) {
    return formData.value
  }
  return null
})

// 动态组件计算属性
const currentFormComponent = computed(() => {
  if (!currentFile.value) return null
  
  const docType = currentFile.value.document_type_code
  console.log('🧩 [FileReview] 当前文档类型:', docType)
  
  if (docType === 'paper') {
    return markRaw(PaperForm)
  } else if (docType === 'commission') {
    return markRaw(CommissionForm)
  }
  
  // 默认使用CommissionForm（向后兼容）
  return markRaw(CommissionForm)
})

// 计算属性
const getDocumentTypeName = () => {
  if (!currentFile.value) return '文档'
  
  const docType = currentFile.value.document_type_code
  if (docType === 'paper') return '论文'
  if (docType === 'commission') return '委托'
  return '文档'
}

const canComplete = computed(() => {
  // 只要委托数据加载成功就可以完成核对，不要求必须有修改
  return true
})

const historyDialog = reactive({
  visible: false
})

// 方法
const initReview = async () => {
  const fileId = route.params.fileId
  if (!fileId) {
    router.push('/files')
    return
  }

  await loadFileData(fileId)
  await loadFormData(fileId)  // 统一的表单数据加载
  await loadOCRData(fileId)
  await loadPdfUrl(fileId)
}

const loadFileData = async (fileId) => {
  try {
    loading.fileData = true
    const response = await filesApi.getFileDetail(fileId)
    
    if (response.data.success) {
      currentFile.value = response.data.data
    } else {
      throw new Error(response.data.message)
    }
  } catch (error) {
    console.error('加载文件数据失败:', error)
    ElMessage.error('加载文件数据失败')
    router.push('/files')
  } finally {
    loading.fileData = false
  }
}

const loadOCRData = async (fileId) => {
  try {
    loading.ocrData = true
    
    // 从已加载的文件数据中获取OCR结果
    if (currentFile.value && currentFile.value.ocr_results) {
      const ocrResults = currentFile.value.ocr_results
      console.log('📋 OCR原始数据:', ocrResults)
      
      // 如果OCR结果是JSON字符串，解析它
      let parsedResults = ocrResults
      if (typeof ocrResults === 'string') {
        try {
          parsedResults = JSON.parse(ocrResults)
        } catch (e) {
          console.error('OCR结果解析失败:', e)
          parsedResults = []
        }
      }
      
      // 转换为页面数据格式
      if (Array.isArray(parsedResults) && parsedResults.length > 0) {
        ocrPages.value = parsedResults
        console.log('✅ OCR数据加载成功，共', parsedResults.length, '页')
        
        if (parsedResults.length > 0) {
          switchPage(1)
        }
      } else if (parsedResults && typeof parsedResults === 'object') {
        // 如果是单页对象，转换为数组
        ocrPages.value = [{ page_number: 1, ...parsedResults }]
        switchPage(1)
      } else {
        console.warn('⚠️ OCR结果为空或格式不正确')
        ocrPages.value = []
      }
    } else {
      console.warn('⚠️ 文件中没有OCR结果数据')
      ocrPages.value = []
    }
    
    // 构建OCR区域映射
    buildOCRRegions()
    
  } catch (error) {
    console.error('加载OCR数据失败:', error)
    ElMessage.error('加载OCR数据失败')
    ocrPages.value = []
  } finally {
    loading.ocrData = false
  }
}

const loadPdfUrl = async (fileId) => {
  try {
    console.log('正在获取PDF文件内容, fileId:', fileId)
    
    // 先尝试预签名URL
    try {
      const previewResponse = await filesApi.getPreviewUrl(fileId)
      console.log('预览URL响应:', previewResponse.data)
      
      if (previewResponse.data.success && previewResponse.data.data.url && !previewResponse.data.data.fallback) {
        // 如果获得了有效的预签名URL且不是回退模式
        pdfUrl.value = previewResponse.data.data.url
        console.log('使用预签名URL:', pdfUrl.value)
        return
      }
    } catch (previewError) {
      console.warn('预签名URL获取失败，尝试下载文件:', previewError.message)
    }
    
    // 回退方案：通过认证下载文件，转换为Blob URL
    console.log('使用文件下载方案')
    const downloadResponse = await filesApi.downloadFile(fileId, true)
    console.log('文件下载响应:', downloadResponse)
    
    // 创建Blob URL
    const blob = new Blob([downloadResponse.data], { type: 'application/pdf' })
    console.log('Blob创建信息:', {
      size: blob.size,
      type: blob.type,
      dataType: typeof downloadResponse.data,
      dataSize: downloadResponse.data?.size || downloadResponse.data?.length || 'unknown'
    })
    
    // 检查是否是有效的PDF数据
    const arrayBuffer = await blob.arrayBuffer()
    const uint8Array = new Uint8Array(arrayBuffer)
    const pdfHeader = String.fromCharCode(...uint8Array.slice(0, 4))
    console.log('PDF文件头:', pdfHeader, '应该是: %PDF')
    
    if (pdfHeader !== '%PDF') {
      console.error('下载的数据不是有效的PDF文件')
      ElMessage.error('下载的数据不是有效的PDF文件')
      return
    }
    
    const blobUrl = URL.createObjectURL(blob)
    pdfUrl.value = blobUrl
    console.log('PDF Blob URL创建成功:', blobUrl)
    
  } catch (error) {
    console.error('获取PDF文件失败:', error)
    ElMessage.error(`获取PDF文件失败: ${error.response?.data?.message || error.message}`)
  }
}

const buildOCRRegions = () => {
  const regions = {}
  const LOW_CONFIDENCE_THRESHOLD = 0.8 // 80%
  
  ocrPages.value.forEach(page => {
    regions[page.page_number] = []
    
    // 添加手写区域（通常置信度较低）
    if (page.handwriting_regions) {
      page.handwriting_regions.forEach(region => {
        const confidence = region.confidence || 0
        regions[page.page_number].push({
          ...region,
          type: 'handwriting',
          lowConfidence: confidence < LOW_CONFIDENCE_THRESHOLD
        })
      })
    }
    
    // 添加表格中置信度低的单元格
    if (page.table_data && page.table_data.rows) {
      page.table_data.rows.forEach((row, rowIndex) => {
        if (Array.isArray(row)) {
          row.forEach((cell, colIndex) => {
            if (cell && typeof cell === 'object') {
              const confidence = cell.confidence ? cell.confidence / 100 : 1
              if (confidence < LOW_CONFIDENCE_THRESHOLD && cell.bbox) {
                regions[page.page_number].push({
                  id: `table-${rowIndex}-${colIndex}`,
                  text: cell.value || '',
                  confidence: confidence,
                  bbox: cell.bbox,
                  type: 'table-cell',
                  lowConfidence: true
                })
              }
            }
          })
        }
      })
    }
    
    // 添加表单字段中置信度低的字段
    if (page.form_fields) {
      Object.entries(page.form_fields).forEach(([key, field]) => {
        if (field && typeof field === 'object') {
          const confidence = field.confidence ? field.confidence / 100 : 1
          if (confidence < LOW_CONFIDENCE_THRESHOLD && field.bbox) {
            regions[page.page_number].push({
              id: `form-${key}`,
              text: field.value || '',
              confidence: confidence,
              bbox: field.bbox,
              type: 'form-field',
              lowConfidence: true
            })
          }
        }
      })
    }
  })
  
  ocrRegions.value = regions
  console.log('📍 构建OCR区域完成，低置信度区域:', regions)
}

const switchPage = (pageNumber) => {
  const pageData = ocrPages.value.find(p => p.page_number === pageNumber)
  if (!pageData) return
  
  currentPageOCR.value = pageData
  currentPageData.value = pageNumber
  
  // 初始化编辑数据
  if (pageData.table_data?.rows) {
    editableTableData.value = JSON.parse(JSON.stringify(pageData.table_data.rows))
  }
  
  if (pageData.form_fields) {
    editableFormData.value = JSON.parse(JSON.stringify(pageData.form_fields))
  }
  
  // 保存原始数据
  originalData.value = {
    table: JSON.parse(JSON.stringify(editableTableData.value)),
    form: JSON.parse(JSON.stringify(editableFormData.value))
  }
}

const setViewMode = (mode) => {
  viewMode.value = mode
}

// 表单数据加载（统一的入口）
const loadFormData = async (fileId) => {
  if (!currentFile.value) {
    console.warn('⚠️ currentFile为空，无法判断文档类型')
    return
  }
  
  const docType = currentFile.value.document_type_code
  console.log('📋 [loadFormData] 文档类型:', docType)
  
  if (docType === 'paper') {
    await loadPaperData(fileId)
  } else {
    await loadCommissionData(fileId)
  }
}

// 论文数据加载
const loadPaperData = async (fileId) => {
  try {
    loading.formData = true
    console.log('🔍 [loadPaperData] 开始加载论文数据, fileId:', fileId)
    
    const response = await documentsApi.getDocumentData(fileId)
    console.log('📥 [loadPaperData] 论文数据API响应:', response.data)
    
    if (response.data.success && response.data.data) {
      const documentType = response.data.document_type
      const backendData = response.data.data
      
      console.log(`📄 文档类型: ${documentType}`)
      
      // 确认是论文类型
      if (documentType === 'paper') {
        // 转换后端数据格式为前端期望的格式
        formData.value = {
          article_id: backendData.article_id || '',
          article_name: backendData.article_name || '',
          performance_trend: backendData.performance_trend || '',
          // 将 material_intermediates 转换为 hierarchical_data
          hierarchical_data: (backendData.material_intermediates || []).map(mi => ({
            material_id: mi.material_id || '',
            material_name: mi.material_name || '',
            cas_number: mi.cas_number || '',
            intermediate_id: mi.intermediate_id || '',
            intermediate_name: mi.intermediate_name || '',
            intermediate_composition: mi.intermediate_composition || '',
            properties: (mi.properties || []).map(p => ({
              property_id: p.property_id || '',
              property_name: p.property_name || '',
              property_value: p.property_value || ''
            }))
          }))
        }
        
        console.log('✅ [loadPaperData] 论文数据加载成功，hierarchical_data长度:', formData.value.hierarchical_data.length)
      } else {
        console.warn('⚠️ [loadPaperData] 文档类型不匹配，期望 paper，实际:', documentType)
        formData.value = createEmptyPaperData()
      }
    } else {
      console.warn('⚠️ [loadPaperData] 没有找到论文数据，创建空数据结构')
      formData.value = createEmptyPaperData()
    }
  } catch (error) {
    console.error('❌ [loadPaperData] 加载论文数据失败:', error)
    formData.value = createEmptyPaperData()
  } finally {
    loading.formData = false
  }
}

// 创建空论文数据结构
const createEmptyPaperData = () => {
  return {
    article_id: '',
    article_name: '',
    performance_trend: '',
    hierarchical_data: []
  }
}

// 委托数据相关方法
const loadCommissionData = async (fileId) => {
  try {
    loading.formData = true  // 改用formData
    console.log('🔍 开始加载委托数据, fileId:', fileId)
    
    const response = await documentsApi.getDocumentData(fileId)
    console.log('📥 委托数据API响应:', response.data)
    
    if (response.data.success && response.data.data) {
      formData.value = initializeCommissionData(response.data.data)  // 改用formData
      console.log('✅ 委托数据加载成功:', formData.value)
    } else {
      console.warn('⚠️ 没有找到委托数据，创建空数据结构')
      formData.value = initializeCommissionData({})
    }
  } catch (error) {
    console.error('❌ 加载委托数据失败:', error)
    console.error('错误详情:', error.response?.data || error.message)
    formData.value = initializeCommissionData({})
  } finally {
    loading.formData = false  // 改用formData
    console.log('🏁 委托数据加载完成，formData:', formData.value)
  }
}

const initializeCommissionData = (data) => {
  console.log('🔧 初始化委托数据:', data)
  
  // 初始化默认数据结构 - 对应 CommissionBasic 模型字段
  const defaultBasicInfo = {
    // 基本标识信息
    form_number: '',
    commission_number: '',
    service_type: '',
    need_report: '',
    project_number: '',        // 研发项目
    material_number: '',       // 物料代码
    product_number: '',        // 产品或原材料型号
    sample_weight: '',         // 样品重量
    
    // 委托信息
    commission_department: '',
    commissioner: '',
    commission_date: '',
    commission_address: '',
    
    // 样品信息
    sample_name: '',
    sample_quantity: '',
    sample_code: '',
    sample_batch: '',
    delivery_time: '',
    required_time: '',
    sample_disposal: '',
    storage_method: '',
    
    // 测试信息
    test_nature: '',
    test_description: '',
    special_condition_flag: '',
    special_condition_detail: '',
    
    // 人员信息
    tester: '',
    data_reviewer: '',
    review_date: '',
    
    // 审核检查项
    form_complete: '',
    sample_info_consistent: '',
    sample_condition_ok: '',
    other_notes: '',
    
    // 签名信息
    delivery_person_signature: '',
    business_receiver_signature: ''
  }
  
  // 默认测试项目结构 - 对应 TestItem 模型字段
  const defaultTestItem = {
    test_item: '',
    test_equipment: '',
    test_standard: '',
    test_condition: '',
    product_standard: '',
    unit: '',
    test_result: '',
    tester: '',
    remark: '',
    sort_order: 0
  }
  
  // 默认特殊测试结构 - 对应 SpecialTest 模型字段
  const defaultSpecialTest = {
    test_type: '',
    element_name: '',
    standard_value: '',
    measured_value: '',
    remark: '',
    sort_order: 0
  }
  
  const result = {
    basic_info: { ...defaultBasicInfo, ...(data.basic_info || {}) },
    test_items: (data.test_items || []).map(item => ({ ...defaultTestItem, ...item })),
    special_tests: (data.special_tests || []).map(test => ({ ...defaultSpecialTest, ...test })),
    ocr_result: data.ocr_result || null,
    commission_number: data.commission_number || ''
  }
  
  console.log('🔧 初始化结果:', result)
  return result
}

const refreshFormData = async () => {
  const fileId = route.params.fileId || route.params.id
  console.log('🔄 刷新表单数据，fileId:', fileId)
  await loadFormData(fileId)
}

const startEditing = () => {
  // 保存原始数据的深拷贝
  originalFormData.value = JSON.parse(JSON.stringify(formData.value))
  isEditing.value = true
  ElMessage.info('进入编辑模式')
}

const cancelEditing = () => {
  ElMessageBox.confirm(
    '确定要取消编辑吗？未保存的修改将会丢失。',
    '取消编辑',
    {
      confirmButtonText: '确定取消',
      cancelButtonText: '继续编辑',
      type: 'warning'
    }
  ).then(() => {
    // 恢复原始数据
    formData.value = JSON.parse(JSON.stringify(originalFormData.value))
    isEditing.value = false
    ElMessage.success('已取消编辑')
  }).catch(() => {
    // 用户选择继续编辑，不做任何操作
  })
}

const saveChanges = async () => {
  try {
    isSaving.value = true
    const docType = currentFile.value?.document_type_code
    
    if (docType === 'paper') {
      await savePaperData()
    } else {
      await saveCommissionData()
    }
    
    isEditing.value = false
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败，请重试')
  } finally {
    isSaving.value = false
  }
}

const markAsChanged = () => {
  hasChanges.value = true
}

// 保存论文数据
const savePaperData = async () => {
  try {
    const fileId = route.params.fileId || route.params.id
    console.log('💾 [savePaperData] 保存论文数据，fileId:', fileId)
    console.log('💾 [savePaperData] 表单数据:', formData.value)
    
    // 使用统一接口保存
    const response = await documentsApi.saveDocumentData(fileId, formData.value)
    
    if (response.data.success) {
      hasChanges.value = false
      console.log('✅ [savePaperData] 论文数据保存成功')
    } else {
      throw new Error(response.data.message || '保存失败')
    }
  } catch (error) {
    console.error('❌ [savePaperData] 保存论文数据失败:', error)
    throw error
  }
}

const saveCommissionData = async () => {
  if (!formData.value || !hasChanges.value) return
  
  try {
    isSaving.value = true
    
    const fileId = route.params.fileId || route.params.id
    console.log('💾 保存委托数据，fileId:', fileId)
    
    // 使用统一接口保存
    const response = await documentsApi.saveDocumentData(fileId, formData.value)
    
    if (response.data.success) {
      ElMessage.success('委托数据保存成功')
      hasChanges.value = false
      // 重新加载数据
      await loadCommissionData(fileId)
    } else {
      ElMessage.error(response.data.message || '保存失败')
    }
  } catch (error) {
    console.error('保存委托数据失败:', error)
    ElMessage.error('保存失败')
  } finally {
    isSaving.value = false
  }
}

const getOcrStatusType = (status) => {
  const statusMap = {
    'pending': 'warning',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'approved': 'success',
    'rejected': 'danger'
  }
  return statusMap[status] || 'info'
}

const saveOCRChanges = async () => {
  try {
    isSaving.value = true
    
    // 构建保存数据
    const saveData = {
      page_number: currentPageData.value,
      table_data: editableTableData.value.length ? { rows: editableTableData.value } : null,
      form_fields: editableFormData.value
    }
    
    // 调用保存API
    // await api.saveReviewChanges(currentFile.value.id, saveData)
    
    ElMessage.success('OCR数据保存成功')
    hasChanges.value = false
    
  } catch (error) {
    console.error('OCR数据保存失败:', error)
    ElMessage.error('OCR数据保存失败')
  } finally {
    isSaving.value = false
  }
}

const resetChanges = () => {
  editableTableData.value = JSON.parse(JSON.stringify(originalData.value.table))
  editableFormData.value = JSON.parse(JSON.stringify(originalData.value.form))
  hasChanges.value = false
}

const completeReview = async () => {
  try {
    await ElMessageBox.confirm(
      '确认完成核对吗？完成后文件将标记为已核对状态。',
      '确认操作',
      {
        confirmButtonText: '确认完成',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 从路由参数获取fileId
    const fileId = route.params.fileId || route.params.id
    console.log('✅ 完成核对，fileId:', fileId)
    
    // 调用API完成核对
    const response = await filesApi.completeReview(fileId)
    console.log('📥 [completeReview] 完成核对API响应:', response.data)
    
    if (response.data.success) {
      ElMessage.success('核对已完成')
      // 返回文件列表
      router.push('/files')
    } else {
      ElMessage.error(response.data.message || '完成核对失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('完成核对失败:', error)
      ElMessage.error('完成核对失败，请重试')
    }
  }
}

const addTableRow = () => {
  const newRow = new Array(tableColumns.value.length).fill('')
  editableTableData.value.push(newRow)
  markAsChanged()
}

const deleteTableRow = (index) => {
  editableTableData.value.splice(index, 1)
  markAsChanged()
}

const highlightTableCell = (rowIndex, colIndex) => {
  // 高亮对应的PDF区域
}

const highlightFormField = (fieldKey) => {
  // 高亮对应的PDF区域
}

const highlightHandwritingRegion = (region) => {
  activeRegionId.value = region.id
}

const enhanceHandwriting = async (region) => {
  try {
    region.enhancing = true
    // 调用手写增强API
    await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟API调用
    ElMessage.success('手写识别增强完成')
  } catch (error) {
    console.error('手写增强失败:', error)
    ElMessage.error('手写增强失败')
  } finally {
    region.enhancing = false
  }
}

const refreshData = () => {
  loadOCRData(currentFile.value.id)
}

const exportData = () => {
  // 导出数据逻辑
}

const toggleHighlight = (show) => {
  showHighlight.value = show
}

const handlePageChange = (pageNumber) => {
  switchPage(pageNumber)
}

const handleRegionSelect = (region) => {
  activeRegionId.value = region.id
}

const handlePdfReady = (info) => {
  // PDF加载完成
}

const goBack = () => {
  if (hasChanges.value) {
    ElMessageBox.confirm(
      '有未保存的修改，确认离开吗？',
      '确认离开',
      {
        confirmButtonText: '确认离开',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).then(() => {
      router.push('/files')
    })
  } else {
    router.push('/files')
  }
}

const getCurrentPageConfidence = () => {
  if (!currentPageOCR.value) return 0
  return Math.round(currentPageOCR.value.confidence_score * 100)
}


const getOcrStatusText = (status) => {
  const statusMap = {
    pending: '待处理',
    processing: '处理中',
    completed: '已完成',
    failed: '失败'
  }
  return statusMap[status] || '未知'
}

const formatFileSize = (size) => {
  const units = ['B', 'KB', 'MB', 'GB']
  let index = 0
  let fileSize = size
  
  while (fileSize >= 1024 && index < units.length - 1) {
    fileSize /= 1024
    index++
  }
  
  return `${fileSize.toFixed(1)} ${units[index]}`
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


// 生命周期
onMounted(() => {
  initReview()
})

// 组件销毁时清理Blob URL
onBeforeUnmount(() => {
  if (pdfUrl.value && pdfUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(pdfUrl.value)
    console.log('🧹 Blob URL已清理:', pdfUrl.value)
  }
})

// 路由守卫
onBeforeRouteLeave((to, from) => {
  if (hasChanges.value) {
    const answer = window.confirm('有未保存的修改，确认离开吗？')
    if (!answer) return false
  }
})
</script>

<style lang="scss" scoped>
.file-review-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-color-page;
}

.review-toolbar {
  @include flex-between;
  padding: $spacing-md;
  background: $bg-color-white;
  border-bottom: 1px solid $border-color-lighter;
  flex-shrink: 0;
  
  .toolbar-left {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
    
    .filename-text {
      display: inline-block;
      max-width: 300px;
      cursor: help;
    }
    
    .file-info {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      font-size: 12px;
      color: $text-color-secondary;
      flex-wrap: wrap;
      
      .el-tag {
        margin: 0;
      }
      
      .file-uploader,
      .file-reviewer {
        padding: 2px 8px;
        background: $bg-color-lighter;
        border-radius: 4px;
        font-size: 12px;
      }
    }
  }
  
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: $spacing-md;
  }
}

.review-content {
  flex: 1;
  display: flex;
  min-height: 0;
  
  &.view-mode-split {
    .data-panel {
      width: 50%;
      border-right: 1px solid $border-color-lighter;
    }
    
    .pdf-panel {
      width: 50%;
    }
  }
  
  &.view-mode-data {
    .data-panel {
      width: 100%;
    }
    
    .pdf-panel {
      display: none;
    }
  }
  
  &.view-mode-pdf {
    .data-panel {
      display: none;
    }
    
    .pdf-panel {
      width: 100%;
    }
  }
}

.data-panel,
.pdf-panel {
  display: flex;
  flex-direction: column;
  background: $bg-color-white;
  
  .panel-header {
    @include flex-between;
    padding: $spacing-md;
    border-bottom: 1px solid $border-color-lighter;
    flex-shrink: 0;
    
    h3 {
      font-size: 16px;
      font-weight: 500;
      color: $text-color-primary;
      margin: 0;
    }
    
    .header-actions {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
    }
  }
  
  .panel-content {
    flex: 1;
    overflow: auto;
    padding: $spacing-md;
    min-height: 0; // 确保flex子元素能正确计算高度
  }
}

.page-selector {
  @include flex-between;
  margin-bottom: $spacing-md;
  
  .page-confidence {
    font-size: 12px;
    color: $text-color-secondary;
  }
}

.data-editor {
  .section-header {
    @include flex-between;
    margin-bottom: $spacing-md;
    
    h4 {
      font-size: 14px;
      font-weight: 500;
      color: $text-color-primary;
      margin: 0;
    }
  }
  
  .table-section,
  .form-section,
  .handwriting-section {
    margin-bottom: $spacing-xl;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
}

.table-editor {
  :deep(.el-table) {
    .el-table__cell {
      padding: 4px;
      
      .el-input__inner {
        border: none;
        padding: 4px 8px;
      }
    }
  }
}

.commission-editor {
  .section-container {
    background: $bg-color-white;
    border-radius: 8px;
    border: 1px solid $border-color-light;
    overflow: hidden;
    margin-bottom: 16px;

    .section-header {
      padding: 16px 20px;
      background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
      border-bottom: 1px solid $border-color-light;
      display: flex;
      justify-content: space-between;
      align-items: center;

      h4 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: $text-color-primary;
        display: flex;
        align-items: center;
        gap: 8px;

        .el-icon {
          font-size: 18px;
          color: $color-primary;
        }
      }

      .section-actions {
        display: flex;
        gap: 8px;
      }
    }

    .form-section-title {
      font-size: 14px;
      font-weight: 600;
      color: $text-color-regular;
      margin: 20px 0 8px 0;
      padding-bottom: 8px;
      border-bottom: 1px solid $border-color-lighter;
      position: relative;

      &:before {
        content: '';
        position: absolute;
        left: 0;
        bottom: -1px;
        width: 30px;
        height: 2px;
        background: $color-primary;
      }
    }

    .el-form {
      padding: 20px;
    }
  }

  // 测试项目卡片样式
  .test-items-list, .special-tests-list {
    padding: 20px;

    .test-item-card, .special-test-card {
      background: $bg-color-page;
      border-radius: 6px;
      border: 1px solid $border-color-lighter;
      margin-bottom: 16px;
      overflow: hidden;
      transition: all 0.2s;

      &:hover {
        border-color: $color-primary;
        box-shadow: 0 2px 8px rgba(64, 158, 255, 0.1);
      }

      .card-header {
        background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 100%);
        padding: 12px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid $border-color-lighter;

        .item-number {
          font-size: 14px;
          font-weight: 600;
          color: $text-color-regular;
        }
      }

      .el-form {
        padding: 16px;
      }
    }
  }

  // 空状态样式
  .empty-list {
    text-align: center;
    padding: 40px 20px;
    color: $text-color-placeholder;

    .el-icon {
      font-size: 48px;
      margin-bottom: 16px;
      color: $border-color-base;
    }

    p {
      margin: 0 0 16px 0;
      font-size: 14px;
    }
  }
}

.form-editor {
  .form-field {
    margin-bottom: $spacing-md;
    
    .field-label {
      display: block;
      font-size: 12px;
      color: $text-color-regular;
      margin-bottom: $spacing-xs;
    }
    
    .field-confidence {
      font-size: 11px;
      color: $text-color-placeholder;
      margin-top: 4px;
    }
  }
}

.handwriting-list {
  .handwriting-item {
    border: 1px solid $border-color-lighter;
    border-radius: $border-radius-base;
    padding: $spacing-md;
    margin-bottom: $spacing-md;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .item-header {
      @include flex-between;
      margin-bottom: $spacing-sm;
      
      .item-label {
        font-size: 12px;
        color: $text-color-regular;
        font-weight: 500;
      }
    }
    
    .el-textarea {
      margin-bottom: $spacing-sm;
    }
  }
}

.pdf-loading {
  @include flex-center;
  flex-direction: column;
  height: 100%;
  color: $text-color-secondary;
  
  .loading-icon {
    font-size: 48px;
    margin-bottom: $spacing-md;
  }
}

.empty-data {
  @include flex-center;
  flex-direction: column;
  height: 200px;
  color: $text-color-placeholder;
  
  .empty-icon {
    font-size: 48px;
    margin-bottom: $spacing-md;
  }
}

.review-footer {
  @include flex-between;
  padding: $spacing-md;
  background: $bg-color-white;
  border-top: 1px solid $border-color-lighter;
  flex-shrink: 0;
  
  .footer-left {
    .ocr-stats {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .stat-item {
        display: flex;
        align-items: center;
        gap: 4px;
        
        .stat-label {
          font-size: 12px;
          color: $text-color-secondary;
          white-space: nowrap;
        }
        
        .stat-value {
          font-size: 13px;
          font-weight: 600;
          color: $text-color-primary;
          
          &.success {
            color: $color-success;
          }
        }
      }
    }
  }
  
  .footer-right {
    display: flex;
    gap: $spacing-sm;
  }
}

.loading-container {
  padding: $spacing-md;
}

// 响应式设计
@include respond-to(lg) {
  .review-content.view-mode-split {
    flex-direction: column;
    
    .data-panel,
    .pdf-panel {
      width: 100%;
      height: 50%;
      border-right: none;
      border-bottom: 1px solid $border-color-lighter;
      
      &:last-child {
        border-bottom: none;
      }
    }
  }
}

@include respond-to(sm) {
  .review-toolbar {
    flex-direction: column;
    align-items: flex-start;
    gap: $spacing-md;
    
    .toolbar-right {
      width: 100%;
      justify-content: flex-end;
    }
  }
  
  .review-footer {
    flex-direction: column;
    gap: $spacing-md;
    
    .footer-left,
    .footer-right {
      width: 100%;
      justify-content: center;
    }
    
    .footer-right {
      .el-button {
        flex: 1;
      }
    }
  }
}

</style>
