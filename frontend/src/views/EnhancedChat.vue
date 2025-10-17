<template>
  <div class="enhanced-chat-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="menu-toggle" @click="toggleSidebar">
          <el-icon><Menu /></el-icon>
        </button>
        <h2 v-if="!sidebarCollapsed" class="sidebar-title">AI 智能助手</h2>
        <el-button
          v-if="!sidebarCollapsed && userStore.isLoggedIn"
          type="text"
          @click="logout"
          class="logout-btn"
          title="退出登录"
        >
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </div>

      <el-button
        v-if="!sidebarCollapsed"
        type="primary"
        @click="startNewChat"
        class="new-chat-btn"
        icon="Plus"
      >
        开启新对话
      </el-button>

      <!-- 会话历史 -->
      <div v-if="!sidebarCollapsed && userStore.isLoggedIn" class="history">
        <h3>对话历史</h3>
        <div class="session-list">
          <div
            v-for="session in chatStore.sessions"
            :key="session.id"
            class="session-item"
            :class="{ active: currentSessionId === session.id }"
            @click="loadSession(session.id)"
          >
            <div class="session-content">
              <el-icon><ChatDotRound /></el-icon>
              <span class="session-title">{{ session.title || '新对话' }}</span>
            </div>
            <el-button
              type="text"
              size="small"
              @click.stop="deleteSession(session.id)"
              class="delete-btn"
              title="删除对话"
            >
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div v-if="sidebarCollapsed" class="collapsed-actions">
        <el-button
          type="primary"
          circle
          @click="startNewChat"
          title="新建对话"
          icon="Plus"
        />
      </div>
    </div>

    <!-- 主聊天区域 -->
    <div class="main-chat">
      <!-- 聊天头部 -->
      <div class="chat-header">
        <div class="header-left">
          <h3 v-if="chatStore.currentSession">
            {{ chatStore.currentSession.title || '新对话' }}
          </h3>
          <h3 v-else>AI 智能助手</h3>
        </div>

        <div class="header-right">
          <!-- 模型选择 -->
          <el-select
            v-model="selectedModel"
            placeholder="选择AI模型"
            size="small"
            style="width: 180px; margin-right: 10px;"
          >
            <el-option
              v-for="model in availableModels"
              :key="model.value"
              :label="model.label"
              :value="model.value"
            />
          </el-select>

          <!-- 深度思考开关 -->
          <el-switch
            v-model="deepThinking"
            active-text="深度思考"
            inactive-text="普通模式"
            size="small"
            style="margin-right: 15px;"
          />

          <!-- 用户菜单 -->
          <div class="user-actions" v-if="userStore.isLoggedIn">
            <el-dropdown @command="handleUserAction">
              <el-button type="text">
                {{ userStore.user?.username || '用户' }}
                <el-icon><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人资料</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <el-button
            v-else
            type="primary"
            size="small"
            @click="$router.push('/login')"
          >
            登录
          </el-button>
        </div>
      </div>

      <!-- 消息列表 -->
      <div class="messages-container" ref="messagesContainer">
        <div
          v-for="(message, index) in messages"
          :key="index"
          class="message-wrapper"
          :class="{ 'user-message': message.is_user, 'ai-message': !message.is_user }"
        >
          <div class="message-avatar">
            <el-avatar
              v-if="message.is_user"
              :size="32"
              :src="userStore.user?.avatar"
              icon="UserFilled"
            />
            <div v-else class="ai-avatar">
              <el-icon><Robot /></el-icon>
            </div>
          </div>

          <div class="message-content">
            <div class="message-header">
              <span class="sender-name">
                {{ message.is_user ? (userStore.user?.username || '我') : selectedModelLabel }}
              </span>
              <span class="message-time">
                {{ formatTime(message.timestamp) }}
              </span>
            </div>

            <!-- 用户消息 -->
            <div v-if="message.is_user" class="message-text user-text">
              {{ message.content }}
            </div>

            <!-- AI消息 -->
            <div v-else class="message-text ai-text">
              <!-- 深度思考过程 -->
              <div v-if="message.thinking" class="thinking-process">
                <el-collapse v-model="activeThinking">
                  <el-collapse-item title="🧠 深度思考过程" name="thinking">
                    <div class="thinking-content">{{ message.thinking }}</div>
                  </el-collapse-item>
                </el-collapse>
              </div>

              <!-- AI回复内容 -->
              <div v-html="renderMarkdown(message.content)" class="markdown-content"></div>

              <!-- 相关问题推荐 -->
              <div v-if="message.suggestions && message.suggestions.length" class="suggestions">
                <h4>💡 相关问题</h4>
                <el-tag
                  v-for="(suggestion, idx) in message.suggestions"
                  :key="idx"
                  @click="askSuggestion(suggestion)"
                  class="suggestion-tag"
                  type="info"
                  effect="plain"
                >
                  {{ suggestion }}
                </el-tag>
              </div>
            </div>
          </div>

          <!-- 消息操作 -->
          <div class="message-actions">
            <el-button
              type="text"
              size="small"
              @click="copyMessage(message.content)"
              title="复制"
            >
              <el-icon><CopyDocument /></el-icon>
            </el-button>
            <el-button
              v-if="!message.is_user"
              type="text"
              size="small"
              @click="regenerateResponse(index)"
              title="重新生成"
            >
              <el-icon><RefreshRight /></el-icon>
            </el-button>
          </div>
        </div>

        <!-- 正在输入指示器 -->
        <div v-if="isTyping" class="typing-indicator">
          <div class="message-wrapper ai-message">
            <div class="message-avatar">
              <div class="ai-avatar">
                <el-icon><Robot /></el-icon>
              </div>
            </div>
            <div class="message-content">
              <div class="typing-animation">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="input-area">
        <div class="input-wrapper">
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            placeholder="输入您的问题..."
            @keydown.ctrl.enter="sendMessage"
            @keydown.meta.enter="sendMessage"
            resize="none"
            maxlength="4000"
            show-word-limit
          />
          
          <div class="input-actions">
            <el-button
              type="primary"
              @click="sendMessage"
              :loading="isTyping"
              :disabled="!inputMessage.trim() || isTyping"
              icon="Position"
            >
              {{ isTyping ? '发送中...' : '发送' }}
            </el-button>
            
            <el-button
              v-if="isTyping"
              @click="stopGeneration"
              type="danger"
              plain
              size="small"
            >
              停止生成
            </el-button>
          </div>
        </div>
        
        <div class="input-tips">
          <span class="shortcut-tip">Ctrl + Enter 快速发送</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import { useUserStore } from '@/stores/user'
import { useChatStore } from '@/stores/chat'
import apiClient from '@/utils/api'

export default {
  name: 'EnhancedChat',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()
    const chatStore = useChatStore()

    // 响应式数据
    const sidebarCollapsed = ref(false)
    const inputMessage = ref('')
    const messages = ref([])
    const isTyping = ref(false)
    const currentSessionId = ref(null)
    const selectedModel = ref('deepseek')
    const deepThinking = ref(true)
    const activeThinking = ref([])
    const messagesContainer = ref(null)
    const eventSource = ref(null)

    // 可用模型
    const availableModels = ref([
      { value: 'deepseek', label: 'DeepSeek深度思考' },
      { value: 'doubao', label: '豆包' },
      { value: 'gpt5', label: 'GPT-5' },
      { value: '通义千问', label: '通义千问' },
      { value: 'Claude4', label: 'Claude 4' },
    ])

    // 计算属性
    const selectedModelLabel = computed(() => {
      return availableModels.value.find(m => m.value === selectedModel.value)?.label || selectedModel.value
    })

    // 方法
    const toggleSidebar = () => {
      sidebarCollapsed.value = !sidebarCollapsed.value
    }

    const startNewChat = async () => {
      if (userStore.isLoggedIn) {
        try {
          const response = await apiClient.post('/api/chat/sessions/', {
            title: '新对话'
          })
          currentSessionId.value = response.data.id
          messages.value = []
          await chatStore.loadSessions()
        } catch (error) {
          ElMessage.error('创建新会话失败')
        }
      } else {
        currentSessionId.value = null
        messages.value = []
      }
    }

    const loadSession = async (sessionId) => {
      try {
        currentSessionId.value = sessionId
        const response = await apiClient.get(`/api/chat/sessions/${sessionId}/history/`)
        messages.value = response.data.messages || []
        scrollToBottom()
      } catch (error) {
        ElMessage.error('加载会话失败')
      }
    }

    const deleteSession = async (sessionId) => {
      try {
        await ElMessageBox.confirm('确定删除这个对话吗？', '确认删除', {
          type: 'warning'
        })
        
        await apiClient.delete(`/api/chat/sessions/${sessionId}/`)
        await chatStore.loadSessions()
        
        if (currentSessionId.value === sessionId) {
          currentSessionId.value = null
          messages.value = []
        }
        
        ElMessage.success('删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const sendMessage = async () => {
      if (!inputMessage.value.trim() || isTyping.value) return

      const message = inputMessage.value.trim()
      inputMessage.value = ''

      // 添加用户消息
      const userMessage = {
        content: message,
        is_user: true,
        timestamp: new Date()
      }
      messages.value.push(userMessage)

      // 添加AI响应占位符
      const aiMessage = {
        content: '',
        is_user: false,
        timestamp: new Date(),
        thinking: '',
        suggestions: []
      }
      messages.value.push(aiMessage)

      scrollToBottom()
      isTyping.value = true

      try {
        // 调用流式API
        await streamChat(message, selectedModel.value, deepThinking.value, aiMessage)
      } catch (error) {
        console.error('发送消息失败:', error)
        aiMessage.content = '抱歉，发送消息时出现错误，请稍后重试。'
        ElMessage.error('发送消息失败')
      } finally {
        isTyping.value = false
      }
    }

    const streamChat = async (message, model, useDeepThinking, aiMessage) => {
      const requestData = {
        message: message,
        model: model,
        session_id: currentSessionId.value,
        deep_thinking: useDeepThinking
      }

      // 添加超时控制 - 根据模型类型设置不同的超时时间
      const controller = new AbortController()
      const getTimeoutForModel = (model, useDeepThinking) => {
        if (useDeepThinking && model === 'deepseek') return 300000 // 深度思考5分钟
        if (model === 'GPT-5') return 180000 // GPT-5 3分钟
        if (['豆包', 'Claude4'].includes(model)) return 120000 // 2分钟
        return 90000 // 默认90秒
      }
      
      const timeoutDuration = getTimeoutForModel(model, useDeepThinking)
      const timeoutId = setTimeout(() => {
        controller.abort()
        console.log(`请求超时: ${model} (${timeoutDuration/1000}秒)`)
      }, timeoutDuration)

      try {
        const response = await fetch('/api/chat/api/stream/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${userStore.token}`
          },
          body: JSON.stringify(requestData),
          signal: controller.signal
        })
        
        clearTimeout(timeoutId)

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) break

          const chunk = decoder.decode(value)
          const lines = chunk.split('\n')

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6)
              
              if (data === '[DONE]') {
                // 获取相关问题推荐
                try {
                  const suggestionsResponse = await apiClient.post('/api/chat/suggestions/', {
                    query: message
                  })
                  aiMessage.suggestions = suggestionsResponse.data.suggestions || []
                } catch (error) {
                  console.error('获取推荐问题失败:', error)
                }
                return
              }

              try {
                const parsed = JSON.parse(data)
                
                if (parsed.content) {
                  aiMessage.content += parsed.content
                }
                
                if (parsed.thinking) {
                  aiMessage.thinking += parsed.thinking
                }

                scrollToBottom()
              } catch (e) {
                console.error('解析流数据失败:', e)
              }
            }
          }
        }
      } catch (error) {
        clearTimeout(timeoutId)
        console.error('流式请求失败:', error)
        
        // 处理超时错误
        if (error.name === 'AbortError') {
          const timeoutMessage = `请求超时 (${timeoutDuration/1000}秒)。${useDeepThinking ? 'deepseek深度思考' : model}模型响应较慢，请稍后重试。`
          aiMessage.content = timeoutMessage
          ElMessage.error(timeoutMessage)
        } else {
          aiMessage.content = '发送消息失败，请重试'
          ElMessage.error('发送消息失败: ' + error.message)
        }
        throw error
      }
    }

    const stopGeneration = () => {
      if (eventSource.value) {
        eventSource.value.close()
        eventSource.value = null
      }
      isTyping.value = false
    }

    const askSuggestion = (suggestion) => {
      inputMessage.value = suggestion
      sendMessage()
    }

    const regenerateResponse = async (messageIndex) => {
      if (messageIndex <= 0 || isTyping.value) return

      const userMessage = messages.value[messageIndex - 1]
      if (!userMessage || userMessage.is_user !== true) return

      // 重置AI消息
      const aiMessage = messages.value[messageIndex]
      aiMessage.content = ''
      aiMessage.thinking = ''
      aiMessage.suggestions = []

      isTyping.value = true

      try {
        await streamChat(userMessage.content, selectedModel.value, deepThinking.value, aiMessage)
      } catch (error) {
        console.error('重新生成失败:', error)
        aiMessage.content = '重新生成失败，请稍后重试。'
        ElMessage.error('重新生成失败')
      } finally {
        isTyping.value = false
      }
    }

    const copyMessage = async (content) => {
      try {
        await navigator.clipboard.writeText(content)
        ElMessage.success('已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }

    const renderMarkdown = (content) => {
      return marked(content || '')
    }

    const formatTime = (timestamp) => {
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date

      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      
      return date.toLocaleDateString()
    }

    const scrollToBottom = () => {
      nextTick(() => {
        if (messagesContainer.value) {
          messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
        }
      })
    }

    const handleUserAction = (command) => {
      switch (command) {
        case 'profile':
          router.push('/profile')
          break
        case 'logout':
          logout()
          break
      }
    }

    const logout = async () => {
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '确认退出', {
          type: 'warning'
        })
        
        userStore.logout()
        currentSessionId.value = null
        messages.value = []
        ElMessage.success('已退出登录')
        router.push('/login')
      } catch (error) {
        // 用户取消
      }
    }

    // 生命周期
    onMounted(async () => {
      if (userStore.isLoggedIn) {
        await chatStore.loadSessions()
        await chatStore.loadAvailableModels()
      }
    })

    // 监听用户登录状态
    watch(() => userStore.isLoggedIn, async (isLoggedIn) => {
      if (isLoggedIn) {
        await chatStore.loadSessions()
      } else {
        currentSessionId.value = null
        messages.value = []
      }
    })

    return {
      // 数据
      sidebarCollapsed,
      inputMessage,
      messages,
      isTyping,
      currentSessionId,
      selectedModel,
      deepThinking,
      activeThinking,
      messagesContainer,
      availableModels,

      // 计算属性
      selectedModelLabel,

      // Stores
      userStore,
      chatStore,

      // 方法
      toggleSidebar,
      startNewChat,
      loadSession,
      deleteSession,
      sendMessage,
      stopGeneration,
      askSuggestion,
      regenerateResponse,
      copyMessage,
      renderMarkdown,
      formatTime,
      handleUserAction,
      logout
    }
  }
}
</script>

<style scoped>
.enhanced-chat-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* 侧边栏样式 */
.sidebar {
  width: 280px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 0 20px 20px 0;
  padding: 20px;
  transition: all 0.3s ease;
  overflow-y: auto;
}

.sidebar.collapsed {
  width: 70px;
  padding: 20px 15px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.menu-toggle {
  background: none;
  border: none;
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  transition: background 0.3s;
}

.menu-toggle:hover {
  background: rgba(0, 0, 0, 0.1);
}

.sidebar-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
  margin: 0;
}

.new-chat-btn {
  width: 100%;
  margin-bottom: 20px;
  border-radius: 12px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  border: none;
  color: white;
  font-weight: 500;
}

.history h3 {
  color: #2c3e50;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 15px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.session-list {
  max-height: 400px;
  overflow-y: auto;
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.5);
}

.session-item:hover {
  background: rgba(102, 126, 234, 0.1);
  transform: translateX(5px);
}

.session-item.active {
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
}

.session-content {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
}

.session-title {
  margin-left: 8px;
  font-size: 14px;
  truncate: ellipsis;
  overflow: hidden;
  white-space: nowrap;
}

.collapsed-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 主聊天区域 */
.main-chat {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px 0 0 20px;
  margin: 20px 20px 20px 0;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.8);
}

.header-left h3 {
  margin: 0;
  color: #2c3e50;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
}

/* 消息列表 */
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px 30px;
  background: rgba(248, 250, 252, 0.5);
}

.message-wrapper {
  display: flex;
  margin-bottom: 24px;
  align-items: flex-start;
}

.user-message {
  flex-direction: row-reverse;
}

.message-avatar {
  margin: 0 12px;
  flex-shrink: 0;
}

.ai-avatar {
  width: 32px;
  height: 32px;
  background: linear-gradient(45deg, #667eea, #764ba2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.message-content {
  flex: 1;
  max-width: 70%;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.sender-name {
  font-weight: 600;
  font-size: 14px;
  color: #2c3e50;
}

.message-time {
  font-size: 12px;
  color: #64748b;
}

.message-text {
  padding: 15px 20px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.6;
}

.user-text {
  background: linear-gradient(45deg, #667eea, #764ba2);
  color: white;
  border-bottom-right-radius: 6px;
}

.ai-text {
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-bottom-left-radius: 6px;
}

/* 深度思考样式 */
.thinking-process {
  margin-bottom: 15px;
}

.thinking-content {
  background: rgba(102, 126, 234, 0.05);
  padding: 15px;
  border-radius: 10px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* Markdown内容样式 */
.markdown-content {
  color: #2c3e50;
}

.markdown-content h1, .markdown-content h2, .markdown-content h3 {
  color: #1e293b;
  margin-top: 20px;
  margin-bottom: 10px;
}

.markdown-content code {
  background: rgba(102, 126, 234, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Consolas', monospace;
}

.markdown-content pre {
  background: #f8fafc;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
  border-left: 4px solid #667eea;
}

/* 相关问题推荐 */
.suggestions {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.suggestions h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #4b5563;
}

.suggestion-tag {
  margin: 4px 8px 4px 0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.suggestion-tag:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
}

/* 消息操作 */
.message-actions {
  display: flex;
  flex-direction: column;
  margin-left: 8px;
  opacity: 0;
  transition: opacity 0.3s;
}

.message-wrapper:hover .message-actions {
  opacity: 1;
}

/* 正在输入动画 */
.typing-indicator {
  margin-bottom: 20px;
}

.typing-animation {
  display: flex;
  align-items: center;
  padding: 15px 20px;
  background: white;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 18px;
  border-bottom-left-radius: 6px;
  width: fit-content;
}

.typing-animation span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  margin: 0 2px;
  animation: typing 1.4s infinite;
}

.typing-animation span:nth-child(1) { animation-delay: 0s; }
.typing-animation span:nth-child(2) { animation-delay: 0.2s; }
.typing-animation span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-10px); opacity: 1; }
}

/* 输入区域 */
.input-area {
  padding: 20px 30px;
  background: rgba(255, 255, 255, 0.8);
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.input-wrapper {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.input-wrapper .el-textarea {
  flex: 1;
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-tips {
  margin-top: 8px;
  text-align: center;
}

.shortcut-tip {
  font-size: 12px;
  color: #64748b;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .enhanced-chat-container {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: auto;
    border-radius: 0;
  }

  .main-chat {
    border-radius: 0;
    margin: 0;
  }

  .message-content {
    max-width: 85%;
  }

  .input-wrapper {
    flex-direction: column;
  }
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
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.messages-container::-webkit-scrollbar-thumb:hover,
.session-list::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
</style>