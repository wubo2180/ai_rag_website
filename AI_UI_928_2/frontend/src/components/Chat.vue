<!--  --><template>
  <div id="chat-container">
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
        <button v-if="!sidebarCollapsed" class="logout-btn" @click="logout" title="退出登录">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
            <polyline points="16 17 21 12 16 7"></polyline>
            <line x1="21" y1="12" x2="9" y2="12"></line>
          </svg>
        </button>
      </div>
      <button v-if="!sidebarCollapsed" class="new-chat-btn" @click="startNewChat">
        <span class="btn-icon">+</span>
        开启新对话
      </button>
      <div v-if="!sidebarCollapsed" class="history">
        <h3>对话历史</h3>
        <ul>
          <li v-for="(chat, index) in chatHistory" :key="index" :class="{ active: currentChatIndex === index }" class="chat-item">
            <div class="chat-content" @click="loadChat(index)">
              <span class="chat-icon">💬</span>
              <span class="chat-title">{{ chat.title || `对话 ${chatHistory.length - index}` }}</span>
            </div>
            <button class="delete-btn" @click.stop="deleteChat(index)" title="删除对话">
              🗑️
            </button>
          </li>
        </ul>
      </div>
      <div v-if="sidebarCollapsed" class="collapsed-actions">
        <button class="collapsed-new-chat" @click="startNewChat" title="新建对话">
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
      </div>
      
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="welcome-message">
          <span class="hello-emoji">👋</span>
          <p>您好 {{ currentUser.username }}，想和我聊点什么？</p>
        </div>
        <div v-for="(msg, index) in messages" :key="index" class="message" :class="msg.sender">
          <div class="bubble">
            <p v-if="msg.text || !isLoading || msg.sender !== 'ai' || index !== messages.length - 1">{{ msg.text }}</p>
            <p v-else-if="isLoading && msg.sender === 'ai' && index === messages.length - 1">正在思考中...</p>
            <div v-if="msg.sender === 'ai' && (msg.text || (!isLoading || index !== messages.length - 1))" class="message-actions">
              <button class="action-btn copy-btn" @click="copyMessage(msg.text)" title="复制">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                  <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                </svg>
              </button>
              <button class="action-btn like-btn" @click="likeMessage" title="赞">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                </svg>
              </button>
              <button class="action-btn dislike-btn" @click="dislikeMessage" title="踩">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                </svg>
              </button>
              <button class="action-btn refresh-btn" @click="refreshMessage" title="重新生成">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polyline points="23 4 23 10 17 10"></polyline>
                  <polyline points="1 20 1 14 7 14"></polyline>
                  <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                </svg>
              </button>
              <button class="action-btn more-btn" @click="showMoreOptions" title="更多">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <circle cx="12" cy="12" r="1"></circle>
                  <circle cx="19" cy="12" r="1"></circle>
                  <circle cx="5" cy="12" r="1"></circle>
                </svg>
              </button>
            </div>
          </div>
        </div>
        <!-- Related Questions - 显示在最后一条AI消息后 -->
        <div v-if="messages.length > 0 && messages[messages.length - 1].sender === 'ai' && relatedQuestions.length > 0" class="related-questions">
          <div class="related-questions-title">💡 相关问题推荐：</div>
          <div class="related-questions-list">
            <div 
              v-for="(question, index) in relatedQuestions" 
              :key="index" 
              class="related-question-item" 
              @click="askRelatedQuestion(question)"
            >
              <span class="question-text">{{ question }}</span>
            </div>
          </div>
        </div>

        <!-- 滚动到底部按钮 -->
        <div v-if="!isAtBottom && messages.length > 0" class="scroll-to-bottom-btn" @click="scrollToBottomManually">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
              placeholder="询问AI任何问题" 
              rows="2"
            ></textarea>
          </div>
          <button @click="sendMessage" class="send-btn">↑</button>
        </div>
        <!-- Button Layer -->
        <div class="button-layer">
          <div class="database-selector" :class="{ open: dropdownOpen }">
            <button class="db-selector-btn" @click="toggleDropdown">
              <span class="db-text">{{ getCurrentDatabaseOption().label }}</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            <div v-if="dropdownOpen" class="dropdown-menu">
              <div 
                v-for="option in databaseOptions" 
                :key="option.value"
                @click="selectDatabase(option.value)"
                :class="['dropdown-item', { active: selectedDatabase === option.value }]"
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
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 12l2 2 4-4"></path>
              <path d="M21 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
              <path d="M3 12c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
              <path d="M12 21c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
              <path d="M12 3c.552 0 1-.448 1-1s-.448-1-1-1-1 .448-1 1 .448 1 1 1z"></path>
            </svg>
            <span class="btn-text">深度搜索</span>
          </button>
          
          <!-- 模型选择按钮 -->
          <div class="model-selector" :class="{ open: modelDropdownOpen }">
            <button class="model-selector-btn" @click="toggleModelDropdown">
              <span class="model-text">{{ getCurrentModelOption().label }}</span>
              <span class="dropdown-arrow">▼</span>
            </button>
            <div v-if="modelDropdownOpen" class="dropdown-menu">
              <div 
                v-for="option in modelOptions" 
                :key="option.value"
                @click="selectModel(option.value)"
                :class="['dropdown-item', { active: selectedModel === option.value }]"
              >
                <span class="model-label">{{ option.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

// 获取当前用户信息
const currentUser = ref({});

// Refs for UI elements and state
const newMessage = ref('');
const messages = ref([]);
const chatHistory = ref([]);
const isLoading = ref(false);
const messagesContainer = ref(null);
const messageTextarea = ref(null);
const currentChatIndex = ref(-1);
const currentChatTitle = ref('');
const sidebarCollapsed = ref(false);

// 新增：对话状态管理
const currentChatId = ref(null); // 当前对话的唯一ID
const isNewChat = ref(true); // 标识当前是否为新对话

// --- LocalStorage Functions ---
const getUserStorageKey = () => {
  const user = JSON.parse(localStorage.getItem('ai-chat-user') || '{}');
  return `ai-chat-history-${user.username || 'anonymous'}`;
};

const loadFromStorage = () => {
  try {
    const storageKey = getUserStorageKey();
    const stored = localStorage.getItem(storageKey);
    if (stored) {
      const data = JSON.parse(stored);
      chatHistory.value = data.chatHistory || [];
      messages.value = data.currentMessages || [];
      currentChatIndex.value = data.currentChatIndex || -1;
      currentChatTitle.value = data.currentChatTitle || '';
      currentChatId.value = data.currentChatId || null;
      isNewChat.value = data.isNewChat !== undefined ? data.isNewChat : true;
      relatedQuestions.value = data.currentRelatedQuestions || [];
    }
  } catch (error) {
    console.error('加载本地存储失败:', error);
  }
};

const saveToStorage = () => {
  try {
    const storageKey = getUserStorageKey();
    const data = {
      chatHistory: chatHistory.value,
      currentMessages: messages.value,
      currentChatIndex: currentChatIndex.value,
      currentChatTitle: currentChatTitle.value,
      currentChatId: currentChatId.value,
      isNewChat: isNewChat.value,
      currentRelatedQuestions: relatedQuestions.value
    };
    localStorage.setItem(storageKey, JSON.stringify(data));
  } catch (error) {
    console.error('保存到本地存储失败:', error);
  }
};

// Database selector state
const selectedDatabase = ref('all');
const dropdownOpen = ref(false);
const databaseOptions = ref([
  { value: 'external', label: '外部数据库' },
  { value: 'internal', label: '内部数据库' },
  { value: 'all', label: '全部' }
]);

// Deep thinking state
const deepThinkingEnabled = ref(true);

// Model selector state
const selectedModel = ref('deepseek');
const modelDropdownOpen = ref(false);
const modelOptions = ref([
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'doubao', label: '豆包' },
  { value: 'gpt5', label: 'GPT-5' }
]);

// Suggestions state
const suggestions = ref([]);
const debounceTimer = ref(null);
const selectedIndex = ref(-1);
const relatedQuestions = ref([]);

// 滚动状态
const isAtBottom = ref(true);

// --- Auth Functions ---
const logout = () => {
  if (confirm('确定要退出登录吗？')) {
    // 保存当前用户的对话记录
    saveToStorage();
    // 只移除用户登录信息，保留对话历史
    localStorage.removeItem('ai-chat-user');
    router.push('/login');
  }
};

// --- Core Functions ---

// 智能滚动：只有当用户在底部时才自动滚动
const scrollToBottom = (force = false) => {
  nextTick(() => {
    if (messagesContainer.value) {
      const container = messagesContainer.value;
      const isAtBottom = container.scrollTop + container.clientHeight >= container.scrollHeight - 50;
      
      // 强制滚动或用户在底部时才滚动
      if (force || isAtBottom) {
        container.scrollTop = container.scrollHeight;
      }
    }
  });
};

// 检查用户是否在底部
const isUserAtBottom = () => {
  if (!messagesContainer.value) return true;
  const container = messagesContainer.value;
  return container.scrollTop + container.clientHeight >= container.scrollHeight - 50;
};

// 监听滚动事件，更新按钮显示状态
const handleScroll = () => {
  isAtBottom.value = isUserAtBottom();
};

// 手动滚动到底部
const scrollToBottomManually = () => {
  scrollToBottom(true);
  isAtBottom.value = true;
};

const sendMessage = async () => {
  if (newMessage.value.trim() === '') return;

  const userMessage = { text: newMessage.value, sender: 'user' };
  const messageToSend = newMessage.value;
  
  // 如果是新对话的第一条消息，设置标题
  if (isNewChat.value && messages.value.length === 0) {
    currentChatTitle.value = messageToSend.length > 20 ? messageToSend.substring(0, 20) + '...' : messageToSend;
  }
  
  messages.value.push(userMessage);
  
  newMessage.value = '';
  suggestions.value = []; // Clear suggestions on send
  relatedQuestions.value = []; // Clear previous related questions
  isLoading.value = true;
  nextTick(adjustTextareaHeight);
  scrollToBottom();

  // 添加一个空的AI消息用于流式更新
  const aiMessageIndex = messages.value.length;
  messages.value.push({ text: '', sender: 'ai' });

  try {
    // 并行启动相关问题获取，不等待AI回复完成
    const relatedQuestionsPromise = (async () => {
      try {
        console.log('开始获取相关问题，消息:', messageToSend);
        const relatedResponse = await fetch('http://127.0.0.1:5000/api/related-questions', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: messageToSend,
          }),
        });
        
        console.log('相关问题API响应状态:', relatedResponse.status);
        if (relatedResponse.ok) {
          const relatedData = await relatedResponse.json();
          console.log('获取到的相关问题数据:', relatedData);
          relatedQuestions.value = relatedData.related_questions || [];
          console.log('设置的相关问题:', relatedQuestions.value);
          scrollToBottom(); // 显示相关问题后重新滚动
        }
      } catch (relatedError) {
        console.warn('获取相关问题失败:', relatedError);
      }
    })();

    // 使用 fetch 进行流式请求
    const response = await fetch('http://127.0.0.1:5000/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: messageToSend,
        database: selectedDatabase.value,
        model: selectedModel.value,
        deep_thinking: deepThinkingEnabled.value,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    // 获取可读数据流读取器
    const reader = response.body.getReader();
    // 创建一个文本解码器来处理 UTF-8 编码的数据
    const decoder = new TextDecoder();
    
    let aiResponse = '';
    
    // 无限循环来持续读取数据流
    while (true) {
      // 读取一块数据 { done, value }
      const { done, value } = await reader.read();
      
      // 如果数据流结束 (done is true)，就跳出循环
      if (done) {
        break;
      }
      
      // 将接收到的数据块 (Uint8Array) 解码成字符串
      const chunk = decoder.decode(value, { stream: true });
      
      // 处理服务器发送事件 (SSE) 格式的数据
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6); // 移除 'data: ' 前缀
          if (data === '[DONE]') {
            break;
          }
          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              aiResponse += parsed.content;
              // 实时更新 Vue 的 ref 变量，UI 会自动响应
              messages.value[aiMessageIndex].text = aiResponse;
              scrollToBottom(); // 智能滚动，只有用户在底部时才滚动
            }
          } catch (e) {
            // 如果不是JSON格式，直接添加文本
            aiResponse += data;
            messages.value[aiMessageIndex].text = aiResponse;
            scrollToBottom(); // 智能滚动
          }
        }
      }
    }
    
    
  } catch (error) {
    console.error('Error sending message:', error);
    messages.value[aiMessageIndex].text = '抱歉，我暂时无法回复。请检查网络连接或稍后重试。';
  } finally {
    isLoading.value = false;
    // 使用统一的保存函数
    saveCurrentChat();
    scrollToBottom();
    

  }
};

// --- Sidebar and Chat History ---

const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value;
};

const saveCurrentChat = () => {
  // 只有当有消息内容时才保存
  if (messages.value.length === 0) return;
  
  const chatData = {
    id: currentChatId.value || Date.now(), // 使用现有ID或生成新ID
    messages: [...messages.value],
    title: currentChatTitle.value || (messages.value[0]?.text.substring(0, 20) + '...' || '新对话'),
    relatedQuestions: [...relatedQuestions.value],
    timestamp: new Date().toISOString()
  };
  
  if (isNewChat.value) {
    // 新对话：添加到历史记录开头
    chatHistory.value.unshift(chatData);
    currentChatIndex.value = 0;
    currentChatId.value = chatData.id;
    isNewChat.value = false; // 标记为已保存的对话
  } else {
    // 已存在的对话：更新对应位置的记录
    if (currentChatIndex.value >= 0 && currentChatIndex.value < chatHistory.value.length) {
      chatHistory.value[currentChatIndex.value] = chatData;
    }
  }
  
  saveToStorage();
};

const startNewChat = () => {
  // 如果当前有对话内容，保存它
  if (messages.value.length > 0) {
    saveCurrentChat();
  }
  
  // 重置为新对话状态
  messages.value = [];
  currentChatIndex.value = -1;
  currentChatTitle.value = '';
  currentChatId.value = null;
  isNewChat.value = true; // 标记为新对话
  relatedQuestions.value = [];
  
  saveToStorage();
};

const loadChat = (index) => {
  // 如果当前有对话内容且是新对话，先保存
  if (messages.value.length > 0 && isNewChat.value) {
    saveCurrentChat();
  }
  
  // 加载指定的历史对话
  const chatData = chatHistory.value[index];
  messages.value = [...chatData.messages];
  currentChatTitle.value = chatData.title;
  currentChatIndex.value = index;
  currentChatId.value = chatData.id;
  isNewChat.value = false; // 标记为已存在的对话
  relatedQuestions.value = [...(chatData.relatedQuestions || [])];
  
  saveToStorage();
  scrollToBottom();
};

const deleteChat = (index) => {
  // 删除指定的对话记录
  chatHistory.value.splice(index, 1);
  
  // 如果删除的是当前对话
  if (currentChatIndex.value === index) {
    // 清空当前对话
    messages.value = [];
    currentChatTitle.value = '';
    currentChatIndex.value = -1;
    relatedQuestions.value = [];
  } else if (currentChatIndex.value > index) {
    // 如果当前对话索引大于删除的索引，需要调整索引
    currentChatIndex.value--;
  }
  
  // 保存到localStorage
  saveToStorage();
};

const copyMessage = async (text) => {
  try {
    await navigator.clipboard.writeText(text);
    showCopyToast('已复制到剪贴板');
  } catch (err) {
    // 如果现代API不可用，使用传统方法
    const textArea = document.createElement('textarea');
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      showCopyToast('已复制到剪贴板');
    } catch (fallbackErr) {
      console.error('复制失败:', fallbackErr);
      showCopyToast('复制失败，请重试');
    }
    document.body.removeChild(textArea);
  }
};

// 显示复制提示
const showCopyToast = (message) => {
  // 移除已存在的提示
  const existingToast = document.querySelector('.copy-toast');
  if (existingToast) {
    existingToast.remove();
  }

  // 创建新的提示元素
  const toast = document.createElement('div');
  toast.className = 'copy-toast';
  toast.textContent = message;
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
  `;

  // 添加CSS动画
  if (!document.querySelector('#copy-toast-style')) {
    const style = document.createElement('style');
    style.id = 'copy-toast-style';
    style.textContent = `
      @keyframes fadeInOut {
        0% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
        20% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        80% { opacity: 1; transform: translate(-50%, -50%) scale(1); }
        100% { opacity: 0; transform: translate(-50%, -50%) scale(0.8); }
      }
    `;
    document.head.appendChild(style);
  }

  document.body.appendChild(toast);

  // 2秒后自动移除
  setTimeout(() => {
    if (toast.parentNode) {
      toast.parentNode.removeChild(toast);
    }
  }, 2000);
};

const likeMessage = () => {
  console.log('点赞消息');
  // 这里可以添加点赞逻辑
};

const dislikeMessage = () => {
  console.log('踩消息');
  // 这里可以添加踩的逻辑
};

const refreshMessage = () => {
  console.log('重新生成消息');
  // 这里可以添加重新生成消息的逻辑
};

const showMoreOptions = () => {
  console.log('显示更多选项');
  // 这里可以添加更多选项的逻辑
};

// --- Database Selector ---

const selectDatabase = (database) => {
  selectedDatabase.value = database;
  dropdownOpen.value = false;
};

const toggleDropdown = () => {
  dropdownOpen.value = !dropdownOpen.value;
};

const getCurrentDatabaseOption = () => {
  return databaseOptions.value.find(option => option.value === selectedDatabase.value) || databaseOptions.value[2];
};

// --- Deep Thinking Functions ---

const toggleDeepThinking = () => {
  deepThinkingEnabled.value = !deepThinkingEnabled.value;
  console.log('深度思考模式:', deepThinkingEnabled.value ? '开启' : '关闭');
};

// --- Model Selector Functions ---

const selectModel = (model) => {
  selectedModel.value = model;
  modelDropdownOpen.value = false;
  console.log('切换模型:', model);
};

const toggleModelDropdown = () => {
  modelDropdownOpen.value = !modelDropdownOpen.value;
};

const getCurrentModelOption = () => {
  return modelOptions.value.find(option => option.value === selectedModel.value) || modelOptions.value[0];
};

const askRelatedQuestion = (question) => {
  newMessage.value = question;
  nextTick(() => {
    adjustTextareaHeight();
    sendMessage();
  });
};

const highlightQuery = (text) => {
  if (!newMessage.value.trim()) return text;
  const query = newMessage.value.trim();
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  return text.replace(regex, '<strong>$1</strong>');
};

// --- Textarea and Suggestions ---

const handleKeydown = (event) => {
  if (suggestions.value.length > 0) {
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      selectedIndex.value = (selectedIndex.value + 1) % suggestions.value.length;
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (selectedIndex.value <= 0) {
        selectedIndex.value = suggestions.value.length - 1;
      } else {
        selectedIndex.value--;
      }
    } else if (event.key === 'Enter') {
      if (selectedIndex.value !== -1) {
        event.preventDefault();
        selectSuggestion(suggestions.value[selectedIndex.value]);
      } else if (!event.shiftKey) {
        event.preventDefault();
        sendMessage();
      }
    } else if (event.key === 'Escape') {
      event.preventDefault();
      clearSuggestions();
    }
  } else if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    sendMessage();
  }
};

const adjustTextareaHeight = () => {
  const textarea = messageTextarea.value;
  if (textarea) {
    textarea.style.height = 'auto';
    const scrollHeight = textarea.scrollHeight;
    const lineHeight = 24;
    const maxHeight = lineHeight * 10;
    const minHeight = lineHeight * 2;
    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);
    textarea.style.height = newHeight + 'px';
  }
};

const handleInput = () => {
  adjustTextareaHeight();
  if (debounceTimer.value) {
    clearTimeout(debounceTimer.value);
  }
  debounceTimer.value = setTimeout(() => {
    fetchSuggestions();
  }, 250);
};

const fetchSuggestions = () => {
  const query = newMessage.value.trim();
  if (!query) {
    suggestions.value = [];
    return;
  }

  const scriptId = 'baidu-jsonp-script';
  const existingScript = document.getElementById(scriptId);
  if (existingScript) {
    existingScript.remove();
  }

  const script = document.createElement('script');
  script.id = scriptId;
  script.src = `https://suggestion.baidu.com/su?wd=${encodeURIComponent(query)}&cb=window.handleBaiduSuggestions`;
  
  script.onerror = () => {
    console.error('Failed to load suggestions.');
    suggestions.value = [];
    if (script.parentNode) {
      script.parentNode.removeChild(script);
    }
  };
  
  script.onload = () => {
      if (script.parentNode) {
          script.parentNode.removeChild(script);
      }
  };

  document.head.appendChild(script);
};

const selectSuggestion = (suggestion) => {
  newMessage.value = suggestion;
  suggestions.value = [];
  selectedIndex.value = -1;
  nextTick(() => {
    adjustTextareaHeight();
    messageTextarea.value.focus();
  });
};

const clearSuggestions = () => {
  setTimeout(() => {
    suggestions.value = [];
    selectedIndex.value = -1;
  }, 150);
};

// --- Lifecycle Hooks ---

const handleClickOutside = (event) => {
  const dbSelector = document.querySelector('.database-selector');
  const modelSelector = document.querySelector('.model-selector');
  
  if (dbSelector && !dbSelector.contains(event.target)) {
    dropdownOpen.value = false;
  }
  
  if (modelSelector && !modelSelector.contains(event.target)) {
    modelDropdownOpen.value = false;
  }
};

onMounted(() => {
  // 获取用户信息
  const userData = localStorage.getItem('ai-chat-user');
  if (userData) {
    currentUser.value = JSON.parse(userData);
  }
  
  document.addEventListener('click', handleClickOutside);
  window.handleBaiduSuggestions = (data) => {
    suggestions.value = data.s || [];
    selectedIndex.value = -1;
  };
  
  // 添加滚动事件监听
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.addEventListener('scroll', handleScroll);
    }
  });
  
  loadFromStorage(); // 从localStorage加载数据
  nextTick(() => {
    scrollToBottom();
    isAtBottom.value = true;
  });
});

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside);
  if (messagesContainer.value) {
    messagesContainer.value.removeEventListener('scroll', handleScroll);
  }
  delete window.handleBaiduSuggestions;
});
</script>

<style scoped>
/* 导入原有的样式 */
@import '../assets/main.css';

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

.deep-thinking-btn:hover {
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
</style>