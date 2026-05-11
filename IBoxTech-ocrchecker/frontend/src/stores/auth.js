import { defineStore } from 'pinia'
import { authApi } from '@/api/auth'
import { useAppStore } from './app'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // 用户信息
    user: null,
    
    // 认证状态
    isAuthenticated: false,
    
    // JWT令牌
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
    
    // 登录状态
    isLoggingIn: false,
    
    // 权限列表
    permissions: []
  }),

  getters: {
    // 是否为管理员
    isAdmin() {
      return this.user?.role === 'admin'
    },
    
    // 用户显示名称
    displayName() {
      return this.user?.real_name || this.user?.username || '未知用户'
    },
    
    // 是否有权限
    hasPermission() {
      return (permission) => {
        if (this.isAdmin) return true
        return this.permissions.includes(permission)
      }
    }
  },

  actions: {
    // 登录
    async login(credentials) {
      const appStore = useAppStore()
      
      try {
        this.isLoggingIn = true
        
        const response = await authApi.login(credentials)
        
        if (response.data.success) {
          const { user, access_token, refresh_token } = response.data.data
          
          console.log('🎯 登录成功调试信息:')
          console.log('   用户信息:', user)
          console.log('   Access Token:', access_token ? access_token.substring(0, 50) + '...' : 'null')
          console.log('   Refresh Token:', refresh_token ? refresh_token.substring(0, 50) + '...' : 'null')
          
          // 保存用户信息和令牌
          this.user = user
          this.accessToken = access_token
          this.refreshToken = refresh_token
          this.isAuthenticated = true
          
          console.log('   Store状态更新完成')
          console.log('   isAuthenticated:', this.isAuthenticated)
          console.log('   checkAuth():', this.checkAuth())
          
          // 保存到本地存储
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', refresh_token)
          console.log('   Token已保存到localStorage')
          
          appStore.showMessage('登录成功', 'success')
          
          return { success: true }
        } else {
          appStore.showMessage(response.data.message || '登录失败', 'error')
          return { success: false, message: response.data.message }
        }
        
      } catch (error) {
        console.error('登录失败:', error)
        const message = error.response?.data?.message || '登录失败，请检查网络连接'
        appStore.showMessage(message, 'error')
        return { success: false, message }
        
      } finally {
        this.isLoggingIn = false
      }
    },
    
    // 注册
    async register(userData) {
      const appStore = useAppStore()
      
      try {
        const response = await authApi.register(userData)
        
        if (response.data.success) {
          appStore.showMessage('注册成功，请登录', 'success')
          return { success: true }
        } else {
          appStore.showMessage(response.data.message || '注册失败', 'error')
          return { success: false, message: response.data.message }
        }
        
      } catch (error) {
        console.error('注册失败:', error)
        const message = error.response?.data?.message || '注册失败，请稍后重试'
        appStore.showMessage(message, 'error')
        return { success: false, message }
      }
    },
    
    // 登出
    async logout() {
      const appStore = useAppStore()
      
      try {
        // 调用登出API
        await authApi.logout()
      } catch (error) {
        console.error('登出API调用失败:', error)
      } finally {
        // 清除本地数据
        this.clearAuthData()
        appStore.showMessage('已退出登录', 'info')
      }
    },
    
    // 清除认证数据
    clearAuthData() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      this.isAuthenticated = false
      this.permissions = []
      
      // 清除本地存储
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    },
    
    // 刷新令牌
    async refreshAccessToken() {
      try {
        if (!this.refreshToken) {
          throw new Error('没有刷新令牌')
        }
        
        const response = await authApi.refresh()
        
        if (response.data.success) {
          this.accessToken = response.data.data.access_token
          localStorage.setItem('access_token', this.accessToken)
          return true
        } else {
          throw new Error(response.data.message)
        }
        
      } catch (error) {
        console.error('刷新令牌失败:', error)
        this.clearAuthData()
        return false
      }
    },
    
    // 获取当前用户信息
    async fetchUserInfo() {
      try {
        const response = await authApi.getCurrentUser()
        
        if (response.data.success) {
          this.user = response.data.data
          this.isAuthenticated = true
          return true
        } else {
          throw new Error(response.data.message)
        }
        
      } catch (error) {
        console.error('获取用户信息失败:', error)
        this.clearAuthData()
        return false
      }
    },
    
    // 修改密码
    async changePassword(passwordData) {
      const appStore = useAppStore()
      
      try {
        const response = await authApi.changePassword(passwordData)
        
        if (response.data.success) {
          appStore.showMessage('密码修改成功', 'success')
          return { success: true }
        } else {
          appStore.showMessage(response.data.message || '密码修改失败', 'error')
          return { success: false, message: response.data.message }
        }
        
      } catch (error) {
        console.error('修改密码失败:', error)
        const message = error.response?.data?.message || '修改密码失败'
        appStore.showMessage(message, 'error')
        return { success: false, message }
      }
    },
    
    // 初始化认证状态
    async initAuth() {
      // 如果有访问令牌，尝试获取用户信息
      if (this.accessToken) {
        const success = await this.fetchUserInfo()
        if (!success) {
          // 如果访问令牌无效，尝试刷新
          const refreshSuccess = await this.refreshAccessToken()
          if (refreshSuccess) {
            await this.fetchUserInfo()
          }
        }
      }
    },
    
    // 检查认证状态
    checkAuth() {
      return this.isAuthenticated && this.user && this.accessToken
    }
  }
})
