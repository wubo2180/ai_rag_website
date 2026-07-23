<template>
  <div :class="['left-nav', { collapsed: isCollapsed }]">
    <div class="nav-header">
      <img
        src="../assets/talk page/talk@3X_03.png"
        class="logo"
        v-show="!isCollapsed"
        alt="Logo"
      />
      <button @click="toggleNav" class="collapse-btn">
        <img
          src="../assets/talk page/talk@3X_40.png"
          alt="Toggle Navigation"
          class="collapse-icon"
        />
      </button>
    </div>
    <div class="user-profile" :class="{ clickable: isLoggedIn }" @click="navigateToProfile">
      <div class="avatar" :style="avatarStyle"></div>
      <div class="user-details">
        <div v-if="isLoggedIn">
          <p class="username">{{ username }}</p>
          <p class="greeting">您好！</p>
        </div>
        <div v-else>
          <button class="login-btn-outline" @click.prevent="goLogin">
            {{ isCollapsed ? '登录' : '立即登录' }}
          </button>
          <!-- <p class="register-link" @click.prevent="goRegister">注册</p> -->
        </div>
      </div>
    </div>
    <ul class="menu-items">
      <li>
        <a href="#" @click.prevent="startNewChat"
          ><img
            src="../assets/talk page/talk@3X_10.png"
            class="menu-icon"
          /><span class="menu-text"> 新建对话</span
          ><span class="tooltip">新建对话</span></a
        >
      </li>
      <!-- <li>
        <a href="#" @click.prevent="navigateToChat"
          ><img
            src="../assets/talk page/talk@3X_21.png"
            class="menu-icon"
          /><span class="menu-text"> 当前对话</span
          ><span class="tooltip">当前对话</span></a
        >
      </li> -->
      <li>
        <a href="#" @click.prevent="toggleHistory"
          ><img
            src="../assets/talk page/talk@3X_28.png"
            class="menu-icon"
          /><span class="menu-text"> 对话历史</span
          ><span class="tooltip">对话历史</span></a
        >
      </li>
      <li>
        <a href="#" @click.prevent="navigateToSmartAgents"
          ><img
            src="../assets/talk page/talk@3X_47.png"
            class="menu-icon"
          /><span class="menu-text"> AI 智能体</span
          ><span class="tooltip">AI 智能体</span></a
        >
      </li>
      <li>
        <a href="#" @click.prevent="navigateToOCRCenter"
          ><img
            src="../assets/talk page/talk@3X_73.png"
            class="menu-icon"
          /><span class="menu-text"> OCR中心</span
          ><span class="tooltip">OCR中心</span></a
        >
      </li>
      <li v-if="isAdmin">
        <a href="#" @click.prevent="navigateToDocuments"
          ><img
            src="../assets/talk page/talk@3X_63.png"
            class="menu-icon"
          /><span class="menu-text"> 文档管理</span
          ><span class="tooltip">文档管理</span></a
        >
      </li>
      <li v-if="isAdmin">
        <a href="#" @click.prevent="navigateToKnowledgeBase"
          ><img
            src="../assets/talk page/talk@3X_67.png"
            class="menu-icon"
          /><span class="menu-text"> 知识库</span
          ><span class="tooltip">知识库</span></a
        >
      </li>
      <li v-if="isAdmin">
        <a href="#" @click.prevent="navigateToKnowledgeGraph"
          ><img
            src="../assets/talk page/talk@3X_71.png"
            class="menu-icon"
          /><span class="menu-text"> 知识图谱</span
          ><span class="tooltip">知识图谱</span></a
        >
      </li>
      <li v-if="isAdmin">
        <a href="#" @click.prevent="navigateToUserManagement"
          ><img
            src="../assets/talk page/talk@3X_74.png"
            class="menu-icon"
          /><span class="menu-text"> 用户管理</span
          ><span class="tooltip">用户管理</span></a
        >
      </li>
    </ul>
    <div class="logout-section">
      <a href="#" class="logout-link" @click.prevent="handleLogout">
        <img
          src="../assets/talk page/talk-xt-@3_10.png"
          alt="logout"
          class="logout-icon"
        />
        注销登录
      </a>
    </div>
  </div>
</template>

<script>
  import { ref, computed } from 'vue'
  import { useRouter } from 'vue-router'
  import { useUserStore } from '@/stores/user'

  export default {
    name: 'NavigationSidebar',
    emits: ['toggle-history', 'start-new-chat'],
    setup(props, { emit }) {
      const router = useRouter()
      const userStore = useUserStore()
      const isCollapsed = ref(false)

      const isLoggedIn = computed(() => userStore.isAuthenticated)
      const username = computed(() => userStore.user?.username || '')
      const isAdmin = computed(() => userStore.user?.profile?.role === 'ADMIN')
      const avatarStyle = computed(() => {
        const avatarUrl = userStore.user?.profile?.avatar_url
        if (avatarUrl) {
          return {
            backgroundImage: `url(${avatarUrl})`,
          }
        }
        return {}
      })

      const toggleNav = () => {
        isCollapsed.value = !isCollapsed.value
      }

      const toggleHistory = () => {
        // 如果当前不在 Chat 页面，先导航到 Chat 页面
        if (router.currentRoute.value.path !== '/chat') {
          router.push('/chat')
        } else {
          emit('toggle-history')
        }
      }

      const navigateToChat = () => {
        // 导航到 Chat 页面
        if (router.currentRoute.value.path !== '/chat') {
          router.push('/chat')
        }
      }

      const startNewChat = () => {
        // 如果当前不在 Chat 页面，先导航到 Chat 页面
        if (router.currentRoute.value.path !== '/chat') {
          router.push('/chat')
        } else {
          emit('start-new-chat')
        }
      }

      const goLogin = () => {
        router.push({ path: '/login', query: { mode: 'login' } })
      }

      const goRegister = () => {
        router.push({ path: '/login', query: { mode: 'register' } })
      }

      const navigateToSmartAgents = () => {
        router.push('/smart-agents')
      }

      const navigateToProfile = () => {
        if (!isLoggedIn.value) return
        router.push('/profile')
      }

      const navigateToOCRCenter = () => {
        router.push('/ocr-center')
      }

      const navigateToDocuments = () => {
        if (!isAdmin.value) {
          console.warn('需要管理员权限访问文档管理')
          return
        }
        router.push('/documents')
      }

      const navigateToKnowledgeBase = () => {
        if (!isAdmin.value) {
          console.warn('需要管理员权限访问知识库')
          return
        }
        router.push('/knowledge-base')
      }

      const navigateToKnowledgeGraph = () => {
        if (!isAdmin.value) {
          console.warn('需要管理员权限访问知识图谱')
          return
        }
        router.push('/knowledge-graph')
      }

      const navigateToUserManagement = () => {
        if (!isAdmin.value) {
          console.warn('需要管理员权限访问用户管理')
          return
        }
        router.push('/user-management')
      }

      const handleLogout = async () => {
        try {
          await userStore.logout()
          // 清除本地聊天数据
          localStorage.removeItem('ai-chat-user')
          localStorage.removeItem('ai-chat2-session')
          localStorage.removeItem('ai-chat2-history')
          // 跳转到登录页
          router.push('/login')
        } catch (error) {
          console.error('退出登录失败:', error)
        }
      }

      return {
        isCollapsed,
        isLoggedIn,
        username,
        isAdmin,
        avatarStyle,
        toggleNav,
        toggleHistory,
        navigateToChat,
        startNewChat,
        goLogin,
        goRegister,
        navigateToSmartAgents,
        navigateToProfile,
        navigateToOCRCenter,
        navigateToDocuments,
        navigateToKnowledgeBase,
        navigateToKnowledgeGraph,
        navigateToUserManagement,
        handleLogout,
      }
    },
  }
</script>

<style scoped>
  .left-nav {
    width: 240px;
    background: linear-gradient(to bottom, #ffffff, #e6f7ff);
    border-right: 1px solid #e0e0e0;
    transition: width 0.3s;
    display: flex;
    flex-direction: column;
    padding: 20px 10px;
    align-items: center; /* Center items horizontally */
    position: relative;
  }

  .left-nav.collapsed {
    width: 80px;
    align-items: center;
  }

  .nav-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    margin-bottom: 20px;
  }
  /* 折叠时：将导航头部居中，保证缩放图标居中 */
  .left-nav.collapsed .nav-header {
    justify-content: center;
  }

  .logo {
    height: 40px; /* Adjust as needed */
    width: auto;
  }

  .collapse-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
  }

  .collapse-icon {
    width: 24px;
    height: 24px;
    transition: transform 0.3s;
  }

  .left-nav:not(.collapsed) .collapse-icon {
    transform: rotate(180deg);
  }

  .user-profile {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-bottom: 20px;
    min-height: 130px; /* Set a fixed min-height to prevent any movement */
  }

  .user-profile.clickable {
    cursor: pointer;
    border-radius: 12px;
    padding: 8px 10px;
    transition: all 0.2s ease;
  }

  .user-profile.clickable:hover {
    background: rgba(59, 130, 246, 0.08);
  }

  .user-details {
    transition:
      visibility 0.3s,
      opacity 0.3s;
    text-align: center;
    height: 60px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .left-nav.collapsed .user-details {
    visibility: visible; /* 保留登录入口在折叠态 */
    opacity: 1;
  }
  .left-nav.collapsed .username,
  .left-nav.collapsed .greeting,
  .left-nav.collapsed .register-link {
    display: none; /* 折叠态隐藏用户名、问候与注册，仅保留登录 */
  }
  .left-nav.collapsed .login-btn-outline {
    width: auto; /* 折叠态仅显示"登录"两字，宽度自适应 */
    padding: 8px 20px; /* 增加水平内边距，让提示框加长一点 */
  }

  .avatar {
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background-color: #d8d8d8;
    margin-bottom: 10px;
    background-image: url('../assets/talk page/talk@3x_08.png'); /* Placeholder for user avatar */
    background-size: cover;
  }

  .username {
    font-weight: bold;
  }

  .greeting {
    font-size: 12px;
    color: #888;
  }

  .register-link {
    font-size: 16px; /* 导航菜单中注册字体调小为16px */
    color: #3b82f6; /* 蓝色 */
    text-align: center;
    cursor: pointer;
    display: inline-block;
    padding: 8px 0;
    width: 220px; /* 接近导航栏宽度（240px），考虑左右内边距 */
    border: none;
    border-radius: 999px; /* 保持圆角，但默认不显示描边 */
    margin-top: 5px; /* 与登录按钮的间距 */
    font-weight: 400; /* 与"新建对话"字重一致 */
  }

  .login-btn-outline {
    background: transparent;
    border: none; /* 默认无描边 */
    color: #60a5fa;
    padding: 8px 0;
    margin-top: 50px; /* 下移，避免挡住头像 */
    border-radius: 999px;
    cursor: pointer;
    font-weight: 400; /* 与"新建对话"保持一致，不加粗 */
    font-size: 16px; /* 导航菜单中登录字体调小为16px */
    width: 220px; /* 接近导航栏宽度（240px） */
    display: inline-block;
    box-sizing: border-box;
  }
  .login-btn-outline:hover,
  .register-link:hover {
    background: #ffffff; /* 悬停时出现白底提示 */
    border: 1px solid #93c5fd; /* 淡蓝描边 */
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.18);
  }

  .menu-items {
    list-style: none;
    padding: 0;
    width: 100%;
    flex-grow: 1;
  }

  .menu-items li {
    margin-bottom: 20px; /* Spacing between items */
  }

  .menu-items a {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 10px;
    text-decoration: none;
    color: #333;
    border-radius: 8px;
    transition:
      background-color 0.3s,
      color 0.3s;
    position: relative; /* For tooltip positioning */
    box-sizing: border-box;
  }

  /* .menu-items a:hover {
    border: 1px solid #004080;
  }

  .menu-items a:hover .menu-icon {
    filter: brightness(0) invert(1);
  } */

  .menu-items a .tooltip {
    visibility: hidden;
    position: absolute;
    background-color: #333;
    color: #fff;
    padding: 5px 10px;
    border-radius: 4px;
    white-space: nowrap;
    z-index: 11000; /* 提升层级，避免被历史记录覆盖 */
    opacity: 0;
    transition: opacity 0.2s;
    pointer-events: none; /* So it doesn't interfere with the mouse */

    /* Position to the bottom-right of the icon */
    left: 75px;
    top: 30px;
  }

  .left-nav.collapsed .menu-items li a:hover .tooltip {
    visibility: visible;
    opacity: 1;
  }

  .menu-icon {
    width: 20px;
    height: 20px;
    margin-right: 10px;
  }

  .left-nav.collapsed .menu-icon {
    margin-right: 0;
  }

  .menu-items a span:first-child {
    margin-right: 10px;
    font-size: 20px;
  }

  .menu-items .active a {
    background-color: #007bff;
    color: white;
  }

  .menu-text {
    white-space: nowrap;
    opacity: 1;
    transition:
      opacity 0.2s 0.1s,
      width 0.3s;
    width: auto;
    overflow: hidden;
  }

  .left-nav.collapsed .menu-text {
    opacity: 0;
    width: 0;
    transition:
      opacity 0.1s,
      width 0.3s;
  }

  .logout-section {
    padding: 10px;
    text-align: center;
    opacity: 1;
    transition: opacity 0.3s;
  }

  .left-nav.collapsed .logout-section {
    opacity: 0;
  }

  .logout-section a {
    text-decoration: none;
  }
  .logout-link {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #3b82f6; /* 蓝色 */
  }
  .logout-icon {
    width: 18px;
    height: 18px;
  }
</style>
