<template>
  <div class="ocr-center-page-wrapper">
    <NavigationSidebar />

    <div class="ocr-center-container">
      <div class="page-header">
        <h1><i class="fas fa-camera-retro"></i> OCR中心</h1>
        <p>OCR 统一仪表盘：展示识别与核对进度，并在下方直接管理最近文件。</p>
      </div>

      <div class="status-card">
        <div class="status-left">
          <h3>Django OCR 统一代理</h3>
          <p>当前统一入口：<code>{{ gatewayBase }}</code></p>
        </div>
        <div class="status-right">
          <button class="btn btn-secondary" @click="refreshDashboard" :disabled="statsLoading || filesLoading">
            {{ statsLoading || filesLoading ? '刷新中...' : '刷新仪表盘' }}
          </button>
          <button class="btn btn-secondary" @click="checkGatewayHealth">健康检查</button>
          <span :class="['health-badge', gatewayStatus]">{{ statusLabel }}</span>
        </div>
      </div>

      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">总文件数</div>
          <div class="stat-value">{{ stats.totalFiles }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已识别文件</div>
          <div class="stat-value success">{{ stats.ocrCompleted }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">已核对文件</div>
          <div class="stat-value success">{{ stats.reviewCompleted }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">待核对文件</div>
          <div class="stat-value warning">{{ stats.pendingReview }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">核对完成率</div>
          <div class="stat-value">{{ reviewRate }}%</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">文档类型分布</div>
          <div class="stat-mini">论文 {{ stats.paperFiles }} | 委托 {{ stats.commissionFiles }}</div>
        </div>
      </div>

      <div class="panel-card">
        <div class="panel-head">
          <h3><i class="fas fa-folder-open"></i> 最近文件（最新10条）</h3>
          <div class="panel-actions">
            <button class="btn btn-secondary" @click="loadFiles">刷新列表</button>
            <button class="btn btn-primary" @click="router.push('/ocr/files')">进入完整文件管理</button>
          </div>
        </div>

        <div class="file-table-wrap">
          <table class="file-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>文件名</th>
                <th>类型</th>
                <th>OCR状态</th>
                <th>核对状态</th>
                <th>更新时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in fileRows" :key="row.id">
                <td>{{ row.id }}</td>
                <td class="filename">{{ row.filename }}</td>
                <td>{{ row.document_type_code || '-' }}</td>
                <td>{{ row.ocr_status || '-' }}</td>
                <td>{{ row.review_status || '-' }}</td>
                <td>{{ formatTime(row.updated_at || row.created_at) }}</td>
                <td class="ops-cell">
                  <div class="action-group">
                    <button class="action-btn action-primary" @click="goRecognize(row.id, row.ocr_status)">
                      {{ recognizeActionLabel(row.ocr_status) }}
                    </button>
                    <button class="action-btn" @click="goReview(row.id)">进入核对</button>
                  </div>
                </td>
              </tr>

              <tr v-if="filesLoading">
                <td colspan="7" class="empty">加载中...</td>
              </tr>
              <tr v-else-if="fileRows.length === 0">
                <td colspan="7" class="empty">暂无文件</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import { ElMessage } from 'element-plus'
import ocrGatewayAPI from '@/services/ocrGateway'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const router = useRouter()
const gatewayBase = '/api/ocr'
const gatewayStatus = ref('idle')
const statsLoading = ref(false)
const filesLoading = ref(false)
const fileRows = ref([])
const stats = ref({
  totalFiles: 0,
  ocrCompleted: 0,
  reviewCompleted: 0,
  pendingReview: 0,
  paperFiles: 0,
  commissionFiles: 0,
})

const statusLabel = computed(() => {
  if (gatewayStatus.value === 'ok') return '正常'
  if (gatewayStatus.value === 'down') return '不可达'
  if (gatewayStatus.value === 'checking') return '检查中'
  return '未检查'
})

const reviewRate = computed(() => {
  if (!stats.value.totalFiles) return 0
  return ((stats.value.reviewCompleted / stats.value.totalFiles) * 100).toFixed(1)
})

const recognizeActionLabel = (status) => {
  return String(status || '').toLowerCase() === 'completed' ? '重新识别' : '开始识别'
}

const extractListData = (responseData) => {
  const queue = [responseData]
  const visited = new Set()

  while (queue.length) {
    const cur = queue.shift()
    if (!cur || typeof cur !== 'object') continue
    if (visited.has(cur)) continue
    visited.add(cur)

    if (Array.isArray(cur.files)) {
      return {
        files: cur.files,
        total: Number(cur.total ?? cur.files.length ?? 0),
      }
    }

    Object.values(cur).forEach((v) => {
      if (v && typeof v === 'object') queue.push(v)
    })
  }

  return {
    files: [],
    total: 0,
  }
}

const getTotalByFilter = async (params = {}) => {
  const data = await ocrCheckerApi.countFiles(params)
  const root = data?.data || data || {}
  const payload = root?.data || root || {}
  return Number(payload.total || 0)
}

const loadStats = async () => {
  statsLoading.value = true
  try {
    const [totalFiles, ocrCompleted, reviewCompleted, paperFiles, commissionFiles] = await Promise.all([
      getTotalByFilter(),
      getTotalByFilter({ status: 'completed' }),
      getTotalByFilter({ review_status: 'completed' }),
      getTotalByFilter({ document_type: 'paper' }),
      getTotalByFilter({ document_type: 'commission' }),
    ])

    stats.value = {
      totalFiles,
      ocrCompleted,
      reviewCompleted,
      pendingReview: Math.max(totalFiles - reviewCompleted, 0),
      paperFiles,
      commissionFiles,
    }
  } catch (error) {
    ElMessage.warning(error?.response?.data?.message || '统计数据读取失败')
  } finally {
    statsLoading.value = false
  }
}

const loadFiles = async () => {
  filesLoading.value = true
  try {
    const data = await ocrCheckerApi.listFiles({ page: 1, per_page: 10 })
    fileRows.value = extractListData(data).files
  } catch (error) {
    fileRows.value = []
    ElMessage.warning(error?.response?.data?.message || '文件列表读取失败')
  } finally {
    filesLoading.value = false
  }
}

const refreshDashboard = async () => {
  await Promise.all([loadStats(), loadFiles()])
}

const formatTime = (value) => {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('zh-CN', { hour12: false })
}

const checkGatewayHealth = async () => {
  gatewayStatus.value = 'checking'
  try {
    await ocrGatewayAPI.health()
    gatewayStatus.value = 'ok'
    ElMessage.success('Django OCR统一代理连接正常')
  } catch (error) {
    gatewayStatus.value = 'down'
    ElMessage.warning('OCR统一代理不可达，请检查 Django 或上游 OCR 服务状态')
  }
}

const goRecognize = (fileId) => {
  router.push(`/ocr/recognize/${fileId}`)
}

const goReview = (fileId) => {
  router.push(`/ocr/review/${fileId}`)
}

refreshDashboard()
</script>

<style scoped>
.ocr-center-page-wrapper {
  display: flex;
  min-height: 100vh;
  background: #f4f7fb;
}

.ocr-center-container {
  flex: 1;
  padding: 26px;
  box-sizing: border-box;
}

.page-header {
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 20px;
  margin-bottom: 14px;
}

.page-header h1 {
  margin: 0;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 10px;
}

.page-header p {
  margin: 8px 0 0;
  color: #64748b;
}

.status-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 14px;
}

.status-left h3 {
  margin: 0;
}

.status-left p {
  margin: 6px 0 0;
  color: #64748b;
}

.status-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.stat-card {
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 12px;
  padding: 14px;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
}

.stat-value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
}

.stat-value.success {
  color: #15803d;
}

.stat-value.warning {
  color: #b45309;
}

.stat-mini {
  margin-top: 10px;
  font-size: 14px;
  color: #334155;
}

.panel-card {
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 14px;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 12px;
}

.panel-head h3 {
  margin: 0;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.file-table-wrap {
  overflow: auto;
  border: 1px solid #eef2f7;
  border-radius: 10px;
}

.file-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 860px;
}

.file-table th,
.file-table td {
  border-bottom: 1px solid #eef2f7;
  padding: 10px 12px;
  text-align: left;
  font-size: 13px;
}

.file-table th {
  background: #f8fafc;
  color: #475569;
}

.filename {
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.ops-cell {
  min-width: 190px;
}

.action-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.action-btn {
  border: 1px solid #dbe4f0;
  background: #fff;
  color: #334155;
  padding: 6px 10px;
  border-radius: 8px;
  cursor: pointer;
  line-height: 1.2;
}

.action-btn:hover {
  background: #f8fafc;
}

.action-primary {
  border-color: #6366f1;
  background: #eef2ff;
  color: #4338ca;
}

.empty {
  text-align: center;
  color: #94a3b8;
}

.health-badge {
  font-size: 12px;
  border-radius: 999px;
  padding: 4px 10px;
  border: 1px solid #dbeafe;
  color: #1d4ed8;
  background: #eff6ff;
}

.health-badge.ok {
  color: #166534;
  border-color: #bbf7d0;
  background: #f0fdf4;
}

.health-badge.down {
  color: #991b1b;
  border-color: #fecaca;
  background: #fef2f2;
}

.btn {
  border: none;
  border-radius: 9px;
  padding: 8px 12px;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(135deg, #5f79ff 0%, #725cff 100%);
  color: #fff;
}

.btn-secondary {
  background: #eef2f8;
  color: #334155;
}

@media (max-width: 768px) {
  .ocr-center-container {
    padding: 14px;
  }

  .status-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .panel-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
