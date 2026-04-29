import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

import App from './App.vue'
import './styles/index.scss'

// 初始化应用
async function initApp() {
  const app = createApp(App)

  // 注册Element Plus图标
  for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
  }

  // 使用插件
  const pinia = createPinia()
  app.use(pinia)
  app.use(router)
  app.use(ElementPlus, {
    locale: zhCn,
    size: 'default'
  })

  // 初始化认证状态
  const { useAuthStore } = await import('@/stores/auth')
  const authStore = useAuthStore()
  
  try {
    await authStore.initAuth()
    console.log('认证状态初始化完成')
  } catch (error) {
    console.error('认证状态初始化失败:', error)
  }

  // 挂载应用
  app.mount('#app')
}

// 启动应用
initApp()
