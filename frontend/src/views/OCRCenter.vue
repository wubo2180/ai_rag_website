<template>
  <div class="ocr-center-page-wrapper">
    <NavigationSidebar />

    <div class="ocr-center-container">
      <div class="page-header">
        <h1><i class="fas fa-camera-retro"></i> OCR中心</h1>
        <p>统一接入委托识别、论文识别与校验系统，已收口到 Django 后端代理层。</p>
      </div>

      <div class="status-card">
        <div class="status-left">
          <h3>Django OCR 统一代理</h3>
          <p>当前统一入口：<code>{{ gatewayBase }}</code></p>
        </div>
        <div class="status-right">
          <button class="btn btn-primary" @click="goMigratedModule">迁移版业务台</button>
          <button class="btn btn-secondary" @click="checkGatewayHealth">健康检查</button>
          <span :class="['health-badge', gatewayStatus]">{{ statusLabel }}</span>
        </div>
      </div>

      <div class="task-query-card">
        <div class="task-query-head">
          <h3><i class="fas fa-tasks"></i> 统一任务状态查询</h3>
          <p>通过 <code>/api/ocr/tasks/:taskId</code> 聚合查询任务状态。</p>
        </div>
        <div class="task-query-controls">
          <input v-model.trim="taskIdInput" type="text" placeholder="请输入任务ID" />
          <select v-model="preferredService">
            <option value="">自动探测</option>
            <option value="commission">commission</option>
            <option value="paper">paper</option>
            <option value="checker">checker</option>
          </select>
          <button class="btn btn-primary" @click="queryTaskStatus">查询状态</button>
        </div>
        <pre v-if="taskStatusResult" class="task-query-result">{{ taskStatusResult }}</pre>
      </div>

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

const statusLabel = computed(() => {
  if (gatewayStatus.value === 'ok') return '正常'
  if (gatewayStatus.value === 'down') return '不可达'
  if (gatewayStatus.value === 'checking') return '检查中'
  return '未检查'
})

const checkGatewayHealth = async () => {
  gatewayStatus.value = 'checking'
  try {
    await ocrGatewayAPI.health()
    gatewayStatus.value = 'ok'
    ElMessage.success('Django OCR统一代理连接正常')
  } catch (error) {
    gatewayStatus.value = 'down'
    ElMessage.warning('OCR统一代理不可达，请检查 Django 或上游OCR服务状态')
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

.status-card,
.tips-card,
.task-query-card {
  background: #fff;
  border: 1px solid #e8edf7;
  border-radius: 14px;
  padding: 16px;
  margin-bottom: 14px;
}

.task-query-head h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
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
}

.task-query-controls input,
.task-query-controls select {
  border: 1px solid #dce4f4;
  border-radius: 10px;
  padding: 8px 10px;
  font-size: 13px;
}

.task-query-result {
  margin-top: 12px;
  background: #111827;
  color: #e5e7eb;
  border-radius: 10px;
  padding: 10px;
  font-size: 12px;
  overflow: auto;
  max-height: 260px;
}

.status-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
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
  }
}
</style>
