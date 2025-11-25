<template>
  <div class="chat-container">
    <!-- 顶部固定的“新的对话”标签 -->
    <div class="chat-header-tag">{{ headerText }}</div>
    <!-- Empty State -->
    <div v-if="messages.length === 0" class="empty-chat-area">
      <div class="logo-placeholder">
        <img class="logo-image" src="@/assets/talk%20page/logo.png" alt="IBOX Materix" />
      </div>
      <h1 class="slogan">材料问题迎刃而解!</h1>
    </div>

    <!-- Messages Area -->
    <div v-else class="messages-area">
      <div
        v-for="(message, index) in messages"
        :key="index"
        :class="['message', message.sender === 'user' ? 'message-user' : 'message-ai']"
      >
        {{ message.content }}
      </div>
    </div>

    <!-- Input Box -->
    <div class="input-container">
      <div class="input-wrapper">
        <textarea v-model="newMessage" 
                  placeholder="向 IBOX Materix 提问" 
                  ref="questionTextarea"
                  @input="handleInput"
                  @keydown="handleKeydown"
                  @focus="fetchSuggestions"
                  @blur="clearSuggestions"></textarea>
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
                <img class="all-icon" src="@/assets/talk%20page/home@3_06.png" alt="全部" :class="{ 'rotated': isAllIconRotated }" />
              </button>
              <div v-if="isAllDropdownVisible" class="dropdown-menu">
                <div v-for="option in options" :key="option" class="dropdown-item" @click="selectOption(option)">
                  {{ option }}
                </div>
              </div>
            </div>
            <button class="tool-btn" :class="{ 'highlighted': isDeepThinkingActive }" @click="toggleDeepThinking">
              <img v-if="!isDeepThinkingActive" src="@/assets/talk%20page/home@3_03.png" alt="深度思考" />
              <img v-else src="@/assets/talk%20page/home@3X_07.png" alt="深度思考" />
              <span>深度思考</span>
            </button>
          </div>
          <div class="toolbar-right">
            <button class="send-button" @click="sendMessage">
              <img class="send-icon" src="@/assets/talk%20page/talk@3X_18.png" alt="发送" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue';

const messages = ref([]); // [{ content: string, sender: 'user' | 'ai' }]
const newMessage = ref('');
const headerText = ref('新的对话');
const headerLocked = ref(false); // 仅首次消息后锁定顶部标签
const isAllDropdownVisible = ref(false);
const isAllIconRotated = ref(false);
const isDeepThinkingActive = ref(false);
const options = ['全部', '内部数据库', '外部数据库'];
const selectedOption = ref('全部');

// --- 联想词相关状态 ---
const suggestions = ref([]);
const debounceTimer = ref(null);
const selectedIndex = ref(-1);
const questionTextarea = ref(null);

const sendMessage = () => {
  const text = newMessage.value.trim();
  if (text !== '') {
    messages.value.push({ content: text, sender: 'user' });
    if (!headerLocked.value) {
      headerText.value = text; // 仅首次消息替换顶部标签
      headerLocked.value = true; // 锁定，后续不更新
    }
    newMessage.value = '';
    clearSuggestions();
  }
};

const toggleAllDropdown = () => {
  isAllDropdownVisible.value = !isAllDropdownVisible.value;
  isAllIconRotated.value = !isAllIconRotated.value;
};

const selectOption = (option) => {
  selectedOption.value = option;
  isAllDropdownVisible.value = false;
  isAllIconRotated.value = false;
};

const toggleDeepThinking = () => {
  isDeepThinkingActive.value = !isDeepThinkingActive.value;
};

// --- 联想词相关逻辑 ---
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
    } else if (event.key === 'Enter' && !event.shiftKey) {
      if (selectedIndex.value !== -1) {
        event.preventDefault();
        selectSuggestion(suggestions.value[selectedIndex.value]);
      } else {
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

const handleInput = () => {
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

  const scriptId = 'baidu-jsonp-script-chat';
  const existingScript = document.getElementById(scriptId);
  if (existingScript) {
    existingScript.remove();
  }

  const script = document.createElement('script');
  script.id = scriptId;
  script.src = `https://suggestion.baidu.com/su?wd=${encodeURIComponent(query)}&cb=window.handleBaiduSuggestionsChat`;
  
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
    if (questionTextarea.value) {
      questionTextarea.value.focus();
    }
  });
};

const clearSuggestions = () => {
  setTimeout(() => {
    suggestions.value = [];
    selectedIndex.value = -1;
  }, 150);
};

const highlightQuery = (text) => {
  if (!newMessage.value.trim()) return text;
  const query = newMessage.value.trim();
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
  return text.replace(regex, '<strong>$1</strong>');
};

onMounted(() => {
  window.handleBaiduSuggestionsChat = (data) => {
    suggestions.value = data.s || [];
    selectedIndex.value = -1;
  };
});

onUnmounted(() => {
  delete window.handleBaiduSuggestionsChat;
  const scriptId = 'baidu-jsonp-script-chat';
  const existingScript = document.getElementById(scriptId);
  if (existingScript && existingScript.parentNode) {
    existingScript.parentNode.removeChild(existingScript);
  }
});

</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  justify-content: flex-start; /* 顶部开始排列，便于精确控制间距 */
  position: relative; /* 使顶部标签绝对定位于容器顶部 */
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
  position: absolute;
  top: 0; /* 固定在聊天组件最上方 */
  left: 50%;
  transform: translateX(-50%);
  font-size: 16px;
  font-weight: 400;
  color: #1a1a1a;
  background: transparent;
  padding: 4px 8px;
  border-radius: 14px;
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
  padding-top: 50px; /* 留出顶部标签区域，避免消息与顶部重叠 */
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
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
  border: 1px solid #1a1a1a; /* Outer circle line color */
  border-radius: 30px;
  padding: 15px;
  margin: 0 auto; /* Center the input box */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative; /* Enable absolute positioning for toolbar children */
}

.input-wrapper:focus-within {
  box-shadow: 0 8px 8px rgba(73, 151, 255, 0.1);
}

/* 联想词列表样式 */
.suggestions-list {
  position: absolute;
  bottom: 100%;
  left: 15px;
  right: 15px;
  margin-bottom: 8px; /* 与输入框的间距 */
  z-index: 10;
  background: rgba(255,255,255,0.92); 
  border: 1px solid rgba(0,0,0,0.08); 
  border-radius: 12px; 
  box-shadow: 0 8px 18px rgba(0,0,0,0.12); 
  max-height: 220px; 
  overflow-y: auto; 
}
.suggestions-list ul { list-style: none; padding: 6px; margin: 0; }
.suggestions-list li { padding: 8px 10px; font-size: 14px; color: #1f2937; cursor: pointer; border-radius: 8px; }
.suggestions-list li:hover, .suggestions-list li.selected { background: rgba(91,141,239,0.14); color: #0b122e; }

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
  background: transparent; /* Match chat box inner color */
  border: 1px solid #1a1a1a; /* Match chat box outer frame color */
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
  transition: transform 0.3s ease, filter 0.3s ease;
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
  background-color: #3d82f5;
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
</style>
/* 消息气泡基础样式 */
.message {
  max-width: 60%;
  border: 1px solid #1a1a1a;
  border-radius: 16px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #1a1a1a;
  background: #ffffff;
}

/* 左侧（AI/系统）消息样式 */
.message-ai {
  align-self: flex-start;
}

/* 右侧（用户）消息样式 */
.message-user {
  align-self: flex-end;
  background: #3d82f5;
  color: #ffffff;
  border-color: #3d82f5;
}