import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/',
    redirect: '/chat',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/chat',
    name: 'Chat',
    component: () => import('@/views/ChatNewUI.vue'),
    meta: { requiresAuth: false }, // 允许匿名访问聊天
  },
  {
    path: '/ChatNewUI',
    name: 'ChatNewUI',
    component: () => import('@/views/ChatNewUI.vue'),
    meta: {
      requiresAuth: false,
      title: '智能对话',
    },
  },
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/views/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/sessions',
    name: 'ChatSessions',
    component: () => import('@/views/ChatSessions.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/documents',
    name: 'Documents',
    component: () => import('@/views/Documents.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/knowledge-base',
    name: 'KnowledgeBase',
    component: () => import('@/views/KnowledgeBase.vue'),
    meta: {
      requiresAuth: false,
      title: '知识库管理',
    },
  },
  {
    path: '/knowledge-graph',
    name: 'KnowledgeGraph',
    component: () => import('@/views/KnowledgeGraph.vue'),
    meta: {
      requiresAuth: false,
      title: '材料知识图谱',
    },
  },
  {
    path: '/smart-agents',
    name: 'SmartAgents',
    component: () => import('@/views/SmartAgents.vue'),
    meta: {
      requiresAuth: true,
      title: 'AI智能体',
    },
  },
  {
    path: '/agents/:id',
    name: 'AgentDetail',
    component: () => import('@/views/AgentDetail.vue'),
    meta: {
      requiresAuth: true,
      title: '智能体详情',
    },
  },
  {
    path: '/agent-tasks',
    name: 'AgentTasks',
    component: () => import('@/views/AgentTasks.vue'),
    meta: {
      requiresAuth: true,
      title: '我的任务',
    },
  },
  {
    path: '/knowledge-extraction',
    name: 'KnowledgeExtraction',
    component: () => import('@/views/KnowledgeExtraction.vue'),
    meta: {
      requiresAuth: false,
      title: '知识抽取智能体',
    },
  },
  {
    path: '/user-management',
    name: 'UserManagement',
    component: () => import('@/views/UserManagement.vue'),
    meta: {
      requiresAuth: true,
      title: '用户管理',
    },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router
