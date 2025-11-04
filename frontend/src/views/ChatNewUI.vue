<!--  -->
<template>
  <div id="chat-container" :class="['theme-' + themeMode]">
    <div class="cursor-trail" ref="cursorTrail" aria-hidden="true"></div>
    <!-- Sidebar -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <button class="menu-toggle" @click="toggleSidebar">
          <span class="hamburger-icon">
            <span></span>
            <span></span>
            <span></span>
          </span>
        </button>
        <h2 v-if="!sidebarCollapsed" class="sidebar-title">iBox Materix</h2>
        <button
          v-if="!sidebarCollapsed"
          class="logout-btn"
          @click="logout"
          title="退出登录"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
      <button
        v-if="!sidebarCollapsed"
        class="new-chat-btn"
        @click="startNewChat"
      >
        <span class="btn-icon">+</span>
        开启新对话
      </button>
      <div v-if="!sidebarCollapsed" class="history">
        <h3>对话历史</h3>
        <div
          class="history-group"
          v-for="(group, gIndex) in groupedHistory"
          :key="gIndex"
        >
          <div class="group-title">{{ group.label }}</div>
          <ul>
            <li
              v-for="(chat, i) in group.items"
              :key="i"
              :class="{ active: currentChatIndex === chat.index }"
              class="chat-item"
            >
              <div class="chat-content" @click="loadChat(chat.index)">
                <span class="chat-icon">💬</span>
                <span class="chat-title">{{
                  chat.title || `对话 ${chatHistory.length - chat.index}`
                }}</span>
              </div>
              <button
                class="delete-btn"
                @click.stop="deleteChat(chat.index)"
                title="删除对话"
              >
                🗑️
              </button>
            </li>
          </ul>
        </div>
      </div>
      <div v-if="sidebarCollapsed" class="collapsed-actions">
        <button
          class="collapsed-new-chat"
          @click="startNewChat"
          title="新建对话"
        >
          <span>+</span>
        </button>
      </div>
    </div>

    <!-- Main Chat -->
    <div class="main-chat">
      <div class="chat-header">
        <div class="user-info">
          <span class="user-avatar">👤</span>
          <span class="user-name">{{ currentUser.username }}</span>
        </div>
        <div class="theme-switcher">
          <button
            class="theme-btn"
            @click="toggleTheme"
            :title="themeMode === 'dark' ? '切换到亮色' : '切换到暗色'"
          >
            <span v-if="themeMode === 'dark'">🌞</span>
            <span v-else>🌙</span>
            <span class="theme-text">{{
              themeMode === 'dark' ? '亮色' : '暗色'
            }}</span>
          </button>
        </div>
      </div>

      <template v-if="chatSessionActive">
        <div class="messages-container" ref="messagesContainer">
          <div v-if="messages.length === 0" class="welcome-message">
            <span class="hello-emoji">👋</span>
            <p>您好 {{ currentUser.username }}，想和我聊点什么？</p>
          </div>
          <div
            v-for="(msg, index) in messages"
            :key="index"
            class="message"
            :class="msg.sender"
          >
            <div
              class="bubble"
              :class="[
                { 'glow-frame': msg.sender === 'ai' },
                {
                  revealing:
                    msg.sender === 'ai' && index === messages.length - 1,
                },
              ]"
            >
              <!-- ================================================================= -->
              <!-- ======================= 核心修改区域 开始 ======================= -->
              <!-- ================================================================= -->

              <!-- 当消息发送者是 'user' 时，仍然使用 p 标签显示纯文本 -->
              <p v-if="msg.sender === 'user'">{{ msg.text }}</p>

              <!-- 当消息发送者是 'ai' 时，使用 v-html 和 marked.parse() 来渲染Markdown -->
              <div
                v-else-if="msg.sender === 'ai' && msg.text"
                class="ai-message-content"
                v-html="marked.parse(msg.text)"
              ></div>

              <!-- 显示“正在思考中...”的逻辑 -->
              <p
                v-else-if="
                  isLoading &&
                  msg.sender === 'ai' &&
                  index === messages.length - 1
                "
              >
                正在思考中...
              </p>

              <!-- ================================================================= -->
              <!-- ======================== 核心修改区域 结束 ======================= -->
              <!-- ================================================================= -->

              <div
                v-if="
                  msg.sender === 'ai' &&
                  (msg.text || !isLoading || index !== messages.length - 1)
                "
                class="message-actions"
              >
                <button
                  class="action-btn copy-btn"
                  @click="copyMessage(msg.text)"
                  title="复制"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <rect
                      x="9"
                      y="9"
                      width="13"
                      height="13"
                      rx="2"
                      ry="2"
                    ></rect>
                    <path
                      d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"
                    ></path>
                  </svg>
                </button>
                <button
                  class="action-btn like-btn"
                  @click="likeMessage"
                  title="赞"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"
                    ></path>
                  </svg>
                </button>
                <button
                  class="action-btn dislike-btn"
                  @click="dislikeMessage"
                  title="踩"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <path
                      d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"
                    ></path>
                  </svg>
                </button>
                <button
                  class="action-btn refresh-btn"
                  @click="refreshMessage(index)"
                  title="重新生成"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <polyline points="1 20 1 14 7 14"></polyline>
                    <path
                      d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"
                    ></path>
                  </svg>
                </button>
                <button
                  class="action-btn more-btn"
                  @click="showMoreOptions"
                  title="更多"
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                  >
                    <circle cx="12" cy="12" r="1"></circle>
                    <circle cx="19" cy="12" r="1"></circle>
                    <circle cx="5" cy="12" r="1"></circle>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          <!-- Related Questions - 显示在最后一条AI消息后 -->
          <transition name="fade-related">
            <div
              v-if="
                messages.length > 0 &&
                messages[messages.length - 1].sender === 'ai' &&
                relatedQuestions.length > 0
              "
              class="related-questions"
            >
              <div class="related-questions-title">💡 相关问题推荐：</div>
              <div class="related-questions-list">
                <div
                  v-for="(question, index) in relatedQuestions"
                  :key="index"
                  class="related-question-item glow-frame"
                  @click="askRelatedQuestion(question)"
                >
                  <span class="question-text">{{ question }}</span>
                </div>
              </div>
            </div>
          </transition>

          <!-- 滚动到底部按钮 -->
          <div
            v-if="!isAtBottom && messages.length > 0"
            class="scroll-to-bottom-btn"
            @click="scrollToBottomManually"
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="7 13 12 18 17 13"></polyline>
              <polyline points="7 6 12 11 17 6"></polyline>
            </svg>
          </div>
        </div>

        <!-- Chat Input Area -->
        <div class="chat-input-area">
          <!-- Suggestions List -->
          <div v-if="suggestions.length > 0" class="suggestions-list">
            <ul>
              <li
                v-for="(suggestion, index) in suggestions"
                :key="index"
                :class="{ selected: index === selectedIndex }"
                @mousedown.prevent="selectSuggestion(suggestion)"
              >
                <span v-html="highlightQuery(suggestion)"></span>
              </li>
            </ul>
          </div>
          <!-- Input Wrapper -->
          <div class="input-wrapper">
            <div class="textarea-container">
              <textarea
                ref="messageTextarea"
                v-model="newMessage"
                @keydown="handleKeydown"
                @input="handleInput"
                @focus="fetchSuggestions"
                @blur="clearSuggestions"
                :placeholder="isLoading ? 'AI正在思考中...' : '询问AI任何问题'"
                rows="2"
                :disabled="isLoading"
              ></textarea>
            </div>
            <button @click="sendMessage" class="send-btn" :disabled="isLoading">
              ↑
            </button>
          </div>
          <!-- Button Layer -->
          <div class="button-layer">
            <div class="database-selector" :class="{ open: dropdownOpen }">
              <button
                class="db-selector-btn"
                @click="toggleDropdown"
                :disabled="isLoading"
              >
                <span class="db-text">{{
                  getCurrentDatabaseOption().label
                }}</span>
                <span class="dropdown-arrow">▼</span>
              </button>
              <div v-if="dropdownOpen" class="dropdown-menu">
                <div
                  v-for="option in databaseOptions"
                  :key="option.value"
                  @click="selectDatabase(option.value)"
                  :class="[
                    'dropdown-item',
                    { active: selectedDatabase === option.value },
                  ]"
                >
                  <span class="db-label">{{ option.label }}</span>
                </div>
              </div>
            </div>

            <!-- 深度思考按钮 -->
            <button
              class="deep-thinking-btn"
              :class="{ active: deepThinkingEnabled }"
              @click="toggleDeepThinking"
              title="深度思考"
              :disabled="isLoading"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M9 12l2 2 4-4"></path>
                <path
                  d="M21 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"
                ></path>
                <path
                  d="M3 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"
                ></path>
                <path
                  d="M12 21c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"
                ></path>
                <path
                  d="M12 3c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"
                ></path>
              </svg>
              <span class="btn-text">深度搜索</span>
            </button>

            <!-- 模型选择按钮 -->
            <div class="model-selector" :class="{ open: modelDropdownOpen }">
              <button class="model-selector-btn" disabled>
                <span class="model-text">DeepSeek</span>
              </button>
            </div>
          </div>
        </div>
      </template>
      <div v-else class="initial-screen">
        <div class="welcome-message">
          <span class="hello-emoji">👋</span>
          <h2>欢迎, {{ currentUser.username }}!</h2>
          <p>点击“开启新对话”开始聊天</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, nextTick, onMounted, onUnmounted, watch, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import axios from 'axios'
  import { marked } from 'marked'
  import 'katex/dist/katex.min.css'
  import { ElMessage } from 'element-plus'
  import {
    UserFilled,
    ArrowDown,
    Plus,
    Menu,
    Close,
  } from '@element-plus/icons-vue'
  import { useUserStore } from '@/stores/user'
  import { useChatStore } from '@/stores/chat'

  import 'highlight.js/styles/github.css'
  import hljs from 'highlight.js'

  const router = useRouter()

  // 获取当前用户信息
  const currentUser = ref({})

  // Refs for UI elements and state
  const newMessage = ref('')
  const messages = ref([])
  const chatHistory = ref([])
  const isLoading = ref(false)
  const messagesContainer = ref(null)
  const messageTextarea = ref(null)
  const currentChatIndex = ref(-1)
  const currentChatTitle = ref('')
  const sidebarCollapsed = ref(false)
  const chatSessionActive = ref(false) // 控制聊天会话是否激活

  const chatStore = useChatStore()

  // 组合C：强赛博动效 — 光标能量尾焰
  const cursorTrail = ref(null)
  let trailRAF = null
  let lastX = 0,
    lastY = 0,
    vx = 0,
    vy = 0
  const handleMouseMove = (e) => {
    const el = cursorTrail.value
    if (!el) return
    const x = e.clientX,
      y = e.clientY
    vx = x - lastX
    vy = y - lastY
    lastX = x
    lastY = y
    // 速度映射到发光强度与缩放
    const speed = Math.min(Math.hypot(vx, vy) / 24, 1)
    el.style.setProperty('--trail-x', x + 'px')
    el.style.setProperty('--trail-y', y + 'px')
    el.style.setProperty('--trail-alpha', (0.1 + speed * 0.18).toFixed(3))
    el.style.setProperty('--trail-scale', (0.65 + speed * 0.35).toFixed(3))
    if (!trailRAF)
      trailRAF = requestAnimationFrame(() => {
        trailRAF = null
      })
  }

  onMounted(() => {
    window.addEventListener('mousemove', handleMouseMove, { passive: true })
  })
  onUnmounted(() => {
    window.removeEventListener('mousemove', handleMouseMove)
    if (trailRAF) cancelAnimationFrame(trailRAF)
  })

  // 主题切换（暗黑/亮色）
  const themeMode = ref('dark')
  const applyStoredTheme = () => {
    const stored = localStorage.getItem('ai-theme-mode')
    if (stored === 'light' || stored === 'dark') themeMode.value = stored
  }
  const toggleTheme = () => {
    themeMode.value = themeMode.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem('ai-theme-mode', themeMode.value)
  }

  watch(messagesContainer, (newContainer, oldContainer) => {
    if (oldContainer) {
      oldContainer.removeEventListener('scroll', handleScroll)
    }
    if (newContainer) {
      newContainer.addEventListener('scroll', handleScroll)
    }
  })

  // 新增：对话状态管理
  const currentChatId = ref(null) // 当前对话的唯一ID
  const isNewChat = ref(true) // 标识当前是否为新对话

  // --- LocalStorage Functions ---
  const getUserStorageKey = () => {
    const user = JSON.parse(localStorage.getItem('ai-chat-user') || '{}')
    return `ai-chat-history-${user.username || 'anonymous'}`
  }

  const loadFromStorage = () => {
    try {
      const storageKey = getUserStorageKey()
      const stored = localStorage.getItem(storageKey)
      if (stored) {
        const data = JSON.parse(stored)
        chatHistory.value = data.chatHistory || []
      }
      // On initial load, don't load any active chat.
      messages.value = []
      currentChatIndex.value = -1
      currentChatTitle.value = ''
      currentChatId.value = null
      isNewChat.value = true
      relatedQuestions.value = []
      chatSessionActive.value = false
    } catch (error) {
      console.error('加载本地存储失败:', error)
    }
  }

  const saveToStorage = () => {
    try {
      const storageKey = getUserStorageKey()
      const data = {
        chatHistory: chatHistory.value,
        currentMessages: messages.value,
        currentChatIndex: currentChatIndex.value,
        currentChatTitle: currentChatTitle.value,
        currentChatId: currentChatId.value,
        isNewChat: isNewChat.value,
        currentRelatedQuestions: relatedQuestions.value,
      }
      localStorage.setItem(storageKey, JSON.stringify(data))
    } catch (error) {
      console.error('保存到本地存储失败:', error)
    }
  }

  // Database selector state
  const selectedDatabase = ref('all')
  const dropdownOpen = ref(false)
  const databaseOptions = ref([
    { value: 'external', label: '外部数据库' },
    { value: 'internal', label: '内部数据库' },
    { value: 'all', label: '全部' },
  ])

  // Deep thinking state
  const deepThinkingEnabled = ref(true)

  // Model selector state
  const selectedModel = ref('deepseek')
  const modelDropdownOpen = ref(false)
  const modelOptions = ref([{ value: 'deepseek', label: 'DeepSeek' }])

  // Suggestions state
  const suggestions = ref([])
  const debounceTimer = ref(null)
  const selectedIndex = ref(-1)
  const relatedQuestions = ref([])

  // 滚动状态
  const isAtBottom = ref(true)

  // --- Auth Functions ---
  const logout = () => {
    if (confirm('确定要退出登录吗？')) {
      // 保存当前用户的对话记录
      saveToStorage()
      // 只移除用户登录信息，保留对话历史
      localStorage.removeItem('ai-chat-user')
      router.push('/login')
    }
  }

  // --- Core Functions ---

  // 计算相对日期标签（今天、1天前、2天前...）
  const getRelativeDayLabel = (iso) => {
    if (!iso) return '今天'
    const target = new Date(iso)
    const now = new Date()
    const startOfDay = (d) =>
      new Date(d.getFullYear(), d.getMonth(), d.getDate())
    const diffMs = startOfDay(now) - startOfDay(target)
    const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
    return days <= 0 ? '今天' : `${days}天前`
  }

  // 计算天数差（用于分组排序）
  const getDayDiff = (iso) => {
    if (!iso) return 0
    const target = new Date(iso)
    const now = new Date()
    const startOfDay = (d) =>
      new Date(d.getFullYear(), d.getMonth(), d.getDate())
    const diffMs = startOfDay(now) - startOfDay(target)
    return Math.floor(diffMs / (1000 * 60 * 60 * 24))
  }

  // 将历史按天分组：今天、1天前、2天前...
  const groupedHistory = computed(() => {
    const groupsMap = new Map()
    chatHistory.value.forEach((chat, idx) => {
      const label = getRelativeDayLabel(chat.timestamp)
      const key = label || '今天'
      if (!groupsMap.has(key)) groupsMap.set(key, [])
      groupsMap.get(key).push({ ...chat, index: idx })
    })
    const entries = Array.from(groupsMap.entries()).map(([label, items]) => ({
      label,
      days: getDayDiff(items[0]?.timestamp),
      items,
    }))
    entries.sort((a, b) => a.days - b.days)
    return entries
  })

  // 动态更新时间标签/分组：每小时刷新一次（足够反映天数推进）
  setInterval(() => {
    chatHistory.value = [...chatHistory.value]
  }, 60 * 60 * 1000)

  // 智能滚动：只有当用户在底部时才自动滚动
  const scrollToBottom = (force = false) => {
    nextTick(() => {
      if (messagesContainer.value) {
        const container = messagesContainer.value
        const isAtBottom =
          container.scrollTop + container.clientHeight >=
          container.scrollHeight - 50

        // 强制滚动或用户在底部时才滚动
        if (force || isAtBottom) {
          container.scrollTop = container.scrollHeight
        }
      }
    })
  }

  // 检查用户是否在底部
  const isUserAtBottom = () => {
    if (!messagesContainer.value) return true
    const container = messagesContainer.value
    return (
      container.scrollTop + container.clientHeight >=
      container.scrollHeight - 50
    )
  }

  // 监听滚动事件，更新按钮显示状态
  const handleScroll = () => {
    isAtBottom.value = isUserAtBottom()
  }

  // 手动滚动到底部
  const scrollToBottomManually = () => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
    isAtBottom.value = true
  }

  const sendMessage = async () => {
    if (newMessage.value.trim() === '') return

    // 确保聊天会话界面处于激活状态
    chatSessionActive.value = true

    const userMessage = { text: newMessage.value, sender: 'user' }
    const messageToSend = newMessage.value

    // 如果是新对话的第一条消息，设置标题并立即保存到历史记录
    if (isNewChat.value && messages.value.length === 0) {
      currentChatTitle.value =
        messageToSend.length > 20
          ? messageToSend.substring(0, 20) + '...'
          : messageToSend
      // conversation_id 将由后端在第一次响应时生成和返回
    }

    messages.value.push(userMessage)

    // 如果这是新对话的第一条消息，立即保存到历史记录
    if (isNewChat.value && messages.value.length === 1) {
      saveCurrentChat()
    }

    newMessage.value = ''
    suggestions.value = [] // Clear suggestions on send
    relatedQuestions.value = [] // Clear previous related questions
    isLoading.value = true
    nextTick(adjustTextareaHeight)
    scrollToBottom(true)

    // 添加一个空的AI消息用于流式更新
    const aiMessageIndex = messages.value.length
    messages.value.push({ text: '', sender: 'ai' })

    try {
      // 使用 Pinia store 的发送方法（非流式），不要当作 fetch Response 使用
      const result = await chatStore.sendMessage(
        messageToSend,
        currentChatId.value || null,
        null // 让 store 使用其内部的 selectedModel
      )

      if (result?.success) {
        // 优先使用返回的 ai_message 文本；兼容不同字段名
        const aiText =
          result.data?.ai_message?.text ||
          result.data?.ai_message?.content ||
          result.data?.reply ||
          ''
        messages.value[aiMessageIndex].text = aiText

        // 更新当前会话 ID（若后端返回）
        if (result.sessionId) {
          currentChatId.value = result.sessionId
        } else if (result.data?.session_id) {
          currentChatId.value = result.data.session_id
        }

        // relatedQuestions 暂时置空，后续可接入专用接口
        relatedQuestions.value = []
        scrollToBottom(true)
      } else {
        messages.value[aiMessageIndex].text =
          result?.error || '抱歉，我暂时无法回复。'
      }
    } catch (error) {
      console.error('Error sending message:', error)
      messages.value[aiMessageIndex].text =
        '抱歉，我暂时无法回复。请检查网络连接或稍后重试。'
    } finally {
      isLoading.value = false
      saveCurrentChat()
      scrollToBottom()
    }
  }

  // --- Sidebar and Chat History ---

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const saveCurrentChat = () => {
    // 只有当有消息内容时才保存
    if (messages.value.length === 0) return

    const chatData = {
      id: currentChatId.value || Date.now(), // 使用现有ID或生成新ID
      messages: [...messages.value],
      title:
        currentChatTitle.value ||
        messages.value[0]?.text.substring(0, 20) + '...' ||
        '新对话',
      relatedQuestions: [...relatedQuestions.value],
      timestamp: new Date().toISOString(),
      conversation_id: currentChatId.value, // 保存当前的 conversation_id
    }

    if (isNewChat.value) {
      // 新对话：添加到历史记录开头
      chatHistory.value.unshift(chatData)
      currentChatIndex.value = 0
      isNewChat.value = false // 标记为已保存的对话
    } else {
      // 已存在的对话：更新对应位置的记录
      if (
        currentChatIndex.value >= 0 &&
        currentChatIndex.value < chatHistory.value.length
      ) {
        chatHistory.value[currentChatIndex.value] = chatData
      }
    }

    saveToStorage()
  }

  const startNewChat = () => {
    chatSessionActive.value = true
    // 如果当前有对话内容，保存它
    if (messages.value.length > 0) {
      saveCurrentChat()
    }

    // 重置为新对话状态
    messages.value = []
    currentChatIndex.value = -1
    currentChatTitle.value = ''
    currentChatId.value = null
    isNewChat.value = true // 标记为新对话
    relatedQuestions.value = []

    saveToStorage()
  }

  const loadChat = (index) => {
    chatSessionActive.value = true
    // 如果当前有对话内容且是新对话，先保存
    if (messages.value.length > 0 && isNewChat.value) {
      saveCurrentChat()
    }

    // 加载指定的历史对话
    const chatData = chatHistory.value[index]
    messages.value = [...chatData.messages]
    currentChatTitle.value = chatData.title
    currentChatIndex.value = index
    currentChatId.value = chatData.conversation_id || null // 恢复 conversation_id
    isNewChat.value = false // 标记为已存在的对话
    relatedQuestions.value = [...(chatData.relatedQuestions || [])]

    saveToStorage()
    scrollToBottom(true)
  }

  const deleteChat = (index) => {
    // 删除指定的对话记录
    chatHistory.value.splice(index, 1)

    // 如果删除的是当前对话
    if (currentChatIndex.value === index) {
      // 清空当前对话并返回初始页（点击“开启新对话”提示）
      messages.value = []
      currentChatTitle.value = ''
      currentChatIndex.value = -1
      relatedQuestions.value = []
      currentChatId.value = null
      isNewChat.value = true
      chatSessionActive.value = false // 关键：切回初始页面
    } else if (currentChatIndex.value > index) {
      // 如果当前对话索引大于删除的索引，需要调整索引
      currentChatIndex.value--
    }

    // 保存到localStorage
    saveToStorage()
  }

  const copyMessage = async (text) => {
    try {
      await navigator.clipboard.writeText(text)
      showCopyToast('已复制到剪贴板')
    } catch (err) {
      // 如果现代API不可用，使用传统方法
      const textArea = document.createElement('textarea')
      textArea.value = text
      document.body.appendChild(textArea)
      textArea.select()
      try {
        document.execCommand('copy')
        showCopyToast('已复制到剪贴板')
      } catch (fallbackErr) {
        console.error('复制失败:', fallbackErr)
        showCopyToast('复制失败，请重试')
      }
      document.body.removeChild(textArea)
    }
  }

  // 显示复制提示
  const showCopyToast = (message) => {
    // 移除已存在的提示
    const existingToast = document.querySelector('.copy-toast')
    if (existingToast) {
      existingToast.remove()
    }

    // 创建新的提示元素
    const toast = document.createElement('div')
    toast.className = 'copy-toast'
    toast.textContent = message
    toast.style.cssText = `
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 14px;
    z-index: 10000;
    animation: fadeInOut 2s ease-in-out;
  `

    // 添加CSS动画
    if (!document.querySelector('#copy-toast-style')) {
      const style = document.createElement('style')
      style.id = 'copy-toast-style'
      style.textContent = `
      @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
      }
    `
      document.head.appendChild(style)
    }

    document.body.appendChild(toast)

    // 2秒后自动移除
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast)
      }
    }, 2000)
  }

  const likeMessage = () => {
    console.log('点赞消息')
    // 这里可以添加点赞逻辑
  }

  const dislikeMessage = () => {
    console.log('踩消息')
    // 这里可以添加踩的逻辑
  }

  const refreshMessage = async (aiIndex) => {
    try {
      const aiMsg = messages.value[aiIndex]
      const userMsg = messages.value[aiIndex - 1]
      if (
        !aiMsg ||
        aiMsg.sender !== 'ai' ||
        !userMsg ||
        userMsg.sender !== 'user'
      ) {
        console.warn('无法重新生成：索引不合法或缺少前一条用户消息')
        return
      }
      const messageToSend = userMsg.text || ''
      if (!messageToSend.trim()) return

      // 状态与准备
      isLoading.value = true
      relatedQuestions.value = [] // 清空旧的相关问题
      nextTick(adjustTextareaHeight)
      scrollToBottom(true)

      // 并行启动相关问题获取（完成后再显示）
      const relatedQuestionsPromise = (async () => {
        try {
          const res = await fetch(
            'http://127.0.0.1:5000/api/related-questions',
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ message: messageToSend }),
            }
          )
          if (res.ok) {
            const data = await res.json()
            return data.related_questions || []
          }
        } catch (err) {
          console.warn('获取相关问题失败（regenerate）:', err)
        }
        return []
      })()

      // 重新生成：调用相同的聊天接口，使用现有的 conversation_id 保持上下文
      const response = await fetch('http://127.0.0.1:5000/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageToSend,
          database: selectedDatabase.value,
          model: selectedModel.value,
          deep_thinking: deepThinkingEnabled.value,
          conversation_id: currentChatId.value,
        }),
      })

      if (!response.ok || !response.body) {
        throw new Error('Regenerate 请求失败')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let aiResponse = ''

      // 清空当前 AI 文本，开始流式写入新内容
      messages.value[aiIndex].text = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break
        const chunk = decoder.decode(value, { stream: true })
        const lines = chunk.split('\n')
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const data = line.slice(6)
          if (data === '[DONE]') break
          try {
            const parsed = JSON.parse(data)
            if (parsed.content) {
              aiResponse += parsed.content
              messages.value[aiIndex].text = aiResponse.replace(
                '</think>',
                '</think>\n\n'
              )
              scrollToBottom()
            }
            if (parsed.conversation_id) {
              currentChatId.value = parsed.conversation_id
            }
          } catch (e) {
            aiResponse += data
            messages.value[aiIndex].text = aiResponse.replace(
              '</think>',
              '</think>\n\n'
            )
            scrollToBottom()
          }
        }
      }

      // 完成后再显示相关问题
      const qs = await relatedQuestionsPromise
      relatedQuestions.value = qs
      scrollToBottom(true)
    } catch (error) {
      console.error('重新生成失败:', error)
      // 显示错误提示到该 AI 消息位置
      if (typeof aiIndex === 'number' && messages.value[aiIndex]) {
        messages.value[aiIndex].text = '抱歉，重新生成失败，请稍后重试。'
      }
    } finally {
      isLoading.value = false
      saveCurrentChat()
      scrollToBottom()
    }
  }

  const showMoreOptions = () => {
    console.log('显示更多选项')
    // 这里可以添加更多选项的逻辑
  }

  // --- Database Selector ---

  const selectDatabase = (database) => {
    selectedDatabase.value = database
    dropdownOpen.value = false
  }

  const toggleDropdown = () => {
    dropdownOpen.value = !dropdownOpen.value
  }

  const getCurrentDatabaseOption = () => {
    return (
      databaseOptions.value.find(
        (option) => option.value === selectedDatabase.value
      ) || databaseOptions.value[2]
    )
  }

  // --- Deep Thinking Functions ---

  const toggleDeepThinking = () => {
    deepThinkingEnabled.value = !deepThinkingEnabled.value
    console.log('深度思考模式:', deepThinkingEnabled.value ? '开启' : '关闭')
  }

  // --- Model Selector Functions ---

  const selectModel = (model) => {
    selectedModel.value = model
    modelDropdownOpen.value = false
    console.log('切换模型:', model)
  }

  const toggleModelDropdown = () => {
    modelDropdownOpen.value = !modelDropdownOpen.value
  }

  const getCurrentModelOption = () => {
    return (
      modelOptions.value.find(
        (option) => option.value === selectedModel.value
      ) || modelOptions.value[0]
    )
  }

  const askRelatedQuestion = (question) => {
    newMessage.value = question
    nextTick(() => {
      adjustTextareaHeight()
      sendMessage()
    })
  }

  const highlightQuery = (text) => {
    if (!newMessage.value.trim()) return text
    const query = newMessage.value.trim()
    const regex = new RegExp(
      `(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`,
      'gi'
    )
    return text.replace(regex, '<strong>$1</strong>')
  }

  // --- Textarea and Suggestions ---

  const handleKeydown = (event) => {
    if (suggestions.value.length > 0) {
      if (event.key === 'ArrowDown') {
        event.preventDefault()
        selectedIndex.value =
          (selectedIndex.value + 1) % suggestions.value.length
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        if (selectedIndex.value <= 0) {
          selectedIndex.value = suggestions.value.length - 1
        } else {
          selectedIndex.value--
        }
      } else if (event.key === 'Enter') {
        if (selectedIndex.value !== -1) {
          event.preventDefault()
          selectSuggestion(suggestions.value[selectedIndex.value])
        } else if (!event.shiftKey) {
          event.preventDefault()
          sendMessage()
        }
      } else if (event.key === 'Escape') {
        event.preventDefault()
        clearSuggestions()
      }
    } else if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      sendMessage()
    }
  }

  const adjustTextareaHeight = () => {
    const textarea = messageTextarea.value
    if (textarea) {
      textarea.style.height = 'auto'
      const scrollHeight = textarea.scrollHeight
      const lineHeight = 24
      const maxHeight = lineHeight * 10
      const minHeight = lineHeight * 2
      const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight)
      textarea.style.height = newHeight + 'px'
    }
  }

  const handleInput = () => {
    adjustTextareaHeight()
    if (debounceTimer.value) {
      clearTimeout(debounceTimer.value)
    }
    debounceTimer.value = setTimeout(() => {
      fetchSuggestions()
    }, 250)
  }

  const fetchSuggestions = () => {
    const query = newMessage.value.trim()
    if (!query) {
      suggestions.value = []
      return
    }

    const scriptId = 'baidu-jsonp-script'
    const existingScript = document.getElementById(scriptId)
    if (existingScript) {
      existingScript.remove()
    }

    const script = document.createElement('script')
    script.id = scriptId
    script.src = `https://suggestion.baidu.com/su?wd=${encodeURIComponent(
      query
    )}&cb=window.handleBaiduSuggestions`

    script.onerror = () => {
      console.error('Failed to load suggestions.')
      suggestions.value = []
      if (script.parentNode) {
        script.parentNode.removeChild(script)
      }
    }

    script.onload = () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script)
      }
    }

    document.head.appendChild(script)
  }

  const selectSuggestion = (suggestion) => {
    newMessage.value = suggestion
    suggestions.value = []
    selectedIndex.value = -1
    nextTick(() => {
      adjustTextareaHeight()
      messageTextarea.value.focus()
    })
  }

  const clearSuggestions = () => {
    setTimeout(() => {
      suggestions.value = []
      selectedIndex.value = -1
    }, 150)
  }

  // --- Lifecycle Hooks ---

  const handleClickOutside = (event) => {
    const dbSelector = document.querySelector('.database-selector')
    const modelSelector = document.querySelector('.model-selector')

    if (dbSelector && !dbSelector.contains(event.target)) {
      dropdownOpen.value = false
    }

    if (modelSelector && !modelSelector.contains(event.target)) {
      modelDropdownOpen.value = false
    }
  }

  onMounted(() => {
    // 安全地在客户端加载和配置 KaTeX 扩展（该包默认导出为函数）
    import('marked-katex-extension')
      .then((mod) => {
        const markedKatex = mod.default || mod.markedKatex
        if (typeof markedKatex === 'function') {
          marked.use(markedKatex({ throwOnError: false }))
          console.log('KaTeX extension loaded and configured.')
        } else {
          console.warn(
            'marked-katex-extension export not found as function:',
            mod
          )
        }
      })
      .catch((e) => {
        console.error('Failed to load KaTeX extension:', e)
      })

    // 获取用户信息
    const userData = localStorage.getItem('ai-chat-user')
    if (userData) {
      currentUser.value = JSON.parse(userData)
    }

    document.addEventListener('click', handleClickOutside)
    window.handleBaiduSuggestions = (data) => {
      suggestions.value = data.s || []
      selectedIndex.value = -1
    }

    applyStoredTheme()
    loadFromStorage() // 从localStorage加载数据
    nextTick(() => {
      scrollToBottom()
      isAtBottom.value = true
    })
  })

  onUnmounted(() => {
    document.removeEventListener('click', handleClickOutside)
    if (messagesContainer.value) {
      messagesContainer.value.removeEventListener('scroll', handleScroll)
    }
    delete window.handleBaiduSuggestions
  })
</script>

<style scoped>
  /* 导入原有的样式 */
  @import '../assets/main.css';

  /* ================================================================= */
  /* =================== 新增的 Markdown 样式 开始 =================== */
  /* ================================================================= */

  /* 
  这个类应用于 v-html 渲染的 AI 消息容器。
  使用 :deep() 选择器来穿透 scoped CSS 的限制，
  从而样式化由 marked.js 动态生成的 HTML 元素。
*/
  .ai-message-content :deep(p) {
    /* 确保段落之间有正常的间距 */
    margin-bottom: 0.5rem;
  }

  .ai-message-content :deep(p:last-child) {
    margin-bottom: 0;
  }

  .ai-message-content :deep(strong) {
    /* 定义加粗文本的样式 */
    font-weight: 600;
  }

  .ai-message-content :deep(ul),
  .ai-message-content :deep(ol) {
    /* 定义列表的样式 */
    padding-left: 24px;
    margin: 0.75rem 0;
  }

  .ai-message-content :deep(li) {
    /* 定义列表项的样式 */
    margin-bottom: 0.25rem;
  }

  .ai-message-content :deep(pre) {
    /* 定义代码块容器的样式 */
    background-color: #f3f4f6; /* 浅灰色背景 */
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    overflow-x: auto; /* 内容过长时可以水平滚动 */
    white-space: pre-wrap; /* 自动换行 */
    word-wrap: break-word;
  }

  .ai-message-content :deep(code) {
    /* 定义行内代码和代码块内代码的字体 */
    font-family: 'Courier New', Courier, monospace;
    font-size: 0.9em;
    background-color: #e5e7eb; /* 浅灰色背景 */
    padding: 2px 5px;
    border-radius: 4px;
  }

  .ai-message-content :deep(pre code) {
    /* 重置代码块内部代码的样式，因为它已经有 <pre> 作为背景 */
    background-color: transparent;
    padding: 0;
    border-radius: 0;
  }

  /* ================================================================= */
  /* ==================== 新增的 Markdown 样式 结束 =================== */
  /* ================================================================= */

  .initial-screen {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    height: calc(100% - 65px); /* Full height minus header */
    text-align: center;
    color: #6b7280;
  }

  .initial-screen .welcome-message {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 16px;
  }

  .initial-screen .hello-emoji {
    font-size: 48px;
  }

  .initial-screen h2 {
    font-size: 24px;
    font-weight: 600;
    color: #374151;
  }

  .initial-screen p {
    font-size: 16px;
  }

  /* 新增的聊天头部样式 */
  .chat-header {
    padding: 16px 24px;
    border-bottom: 1px solid #e5e7eb;
    background: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .user-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .user-avatar {
    font-size: 20px;
  }

  .user-name {
    font-weight: 500;
    color: #374151;
  }

  /* 退出登录按钮样式 */
  .logout-btn {
    background: none;
    border: none;
    padding: 8px;
    border-radius: 6px;
    cursor: pointer;
    color: #6b7280;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .logout-btn:hover {
    background: #f3f4f6;
    color: #ef4444;
  }

  /* 调整侧边栏头部布局 */
  .sidebar-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px;
    border-bottom: 1px solid #e5e7eb;
  }

  .sidebar-title {
    margin: 0;
    flex: 1;
    text-align: center;
  }

  /* 按钮层样式 */
  .button-layer {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  /* 数据库选择器样式统一 */
  .database-selector .db-selector-btn {
    height: 36px;
    font-size: 14px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .database-selector .db-text {
    font-size: 14px;
  }

  .database-selector .dropdown-arrow {
    font-size: 12px;
  }

  /* 深度思考按钮样式 */
  .deep-thinking-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    font-size: 14px;
    color: #6c757d;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    height: 36px;
  }

  /* 暗色主题：去除深度搜索按钮的高亮，改为深色不刺眼 */
  #chat-container.theme-dark .deep-thinking-btn:hover {
    background: rgba(28, 38, 68, 0.78) !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
    color: #ffffff !important;
  }
  /* 亮色主题保持原样 */
  #chat-container.theme-light .deep-thinking-btn:hover {
    background: #e9ecef;
    border-color: #dee2e6;
  }

  .deep-thinking-btn.active {
    background: #e3f2fd;
    border-color: #2196f3;
    color: #1976d2;
  }

  .deep-thinking-btn.active svg {
    color: #1976d2;
  }

  /* 模型选择器样式 */
  .model-selector {
    position: relative;
    display: inline-block;
  }

  .model-selector-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    font-size: 14px;
    color: #495057;
    cursor: pointer;
    transition: all 0.2s ease;
    white-space: nowrap;
    min-width: 100px;
    height: 36px;
  }

  .model-selector-btn:hover {
    background: #e9ecef;
    border-color: #dee2e6;
  }

  .model-selector.open .model-selector-btn {
    background: #e9ecef;
    border-color: #dee2e6;
  }

  .model-text {
    flex: 1;
    text-align: left;
    font-size: 14px;
  }

  .model-label {
    flex: 1;
    text-align: left;
    font-size: 14px;
  }

  /* 统一下拉菜单样式 */
  .dropdown-menu {
    font-size: 14px;
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
  }

  .db-label {
    font-size: 14px;
  }

  .dropdown-arrow {
    font-size: 12px;
    transition: transform 0.2s ease;
  }

  .database-selector.open .dropdown-arrow,
  .model-selector.open .dropdown-arrow {
    transform: rotate(180deg);
  }

  /* 滚动到底部按钮样式 */
  .scroll-to-bottom-btn {
    position: fixed;
    bottom: 188px; /* 按钮底部与对话框底部对齐 */
    right: 20px;
    width: 48px;
    height: 48px;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    z-index: 1000;
    color: #6b7280;
  }

  .scroll-to-bottom-btn:hover {
    background: #f9fafb;
    border-color: #d1d5db;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
    color: #374151;
    transform: translateY(-2px);
  }

  .scroll-to-bottom-btn:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .scroll-to-bottom-btn svg {
    transition: transform 0.2s ease;
  }

  .scroll-to-bottom-btn:hover svg {
    transform: translateY(1px);
  }

  /* 确保消息容器是相对定位，以便按钮正确定位 */
  .messages-container {
    position: relative;
  }

  /* 响应式调整 */
  @media (max-width: 768px) {
    .scroll-to-bottom-btn {
      width: 44px;
      height: 44px;
      bottom: 160px;
      right: 16px;
    }
  }

  @media (max-width: 768px) {
    .button-layer {
      gap: 6px;
    }

    .deep-thinking-btn .btn-text {
      display: none;
    }

    .deep-thinking-btn {
      padding: 8px;
      min-width: auto;
    }

    .model-selector-btn {
      min-width: 80px;
      padding: 8px 10px;
    }

    .model-text {
      font-size: 12px;
    }
  }

  @media (max-width: 480px) {
    .button-layer {
      flex-direction: column;
      align-items: stretch;
      gap: 8px;
    }

    .database-selector,
    .model-selector {
      width: 100%;
    }

    .db-selector-btn,
    .model-selector-btn {
      width: 100%;
      justify-content: space-between;
    }

    .deep-thinking-btn {
      width: 100%;
      justify-content: center;
    }

    .deep-thinking-btn .btn-text {
      display: inline;
    }
  }

  /* 新增：禁用状态下的输入区域样式 */
  .input-wrapper textarea:disabled,
  .send-btn:disabled,
  .button-layer button:disabled,
  .button-layer .db-selector-btn:disabled,
  .button-layer .model-selector-btn:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .fade-related-enter-active,
  .fade-related-leave-active {
    transition: opacity 0.3s ease, transform 0.3s ease;
  }
  .fade-related-enter-from,
  .fade-related-leave-to {
    opacity: 0;
    transform: translateY(6px);
  }
  .fade-related-enter-to,
  .fade-related-leave-from {
    opacity: 1;
    transform: translateY(0);
  }

  /* 对话历史时间样式 */
  .chat-texts {
    display: flex;
    flex-direction: column;
  }
  .chat-time {
    font-size: 12px;
    color: #909399;
    margin-top: 2px;
  }

  /* 历史分组标题样式 */
  .history-group {
    margin-bottom: 12px;
  }
  .group-title {
    font-size: 13px;
    color: #666;
    margin: 6px 0;
  }

  /* ===== Tech Theme Override ===== */
  :root {
    --bg-gradient: radial-gradient(
        1000px 600px at 10% -10%,
        rgba(31, 64, 154, 0.35) 0%,
        rgba(10, 16, 40, 0) 60%
      ),
      radial-gradient(
        800px 500px at 100% 0%,
        rgba(0, 255, 200, 0.12) 0%,
        rgba(10, 16, 40, 0) 70%
      ),
      linear-gradient(180deg, #0a1028 0%, #0d102f 100%);
    --glass-bg: rgba(255, 255, 255, 0.06);
    --glass-border: 1px solid rgba(255, 255, 255, 0.12);
    --text-primary: #e8f0ff;
    --text-secondary: #9fb0d1;
    --neon-blue: #40a9ff;
    --neon-cyan: #00e6ff;
    --neon-purple: #8a2be2;
    --accent-green: #22d3a8;
  }

  #chat-container {
    background: var(--bg-gradient);
    color: var(--text-primary);
  }

  /* Sidebar */
  .sidebar {
    backdrop-filter: blur(14px) saturate(140%);
    background: var(--glass-bg);
    border-right: var(--glass-border);
  }
  .sidebar-header .menu-toggle {
    background: transparent;
    border: var(--glass-border);
    border-radius: 10px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }
  .sidebar-header .menu-toggle:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.25);
  }
  .sidebar-title {
    color: var(--text-primary);
    letter-spacing: 0.5px;
  }
  .logout-btn {
    border: var(--glass-border);
    border-radius: 10px;
    background: transparent;
    color: var(--text-secondary);
  }
  .logout-btn:hover {
    box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.25);
    color: var(--text-primary);
  }

  .new-chat-btn {
    background: linear-gradient(
      135deg,
      rgba(64, 169, 255, 0.18),
      rgba(0, 230, 255, 0.18)
    );
    border: var(--glass-border);
    color: var(--text-primary);
    border-radius: 12px;
    transition: box-shadow 0.2s ease, transform 0.2s ease;
  }
  .new-chat-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 12px rgba(64, 169, 255, 0.35);
  }
  .btn-icon {
    color: var(--neon-cyan);
  }

  /* History groups */
  .history h3 {
    color: var(--text-secondary);
  }
  .group-title {
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }
  .chat-item {
    border-radius: 10px;
    transition: background 0.2s ease, box-shadow 0.2s ease;
  }
  .chat-item .chat-content {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .chat-item:hover {
    background: rgba(255, 255, 255, 0.06);
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
  }
  .chat-icon {
    color: var(--neon-blue);
  }
  .chat-title {
    color: var(--text-primary);
  }
  .chat-time {
    color: var(--text-secondary);
  }
  .delete-btn {
    background: transparent;
    border: var(--glass-border);
    color: #fca5a5;
    border-radius: 10px;
  }
  .delete-btn:hover {
    box-shadow: 0 0 0 2px rgba(252, 165, 165, 0.25);
  }

  /* Main header */
  .chat-header {
    backdrop-filter: blur(10px);
    background: rgba(255, 255, 255, 0.04);
    border-bottom: var(--glass-border);
  }
  .user-info .user-avatar {
    filter: drop-shadow(0 0 6px rgba(64, 169, 255, 0.35));
  }
  .user-info .user-name {
    color: var(--text-primary);
  }

  /* Messages */
  .messages-container {
    background: transparent;
  }
  .message.user .bubble {
    background: linear-gradient(
      135deg,
      rgba(64, 169, 255, 0.16),
      rgba(138, 43, 226, 0.12)
    );
    border: var(--glass-border);
    color: var(--text-primary);
    box-shadow: 0 6px 16px rgba(10, 16, 40, 0.35);
  }
  .message.ai .bubble {
    background: linear-gradient(
      135deg,
      rgba(34, 211, 168, 0.14),
      rgba(0, 230, 255, 0.1)
    );
    border: var(--glass-border);
    color: var(--text-primary);
    box-shadow: 0 6px 16px rgba(10, 16, 40, 0.35);
  }
  .bubble {
    border-radius: 14px;
    backdrop-filter: blur(12px) saturate(140%);
  }
  .ai-message-content :deep(code),
  .ai-message-content :deep(pre) {
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #d3e2ff;
  }
  .ai-message-content :deep(a) {
    color: var(--neon-cyan);
  }
  .welcome-message {
    color: var(--text-secondary);
  }

  /* Action buttons */
  .message-actions {
    display: flex;
    gap: 8px;
  }
  .action-btn {
    background: rgba(255, 255, 255, 0.05);
    border: var(--glass-border);
    color: var(--text-primary);
    border-radius: 10px;
    transition: transform 0.15s ease, box-shadow 0.15s ease, color 0.15s ease;
  }
  .action-btn:hover {
    transform: translateY(-1px);
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.25);
    color: var(--neon-cyan);
  }
  .copy-btn:hover {
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.45),
      0 0 16px rgba(64, 169, 255, 0.35);
    color: var(--neon-blue);
  }
  .like-btn:hover {
    box-shadow: 0 0 0 2px rgba(34, 211, 168, 0.45),
      0 0 16px rgba(34, 211, 168, 0.35);
    color: var(--accent-green);
  }
  .dislike-btn:hover {
    box-shadow: 0 0 0 2px rgba(252, 165, 165, 0.5),
      0 0 16px rgba(239, 68, 68, 0.35);
    color: #ef4444;
  }
  .refresh-btn:hover {
    box-shadow: 0 0 0 2px rgba(138, 43, 226, 0.5),
      0 0 16px rgba(138, 43, 226, 0.35);
    color: var(--neon-purple);
  }
  .more-btn:hover {
    box-shadow: 0 0 0 2px rgba(156, 163, 175, 0.45),
      0 0 14px rgba(156, 163, 175, 0.3);
    color: var(--text-primary);
  }

  /* Input area */
  .input-wrapper textarea {
    background: rgba(255, 255, 255, 0.06);
    border: var(--glass-border);
    color: var(--text-primary);
    border-radius: 12px;
  }
  .send-btn {
    position: relative;
    overflow: hidden;
    background: linear-gradient(
      135deg,
      rgba(64, 169, 255, 0.32),
      rgba(0, 230, 255, 0.32)
    );
    border: var(--glass-border);
    color: #0b122e;
    font-weight: 600;
    border-radius: 12px;
  }
  .send-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: radial-gradient(
      180px 180px at 50% 50%,
      rgba(0, 230, 255, 0.35),
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.25s ease;
    mix-blend-mode: screen;
  }
  .send-btn:hover {
    box-shadow: 0 0 0 2px rgba(0, 230, 255, 0.45),
      0 0 20px rgba(0, 230, 255, 0.35);
  }
  .send-btn:hover::after {
    opacity: 1;
  }

  /* Dropdowns */
  .database-selector .db-selector-btn,
  .model-selector .model-selector-btn,
  .button-layer button {
    background: rgba(255, 255, 255, 0.06);
    border: var(--glass-border);
    color: var(--text-primary);
    border-radius: 12px;
  }
  .dropdown-list {
    background: rgba(10, 16, 40, 0.88);
    border: var(--glass-border);
    backdrop-filter: blur(10px);
  }
  .dropdown-item {
    color: var(--text-secondary);
  }
  .dropdown-item.active,
  .dropdown-item:hover {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.06);
  }

  /* Scroll to bottom button */
  .scroll-to-bottom-btn {
    background: rgba(255, 255, 255, 0.08);
    border: var(--glass-border);
    color: var(--text-primary);
    border-radius: 10px;
    backdrop-filter: blur(8px);
  }
  .scroll-to-bottom-btn:hover {
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.3);
  }

  /* Related questions */
  .related-questions {
    background: rgba(255, 255, 255, 0.05);
    border: var(--glass-border);
    border-radius: 12px;
  }
  .related-questions-title {
    color: var(--text-secondary);
  }
  .related-question-item {
    background: rgba(255, 255, 255, 0.06);
    border: 1px dashed rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
  }
  .related-question-item:hover {
    border-color: var(--neon-cyan);
    box-shadow: 0 0 12px rgba(0, 230, 255, 0.25);
  }

  /* Scrollbar */
  .messages-container::-webkit-scrollbar {
    width: 8px;
  }
  .messages-container::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--neon-blue), var(--neon-purple));
    border-radius: 6px;
  }
  .messages-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.06);
  }

  /* Small screens */
  @media (max-width: 640px) {
    .sidebar {
      backdrop-filter: blur(10px);
    }
    .new-chat-btn,
    .send-btn {
      border-radius: 10px;
    }
  }

  /* ===== Advanced Tech Animations & Polish ===== */
  #chat-container {
    position: relative;
    overflow: hidden;
  }
  #chat-container::before {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    mix-blend-mode: screen;
    background-image: radial-gradient(
        800px 600px at -10% -10%,
        rgba(64, 169, 255, 0.12),
        transparent 60%
      ),
      radial-gradient(
        700px 500px at 110% 10%,
        rgba(0, 230, 255, 0.1),
        transparent 65%
      ),
      repeating-linear-gradient(
        45deg,
        rgba(0, 230, 255, 0.08) 0 2px,
        transparent 2px 36px
      ),
      repeating-linear-gradient(
        -45deg,
        rgba(138, 43, 226, 0.06) 0 2px,
        transparent 2px 36px
      ),
      radial-gradient(
        circle at 50% 50%,
        rgba(255, 255, 255, 0.03) 0 1px,
        transparent 1px 6px
      );
    background-size: 100% 100%, 100% 100%, 260px 260px, 260px 260px, 14px 14px;
    opacity: 0.65;
    transform: translateZ(0);
    animation: techGridFloat 22s linear infinite;
  }
  #chat-container::after {
    content: '';
    position: absolute;
    inset: 0;
    pointer-events: none;
    background-image: linear-gradient(
      180deg,
      transparent 30%,
      rgba(0, 230, 255, 0.12) 50%,
      transparent 70%
    );
    mix-blend-mode: overlay;
    opacity: 0.22;
    animation: scanSweep 6.8s ease-in-out infinite;
  }
  @keyframes techGridFloat {
    0% {
      background-position: 0 0, 0 0, 0 0, 0 0, 0 0;
    }
    50% {
      background-position: 20px 0, -10px 10px, 130px 130px, -130px -130px, 0 6px;
    }
    100% {
      background-position: 40px 0, -20px 20px, 260px 260px, -260px -260px, 0 0;
    }
  }
  @keyframes scanSweep {
    0%,
    100% {
      transform: translateY(-10%);
    }
    50% {
      transform: translateY(10%);
    }
  }

  /* Subtle gradient pulsation */
  #chat-container.theme-dark::before {
    opacity: 0.72;
  }
  #chat-container.theme-light::before {
    opacity: 0.45;
  }
  #chat-container {
    animation: bgPulse 12s ease-in-out infinite;
  }
  @keyframes bgPulse {
    0%,
    100% {
      filter: brightness(1);
    }
    50% {
      filter: brightness(1.06);
    }
  }

  /* Bubble entrance */
  .message .bubble {
    animation: bubbleIn 0.25s ease both;
  }
  @keyframes bubbleIn {
    from {
      opacity: 0;
      transform: translateY(6px) scale(0.98);
    }
    to {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  /* Active chat item highlight */
  .chat-item.active {
    background: rgba(64, 169, 255, 0.12);
    box-shadow: inset 0 0 0 1px rgba(64, 169, 255, 0.25),
      0 6px 18px rgba(10, 16, 40, 0.4);
  }
  .chat-item.active .chat-title {
    color: var(--neon-cyan);
  }

  /* Action button ripple & glow */
  .action-btn {
    position: relative;
    overflow: hidden;
  }
  .action-btn::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    background: radial-gradient(
      220px 220px at 50% 50%,
      rgba(64, 169, 255, 0.35),
      transparent 70%
    );
    opacity: 0;
    transition: opacity 0.22s ease;
    mix-blend-mode: screen;
  }
  .action-btn:hover::after {
    opacity: 1;
  }
  .action-btn {
    --mx: 50%;
    --my: 50%;
  }

  /* Input focus glow */
  .input-wrapper textarea:focus {
    box-shadow: 0 0 0 2px rgba(0, 230, 255, 0.35),
      0 0 16px rgba(0, 230, 255, 0.25);
  }

  /* Dropdown polish */
  .dropdown-list {
    transform-origin: top;
    transition: transform 0.18s ease, opacity 0.18s ease;
  }

  /* Related questions polish */
  .related-questions {
    box-shadow: 0 10px 28px rgba(10, 16, 40, 0.35);
  }
  .related-question-item {
    transition: transform 0.15s ease;
  }
  .related-question-item:hover {
    transform: translateY(-1px);
  }

  /* Scrollbar for sidebar history */
  .history ul::-webkit-scrollbar {
    width: 8px;
  }
  .history ul::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 6px;
  }

  /* ===== Theme Switcher UI ===== */
  .theme-switcher {
    margin-left: auto;
    display: flex;
    align-items: center;
  }
  .theme-btn {
    background: rgba(255, 255, 255, 0.06);
    border: var(--glass-border);
    color: var(--text-primary);
    border-radius: 10px;
    padding: 6px 10px;
    display: flex;
    gap: 6px;
    align-items: center;
  }
  .theme-btn .theme-text {
    font-size: 12px;
    color: var(--text-secondary);
  }
  .theme-btn:hover {
    box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.3);
  }

  /* ===== Light Theme Overrides ===== */
  #chat-container.theme-light {
    --bg-gradient: radial-gradient(
      900px 600px at 0% 0%,
      rgba(255, 255, 255, 0.9) 0%,
      rgba(255, 255, 255, 0.6) 50%,
      rgba(240, 244, 255, 0.9) 100%
    );
    --glass-bg: rgba(255, 255, 255, 0.75);
    --glass-border: 1px solid rgba(0, 0, 0, 0.08);
    --text-primary: #0b122e;
    --text-secondary: #4b5563;
    --neon-blue: #2563eb;
    --neon-cyan: #06b6d4;
    --neon-purple: #7c3aed;
    --accent-green: #059669;
  }

  #chat-container.theme-light .sidebar {
    background: var(--glass-bg);
  }
  #chat-container.theme-light .logout-btn,
  #chat-container.theme-light .new-chat-btn,
  #chat-container.theme-light .action-btn,
  #chat-container.theme-light .input-wrapper textarea,
  #chat-container.theme-light .send-btn,
  #chat-container.theme-light .database-selector .db-selector-btn,
  #chat-container.theme-light .model-selector .model-selector-btn,
  #chat-container.theme-light .dropdown-list {
    border: var(--glass-border);
  }

  #chat-container.theme-light .message.user .bubble {
    background: #ffffff;
    border: 1px solid rgba(0, 0, 0, 0.08);
    color: var(--text-primary);
  }
  #chat-container.theme-light .message.ai .bubble {
    background: #f8fafc;
    border: 1px solid rgba(0, 0, 0, 0.08);
    color: var(--text-primary);
  }
  #chat-container.theme-light .bubble {
    box-shadow: 0 6px 16px rgba(11, 18, 46, 0.08);
  }
  #chat-container.theme-light .ai-message-content :deep(code),
  #chat-container.theme-light .ai-message-content :deep(pre) {
    background: #0b122e0f;
    border: 1px solid rgba(11, 18, 46, 0.12);
    color: #0b122e;
  }
  #chat-container.theme-light .ai-message-content :deep(a) {
    color: var(--neon-blue);
  }
  #chat-container.theme-light .welcome-message {
    color: var(--text-secondary);
  }

  #chat-container.theme-light .action-btn {
    background: rgba(11, 18, 46, 0.06);
    color: var(--text-primary);
  }
  #chat-container.theme-light .action-btn:hover {
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.25);
    color: var(--neon-blue);
  }

  #chat-container.theme-light .scroll-to-bottom-btn {
    background: rgba(11, 18, 46, 0.06);
  }

  #chat-container.theme-light .related-questions {
    background: rgba(255, 255, 255, 0.8);
    border-color: rgba(0, 0, 0, 0.08);
  }
  #chat-container.theme-light .related-question-item {
    background: rgba(255, 255, 255, 0.9);
    border-color: rgba(0, 0, 0, 0.08);
    color: var(--text-primary);
  }
  #chat-container.theme-light .related-question-item:hover {
    box-shadow: 0 8px 18px rgba(11, 18, 46, 0.12);
  }

  #chat-container.theme-light .messages-container::-webkit-scrollbar-thumb {
    background: linear-gradient(var(--neon-blue), var(--neon-purple));
  }

  /* ===== Explicit Dark Theme Overrides ===== */
  #chat-container.theme-dark {
    /* 强制深色背景，避免被全局样式覆盖 */
    --bg-gradient: radial-gradient(
        1000px 600px at 10% -10%,
        rgba(31, 64, 154, 0.35) 0%,
        rgba(10, 16, 40, 0) 60%
      ),
      radial-gradient(
        800px 500px at 100% 0%,
        rgba(0, 255, 200, 0.12) 0%,
        rgba(10, 16, 40, 0) 70%
      ),
      linear-gradient(180deg, #0a1028 0%, #0d102f 100%);
    --glass-bg: rgba(255, 255, 255, 0.06);
    --glass-border: 1px solid rgba(255, 255, 255, 0.12);
    --text-primary: #e8f0ff;
    --text-secondary: #9fb0d1;
    --neon-blue: #40a9ff;
    --neon-cyan: #00e6ff;
    --neon-purple: #8a2be2;
    --accent-green: #22d3a8;
    background: var(--bg-gradient) !important;
    color: var(--text-primary);
  }
  #chat-container.theme-dark .sidebar,
  #chat-container.theme-dark .chat-header,
  #chat-container.theme-dark .messages-container,
  #chat-container.theme-dark .input-wrapper textarea,
  #chat-container.theme-dark .send-btn,
  #chat-container.theme-dark .action-btn,
  #chat-container.theme-dark .dropdown-list,
  #chat-container.theme-dark .related-questions {
    border-color: rgba(255, 255, 255, 0.12);
  }

  /* 输入框主题适配 */
  #chat-container.theme-dark .input-wrapper textarea {
    background: rgba(18, 24, 40, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: var(--text-primary);
  }
  #chat-container.theme-dark .input-wrapper textarea::placeholder {
    color: rgba(232, 240, 255, 0.45);
  }

  #chat-container.theme-light .input-wrapper textarea {
    background: #ffffff;
    border: 1px solid rgba(11, 18, 46, 0.12);
    color: var(--text-primary);
  }
  #chat-container.theme-light .input-wrapper textarea::placeholder {
    color: rgba(75, 85, 99, 0.7);
  }

  /* 输入容器主题适配（覆盖 assets/main.css 的白底边框） */
  #chat-container.theme-dark .input-wrapper {
    background: rgba(10, 14, 28, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.35) inset;
  }
  #chat-container.theme-light .input-wrapper {
    background: #ffffff;
    border: 1px solid rgba(11, 18, 46, 0.12);
  }

  /* 发送按钮主题适配 */
  #chat-container.theme-dark .send-btn {
    background: linear-gradient(
      135deg,
      rgba(64, 169, 255, 0.28),
      rgba(0, 230, 255, 0.28)
    );
    color: #0b122e;
    border: 1px solid rgba(255, 255, 255, 0.12);
  }
  #chat-container.theme-light .send-btn {
    background-color: #2563eb;
    color: #fff;
    border: 1px solid rgba(11, 18, 46, 0.12);
  }

  /* 占位符与滚动条微调，避免视觉突兀 */
  #chat-container.theme-dark
    .textarea-container
    textarea::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.18);
    border-radius: 6px;
  }
  #chat-container.theme-dark
    .textarea-container
    textarea::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.06);
  }

  /* 修复：暗色主题下输入区域外圈白底（来自 assets/main.css 的 .chat-input-area） */
  #chat-container.theme-dark .chat-input-area {
    background: transparent !important;
    border-top: 1px solid rgba(255, 255, 255, 0.12) !important;
  }

  /* 同时覆盖建议列表的白底，避免形成白色边缘 */
  #chat-container.theme-dark .suggestions-list {
    background: rgba(10, 16, 40, 0.92) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.35) !important;
  }

  /* 进一步统一下拉菜单的暗色背景，防止白边错觉 */
  #chat-container.theme-dark .dropdown-menu {
    background: rgba(10, 16, 40, 0.92) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
  }

  /* 暗色主题下：相关问题模块文字统一为白色，提升可读性 */
  #chat-container.theme-dark .related-questions-title {
    color: #ffffff !important;
  }
  #chat-container.theme-dark .related-question-item {
    color: #ffffff !important;
  }
  #chat-container.theme-dark .related-question-item:hover {
    color: #ffffff !important;
  }
  #chat-container.theme-dark .related-questions .question-text {
    color: #ffffff !important;
  }

  /* 暗色主题下：修正相关问题项 hover 出现白色高亮的问题（覆盖全局样式） */
  #chat-container.theme-dark .related-question-item {
    background: rgba(20, 28, 52, 0.6) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    color: #ffffff !important;
  }
  #chat-container.theme-dark .related-question-item:hover {
    background: rgba(28, 38, 68, 0.78) !important; /* 深色渐变而非白色 */
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 0 12px rgba(0, 230, 255, 0.25) !important;
    color: #ffffff !important;
  }
  #chat-container.theme-dark .related-questions .question-text {
    color: #ffffff !important;
  }

  /* 暗色主题下：对话历史选中/悬停不再高亮刺眼，统一为深色方案 */
  #chat-container.theme-dark .history li.chat-item {
    background: transparent !important;
    color: var(--text-primary) !important;
  }
  #chat-container.theme-dark .history li.chat-item:hover {
    background: rgba(28, 38, 68, 0.55) !important;
    box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.1) !important;
  }
  #chat-container.theme-dark .history li.chat-item.active {
    background: rgba(28, 38, 68, 0.78) !important;
    box-shadow: inset 0 0 0 1px var(--glass-border),
      0 0 12px rgba(0, 230, 255, 0.25) !important;
    color: #ffffff !important;
  }
  #chat-container.theme-dark .history li.chat-item.active .chat-title {
    color: #ffffff !important;
  }
  #chat-container.theme-dark .history li.chat-item .delete-btn:hover {
    background-color: rgba(239, 68, 68, 0.15) !important;
  }

  /* 暗色主题下：退出登录按钮状态优化（选中/悬停/聚焦不再过亮） */
  #chat-container.theme-dark .logout-btn {
    color: #ffffff !important;
    background: transparent !important;
    border-color: rgba(255, 255, 255, 0.18) !important;
  }
  #chat-container.theme-dark .logout-btn:hover,
  #chat-container.theme-dark .logout-btn:focus-visible,
  #chat-container.theme-dark .logout-btn:active {
    background: rgba(28, 38, 68, 0.78) !important;
    color: #ffffff !important;
    box-shadow: 0 0 0 2px rgba(0, 230, 255, 0.25) !important;
  }

  /* 暗色主题下：侧边栏折叠态图标/文字统一为白色，提高可读性 */
  #chat-container.theme-dark .sidebar.collapsed .hamburger-icon span {
    background-color: #ffffff !important;
  }
  #chat-container.theme-dark .sidebar.collapsed .collapsed-new-chat {
    color: #ffffff !important;
  }
  #chat-container.theme-dark .sidebar.collapsed .collapsed-new-chat:hover {
    background: rgba(28, 38, 68, 0.78) !important;
    box-shadow: 0 0 0 2px rgba(0, 230, 255, 0.25) !important;
  }
  #chat-container.theme-dark .sidebar.collapsed .menu-toggle {
    border-color: rgba(255, 255, 255, 0.18) !important;
  }

  /* 暗色主题下：折叠态汉堡菜单三条线与退出按钮同色（白色），并优化悬停背景 */
  #chat-container.theme-dark .sidebar.collapsed .hamburger-icon span {
    background-color: #ffffff !important;
  }
  #chat-container.theme-dark .sidebar.collapsed .menu-toggle {
    border-color: rgba(255, 255, 255, 0.18) !important;
  }
  #chat-container.theme-dark .sidebar.collapsed .menu-toggle:hover {
    background: rgba(28, 38, 68, 0.78) !important;
  }

  /* 暗色主题下：无论折叠与否，汉堡菜单三条线统一白色 */
  #chat-container.theme-dark .sidebar .hamburger-icon span {
    background-color: #ffffff !important;
  }
  #chat-container.theme-dark .sidebar .menu-toggle:hover {
    background: rgba(28, 38, 68, 0.78) !important;
  }

  /* 去除“相关问题推荐”外层容器的外圈（背景/边框/阴影） */
  .related-questions {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  #chat-container.theme-dark .related-questions {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }
  #chat-container.theme-light .related-questions {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }

  /* 强化“相关问题”每一项的外圈可见度（暗色与亮色分别优化） */
  .related-questions .related-question-item {
    position: relative;
    border-radius: 10px;
  }

  /* 暗色主题：默认细描边，更明显但不过亮；悬停加粗并带柔和外发光 */
  #chat-container.theme-dark .related-questions .related-question-item {
    box-shadow: 0 0 0 1.5px rgba(255, 255, 255, 0.18) !important;
    background: rgba(20, 28, 52, 0.6) !important;
  }
  #chat-container.theme-dark .related-questions .related-question-item:hover {
    box-shadow: 0 0 0 2px rgba(0, 230, 255, 0.55),
      0 0 12px rgba(0, 230, 255, 0.25) !important;
    border-color: rgba(0, 230, 255, 0.45) !important;
  }

  /* 亮色主题：默认浅灰描边，悬停略增强但不刺眼 */
  #chat-container.theme-light .related-questions .related-question-item {
    box-shadow: 0 0 0 1.5px rgba(17, 24, 39, 0.14) !important;
    background: #ffffff !important;
  }
  #chat-container.theme-light .related-questions .related-question-item:hover {
    box-shadow: 0 0 0 2px rgba(17, 24, 39, 0.22) !important;
  }

  /* 亮色主题：更克制的科技感背景（浅灰/蓝色斜网格 + 轻微星点 + 柔和扫描光） */
  #chat-container.theme-light::before {
    mix-blend-mode: multiply;
    background-image: radial-gradient(
        800px 600px at -10% -10%,
        rgba(99, 102, 241, 0.1),
        transparent 60%
      ),
      radial-gradient(
        700px 500px at 110% 10%,
        rgba(59, 130, 246, 0.1),
        transparent 65%
      ),
      repeating-linear-gradient(
        45deg,
        rgba(17, 24, 39, 0.06) 0 2px,
        transparent 2px 36px
      ),
      repeating-linear-gradient(
        -45deg,
        rgba(17, 24, 39, 0.05) 0 2px,
        transparent 2px 36px
      ),
      radial-gradient(
        circle at 50% 50%,
        rgba(0, 0, 0, 0.025) 0 1px,
        transparent 1px 6px
      );
    background-size: 100% 100%, 100% 100%, 260px 260px, 260px 260px, 14px 14px;
    opacity: 0.45;
  }
  #chat-container.theme-light::after {
    background-image: linear-gradient(
      180deg,
      transparent 30%,
      rgba(59, 130, 246, 0.14) 50%,
      transparent 70%
    );
    mix-blend-mode: soft-light;
    opacity: 0.18;
  }
  /* 组合C — 光标能量尾焰 */
  .cursor-trail {
    position: fixed;
    left: 0;
    top: 0;
    width: 0;
    height: 0;
    pointer-events: none;
    z-index: 1;
  }
  .cursor-trail::before {
    content: '';
    position: fixed;
    left: var(--trail-x, -100px);
    top: var(--trail-y, -100px);
    width: 140px;
    height: 140px;
    transform: translate(-50%, -50%) scale(var(--trail-scale, 0.85));
    background: radial-gradient(
        84px 84px at 50% 50%,
        rgba(0, 230, 255, var(--trail-alpha, 0.16)),
        transparent 70%
      ),
      radial-gradient(
        54px 54px at 60% 40%,
        rgba(138, 43, 226, var(--trail-alpha, 0.12)),
        transparent 70%
      );
    filter: blur(14px) saturate(130%);
    mix-blend-mode: screen;
  }
  #chat-container.theme-light .cursor-trail::before {
    filter: blur(16px) saturate(120%);
    mix-blend-mode: multiply;
  }

  /* 组合C — 霓虹流光边框（关键模块） */
  .glow-frame {
    position: relative;
  }
  .glow-frame::after {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: inherit;
    pointer-events: none;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(0, 230, 255, 0.55),
      transparent
    );
    background-size: 300% 100%;
    animation: frameFlow 3.6s linear infinite;
    opacity: 0.66;
  }
  @keyframes frameFlow {
    0% {
      background-position: 0% 0;
    }
    100% {
      background-position: 300% 0;
    }
  }

  /* 应用到对话气泡与相关问题项 */
  .message.ai .bubble.glow-frame,
  .related-questions .related-question-item.glow-frame {
    box-shadow: 0 0 0 1px rgba(0, 230, 255, 0.28),
      0 0 16px rgba(0, 230, 255, 0.18);
  }
  #chat-container.theme-light .message.ai .bubble.glow-frame,
  #chat-container.theme-light
    .related-questions
    .related-question-item.glow-frame {
    box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.24),
      0 0 12px rgba(59, 130, 246, 0.14);
  }

  /* 组合C — 扫描线高亮出现动画（AI消息） */
  .message.ai .bubble {
    position: relative;
    overflow: hidden;
  }
  .message.ai .bubble.revealing::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
      180deg,
      rgba(0, 230, 255, 0) 0%,
      rgba(0, 230, 255, 0.18) 50%,
      rgba(0, 230, 255, 0) 100%
    );
    mix-blend-mode: screen;
    opacity: 0;
    transform: translateY(-60%);
    animation: revealScan 1.1s ease-out forwards; /* 首次出现扫过一次 */
  }
  @keyframes revealScan {
    0% {
      opacity: 0;
      transform: translateY(-60%);
    }
    40% {
      opacity: 0.35;
    }
    100% {
      opacity: 0;
      transform: translateY(60%);
    }
  }
</style>
