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
            <div class="message-text">
              <!-- 用户消息显示纯文本 -->
              <span v-if="message.is_user">{{ message.content }}</span>
              <!-- AI 消息显示 Markdown -->
              <div v-else v-html="renderMarkdown(message.content)" class="markdown-content"></div>
            </div>
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
import { marked } from 'marked'
import 'highlight.js/styles/github.css'
import hljs from 'highlight.js'

// 配置 marked
marked.setOptions({
  highlight: function(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  },
  langPrefix: 'hljs language-',
  breaks: true,
  gfm: true
})

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

// 渲染 Markdown
const renderMarkdown = (content) => {
  try {
    return marked(content)
  } catch (error) {
    console.error('Markdown 渲染错误:', error)
    return content // 如果渲染失败，返回原文本
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.sidebar {
  width: 320px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-right: none;
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 20px rgba(0, 0, 0, 0.1);
  border-radius: 0 20px 20px 0;
  margin: 10px 0;
}

.session-header {
  padding: 25px 20px;
  border-bottom: 1px solid rgba(224, 224, 224, 0.3);
  background: linear-gradient(45deg, #667eea, #764ba2);
  border-radius: 0 20px 0 0;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 0;
}

.session-item {
  padding: 16px 20px;
  cursor: pointer;
  border-bottom: none;
  margin: 4px 12px;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.session-item:hover {
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
}

.session-item.active {
  background: linear-gradient(45deg, rgba(102, 126, 234, 0.15), rgba(118, 75, 162, 0.15));
  border-left: 4px solid #667eea;
  transform: translateX(4px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.2);
}

.session-title {
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
  line-height: 1.4;
}

.session-time {
  font-size: 11px;
  color: #718096;
  font-weight: 400;
}

.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  margin: 10px 10px 10px 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.chat-main.full-width {
  width: 100%;
  margin: 10px;
}

.chat-header {
  height: 70px;
  padding: 0 30px;
  background: linear-gradient(90deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
  border-bottom: 1px solid rgba(224, 224, 224, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  backdrop-filter: blur(10px);
}

.header-left h3 {
  margin: 0;
  color: #2d3748;
  font-weight: 700;
  font-size: 20px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  padding: 30px 25px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.8) 0%, rgba(250, 250, 250, 0.9) 100%);
}

.welcome-message {
  text-align: center;
  margin-top: 120px;
  color: #718096;
  animation: fadeInUp 0.8s ease-out;
}

.welcome-message h2 {
  margin-bottom: 15px;
  color: #2d3748;
  font-weight: 700;
  font-size: 28px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.welcome-message p {
  font-size: 16px;
  line-height: 1.6;
  max-width: 400px;
  margin: 0 auto;
}

.message {
  display: flex;
  margin-bottom: 24px;
  align-items: flex-start;
  animation: slideInMessage 0.4s ease-out;
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
  max-width: 75%;
  background: white;
  padding: 16px 20px;
  border-radius: 18px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  position: relative;
}

.message-content:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.user-message .message-content {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-message .message-content {
  background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
  border-bottom-left-radius: 4px;
}

.message-text {
  word-wrap: break-word;
  white-space: pre-wrap;
  font-size: 15px;
  line-height: 1.6;
}

.message-time {
  font-size: 11px;
  color: #a0aec0;
  margin-top: 6px;
  font-weight: 500;
}

.user-message .message-time {
  color: rgba(255, 255, 255, 0.8);
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
  padding: 25px 30px 30px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95) 0%, rgba(250, 250, 250, 0.98) 100%);
  border-top: 1px solid rgba(224, 224, 224, 0.3);
  backdrop-filter: blur(10px);
}

.input-wrapper {
  display: flex;
  gap: 15px;
  align-items: flex-end;
  background: white;
  border-radius: 16px;
  padding: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.input-wrapper:focus-within {
  border-color: #667eea;
  box-shadow: 0 6px 24px rgba(102, 126, 234, 0.15);
  transform: translateY(-2px);
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-hint {
  font-size: 12px;
  color: #718096;
  margin-top: 10px;
  text-align: center;
  font-weight: 500;
}

/* Markdown 样式 */
.markdown-content {
  line-height: 1.6;
}

.markdown-content h1,
.markdown-content h2,
.markdown-content h3,
.markdown-content h4,
.markdown-content h5,
.markdown-content h6 {
  margin-top: 1.5em;
  margin-bottom: 0.5em;
  font-weight: 600;
}

.markdown-content h1 { font-size: 1.8em; }
.markdown-content h2 { font-size: 1.6em; }
.markdown-content h3 { font-size: 1.4em; }
.markdown-content h4 { font-size: 1.2em; }
.markdown-content h5 { font-size: 1.1em; }
.markdown-content h6 { font-size: 1em; }

.markdown-content p {
  margin: 0.8em 0;
}

.markdown-content ul,
.markdown-content ol {
  margin: 0.8em 0;
  padding-left: 2em;
}

.markdown-content li {
  margin: 0.3em 0;
}

.markdown-content blockquote {
  border-left: 4px solid #ddd;
  margin: 1em 0;
  padding: 0.5em 1em;
  background-color: #f9f9f9;
  color: #666;
}

.markdown-content code {
  background-color: #f1f1f1;
  padding: 0.2em 0.4em;
  border-radius: 3px;
  font-family: 'Courier New', Courier, monospace;
  font-size: 0.9em;
}

.markdown-content pre {
  background-color: #f8f8f8;
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 1em;
  margin: 1em 0;
  overflow-x: auto;
}

.markdown-content pre code {
  background: none;
  padding: 0;
  border-radius: 0;
}

.markdown-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 1em 0;
}

.markdown-content th,
.markdown-content td {
  border: 1px solid #ddd;
  padding: 0.5em;
  text-align: left;
}

.markdown-content th {
  background-color: #f2f2f2;
  font-weight: 600;
}

.markdown-content a {
  color: #1890ff;
  text-decoration: none;
}

.markdown-content a:hover {
  text-decoration: underline;
}

.markdown-content hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 2em 0;
}

/* 代码高亮样式调整 */
.markdown-content .hljs {
  background: #f8f8f8 !important;
  color: #333 !important;
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideInMessage {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

/* 改进的打字动画 */
.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 12px 0;
}

.typing-indicator span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: linear-gradient(45deg, #667eea, #764ba2);
  animation: typingBounce 1.4s infinite ease-in-out;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
.typing-indicator span:nth-child(3) { animation-delay: 0s; }

@keyframes typingBounce {
  0%, 80%, 100% { 
    transform: scale(0.8); 
    opacity: 0.5;
  }
  40% { 
    transform: scale(1.2); 
    opacity: 1;
  }
}

/* 头像样式增强 */
.message-avatar .el-avatar {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border: 3px solid rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
}

.message-avatar .el-avatar:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
}

/* 按钮样式增强 */
.el-button {
  border-radius: 12px !important;
  font-weight: 600 !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.el-button--primary {
  background: linear-gradient(45deg, #667eea, #764ba2) !important;
  border: none !important;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
}

.el-button--primary:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
}

/* 输入框样式增强 */
.el-textarea__inner {
  border: none !important;
  border-radius: 12px !important;
  resize: none !important;
  font-size: 15px !important;
  line-height: 1.6 !important;
  background: transparent !important;
  box-shadow: none !important;
}

.el-textarea__inner:focus {
  box-shadow: none !important;
}

/* 下拉选择器样式 */
.el-select .el-input {
  border-radius: 12px !important;
}

.el-select .el-input__wrapper {
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
}

/* 滚动条样式 */
.messages-container::-webkit-scrollbar,
.session-list::-webkit-scrollbar {
  width: 6px;
}

.messages-container::-webkit-scrollbar-track,
.session-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb,
.session-list::-webkit-scrollbar-thumb {
  background: linear-gradient(45deg, #667eea, #764ba2);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover,
.session-list::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(45deg, #5a6fd8, #6a4c93);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .sidebar {
    width: 280px;
    position: absolute;
    left: -280px;
    z-index: 1000;
    transition: left 0.3s ease;
  }
  
  .sidebar.mobile-open {
    left: 0;
  }
  
  .chat-main {
    width: 100%;
    margin: 10px;
  }
  
  .message-content {
    max-width: 85%;
  }
}

@media (max-width: 480px) {
  .chat-header {
    padding: 0 15px;
  }
  
  .messages-container {
    padding: 20px 15px;
  }
  
  .input-container {
    padding: 20px 15px;
  }
  
  .message-content {
    max-width: 90%;
    padding: 12px 16px;
  }
}

/* 特殊效果 */
.session-header .el-button--primary {
  width: 100%;
  background: rgba(255, 255, 255, 0.2) !important;
  border: 2px solid rgba(255, 255, 255, 0.3) !important;
  color: white !important;
  backdrop-filter: blur(10px);
}

.session-header .el-button--primary:hover {
  background: rgba(255, 255, 255, 0.3) !important;
  border-color: rgba(255, 255, 255, 0.5) !important;
  transform: translateY(-2px) !important;
}

/* 消息气泡指示箭头效果 */
.user-message .message-content::after {
  content: '';
  position: absolute;
  right: -8px;
  bottom: 12px;
  width: 0;
  height: 0;
  border: 8px solid transparent;
  border-left: 8px solid #764ba2;
}

.ai-message .message-content::after {
  content: '';
  position: absolute;
  left: -8px;
  bottom: 12px;
  width: 0;
  height: 0;
  border: 8px solid transparent;
  border-right: 8px solid #edf2f7;
}
</style>