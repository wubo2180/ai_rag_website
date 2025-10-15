import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const apiClient = axios.create({
  baseURL: '/api', // Vite代理会将/api转发到Django后端
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 从localStorage获取token
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    console.error('请求拦截器错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config

    // 处理401错误（Token过期）
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')
        if (!refreshToken) {
          throw new Error('没有刷新令牌')
        }

        // 尝试刷新token
        const response = await axios.post('/api/auth/token/refresh/', {
          refresh: refreshToken
        })

        const newAccessToken = response.data.access
        localStorage.setItem('access_token', newAccessToken)

        // 更新请求头并重新发送原请求
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`
        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`

        return apiClient(originalRequest)
      } catch (refreshError) {
        console.error('Token刷新失败:', refreshError)
        
        // 清除所有认证信息
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        delete apiClient.defaults.headers.common['Authorization']

        // 重定向到登录页
        if (window.location.pathname !== '/login') {
          ElMessage.error('登录已过期，请重新登录')
          window.location.href = '/login'
        }

        return Promise.reject(refreshError)
      }
    }

    // 处理其他错误
    const errorMessage = error.response?.data?.error 
      || error.response?.data?.message 
      || error.message 
      || '请求失败'

    // 显示错误消息（除了401错误，因为已经处理了）
    if (error.response?.status !== 401) {
      ElMessage.error(errorMessage)
    }

    return Promise.reject(error)
  }
)

export default apiClient