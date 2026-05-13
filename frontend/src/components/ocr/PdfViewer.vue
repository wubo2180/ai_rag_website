<template>
  <div class="pdf-viewer">
    <div class="toolbar">
      <el-button size="small" @click="loadPdf" :loading="loading">刷新预览</el-button>
      <el-button size="small" @click="downloadPdf" :disabled="!pdfSrc">下载</el-button>
      <span class="status" v-if="errorText">{{ errorText }}</span>
      <span class="hint" v-else-if="hintText">{{ hintText }}</span>
    </div>
    <div class="content">
      <iframe v-if="pdfSrc" :src="pdfSrc" title="pdf-preview" />
      <el-empty v-else :description="loading ? '正在加载 PDF...' : '暂无可预览 PDF'" />
    </div>
  </div>
</template>

<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const props = defineProps({
  fileId: {
    type: [String, Number],
    required: true,
  },
})

const pdfSrc = ref('')
const loading = ref(false)
const errorText = ref('')
const hintText = ref('')
let blobUrl = ''

const revokeBlobUrl = () => {
  if (blobUrl) {
    URL.revokeObjectURL(blobUrl)
    blobUrl = ''
  }
}

const loadPdf = async () => {
  loading.value = true
  errorText.value = ''
  hintText.value = ''
  revokeBlobUrl()

  try {
    const previewData = await ocrCheckerApi.getFilePreviewUrl(props.fileId)
    const root = previewData || {}
    const preview = root?.data || root
    const url = preview?.url || preview?.preview_url || ''
    const diagnostics = preview?.diagnostics || null

    if (diagnostics) {
      if (diagnostics.local_exists) {
        hintText.value = '诊断：本地文件可用，使用下载流预览。'
      } else if (diagnostics.minio?.available) {
        hintText.value = `诊断：MinIO对象可用（${diagnostics.minio.bucket}/${diagnostics.minio.object}）。`
      } else if (diagnostics.minio?.error) {
        hintText.value = `诊断：${diagnostics.minio.error}`
      } else {
        hintText.value = '诊断：未命中本地文件，正在尝试对象存储。'
      }
    }

    if (url) {
      pdfSrc.value = url
      return
    }

    const blob = await ocrCheckerApi.downloadFileBlob(props.fileId)
    blobUrl = URL.createObjectURL(blob)
    pdfSrc.value = blobUrl
  } catch (e) {
    pdfSrc.value = ''
    errorText.value = 'PDF 预览加载失败'
    ElMessage.warning(e?.response?.data?.message || e?.message || 'PDF 预览加载失败')
  } finally {
    loading.value = false
  }
}

const downloadPdf = async () => {
  try {
    const blob = await ocrCheckerApi.downloadFileBlob(props.fileId, false)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `ocr-file-${props.fileId}.pdf`
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.warning('下载失败')
  }
}

watch(() => props.fileId, loadPdf)
onMounted(loadPdf)
onUnmounted(revokeBlobUrl)
</script>

<style scoped>
.pdf-viewer { display: flex; flex-direction: column; height: 100%; }
.toolbar { display: flex; align-items: center; gap: 8px; padding: 8px 0; }
.status { color: #dc2626; font-size: 12px; }
.hint { color: #d97706; font-size: 12px; }
.content {
  flex: 1;
  height: calc(100vh - 240px);
  min-height: 700px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  background: #f8fafc;
  display: flex;
}
iframe {
  width: 100%;
  height: 100%;
  min-height: 700px;
  border: none;
  display: block;
}
</style>
