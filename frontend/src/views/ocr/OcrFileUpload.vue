<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="toolbar">
        <h2>OCR 文件上传</h2>
        <button class="btn" @click="router.push('/ocr/files')">返回文件管理</button>
      </div>

      <div class="panel">
        <input type="file" accept="application/pdf" @change="onPick" />
        <div v-if="file" class="meta">已选择：{{ file.name }} ({{ (file.size/1024).toFixed(1) }} KB)</div>
        <div class="actions">
          <button class="btn primary" :disabled="!file || uploading" @click="upload">{{ uploading ? '上传中...' : '上传并入库' }}</button>
        </div>
        <p class="tip">说明：上传会优先走 checker 服务的批量上传接口。</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import NavigationSidebar from '@/components/NavigationSidebar.vue'
import ocrCheckerApi from '@/services/ocrCheckerApi'

const router = useRouter()
const file = ref(null)
const uploading = ref(false)

const onPick = (e) => {
  file.value = e.target.files?.[0] || null
}

const upload = async () => {
  if (!file.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('files', file.value)
    fd.append('document_type_code', 'commission')

    await ocrCheckerApi.batchUpload(fd)

    ElMessage.success('上传成功')
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
.meta { margin:10px 0; color:#64748b; }
.actions { margin:10px 0; }
.tip { color:#94a3b8; font-size:12px; }
.btn { border:1px solid #dce4f4; background:#fff; padding:6px 12px; border-radius:8px; cursor:pointer; }
.btn.primary { background:#6366f1; color:#fff; border-color:#6366f1; }
.btn:disabled { opacity:.5; cursor:not-allowed; }
</style>
