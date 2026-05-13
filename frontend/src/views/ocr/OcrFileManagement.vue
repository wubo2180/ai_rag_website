<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <h2>OCR 文件管理</h2>
        <div class="actions">
          <button class="btn" @click="fetchFiles">刷新</button>
          <button class="btn primary" @click="router.push('/ocr/upload')">上传文件</button>
        </div>
      </div>

      <div class="panel">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>文件名</th>
              <th>类型</th>
              <th>OCR状态</th>
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
              <td>
                <button class="link" @click="goRecognize(item)">识别页</button>
                <button class="link" @click="goReview(item)">核对页</button>
                <button class="link" @click="openWorkbench(item)">工作台</button>
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const router = useRouter()
const loading = ref(false)
const files = ref([])

const fetchFiles = async () => {
  loading.value = true
  try {
    const data = await ocrCheckerApi.listFiles({ page: 1, per_page: 50, view_mode: 'my_files' })
    const list = data?.data?.files || data?.files || data?.data || []
    files.value = Array.isArray(list) ? list : []
  } catch (e) {
    files.value = []
    ElMessage.warning('读取文件列表失败（可先检查 checker 服务状态）')
  } finally {
    loading.value = false
  }
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

onMounted(fetchFiles)
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
.table { width:100%; border-collapse:collapse; }
.table th,.table td { border-bottom:1px solid #eef2f7; text-align:left; padding:10px 12px; font-size:13px; }
.table th { background:#f8fafc; color:#475569; }
.empty { text-align:center; color:#94a3b8; }
.link { border:none; background:none; color:#4f46e5; cursor:pointer; }
</style>
