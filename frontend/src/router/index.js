import { createRouter, createWebHistory } from 'vue-router'
import Home from '../components/Home.vue'
import Login from '../components/Login.vue'
import Chat from '../components/Chat.vue'
import Terms from '../components/Terms.vue'
import Privacy from '../components/Privacy.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/login2',
    redirect: '/login'
  },
  {
    path: '/chat',
    name: 'Chat',
    component: Chat
  },
  {
    path: '/terms',
    name: 'Terms',
    component: Terms
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: Privacy
  },
  {
    path: '/chat2',
    redirect: '/chat'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const isAuthenticated = localStorage.getItem('ai-chat-user')
  
  if ((to.path === '/login' || to.path === '/login2') && isAuthenticated) {
    // 已登录但访问登录页，跳转到聊天页
    next('/chat')
  } else {
    next()
  }
})

export default router