<template>
  <div class="pdf-viewer-container">
    <div class="viewer-toolbar">
      <div class="toolbar-left">
        <el-button-group>
          <el-button
            size="small"
            :disabled="currentPage <= 1 || !totalPages"
            @click="prevPage"
          >
            <el-icon><ArrowLeft /></el-icon>
          </el-button>
          <el-button
            size="small"
            :disabled="currentPage >= totalPages || !totalPages"
            @click="nextPage"
          >
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </el-button-group>
        
        <div class="page-info">
          <el-input-number
            v-model="currentPage"
            :min="1"
            :max="Math.max(1, totalPages)"
            size="small"
            controls-position="right"
            :disabled="!totalPages || totalPages <= 0"
            @change="goToPage"
          />
          <span class="page-total">/ {{ totalPages || 0 }}</span>
        </div>
      </div>
      
      <div class="toolbar-center">
        <el-button-group>
          <el-button
            size="small"
            :disabled="scale <= 0.5 || !totalPages"
            @click="zoomOut"
          >
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <el-button size="small" @click="resetZoom" :disabled="!totalPages">
            {{ Math.round(scale * 100) }}%
          </el-button>
          <el-button
            size="small"
            :disabled="scale >= 3 || !totalPages"
            @click="zoomIn"
          >
            <el-icon><ZoomIn /></el-icon>
          </el-button>
        </el-button-group>
        
        <el-button size="small" @click="fitWidth">
          <el-icon><FullScreen /></el-icon>
          适应宽度
        </el-button>
      </div>
      
      <div class="toolbar-right">
        <el-button size="small" @click="rotate">
          <el-icon><RefreshRight /></el-icon>
          旋转
        </el-button>
        <el-button size="small" @click="download">
          <el-icon><Download /></el-icon>
          下载
        </el-button>
      </div>
    </div>
    
    <div 
      ref="viewerContainer" 
      class="viewer-content" 
      @scroll="handleScroll"
    >
      <div v-if="loading" class="loading-container">
        <el-skeleton :rows="10" animated />
      </div>
      
      <div v-else-if="error" class="error-container">
        <el-icon class="error-icon"><WarningFilled /></el-icon>
        <p class="error-text">{{ error }}</p>
        <el-button type="primary" @click="reload">重新加载</el-button>
      </div>
      
      <div v-else class="pdf-pages">
        <div v-if="!visiblePages.length" class="no-pages">
          <p>没有可显示的页面</p>
        </div>
        <div
          v-for="page in visiblePages"
          :key="`page-${page.pageNumber}`"
          :class="[
            'pdf-page',
            { 'current-page': page.pageNumber === currentPage }
          ]"
        >
          <!-- <div class="page-info">页面 {{ page.pageNumber }}</div> -->
          <canvas
            :ref="el => setPageCanvasRef(el, page.pageNumber)"
            :id="`pdf-page-${page.pageNumber}`"
            class="page-canvas"
            @click="handlePageClick"
          />
          
          <!-- OCR区域高亮 -->
          <div
            v-if="showHighlight && ocrRegions[page.pageNumber]"
            class="ocr-overlay"
          >
            <div
              v-for="(region, index) in ocrRegions[page.pageNumber]"
              :key="index"
              :class="[
                'ocr-region',
                { 'active': region.id === activeRegionId },
                { 'low-confidence': region.lowConfidence }
              ]"
              :style="{
                left: region.bbox.x + 'px',
                top: region.bbox.y + 'px',
                width: region.bbox.width + 'px',
                height: region.bbox.height + 'px'
              }"
              @click="selectRegion(region)"
              :title="`置信度: ${Math.round((region.confidence || 0) * 100)}%`"
            >
              <div class="region-text">
                <span v-if="region.lowConfidence" class="confidence-badge">
                  {{ Math.round((region.confidence || 0) * 100)}}%
                </span>
                {{ region.text }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 页面缩略图 -->
    <div v-if="showThumbnails" class="thumbnails-panel">
      <div class="panel-header">
        <h4>页面缩略图</h4>
        <el-button 
          type="text" 
          size="small"
          @click="showThumbnails = false"
        >
          <el-icon><Close /></el-icon>
        </el-button>
      </div>
      <div class="thumbnails-list">
        <div
          v-for="page in thumbnails"
          :key="page.pageNumber"
          :class="[
            'thumbnail-item',
            { 'active': page.pageNumber === currentPage }
          ]"
          @click="goToPage(page.pageNumber)"
        >
          <canvas
            :ref="el => setThumbnailCanvasRef(el, page.pageNumber)"
            class="thumbnail-canvas"
          />
          <div class="thumbnail-number">{{ page.pageNumber }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as pdfjsLib from 'pdfjs-dist'

// 设置PDF.js worker - 使用CDN
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js`

// 设置全局配置，确保CMap能被正确加载
pdfjsLib.GlobalWorkerOptions.verbosity = pdfjsLib.VerbosityLevel.ERRORS  // 只显示错误

const props = defineProps({
  url: {
    type: String,
    required: true
  },
  initialPage: {
    type: Number,
    default: 1
  },
  showHighlight: {
    type: Boolean,
    default: true
  },
  ocrRegions: {
    type: Object,
    default: () => ({})
  },
  activeRegionId: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['page-change', 'region-select', 'ready', 'error'])

// 响应式数据
const viewerContainer = ref()
const pageCanvasRefs = reactive({})
const thumbnailCanvasRefs = reactive({})

const loading = ref(false)
const error = ref('')
const pdfDoc = ref(null)
const currentPage = ref(props.initialPage)
const totalPages = ref(1)
const scale = ref(1.2)
const rotation = ref(0)

const showThumbnails = ref(false)
const visiblePages = ref([])
const thumbnails = ref([])

// 追踪渲染任务，避免重复渲染
const renderTasks = reactive({})

// 方法
const setPageCanvasRef = (el, pageNumber) => {
  if (el) {
    pageCanvasRefs[pageNumber] = el
    console.log(`🎯 设置页面 ${pageNumber} 的canvas ref`)
    
    // 如果PDF已加载且这是我们需要渲染的页面，立即渲染
    if (pdfDoc.value && visiblePages.value.some(p => p.pageNumber === pageNumber)) {
      console.log(`⚡ 立即渲染页面 ${pageNumber}`)
      // 使用setTimeout确保在当前执行栈完成后再渲染
      setTimeout(() => renderPage(pageNumber), 0)
    }
  } else {
    // 清理ref
    delete pageCanvasRefs[pageNumber]
    console.log(`🧹 清理页面 ${pageNumber} 的canvas ref`)
  }
}

const setThumbnailCanvasRef = (el, pageNumber) => {
  if (el) {
    thumbnailCanvasRefs[pageNumber] = el
  }
}

const loadPDF = async () => {
  if (!props.url) {
    console.warn('PdfViewer: 没有提供PDF URL')
    return
  }
  
  try {
    loading.value = true
    error.value = ''
    console.log('🔍 PdfViewer开始加载PDF:', props.url)
    console.log('📝 URL类型:', props.url.startsWith('blob:') ? 'Blob URL' : props.url.startsWith('http') ? 'HTTP URL' : '未知类型')
    
    // 如果是Blob URL，先验证可访问性
    if (props.url.startsWith('blob:')) {
      try {
        console.log('🧪 验证Blob URL可访问性...')
        const testResponse = await fetch(props.url)
        const testArrayBuffer = await testResponse.arrayBuffer()
        const testUint8Array = new Uint8Array(testArrayBuffer)
        const pdfHeader = String.fromCharCode(...testUint8Array.slice(0, 4))
        console.log('📄 Blob内容验证:', {
          size: testArrayBuffer.byteLength,
          header: pdfHeader,
          isValidPDF: pdfHeader === '%PDF'
        })
        
        if (pdfHeader !== '%PDF') {
          throw new Error('Blob URL中的数据不是有效的PDF格式')
        }
        console.log('✅ Blob URL验证通过')
      } catch (blobError) {
        console.error('❌ Blob URL验证失败:', blobError)
        throw new Error(`Blob URL访问失败: ${blobError.message}`)
      }
    }
    
    console.log('🚀 开始PDF.js加载任务...')
    const loadingTask = pdfjsLib.getDocument({
      url: props.url,
      // 使用本地托管的CMap文件（避免CORS和网络问题）
      cMapUrl: '/cmaps/',
      cMapPacked: true,
      // 暂不使用standardFontDataUrl，让PDF.js使用内置字体处理
      // standardFontDataUrl: '/standard_fonts/',
      // 禁用范围请求，某些情况下会导致字体加载失败
      disableRange: false,
      disableStream: false,
      // 启用字体替换
      disableFontFace: false,
      // 工作线程
      disableWorker: false,
      // 日志级别
      verbosity: 0
    })
    
    // 监听进度
    loadingTask.onProgress = (progress) => {
      console.log('📊 PDF加载进度:', `${progress.loaded}/${progress.total}`)
    }
    
    // 使用markRaw防止PDF文档对象被Vue响应式系统代理
    const pdf = await loadingTask.promise
    pdfDoc.value = markRaw(pdf)
    console.log('✅ PDF加载成功！页数:', pdfDoc.value.numPages)
    
    totalPages.value = pdfDoc.value.numPages
    
    if (totalPages.value <= 0) {
      throw new Error('PDF没有有效页面')
    }
    
    console.log('🎯 初始化可见页面...')
    // 初始化可见页面（不立即渲染，等ref绑定后自动渲染）
    await updateVisiblePagesWithoutRender()
    
    console.log('🖼️ 生成缩略图...')
    // 生成缩略图
    await generateThumbnails()
    
    emit('ready', {
      totalPages: totalPages.value,
      currentPage: currentPage.value
    })
    
    console.log('🎉 PDF组件初始化完成!')
    
  } catch (err) {
    console.error('❌ PDF加载失败:', err)
    console.error('🌐 PDF URL:', props.url)
    console.error('📋 错误详情:', {
      name: err.name,
      message: err.message,
      stack: err.stack
    })
    error.value = 'PDF加载失败：' + err.message
    emit('error', err)
    
    // 重置状态
    pdfDoc.value = null
    totalPages.value = 1
    
  } finally {
    loading.value = false
  }
}

// 不渲染的版本，只设置可见页面
const updateVisiblePagesWithoutRender = async () => {
  if (!pdfDoc.value) {
    console.warn('🚫 无法更新可见页面: PDF文档未加载')
    return
  }
  
  // 显示所有页面（不再使用虚拟滚动限制）
  console.log(`📄 显示所有页面 (总页数: ${totalPages.value})`)
  
  const pages = []
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    pages.push({ pageNumber: pageNum })
  }
  
  visiblePages.value = pages
  console.log(`📋 设置可见页面: 全部 ${pages.length} 页`)
  console.log('⏳ 等待canvas refs自动绑定和渲染...')
}

// 保留原版本用于用户操作（翻页、缩放等）
const updateVisiblePages = async () => {
  if (!pdfDoc.value) {
    console.warn('🚫 无法更新可见页面: PDF文档未加载')
    return
  }
  
  // 显示所有页面（不再使用虚拟滚动限制）
  console.log(`📄 显示所有页面 (总页数: ${totalPages.value})`)
  
  const pages = []
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    pages.push({ pageNumber: pageNum })
  }
  
  visiblePages.value = pages
  console.log(`📋 设置可见页面: 全部 ${pages.length} 页`)
  
  // 等待DOM更新
  await nextTick()
  console.log('⏳ DOM更新完成，开始渲染现有refs...')
  
  // 渲染已经绑定的页面
  for (const page of pages) {
    if (pageCanvasRefs[page.pageNumber]) {
      console.log(`🎯 准备渲染页面 ${page.pageNumber}`)
      await renderPage(page.pageNumber)
    } else {
      console.log(`⏳ 页面 ${page.pageNumber} 的canvas ref尚未绑定，等待自动渲染`)
    }
  }
  
  console.log('🎉 可见页面更新完成!')
}

const renderPage = async (pageNumber) => {
  if (!pdfDoc.value) {
    console.warn(`🚫 无法渲染页面 ${pageNumber}: PDF文档未加载`)
    return
  }
  
  // 如果该页面正在渲染，先取消
  if (renderTasks[pageNumber]) {
    console.log(`⏸️ 取消页面 ${pageNumber} 的之前渲染任务`)
    try {
      renderTasks[pageNumber].cancel()
    } catch (e) {
      console.warn(`⚠️ 取消渲染任务时出错:`, e.message)
    }
    delete renderTasks[pageNumber]
  }
  
  try {
    console.log(`🎨 开始渲染页面 ${pageNumber}`)
    const page = await pdfDoc.value.getPage(pageNumber)
    let canvas = pageCanvasRefs[pageNumber]
    
    // 如果找不到canvas，尝试直接通过DOM查找
    if (!canvas) {
      console.warn(`🔍 在refs中找不到页面 ${pageNumber} 的canvas，尝试DOM查找`)
      canvas = document.getElementById(`pdf-page-${pageNumber}`)
      
      if (canvas) {
        console.log(`✅ 通过DOM找到了页面 ${pageNumber} 的canvas`)
        // 更新refs
        pageCanvasRefs[pageNumber] = canvas
      } else {
        console.error(`❌ 无法找到页面 ${pageNumber} 的canvas元素`)
        return
      }
    }
    
    console.log(`📐 设置页面 ${pageNumber} 的viewport`, { scale: scale.value, rotation: rotation.value })
    const context = canvas.getContext('2d')
    const viewport = page.getViewport({ scale: scale.value, rotation: rotation.value })
    
    // 提高canvas分辨率以获得更清晰的文字
    const outputScale = window.devicePixelRatio || 1
    canvas.width = viewport.width * outputScale
    canvas.height = viewport.height * outputScale
    canvas.style.width = viewport.width + 'px'
    canvas.style.height = viewport.height + 'px'
    
    // 缩放context以匹配高分辨率
    context.scale(outputScale, outputScale)
    
    console.log(`🖼️ 页面 ${pageNumber} 尺寸:`, { 
      width: viewport.width, 
      height: viewport.height,
      outputScale 
    })
    
    const renderContext = {
      canvasContext: context,
      viewport: viewport,
      // 确保文本能正确渲染
      enableWebGL: false,
      renderInteractiveForms: false
    }
    
    console.log(`⚡ 开始渲染页面 ${pageNumber}...`)
    
    // 保存渲染任务，以便后续取消
    const renderTask = page.render(renderContext)
    renderTasks[pageNumber] = renderTask
    
    await renderTask.promise
    
    // 渲染完成后清理任务
    delete renderTasks[pageNumber]
    
    console.log(`✅ 页面 ${pageNumber} 渲染完成!`)
    
  } catch (err) {
    // 清理失败的任务
    delete renderTasks[pageNumber]
    
    // 如果是取消错误，不需要报警
    if (err.name === 'RenderingCancelledException') {
      console.log(`⏸️ 页面 ${pageNumber} 渲染被取消`)
    } else {
      console.error(`❌ 渲染页面 ${pageNumber} 失败:`, err)
    }
  }
}

const generateThumbnails = async () => {
  if (!pdfDoc.value) return
  
  const thumbs = []
  const thumbnailScale = 0.2
  
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    thumbs.push({ pageNumber: pageNum })
  }
  
  thumbnails.value = thumbs
  
  // 渲染缩略图
  await nextTick()
  for (let pageNum = 1; pageNum <= totalPages.value; pageNum++) {
    await renderThumbnail(pageNum, thumbnailScale)
  }
}

const renderThumbnail = async (pageNumber, thumbnailScale) => {
  if (!pdfDoc.value) return
  
  try {
    const page = await pdfDoc.value.getPage(pageNumber)
    const canvas = thumbnailCanvasRefs[pageNumber]
    
    if (!canvas) return
    
    const context = canvas.getContext('2d')
    const viewport = page.getViewport({ scale: thumbnailScale })
    
    canvas.width = viewport.width
    canvas.height = viewport.height
    
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    }
    
    await page.render(renderContext).promise
    
  } catch (err) {
    console.error(`渲染缩略图 ${pageNumber} 失败:`, err)
  }
}

const prevPage = () => {
  if (currentPage.value > 1) {
    goToPage(currentPage.value - 1)
  }
}

const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    goToPage(currentPage.value + 1)
  }
}

const goToPage = async (pageNumber) => {
  if (pageNumber < 1 || pageNumber > totalPages.value) return
  
  currentPage.value = pageNumber
  await updateVisiblePages()
  
  emit('page-change', pageNumber)
}

const zoomIn = async () => {
  if (scale.value < 3) {
    scale.value = Math.min(3, scale.value * 1.2)
    await updateVisiblePages()
  }
}

const zoomOut = async () => {
  if (scale.value > 0.5) {
    scale.value = Math.max(0.5, scale.value / 1.2)
    await updateVisiblePages()
  }
}

const resetZoom = async () => {
  scale.value = 1.2
  await updateVisiblePages()
}

const fitWidth = async () => {
  const container = viewerContainer.value
  if (!container || !pdfDoc.value) return
  
  const containerWidth = container.clientWidth - 40 // 减去padding
  const page = await pdfDoc.value.getPage(currentPage.value)
  const viewport = page.getViewport({ scale: 1 })
  
  scale.value = containerWidth / viewport.width
  await updateVisiblePages()
}

const rotate = async () => {
  rotation.value = (rotation.value + 90) % 360
  await updateVisiblePages()
}

const download = () => {
  const link = document.createElement('a')
  link.href = props.url
  link.download = 'document.pdf'
  link.click()
}

const reload = () => {
  loadPDF()
}

const handleScroll = () => {
  // 处理滚动事件，可以实现自动翻页
}

const handlePageClick = (event) => {
  // 处理页面点击事件
}

const selectRegion = (region) => {
  emit('region-select', region)
}

// 监听props变化
watch(() => props.url, (newUrl) => {
  if (newUrl) {
    loadPDF()
  }
})

watch(() => props.initialPage, (newPage) => {
  goToPage(newPage)
})

// 生命周期
onMounted(() => {
  if (props.url) {
    loadPDF()
  }
})

onUnmounted(() => {
  // 取消所有正在进行的渲染任务
  Object.keys(renderTasks).forEach(pageNumber => {
    if (renderTasks[pageNumber]) {
      try {
        renderTasks[pageNumber].cancel()
        console.log(`⏸️ 取消页面 ${pageNumber} 的渲染任务`)
      } catch (e) {
        // 忽略取消错误
      }
    }
  })
  
  // 清理资源
  if (pdfDoc.value) {
    try {
      pdfDoc.value.destroy()
      console.log('📚 PDF文档资源已清理')
    } catch (error) {
      console.warn('⚠️ PDF文档清理警告:', error.message)
    }
  }
})
</script>

<style lang="scss" scoped>
.pdf-viewer-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f5f5f5;
  position: relative;
}

.viewer-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $spacing-sm $spacing-md;
  background: $bg-color-white;
  border-bottom: 1px solid $border-color-lighter;
  flex-shrink: 0;
  
  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
  }
  
  .page-info {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    
    .page-total {
      font-size: 12px;
      color: $text-color-secondary;
      white-space: nowrap;
    }
  }
}

.viewer-content {
  flex: 1;
  overflow: auto;
  background: #e0e0e0;
  position: relative;
}

.loading-container {
  padding: $spacing-xl;
}

.error-container {
  @include flex-center;
  flex-direction: column;
  padding: $spacing-xl;
  color: $text-color-secondary;
  
  .error-icon {
    font-size: 48px;
    color: $color-warning;
    margin-bottom: $spacing-md;
  }
  
  .error-text {
    margin-bottom: $spacing-md;
  }
}

.pdf-pages {
  display: flex;
  flex-direction: column;
  align-items: center;  // 居中对齐，确保旋转后也能看到完整页面
  padding: $spacing-lg;
  gap: $spacing-lg;
  min-width: min-content;
}

.pdf-page {
  position: relative;
  background: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-radius: 4px;
  display: inline-block;
  
  &.current-page {
    box-shadow: 0 4px 20px rgba($color-primary, 0.3);
  }
  
  .page-canvas {
    display: block;
    border-radius: 4px;
    max-width: none;
    width: auto;
    height: auto;
  }
}

.ocr-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  
  .ocr-region {
    position: absolute;
    border: 2px solid rgba($color-primary, 0.6);
    background: rgba($color-primary, 0.1);
    cursor: pointer;
    pointer-events: auto;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: $color-primary;
      background: rgba($color-primary, 0.2);
    }
    
    &.active {
      border-color: $color-success;
      background: rgba($color-success, 0.2);
    }
    
    // 低置信度区域样式（红色警告）
    &.low-confidence {
      border-color: rgba($color-warning, 0.8);
      background: rgba($color-warning, 0.15);
      
      &:hover {
        border-color: $color-warning;
        background: rgba($color-warning, 0.25);
      }
      
      &.active {
        border-color: $color-danger;
        background: rgba($color-danger, 0.2);
      }
    }
    
    .region-text {
      position: absolute;
      top: -20px;
      left: 0;
      background: rgba(0, 0, 0, 0.8);
      color: white;
      padding: 2px 6px;
      border-radius: 2px;
      font-size: 10px;
      max-width: 200px;
      @include text-ellipsis;
      opacity: 0;
      transition: opacity 0.2s ease;
      white-space: nowrap;
      
      .confidence-badge {
        display: inline-block;
        background: $color-warning;
        color: white;
        padding: 0 4px;
        border-radius: 2px;
        margin-right: 4px;
        font-weight: bold;
        font-size: 9px;
      }
    }
    
    &:hover .region-text {
      opacity: 1;
    }
  }
}

.thumbnails-panel {
  position: absolute;
  right: 0;
  top: 0;
  width: 200px;
  height: 100%;
  background: $bg-color-white;
  border-left: 1px solid $border-color-lighter;
  display: flex;
  flex-direction: column;
  
  .panel-header {
    @include flex-between;
    padding: $spacing-md;
    border-bottom: 1px solid $border-color-lighter;
    
    h4 {
      font-size: 14px;
      margin: 0;
    }
  }
  
  .thumbnails-list {
    flex: 1;
    overflow-y: auto;
    padding: $spacing-sm;
  }
  
  .thumbnail-item {
    position: relative;
    margin-bottom: $spacing-sm;
    border: 2px solid transparent;
    border-radius: 4px;
    cursor: pointer;
    transition: border-color 0.2s ease;
    
    &:hover {
      border-color: $border-color-base;
    }
    
    &.active {
      border-color: $color-primary;
    }
    
    .thumbnail-canvas {
      width: 100%;
      height: auto;
      display: block;
      border-radius: 2px;
    }
    
    .thumbnail-number {
      position: absolute;
      bottom: 4px;
      right: 4px;
      background: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 2px 4px;
      border-radius: 2px;
      font-size: 10px;
    }
  }
}

// 响应式设计
@include respond-to(sm) {
  .viewer-toolbar {
    flex-wrap: wrap;
    gap: $spacing-sm;
    
    .toolbar-center {
      order: 3;
      width: 100%;
      justify-content: center;
    }
  }
  
  .thumbnails-panel {
    width: 150px;
  }
}
</style>
