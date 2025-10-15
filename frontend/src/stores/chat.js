import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/utils/api'

export const useChatStore = defineStore('chat', () => {
  // 状态
  const sessions = ref([])
  const currentSession = ref(null)
  const messages = ref([])
  const isLoading = ref(false)
  const availableModels = ref([])
  const selectedModel = ref('')

  // 计算属性
  const hasMessages = computed(() => messages.value.length > 0)
  const sessionCount = computed(() => sessions.value.length)

  // 获取聊天会话列表
  async function fetchSessions() {
    try {
      const response = await apiClient.get('/chat/sessions/')
      sessions.value = response.data.results || response.data
      return { success: true, data: response.data }
    } catch (error) {
      console.error('获取会话列表失败:', error)
      return { success: false, error: '获取会话列表失败' }
    }
  }

  // 创建新会话
  async function createSession(title = '') {
    try {
      const response = await apiClient.post('/chat/sessions/', { title })
      const newSession = response.data
      sessions.value.unshift(newSession)
      return { success: true, data: newSession }
    } catch (error) {
      console.error('创建会话失败:', error)
      return { success: false, error: '创建会话失败' }
    }
  }

  // 获取会话历史
  async function fetchSessionHistory(sessionId) {
    try {
      const response = await apiClient.get(`/chat/sessions/${sessionId}/history/`)
      messages.value = response.data.messages || []
      currentSession.value = {
        id: response.data.id,
        title: response.data.title,
        created_at: response.data.created_at,
        updated_at: response.data.updated_at
      }
      return { success: true, data: response.data }
    } catch (error) {
      console.error('获取会话历史失败:', error)
      return { success: false, error: '获取会话历史失败' }
    }
  }

  // 发送消息
  async function sendMessage(message, sessionId = null, model = null) {
    isLoading.value = true
    
    try {
      const response = await apiClient.post('/chat/chat/', {
        message,
        session_id: sessionId,
        model: model || selectedModel.value
      })

      if (response.data.success) {
        // 添加用户消息和AI回复到消息列表
        if (response.data.user_message) {
          messages.value.push(response.data.user_message)
        }
        if (response.data.ai_message) {
          messages.value.push(response.data.ai_message)
        }

        // 更新当前会话ID
        if (response.data.session_id && !currentSession.value) {
          currentSession.value = { id: response.data.session_id }
        }

        return { 
          success: true, 
          data: response.data,
          sessionId: response.data.session_id
        }
      } else {
        return { 
          success: false, 
          error: response.data.error || '发送消息失败' 
        }
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      return { 
        success: false, 
        error: error.response?.data?.error || '发送消息失败' 
      }
    } finally {
      isLoading.value = false
    }
  }

  // 获取可用模型
  async function fetchAvailableModels() {
    try {
      const response = await apiClient.get('/chat/models/')
      availableModels.value = response.data.models || []
      selectedModel.value = response.data.default_model || ''
      return { success: true, data: response.data }
    } catch (error) {
      console.error('获取可用模型失败:', error)
      return { success: false, error: '获取可用模型失败' }
    }
  }

  // 重命名会话
  async function renameSession(sessionId, newTitle) {
    try {
      const response = await apiClient.post(`/chat/sessions/${sessionId}/rename/`, {
        title: newTitle
      })
      
      // 更新本地会话列表
      const sessionIndex = sessions.value.findIndex(s => s.id === sessionId)
      if (sessionIndex !== -1) {
        sessions.value[sessionIndex].title = newTitle
      }
      
      // 更新当前会话标题
      if (currentSession.value && currentSession.value.id === sessionId) {
        currentSession.value.title = newTitle
      }

      return { success: true, data: response.data }
    } catch (error) {
      console.error('重命名会话失败:', error)
      return { success: false, error: '重命名会话失败' }
    }
  }

  // 删除会话
  async function deleteSession(sessionId) {
    try {
      await apiClient.delete(`/chat/sessions/${sessionId}/`)
      
      // 从本地列表中移除
      sessions.value = sessions.value.filter(s => s.id !== sessionId)
      
      // 如果删除的是当前会话，清空当前会话和消息
      if (currentSession.value && currentSession.value.id === sessionId) {
        currentSession.value = null
        messages.value = []
      }

      return { success: true }
    } catch (error) {
      console.error('删除会话失败:', error)
      return { success: false, error: '删除会话失败' }
    }
  }

  // 清空当前会话
  function clearCurrentSession() {
    currentSession.value = null
    messages.value = []
  }

  // 设置当前会话
  function setCurrentSession(session) {
    currentSession.value = session
    messages.value = []
  }

  return {
    // 状态
    sessions,
    currentSession,
    messages,
    isLoading,
    availableModels,
    selectedModel,

    // 计算属性
    hasMessages,
    sessionCount,

    // 方法
    fetchSessions,
    createSession,
    fetchSessionHistory,
    sendMessage,
    fetchAvailableModels,
    renameSession,
    deleteSession,
    clearCurrentSession,
    setCurrentSession
  }
})