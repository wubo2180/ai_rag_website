<template>
  <div class="ocr-module-page">
    <NavigationSidebar />
    <div class="content">
      <div class="header">
        <h1>OCR 业务模块</h1>
        <p>已从 IBoxTech-ocrchecker 迁移到当前 Vue + Django 统一架构。</p>
      </div>

      <div class="cards">
        <div class="card" @click="go('/ocr/files')">
          <h3>文件管理</h3>
          <p>查看文件、状态、执行识别与核对。</p>
        </div>
        <div class="card" @click="go('/ocr/upload')">
          <h3>文件上传</h3>
          <p>上传 PDF 进入 OCR 处理流水线。</p>
        </div>
        <div class="card" @click="go('/ocr-center')">
          <h3>OCR 中心</h3>
          <p>进入统一代理入口与服务工作台。</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()
const go = (path) => router.push(path)
</script>

<style scoped>
.ocr-module-page { display:flex; min-height:100vh; background:#f4f7fb; }
.content { flex:1; padding:24px; }
.header { background:#fff; border:1px solid #e8edf7; border-radius:12px; padding:18px; margin-bottom:14px; }
.header h1 { margin:0 0 8px; color:#1e293b; }
.header p { margin:0; color:#64748b; }
.cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:12px; }
.card { background:#fff; border:1px solid #e8edf7; border-radius:12px; padding:16px; cursor:pointer; transition:.2s; }
.card:hover { transform:translateY(-2px); box-shadow:0 8px 24px rgba(15,23,42,.08); }
.card h3 { margin:0 0 8px; color:#1e293b; }
.card p { margin:0; color:#64748b; font-size:13px; }
</style>
