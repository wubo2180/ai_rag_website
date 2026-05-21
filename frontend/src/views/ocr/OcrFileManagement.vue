<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <h2>OCR 文件管理</h2>
        <div class="actions">
          <button class="btn" @click="fetchFiles(currentPage)">刷新</button>
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
              <th>ID</th>
              <th>文件名</th>
              <th>类型</th>
              <th>OCR 状态</th>
              <th>核对状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in files" :key="item.id">
              <td>{{ item.id }}</td>
              <td>{{ item.filename }}</td>
              <td>{{ item.document_type_code || '-' }}</td>
              <td>{{ item.ocr_status || '-' }}</td>
              <td>{{ item.review_status || '-' }}</td>
              <td class="ops-cell">
                <div class="action-group">
                  <button class="action-btn action-primary" @click="goRecognize(item)">
                    {{ recognizeActionLabel(item) }}
                  </button>
                  <button class="action-btn" @click="goReview(item)">进入核对</button>
                  <button class="action-btn" @click="openWorkbench(item)">服务工作台</button>
                </div>
              </td>
            </tr>
            <tr v-if="!loading && files.length === 0">
              <td colspan="6" class="empty">暂无数据</td>
            </tr>
            <tr v-if="loading">
              <td colspan="6" class="empty">加载中...</td>
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
import { computed, onMounted, ref } from 'vue'
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

const fetchFiles = async (page = currentPage.value) => {
  loading.value = true
  try {
    const data = await ocrCheckerApi.listFiles({ page, per_page: perPage.value, view_mode: 'my_files' })
    const payload = data?.data && typeof data.data === 'object' && !Array.isArray(data.data) ? data.data : data
    const list = payload?.files || data?.files || data?.data || []

    files.value = Array.isArray(list) ? list : []
    total.value = Number(payload?.total ?? files.value.length ?? 0)
    totalPages.value = Number(payload?.pages ?? (files.value.length ? 1 : 0))
    currentPage.value = Number(payload?.current_page ?? page)
    perPage.value = Number(payload?.per_page ?? perPage.value)
  } catch (e) {
    files.value = []
    total.value = 0
    totalPages.value = 0
    ElMessage.warning('读取文件列表失败，请先检查 checker 服务状态')
  } finally {
    loading.value = false
  }
}

const changePage = (page) => {
  const targetPage = Math.min(Math.max(Number(page) || 1, 1), displayTotalPages.value)
  if (loading.value || targetPage === currentPage.value) {
    return
  }
  fetchFiles(targetPage)
}

const openWorkbench = (item) => {
  const service = item?.document_type_code === 'paper' ? 'paper' : 'commission'
  router.push(`/ocr-center/${service}`)
}

const goRecognize = (item) => {
  router.push(`/ocr/recognize/${item.id}`)
}

const goReview = (item) => {
  router.push(`/ocr/review/${item.id}`)
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
.actions { display:flex; gap:8px; }
.btn { border:1px solid #dce4f4; background:#fff; padding:6px 12px; border-radius:8px; cursor:pointer; }
.btn.primary { background:#6366f1; color:#fff; border-color:#6366f1; }
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
.ops-cell { min-width:280px; }
.action-group { display:flex; flex-wrap:wrap; gap:8px; }
.action-btn { border:1px solid #dbe4f0; background:#fff; color:#334155; padding:6px 10px; border-radius:8px; cursor:pointer; line-height:1.2; }
.action-btn:hover { background:#f8fafc; }
.action-primary { border-color:#6366f1; background:#eef2ff; color:#4338ca; }
.empty { text-align:center; color:#94a3b8; }

@media (max-width: 960px) {
  .pagination-bar { flex-direction:column; align-items:flex-start; }
  .pagination-actions { width:100%; justify-content:flex-start; }
}
</style>
