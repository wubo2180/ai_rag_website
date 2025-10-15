<template>
  <div class="chat-container">
    <!-- 左侧会话列表 -->
    <div class="sidebar" v-if="userStore.isLoggedIn">
      <div class="session-header">
        <el-button type="primary" @click="startNewChat" icon="Plus" size="small">
          新建对话
        </el-button>
      </div>
      
      <div class="session-list">
        <div 
          v-for="session in chatStore.sessions" 
          :key="session.id"
          class="session-item"
          :class="{ active: currentSessionId === session.id }"
          @click="loadSession(session.id)"
        >
          <div class="session-title">{{ session.title || '新对话' }}</div>
          <div class="session-time">{{ formatTime(session.updated_at) }}</div>
        </div>
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="chat-main" :class="{ 'full-width': !userStore.isLoggedIn }">
      <!-- 头部 -->
      <div class="chat-header">
        <div class="header-left">
          <h3 v-if="chatStore.currentSession">{{ chatStore.currentSession.title || '新对话' }}</h3>
          <h3 v-else>AI 智能助手</h3>
        </div>
        
        <div class="header-right">
          <el-select 
            v-model="chatStore.selectedModel" 
            placeholder="选择模型"
            size="small"
            style="width: 200px"
          >
            <el-option
              v-for="model in chatStore.availableModels"
              :key="model"
              :label="model"
              :value="model"
            />
          </el-select>
          
          <div class="user-actions" v-if="userStore.isLoggedIn">
            <el-dropdown @command="handleUserAction">
              <span class="el-dropdown-link">
                {{ userStore.username }}
                <el-icon><arrow-down /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item command="sessions">会话管理</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
          
          <div class="auth-buttons" v-else>
            <el-button size="small" @click="$router.push('/login')">登录</el-button>
            <el-button type="primary" size="small" @click="$router.push('/register')">注册</el-button>
          </div>
        </div>
      </div>

      <!-- 消息区域 -->
      <div class="messages-container" ref="messagesContainer">
        <div v-if="chatStore.messages.length === 0" class="welcome-message">
          <h2>欢迎使用 AI 智能助手</h2>
          <p>您可以向我提问任何问题，我会尽力为您解答。</p>
        </div>
        
        <div 
          v-for="message in chatStore.messages" 
          :key="message.id"
          class="message"
          :class="{ 'user-message': message.is_user, 'ai-message': !message.is_user }"
        >
          <div class="message-avatar">
            <el-avatar v-if="message.is_user" :icon="UserFilled" />
            <el-avatar v-else style="background-color: #409eff;">AI</el-avatar>
          </div>
          
          <div class="message-content">
            <div class="message-text">{{ message.content }}</div>
            <div class="message-time">{{ formatTime(message.created_at) }}</div>
          </div>
        </div>
        
        <!-- 加载中消息 -->
        <div v-if="chatStore.isLoading" class="message ai-message">
          <div class="message-avatar">
            <el-avatar style="background-color: #409eff;">AI</el-avatar>
          </div>
          <div class="message-content">
            <div class="typing-indicator">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-container">
        <div class="input-wrapper">
          <el-input
            v-model="messageInput"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            :disabled="chatStore.isLoading"
            @keydown.enter.ctrl="sendMessage"
            @keydown.enter.exact.prevent="sendMessage"
          />
          <el-button 
            type="primary" 
            @click="sendMessage"
            :loading="chatStore.isLoading"
            :disabled="!messageInput.trim()"
          >
            发送
          </el-button>
        </div>
        <div class="input-hint">
          按 Enter 发送，Ctrl + Enter 换行
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UserFilled, ArrowDown, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'

const router = useRouter()
const userStore = useUserStore()
const chatStore = useChatStore()

const messageInput = ref('')
const messagesContainer = ref()
const currentSessionId = ref(null)

// 计算属性
const isLoggedIn = computed(() => userStore.isLoggedIn)

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
  } else {
    return date.toLocaleDateString()
  }
}

// 发送消息
const sendMessage = async () => {
  if (!messageInput.value.trim()) return

  const message = messageInput.value.trim()
  messageInput.value = ''

  const result = await chatStore.sendMessage(
    message, 
    currentSessionId.value,
    chatStore.selectedModel
  )

  if (result.success) {
    // 如果是新会话，更新会话ID
    if (result.sessionId && !currentSessionId.value) {
      currentSessionId.value = result.sessionId
      // 刷新会话列表
      if (userStore.isLoggedIn) {
        chatStore.fetchSessions()
      }
    }
    
    // 滚动到底部
    scrollToBottom()
  } else {
    ElMessage.error(result.error)
  }
}

// 滚动到底部
const scrollToBottom = () => {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// 开始新聊天
const startNewChat = () => {
  currentSessionId.value = null
  chatStore.clearCurrentSession()
}

// 加载会话
const loadSession = async (sessionId) => {
  currentSessionId.value = sessionId
  const result = await chatStore.fetchSessionHistory(sessionId)
  if (result.success) {
    scrollToBottom()
  } else {
    ElMessage.error(result.error)
  }
}

// 处理用户操作
const handleUserAction = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'sessions':
      router.push('/sessions')
      break
    case 'logout':
      userStore.logout()
      ElMessage.success('已退出登录')
      // 清空当前会话但保持在聊天页面
      startNewChat()
      chatStore.sessions = []
      break
  }
}

// 初始化
onMounted(async () => {
  // 获取可用模型
  await chatStore.fetchAvailableModels()
  
  // 如果用户已登录，获取会话列表
  if (userStore.isLoggedIn) {
    await chatStore.fetchSessions()
  }
  
  // 初始化用户认证状态
  userStore.initAuth()
})
</script>

<style scoped>
.chat-container {
  display: flex;
  height: 100vh;
  background: #f5f5f5;
}

.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #e0e0e0;
  display: flex;
  flex-direction: column;
}

.session-header {
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.session-item {
  padding: 15px 20px;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.3s;
}

.session-item:hover {
  background-color: #f5f5f5;
}

.session-item.active {
  background-color: #e6f7ff;
  border-right: 3px solid #1890ff;
}

.session-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 5px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.session-time {
  font-size: 12px;
  color: #999;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.chat-main.full-width {
  width: 100%;
}

.chat-header {
  height: 60px;
  padding: 0 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left h3 {
  margin: 0;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-actions .el-dropdown-link {
  cursor: pointer;
  color: #409eff;
  display: flex;
  align-items: center;
  gap: 5px;
}

.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-message {
  text-align: center;
  margin-top: 100px;
  color: #666;
}

.welcome-message h2 {
  margin-bottom: 10px;
  color: #333;
}

.message {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.user-message .message-content {
  margin-right: 10px;
  margin-left: 0;
}

.ai-message .message-content {
  margin-left: 10px;
}

.message-content {
  max-width: 70%;
  background: white;
  padding: 12px 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-message .message-content {
  background: #1890ff;
  color: white;
}

.message-text {
  word-wrap: break-word;
  white-space: pre-wrap;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.7);
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #ccc;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-container {
  padding: 20px;
  background: white;
  border-top: 1px solid #e0e0e0;
}

.input-wrapper {
  display: flex;
  gap: 10px;
  align-items: flex-end;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-hint {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
  text-align: center;
}
</style>