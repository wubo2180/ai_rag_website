import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Chat from '../views/Chat.vue'
import Terms from '../views/Terms.vue'
import Privacy from '../views/Privacy.vue'

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
    path: '/login2',
    redirect: '/login',
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
    component: () => import('@/views/Chat.vue'),
    meta: { requiresAuth: false }, // 允许匿名访问聊天
  },
  // {
  //   path: '/chatnewui',
  //   name: 'ChatNewUI',
  //   component: () => import('@/views/ChatNewUI.vue'),
  //   meta: {
  //     requiresAuth: false,
  //     title: '智能对话',
  //   },
  // },
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
    path: '/terms',
    name: 'Terms',
    component: Terms,
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: Privacy,
  },
  {
    path: '/chat2',
    redirect: '/chat',
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
    path: '/ocr-center',
    name: 'OCRCenter',
    component: () => import('@/views/OCRCenter.vue'),
    meta: {
      requiresAuth: false,
      title: 'OCR中心',
    },
  },
  {
    path: '/ocr-center/:service',
    name: 'OCRServiceWorkbench',
    component: () => import('@/views/OCRServiceWorkbench.vue'),
    meta: {
      requiresAuth: false,
      title: 'OCR服务工作台',
    },
  },
  {
    path: '/formula-generation',
    name: 'FormulaGeneration',
    component: () => import('@/views/FormulaGeneration.vue'),
    meta: {
      requiresAuth: false,
      title: '配方生成',
    },
  },
  {
    path: '/process-optimization',
    name: 'ProcessOptimization',
    component: () => import('@/views/ProcessOptimization.vue'),
    meta: {
      requiresAuth: false,
      title: '工艺优化',
    },
  },
  {
    path: '/data-analysis',
    name: 'DataAnalysis',
    component: () => import('@/views/DataAnalysis.vue'),
    meta: {
      requiresAuth: false,
      title: '数据分析',
    },
  },
  {
    path: '/property-prediction',
    name: 'PropertyPrediction',
    component: () => import('@/views/PropertyPrediction.vue'),
    meta: {
      requiresAuth: false,
      title: '性质预测',
    },
  },
  {
    path: '/decision-support',
    name: 'DecisionSupport',
    component: () => import('@/views/DecisionSupport.vue'),
    meta: {
      requiresAuth: false,
      title: '决策支持',
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
