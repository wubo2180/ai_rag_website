<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <h2>OCR 文件管理</h2>
        <div class="actions">
          <div class="type-filters">
            <button
              class="btn filter-btn"
              :class="{ active: selectedDocumentType === 'all' }"
              :disabled="loading"
              @click="switchDocumentType('all')"
            >
              全部
            </button>
            <button
              class="btn filter-btn"
              :class="{ active: selectedDocumentType === 'paper' }"
              :disabled="loading"
              @click="switchDocumentType('paper')"
            >
              论文
            </button>
            <button
              class="btn filter-btn"
              :class="{ active: selectedDocumentType === 'commission' }"
              :disabled="loading"
              @click="switchDocumentType('commission')"
            >
              委托单
            </button>
          </div>
          <span class="filter-indicator">当前筛选：{{ selectedDocumentTypeLabel }}</span>
          <button class="btn" @click="router.push('/ocr-center')">返回OCR中心</button>
          <button class="btn" @click="fetchFiles(currentPage)">刷新</button>
          <label class="check-option">
            <input v-model="onlyPendingForBatch" type="checkbox" />
            仅识别待识别
          </label>
          <button
            class="btn"
            :disabled="loading || batchRecognizing || selectedCount === 0"
            @click="batchRecognizeSelected"
          >
            {{ batchRecognizing ? '批量识别中...' : `批量识别（${batchTargetCount}）` }}
          </button>
          <button class="btn primary" @click="router.push('/ocr/upload')">上传文件</button>
        </div>
      </div>

      <div class="panel">
        <div class="pagination-bar">
          <div class="pagination-summary">
            共 {{ total }} 个文件，第 {{ currentPage }} / {{ displayTotalPages }} 页
          </div>
          <div class="pagination-actions">
            <button class="page-btn" :disabled="loading || currentPage <= 1" @click="changePage(1)">首页</button>
            <button class="page-btn" :disabled="loading || currentPage <= 1" @click="changePage(currentPage - 1)">上一页</button>
            <button
              v-for="page in visiblePages"
              :key="`top-${page}`"
              class="page-btn"
              :class="{ active: page === currentPage }"
              :disabled="loading"
              @click="changePage(page)"
            >
              {{ page }}
            </button>
            <button class="page-btn" :disabled="loading || currentPage >= displayTotalPages" @click="changePage(currentPage + 1)">下一页</button>
            <button class="page-btn" :disabled="loading || currentPage >= displayTotalPages" @click="changePage(displayTotalPages)">末页</button>
          </div>
        </div>

        <table class="table">
          <thead>
            <tr>
              <th class="checkbox-col">
                <input
                  type="checkbox"
                  :checked="allSelectedOnPage"
                  :disabled="loading || files.length === 0"
                  @change="toggleSelectAllOnPage"
                />
              </th>
              <th>ID</th>
              <th>文件名</th>
              <th>类型</th>
              <th>上传时间</th>
              <th>OCR 状态</th>
              <th>核对状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in files" :key="item.id">
              <td class="checkbox-col">
                <input
                  type="checkbox"
                  :value="item.id"
                  v-model="selectedIds"
                  :disabled="loading || batchRecognizing"
                />
              </td>
              <td>{{ item.id }}</td>
              <td>{{ item.filename }}</td>
              <td>{{ getDocumentTypeText(item.document_type_code) }}</td>
              <td>{{ formatTime(item.created_at) }}</td>
              <td>
                <span
                  v-if="getOcrStatusText(item?.ocr_status)"
                  class="status-hint"
                  :class="getOcrStatusClass(item?.ocr_status)"
                >
                  {{ getOcrStatusText(item?.ocr_status) }}
                </span>
                <span v-else>-</span>
              </td>
              <td>
                <span
                  v-if="getReviewStatusText(item?.review_status)"
                  class="status-hint"
                  :class="getReviewStatusClass(item?.review_status)"
                >
                  {{ getReviewStatusText(item?.review_status) }}
                </span>
                <span v-else>-</span>
              </td>
              <td class="ops-cell">
                <div class="action-group">
                  <button class="action-btn action-primary" @click="goRecognize(item)">
                    {{ recognizeActionLabel(item) }}
                  </button>
                  <button class="action-btn" @click="goReview(item)">进入核对</button>
                  <button
                    class="action-btn danger"
                    :disabled="deletingId === item.id"
                    @click="removeFile(item)"
                  >
                    {{ deletingId === item.id ? '删除中...' : '删除文件' }}
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && files.length === 0">
              <td colspan="8" class="empty">暂无数据</td>
            </tr>
            <tr v-if="loading">
              <td colspan="8" class="empty">加载中...</td>
            </tr>
          </tbody>
        </table>

        <div class="pagination-bar bottom">
          <div class="pagination-summary">
            共 {{ total }} 个文件，第 {{ currentPage }} / {{ displayTotalPages }} 页
          </div>
          <div class="pagination-actions">
            <button class="page-btn" :disabled="loading || currentPage <= 1" @click="changePage(1)">首页</button>
            <button class="page-btn" :disabled="loading || currentPage <= 1" @click="changePage(currentPage - 1)">上一页</button>
            <button
              v-for="page in visiblePages"
              :key="`bottom-${page}`"
              class="page-btn"
              :class="{ active: page === currentPage }"
              :disabled="loading"
              @click="changePage(page)"
            >
              {{ page }}
            </button>
            <button class="page-btn" :disabled="loading || currentPage >= displayTotalPages" @click="changePage(currentPage + 1)">下一页</button>
            <button class="page-btn" :disabled="loading || currentPage >= displayTotalPages" @click="changePage(displayTotalPages)">末页</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const router = useRouter()
const loading = ref(false)
const files = ref([])
const currentPage = ref(1)
const totalPages = ref(0)
const total = ref(0)
const perPage = ref(50)
const selectedIds = ref([])
const deletingId = ref(null)
const batchRecognizing = ref(false)
const onlyPendingForBatch = ref(true)
const selectedDocumentType = ref('all')
const selectedDocumentTypeLabel = computed(() => {
  if (selectedDocumentType.value === 'paper') return '论文'
  if (selectedDocumentType.value === 'commission') return '委托单'
  return '全部'
})

const currentPageIds = computed(() => files.value.map((item) => Number(item?.id)).filter((id) => Number.isFinite(id)))
const selectedCount = computed(() => selectedIds.value.length)
const selectedItems = computed(() => {
  const selectedIdSet = new Set(selectedIds.value)
  return files.value.filter((item) => selectedIdSet.has(Number(item?.id)))
})
const batchTargetItems = computed(() => (
  onlyPendingForBatch.value
    ? selectedItems.value.filter((item) => String(item?.ocr_status || '').toLowerCase() === 'pending')
    : selectedItems.value
))
const batchTargetCount = computed(() => batchTargetItems.value.length)
const pendingPageIds = computed(() => (
  files.value
    .filter((item) => String(item?.ocr_status || '').toLowerCase() === 'pending')
    .map((item) => Number(item?.id))
    .filter((id) => Number.isFinite(id))
))
const allSelectedOnPage = computed(() => (
  currentPageIds.value.length > 0
  && currentPageIds.value.every((id) => selectedIds.value.includes(id))
))

const displayTotalPages = computed(() => Math.max(totalPages.value, 1))

const visiblePages = computed(() => {
  const pageCount = displayTotalPages.value
  const current = Math.min(currentPage.value, pageCount)
  let start = Math.max(1, current - 2)
  let end = Math.min(pageCount, start + 4)

  start = Math.max(1, end - 4)

  const pages = []
  for (let page = start; page <= end; page += 1) {
    pages.push(page)
  }
  return pages
})

const recognizeActionLabel = (item) => {
  const status = String(item?.ocr_status || '').toLowerCase()
  return status === 'completed' ? '重新识别' : '开始识别'
}

const normalizeStatus = (status) => String(status || '').toLowerCase()

const getDocumentTypeText = (code) => {
  const normalized = normalizeStatus(code)
  if (normalized === 'paper') return '论文'
  if (normalized === 'commission') return '委托单'
  return '-'
}

const formatTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('zh-CN', { hour12: false })
}

const getOcrStatusText = (status) => {
  const normalized = normalizeStatus(status)
  if (normalized === 'completed') return '已识别'
  if (normalized === 'pending') return '待识别'
  if (normalized === 'processing') return '识别中'
  if (normalized === 'failed') return '识别失败'
  return ''
}

const getOcrStatusClass = (status) => {
  const normalized = normalizeStatus(status)
  if (normalized === 'completed') return 'recognized'
  if (normalized === 'pending') return 'pending'
  if (normalized === 'processing') return 'processing'
  if (normalized === 'failed') return 'failed'
  return ''
}

const getReviewStatusText = (status) => {
  const normalized = normalizeStatus(status)
  if (normalized === 'completed') return '已核对'
  if (['unassigned', 'pending', 'assigned'].includes(normalized)) return '待核对'
  if (['processing', 'in_progress'].includes(normalized)) return '核对中'
  if (normalized === 'failed') return '核对失败'
  return ''
}

const getReviewStatusClass = (status) => {
  const normalized = normalizeStatus(status)
  if (normalized === 'completed') return 'reviewed'
  if (['unassigned', 'pending', 'assigned'].includes(normalized)) return 'to-review'
  if (['processing', 'in_progress'].includes(normalized)) return 'review-processing'
  if (normalized === 'failed') return 'failed'
  return ''
}

const fetchFiles = async (page = currentPage.value) => {
  loading.value = true
  try {
    const query = {
      page,
      per_page: perPage.value,
      view_mode: 'my_files',
    }
    if (selectedDocumentType.value !== 'all') {
      query.document_type = selectedDocumentType.value
    }

    const data = await ocrCheckerApi.listFiles(query)
    const payload = data?.data && typeof data.data === 'object' && !Array.isArray(data.data) ? data.data : data
    const list = payload?.files || data?.files || data?.data || []

    files.value = Array.isArray(list) ? list : []
    total.value = Number(payload?.total ?? files.value.length ?? 0)
    totalPages.value = Number(payload?.pages ?? (files.value.length ? 1 : 0))
    currentPage.value = Number(payload?.current_page ?? page)
    perPage.value = Number(payload?.per_page ?? perPage.value)
    selectedIds.value = []
  } catch (e) {
    files.value = []
    total.value = 0
    totalPages.value = 0
    selectedIds.value = []
    ElMessage.warning('读取文件列表失败，请先检查 checker 服务状态')
  } finally {
    loading.value = false
  }
}

const switchDocumentType = (documentType) => {
  if (loading.value || selectedDocumentType.value === documentType) {
    return
  }
  selectedDocumentType.value = documentType
  selectedIds.value = []
  fetchFiles(1)
}

const toggleSelectAllOnPage = (event) => {
  const checked = !!event?.target?.checked
  const baseIds = onlyPendingForBatch.value ? pendingPageIds.value : currentPageIds.value
  if (checked) {
    selectedIds.value = [...new Set([...selectedIds.value, ...baseIds])]
    return
  }
  const pageIdSet = new Set(baseIds)
  selectedIds.value = selectedIds.value.filter((id) => !pageIdSet.has(id))
}

watch(onlyPendingForBatch, (enabled) => {
  if (!enabled) {
    return
  }
  const pendingIdSet = new Set(pendingPageIds.value)
  selectedIds.value = selectedIds.value.filter((id) => pendingIdSet.has(id))
})

const extractErrorMessage = (error) => (
  error?.response?.data?.message
  || error?.message
  || '请求失败'
)

const batchRecognizeSelected = async () => {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先勾选要识别的文件')
    return
  }

  if (batchTargetItems.value.length === 0) {
    ElMessage.warning('当前勾选中没有待识别文件，请取消过滤或调整勾选')
    return
  }

  batchRecognizing.value = true
  const targetIds = batchTargetItems.value.map((item) => Number(item.id)).filter((id) => Number.isFinite(id))
  const results = await Promise.allSettled(targetIds.map((id) => ocrCheckerApi.startRecognize(id)))

  let successCount = 0
  let failedCount = 0
  let firstErrorMessage = ''

  results.forEach((result) => {
    if (result.status === 'fulfilled') {
      successCount += 1
      return
    }
    failedCount += 1
    if (!firstErrorMessage) {
      firstErrorMessage = extractErrorMessage(result.reason)
    }
  })

  if (successCount > 0 && failedCount === 0) {
    ElMessage.success(`批量识别任务已提交：${successCount} 个文件`)
  } else if (successCount > 0) {
    ElMessage.warning(`批量识别部分成功：成功 ${successCount}，失败 ${failedCount}（${firstErrorMessage || '请稍后重试'}）`)
  } else {
    ElMessage.error(`批量识别失败：${firstErrorMessage || '请稍后重试'}`)
  }

  selectedIds.value = []
  batchRecognizing.value = false
  await fetchFiles(currentPage.value)
}

const changePage = (page) => {
  const targetPage = Math.min(Math.max(Number(page) || 1, 1), displayTotalPages.value)
  if (loading.value || targetPage === currentPage.value) {
    return
  }
  fetchFiles(targetPage)
}

const goRecognize = (item) => {
  router.push(`/ocr/recognize/${item.id}`)
}

const goReview = (item) => {
  router.push(`/ocr/review/${item.id}`)
}

const removeFile = async (item) => {
  if (!item?.id || deletingId.value) return
  const confirmed = window.confirm(`确认删除文件《${item.filename}》吗？`)
  if (!confirmed) return

  deletingId.value = item.id
  try {
    await ocrCheckerApi.deleteFile(item.id)
    ElMessage.success('文件已删除')
    await fetchFiles(files.value.length === 1 && currentPage.value > 1 ? currentPage.value - 1 : currentPage.value)
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || error?.message || '删除失败，请稍后重试')
  } finally {
    deletingId.value = null
  }
}
onMounted(() => {
  fetchFiles(1)
})
</script>

<style scoped>
.ocr-module-page { display:flex; min-height:100vh; background:#f4f7fb; }
.content { flex:1; padding:24px; }
.toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.toolbar h2 { margin:0; color:#1e293b; }
.actions { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
.type-filters { display:flex; gap:6px; }
.filter-btn { padding:6px 10px; }
.filter-btn.active { border-color:#6366f1; background:#eef2ff; color:#4338ca; font-weight:600; }
.filter-indicator { display:flex; align-items:center; color:#64748b; font-size:13px; padding:0 4px; }
.check-option { display:flex; align-items:center; gap:6px; color:#475569; font-size:13px; padding:0 4px; user-select:none; }
.check-option input { margin:0; }
.btn { border:1px solid #dce4f4; background:#fff; padding:6px 12px; border-radius:8px; cursor:pointer; }
.btn.primary { background:#6366f1; color:#fff; border-color:#6366f1; }
.btn:disabled { cursor:not-allowed; opacity:.55; }
.panel { background:#fff; border:1px solid #e8edf7; border-radius:12px; overflow:hidden; }
.pagination-bar { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px 14px; border-bottom:1px solid #eef2f7; background:#fbfcfe; }
.pagination-bar.bottom { border-top:1px solid #eef2f7; border-bottom:none; }
.pagination-summary { color:#64748b; font-size:13px; }
.pagination-actions { display:flex; flex-wrap:wrap; gap:8px; justify-content:flex-end; }
.page-btn { min-width:44px; border:1px solid #dbe4f0; background:#fff; color:#334155; padding:6px 10px; border-radius:8px; cursor:pointer; line-height:1.2; }
.page-btn:hover:not(:disabled) { background:#f8fafc; }
.page-btn.active { border-color:#6366f1; background:#eef2ff; color:#4338ca; }
.page-btn:disabled { cursor:not-allowed; opacity:.5; }
.table { width:100%; border-collapse:collapse; }
.table th,.table td { border-bottom:1px solid #eef2f7; text-align:left; padding:10px 12px; font-size:13px; vertical-align:top; }
.table th { background:#f8fafc; color:#475569; }
.checkbox-col { width:44px; text-align:center !important; }
.ops-cell { min-width:280px; }
.action-group { display:flex; flex-wrap:wrap; gap:8px; }
.action-btn { border:1px solid #dbe4f0; background:#fff; color:#334155; padding:6px 10px; border-radius:8px; cursor:pointer; line-height:1.2; }
.action-btn:hover { background:#f8fafc; }
.action-primary { border-color:#6366f1; background:#eef2ff; color:#4338ca; }
.action-btn.danger { border-color:#fecaca; background:#fff; color:#b91c1c; }
.action-btn.danger:hover:not(:disabled) { background:#fef2f2; }
.status-hint { margin-left:8px; font-size:12px; line-height:1; padding:3px 8px; border-radius:999px; }
.status-hint.recognized { color:#166534; background:#dcfce7; border:1px solid #bbf7d0; }
.status-hint.pending { color:#92400e; background:#fef3c7; border:1px solid #fde68a; }
.status-hint.processing,
.status-hint.review-processing { color:#1d4ed8; background:#dbeafe; border:1px solid #bfdbfe; }
.status-hint.reviewed { color:#166534; background:#dcfce7; border:1px solid #bbf7d0; }
.status-hint.to-review { color:#b45309; background:#ffedd5; border:1px solid #fed7aa; }
.status-hint.failed { color:#b91c1c; background:#fee2e2; border:1px solid #fecaca; }
.empty { text-align:center; color:#94a3b8; }

@media (max-width: 960px) {
  .pagination-bar { flex-direction:column; align-items:flex-start; }
  .pagination-actions { width:100%; justify-content:flex-start; }
}
</style>
