<template>
  <div class="file-review-container">
    <NavigationSidebar />

    <div class="workbench-main">
      <div class="review-toolbar">
        <div class="toolbar-left">
          <div class="breadcrumb">文件管理 / 文件校对 / {{ currentFileName }}</div>
          <div class="file-info">
            <span class="tag success">{{ reviewStatus }}</span>
            <span class="tag">{{ healthLabel }}</span>
            <span>{{ fileSizeLabel }}</span>
            <span>{{ pageCount }} 页</span>
          </div>
        </div>

        <div class="toolbar-right">
          <button :class="['btn', viewMode==='split' ? 'primary' : '']" @click="viewMode='split'">分屏模式</button>
          <button :class="['btn', viewMode==='data' ? 'primary' : '']" @click="viewMode='data'">数据模式</button>
          <button :class="['btn', viewMode==='pdf' ? 'primary' : '']" @click="viewMode='pdf'">PDF模式</button>
          <button class="btn success" :disabled="!dirty" @click="saveDraft">保存修改</button>
        </div>
      </div>

      <div class="review-content" :class="`view-mode-${viewMode}`">
        <div v-if="viewMode !== 'pdf'" class="data-panel">
          <div class="panel-header">
            <h3>{{ documentTitle }}</h3>
            <div class="header-actions">
              <button class="btn" @click="checkHealth">刷新</button>
              <button class="btn" @click="exportJson">导出</button>
              <button v-if="!isEditing" class="btn primary" @click="isEditing=true">编辑</button>
              <template v-else>
                <button class="btn primary" @click="applyEdit">保存</button>
                <button class="btn" @click="cancelEdit">取消</button>
              </template>
            </div>
          </div>

          <div class="panel-content">
            <div class="card-block">
              <h4>{{ service.key === 'paper' ? '文献基本信息' : '委托基本信息' }}</h4>
              <div class="form-grid">
                <label>文献编号</label>
                <input v-model="form.article_id" :readonly="!isEditing" @input="dirty=true" />
                <label>文献名称</label>
                <textarea v-model="form.article_name" :readonly="!isEditing" rows="2" @input="dirty=true" />
                <label>性能趋势</label>
                <textarea v-model="form.performance_trend" :readonly="!isEditing" rows="3" @input="dirty=true" />
              </div>
            </div>

            <div class="card-block">
              <h4>OCR提取字段（动态）</h4>
              <div v-if="dynamicBasicEntries.length" class="form-grid">
                <template v-for="entry in dynamicBasicEntries" :key="entry.key">
                  <label>{{ entry.key }}</label>
                  <textarea
                    v-model="dynamicBasicInfo[entry.key]"
                    :readonly="!isEditing"
                    rows="2"
                    @input="dirty=true"
                  />
                </template>
              </div>
              <div v-else class="empty-pdf">暂无动态字段，请先点击“重新识别”</div>
            </div>

            <div v-if="dynamicTables.length" class="card-block">
              <h4>OCR提取表格（动态）</h4>
              <div v-for="(table, tIndex) in dynamicTables" :key="`${table.name}-${tIndex}`" class="table-block">
                <h5>{{ table.name }}</h5>
                <div class="table-wrapper">
                  <table class="ocr-table">
                    <thead>
                      <tr>
                        <th v-for="col in table.columns" :key="col">{{ col }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, rIdx) in table.rows" :key="rIdx">
                        <td v-for="col in table.columns" :key="`${rIdx}-${col}`">{{ row[col] ?? '' }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div v-if="service.key === 'commission'" class="card-block">
              <h4>四级数据链接（Material-Intermediate-Property）</h4>
              <div v-for="(item, idx) in form.hierarchical_data" :key="idx" class="sub-card">
                <h5>材料/中间体 #{{ idx + 1 }}</h5>
                <div class="form-grid two-col">
                  <label>材料编号</label>
                  <input v-model="item.material_id" :readonly="!isEditing" @input="dirty=true" />
                  <label>原材料名称</label>
                  <input v-model="item.material_name" :readonly="!isEditing" @input="dirty=true" />
                  <label>CAS号</label>
                  <input v-model="item.cas_number" :readonly="!isEditing" @input="dirty=true" />
                  <label>中间体编号</label>
                  <input v-model="item.intermediate_id" :readonly="!isEditing" @input="dirty=true" />
                </div>
                <label>中间体名称</label>
                <textarea v-model="item.intermediate_name" :readonly="!isEditing" rows="2" @input="dirty=true" />
                <label>中间体组成</label>
                <textarea v-model="item.intermediate_composition" :readonly="!isEditing" rows="2" @input="dirty=true" />
              </div>
            </div>
          </div>
        </div>

        <div v-if="viewMode !== 'data'" class="pdf-panel">
          <div class="panel-header">
            <h3>PDF预览</h3>
            <div class="header-actions">
              <label class="btn upload-btn">
                加载PDF
                <input type="file" accept="application/pdf" @change="onPdfSelect" />
              </label>
              <span class="highlight-tip">显示高亮</span>
              <input type="checkbox" v-model="showHighlight" />
            </div>
          </div>

          <div class="pdf-toolbar">
            <button class="btn" @click="prevPage">&lt;</button>
            <span>{{ currentPage }}</span>
            <button class="btn" @click="nextPage">&gt;</button>
            <select v-model="zoom">
              <option value="80">80%</option>
              <option value="100">100%</option>
              <option value="120">120%</option>
              <option value="150">150%</option>
            </select>
          </div>

          <div class="pdf-content">
            <iframe v-if="pdfUrl" :src="pdfUrl" title="pdf-preview" />
            <div v-else class="empty-pdf">请先点击“加载PDF”选择文件预览</div>
          </div>
        </div>
      </div>

      <div class="review-footer">
        <div class="footer-left">{{ service.name }} · Django统一入口</div>
        <div class="footer-right">
          <button class="btn" @click="goBack">返回OCR中心</button>
          <button class="btn primary" @click="submitAnalyze">重新识别</button>
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
import ocrGatewayAPI from '@/services/ocrGateway'

const route = useRoute()
const router = useRouter()

const serviceMap = {
  commission: { key: 'commission', name: '委托识别服务' },
  paper: { key: 'paper', name: '论文识别服务' },
}

const service = computed(() => serviceMap[String(route.params.service || '').toLowerCase()] || serviceMap.paper)

const viewMode = ref('split')
const isEditing = ref(false)
const dirty = ref(false)
const showHighlight = ref(true)
const currentPage = ref(1)
const pageCount = ref(0)
const zoom = ref('120')
const pdfUrl = ref('')
const pdfFile = ref(null)
const healthLabel = ref('未检查')
const rawAnalyzeResult = ref(null)
const dynamicBasicInfo = ref({})
const dynamicTables = ref([])

const currentFileName = ref('未选择文件')
const fileSizeLabel = ref('0 B')
const reviewStatus = ref('待核对')

const form = ref({
  article_id: '',
  article_name: '',
  performance_trend: '',
  hierarchical_data: [
    {
      material_id: '',
      material_name: '',
      cas_number: '',
      intermediate_id: '',
      intermediate_name: '',
      intermediate_composition: '',
    },
  ],
})

const buildSnapshot = () => JSON.stringify({
  form: form.value,
  dynamicBasicInfo: dynamicBasicInfo.value,
  dynamicTables: dynamicTables.value,
  rawAnalyzeResult: rawAnalyzeResult.value,
})

const snapshot = ref(buildSnapshot())

const documentTitle = computed(() => (service.value.key === 'paper' ? '论文数据' : '委托数据'))
const dynamicBasicEntries = computed(() => Object.entries(dynamicBasicInfo.value).map(([key, value]) => ({ key, value })))

const toDisplayValue = (v) => {
  if (v === null || v === undefined) return ''
  if (typeof v === 'string') return v
  if (typeof v === 'number' || typeof v === 'boolean') return String(v)
  try {
    return JSON.stringify(v, null, 2)
  } catch {
    return String(v)
  }
}

const uniqueColumns = (rows = []) => {
  const set = new Set()
  rows.forEach((r) => {
    if (r && typeof r === 'object' && !Array.isArray(r)) {
      Object.keys(r).forEach((k) => set.add(k))
    }
  })
  return [...set]
}

const flattenObject = (obj, prefix = '', result = {}) => {
  if (!obj || typeof obj !== 'object') return result
  Object.entries(obj).forEach(([k, v]) => {
    const key = prefix ? `${prefix}.${k}` : k
    if (Array.isArray(v)) {
      if (v.length > 0 && typeof v[0] === 'object') {
        if (v.length <= 8) {
          result[key] = toDisplayValue(v)
        }
      } else {
        result[key] = v.join(', ')
      }
      return
    }

    if (v && typeof v === 'object') {
      const subKeys = Object.keys(v)
      if ('value' in v && subKeys.length <= 4) {
        result[key] = toDisplayValue(v.value)
      } else {
        flattenObject(v, key, result)
      }
      return
    }

    result[key] = toDisplayValue(v)
  })
  return result
}

const updateCoreFieldsFromBasicInfo = (basicInfo) => {
  const entries = Object.entries(basicInfo || {})
  const pick = (...keys) => {
    const lowerKeys = keys.map((k) => String(k).toLowerCase())
    const found = entries.find(([name]) => lowerKeys.some((k) => String(name).toLowerCase().includes(k)))
    return found?.[1] || ''
  }

  const articleId = pick('文献编号', '编号', 'article_id', 'article id')
  const articleName = pick('文献名称', '文献标题', '标题', 'title', 'article_name')
  const trend = pick('性能趋势', '趋势', 'performance_trend', '摘要', 'summary')

  if (articleId) form.value.article_id = articleId
  if (articleName) form.value.article_name = articleName
  if (trend) form.value.performance_trend = trend
}

const parseCommissionField = (fieldName, fieldData) => {
  if (Array.isArray(fieldData)) {
    if (fieldData.length > 0 && typeof fieldData[0] === 'object') {
      if ('data' in fieldData[0] && Array.isArray(fieldData[0].data)) {
        return { type: 'table', name: fieldName, rows: fieldData[0].data }
      }
      if ('value' in fieldData[0]) {
        const text = fieldData.map((item) => toDisplayValue(item?.value)).filter(Boolean).join(' | ')
        return { type: 'basic', key: fieldName, value: text }
      }
      return { type: 'table', name: fieldName, rows: fieldData }
    }
    return { type: 'basic', key: fieldName, value: fieldData.join(', ') }
  }

  if (fieldData && typeof fieldData === 'object') {
    if (fieldData.type === 'multi_row_table' || Array.isArray(fieldData.data)) {
      return { type: 'table', name: fieldName, rows: Array.isArray(fieldData.data) ? fieldData.data : [] }
    }
    if ('value' in fieldData) {
      return { type: 'basic', key: fieldName, value: toDisplayValue(fieldData.value) }
    }
    return { type: 'basic', key: fieldName, value: toDisplayValue(fieldData) }
  }

  return { type: 'basic', key: fieldName, value: toDisplayValue(fieldData) }
}

const mapAnalyzeResultToView = (data) => {
  rawAnalyzeResult.value = data
  const basicInfo = {}
  const tables = []

  if (service.value.key === 'commission') {
    const payload = data?.data || {}
    pageCount.value = Number(payload?.total_pages || 0)

    const combined = payload?.combined_results?.combined_field_data?.all_extracted_fields
    const fallbackPage = payload?.field_extraction_results?.[0]?.extracted_fields
    const sourceFields = (combined && typeof combined === 'object') ? combined : fallbackPage

    if (sourceFields && typeof sourceFields === 'object') {
      Object.entries(sourceFields).forEach(([fieldName, fieldData]) => {
        const parsed = parseCommissionField(fieldName, fieldData)
        if (parsed.type === 'table') {
          const rows = Array.isArray(parsed.rows) ? parsed.rows : []
          tables.push({
            name: parsed.name,
            rows,
            columns: uniqueColumns(rows),
          })
        } else {
          basicInfo[parsed.key] = parsed.value
        }
      })
    }
  } else {
    const payload = data?.data || {}
    const flattened = flattenObject(payload)
    Object.assign(basicInfo, flattened)
    if (!basicInfo.论文识别结果 && Object.keys(flattened).length === 0) {
      basicInfo.论文识别结果 = toDisplayValue(data)
    }
  }

  dynamicBasicInfo.value = basicInfo
  dynamicTables.value = tables
  updateCoreFieldsFromBasicInfo(basicInfo)
}

const checkHealth = async () => {
  try {
    const data = await ocrGatewayAPI.serviceHealth(service.value.key)
    healthLabel.value = data?.status === 'ok' ? '已完成' : '异常'
  } catch {
    healthLabel.value = '异常'
  }
}

const onPdfSelect = (event) => {
  const f = event.target.files?.[0]
  if (!f) return
  pdfFile.value = f
  currentFileName.value = f.name
  fileSizeLabel.value = `${(f.size / 1024).toFixed(1)} KB`
  pageCount.value = 1
  if (pdfUrl.value) URL.revokeObjectURL(pdfUrl.value)
  pdfUrl.value = URL.createObjectURL(f)
}

const exportJson = () => {
  const payload = {
    service: service.value.key,
    form: form.value,
    dynamic_basic_info: dynamicBasicInfo.value,
    dynamic_tables: dynamicTables.value,
    raw_analyze_result: rawAnalyzeResult.value,
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${service.value.key}-data.json`
  a.click()
  URL.revokeObjectURL(url)
}

const applyEdit = () => {
  snapshot.value = buildSnapshot()
  isEditing.value = false
  dirty.value = false
  ElMessage.success('已保存到页面草稿')
}

const cancelEdit = () => {
  const restored = JSON.parse(snapshot.value)
  form.value = restored.form || form.value
  dynamicBasicInfo.value = restored.dynamicBasicInfo || {}
  dynamicTables.value = restored.dynamicTables || []
  rawAnalyzeResult.value = restored.rawAnalyzeResult || null
  isEditing.value = false
  dirty.value = false
}

const saveDraft = () => {
  snapshot.value = buildSnapshot()
  dirty.value = false
  ElMessage.success('修改已保存')
}

const submitAnalyze = async () => {
  if (!pdfFile.value) {
    ElMessage.warning('请先加载PDF文件')
    return
  }

  try {
    const fd = new FormData()
    fd.append('file', pdfFile.value)
    fd.append('response_mode', 'blocking')

    const res = await ocrGatewayAPI.proxyRequest(service.value.key, 'api/analyze', 'POST', fd, null, {
      'Content-Type': 'multipart/form-data',
    })

    const data = res || {}
    mapAnalyzeResultToView(data)

    reviewStatus.value = '已完成'
    dirty.value = true
    snapshot.value = buildSnapshot()
    ElMessage.success('识别完成，可在左侧继续修订')
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '识别失败')
  }
}

const prevPage = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}

const nextPage = () => {
  if (currentPage.value < Math.max(1, pageCount.value)) currentPage.value += 1
}

const goBack = () => {
  router.push('/ocr-center')
}

onMounted(() => {
  checkHealth()
})
</script>

<style scoped>
.file-review-container {
  display: flex;
  min-height: 100vh;
  background: #f3f5f7;
}

.workbench-main {
  flex: 1;
  padding: 14px;
}

.review-toolbar,
.review-footer {
  background: #fff;
  border: 1px solid #e5e9ef;
  border-radius: 8px;
  padding: 10px 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.toolbar-left {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.breadcrumb {
  color: #606266;
  font-size: 14px;
}

.file-info {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #909399;
}

.tag {
  padding: 2px 8px;
  border-radius: 12px;
  background: #eef2f6;
  color: #606266;
}

.tag.success {
  background: #f0f9eb;
  color: #67c23a;
}

.toolbar-right,
.header-actions,
.footer-right {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn {
  border: 1px solid #dcdfe6;
  background: #fff;
  color: #606266;
  border-radius: 4px;
  padding: 6px 12px;
  cursor: pointer;
}

.btn.primary {
  background: #409eff;
  color: #fff;
  border-color: #409eff;
}

.btn.success {
  background: #67c23a;
  color: #fff;
  border-color: #67c23a;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.review-content {
  margin-top: 12px;
  margin-bottom: 12px;
  display: grid;
  gap: 12px;
}

.review-content.view-mode-split {
  grid-template-columns: 1fr 1fr;
}

.review-content.view-mode-data,
.review-content.view-mode-pdf {
  grid-template-columns: 1fr;
}

.data-panel,
.pdf-panel {
  background: #fff;
  border: 1px solid #e5e9ef;
  border-radius: 8px;
  min-height: 620px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 12px 14px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-header h3 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.panel-content {
  padding: 12px;
  overflow: auto;
}

.card-block {
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
}

.card-block h4 {
  margin: 0 0 12px;
  border-bottom: 2px solid #409eff;
  padding-bottom: 8px;
}

.sub-card {
  border: 1px solid #f0f2f5;
  background: #fafbfc;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 10px;
}

.sub-card h5 {
  margin: 0 0 10px;
}

.table-block {
  margin-bottom: 12px;
}

.table-block h5 {
  margin: 0 0 8px;
}

.table-wrapper {
  overflow: auto;
  border: 1px solid #ebeef5;
  border-radius: 6px;
}

.ocr-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
  background: #fff;
}

.ocr-table th,
.ocr-table td {
  border-bottom: 1px solid #f0f2f5;
  padding: 8px 10px;
  text-align: left;
  font-size: 13px;
  color: #303133;
  vertical-align: top;
}

.ocr-table th {
  background: #f8fafc;
  color: #606266;
  font-weight: 600;
}

.form-grid {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 8px 10px;
  align-items: center;
}

.form-grid.two-col {
  grid-template-columns: 100px 1fr 100px 1fr;
}

input,
textarea,
select {
  width: 100%;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 6px 8px;
  font-size: 13px;
  box-sizing: border-box;
}

textarea {
  margin-bottom: 8px;
}

.pdf-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-bottom: 1px solid #ebeef5;
  background: #f8fafc;
}

.pdf-content {
  flex: 1;
  background: #e9edf2;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 520px;
}

.pdf-content iframe {
  width: 96%;
  height: 96%;
  border: none;
  background: #fff;
}

.empty-pdf {
  color: #909399;
}

.upload-btn input {
  display: none;
}

.highlight-tip {
  color: #409eff;
  font-size: 13px;
}

.review-footer {
  margin-top: 8px;
}

.footer-left {
  color: #909399;
  font-size: 13px;
}

@media (max-width: 1200px) {
  .review-content.view-mode-split {
    grid-template-columns: 1fr;
  }

  .form-grid.two-col {
    grid-template-columns: 120px 1fr;
  }
}
</style>
