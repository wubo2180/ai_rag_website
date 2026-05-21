<template>
  <!-- 
    背景现在直接应用在这个主容器上。
    它的最小尺寸被CSS固定为1920x1080。
  -->
  <div class="home-container" :style="bgStyle">
    <header class="home-header">
      <div class="left-brand">
        <img :src="logoTopLeft" alt="IBOX Materix" class="brand-logo" />
        <ul class="top-menu">
          <li v-for="(item,i) in menuItems" :key="i" class="menu-item">{{ item }}</li>
        </ul>
      </div>
      <nav class="home-nav">
        <div class="login-register">
          <button class="lr-btn" @click="goLogin">登录</button>
          <span class="lr-divider">｜</span>
          <button class="lr-btn" @click="goRegister">注册</button>
        </div>
      </nav>
    </header>

    <main class="home-main">
      <div class="hero">
        <div class="search-box">
          <textarea
            ref="questionTextarea"
            v-model="question"
            class="question-textarea"
            rows="3"
            placeholder="向IBOX Materix提问"
            @keydown="handleKeydown"
            @input="handleInput"
            @focus="fetchSuggestions"
            @blur="clearSuggestions"
          ></textarea>
          <!-- Baidu 提示词列表 -->
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
          <div class="search-actions">
            <div class="left-actions">
              <button class="chip source" :class="{ open: sourceDropdownOpen }" @click="toggleSourceDropdown">
                <span>{{ sourceLabel }}</span>
                <img :src="iconAll" alt="数据源" class="chip-icon-right" />
              </button>
              <div v-if="sourceDropdownOpen" class="dropdown">
                <div class="dropdown-item" @click="selectSource('all')">全部</div>
                <div class="dropdown-item" @click="selectSource('internal')">内部数据库</div>
                <div class="dropdown-item" @click="selectSource('external')">外部数据库</div>
              </div>
              <button class="chip" :class="{ active: deepActive }" @click="toggleDeep">
                <img :src="iconDeep" alt="深度搜索" class="chip-icon" />
                <span>深度搜索</span>
              </button>
            </div>
            <button class="ask-btn" :class="{ disabled: !question.trim() }" :title="askBtnTitle" @click="startChat">
              <img :src="iconAsk" alt="立即提问" class="ask-icon" />
              <span>立即提问</span>
            </button>
          </div>
        </div>

        <div class="suggestions">
          <div class="s-title">热门问题</div>
          <div class="s-list">
            <button
              v-for="(s, i) in suggestionList"
              :key="i"
              class="s-chip"
              @click="useSuggestion(s)"
            >{{ s }}</button>
          </div>
        </div>
      </div>

      <img :src="logoBottom" class="bottom-logo" alt="IBOX Materix" />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import homeBg from '@/assets/home page/主页1920_1080.png'
import logoBottom from '@/assets/home page/home@3X_19.png'
import logoTopLeft from '@/assets/home page/home@3X_03.png'
import iconAll from '@/assets/home page/home@3_06.png'
import iconDeep from '@/assets/home page/home@3_03.png'
import iconAsk from '@/assets/home page/home@3_09.png'

const router = useRouter()
const question = ref('')
const questionTextarea = ref(null)
// Baidu 提示词状态
const suggestions = ref([])
const debounceTimer = ref(null)
const selectedIndex = ref(-1)

const menuItems = [
  '智能检索','智能对话','AI 智能体','知识库','知识图谱','我的任务'
]

const suggestionList = [
  '在性能检测中，铝基与镁基的产品有哪些参考？',
  '粉末冶金的构件有哪些常见缺陷？',
  '在连接焊接中，材料如何减少热影响区影响？',
  '稀有金属的镍钴合金有哪些推荐方案？'
]

const bgStyle = computed(() => ({
  // 这个计算属性保持不变，它做得很好
  backgroundImage: `url(${homeBg})`
}))

const sourceType = ref('all')
const sourceDropdownOpen = ref(false)
const deepActive = ref(false)

const sourceLabel = computed(() => {
  if (sourceType.value === 'internal') return '内部数据库'
  if (sourceType.value === 'external') return '外部数据库'
  return '全部'
})

const toggleSourceDropdown = () => { sourceDropdownOpen.value = !sourceDropdownOpen.value }
const selectSource = (t) => { sourceType.value = t; sourceDropdownOpen.value = false }
const toggleDeep = () => { deepActive.value = !deepActive.value }

const askBtnTitle = computed(() => (question.value.trim() ? '立即提问' : '请输入问题后再提问'))

const startChat = () => {
  const prompt = question.value.trim()
  if (!prompt) return
  router.push({ path: '/chat', query: { prompt, source: sourceType.value, deep: deepActive.value ? '1' : '0' } })
}

const useSuggestion = (s) => {
  question.value = s
  startChat()
}

// --- 提示词相关逻辑 ---
const handleKeydown = (event) => {
  if (suggestions.value.length > 0) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      selectedIndex.value = (selectedIndex.value + 1) % suggestions.value.length
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
      }
    } else if (event.key === 'Escape') {
      event.preventDefault()
      clearSuggestions()
    }
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
  const query = question.value.trim()
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
  script.src = `https://suggestion.baidu.com/su?wd=${encodeURIComponent(query)}&cb=window.handleBaiduSuggestions`
  
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
  question.value = suggestion
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
  if (!question.value.trim()) return text
  const query = question.value.trim()
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
  return text.replace(regex, '<strong>$1</strong>')
}

onMounted(() => {
  window.handleBaiduSuggestions = (data) => {
    suggestions.value = data.s || []
    selectedIndex.value = -1
  }
})

onUnmounted(() => {
  delete window.handleBaiduSuggestions
  const scriptId = 'baidu-jsonp-script'
  const existingScript = document.getElementById(scriptId)
  if (existingScript && existingScript.parentNode) {
    existingScript.parentNode.removeChild(existingScript)
  }
})

const goLogin = () => router.push('/login')
const goRegister = () => router.push({ path: '/login', query: { mode: 'register' } })
</script>

<style scoped>
/* 
  关键改动 1: 全局样式
  我们让 html 和 body 能够滚动，并使用 flex 布局来居中我们的主容器。
  这在屏幕大于1920x1080时使其居中，在小于时使其可以滚动。
*/
:global(html), :global(body) {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: auto; /* 允许 body 出现滚动条 */
}

:global(body) {
  display: flex;
  justify-content: flex-start; /* 水平居左 */
  align-items: flex-start;    /* 垂直居上 */
}


/* 
  关键改动 2: 主容器样式
  我们给它设置了固定的最小尺寸，并让背景图不重复。
*/
.home-container {
  min-width: 1920px;
  min-height: 1080px;
  background-size: 1920px 1080px; /* 固定背景尺寸 */
  background-position: top left;
  background-repeat: no-repeat;
  display: flex;
  flex-direction: column;
  position: relative;
  justify-content: flex-start; /* 从顶部开始排列 */
  /* 移除了 width: 100vw 和 min-height: 100vh */
}

.home-header {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 240px 0 240px;
  position: relative;
  z-index: 5;
  /* 使用 flex-shrink: 0 防止页头在 flex 布局中被压缩 */
  flex-shrink: 0;
}

.left-brand { display: flex; align-items: center; gap: 60px; }
.brand-logo { height: 34px; width: auto; }

.top-menu { list-style: none; display: flex; gap: 60px; padding: 0; margin: 0; }
.menu-item { color: rgba(255,255,255,0.92); font-size: 14px; font-weight: 600; letter-spacing: 0.5px; cursor: pointer; }
.menu-item:hover { color: #ffffff; text-shadow: 0 0 6px rgba(255,255,255,0.35); }
.home-nav { display: flex; align-items: center; }
.login-register {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 16px;
  border-radius: 9999px;
  border: 1.5px solid rgba(255,255,255,0.95);
  background: rgba(255,255,255,0.14);
  color: #ffffff;
}
.lr-btn { background: transparent; border: none; color: inherit; font-weight: 700; cursor: pointer; opacity: 0.95; }
.lr-btn:hover { opacity: 1; }
.lr-divider { color: rgba(255,255,255,0.95); }

.home-main {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-start; /* 内容从顶部开始排列 */
  align-items: center; /* 水平居中 flex 子项 */
  flex-direction: column;
  position: relative; /* 成为子元素绝对定位的参照物 */
  padding: 0 24px;
}

.hero { width: 1100px; margin-top: 350px; } /* 使用 margin-top 控制与顶部的距离 */
.hero-logo { text-align: center; margin: 10px 0 6px 0; }
.ibox { font-size: 36px; font-weight: 800; color: #2b6cb0; letter-spacing: 1px; }
.materix { font-size: 36px; font-weight: 800; color: #5b8def; margin-left: 6px; }
.hero-title { text-align: center; font-size: 24px; color: #111827; margin: 0 0 14px 0; }

.search-box {
  background: rgba(255,255,255,0.22);
  border: 1px solid rgba(255,255,255,0.55);
  border-radius: 22px;
  box-shadow: 0 10px 28px rgba(0,0,0,0.08);
  padding: 50px; /* 统一内边距，并增加高度 */
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-sizing: border-box;
  position: relative;
  z-index: 2;
}
.question-textarea {
  width: 100%; /* 填充容器 */
  max-width: 100%;
  margin: 0;
  resize: none;
  border: 1.5px solid #5b8def;
  border-radius: 16px;
  padding: 14px;
  background: transparent; /* 保持透明背景 */
  font-size: 15px;
  color: #111827;
  box-sizing: border-box;
  min-height: 140px; /* 再次缩小高度 */
  display: block;
  overflow: auto;
}
.question-textarea::placeholder { color: rgba(17,24,39,0.60); }
.question-textarea:focus { outline: none; border-color: #5b8def; box-shadow: 0 0 0 3px rgba(91,141,239,0.20); }

/* 新增：Baidu 提示词列表样式 */
.suggestions-list { 
  margin-top: 10px; 
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

.search-actions { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; width: 100%; }
.left-actions { display: flex; gap: 12px; position: relative; }
.chip {
  display: flex; align-items: center; gap: 8px;
  border-radius: 18px;
  padding: 8px 14px;
  background: rgba(255,255,255,0.85);
  border: 1px solid rgba(0,0,0,0.06);
  color: #334155;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.chip.active { background: #5b8def; color: #ffffff; border-color: #5b8def; }
.chip-icon { width: 18px; height: 18px; }
.chip span { font-size: 13px; }
.chip-icon-right { width: 18px; height: 18px; margin-left: 8px; transition: transform 0.2s ease; }
.chip.source.open .chip-icon-right { transform: rotate(-90deg); }

.dropdown {
  position: absolute;
  top: 44px;
  left: 0;
  min-width: 180px;
  background: rgba(255,255,255,0.92);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 12px;
  box-shadow: 0 12px 28px rgba(0,0,0,0.12);
  backdrop-filter: blur(8px);
  z-index: 1000;
}
.dropdown-item {
  padding: 10px 12px;
  font-size: 14px;
  color: #1f2937;
  cursor: pointer;
}
.dropdown-item:hover { background: rgba(91,141,239,0.12); }

.ask-btn {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  border-radius: 18px;
  background: rgba(255,255,255,0.88);
  border: 1px solid rgba(0,0,0,0.06);
  color: #334155;
  cursor: pointer;
  transition: background 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease, transform 0.1s ease;
}
.ask-btn:hover { background: rgba(255,255,255,0.98); border-color: rgba(91,141,239,0.50); box-shadow: 0 6px 20px rgba(91,141,239,0.30); }
.ask-btn.disabled { opacity: 0.6; cursor: not-allowed; }
.ask-btn.disabled:hover { background: rgba(255,255,255,0.88); border-color: rgba(0,0,0,0.06); box-shadow: none; }
.ask-icon { width: 18px; height: 18px; }

.suggestions { margin-top: 14px; position: relative; z-index: 1; }
.s-title { color: #374151; font-size: 14px; margin-bottom: 8px; }
.s-list { display: flex; flex-wrap: wrap; gap: 10px; }
.s-chip { padding: 6px 10px; border-radius: 14px; background: rgba(255,255,255,0.28); border: 1px solid rgba(255,255,255,0.4); color: #374151; backdrop-filter: blur(6px); -webkit-backdrop-filter: blur(6px); font-size: 13px; cursor: pointer; transition: background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease, color 0.2s ease; }
.s-chip:hover { background: rgba(91,141,239,0.18); border-color: rgba(91,141,239,0.38); box-shadow: 0 4px 16px rgba(91,141,239,0.24); color: #1f2937; }

.bottom-logo {
  margin-top: auto; /* 自动推至底部 */
  margin-bottom: 40px; /* 距离底部 40px */
  height: 64px;
  width: auto;
  z-index: 4;
}

/* 
  关键改动 3: 移除了 .bg-layer 样式和所有的 @media 响应式查询
  因为我们不再需要一个单独的背景层，也不再需要页面根据屏幕宽度改变布局。
*/

</style>