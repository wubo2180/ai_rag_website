<template>
  <div class="pdf-viewer">
    <div class="toolbar">
      <div class="toolbar-left">
        <el-button size="small" :loading="loading" @click="loadPdf(true)">刷新预览</el-button>
        <el-button size="small" :disabled="loading || scale <= minScale" @click="zoomOut">缩小</el-button>
        <span class="zoom-label">{{ Math.round(scale * 100) }}%</span>
        <el-button size="small" :disabled="loading || scale >= maxScale" @click="zoomIn">放大</el-button>
        <el-button size="small" :disabled="loading" @click="downloadPdf">下载</el-button>
      </div>
      <div class="toolbar-right">
        <span v-if="errorText" class="status">{{ errorText }}</span>
        <span v-else-if="highlightSummary" class="highlight-summary">{{ highlightSummary }}</span>
        <span v-else-if="hintText" class="hint">{{ hintText }}</span>
      </div>
    </div>

    <!-- 高亮词列表面板 -->
    <div v-if="normalizedHighlightTerms.length && pages.length" class="highlight-terms-panel">
      <div class="panel-header">
        <span class="panel-title">已识别的高亮词 ({{ normalizedHighlightTerms.length }})</span>
        <el-button text size="small" @click="toggleTermsPanel">
          {{ showTermsPanel ? '收起' : '展开' }}
        </el-button>
      </div>
      <div v-show="showTermsPanel" class="terms-list">
        <div
          v-for="(term, index) in normalizedHighlightTerms"
          :key="index"
          class="term-item"
          :class="{ 'has-match': termMatchCount(term) > 0 }"
        >
          <span class="term-text">{{ term }}</span>
          <span class="term-count" v-if="termMatchCount(term) > 0">
            命中 {{ termMatchCount(term) }} 处
          </span>
          <span class="term-count no-match" v-else>未找到</span>
        </div>
      </div>
    </div>

    <div ref="scrollRef" class="content">
      <div v-if="pages.length" class="pages">
        <section v-for="page in pages" :key="page.pageNumber" class="page-card">
          <div class="page-label">第 {{ page.pageNumber }} / {{ pages.length }} 页</div>
          <div
            class="page-stage"
            :style="{ width: `${page.viewport.width}px`, height: `${page.viewport.height}px` }"
          >
            <canvas :ref="bindCanvasRef(page.pageNumber)" class="page-canvas"></canvas>
            <div
              :ref="bindTextLayerRef(page.pageNumber)"
              class="text-layer"
              :style="{ width: `${page.viewport.width}px`, height: `${page.viewport.height}px` }"
            ></div>
          </div>
        </section>
      </div>
      <el-empty v-else :description="loading ? '正在加载 PDF...' : '暂无可预览 PDF'" />
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf.mjs'
import pdfjsWorker from 'pdfjs-dist/legacy/build/pdf.worker.min.mjs?url'
import ocrCheckerApi from '@/services/ocrCheckerApi'

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker

const props = defineProps({
  fileId: {
    type: [String, Number],
    required: true,
  },
  highlightTerms: {
    type: Array,
    default: () => [],
  },
})

const loading = ref(false)
const errorText = ref('')
const hintText = ref('')
const pages = ref([])
const scale = ref(1.25)
const pdfBytes = ref(null)
const renderNonce = ref(0)
const totalHighlights = ref(0)
const scrollRef = ref(null)
const showTermsPanel = ref(true)
const termMatchCounts = ref({})

const minScale = 0.75
const maxScale = 2.25
const canvasRefs = reactive({})
const textLayerRefs = reactive({})
let highlightTimer = null

const normalizedHighlightTerms = computed(() => {
  const uniqueTerms = new Set()
  ;(props.highlightTerms || []).forEach((item) => {
    const text = String(item || '').trim()
    if (!text) return
    if (text.length < 2) return
    if (text.length > 120) return
    uniqueTerms.add(text)
  })
  return Array.from(uniqueTerms).sort((left, right) => right.length - left.length)
})

const highlightSummary = computed(() => {
  if (!normalizedHighlightTerms.value.length || !pages.value.length) return ''
  if (!totalHighlights.value) {
    return `已准备 ${normalizedHighlightTerms.value.length} 个高亮词`
  }
  return `已高亮 ${normalizedHighlightTerms.value.length} 个字段值，命中 ${totalHighlights.value} 处`
})

const escapeHtml = (value) => String(value || '')
  .replaceAll('&', '&amp;')
  .replaceAll('<', '&lt;')
  .replaceAll('>', '&gt;')

const bindCanvasRef = (pageNumber) => (element) => {
  if (element) {
    canvasRefs[pageNumber] = element
  } else {
    delete canvasRefs[pageNumber]
  }
}

const bindTextLayerRef = (pageNumber) => (element) => {
  if (element) {
    textLayerRefs[pageNumber] = element
  } else {
    delete textLayerRefs[pageNumber]
  }
}

const findHighlightRanges = (text) => {
  const source = String(text || '')
  const lowerSource = source.toLowerCase()
  const ranges = []

  normalizedHighlightTerms.value.forEach((term) => {
    const lowerTerm = term.toLowerCase()
    let startIndex = 0
    while (startIndex < lowerSource.length) {
      const foundAt = lowerSource.indexOf(lowerTerm, startIndex)
      if (foundAt === -1) break
      const endAt = foundAt + term.length
      const overlapped = ranges.some((item) => !(endAt <= item.start || foundAt >= item.end))
      if (!overlapped) {
        ranges.push({ start: foundAt, end: endAt })
      }
      startIndex = foundAt + Math.max(term.length, 1)
    }
  })

  return ranges.sort((left, right) => left.start - right.start)
}

const decorateText = (text) => {
  const source = String(text || '')
  if (!source || !normalizedHighlightTerms.value.length) {
    return { html: escapeHtml(source), count: 0 }
  }

  const ranges = findHighlightRanges(source)
  if (!ranges.length) {
    return { html: escapeHtml(source), count: 0 }
  }

  let cursor = 0
  let html = ''
  ranges.forEach((range) => {
    if (range.start > cursor) {
      html += escapeHtml(source.slice(cursor, range.start))
    }
    html += `<mark class="pdf-highlight">${escapeHtml(source.slice(range.start, range.end))}</mark>`
    cursor = range.end
  })
  if (cursor < source.length) {
    html += escapeHtml(source.slice(cursor))
  }

  return { html, count: ranges.length }
}

const buildTextSpan = (item, viewport) => {
  const tx = pdfjsLib.Util.transform(viewport.transform, item.transform)
  const fontSize = Math.hypot(tx[2], tx[3]) || 12
  const angle = Math.atan2(tx[1], tx[0])
  const left = tx[4]
  const top = tx[5] - fontSize
  const { html, count } = decorateText(item.str || '')

  return {
    html,
    count,
    style: {
      left: `${left}px`,
      top: `${top}px`,
      fontSize: `${fontSize}px`,
      transform: angle ? `rotate(${angle}rad)` : 'none',
      transformOrigin: 'left bottom',
    },
  }
}

const renderPageTextLayer = (page) => {
  const container = textLayerRefs[page.pageNumber]
  if (!container) return 0

  container.innerHTML = ''
  let matchCount = 0
  page.textItems.forEach((item) => {
    const spanMeta = buildTextSpan(item, page.viewport)
    const span = document.createElement('span')
    span.className = 'text-item'
    Object.assign(span.style, spanMeta.style)
    span.innerHTML = spanMeta.html
    container.appendChild(span)
    matchCount += spanMeta.count
  })

  return matchCount
}

const updateHighlights = () => {
  let nextCount = 0
  pages.value.forEach((page) => {
    nextCount += renderPageTextLayer(page)
  })
  totalHighlights.value = nextCount

  // 计算每个高亮词的命中次数（直接计算，不依赖缓存）
  const counts = {}
  normalizedHighlightTerms.value.forEach((term) => {
    if (!term || !pages.value.length) {
      counts[term] = 0
      return
    }
    const lowerTerm = term.toLowerCase()
    let count = 0
    pages.value.forEach((page) => {
      page.textItems.forEach((item) => {
        const text = String(item.str || '').toLowerCase()
        let startIndex = 0
        while (startIndex < text.length) {
          const foundAt = text.indexOf(lowerTerm, startIndex)
          if (foundAt === -1) break
          count += 1
          startIndex = foundAt + Math.max(term.length, 1)
        }
      })
    })
    counts[term] = count
  })
  termMatchCounts.value = counts
}

const renderPageCanvas = async (pdfDocument, pageMeta, token) => {
  const canvas = canvasRefs[pageMeta.pageNumber]
  if (!canvas) return

  const page = await pdfDocument.getPage(pageMeta.pageNumber)
  if (token !== renderNonce.value) return

  const viewport = page.getViewport({ scale: scale.value })
  const context = canvas.getContext('2d')
  const outputScale = window.devicePixelRatio || 1

  canvas.width = Math.floor(viewport.width * outputScale)
  canvas.height = Math.floor(viewport.height * outputScale)
  canvas.style.width = `${viewport.width}px`
  canvas.style.height = `${viewport.height}px`
  context.setTransform(outputScale, 0, 0, outputScale, 0, 0)

  await page.render({
    canvasContext: context,
    viewport,
  }).promise
}

const renderDocument = async () => {
  if (!pdfBytes.value) return

  const token = Date.now()
  renderNonce.value = token
  totalHighlights.value = 0

  const loadingTask = pdfjsLib.getDocument({ data: pdfBytes.value })
  const pdfDocument = await loadingTask.promise

  const nextPages = []
  for (let pageNumber = 1; pageNumber <= pdfDocument.numPages; pageNumber += 1) {
    const page = await pdfDocument.getPage(pageNumber)
    const viewport = page.getViewport({ scale: scale.value })
    const textContent = await page.getTextContent()
    nextPages.push({
      pageNumber,
      viewport,
      textItems: textContent.items || [],
    })
  }

  if (token !== renderNonce.value) return

  pages.value = nextPages
  await nextTick()

  for (const page of nextPages) {
    await renderPageCanvas(pdfDocument, page, token)
  }

  if (token !== renderNonce.value) return
  updateHighlights()
}

const loadPdf = async (reloadBinary = false) => {
  loading.value = true
  errorText.value = ''
  hintText.value = ''

  try {
    const previewData = await ocrCheckerApi.getFilePreviewUrl(props.fileId)
    const preview = previewData?.data || previewData || {}
    const diagnostics = preview?.diagnostics || null

    if (diagnostics?.minio?.available) {
      hintText.value = `PDF 来自对象存储：${diagnostics.minio.bucket}/${diagnostics.minio.object}`
    } else {
      hintText.value = '当前使用项目内 PDF 预览器，并同步高亮抽取结果'
    }

    if (reloadBinary || !pdfBytes.value) {
      const blob = await ocrCheckerApi.downloadFileBlob(props.fileId)
      pdfBytes.value = new Uint8Array(await blob.arrayBuffer())
    }

    await renderDocument()
  } catch (error) {
    pages.value = []
    totalHighlights.value = 0
    errorText.value = 'PDF 预览加载失败'
    ElMessage.warning(error?.response?.data?.message || error?.message || 'PDF 预览加载失败')
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

const zoomIn = () => {
  scale.value = Math.min(maxScale, Number((scale.value + 0.1).toFixed(2)))
}

const zoomOut = () => {
  scale.value = Math.max(minScale, Number((scale.value - 0.1).toFixed(2)))
}

const termMatchCount = (term) => {
  if (!term) return 0
  return termMatchCounts.value[term] ?? 0
}

const toggleTermsPanel = () => {
  showTermsPanel.value = !showTermsPanel.value
}

watch(() => props.fileId, () => loadPdf(true))
</script>

<style scoped>
.pdf-viewer {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 10px;
  height: 50px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ec;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.zoom-label {
  margin: 0 10px;
  font-weight: 500;
  color: #333;
}

.status {
  color: #f56c6c;
}

.highlight-summary {
  color: #67c23a;
}

.hint {
  color: #909399;
}

.highlight-terms-panel {
  background-color: #fff;
  border-top: 1px solid #e4e7ec;
  padding: 10px;
  max-height: 300px;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.panel-title {
  font-weight: 600;
  color: #333;
}

.terms-list {
  padding-left: 10px;
}

.term-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
}

.term-text {
  color: #333;
}

.term-count {
  font-size: 12px;
  color: #999;
}

.term-count.no-match {
  color: #f56c6c;
}

.content {
  flex: 1;
  overflow-y: auto;
}

.pages {
  display: flex;
  flex-direction: column;
  padding: 10px;
}

.page-card {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #e4e7ec;
  border-radius: 4px;
}

.page-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 10px;
}

.page-stage {
  position: relative;
  overflow: hidden;
  border: 1px solid #e4e7ec;
  border-radius: 4px;
}

.page-canvas {
  display: block;
}

.text-layer {
  position: absolute;
  inset: 0;
  color: transparent;
  user-select: text;
  pointer-events: auto;
}

.text-item {
  position: absolute;
  white-space: pre;
  line-height: 1;
  color: transparent;
  pointer-events: auto;
}

.pdf-highlight {
  background: linear-gradient(135deg, rgba(250, 204, 21, 0.5) 0%, rgba(251, 191, 36, 0.6) 100%);
  color: transparent;
  border-radius: 3px;
  box-shadow: 0 0 0 1.5px rgba(234, 179, 8, 0.5), 0 2px 4px rgba(234, 179, 8, 0.3);
  font-weight: 600;
  padding: 1px 2px;
  margin: -1px -2px;
  animation: highlight-pulse 2s ease-in-out infinite;
}

@keyframes highlight-pulse {
  0%, 100% {
    box-shadow: 0 0 0 1.5px rgba(234, 179, 8, 0.5), 0 2px 4px rgba(234, 179, 8, 0.3);
  }
  50% {
    box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.7), 0 2px 6px rgba(234, 179, 8, 0.5);
  }
}
</style>
