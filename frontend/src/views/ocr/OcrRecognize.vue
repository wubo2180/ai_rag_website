<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <div>
          <h2>文件识别</h2>
          <p class="sub">fileId: {{ fileId }} · {{ docTypeText }} · {{ fixVersion }}</p>
        </div>
        <div class="actions">
          <button class="btn" @click="router.push('/ocr/files')">返回列表</button>
          <button class="btn" @click="loadAll">刷新</button>
          <button class="btn primary" :disabled="recognizing" @click="startRecognize">
            {{ recognizing ? '识别中...' : '开始识别' }}
          </button>
          <button class="btn success" :disabled="!hasData || saving" @click="saveToDb">保存入库</button>
          <button class="btn go" :disabled="!hasData" @click="goReview">去核对</button>
        </div>
      </div>

      <div class="panel" v-if="fileInfo">
        <div class="meta-grid">
          <div><b>文件名：</b>{{ fileInfo.filename }}</div>
          <div><b>文档类型：</b>{{ fileInfo.document_type_code || '-' }}</div>
          <div><b>OCR状态：</b>{{ fileInfo.ocr_status || '-' }}</div>
          <div><b>核对状态：</b>{{ fileInfo.review_status || '-' }}</div>
        </div>
      </div>

      <div class="split">
        <div class="panel editor-panel">
          <h3>{{ docTypeText }}数据</h3>
          <component :is="currentForm" v-if="currentForm" v-model="formData" :readonly="false" />
          <el-empty v-else description="暂不支持此文档类型" />
        </div>

        <div class="panel preview-panel">
          <h3>PDF 预览</h3>
          <PdfViewer :file-id="fileId" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import ocrCheckerApi from '@/services/ocrCheckerApi'
import ocrGatewayAPI from '@/services/ocrGateway'
import PaperForm from '@/components/ocr/PaperForm.vue'
import CommissionForm from '@/components/ocr/CommissionForm.vue'
import PdfViewer from '@/components/ocr/PdfViewer.vue'

const route = useRoute()
const router = useRouter()
const fileId = route.params.fileId

const fileInfo = ref(null)
const formData = ref({})
const recognizing = ref(false)
const saving = ref(false)
const hasData = ref(false)
const fixVersion = 'doc-fix-v4'

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms))

const docType = computed(() => String(fileInfo.value?.document_type_code || 'commission').toLowerCase())
const docTypeText = computed(() => (docType.value === 'paper' ? '论文' : '委托单'))
const currentForm = computed(() => (docType.value === 'paper' ? PaperForm : CommissionForm))

const hasDocumentShape = (obj) => {
  if (!obj || typeof obj !== 'object') return false
  return Boolean(
    obj.article_id
    || obj.article_name
    || obj.performance_trend
    || Array.isArray(obj.hierarchical_data)
    || Array.isArray(obj.material_intermediates)
    || typeof obj.basic_info === 'object'
    || Array.isArray(obj.test_items)
    || Array.isArray(obj.special_tests),
  )
}

const extractDocumentPayload = (responseData) => {
  const queue = [responseData]
  const visited = new Set()
  let detectedType = ''

  while (queue.length) {
    const cursor = queue.shift()
    if (!cursor || typeof cursor !== 'object') continue
    if (visited.has(cursor)) continue
    visited.add(cursor)

    if (!detectedType && typeof cursor.document_type === 'string') {
      detectedType = cursor.document_type
    }

    if (hasDocumentShape(cursor)) {
      return {
        documentType: detectedType,
        payload: cursor,
      }
    }

    const candidateKeys = ['data', 'body', 'result', 'payload', 'content']
    candidateKeys.forEach((key) => {
      const nextValue = cursor?.[key]
      if (nextValue && typeof nextValue === 'object') {
        queue.push(nextValue)
      }
    })

    Object.values(cursor).forEach((value) => {
      if (value && typeof value === 'object') {
        queue.push(value)
      }
    })
  }

  return {
    documentType: detectedType,
    payload: {},
  }
}

const normalizeData = (rawData, dt = docType.value) => {
  const normalizedType = String(dt || '').toLowerCase()
  const paperLike = Boolean(
    rawData?.article_id || rawData?.article_name || rawData?.performance_trend
      || Array.isArray(rawData?.hierarchical_data)
      || Array.isArray(rawData?.material_intermediates),
  )

  if (normalizedType === 'paper' || paperLike) {
    return {
      article_id: rawData?.article_id || '',
      article_name: rawData?.article_name || '',
      performance_trend: rawData?.performance_trend || '',
      hierarchical_data: rawData?.hierarchical_data || rawData?.material_intermediates || [],
    }
  }

  return {
    basic_info: rawData?.basic_info || {},
    test_items: rawData?.test_items || [],
    special_tests: rawData?.special_tests || [],
  }
}

const loadFile = async () => {
  const data = await ocrCheckerApi.getFileDetail(fileId)
  fileInfo.value = data?.data || data || null
}

const loadDocumentData = async () => {
  const requestPlans = [
    () => ocrCheckerApi.getDocumentData(fileId),
    () => ocrGatewayAPI.proxyRequest('checker', `files/${fileId}/document-data`, 'GET', null, { refresh: 1 }),
  ]

  for (const request of requestPlans) {
    try {
      const resp = await request()
      const { payload, documentType } = extractDocumentPayload(resp)
      if (hasDocumentShape(payload)) {
        formData.value = normalizeData(payload, documentType || docType.value)
        hasData.value = true
        return
      }
    } catch {
      // 忽略单路失败，继续走下一条兜底路径
    }
  }

  formData.value = normalizeData({}, docType.value)
  hasData.value = false
  ElMessage.warning('未命中有效文档数据，已回退为空模板（可点击“刷新”重试）')
}

const loadAll = async () => {
  try {
    await loadFile()
    await loadDocumentData()
  } catch {
    ElMessage.warning('读取文件信息失败')
  }
}

const startRecognize = async () => {
  recognizing.value = true
  try {
    const data = await ocrCheckerApi.startRecognize(fileId)
    const taskId = data?.data?.task_id

    if (!taskId) {
      ElMessage.success('识别请求已提交')
      await loadAll()
      return
    }

    for (let i = 0; i < 80; i += 1) {
      await sleep(1500)
      const statusData = await ocrCheckerApi.getTaskStatus(taskId)
      const task = statusData?.data || statusData
      const status = task?.status

      if (status === 'completed') {
        ElMessage.success('OCR识别完成')
        break
      }

      if (status === 'failed') {
        throw new Error(task?.error_message || 'OCR任务失败')
      }
    }

    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '识别失败')
  } finally {
    recognizing.value = false
  }
}

const saveToDb = async () => {
  saving.value = true
  try {
    await ocrCheckerApi.saveOcrResult(fileId, formData.value)
    ElMessage.success('已保存入库')
    await loadAll()
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const goReview = () => router.push(`/ocr/review/${fileId}`)

onMounted(loadAll)
</script>

<style scoped>
.ocr-module-page { display:flex; min-height:100vh; background:#f4f7fb; }
.content { flex:1; padding:24px; min-height: 100vh; box-sizing: border-box; }
.toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; gap: 12px; }
.sub { margin:4px 0 0; color:#64748b; font-size:12px; }
.actions { display:flex; gap:8px; flex-wrap: wrap; }
.btn { border:1px solid #dce4f4; background:#fff; padding:6px 12px; border-radius:8px; cursor:pointer; }
.btn.primary { background:#6366f1; color:#fff; border-color:#6366f1; }
.btn.success { background:#16a34a; color:#fff; border-color:#16a34a; }
.btn.go { background:#0891b2; color:#fff; border-color:#0891b2; }
.btn:disabled { opacity:.5; cursor:not-allowed; }
.panel { background:#fff; border:1px solid #e8edf7; border-radius:12px; padding:14px; margin-bottom:12px; }
.meta-grid { display:grid; grid-template-columns:repeat(2,minmax(220px,1fr)); gap:8px; font-size:13px; color:#334155; }
.split {
  display:grid;
  grid-template-columns: minmax(380px, 1fr) minmax(420px, 1fr);
  gap: 12px;
  align-items: stretch;
  min-height: calc(100vh - 220px);
}
.editor-panel { min-height: 600px; }
.preview-panel { min-height: 700px; display: flex; flex-direction: column; }
.preview-panel :deep(.pdf-viewer) { flex: 1; min-height: 0; }
</style>
