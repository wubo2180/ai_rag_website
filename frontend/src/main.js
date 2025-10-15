import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'

const app = createApp(App)

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus)

// 初始化用户认证状态
const userStore = useUserStore()
userStore.initAuth()

// 异步验证token（不阻塞应用启动）
userStore.validateToken().then(isValid => {
  if (isValid) {
    console.log('用户认证验证成功')
  } else {
    console.log('用户认证验证失败或未登录')
  }
}).catch(error => {
  console.error('用户认证验证错误:', error)
})

app.mount('#app')