import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/utils/api'

export const useUserStore = defineStore('user', () => {
  // 状态
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('access_token'))
  const refreshToken = ref(localStorage.getItem('refresh_token'))

  // 计算属性
  const isLoggedIn = computed(() => !!accessToken.value)
  const username = computed(() => user.value?.username || '')

  // 设置认证信息
  function setAuth(authData) {
    user.value = authData.user
    accessToken.value = authData.access
    refreshToken.value = authData.refresh
    
    localStorage.setItem('access_token', authData.access)
    localStorage.setItem('refresh_token', authData.refresh)
    
    // 设置API客户端的认证头
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${authData.access}`
  }

  // 清除认证信息
  function clearAuth() {
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    
    // 清除API客户端的认证头
    delete apiClient.defaults.headers.common['Authorization']
  }

  // 登录
  async function login(credentials) {
    try {
      const response = await apiClient.post('/auth/login/', credentials)
      setAuth(response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('登录失败:', error)
      return { 
        success: false, 
        error: error.response?.data?.message || '登录失败' 
      }
    }
  }

  // 注册
  async function register(userData) {
    try {
      const response = await apiClient.post('/auth/register/', userData)
      setAuth(response.data)
      return { success: true, data: response.data }
    } catch (error) {
      console.error('注册失败:', error)
      return { 
        success: false, 
        error: error.response?.data || '注册失败' 
      }
    }
  }

  // 登出
  async function logout() {
    try {
      if (refreshToken.value) {
        await apiClient.post('/auth/logout/', { 
          refresh: refreshToken.value 
        })
      }
    } catch (error) {
      console.error('登出请求失败:', error)
    } finally {
      clearAuth()
    }
  }

  // 获取用户信息
  async function fetchUserInfo() {
    try {
      const response = await apiClient.get('/auth/user-info/')
      user.value = response.data.user
      return { success: true, data: response.data }
    } catch (error) {
      console.error('获取用户信息失败:', error)
      return { success: false, error: '获取用户信息失败' }
    }
  }

  // 刷新Token
  async function refreshAccessToken() {
    try {
      if (!refreshToken.value) {
        throw new Error('没有刷新令牌')
      }

      const response = await apiClient.post('/auth/token/refresh/', {
        refresh: refreshToken.value
      })

      accessToken.value = response.data.access
      localStorage.setItem('access_token', response.data.access)
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${response.data.access}`

      return { success: true, data: response.data }
    } catch (error) {
      console.error('刷新Token失败:', error)
      clearAuth()
      return { success: false, error: 'Token刷新失败' }
    }
  }

  // 初始化认证状态
  function initAuth() {
    if (accessToken.value) {
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken.value}`
      console.log('已设置认证头:', `Bearer ${accessToken.value.substring(0, 20)}...`)
    } else {
      console.log('未找到访问令牌')
    }
  }

  // 验证token有效性（单独的异步方法）
  async function validateToken() {
    if (!accessToken.value) {
      return false
    }

    try {
      const response = await apiClient.get('/auth/user-info/')
      user.value = response.data.user
      console.log('Token验证成功，用户:', response.data.user.username)
      return true
    } catch (error) {
      console.log('Token验证失败:', error.response?.status)
      if (error.response?.status === 401) {
        clearAuth()
      }
      return false
    }
  }

  return {
    // 状态
    user,
    accessToken,
    refreshToken,
    
    // 计算属性
    isLoggedIn,
    username,
    
    // 方法
    setAuth,
    clearAuth,
    login,
    register,
    logout,
    fetchUserInfo,
    refreshAccessToken,
    initAuth,
    validateToken
  }
})