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
              src="../../assets/talk page/talk@3x_09.png"
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
              <div
                v-if="
                  message._isLoading &&
                  !message.content &&
                  !message.thinkingContent
                "
                class="thinking-indicator"
              >
                <div class="thinking-dots">
                  <span class="thinking-text">{{
                    message._stageText || '🤔 思考中'
                  }}</span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
              <!-- 聚合模式：汇总阶段提示（不再 loading 但内容还未开始） -->
              <div
                v-else-if="message._stageText && !message.content"
                class="thinking-indicator"
              >
                <div class="thinking-dots">
                  <span class="thinking-text">{{ message._stageText }}</span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
              <!-- 正常消息内容 -->
              <div v-else class="ai-text-content">
                <details v-if="message.thinkingContent" class="think-block">
                  <summary class="think-summary">
                    🧠 AI 思考过程...点击展开
                  </summary>
                  <div
                    class="think-content"
                    v-html="renderMarkdown(message.thinkingContent)"
                  ></div>
                </details>
                <div v-html="renderMarkdown(message.content)"></div>
                <div
                  v-if="
                    message.sourcesReady &&
                    message.sources &&
                    message.sources.length
                  "
                  class="web-sources"
                >
                  <div class="web-sources-title">🌐 参考网页</div>
                  <a
                    v-for="(source, sourceIndex) in message.sources"
                    :key="`${source.url}-${sourceIndex}`"
                    class="web-source-item"
                    :href="source.url"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <span class="web-source-index">{{ sourceIndex + 1 }}</span>
                    <span class="web-source-title">{{
                      source.title || source.url
                    }}</span>
                    <span class="web-source-url">{{ source.url }}</span>
                  </a>
                </div>
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
                <button
                  class="tool-btn"
                  :class="{ highlighted: isAggregateMode }"
                  @click="toggleAggregateMode"
                  title="启用后由Dify聚合编排处理（默认关闭）"
                  :aria-pressed="isAggregateMode"
                >
                  <span>聚合模式</span>
                </button>
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

                <!-- 联网搜索开关（默认关闭） -->
                <button
                  class="tool-btn"
                  :class="{ highlighted: isWebSearchActive }"
                  @click="toggleWebSearch"
                  title="启用后AI将尝试联网检索外部信息（默认关闭）"
                >
                  <svg
                    class="web-search-icon"
                    viewBox="0 0 24 24"
                    role="img"
                    :aria-label="
                      isWebSearchActive ? '联网搜索开启' : '联网搜索关闭'
                    "
                  >
                    <circle cx="10.5" cy="10.5" r="6.5" />
                    <path d="M15.5 15.5 21 21" />
                    <path d="M4 10.5h13M10.5 4a10.5 10.5 0 0 1 0 13" />
                  </svg>
                  <span>联网搜索</span>
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
      const isDeepThinkingActive = ref(false)
      const isWebSearchActive = ref(false)
      // 聚合模式与联网搜索一样是独立开关，默认关闭即普通问答。
      const isAggregateMode = ref(false)
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
            thinkingContent: '',
            _rawContent: '',
            sources: [],
            sourcesReady: false,
            sender: 'ai',
            _isLoading: true,
          })
          // 记录消息索引，用于后续更新（确保响应式）
          const aiMessageIndex = messages.value.length - 1
          // 滚动到底部显示思考中状态
          scrollToBottom()

          try {
            isLoading.value = true

            const aggregateMode = isAggregateMode.value
            const streamUrl = aggregateMode
              ? '/api/chat/aggregate/stream/'
              : '/api/chat/wechat/stream/'

            const payload = aggregateMode
              ? {
                  message: text,
                  user_id: localStorage.getItem('user_id') || 'web_anonymous',
                  web_search: isWebSearchActive.value,
                  Aggregation: 'yes',
                  ...(currentChatId.value &&
                  !String(currentChatId.value).startsWith('temp_')
                    ? {
                        session_id:
                          parseInt(currentChatId.value, 10) ||
                          currentChatId.value,
                      }
                    : {}),
                }
              : {
                  message: text,
                  web_search: isWebSearchActive.value,
                  user_id: localStorage.getItem('user_id') || 'web_anonymous',
                  ...(currentChatId.value &&
                  !String(currentChatId.value).startsWith('temp_')
                    ? {
                        session_id:
                          parseInt(currentChatId.value, 10) ||
                          currentChatId.value,
                      }
                    : {}),
                }

            console.log(
              'SSE 请求 payload:',
              payload,
              '聚合模式:',
              aggregateMode,
            )

            const response = await fetch(streamUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(localStorage.getItem('access_token')
                  ? {
                      Authorization: `Bearer ${localStorage.getItem('access_token')}`,
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
            let receivedFirstContent = false

            while (true) {
              const { done, value } = await reader.read()
              if (done) break

              buffer += decoder.decode(value, { stream: true })
              const lines = buffer.split('\n')
              buffer = lines.pop() || ''

              for (const line of lines) {
                if (!line.startsWith('data: ')) continue
                const dataStr = line.slice(6).trim()
                if (dataStr === '[DONE]' || !dataStr) continue

                try {
                  const data = JSON.parse(dataStr)

                  if (data.error) {
                    messages.value[aiMessageIndex]._isLoading = false
                    messages.value[aiMessageIndex]._stageText = ''
                    messages.value[aiMessageIndex].content =
                      `错误: ${data.error}`
                    continue
                  }

                  // 使用本次请求开始时固定的布尔值，不能直接判断 Vue ref；
                  // ref 对象本身始终为真，会导致普通 SSE 被误判为聚合 SSE。
                  if (aggregateMode) {
                    // ---- 聚合模式 SSE 处理 ----
                    if (data.stage === 'collecting') {
                      if (data.session_id)
                        currentChatId.value = String(data.session_id)
                      messages.value[aiMessageIndex]._stageText =
                        '🔄 正在向所有模型提问...'
                    } else if (data.stage === 'model_done') {
                      const doneCount =
                        Object.keys(
                          messages.value[aiMessageIndex]._modelResults || {},
                        ).length + 1
                      if (!messages.value[aiMessageIndex]._modelResults)
                        messages.value[aiMessageIndex]._modelResults = {}
                      messages.value[aiMessageIndex]._modelResults[data.model] =
                        data.content
                      messages.value[aiMessageIndex]._stageText =
                        `⏳ 已收到 ${doneCount} 个模型回复，等待其余模型...`
                    } else if (data.stage === 'summarizing') {
                      messages.value[aiMessageIndex]._isLoading = false
                      messages.value[aiMessageIndex]._stageText =
                        '🔄 正在优化汇总...'
                    } else if (data.stage === 'answer') {
                      if (
                        aggregateMode &&
                        ['yes', 'no', 'true', 'false', 'null'].includes(
                          String(data.content || '')
                            .trim()
                            .toLowerCase(),
                        )
                      ) {
                        continue
                      }
                      if (!receivedFirstContent) {
                        receivedFirstContent = true
                        messages.value[aiMessageIndex]._stageText = ''
                        messages.value[aiMessageIndex].content = ''
                      }
                      appendStreamContent(
                        messages.value[aiMessageIndex],
                        data.content,
                      )
                      if (isAtBottom.value) scrollToBottom()
                    } else if (data.stage === 'done') {
                      if (data.session_id)
                        currentChatId.value = String(data.session_id)
                    }
                    if (Array.isArray(data.sources)) {
                      messages.value[aiMessageIndex].sources = mergeSources(
                        messages.value[aiMessageIndex].sources,
                        data.sources,
                      )
                    }
                  } else {
                    // ---- 普通模式 SSE 处理（原有逻辑）----
                    if (data.session_id && !data.content && !data.done) {
                      currentChatId.value = String(data.session_id)
                    }
                    // 普通模式正文由后端统一转成 content；同时兼容旧接口
                    // 直接返回 answer/text/output 的情况。
                    const streamContent = extractSseContent(data)
                    if (streamContent) {
                      if (!receivedFirstContent) {
                        receivedFirstContent = true
                        messages.value[aiMessageIndex]._isLoading = false
                        messages.value[aiMessageIndex].content = ''
                      }
                      appendStreamContent(
                        messages.value[aiMessageIndex],
                        typeof streamContent === 'string'
                          ? streamContent
                          : JSON.stringify(streamContent),
                      )
                      if (isAtBottom.value) scrollToBottom()
                    }
                    if (Array.isArray(data.sources)) {
                      messages.value[aiMessageIndex].sources = mergeSources(
                        messages.value[aiMessageIndex].sources,
                        data.sources,
                      )
                    }
                    if (data.done && data.session_id) {
                      currentChatId.value = String(data.session_id)
                    }
                    if (data.done) {
                      messages.value[aiMessageIndex]._isLoading = false
                      messages.value[aiMessageIndex]._stageText = ''
                    }
                  }
                } catch (e) {
                  console.debug('解析 SSE 数据失败:', line, e)
                }
              }
            }

            // reader 结束时可能还有一条没有以换行符结尾的 SSE 数据。
            // 这里补处理最后的 data 行，避免正文只出现在 Network 而未进入页面。
            const lastLine = buffer.trim()
            if (lastLine.startsWith('data: ')) {
              const dataStr = lastLine.slice(6).trim()
              if (dataStr && dataStr !== '[DONE]') {
                try {
                  const data = JSON.parse(dataStr)
                  if (!aggregateMode && !data.error) {
                    const streamContent = extractSseContent(data)
                    if (streamContent) {
                      receivedFirstContent = true
                      messages.value[aiMessageIndex]._isLoading = false
                      appendStreamContent(
                        messages.value[aiMessageIndex],
                        typeof streamContent === 'string'
                          ? streamContent
                          : JSON.stringify(streamContent),
                      )
                    }
                    if (data.done && data.session_id) {
                      currentChatId.value = String(data.session_id)
                    }
                  }
                } catch (e) {
                  console.debug('解析 SSE 末尾数据失败:', lastLine, e)
                }
              }
            }

            const finalContent = messages.value[aiMessageIndex].content || ''
            messages.value[aiMessageIndex].sources = mergeSources(
              messages.value[aiMessageIndex].sources,
              extractSourcesFromText(finalContent),
            )
            messages.value[aiMessageIndex].sourcesReady = true

            if (
              !messages.value[aiMessageIndex].content &&
              !messages.value[aiMessageIndex].thinkingContent &&
              !messages.value[aiMessageIndex]._rawContent &&
              !receivedFirstContent
            ) {
              messages.value[aiMessageIndex]._isLoading = false
              messages.value[aiMessageIndex]._stageText = ''
              messages.value[aiMessageIndex].content =
                '抱歉，未能获取到 AI 回复。'
            }

            isLoading.value = false
            saveCurrentChat()
          } catch (error) {
            console.error('Error fetching AI response:', error)
            messages.value[aiMessageIndex]._isLoading = false
            messages.value[aiMessageIndex]._stageText = ''
            messages.value[aiMessageIndex].content =
              '抱歉，AI 服务暂时不可用，请稍后重试。'
            isLoading.value = false
          }
          // 每次交互后保存当前会话状态
          saveToStorage()
          saveHistoryToStorage()
        }
      }

      const toggleWebSearch = () => {
        isWebSearchActive.value = !isWebSearchActive.value
      }

      // 兼容不同 Dify 应用返回的正文位置。
      const extractSseContent = (data) => {
        if (!data || typeof data !== 'object') return ''
        const directValue =
          data.content ?? data.answer ?? data.text ?? data.output
        if (typeof directValue === 'string' && directValue) return directValue
        if (directValue && typeof directValue !== 'object') {
          return String(directValue)
        }
        if (typeof data.message === 'string' && data.message) {
          return data.message
        }
        const nested = data.outputs ?? data.data ?? data.message
        if (nested && typeof nested === 'object') {
          return extractSseContent(nested)
        }
        return ''
      }

      const appendStreamContent = (message, chunk) => {
        if (!chunk) return
        message._rawContent = `${message._rawContent || ''}${chunk}`
        const raw = message._rawContent
        const openTag = '<think>'
        const closeTag = '</think>'
        const openIndex = raw.indexOf(openTag)
        const closeIndex = raw.indexOf(closeTag)

        if (openIndex >= 0) {
          const endIndex = closeIndex >= openIndex ? closeIndex : raw.length
          message.thinkingContent = raw.slice(
            openIndex + openTag.length,
            endIndex,
          )
          message.content =
            closeIndex >= openIndex
              ? raw.slice(closeIndex + closeTag.length)
              : ''
          return
        }

        // Some Dify streams omit the opening tag but still emit </think>.
        if (closeIndex >= 0) {
          message.thinkingContent = raw.slice(0, closeIndex)
          message.content = raw.slice(closeIndex + closeTag.length)
          return
        }

        message.content = raw
      }

      const mergeSources = (existing = [], incoming = []) => {
        const merged = [...existing, ...incoming].filter(
          (source) => source && source.url,
        )
        return Array.from(
          new Map(merged.map((source) => [source.url, source])).values(),
        )
      }

      const extractSourcesFromText = (text = '') => {
        const sources = []
        const markdownLinkPattern = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g
        const urlPattern = /https?:\/\/[^\s<>)\]"']+/g
        let match

        while ((match = markdownLinkPattern.exec(text))) {
          sources.push({ title: match[1].trim(), url: match[2] })
        }
        while ((match = urlPattern.exec(text))) {
          const url = match[0].replace(/[.,;:!?，。；：！？]+$/, '')
          if (!sources.some((source) => source.url === url)) {
            sources.push({ title: url, url })
          }
        }
        return sources
      }

      const toggleAggregateMode = () => {
        isAggregateMode.value = !isAggregateMode.value
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
      marked.setOptions({
        gfm: true,
        breaks: true,
        pedantic: false,
      })
      const renderMarkdown = (text) => {
        if (!text) return ''

        // 来源统一由底部“参考网页”区域展示，避免正文和来源区域重复。
        const answerOnlyText = String(text).replace(
          /(?:^|\n)\s*(?:#{1,6}\s*)?(?:参考网页|参考来源|来源|sources|references)\s*:?\s*[\s\S]*$/i,
          '',
        )

        // Dify/模型输出中偶尔会生成 "####标题"，标准 Markdown 要求标题符号后有空格。
        // 同时统一换行，避免流式分片造成标题和段落粘连。
        let normalizedText = answerOnlyText
          .replace(/\r\n?/g, '\n')
          .replace(/^(#{1,6})(?!#)([^\s#])/gm, '$1 $2')
          .replace(/^(\s*[-*])(?=\S)/gm, '$1 ')
        normalizedText = normalizedText.replace(
          /([^\n])\n(?=#{1,6} |[-*] |\d+\. )/g,
          '$1\n\n',
        )

        // 处理 <think> 标签，将其转换为可折叠的思考过程区块
        let processedText = normalizedText.replace(
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

        // DOMPurify 保留 GFM 生成的 table、strong、code 等安全标签。
        // 为表格加可横向滚动的容器，避免宽表格在聊天区域被挤压成不可读内容。
        const safe = DOMPurify.sanitize(marked.parse(processedText), {
          USE_PROFILES: { html: true },
        })
        return safe
          .replace(/<table>/g, '<div class="markdown-table-wrap"><table>')
          .replace(/<\/table>/g, '</table></div>')
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
          // 仅允许通过首页参数显式开启聚合模式，其他来源均保持关闭。
          const src = route?.query?.source
          isAggregateMode.value = src === 'aggregate'
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
        isDeepThinkingActive,
        isAggregateMode,
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
        toggleAggregateMode,
        toggleDeepThinking,
        isWebSearchActive,
        toggleWebSearch,
        handleKeydown,
        handleInput,
        fetchSuggestions,
        selectSuggestion,
        clearSuggestions,
        highlightQuery,
        renderMarkdown,
        mergeSources,
        groupedHistory,
        router,
      }
    },
    data() {
      return {
        // from chat2.vue
        showHistory: false,
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
    min-height: 0; /* 防止 flex 子元素撑破容器 */
  }

  .navigation-container {
    display: flex;
    /* flex-shrink: 0;  */
    box-shadow: none;
    position: relative;
  }

  .main-content {
    flex-grow: 1;
    padding: 20px;
    display: flex;
    flex-direction: column;
    min-width: 0; /* 防止 flex 子元素溢出 */
    overflow: hidden;
  }

  .chat-container {
    max-width: 1024px; /* 设置最大宽度 */
    width: 100%; /* 确保在小屏下不超出 */
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
    left: 50%;
    transform: translateX(-50%); /* 用居中替换硬编码 right: 450px */
    bottom: 180px; /* 避开输入框 */
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
    width: min(860px, 100%); /* 最大860px，小屏自动收缩 */
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
    box-sizing: border-box; /* 确保 padding 不撑破宽度 */
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

  .tool-btn .web-search-icon {
    width: 24px;
    height: 24px;
    fill: none;
    stroke: currentColor;
    stroke-linecap: round;
    stroke-linejoin: round;
    stroke-width: 1.8;
    transition: transform 0.3s ease;
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
    max-width: min(880px, 95%); /* 大屏880px，小屏95%宽 */
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
    max-width: min(700px, 85%); /* 大屏700px，小屏85%宽 */
  }

  :deep(.dialog-history-container) {
    width: clamp(240px, 25vw, 336px) !important; /* 随视口宽度自适应 */
    position: relative;
    z-index: 10001; /* 提升到最高层，避免被任何浮层覆盖 */
  }

  .hidden-history {
    display: none;
  }

  /* 未登录时：历史对话空态 */
  .history-empty {
    width: clamp(200px, 25vw, 336px); /* 与历史面板同步 */
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

  /* 回答 Markdown 排版：普通模式与聚合模式共用同一渲染区域。 */
  .ai-text-content {
    display: block;
    width: 100%;
    color: #1f2937;
    font-size: 15px;
    line-height: 1.85;
    letter-spacing: 0.01em;
  }

  :deep(.ai-text-content > div) {
    display: block;
    color: #1f2937;
    line-height: inherit;
    overflow-wrap: anywhere;
  }

  :deep(.ai-text-content h1),
  :deep(.ai-text-content h2),
  :deep(.ai-text-content h3),
  :deep(.ai-text-content h4),
  :deep(.ai-text-content h5),
  :deep(.ai-text-content h6) {
    color: #172033;
    line-height: 1.35;
    font-weight: 750;
    letter-spacing: 0;
  }

  :deep(.ai-text-content h1) {
    margin: 26px 0 14px;
    font-size: 1.55em;
  }

  :deep(.ai-text-content h2) {
    margin: 23px 0 12px;
    padding-bottom: 7px;
    font-size: 1.32em;
    border-bottom: 1px solid #dbe4f0;
  }

  :deep(.ai-text-content h3) {
    margin: 20px 0 10px;
    font-size: 1.15em;
  }

  :deep(.ai-text-content h4),
  :deep(.ai-text-content h5),
  :deep(.ai-text-content h6) {
    margin: 16px 0 8px;
    font-size: 1em;
  }

  :deep(.ai-text-content p) {
    margin: 0 0 14px;
  }

  :deep(.ai-text-content ul),
  :deep(.ai-text-content ol) {
    margin: 8px 0 16px;
    padding-left: 28px;
  }

  :deep(.ai-text-content li) {
    margin: 5px 0;
    padding-left: 3px;
  }

  :deep(.ai-text-content li::marker) {
    color: #2563eb;
    font-weight: 700;
  }

  :deep(.ai-text-content strong) {
    color: #0f3e7a;
    font-weight: 750;
  }

  :deep(.ai-text-content em) {
    color: #374151;
  }

  :deep(.ai-text-content a) {
    color: #2563eb;
    font-weight: 600;
    text-decoration: underline;
    text-decoration-color: #93c5fd;
    text-underline-offset: 3px;
  }

  :deep(.ai-text-content a:hover) {
    color: #1d4ed8;
    text-decoration-color: currentColor;
  }

  :deep(.ai-text-content blockquote) {
    margin: 16px 0;
    padding: 10px 14px;
    color: #475569;
    background: #f8fafc;
    border-left: 4px solid #60a5fa;
    border-radius: 0 8px 8px 0;
  }

  :deep(.ai-text-content blockquote p:last-child) {
    margin-bottom: 0;
  }

  :deep(.ai-text-content code) {
    padding: 2px 6px;
    color: #be123c;
    font-family: 'Cascadia Code', Consolas, monospace;
    font-size: 0.88em;
    background: #fff1f2;
    border: 1px solid #ffe4e6;
    border-radius: 5px;
  }

  :deep(.ai-text-content pre) {
    margin: 16px 0;
    padding: 14px 16px;
    overflow-x: auto;
    color: #e2e8f0;
    background: #172033;
    border-radius: 10px;
  }

  :deep(.ai-text-content pre code) {
    padding: 0;
    color: inherit;
    font-size: 0.88em;
    line-height: 1.65;
    white-space: pre;
    background: transparent;
    border: 0;
  }

  :deep(.ai-text-content hr) {
    height: 1px;
    margin: 22px 0;
    background: #dbe4f0;
    border: 0;
  }

  :deep(.ai-text-content .markdown-table-wrap) {
    width: 100%;
    margin: 18px 0;
    overflow-x: auto;
    border: 1px solid #dbe4f0;
    border-radius: 10px;
    background: #fff;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
  }

  :deep(.ai-text-content table) {
    width: 100%;
    min-width: 520px;
    border-spacing: 0;
    border-collapse: collapse;
    color: #243044;
    font-size: 0.94em;
    line-height: 1.6;
  }

  :deep(.ai-text-content th) {
    padding: 10px 13px;
    color: #183b69;
    font-weight: 750;
    text-align: left;
    white-space: nowrap;
    background: #edf5ff;
    border-bottom: 1px solid #cdddf1;
  }

  :deep(.ai-text-content td) {
    padding: 10px 13px;
    vertical-align: top;
    border-bottom: 1px solid #e5edf6;
  }

  :deep(.ai-text-content tr:last-child td) {
    border-bottom: 0;
  }

  :deep(.ai-text-content tbody tr:nth-child(even)) {
    background: #f8fbff;
  }

  :deep(.ai-text-content tbody tr:hover) {
    background: #eff6ff;
  }

  :deep(.ai-text-content img) {
    display: block;
    max-width: 100%;
    height: auto;
    margin: 16px 0;
    border: 1px solid #dbe4f0;
    border-radius: 10px;
  }

  .web-sources {
    display: flex;
    flex-direction: column;
    gap: 7px;
    margin-top: 18px;
    padding-top: 12px;
    border-top: 1px solid #e5e7eb;
  }

  .web-sources-title {
    color: #374151;
    font-size: 13px;
    font-weight: 700;
  }

  .web-source-item {
    display: grid;
    grid-template-columns: 22px minmax(0, 1fr);
    gap: 5px 7px;
    padding: 8px 10px;
    border-radius: 7px;
    color: #2563eb;
    background: #f8fafc;
    text-decoration: none;
  }

  .web-source-item:hover {
    background: #eff6ff;
  }

  .web-source-index {
    grid-row: span 2;
    color: #64748b;
    font-size: 12px;
  }

  .web-source-title {
    overflow: hidden;
    font-size: 13px;
    font-weight: 600;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .web-source-url {
    overflow: hidden;
    color: #64748b;
    font-size: 11px;
    text-overflow: ellipsis;
    white-space: nowrap;
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

  /* ===== 断点：平板（≤ 1024px） ===== */
  @media (max-width: 1024px) {
    .main-content {
      padding: 12px;
    }

    .input-wrapper {
      height: 140px;
      border-radius: 20px;
    }

    :deep(.dialog-history-container) {
      width: 260px !important;
    }

    .history-empty {
      width: 260px;
    }

    .slogan {
      font-size: 38px;
    }

    .empty-chat-area {
      margin-top: 120px;
    }
  }

  /* ===== 断点：手机（≤ 768px） ===== */
  @media (max-width: 768px) {
    .main-content {
      padding: 8px;
    }

    .input-wrapper {
      height: 120px;
      border-radius: 16px;
      padding: 10px;
    }

    textarea {
      font-size: 14px;
    }

    .slogan {
      font-size: 28px;
    }

    .empty-chat-area {
      margin-top: 80px;
    }

    .messages-area {
      padding: 10px;
    }

    .scroll-bottom-btn {
      bottom: 140px;
    }

    .chat-header-tag {
      font-size: 14px;
      max-width: 90%;
    }

    /* 手机端历史面板改为固定覆盖层 */
    :deep(.dialog-history-container) {
      width: 80vw !important;
      position: fixed !important;
      top: 0;
      left: 0;
      height: 100vh;
      z-index: 10001;
      box-shadow: 4px 0 16px rgba(0, 0, 0, 0.15);
    }

    .history-empty {
      display: none;
    }
  }

  /* ===== 断点：超小屏（≤ 480px） ===== */
  @media (max-width: 480px) {
    .input-wrapper {
      height: 110px;
      border-radius: 14px;
    }

    .tool-btn span {
      display: none; /* 超小屏隐藏按钮文字，只保留图标 */
    }

    .slogan {
      font-size: 22px;
    }
  }
</style>
