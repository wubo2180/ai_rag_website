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
              论文/文献
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
            <div class="dropzone-title">拖拽一批 PDF 到这里</div>
            <div class="dropzone-subtitle">也可以点击这个区域，一次框选多个文件</div>
            <div class="dropzone-meta">
              <span>仅支持 PDF</span>
              <span>已选 {{ selectedFiles.length }} 个</span>
              <span>总大小 {{ totalSizeText }}</span>
            </div>
          </div>
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
            {{ uploading ? '上传中...' : `批量上传并入库 (${selectedFiles.length})` }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const router = useRouter()
const fileInputRef = ref(null)
const selectedFiles = ref([])
const documentType = ref('')
const uploading = ref(false)
const isDragActive = ref(false)

const fileKey = (file) => `${file.name}__${file.size}__${file.lastModified}`

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

const canUpload = computed(() => {
  return Boolean(selectedFiles.value.length && documentType.value && !uploading.value)
})

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

const onPick = (e) => {
  mergeFiles(e.target.files)
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

const onDragLeave = (e) => {
  const currentTarget = e.currentTarget
  const relatedTarget = e.relatedTarget
  if (!currentTarget || !relatedTarget || !currentTarget.contains(relatedTarget)) {
    isDragActive.value = false
  }
}

const onDrop = (e) => {
  isDragActive.value = false
  mergeFiles(e.dataTransfer?.files)
}

const clearFiles = () => {
  selectedFiles.value = []
  isDragActive.value = false
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const upload = async () => {
  if (!canUpload.value) return

  uploading.value = true
  try {
    const fd = new FormData()
    selectedFiles.value.forEach((item) => {
      fd.append('files', item)
    })
    fd.append('document_type_code', documentType.value)

    const resp = await ocrCheckerApi.batchUpload(fd)
    const total = resp?.data?.total || resp?.data?.data?.total || selectedFiles.value.length

    ElMessage.success(`上传成功，共入库 ${total} 个文件`)
    clearFiles()
    router.push('/ocr/files')
  } catch (e) {
    ElMessage.error(e?.response?.data?.message || '上传失败，请检查 checker 服务')
  } finally {
    uploading.value = false
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
.file-list { margin:0 0 16px; padding:0; list-style:none; border:1px solid #eef2f7; border-radius:10px; overflow:hidden; }
.file-item { display:flex; justify-content:space-between; gap:12px; padding:10px 12px; border-top:1px solid #eef2f7; font-size:13px; }
.file-item:first-child { border-top:none; }
.file-name { color:#1e293b; word-break:break-all; }
.file-size { flex:0 0 auto; color:#64748b; }
.actions { display:flex; gap:8px; margin-top:16px; }
.btn { border:1px solid #dce4f4; background:#fff; padding:6px 12px; border-radius:8px; cursor:pointer; }
.btn.primary { background:#6366f1; color:#fff; border-color:#6366f1; }
.btn:disabled { opacity:.5; cursor:not-allowed; }
</style>
