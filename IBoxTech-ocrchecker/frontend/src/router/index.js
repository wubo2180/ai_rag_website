import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

// 路由组件懒加载
const Layout = () => import('@/components/Layout/index.vue')
const Login = () => import('@/views/Login/index.vue')
const Dashboard = () => import('@/views/Dashboard/index.vue')
const FileManagement = () => import('@/views/FileManagement/index.vue')
const FileUpload = () => import('@/views/FileUpload/index.vue')
const FileReview = () => import('@/views/FileReview/index.vue')
const FileRecognize = () => import('@/views/FileRecognize/index.vue')
const UserManagement = () => import('@/views/UserManagement/index.vue')
const ModelConfig = () => import('@/views/ModelConfig/index.vue')
const FileTypeConfig = () => import('@/views/FileTypeConfig/index.vue')
const Profile = () => import('@/views/Profile/index.vue')
const NotFound = () => import('@/views/NotFound/index.vue')

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: {
      title: '用户登录',
      requiresAuth: false
    }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    meta: {
      requiresAuth: true
    },
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: {
          title: '仪表盘',
          icon: 'Odometer'
        }
      },
      {
        path: 'files',
        name: 'FileManagement',
        component: FileManagement,
        meta: {
          title: '文件管理',
          icon: 'Folder'
        }
      },
      {
        path: 'upload',
        name: 'FileUpload',
        component: FileUpload,
        meta: {
          title: '文件上传',
          icon: 'Upload'
        }
      },
      {
        path: 'recognize/:fileId',
        name: 'FileRecognize',
        component: FileRecognize,
        meta: {
          title: '文件识别',
          hidden: true
        }
      },
      {
        path: 'review/:fileId',
        name: 'FileReview',
        component: FileReview,
        meta: {
          title: '文件核对',
          hidden: true
        }
      },
      {
        path: 'users',
        name: 'UserManagement',
        component: UserManagement,
        meta: {
          title: '用户管理',
          icon: 'User',
          requiresAdmin: true
        }
      },
      {
        path: 'system-config',
        name: 'SystemConfig',
        meta: {
          title: '系统配置',
          icon: 'Setting',
          requiresAdmin: true
        },
        redirect: '/model-config',
        children: [
          {
            path: '/model-config',
            name: 'ModelConfig',
            component: ModelConfig,
            meta: {
              title: '模型配置',
              icon: 'Connection',
              requiresAdmin: true
            }
          },
          {
            path: '/file-type-config',
            name: 'FileTypeConfig',
            component: FileTypeConfig,
            meta: {
              title: '文件类型配置',
              icon: 'Files',
              requiresAdmin: true
            }
          }
        ]
      },
      {
        path: 'profile',
        name: 'Profile',
        component: Profile,
        meta: {
          title: '个人中心',
          icon: 'UserFilled'
        }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: NotFound,
    meta: {
      title: '页面不存在'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 全局前置守卫
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()
  const appStore = useAppStore()
  
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - ${appStore.appConfig.title}` : appStore.appConfig.title
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    // 如果没有认证状态，尝试获取用户信息（仅当有token时）
    if (!authStore.checkAuth()) {
      if (authStore.accessToken && !authStore.user) {
        // 只有当有token但没有用户信息时才尝试获取
        const success = await authStore.fetchUserInfo()
        if (!success) {
          // 如果获取失败，清除可能无效的token
          authStore.clearAuthData()
        }
      }
      
      // 再次检查认证状态
      if (!authStore.checkAuth()) {
        next({
          path: '/login',
          query: { redirect: to.fullPath }
        })
        return
      }
    }
    
    // 检查管理员权限
    if (to.meta.requiresAdmin && !authStore.isAdmin) {
      appStore.showMessage('需要管理员权限访问此页面', 'error')
      next({ path: '/dashboard' })
      return
    }
  } else {
    // 如果已经认证且访问登录页，重定向到仪表盘
    if (to.path === '/login' && authStore.checkAuth()) {
      next({ path: '/dashboard' })
      return
    }
  }
  
  next()
})

// 全局后置钩子
router.afterEach((to, from) => {
  // 这里可以添加页面访问统计等逻辑
})

export default router
