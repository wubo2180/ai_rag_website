import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例 - 增加超时时间以支持复杂AI模型
const apiClient = axios.create({
  baseURL: '/api', // Vite代理会将/api转发到Django后端
  timeout: 180000, // 增加到3分钟，支持deepseek深度思考等慢速模型
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
        const response = await axios.create({ baseURL: '/api' }).post('/auth/token/refresh/', {
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

// AI_UI_928_2 集成 - 增强版API方法
export const enhancedAPI = {
  // 流式聊天API - 修复：添加超时和AbortController支持
  async streamChat(data, onMessage, onThinking, onError) {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => {
      controller.abort()
    }, 300000) // 5分钟超时，支持deepseek深度思考等复杂模型

    try {
      const response = await fetch('/api/chat/api/stream/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        body: JSON.stringify(data),
        signal: controller.signal  // 添加取消信号
      })
      
      clearTimeout(timeoutId) // 清除超时计时器

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.slice(6).trim()
            if (dataStr === '[DONE]') {
              return
            }

            try {
              const data = JSON.parse(dataStr)
              if (data.content) {
                onMessage(data.content)
              }
              if (data.thinking && onThinking) {
                onThinking(data.thinking)
              }
            } catch (e) {
              console.error('解析流数据失败:', e)
            }
          }
        }
      }
    } catch (error) {
      clearTimeout(timeoutId) // 确保清除超时计时器
      console.error('流式请求失败:', error)
      
      if (error.name === 'AbortError') {
        console.error('请求被取消或超时')
        if (onError) {
          onError(new Error('请求超时，请稍后重试'))
        }
      } else if (onError) {
        onError(error)
      }
    }
  },

  // 获取相关问题推荐
  async getRelatedQuestions(query) {
    try {
      const response = await apiClient.post('/chat/api/suggestions/', { query })
      return response.data
    } catch (error) {
      console.error('获取相关问题失败:', error)
      return { success: false, suggestions: [] }
    }
  },

  // 获取增强版可用模型
  async getEnhancedModels() {
    try {
      const response = await apiClient.get('/chat/api/enhanced-models/')
      return response.data
    } catch (error) {
      console.error('获取AI模型列表失败:', error)
      return { success: false, models: [] }
    }
  },

  // 切换用户偏好模型
  async switchModel(model, deep_thinking = false) {
    try {
      const response = await apiClient.post('/chat/api/model-switch/', {
        model,
        deep_thinking
      })
      return response.data
    } catch (error) {
      console.error('切换模型失败:', error)
      return { success: false }
    }
  },

  // 获取用户模型偏好
  async getUserModelPreferences() {
    try {
      const response = await apiClient.get('/chat/api/model-switch/')
      return response.data
    } catch (error) {
      console.error('获取用户偏好失败:', error)
      return { success: false, model: 'deepseek', deep_thinking: true }
    }
  }
}

export default apiClient