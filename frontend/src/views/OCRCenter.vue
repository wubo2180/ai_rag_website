<template>
  <div class="ocr-center-page-wrapper">
    <NavigationSidebar />

    <div class="ocr-center-container">
      <div class="page-header">
        <h1><i class="fas fa-camera-retro"></i> OCR中心</h1>
<<<<<<< HEAD
        <p>OCR 统一仪表盘：展示识别与核对进度，并在下方直接管理最近文件。</p>
=======
        <p>统一接入委托识别、论文识别与校验系统，已收口到 Django 后端代理层。</p>
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
      </div>

      <div class="status-card">
        <div class="status-left">
          <h3>Django OCR 统一代理</h3>
          <p>当前统一入口：<code>{{ gatewayBase }}</code></p>
        </div>
        <div class="status-right">
          <button class="btn btn-primary" @click="goMigratedModule">迁移版业务台</button>
          <button class="btn btn-primary" @click="goMigratedModule">迁移版业务台</button>
          <button class="btn btn-secondary" @click="checkGatewayHealth">健康检查</button>
          <span :class="['health-badge', gatewayStatus]">{{ statusLabel }}</span>
        </div>
      </div>

      <div class="task-query-card">
        <div class="task-query-head">
          <h3><i class="fas fa-tasks"></i> 统一任务状态查询</h3>
          <p>通过 <code>/api/ocr/tasks/:taskId</code> 聚合查询任务状态。</p>
      <div class="task-query-card">
        <div class="task-query-head">
          <h3><i class="fas fa-tasks"></i> 统一任务状态查询</h3>
          <p>通过 <code>/api/ocr/tasks/:taskId</code> 聚合查询任务状态。</p>
        </div>
<<<<<<< HEAD
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
=======
        <div class="task-query-controls">
          <input v-model.trim="taskIdInput" type="text" placeholder="请输入任务ID" />
          <select v-model="preferredService">
            <option value="">自动探测</option>
            <option value="commission">commission</option>
            <option value="paper">paper</option>
            <option value="checker">checker</option>
          </select>
          <button class="btn btn-primary" @click="queryTaskStatus">查询状态</button>
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
        </div>
        <pre v-if="taskStatusResult" class="task-query-result">{{ taskStatusResult }}</pre>
      </div>

<<<<<<< HEAD
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
=======
      <div class="service-grid">
        <div class="service-card" v-for="service in services" :key="service.key">
          <div class="service-title">
            <i :class="service.icon"></i>
            <h3>{{ service.name }}</h3>
          </div>
          <p class="service-desc">{{ service.desc }}</p>
          <div class="service-meta">
            <span>统一路径：<code>{{ service.gatewayPath }}</code></span>
          </div>
          <div v-if="serviceDiagnostics[service.key]" class="service-error">
            {{ serviceDiagnostics[service.key] }}
          </div>
          <div class="service-actions">
            <button class="btn btn-primary" @click="openGatewayEndpoint(service)">检测并打开</button>
          </div>
        </div>
      </div>

      <div class="tips-card">
        <h3><i class="fas fa-lightbulb"></i> 架构说明</h3>
        <ul>
          <li>OCR 统一入口已并入 <code>backend</code> 与 <code>frontend</code>。</li>
          <li>Django 提供 <code>/api/ocr/*</code> 代理层，前端统一通过该入口调用。</li>
          <li>“检测并打开”会打开前端 Vue 工作台，不再直接打开后端 HTML 入口页。</li>
        </ul>
      </div>
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import { ElMessage } from 'element-plus'
import ocrGatewayAPI from '@/services/ocrGateway'

const router = useRouter()
const gatewayBase = '/api/ocr'
const gatewayStatus = ref('idle')
const taskIdInput = ref('')
const preferredService = ref('')
const taskStatusResult = ref('')
const serviceDiagnostics = ref({})

const services = [
  {
    key: 'commission',
    name: '委托识别服务',
    desc: '用于批量委托文档OCR识别与任务处理。',
  gatewayPath: '/ocr-center/commission',
    icon: 'fas fa-file-signature',
  },
  {
    key: 'paper',
    name: '论文识别服务',
    desc: '用于论文文档识别、抽取和结构化解析。',
  gatewayPath: '/ocr-center/paper',
    icon: 'fas fa-newspaper',
  },
  {
    key: 'checker',
    name: '校验系统服务',
    desc: '用于任务复核、质检和数据校验流程。',
  gatewayPath: '/ocr-center/checker',
    icon: 'fas fa-check-double',
  },
]
const taskIdInput = ref('')
const preferredService = ref('')
const taskStatusResult = ref('')
const serviceDiagnostics = ref({})

const services = [
  {
    key: 'commission',
    name: '委托识别服务',
    desc: '用于批量委托文档OCR识别与任务处理。',
  gatewayPath: '/ocr-center/commission',
    icon: 'fas fa-file-signature',
  },
  {
    key: 'paper',
    name: '论文识别服务',
    desc: '用于论文文档识别、抽取和结构化解析。',
  gatewayPath: '/ocr-center/paper',
    icon: 'fas fa-newspaper',
  },
  {
    key: 'checker',
    name: '校验系统服务',
    desc: '用于任务复核、质检和数据校验流程。',
  gatewayPath: '/ocr-center/checker',
    icon: 'fas fa-check-double',
  },
]

const statusLabel = computed(() => {
  if (gatewayStatus.value === 'ok') return '正常'
  if (gatewayStatus.value === 'down') return '不可达'
  if (gatewayStatus.value === 'checking') return '检查中'
  return '未检查'
})

<<<<<<< HEAD
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

=======
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
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

const queryTaskStatus = async () => {
  if (!taskIdInput.value) {
    ElMessage.warning('请先输入任务ID')
    return
  }

  try {
    const data = await ocrGatewayAPI.getTaskStatus(taskIdInput.value, preferredService.value)
    taskStatusResult.value = JSON.stringify(data, null, 2)
    ElMessage.success('任务状态查询成功')
  } catch (error) {
    taskStatusResult.value = JSON.stringify(
      {
        status: 'error',
        message: error?.response?.data?.message || '查询失败',
      },
      null,
      2
    )
  }
}

const openGatewayEndpoint = (service) => {
  openServiceEntry(service)
}

const goMigratedModule = () => {
  router.push('/ocr/dashboard')
}

const openServiceEntry = async (service) => {
  serviceDiagnostics.value[service.key] = ''
  const openedWindow = window.open('', '_blank')
  if (!openedWindow) {
    ElMessage.warning('浏览器拦截了新窗口，请允许弹窗后重试')
    return
  }

  openedWindow.document.write('<p style="font-family: Arial; padding: 16px;">正在检测服务状态...</p>')

  try {
    const result = await ocrGatewayAPI.serviceHealth(service.key)
    if (result?.status === 'error' || result?.status === 'down') {
      const message = result?.message || `${service.name}暂不可用`
      const detail = result?.detail ? `：${result.detail}` : ''
      const display = `${message}${detail}`
      serviceDiagnostics.value[service.key] = display
      ElMessage.error(display)
      openedWindow.location.href = service.gatewayPath
      return
    }

    openedWindow.location.href = service.gatewayPath
    ElMessage.success(`${service.name}可用，已打开统一入口`)
  } catch (error) {
    const respMessage = error?.response?.data?.message || '服务检测失败'
    const respDetail = error?.response?.data?.detail ? `：${error.response.data.detail}` : ''
    const display = `${respMessage}${respDetail}`
    serviceDiagnostics.value[service.key] = display
    ElMessage.error(display)
    openedWindow.location.href = service.gatewayPath
  }
}
const queryTaskStatus = async () => {
  if (!taskIdInput.value) {
    ElMessage.warning('请先输入任务ID')
    return
  }

  try {
    const data = await ocrGatewayAPI.getTaskStatus(taskIdInput.value, preferredService.value)
    taskStatusResult.value = JSON.stringify(data, null, 2)
    ElMessage.success('任务状态查询成功')
  } catch (error) {
    taskStatusResult.value = JSON.stringify(
      {
        status: 'error',
        message: error?.response?.data?.message || '查询失败',
      },
      null,
      2
    )
  }
}

const openGatewayEndpoint = (service) => {
  openServiceEntry(service)
}

const goMigratedModule = () => {
  router.push('/ocr/dashboard')
}

const openServiceEntry = async (service) => {
  serviceDiagnostics.value[service.key] = ''
  const openedWindow = window.open('', '_blank')
  if (!openedWindow) {
    ElMessage.warning('浏览器拦截了新窗口，请允许弹窗后重试')
    return
  }

  openedWindow.document.write('<p style="font-family: Arial; padding: 16px;">正在检测服务状态...</p>')

  try {
    const result = await ocrGatewayAPI.serviceHealth(service.key)
    if (result?.status === 'error' || result?.status === 'down') {
      const message = result?.message || `${service.name}暂不可用`
      const detail = result?.detail ? `：${result.detail}` : ''
      const display = `${message}${detail}`
      serviceDiagnostics.value[service.key] = display
      ElMessage.error(display)
      openedWindow.location.href = service.gatewayPath
      return
    }

    openedWindow.location.href = service.gatewayPath
    ElMessage.success(`${service.name}可用，已打开统一入口`)
  } catch (error) {
    const respMessage = error?.response?.data?.message || '服务检测失败'
    const respDetail = error?.response?.data?.detail ? `：${error.response.data.detail}` : ''
    const display = `${respMessage}${respDetail}`
    serviceDiagnostics.value[service.key] = display
    ElMessage.error(display)
    openedWindow.location.href = service.gatewayPath
  }
}
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

<<<<<<< HEAD
.status-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
=======
.status-card,
.tips-card,
.task-query-card {
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 14px;
}

<<<<<<< HEAD
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
=======
.task-query-head h3 {
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #1e293b;
  color: #1e293b;
}

.task-query-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.task-query-controls {
  display: grid;
  grid-template-columns: 1.6fr 1fr auto;
  gap: 10px;
  margin-top: 12px;
.task-query-head p {
  margin: 6px 0 0;
  color: #64748b;
  font-size: 13px;
}

.task-query-controls {
  display: grid;
  grid-template-columns: 1.6fr 1fr auto;
  gap: 10px;
  margin-top: 12px;
}

.task-query-controls input,
.task-query-controls select {
  border: 1px solid #dce4f4;
.task-query-controls input,
.task-query-controls select {
  border: 1px solid #dce4f4;
  border-radius: 10px;
  padding: 8px 10px;
  padding: 8px 10px;
  font-size: 13px;
}

<<<<<<< HEAD
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
=======
.task-query-result {
  margin-top: 12px;
  background: #111827;
  color: #e5e7eb;
  border-radius: 10px;
  padding: 10px;
  font-size: 12px;
  overflow: auto;
  max-height: 260px;
>>>>>>> parent of 3d11ed6 (将OCR统计面板bug修复了)
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

.service-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.service-card {
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 14px;
}

.service-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.service-title h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}

.service-desc {
  color: #64748b;
  font-size: 13px;
  min-height: 40px;
}

.service-meta {
  font-size: 12px;
  color: #64748b;
}

.service-actions {
  margin-top: 10px;
}

.service-error {
  margin-top: 8px;
  font-size: 12px;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 6px 8px;
  line-height: 1.4;
  word-break: break-all;
}

.service-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 12px;
  margin-bottom: 14px;
}

.service-card {
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 14px;
}

.service-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.service-title h3 {
  margin: 0;
  font-size: 16px;
  color: #1e293b;
}

.service-desc {
  color: #64748b;
  font-size: 13px;
  min-height: 40px;
}

.service-meta {
  font-size: 12px;
  color: #64748b;
}

.service-actions {
  margin-top: 10px;
}

.service-error {
  margin-top: 8px;
  font-size: 12px;
  color: #b91c1c;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  padding: 6px 8px;
  line-height: 1.4;
  word-break: break-all;
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

.tips-card ul {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.8;
}

.tips-card ul {
  margin: 10px 0 0;
  padding-left: 18px;
  color: #475569;
  line-height: 1.8;
}

@media (max-width: 768px) {
  .ocr-center-container {
    padding: 14px;
  }

  .status-card {
    flex-direction: column;
    align-items: flex-start;
  }

  .task-query-controls {
    grid-template-columns: 1fr;
  .task-query-controls {
    grid-template-columns: 1fr;
  }
}
</style>
