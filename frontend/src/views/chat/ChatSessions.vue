<template>
  <div class="sessions-container">
    <div class="sessions-header">
      <h2>会话管理</h2>
      <div class="header-actions">
        <el-button @click="$router.push('/chat')" type="primary" icon="ChatDotSquare">
          新建对话
        </el-button>
        <el-button @click="$router.go(-1)" icon="ArrowLeft">返回</el-button>
      </div>
    </div>

    <div class="sessions-content">
      <div v-if="loading" class="loading">
        <el-skeleton :rows="5" animated />
      </div>

      <div v-else-if="sessions.length === 0" class="empty-state">
        <el-empty description="暂无对话记录">
          <el-button type="primary" @click="$router.push('/chat')">
            开始对话
          </el-button>
        </el-empty>
      </div>

      <div v-else class="sessions-list">
        <el-card 
          v-for="session in sessions" 
          :key="session.id" 
          class="session-card"
          shadow="hover"
        >
          <template #header>
            <div class="session-header">
              <div class="session-info">
                <h4 class="session-title" @click="goToSession(session.id)">
                  {{ session.title || '新对话' }}
                </h4>
                <div class="session-meta">
                  <span class="message-count">{{ session.message_count || 0 }} 条消息</span>
                  <span class="session-time">{{ formatTime(session.updated_at) }}</span>
                </div>
              </div>
              
              <div class="session-actions">
                <el-button 
                  size="small" 
                  icon="Edit" 
                  @click="startRename(session)"
                >
                  重命名
                </el-button>
                <el-button 
                  size="small" 
                  type="danger" 
                  icon="Delete"
                  @click="confirmDelete(session)"
                >
                  删除
                </el-button>
              </div>
            </div>
          </template>

          <div class="session-content">
            <div class="session-date">
              创建时间：{{ formatFullTime(session.created_at) }}
            </div>
            <div class="session-updated">
              更新时间：{{ formatFullTime(session.updated_at) }}
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 重命名对话框 -->
    <el-dialog 
      v-model="renameDialogVisible" 
      title="重命名对话" 
      width="400px"
      @close="cancelRename"
    >
      <el-form :model="renameForm" ref="renameFormRef">
        <el-form-item label="对话标题" :rules="[{ required: true, message: '请输入对话标题' }]" prop="title">
          <el-input 
            v-model="renameForm.title" 
            placeholder="请输入新的对话标题"
            maxlength="100"
            show-word-limit
            @keyup.enter="confirmRename"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="cancelRename">取消</el-button>
        <el-button type="primary" @click="confirmRename" :loading="renameLoading">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotSquare, ArrowLeft, Edit, Delete } from '@element-plus/icons-vue'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const chatStore = useChatStore()

const loading = ref(false)
const sessions = ref([])
const renameDialogVisible = ref(false)
const renameLoading = ref(false)
const renameFormRef = ref()

const renameForm = reactive({
  title: '',
  sessionId: null
})

// 格式化时间
const formatTime = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const diff = now - date
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 24小时内
    return `${Math.floor(diff / 3600000)}小时前`
  } else if (diff < 604800000) { // 7天内
    return `${Math.floor(diff / 86400000)}天前`
  } else {
    return date.toLocaleDateString()
  }
}

const formatFullTime = (dateString) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 获取会话列表
const fetchSessions = async () => {
  loading.value = true
  try {
    const result = await chatStore.fetchSessions()
    if (result.success) {
      sessions.value = chatStore.sessions
    } else {
      ElMessage.error(result.error)
    }
  } catch (error) {
    console.error('获取会话列表失败:', error)
    ElMessage.error('获取会话列表失败')
  } finally {
    loading.value = false
  }
}

// 跳转到会话
const goToSession = (sessionId) => {
  router.push({
    path: '/chat',
    query: { sessionId }
  })
}

// 开始重命名
const startRename = (session) => {
  renameForm.title = session.title || '新对话'
  renameForm.sessionId = session.id
  renameDialogVisible.value = true
}

// 取消重命名
const cancelRename = () => {
  renameDialogVisible.value = false
  renameForm.title = ''
  renameForm.sessionId = null
}

// 确认重命名
const confirmRename = async () => {
  if (!renameFormRef.value) return
  
  try {
    await renameFormRef.value.validate()
    renameLoading.value = true
    
    const result = await chatStore.renameSession(renameForm.sessionId, renameForm.title)
    
    if (result.success) {
      ElMessage.success('重命名成功')
      renameDialogVisible.value = false
      
      // 更新本地会话列表
      const sessionIndex = sessions.value.findIndex(s => s.id === renameForm.sessionId)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].title = renameForm.title
      }
    } else {
      ElMessage.error(result.error)
    }
  } catch (error) {
    console.error('重命名失败:', error)
  } finally {
    renameLoading.value = false
  }
}

// 确认删除
const confirmDelete = (session) => {
  ElMessageBox.confirm(
    `确定要删除对话"${session.title || '新对话'}"吗？此操作不可恢复。`,
    '删除确认',
    {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    const result = await chatStore.deleteSession(session.id)
    
    if (result.success) {
      ElMessage.success('删除成功')
      // 从列表中移除
      sessions.value = sessions.value.filter(s => s.id !== session.id)
    } else {
      ElMessage.error(result.error)
    }
  }).catch(() => {
    // 用户取消删除
  })
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.sessions-container {
  padding: 20px;
  min-height: 100vh;
  background: #f5f5f5;
}

.sessions-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 0 20px;
}

.sessions-header h2 {
  margin: 0;
  color: #333;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.sessions-content {
  max-width: 1000px;
  margin: 0 auto;
}

.loading {
  background: white;
  padding: 20px;
  border-radius: 8px;
}

.empty-state {
  background: white;
  padding: 60px 20px;
  border-radius: 8px;
  text-align: center;
}

.sessions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
}

.session-card {
  transition: transform 0.2s;
}

.session-card:hover {
  transform: translateY(-2px);
}

.session-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-title {
  margin: 0 0 8px 0;
  color: #333;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s;
}

.session-title:hover {
  color: #409eff;
}

.session-meta {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #999;
}

.session-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  margin-left: 15px;
}

.session-content {
  color: #666;
  font-size: 13px;
  line-height: 1.6;
}

.session-date, .session-updated {
  margin-bottom: 5px;
}
</style>