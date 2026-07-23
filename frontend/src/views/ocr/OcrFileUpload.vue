<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <h2>OCR 文件上传</h2>
        <button class="btn" @click="router.push('/ocr/files')">返回文件管理</button>
      </div>

      <div class="panel">
        <div class="field">
          <label class="label">文档类型</label>
          <div class="type-switch" role="radiogroup" aria-label="文档类型">
            <label :class="['type-option', { active: documentType === 'paper' }]">
              <input v-model="documentType" type="radio" value="paper" />
              论文 / 文献
            </label>
            <label :class="['type-option', { active: documentType === 'commission' }]">
              <input v-model="documentType" type="radio" value="commission" />
              委托单
            </label>
          </div>
        </div>

        <div class="field">
          <label class="label">上传文件</label>
          <input
            ref="fileInputRef"
            class="hidden-input"
            type="file"
            accept="application/pdf"
            multiple
            @change="onPick"
          />
          <div
            :class="['dropzone', { active: isDragActive }]"
            @click="openFilePicker"
            @dragenter.prevent="onDragEnter"
            @dragover.prevent="onDragOver"
            @dragleave.prevent="onDragLeave"
            @drop.prevent="onDrop"
          >
            <div class="dropzone-title">拖拽 PDF 到这里</div>
            <div class="dropzone-subtitle">也可以点击此区域，一次选择多个文件</div>
            <div class="dropzone-meta">
              <span>仅支持 PDF</span>
              <span>已选 {{ selectedFiles.length }} 个</span>
              <span>总大小 {{ totalSizeText }}</span>
              <span>单批最多 {{ maxChunkFiles }} 个 / {{ formatSize(maxChunkBytes) }}</span>
            </div>
          </div>
          <div class="field-tip">
            选择很多文件也没关系，系统会自动拆成多批上传。若检测到已存在文件，会让你选择删除原文件后重传，或取消该重复文件的上传。
          </div>
        </div>

        <div v-if="uploading" class="upload-progress">
          <div class="progress-header">
            <span>正在上传第 {{ currentChunkIndex }} / {{ totalChunks }} 批</span>
            <span>{{ uploadedCount }} / {{ selectedFiles.length }} 个文件</span>
          </div>
          <div class="progress-track">
            <div class="progress-value" :style="{ width: `${progressPercent}%` }"></div>
          </div>
        </div>

        <div v-if="duplicateFiles.length > 0" class="duplicate-list">
          <div class="duplicate-header">
            <span class="duplicate-title">发现 {{ duplicateFiles.length }} 个未完成处理的重复文件</span>
          </div>
          <ul class="duplicate-items">
            <li v-for="(dup, index) in duplicateFiles" :key="index" class="duplicate-item">
              <div class="duplicate-info">
                <span class="duplicate-filename">{{ dup.filename }}</span>
                <span class="duplicate-reason">
                  {{ dup.reason === 'duplicate_in_batch' ? '批次内重复' : '库中已存在' }}
                </span>
              </div>
              <div v-if="dup.existing_file_id" class="duplicate-existing">
                <span class="duplicate-label">已有文件</span>
                <span class="duplicate-id">ID: {{ dup.existing_file_id }}</span>
                <span v-if="dup.existing_filename" class="duplicate-existing-name">
                  {{ dup.existing_filename }}
                </span>
              </div>
            </li>
          </ul>
        </div>

        <ul v-if="selectedFiles.length" class="file-list">
          <li
            v-for="item in selectedFiles"
            :key="item.name + item.size + item.lastModified"
            class="file-item"
          >
            <span class="file-name">{{ item.name }}</span>
            <span class="file-size">{{ formatSize(item.size) }}</span>
          </li>
        </ul>

        <div class="actions">
          <button class="btn" :disabled="uploading || !selectedFiles.length" @click="clearFiles">
            清空
          </button>
          <button class="btn primary" :disabled="!canUpload" @click="upload">
            {{ uploadButtonText }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const router = useRouter()
const fileInputRef = ref(null)
const selectedFiles = ref([])
const documentType = ref('')
const uploading = ref(false)
const isDragActive = ref(false)
const currentChunkIndex = ref(0)
const totalChunks = ref(0)
const uploadedCount = ref(0)
const duplicateFiles = ref([])

const maxChunkFiles = 40
const maxChunkBytes = 120 * 1024 * 1024

const fileKey = (file) => `${file.name}__${file.size}__${file.lastModified}`
const duplicateMatchKey = (item) => `${item.filename}__${Number(item.file_size || 0)}`
const selectedFileMatchKey = (file) => `${file.name}__${Number(file.size || 0)}`

const formatSize = (size) => {
  const value = Number(size || 0)
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`
  if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)} MB`
  return `${(value / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

const totalSizeText = computed(() => {
  const total = selectedFiles.value.reduce((sum, item) => sum + Number(item.size || 0), 0)
  return formatSize(total)
})

const documentTypeLabel = computed(() => (documentType.value === 'paper' ? '论文' : '委托单'))

const canUpload = computed(() => Boolean(selectedFiles.value.length && documentType.value && !uploading.value))

const progressPercent = computed(() => {
  if (!selectedFiles.value.length) return 0
  return Math.min(100, Math.round((uploadedCount.value / selectedFiles.value.length) * 100))
})

const uploadButtonText = computed(() => {
  if (uploading.value) {
    return `上传中 (${uploadedCount.value}/${selectedFiles.value.length})`
  }
  return `批量上传并入库 (${selectedFiles.value.length})`
})

const buildChunks = (files) => {
  const chunks = []
  let currentChunk = []
  let currentBytes = 0

  files.forEach((file) => {
    const fileSize = Number(file?.size || 0)
    const shouldStartNextChunk =
      currentChunk.length > 0 &&
      (currentChunk.length >= maxChunkFiles || currentBytes + fileSize > maxChunkBytes)

    if (shouldStartNextChunk) {
      chunks.push(currentChunk)
      currentChunk = []
      currentBytes = 0
    }

    currentChunk.push(file)
    currentBytes += fileSize
  })

  if (currentChunk.length) {
    chunks.push(currentChunk)
  }

  return chunks
}

const mergeFiles = (files) => {
  const onlyPdf = Array.from(files || []).filter((item) => {
    const lowerName = String(item?.name || '').toLowerCase()
    return item && lowerName.endsWith('.pdf')
  })

  const merged = new Map(selectedFiles.value.map((item) => [fileKey(item), item]))
  onlyPdf.forEach((item) => {
    merged.set(fileKey(item), item)
  })
  selectedFiles.value = Array.from(merged.values())
}

const openFilePicker = () => {
  fileInputRef.value?.click()
}

const onPick = (event) => {
  mergeFiles(event.target.files)
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const onDragEnter = () => {
  isDragActive.value = true
}

const onDragOver = () => {
  isDragActive.value = true
}

const onDragLeave = (event) => {
  const currentTarget = event.currentTarget
  const relatedTarget = event.relatedTarget
  if (!currentTarget || !relatedTarget || !currentTarget.contains(relatedTarget)) {
    isDragActive.value = false
  }
}

const onDrop = (event) => {
  isDragActive.value = false
  mergeFiles(event.dataTransfer?.files)
}

const resetProgressState = () => {
  currentChunkIndex.value = 0
  totalChunks.value = 0
  uploadedCount.value = 0
}

const clearSelectedFiles = () => {
  selectedFiles.value = []
  isDragActive.value = false
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const clearFiles = () => {
  clearSelectedFiles()
  resetProgressState()
  duplicateFiles.value = []
}

const uploadChunk = async (files, replaceExisting = false) => {
  const formData = new FormData()
  files.forEach((item) => {
    formData.append('files', item)
  })
  formData.append('document_type_code', documentType.value)
  if (replaceExisting) {
    formData.append('replace_existing', '1')
  }
  return ocrCheckerApi.batchUpload(formData)
}

const performUpload = async (files, options = {}) => {
  const { replaceExisting = false } = options
  const chunks = buildChunks(files)
  let savedCount = 0
  const duplicates = []
  const errors = []

  currentChunkIndex.value = 0
  totalChunks.value = chunks.length
  uploadedCount.value = 0

  for (let index = 0; index < chunks.length; index += 1) {
    currentChunkIndex.value = index + 1
    const chunk = chunks[index]
    const response = await uploadChunk(chunk, replaceExisting)
    const payload = response?.data && typeof response.data === 'object' ? response.data : response
    const data = payload?.data && typeof payload.data === 'object' ? payload.data : payload

    savedCount += Number(data?.total ?? 0)
    uploadedCount.value += chunk.length

    if (Array.isArray(data?.duplicates)) {
      duplicates.push(...data.duplicates)
    }

    if (Array.isArray(data?.errors)) {
      errors.push(...data.errors)
    }
  }

  return {
    savedCount,
    duplicates,
    errors,
  }
}

const pickFilesForDuplicates = (duplicates, sourceFiles) => {
  const fileBuckets = new Map()

  sourceFiles.forEach((file) => {
    const key = selectedFileMatchKey(file)
    if (!fileBuckets.has(key)) {
      fileBuckets.set(key, [])
    }
    fileBuckets.get(key).push(file)
  })

  return duplicates.reduce((matchedFiles, duplicate) => {
    const bucket = fileBuckets.get(duplicateMatchKey(duplicate)) || []
    const nextFile = bucket.shift()
    if (nextFile) {
      matchedFiles.push(nextFile)
    }
    return matchedFiles
  }, [])
}

const showUploadSummary = ({ createdCount, replacedCount, batchDuplicateCount, cancelledCount, errorCount }) => {
  const summaryParts = []
  if (createdCount > 0) summaryParts.push(`新增 ${createdCount} 个`)
  if (replacedCount > 0) summaryParts.push(`替换 ${replacedCount} 个`)
  if (batchDuplicateCount > 0) summaryParts.push(`批内重复跳过 ${batchDuplicateCount} 个`)
  if (cancelledCount > 0) summaryParts.push(`取消 ${cancelledCount} 个`)
  if (errorCount > 0) summaryParts.push(`失败 ${errorCount} 个`)

  const summaryText = summaryParts.length > 0 ? summaryParts.join('，') : '没有文件被处理'

  if (errorCount > 0 || cancelledCount > 0 || batchDuplicateCount > 0) {
    ElMessage.warning(`上传完成：${summaryText}`)
    return
  }

  ElMessage.success(`上传成功：${summaryText}`)
}

const upload = async () => {
  if (!canUpload.value) return

  const filesSnapshot = [...selectedFiles.value]
  duplicateFiles.value = []
  uploading.value = true

  try {
    const initialResult = await performUpload(filesSnapshot)
    const initialDuplicates = Array.isArray(initialResult.duplicates) ? initialResult.duplicates : []
    const historyDuplicates = initialDuplicates.filter((item) => item.reason === 'duplicate_in_history')
    const batchDuplicates = initialDuplicates.filter((item) => item.reason === 'duplicate_in_batch')

    let replacedCount = 0
    let finalErrors = [...initialResult.errors]
    let unresolvedHistoryDuplicates = [...historyDuplicates]
    let finalDuplicateFiles = [...initialDuplicates]

    if (historyDuplicates.length > 0) {
      const duplicateTargets = pickFilesForDuplicates(historyDuplicates, filesSnapshot)

      if (duplicateTargets.length > 0) {
        try {
          await ElMessageBox.confirm(
            `检测到 ${historyDuplicates.length} 个已存在的${documentTypeLabel.value}文件。是否删除原文件后重新上传？`,
            '发现重复文件',
            {
              type: 'warning',
              confirmButtonText: '删除原文件并重传',
              cancelButtonText: '取消上传',
              distinguishCancelAndClose: true,
            },
          )

          const replaceResult = await performUpload(duplicateTargets, { replaceExisting: true })
          replacedCount = replaceResult.savedCount
          finalErrors = [...finalErrors, ...replaceResult.errors]

          const replaceDuplicates = Array.isArray(replaceResult.duplicates) ? replaceResult.duplicates : []
          unresolvedHistoryDuplicates = replaceDuplicates.filter((item) => item.reason === 'duplicate_in_history')
          finalDuplicateFiles = [...batchDuplicates, ...replaceDuplicates]
        } catch (action) {
          if (action === 'cancel' || action === 'close') {
            ElMessage.info('已取消重复文件的上传')
          } else {
            throw action
          }
        }
      }
    }

    duplicateFiles.value = finalDuplicateFiles

    showUploadSummary({
      createdCount: initialResult.savedCount,
      replacedCount,
      batchDuplicateCount: batchDuplicates.length,
      cancelledCount: unresolvedHistoryDuplicates.length,
      errorCount: finalErrors.length,
    })

    clearSelectedFiles()
  } catch (error) {
    ElMessage.error(error?.response?.data?.message || '上传失败，请检查 checker 服务状态')
  } finally {
    uploading.value = false
    resetProgressState()
  }
}
</script>

<style scoped>
.ocr-module-page { display:flex; min-height:100vh; background:#f4f7fb; }
.content { flex:1; padding:24px; }
.toolbar { display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }
.panel { background:#fff; border:1px solid #e8edf7; border-radius:12px; padding:16px; }
.field { margin-bottom:14px; }
.label { display:block; margin-bottom:8px; color:#334155; font-size:13px; font-weight:600; }
.field-tip { margin-top:10px; color:#64748b; font-size:12px; }
.type-switch { display:flex; gap:8px; flex-wrap:wrap; }
.type-option { display:inline-flex; align-items:center; gap:6px; min-height:34px; padding:0 12px; border:1px solid #dce4f4; border-radius:8px; color:#475569; cursor:pointer; background:#fff; }
.type-option.active { border-color:#4f46e5; color:#312e81; background:#eef2ff; }
.type-option input { margin:0; }
.hidden-input { display:none; }
.dropzone { display:flex; flex-direction:column; align-items:center; justify-content:center; gap:10px; min-height:180px; padding:24px; border:2px dashed #cbd5e1; border-radius:14px; background:#f8fafc; cursor:pointer; transition:border-color .2s ease, background .2s ease, transform .2s ease; }
.dropzone.active { border-color:#4f46e5; background:#eef2ff; transform:translateY(-1px); }
.dropzone-title { color:#0f172a; font-size:18px; font-weight:600; }
.dropzone-subtitle { color:#64748b; font-size:13px; }
.dropzone-meta { display:flex; flex-wrap:wrap; justify-content:center; gap:8px; color:#475569; font-size:12px; }
.dropzone-meta span { padding:4px 10px; border-radius:999px; background:#e2e8f0; }
.upload-progress { margin:0 0 16px; padding:12px; border:1px solid #e5e7eb; border-radius:10px; background:#f8fafc; }
.progress-header { display:flex; justify-content:space-between; gap:12px; margin-bottom:8px; color:#475569; font-size:13px; }
.progress-track { height:8px; border-radius:999px; background:#e2e8f0; overflow:hidden; }
.progress-value { height:100%; border-radius:999px; background:#6366f1; transition:width .2s ease; }
.duplicate-list { margin:0 0 16px; padding:12px; border:1px solid #fbbf24; border-radius:10px; background:#fffbeb; }
.duplicate-header { margin-bottom:10px; }
.duplicate-title { color:#92400e; font-size:14px; font-weight:600; }
.duplicate-items { margin:0; padding:0; list-style:none; }
.duplicate-item { padding:8px 10px; border-top:1px solid #fde68a; font-size:13px; }
.duplicate-item:first-child { border-top:none; }
.duplicate-info { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-bottom:4px; }
.duplicate-filename { color:#1e293b; word-break:break-all; font-weight:500; }
.duplicate-reason { flex:0 0 auto; padding:2px 8px; border-radius:4px; background:#fef3c7; color:#92400e; font-size:12px; }
.duplicate-existing { display:flex; align-items:center; gap:8px; padding:4px 8px; background:#fef9c3; border-radius:6px; font-size:12px; }
.duplicate-label { color:#78716c; }
.duplicate-id { color:#dc2626; font-weight:600; font-family:monospace; }
.duplicate-existing-name { color:#1e40af; word-break:break-all; }
.file-list { margin:0 0 16px; padding:0; list-style:none; border:1px solid #eef2f7; border-radius:10px; overflow:hidden; }
.file-item { display:flex; justify-content:space-between; gap:12px; padding:10px 12px; border-top:1px solid #eef2f7; font-size:13px; }
.file-item:first-child { border-top:none; }
.file-name { color:#1e293b; word-break:break-all; }
.file-size { flex:0 0 auto; color:#64748b; }
.actions { display:flex; gap:8px; margin-top:16px; }
.btn { border:1px solid #dce4f4; background:#fff; padding:6px 12px; border-radius:8px; cursor:pointer; }
.btn.primary { background:#6366f1; color:#fff; border-color:#6366f1; }
.btn:disabled { opacity:.5; cursor:not-allowed; }
.duplicate-files { margin-top:16px; }
.duplicate-title { margin-bottom:8px; color:#334155; font-size:14px; font-weight:600; }
.duplicate-list { padding:0; list-style:none; border:1px solid #eef2f7; border-radius:10px; overflow:hidden; }
.duplicate-item { display:flex; justify-content:space-between; gap:12px; padding:10px 12px; border-top:1px solid #eef2f7; font-size:13px; }
.duplicate-item:first-child { border-top:none; }
.duplicate-file-id { color:#4f46e5; }
.duplicate-file-name { color:#1e293b; word-break:break-all; }
</style>
