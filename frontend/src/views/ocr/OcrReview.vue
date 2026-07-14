<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <div>
          <h2>文件核对</h2>
          <p class="sub">
            fileId: {{ fileId }} | {{ docTypeText }} | {{ fixVersion }}
          </p>
        </div>
        <div class="actions">
          <button
            class="btn"
            @click="
              router.push({
                path: '/ocr/files',
                query: { page: route.query.page || 1 },
              })
            "
          >
            返回列表
          </button>
          <button class="btn" @click="loadData">刷新</button>
          <button class="btn success" :disabled="saving" @click="saveDraft">
            保存修改
          </button>
          <button
            class="btn warning"
            :disabled="saving"
            @click="markAsUnreviewed"
          >
            标记未核对
          </button>
          <button
            class="btn primary"
            :disabled="saving"
            @click="completeReview"
          >
            完成核对
          </button>
        </div>
      </div>

      <div v-if="fileInfo" class="panel">
        <div class="meta-grid">
          <div><b>文件名：</b>{{ fileInfo.filename }}</div>
          <div><b>文档类型：</b>{{ fileDocumentTypeText }}</div>
          <div><b>OCR 状态：</b>{{ fileOcrStatusText }}</div>
          <div><b>核对状态：</b>{{ fileReviewStatusText }}</div>
        </div>
      </div>

      <div class="split">
        <div class="panel editor-panel">
          <h3>{{ docTypeText }}核对数据</h3>
          <component
            :is="currentForm"
            v-if="currentForm"
            v-model="formData"
            :readonly="false"
          />
          <el-empty v-else description="暂不支持该文档类型" />
        </div>

        <div class="panel preview-panel">
          <PdfViewer :file-id="fileId" :highlight-terms="paperHighlightTerms" />
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
  import {
    buildPaperHighlightTerms,
    createPaperTemplate,
    hasPaperShape,
    normalizePaperData,
  } from './paperTemplate'

  const route = useRoute()
  const router = useRouter()
  const fileId = route.params.fileId
  const fixVersion = 'paper-template-v2'

  const fileInfo = ref(null)
  const formData = ref({})
  const saving = ref(false)

  const docType = computed(() =>
    String(fileInfo.value?.document_type_code || 'commission').toLowerCase(),
  )
  const docTypeText = computed(() =>
    docType.value === 'paper' ? '论文' : '委托单',
  )
  const currentForm = computed(() =>
    docType.value === 'paper' ? PaperForm : CommissionForm,
  )
  const fallbackTitle = computed(() =>
    String(fileInfo.value?.filename || '').replace(/\.pdf$/i, ''),
  )
  const paperHighlightTerms = computed(() =>
    docType.value === 'paper'
      ? buildPaperHighlightTerms(formData.value, fallbackTitle.value)
      : [],
  )

  const normalizeStatus = (value) => String(value || '').toLowerCase()

  const getDocumentTypeText = (code) => {
    const normalized = normalizeStatus(code)
    if (normalized === 'paper') return '论文'
    if (normalized === 'commission') return '委托单'
    return '-'
  }

  const getOcrStatusText = (status) => {
    const normalized = normalizeStatus(status)
    if (normalized === 'completed') return '已识别'
    if (normalized === 'pending') return '待识别'
    if (normalized === 'processing') return '识别中'
    if (normalized === 'failed') return '识别失败'
    return '-'
  }

  const getReviewStatusText = (status) => {
    const normalized = normalizeStatus(status)
    if (normalized === 'completed') return '已核对'
    if (['unassigned', 'pending', 'assigned'].includes(normalized))
      return '待核对'
    if (['processing', 'in_progress'].includes(normalized)) return '核对中'
    if (normalized === 'failed') return '核对失败'
    return '-'
  }

  const fileDocumentTypeText = computed(() =>
    getDocumentTypeText(fileInfo.value?.document_type_code),
  )
  const fileOcrStatusText = computed(() =>
    getOcrStatusText(fileInfo.value?.ocr_status),
  )
  const fileReviewStatusText = computed(() =>
    getReviewStatusText(fileInfo.value?.review_status),
  )

  const hasCommissionShape = (obj) => {
    if (!obj || typeof obj !== 'object') return false
    return Boolean(
      (obj.basic_info && typeof obj.basic_info === 'object') ||
      Array.isArray(obj.test_items) ||
      Array.isArray(obj.special_tests),
    )
  }

  const hasDocumentShape = (obj) =>
    hasPaperShape(obj) || hasCommissionShape(obj)

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

      ;['data', 'body', 'result', 'payload', 'content'].forEach((key) => {
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

  const normalizeCommissionData = (rawData) => ({
    basic_info: rawData?.basic_info || {},
    test_items: rawData?.test_items || [],
    special_tests: rawData?.special_tests || [],
  })

  const normalizeData = (rawData, dt = docType.value) => {
    const normalizedType = String(dt || '').toLowerCase()
    if (normalizedType === 'paper') {
      return normalizePaperData(rawData, fallbackTitle.value)
    }
    if (normalizedType === 'commission') {
      return normalizeCommissionData(rawData)
    }
    if (hasPaperShape(rawData)) {
      return normalizePaperData(rawData, fallbackTitle.value)
    }
    return normalizeCommissionData(rawData)
  }

  const loadData = async () => {
    try {
      const fileData = await ocrCheckerApi.getFileDetail(fileId)
      fileInfo.value = fileData?.data || fileData || null
    } catch {
      fileInfo.value = null
      ElMessage.warning('读取文件信息失败')
    }

    const requestPlans = [
      () => ocrCheckerApi.getDocumentData(fileId),
      () =>
        ocrGatewayAPI.proxyRequest(
          'checker',
          `files/${fileId}/document-data`,
          'GET',
          null,
          { refresh: 1 },
        ),
    ]

    for (const request of requestPlans) {
      try {
        const data = await request()
        const { payload, documentType } = extractDocumentPayload(data)
        if (hasDocumentShape(payload)) {
          formData.value = normalizeData(payload, documentType || docType.value)
          return
        }
      } catch {
        // ignore and try next fallback path
      }
    }

    formData.value =
      docType.value === 'paper'
        ? createPaperTemplate(fallbackTitle.value)
        : normalizeCommissionData({})
    ElMessage.warning('未命中有效核对数据，已回退为空模板，可点击“刷新”重试')
  }

  const saveDraft = async () => {
    saving.value = true
    try {
      await ocrCheckerApi.updateDocumentData(fileId, formData.value)
      ElMessage.success('保存成功')
    } catch (error) {
      ElMessage.error(error?.response?.data?.message || '保存失败')
    } finally {
      saving.value = false
    }
  }

  const completeReview = async () => {
    saving.value = true
    try {
      await ocrCheckerApi.updateDocumentData(fileId, formData.value)
      await ocrCheckerApi.completeReview(fileId)
      ElMessage.success('已标记为完成核对')
      await loadData()
    } catch (error) {
      ElMessage.warning(error?.response?.data?.message || '完成核对失败')
    } finally {
      saving.value = false
    }
  }

  const markAsUnreviewed = async () => {
    saving.value = true
    try {
      await ocrCheckerApi.updateDocumentData(fileId, formData.value)
      await ocrCheckerApi.markAsUnreviewed(fileId)
      ElMessage.success('已标记为未核对')
      await loadData()
    } catch (error) {
      ElMessage.warning(error?.response?.data?.message || '标记未核对失败')
    } finally {
      saving.value = false
    }
  }

  onMounted(loadData)
</script>

<style scoped>
  .ocr-module-page {
    display: flex;
    height: 100vh;
    overflow: hidden;
    background: #f4f7fb;
    min-width: 0;
  }
  .content {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100vh;
    overflow: hidden;
    padding: 24px 24px 0;
    box-sizing: border-box;
    min-width: 0;
  }
  .toolbar {
    flex-shrink: 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    gap: 12px;
  }
  .sub {
    margin: 4px 0 0;
    color: #64748b;
    font-size: 12px;
  }
  .actions {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
  .btn {
    border: 1px solid #dce4f4;
    background: #fff;
    padding: 6px 12px;
    border-radius: 8px;
    cursor: pointer;
  }
  .btn.primary {
    background: #6366f1;
    color: #fff;
    border-color: #6366f1;
  }
  .btn.success {
    background: #16a34a;
    color: #fff;
    border-color: #16a34a;
  }
  .btn.warning {
    background: #f59e0b;
    color: #fff;
    border-color: #f59e0b;
  }
  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .panel {
    flex-shrink: 0;
    background: #fff;
    border: 1px solid #e8edf7;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
    min-width: 0;
    max-width: 100%;
    box-sizing: border-box;
  }
  .meta-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(220px, 1fr));
    gap: 8px;
    font-size: 13px;
    color: #334155;
  }
  .split {
    flex: 1;
    min-height: 0;
    display: grid;
    grid-template-columns: minmax(0, 1.08fr) minmax(360px, 0.92fr);
    gap: 12px;
    min-width: 0;
  }
  .split > * {
    min-width: 0;
    min-height: 0;
  }
  .editor-panel {
    overflow-y: auto;
    background: #fff;
    border: 1px solid #e8edf7;
    border-radius: 12px;
    padding: 14px;
    box-sizing: border-box;
  }
  .editor-panel :deep(.paper-form),
  .editor-panel :deep(.commission-form) {
    min-width: 0;
    max-width: 100%;
  }
  .preview-panel {
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border-radius: 12px;
    border: 1px solid #e8edf7;
    background: #fff;
  }
  .preview-panel :deep(.pdf-viewer) {
    flex: 1;
    min-height: 0;
    height: 100%;
  }
  .preview-panel :deep(.pdf-viewer .content) {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
  }

  @media (max-width: 1360px) {
    .ocr-module-page {
      height: auto;
      overflow: auto;
    }
    .content {
      height: auto;
      overflow: visible;
    }
    .split {
      display: block;
    }
    .editor-panel {
      overflow-y: visible;
      height: auto;
      margin-bottom: 12px;
    }
    .preview-panel {
      height: 80vh;
    }
  }
</style>
