import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'

// 创建axios实例
const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    console.log('🔍 API请求调试信息:')
    console.log('   URL:', config.url)
    console.log('   Method:', config.method)
    console.log('   Token存在:', !!authStore.accessToken)
    console.log('   Token:', authStore.accessToken ? authStore.accessToken.substring(0, 50) + '...' : 'null')
    
    // 添加认证头
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
      console.log('   Authorization header已设置')
    } else {
      console.log('   ❌ 没有Token，未设置Authorization header')
    }
    
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    console.log('📥 API响应:', response.config.url, '状态:', response.status)
    console.log('📦 响应数据:', response.data)
    return response  // 返回完整的 response，让调用方访问 response.data
  },
  async (error) => {
    const authStore = useAuthStore()
    const appStore = useAppStore()
    
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 令牌过期或无效
          if (data.message?.includes('过期') || data.message?.includes('expired')) {
            // 尝试刷新令牌
            const refreshSuccess = await authStore.refreshAccessToken()
            if (refreshSuccess) {
              // 重试原请求
              return request(error.config)
            }
          }
          
          // 刷新失败或其他认证错误，重定向到登录页
          authStore.clearAuthData()
          if (window.location.pathname !== '/login') {
            window.location.href = '/login'
          }
          appStore.showMessage('登录已过期，请重新登录', 'warning')
          break
          
        case 403:
          appStore.showMessage('没有权限访问此资源', 'error')
          break
          
        case 404:
          appStore.showMessage('请求的资源不存在', 'error')
          break
          
        case 429:
          appStore.showMessage('请求过于频繁，请稍后重试', 'warning')
          break
          
        case 500:
          appStore.showMessage('服务器内部错误', 'error')
          break
          
        default:
          appStore.showMessage(data.message || '网络请求失败', 'error')
      }
    } else if (error.code === 'ECONNABORTED') {
      appStore.showMessage('请求超时，请检查网络连接', 'error')
    } else {
      appStore.showMessage('网络连接失败，请检查网络', 'error')
    }
    
    return Promise.reject(error)
  }
)

// 上传文件专用的axios实例
export const uploadRequest = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 300000, // 5分钟超时，用于大文件上传
  headers: {
    'Content-Type': 'multipart/form-data'
  }
})

// 上传请求拦截器
uploadRequest.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    
    if (authStore.accessToken) {
      config.headers.Authorization = `Bearer ${authStore.accessToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 上传响应拦截器
uploadRequest.interceptors.response.use(
  (response) => response,
  (error) => {
    const appStore = useAppStore()
    
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.clearAuthData()
      window.location.href = '/login'
    } else {
      appStore.showMessage('上传失败，请重试', 'error')
    }
    
    return Promise.reject(error)
  }
)

export default request
