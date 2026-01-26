<template>
  <div class="chat2-container">
    <div class="navigation-container">
      <NavigationSidebar
        @toggle-history="showHistory = !showHistory"
        @start-new-chat="startNewChat"
      />
      <template v-if="isLoggedIn">
        <DialogHistory
          :class="{ 'hidden-history': !showHistory }"
          :groups="groupedHistory"
          :disabled="isLoading"
          @select="loadChat"
          @delete="deleteChat"
        />
      </template>
      <template v-else>
        <div :class="['history-empty', { 'hidden-history': !showHistory }]">
          <div class="history-empty-content">
            <img
              class="history-empty-icon"
              src="../assets/talk page/talk@3x_09.png"
              alt="未登录提示"
            />
            <p class="history-empty-tip">登录后可查看历史对话！</p>
          </div>
        </div>
      </template>
    </div>
    <div class="main-content">
      <div class="chat-container">
        <!-- 顶部固定的“新的对话”标签 -->
        <div class="chat-header-tag">{{ headerText }}</div>
        <!-- Empty State -->
        <div v-if="messages.length === 0" class="empty-chat-area">
          <div class="logo-placeholder">
            <img
              class="logo-image"
              src="@/assets/talk%20page/logo.png"
              alt="IBOX Materix"
            />
          </div>
          <h1 class="slogan">材料问题迎刃而解!</h1>
        </div>

        <!-- Messages Area -->
        <div
          v-else
          class="messages-area"
          ref="messagesArea"
          @scroll="onMessagesScroll"
        >
          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="[
              'message',
              message.sender === 'user' ? 'message-user' : 'message-ai',
            ]"
          >
            <div v-if="message.sender === 'user'">{{ message.content }}</div>
            <div v-else class="ai-message-content">
              <!-- 思考中加载状态 -->
              <div v-if="message._isLoading" class="thinking-indicator">
                <div class="thinking-dots">
                  <span class="thinking-text">🤔 思考中</span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
              <!-- 正常消息内容 -->
              <div v-else class="ai-text-content">
                <span v-html="renderMarkdown(message.content)"></span>
                <span
                  v-if="
                    isLoading &&
                    index === messages.length - 1 &&
                    message.content
                  "
                  class="typing-cursor"
                  >|</span
                >
              </div>
              <button
                v-if="
                  !message._isLoading &&
                  (!isLoading || index !== messages.length - 1)
                "
                class="copy-btn"
                :class="{ animate: message._copyAnimating }"
                @click="copyAiMessage(message)"
                :title="message._copied ? '已复制' : '复制'"
              >
                <img
                  v-if="!message._copied"
                  src="@/assets/talk%20page/talk@3_03.png"
                  alt="复制"
                  class="copy-icon"
                />
                <span v-else class="copy-check">☑</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 滚动到底部按钮：当未处于底部且有消息时显示 -->
        <button
          v-if="!isAtBottom && messages.length > 0"
          class="scroll-bottom-btn"
          @click="scrollToBottom"
          title="滚动到底部"
        >
          ↓
        </button>

        <!-- Input Box -->
        <div class="input-container">
          <div
            class="input-wrapper"
            :class="{ 'has-text': newMessage.trim() !== '' }"
          >
            <textarea
              v-model="newMessage"
              placeholder="向 IBOX Materix 提问"
              ref="questionTextarea"
              @input="handleInput"
              @keydown="handleKeydown"
              @focus="fetchSuggestions"
              @blur="clearSuggestions"
            ></textarea>
            <!-- 联想词列表 -->
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
            <div class="input-toolbar">
              <div class="toolbar-left">
                <div class="all-button-container">
                  <button class="tool-btn" @click="toggleAllDropdown">
                    <span>{{ selectedOption }}</span>
                    <img
                      class="all-icon"
                      src="@/assets/talk%20page/home@3_06.png"
                      alt="全部"
                      :class="{ rotated: isAllIconRotated }"
                    />
                  </button>
                  <div v-if="isAllDropdownVisible" class="dropdown-menu">
                    <div
                      v-for="option in options"
                      :key="option"
                      class="dropdown-item"
                      @click="selectOption(option)"
                    >
                      {{ option }}
                    </div>
                  </div>
                </div>
                <button
                  class="tool-btn"
                  :class="{ highlighted: isDeepThinkingActive }"
                  @click="toggleDeepThinking"
                >
                  <img
                    v-if="!isDeepThinkingActive"
                    src="@/assets/talk%20page/home@3_03.png"
                    alt="深度思考"
                  />
                  <img
                    v-else
                    src="@/assets/talk%20page/home@3X_07.png"
                    alt="深度思考"
                  />
                  <span>深度思考</span>
                </button>
              </div>
              <div class="toolbar-right">
                <button
                  class="send-button"
                  @click="sendMessage"
                  :disabled="isLoading || newMessage.trim() === ''"
                  :title="
                    isLoading
                      ? 'AI正在回复，无法发送'
                      : newMessage.trim() === ''
                        ? '请输入内容后再发送'
                        : '发送'
                  "
                >
                  <img
                    class="send-icon"
                    src="@/assets/talk%20page/talk@3X_18.png"
                    alt="发送"
                  />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import DialogHistory from './DialogHistory.vue'
  import NavigationSidebar from '@/components/NavigationSidebar.vue'
  import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { useUserStore } from '@/stores/user'
  import { useChatStore } from '@/stores/chat'
  import axios from 'axios'
  import { marked } from 'marked'
  import DOMPurify from 'dompurify'
  import 'katex/dist/katex.min.css'
  // Assuming katex-loader.js exists
  // import { loadKaTeX } from '../utils/katex-loader';
  import copy from 'copy-to-clipboard'

  export default {
    name: 'Chat',
    components: {
      DialogHistory,
      NavigationSidebar,
    },
    setup() {
      const route = useRoute()
      const router = useRouter()
      const messages = ref([]) // [{ content: string, sender: 'user' | 'ai' }]
      const newMessage = ref('')
      const headerText = ref('新的对话')
      const headerLocked = ref(false) // 仅首次消息后锁定顶部标签
      const isLoading = ref(false) // AI 回复进行中时禁用发送
      const isAllDropdownVisible = ref(false)
      const isAllIconRotated = ref(false)
      const isDeepThinkingActive = ref(false)
      const options = ['全部', '内部数据库', '外部数据库']
      const selectedOption = ref('全部')
      // 对话上下文ID（用于后端记忆）
      const currentChatId = ref(null)
      // 历史记录状态
      const chatHistory = ref([]) // 每项: { id, title, messages, timestamp, conversation_id }
      const isNewChat = ref(true)
      const currentChatIndex = ref(-1)

      // --- 联想词相关状态 ---
      const suggestions = ref([])
      const debounceTimer = ref(null)
      const selectedIndex = ref(-1)
      const questionTextarea = ref(null)
      const messagesArea = ref(null)
      const isAtBottom = ref(true)
      const chatStore = useChatStore()
      const scrollToBottom = () => {
        nextTick(() => {
          if (messagesArea.value) {
            messagesArea.value.scrollTop = messagesArea.value.scrollHeight
            updateIsAtBottom()
          }
        })
      }

      const SCROLL_THRESHOLD = 20 // 距底部 20px 内认为在底部
      const updateIsAtBottom = () => {
        if (!messagesArea.value) return
        const el = messagesArea.value
        isAtBottom.value =
          el.scrollHeight - el.scrollTop - el.clientHeight <= SCROLL_THRESHOLD
      }

      const onMessagesScroll = () => {
        updateIsAtBottom()
      }

      const copyAiMessage = (message) => {
        if (!message || !message.content) return
        try {
          copy(message.content)
          // 复制提示显示
          message._copied = true
          // 点击动效
          message._copyAnimating = true
          setTimeout(() => {
            message._copied = false
          }, 1200)
          setTimeout(() => {
            message._copyAnimating = false
          }, 300)
        } catch (e) {
          console.warn('复制失败:', e)
        }
      }

      const sendMessage = async () => {
        const text = newMessage.value.trim()
        if (text !== '') {
          messages.value.push({ content: text, sender: 'user' })
          // 发送后自动滚动到底部
          scrollToBottom()
          if (!headerLocked.value) {
            headerText.value = text
            headerLocked.value = true
          }
          newMessage.value = ''
          clearSuggestions()
          // 发送后保持输入框聚焦，便于继续输入，且让占位提示在空内容时可见
          nextTick(() => {
            if (questionTextarea.value) {
              questionTextarea.value.focus()
            }
          })

          // 首次用户消息后立即创建/更新历史项，确保侧栏立刻显示
          saveCurrentChat()

          console.log(
            '准备发送消息, currentChatId:',
            currentChatId.value,
            'type:',
            typeof currentChatId.value,
          )

          // 立即添加一个"思考中"的占位消息
          messages.value.push({
            content: '',
            sender: 'ai',
            _isLoading: true,
          })
          // 记录消息索引，用于后续更新（确保响应式）
          const aiMessageIndex = messages.value.length - 1
          // 滚动到底部显示思考中状态
          scrollToBottom()

          try {
            isLoading.value = true

            // 使用微信小程序SSE接口（使用相对路径，让 Vite 代理处理）
            const streamUrl = '/api/chat/wechat/stream/'

            // 构建请求体 - 符合微信小程序SSE接口格式
            const payload = {
              message: text,
              model: chatStore.selectedModel || 'deepseek',
              // 微信小程序接口使用 user_id 字段
              user_id: localStorage.getItem('user_id') || 'web_anonymous',
            }

            // 添加会话 ID
            if (
              currentChatId.value &&
              !String(currentChatId.value).startsWith('temp_')
            ) {
              payload.session_id =
                parseInt(currentChatId.value, 10) || currentChatId.value
            }

            console.log('微信小程序SSE请求 payload:', payload)

            // 发起流式请求
            const response = await fetch(streamUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                // 添加认证头（如果有）
                ...(localStorage.getItem('access_token')
                  ? {
                      Authorization: `Bearer ${localStorage.getItem(
                        'access_token',
                      )}`,
                    }
                  : {}),
              },
              body: JSON.stringify(payload),
            })

            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`)
            }

            const reader = response.body.getReader()
            const decoder = new TextDecoder()
            let buffer = ''
            let receivedFirstContent = false // 标记是否收到第一个内容块

            while (true) {
              const { done, value } = await reader.read()

              if (done) {
                console.log('微信小程序SSE流式响应接收完成')
                break
              }

              // 解码数据块
              buffer += decoder.decode(value, { stream: true })

              // 按行处理 SSE 数据
              const lines = buffer.split('\n')
              buffer = lines.pop() || '' // 保留未完成的行

              for (const line of lines) {
                if (line.startsWith('data: ')) {
                  const dataStr = line.slice(6).trim()

                  // 处理SSE结束标记
                  if (dataStr === '[DONE]') {
                    console.log('收到SSE结束标记 [DONE]')
                    continue
                  }

                  if (!dataStr) continue

                  try {
                    const data = JSON.parse(dataStr)

                    // 处理错误信息
                    if (data.error) {
                      console.error('SSE流式响应错误:', data.error)
                      messages.value[aiMessageIndex]._isLoading = false
                      messages.value[aiMessageIndex].content =
                        `错误: ${data.error}`
                      continue
                    }

                    // 处理会话 ID（在流开始时返回）
                    if (data.session_id && !data.content && !data.done) {
                      currentChatId.value = String(data.session_id)
                      console.log('更新 currentChatId:', currentChatId.value)
                      // 同时保存 conversation_id
                      if (data.conversation_id) {
                        console.log(
                          '收到 conversation_id:',
                          data.conversation_id,
                        )
                      }
                    }

                    // 处理内容块
                    if (data.content) {
                      // 收到第一个内容块时，切换为打字机模式
                      if (!receivedFirstContent) {
                        receivedFirstContent = true
                        messages.value[aiMessageIndex]._isLoading = false
                        messages.value[aiMessageIndex].content = ''
                      }
                      messages.value[aiMessageIndex].content += data.content
                      // 若当前在底部，则跟随滚动
                      if (isAtBottom.value) scrollToBottom()
                    }

                    // 处理完成信号
                    if (data.done) {
                      console.log('收到完成信号, message_id:', data.message_id)
                      // 更新最终的 session_id 和 conversation_id
                      if (data.session_id) {
                        currentChatId.value = String(data.session_id)
                      }
                    }
                  } catch (e) {
                    // 忽略解析错误，可能是不完整的 JSON
                    console.debug('解析 SSE 数据失败:', line, e)
                  }
                }
              }
            }

            // 如果没有收到任何内容，显示默认消息
            if (!messages.value[aiMessageIndex].content) {
              messages.value[aiMessageIndex]._isLoading = false
              messages.value[aiMessageIndex].content =
                '抱歉，未能获取到 AI 回复。'
            }

            isLoading.value = false
            // AI 回复完成后，更新历史记录
            saveCurrentChat()
          } catch (error) {
            console.error('Error fetching AI response:', error)
            // 更新占位消息为错误提示
            messages.value[aiMessageIndex]._isLoading = false
            messages.value[aiMessageIndex].content =
              '抱歉，AI 服务暂时不可用，请稍后重试。'
            isLoading.value = false
          }
          // 每次交互后保存当前会话状态
          saveToStorage()
          saveHistoryToStorage()
        }
      }

      const toggleAllDropdown = () => {
        isAllDropdownVisible.value = !isAllDropdownVisible.value
        isAllIconRotated.value = !isAllIconRotated.value
      }

      const selectOption = (option) => {
        selectedOption.value = option
        isAllDropdownVisible.value = false
        isAllIconRotated.value = false
      }

      const toggleDeepThinking = () => {
        isDeepThinkingActive.value = !isDeepThinkingActive.value
      }

      // --- 联想词相关逻辑 ---
      const handleKeydown = (event) => {
        // AI 回复过程中禁止发送（回车）
        if (isLoading.value && event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault()
          event.stopPropagation()
          return
        }
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
          } else if (event.key === 'Enter' && !event.shiftKey) {
            if (selectedIndex.value !== -1) {
              event.preventDefault()
              event.stopPropagation()
              selectSuggestion(suggestions.value[selectedIndex.value])
            } else {
              event.preventDefault()
              event.stopPropagation()
              sendMessage()
            }
          } else if (event.key === 'Escape') {
            event.preventDefault()
            clearSuggestions()
          }
        } else if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault()
          event.stopPropagation()
          sendMessage()
        }
      }

      const handleInput = () => {
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

        const scriptId = 'baidu-jsonp-script-chat'
        const existingScript = document.getElementById(scriptId)
        if (existingScript) {
          existingScript.remove()
        }

        const script = document.createElement('script')
        script.id = scriptId
        script.src = `https://suggestion.baidu.com/su?wd=${encodeURIComponent(
          query,
        )}&cb=window.handleBaiduSuggestionsChat`

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
          if (questionTextarea.value) {
            questionTextarea.value.focus()
          }
        })
      }

      const clearSuggestions = () => {
        setTimeout(() => {
          suggestions.value = []
          selectedIndex.value = -1
        }, 150)
      }

      const highlightQuery = (text) => {
        if (!newMessage.value.trim()) return text
        const query = newMessage.value.trim()
        const regex = new RegExp(
          `(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`,
          'gi',
        )
        return text.replace(regex, '<strong>$1</strong>')
      }

      // --- 本地存储：加载 / 保存当前会话（消息、标题、conversation_id） ---
      const getStorageKey = () => {
        return 'ai-chat2-session'
      }

      const loadFromStorage = () => {
        try {
          const raw = localStorage.getItem(getStorageKey())
          if (!raw) return
          const data = JSON.parse(raw)
          messages.value = Array.isArray(data.messages) ? data.messages : []
          headerText.value =
            typeof data.headerText === 'string' ? data.headerText : '新的对话'
          headerLocked.value = !!(messages.value && messages.value.length > 0)
          currentChatId.value = data.currentChatId || null
        } catch (err) {
          console.warn('加载会话存储失败:', err)
        }
      }

      const saveToStorage = () => {
        try {
          const data = {
            messages: messages.value,
            headerText: headerText.value,
            currentChatId: currentChatId.value,
          }
          localStorage.setItem(getStorageKey(), JSON.stringify(data))
        } catch (err) {
          console.warn('保存会话存储失败:', err)
        }
      }

      // --- 历史记录的本地存储 ---
      const getHistoryStorageKey = () => 'ai-chat2-history'
      const HISTORY_MAX_LENGTH = 100 // 历史保存长度上限，可按需调整

      const loadHistoryFromStorage = () => {
        try {
          const raw = localStorage.getItem(getHistoryStorageKey())
          chatHistory.value = raw ? JSON.parse(raw) : []
          if (
            Array.isArray(chatHistory.value) &&
            chatHistory.value.length > HISTORY_MAX_LENGTH
          ) {
            // 仅保留最新的 N 条（列表头部为最新）
            chatHistory.value = chatHistory.value.slice(0, HISTORY_MAX_LENGTH)
          }
        } catch (err) {
          console.warn('加载历史存储失败:', err)
          chatHistory.value = []
        }
      }

      const saveHistoryToStorage = () => {
        try {
          if (
            Array.isArray(chatHistory.value) &&
            chatHistory.value.length > HISTORY_MAX_LENGTH
          ) {
            chatHistory.value = chatHistory.value.slice(0, HISTORY_MAX_LENGTH)
          }
          localStorage.setItem(
            getHistoryStorageKey(),
            JSON.stringify(chatHistory.value),
          )
        } catch (err) {
          console.warn('保存历史存储失败:', err)
        }
      }

      // 保存当前对话到历史：避免刷新后继续发送造成重复创建
      const saveCurrentChat = () => {
        if (messages.value.length === 0) return

        // 先计算匹配用的标题与会话ID
        // 注意：只有在有真实 conversation_id 时才保存，避免使用临时ID
        const idCandidate = currentChatId.value || `temp_${Date.now()}`
        const titleCandidate =
          headerText.value ||
          messages.value[0]?.content?.substring(0, 20) + '...' ||
          '新对话'
        const conversationIdCandidate = currentChatId.value || null

        // 查找已存在的同一会话：优先通过 conversation_id，若无则用标题做近似匹配
        // 仅按 conversation_id 进行匹配；如果尚未分配，则不以标题进行去重
        let existingIndex = chatHistory.value.findIndex((h) => {
          return (
            !!conversationIdCandidate &&
            !!h.conversation_id &&
            h.conversation_id === conversationIdCandidate
          )
        })

        // 若找不到，但当前有选中的历史索引，则沿用该索引进行更新（避免在会话ID生成后重复创建新项）
        if (
          existingIndex === -1 &&
          currentChatIndex.value >= 0 &&
          currentChatIndex.value < chatHistory.value.length
        ) {
          existingIndex = currentChatIndex.value
        }

        // 如果已有记录，则沿用其 timestamp；否则使用当前时间
        const fixedTimestamp =
          existingIndex !== -1
            ? chatHistory.value[existingIndex].timestamp
            : new Date().toISOString()

        const chatData = {
          id: idCandidate,
          title: titleCandidate,
          messages: [...messages.value],
          timestamp: fixedTimestamp,
          conversation_id: conversationIdCandidate,
        }

        if (existingIndex !== -1) {
          // 更新已存在项（保持首条消息时间不变）
          chatHistory.value[existingIndex] = chatData
          currentChatIndex.value = existingIndex
          isNewChat.value = false
        } else {
          // 创建新历史项（首条消息时间为当前）
          chatHistory.value.unshift(chatData)
          currentChatIndex.value = 0
          isNewChat.value = false
        }

        // 进行长度裁剪，保留最新 N 条
        if (chatHistory.value.length > HISTORY_MAX_LENGTH) {
          chatHistory.value = chatHistory.value.slice(0, HISTORY_MAX_LENGTH)
        }
        saveHistoryToStorage()
      }

      // 日期标签与分组
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

      const getDayDiff = (iso) => {
        if (!iso) return 0
        const target = new Date(iso)
        const now = new Date()
        const startOfDay = (d) =>
          new Date(d.getFullYear(), d.getMonth(), d.getDate())
        const diffMs = startOfDay(now) - startOfDay(target)
        return Math.floor(diffMs / (1000 * 60 * 60 * 24))
      }

      const groupedHistory = computed(() => {
        const groupsMap = new Map()
        chatHistory.value.forEach((chat, idx) => {
          const label = getRelativeDayLabel(chat.timestamp)
          const key = label || '今天'
          if (!groupsMap.has(key)) groupsMap.set(key, [])
          groupsMap.get(key).push({ ...chat, index: idx })
        })
        const entries = Array.from(groupsMap.entries()).map(
          ([label, items]) => ({
            label,
            days: getDayDiff(items[0]?.timestamp),
            items,
          }),
        )
        entries.sort((a, b) => a.days - b.days)
        return entries
      })

      // Markdown 渲染与安全过滤
      marked.setOptions({ gfm: true, breaks: true })
      const renderMarkdown = (text) => {
        if (!text) return ''

        // 处理 <think> 标签，将其转换为可折叠的思考过程区块
        let processedText = text.replace(
          /<think>([\s\S]*?)<\/think>/g,
          (match, thinkContent) => {
            const thinkId = 'think-' + Math.random().toString(36).substr(2, 9)
            return `
<details class="think-block">
  <summary class="think-summary">🧠 AI 思考过程...点击展开</summary>
  <div class="think-content">${thinkContent.trim()}</div>
</details>
`
          },
        )

        const safe = DOMPurify.sanitize(marked.parse(processedText))
        return safe
      }

      onMounted(() => {
        // 先从本地存储恢复会话
        loadFromStorage()
        loadHistoryFromStorage()
        // 初始化底部状态
        nextTick(() => updateIsAtBottom())
        window.handleBaiduSuggestionsChat = (data) => {
          suggestions.value = data.s || []
          selectedIndex.value = -1
        }

        // 从首页携带的查询参数触发一次提问与AI回复
        const q =
          typeof route?.query?.prompt === 'string'
            ? route.query.prompt.trim()
            : ''
        if (q) {
          // 从首页进入时，先新建一个会话
          startNewChat()
          newMessage.value = q
          // 深度思考开关：'1' 为开启
          if (route?.query?.deep === '1') {
            isDeepThinkingActive.value = true
          }
          // 数据源选择：all/internal/external 映射到标签
          const src = route?.query?.source
          if (src === 'internal') selectedOption.value = '内部数据库'
          else if (src === 'external') selectedOption.value = '外部数据库'
          else selectedOption.value = '全部'
          // 发送并让AI回复
          nextTick(() => {
            sendMessage()
          })
        }
      })

      onUnmounted(() => {
        delete window.handleBaiduSuggestionsChat
        const scriptId = 'baidu-jsonp-script-chat'
        const existingScript = document.getElementById(scriptId)
        if (existingScript && existingScript.parentNode) {
          existingScript.parentNode.removeChild(existingScript)
        }
      })

      // 新建对话：重置消息、标题、conversation_id 并保存
      const startNewChat = (isDeletion = false) => {
        if (messages.value.length > 0 && !isDeletion) {
          // 先保存当前对话到历史
          saveCurrentChat()
        }
        messages.value = []
        headerText.value = '新的对话'
        headerLocked.value = false
        currentChatId.value = null
        isNewChat.value = true
        currentChatIndex.value = -1
        saveToStorage()
      }

      // 点击历史记录，加载指定对话
      const loadChat = (index) => {
        if (isLoading.value) {
          // AI 正在回复，禁止切换历史记录
          return
        }
        if (messages.value.length > 0 && isNewChat.value) {
          // 若当前是未保存的新对话，先保存
          saveCurrentChat()
        }
        const chatData = chatHistory.value[index]
        if (!chatData) return
        messages.value = [...chatData.messages]
        headerText.value = chatData.title || '新的对话'
        headerLocked.value = messages.value.length > 0
        currentChatIndex.value = index
        // 只使用真实的 conversation_id，忽略临时ID
        currentChatId.value =
          chatData.conversation_id &&
          !String(chatData.conversation_id).startsWith('temp_')
            ? String(chatData.conversation_id)
            : null
        isNewChat.value = false
        saveToStorage()
        // 切换到历史对话后，默认滚动到聊天底部
        scrollToBottom()
      }

      // 删除指定历史对话
      const deleteChat = (index) => {
        if (index < 0 || index >= chatHistory.value.length) return
        const isDeletingCurrent = currentChatIndex.value === index
        chatHistory.value.splice(index, 1)
        if (isDeletingCurrent) {
          startNewChat(true) // 传入 true，表示由删除触发
        } else if (currentChatIndex.value > index) {
          currentChatIndex.value--
        }
        saveHistoryToStorage()
      }

      return {
        messages,
        newMessage,
        headerText,
        headerLocked,
        isLoading,
        messagesArea,
        isAtBottom,
        isAllDropdownVisible,
        isAllIconRotated,
        isDeepThinkingActive,
        options,
        selectedOption,
        suggestions,
        selectedIndex,
        questionTextarea,
        sendMessage,
        startNewChat,
        loadChat,
        deleteChat,
        scrollToBottom,
        onMessagesScroll,
        copyAiMessage,
        toggleAllDropdown,
        selectOption,
        toggleDeepThinking,
        handleKeydown,
        handleInput,
        fetchSuggestions,
        selectSuggestion,
        clearSuggestions,
        highlightQuery,
        renderMarkdown,
        groupedHistory,
        router,
      }
    },
    data() {
      return {
        // from chat2.vue
        showHistory: true,
      }
    },
    computed: {
      // 使用 Pinia store 的状态
      isLoggedIn() {
        const userStore = useUserStore()
        return userStore.isAuthenticated
      },
      username() {
        const userStore = useUserStore()
        return userStore.user?.username || ''
      },
      isAdmin() {
        const userStore = useUserStore()
        return userStore.user?.profile?.role === 'ADMIN'
      },
    },
    methods: {
      async fetchUserData() {
        // 从 store 获取用户信息
        const userStore = useUserStore()
        if (userStore.isAuthenticated && !userStore.user) {
          // 如果已认证但没有用户信息，则获取
          await userStore.fetchUserInfo()
        }
      },
    },
    mounted() {
      this.fetchUserData()
      // 调试信息
      const userStore = useUserStore()
      console.log('=== Chat.vue 挂载时的认证状态 ===')
      console.log('isAuthenticated:', userStore.isAuthenticated)
      console.log('isLoggedIn:', userStore.isLoggedIn)
      console.log('user:', userStore.user)
      console.log('accessToken:', userStore.accessToken ? '已存在' : '不存在')
      console.log('isAdmin:', this.isAdmin)
    },
  }
</script>

<style scoped>
  .chat2-container {
    display: flex;
    height: 100%;
  }

  .navigation-container {
    display: flex;
    flex-shrink: 0; /* Prevent shrinking */
    box-shadow: none;
  }

  .main-content {
    flex-grow: 1;
    padding: 20px;
    display: flex;
    flex-direction: column;
  }

  .chat-container {
    max-width: 1024px; /* 设置最大宽度 */
    margin: 0 auto; /* 左右外边距自动，实现居中 */
    display: flex;
    flex-direction: column;
    height: 100%;
    justify-content: flex-start; /* 顶部开始排列，便于精确控制间距 */
    position: relative; /* 便于定位滚到底部按钮 */
  }

  .empty-chat-area {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    color: #333;
    margin-top: 200px; /* 整体距离页面顶部 400px */
    margin-bottom: 0; /* 紧跟其后的输入框由相邻选择器控制距离 */
  }

  .logo-placeholder {
    font-size: 48px;
    font-weight: bold;
    margin-bottom: 16px;
    position: relative; /* 作为“新的对话”定位参照 */
  }

  .logo-box {
    background-color: #3d82f5;
    color: white;
    padding: 5px 10px;
    border-radius: 8px;
  }

  .logo-materix {
    color: #3d82f5;
  }

  .logo-image {
    height: 48px;
  }

  .chat-header-tag {
    text-align: center;
    padding: 10px 0;
    font-size: 16px;
    font-weight: 400;
    color: #1a1a1a;
    background: transparent;
    /* 限制长度并不允许换行 */
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 700px;
    margin: 0 auto;
    position: absolute; /* 固定在容器顶部，不随内容推移 */
    top: 0;
    left: 0;
    right: 0;
    z-index: 3;
  }

  .slogan {
    font-size: 50px;
    font-weight: 700;
    color: #1a1a1a;
    margin-top: 6px; /* 更贴近上方 logo */
    margin-bottom: 10px; /* 下方略留白 */
  }

  .messages-area {
    flex-grow: 1;
    padding: 20px;
    margin-top: 44px; /* 预留顶部标签空间，避免被覆盖 */
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .scroll-bottom-btn {
    position: absolute;
    right: 450px;
    bottom: 250px; /* 避开输入框 */
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: rgba(64, 158, 255, 0.95);
    color: #fff;
    border: none;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.18);
    cursor: pointer;
    z-index: 10;
  }

  .scroll-bottom-btn:hover {
    background: #4997ff;
  }

  .input-container {
    padding: 20px;
    background-color: transparent;
    margin-top: 0; /* 默认不推到底部，由空状态相邻选择器控制 */
  }

  /* 空状态下：输入框放在“logo+标语”整体下方 100px */
  .empty-chat-area + .input-container {
    margin-top: 100px;
  }

  /* 空状态下：当输入框紧随“空状态”区域时，缩小与标语的间距并上移 */
  .empty-chat-area + .input-container {
    margin-top: 20px; /* 覆盖默认的 auto，使输入框更靠近标语 */
  }

  .input-wrapper {
    width: 860px;
    height: 160px;
    background-color: transparent;
    border: 1px solid #dcdfe6; /* Outer circle line color */
    border-radius: 30px;
    padding: 15px;
    margin: 0 auto; /* Center the input box */
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative; /* Enable absolute positioning for toolbar children */
  }

  .input-wrapper:focus-within {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }

  /* 当输入框有文本时，外框边框颜色变为蓝色 */
  .input-wrapper.has-text {
    border-color: #4997ff;
  }

  /* 联想词列表样式 */
  .suggestions-list {
    position: absolute;
    bottom: 100%;
    left: 15px;
    right: 15px;
    margin-bottom: 8px; /* 与输入框的间距 */
    z-index: 10;
    background: rgba(255, 255, 255, 0.92);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: 12px;
    box-shadow: 0 8px 18px rgba(0, 0, 0, 0.12);
    max-height: 220px;
    overflow-y: auto;
  }
  .suggestions-list ul {
    list-style: none;
    padding: 6px;
    margin: 0;
  }
  .suggestions-list li {
    padding: 8px 10px;
    font-size: 14px;
    color: #1f2937;
    cursor: pointer;
    border-radius: 8px;
  }
  .suggestions-list li:hover,
  .suggestions-list li.selected {
    background: rgba(91, 141, 239, 0.14);
    color: #0b122e;
  }

  textarea {
    width: 100%;
    border: none;
    resize: none;
    font-size: 16px;
    padding: 10px;
    box-sizing: border-box;
    background-color: transparent;
    flex-grow: 1;
  }

  textarea:focus {
    outline: none;
  }

  /* 保证在输入为空时占位提示可见，含获得焦点状态 */
  textarea::placeholder {
    color: #9aa4b2;
    opacity: 1;
  }
  textarea:focus::placeholder {
    opacity: 1;
  }

  .input-toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .toolbar-left {
    display: flex;
    gap: 10px;
    align-items: center;
    position: absolute;
    bottom: 15px;
    left: 15px;
  }

  .toolbar-right {
    position: absolute;
    bottom: 15px;
    right: 15px;
  }

  .all-button-container {
    position: relative;
  }

  .tool-btn {
    background: #f0f2f5; /* Match chat box inner color */
    border: none; /* Match chat box outer frame color */
    padding: 5px 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 5px;
    border-radius: 30px;
  }

  .tool-btn img {
    width: 24px;
    height: 24px;
    transition:
      transform 0.3s ease,
      filter 0.3s ease;
  }
  .tool-btn .all-icon {
    width: 21.6px; /* 24px * 0.9 */
    height: 21.6px; /* 24px * 0.9 */
  }

  .tool-btn img.rotated {
    transform: rotate(-90deg);
  }

  .tool-btn.highlighted {
    background-color: #0056b3; /* menu highlight tone */
    color: #ffffff;
    border-color: #1a1a1a; /* keep outer ring consistent */
  }

  .tool-btn.highlighted span {
    color: #ffffff;
    font-weight: 600;
  }

  .dropdown-menu {
    position: absolute;
    bottom: 100%;
    left: 0;
    background-color: white;
    border: 1px solid #e0e0e0;
    border-radius: 30px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    padding: 5px;
    margin-bottom: 10px;
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 120px;
  }

  .dropdown-item {
    padding: 8px 12px;
    cursor: pointer;
    white-space: nowrap;
    transition: background-color 0.2s ease;
  }

  .dropdown-item:hover {
    background-color: #f0f2f5;
  }

  .send-button {
    background-color: #409eff;
    color: white;
    border: none;
    border-radius: 50%;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
  }

  .send-icon {
    width: 40px;
    height: 40px;
  }

  /* 消息气泡基础样式 */
  .message {
    border: 1px solid #e0e0e0;
    border-radius: 16px;
    padding: 10px 12px;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
    background: #ffffff;
    overflow-wrap: break-word;
  }

  /* 左侧（AI/系统）消息样式 */
  .message-ai {
    align-self: flex-start;
    max-width: 880px;
    background: transparent;
    border: none;
    padding: 10px 0;
    position: relative;
  }

  /* 右侧（用户）消息样式 */
  .message-user {
    align-self: flex-end;
    background: #bae1f3; /* 浅蓝色背景 */
    color: #333; /* 浅色背景下使用深色文字增强可读性 */
    border: none;
    max-width: 700px; /* 限制最大宽度为700px，超出自动换行 */
  }

  :deep(.dialog-history-container) {
    width: 336px !important;
    position: relative;
    z-index: 10001; /* 提升到最高层，避免被任何浮层覆盖 */
  }

  .hidden-history {
    visibility: hidden;
  }

  /* 未登录时：历史对话空态 */
  .history-empty {
    width: 336px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .history-empty-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    width: 100%;
    padding-top: 10px; /* 整体上移，居中偏上一点 */
    transform: translateY(-80px); /* 进一步整体上移100px */
  }
  .history-empty-icon {
    width: 72px;
    height: 72px;
    opacity: 0.9;
  }
  .history-empty-tip {
    margin-top: 16px;
    color: #9aa0a6; /* 次要提示色 */
    font-size: 14px;
  }
  .history-login-link {
    margin-top: 30px; /* 进一步增大与提示语的间距 */
    font-size: 16px; /* 调小字体以更精致紧凑 */
    color: #3b82f6; /* 蓝色文本 */
    cursor: pointer;
  }
  .history-register {
    margin-top: 5px;
    font-size: 16px; /* 调小字体以更精致紧凑 */
    color: #3b82f6; /* 蓝色 */
    cursor: pointer;
  }

  /* AI 消息复制按钮 */
  .copy-btn {
    position: absolute;
    left: -3px;
    bottom: -3px;
    border: none;
    background: transparent;
    padding: 0;
    cursor: pointer;
  }
  .copy-icon {
    width: 20px;
    height: 20px;
    opacity: 0.9;
  }
  .copy-check {
    display: inline-block;
    font-size: 30px;
    line-height: 20px;
    color: #080808; /* 成功提示色 */
  }

  /* 点击动效：图标/√ 轻微弹跳 */
  .copy-btn.animate .copy-icon,
  .copy-btn.animate .copy-check {
    animation: pop 250ms ease;
  }
  @keyframes pop {
    0% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.2);
    }
    100% {
      transform: scale(1);
    }
  }

  /* 悬停提示气泡样式，仅在鼠标放上登录/注册时显示 */
  .tooltip-link {
    position: relative;
    display: inline-block;
    padding: 6px 12px; /* 为文字本身的高亮留出内边距 */
    border-radius: 999px; /* 圆角形状包裹文字 */
    border: 1px solid transparent; /* 常驻边框，避免 hover 时尺寸变化导致抖动 */
    transition:
      background-color 0.2s ease,
      color 0.2s ease,
      box-shadow 0.2s ease,
      border-color 0.2s ease;
    width: 200px; /* 固定长度为200px */
    box-sizing: border-box; /* 保证包含内边距后总宽度仍为200px */
    text-align: center; /* 文本居中显示 */
    white-space: nowrap; /* 防止文本换行 */
    margin-left: auto; /* 在父容器中水平居中 */
    margin-right: auto; /* 保留左右居中，不影响上方自定义间距 */
  }
  /* 删除上方气泡提示，保留文字本身的悬停高亮效果 */

  /* 悬停时：对文字本身进行蓝色圆角描边与填充高亮 */
  .tooltip-link:hover {
    background: #3b82f6;
    color: #fff;
    border: 1px solid #93c5fd;
    box-shadow: 0 6px 14px rgba(59, 130, 246, 0.25);
  }

  /* AI 思考过程区块样式 */
  :deep(.think-block) {
    margin: 12px 0;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    background: #f9fafb;
    overflow: hidden;
  }

  :deep(.think-summary) {
    padding: 10px 14px;
    cursor: pointer;
    user-select: none;
    font-weight: 500;
    color: #6b7280;
    background: #f3f4f6;
    border-bottom: 1px solid #e5e7eb;
    transition: background-color 0.2s ease;
    list-style: none;
  }

  :deep(.think-summary::-webkit-details-marker) {
    display: none;
  }

  :deep(.think-summary):hover {
    background: #e5e7eb;
    color: #374151;
  }

  :deep(.think-block[open] .think-summary) {
    background: #e0e7ff;
    color: #4f46e5;
    border-bottom-color: #c7d2fe;
  }

  :deep(.think-content) {
    padding: 14px;
    color: #4b5563;
    font-size: 13px;
    line-height: 1.6;
    white-space: pre-wrap;
    background: #ffffff;
  }

  /* 思考中加载动画样式 */
  .thinking-indicator {
    display: flex;
    align-items: center;
    padding: 12px 16px;
    background: linear-gradient(135deg, #f0f7ff 0%, #e8f4fd 100%);
    border-radius: 12px;
    border: 1px solid #d0e3f7;
  }

  .thinking-dots {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .thinking-text {
    font-size: 14px;
    color: #4a90d9;
    font-weight: 500;
    margin-right: 8px;
  }

  .thinking-dots .dot {
    width: 8px;
    height: 8px;
    background-color: #4a90d9;
    border-radius: 50%;
    animation: thinking-bounce 1.4s ease-in-out infinite;
  }

  .thinking-dots .dot:nth-child(2) {
    animation-delay: 0.16s;
  }

  .thinking-dots .dot:nth-child(3) {
    animation-delay: 0.32s;
  }

  .thinking-dots .dot:nth-child(4) {
    animation-delay: 0.48s;
  }

  @keyframes thinking-bounce {
    0%,
    80%,
    100% {
      transform: scale(0.6);
      opacity: 0.5;
    }
    40% {
      transform: scale(1);
      opacity: 1;
    }
  }

  /* 打字机光标效果 */
  .ai-text-content {
    display: inline;
  }

  .typing-cursor {
    display: inline-block;
    color: #4a90d9;
    font-weight: bold;
    animation: blink 0.8s ease-in-out infinite;
    margin-left: 2px;
  }

  @keyframes blink {
    0%,
    50% {
      opacity: 1;
    }
    51%,
    100% {
      opacity: 0;
    }
  }
</style>
