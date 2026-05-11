import { defineStore } from 'pinia'

export const useAppStore = defineStore('app', {
  state: () => ({
    // 全局加载状态
    globalLoading: false,
    
    // 全局消息提示
    globalMessage: {
      show: false,
      text: '',
      type: 'info', // success, warning, error, info
      duration: 3000
    },
    
    // 应用配置
    appConfig: {
      title: 'OCR数据识别系统',
      version: '1.0.0',
      apiBaseUrl: import.meta.env.VITE_API_BASE_URL || '/api'
    },
    
    // 侧边栏状态
    sidebarCollapsed: false,
    
    // 主题设置
    theme: {
      mode: 'light', // light, dark
      primaryColor: '#409eff'
    },
    
    // 上传进度
    uploadProgress: {
      show: false,
      percentage: 0,
      status: '' // '', 'success', 'exception', 'warning' (Element Plus ElProgress 支持的值)
    }
  }),

  getters: {
    // 是否为移动端
    isMobile() {
      return window.innerWidth < 768
    },
    
    // 获取API基础URL
    apiUrl() {
      return this.appConfig.apiBaseUrl
    }
  },

  actions: {
    // 显示全局加载
    showLoading() {
      this.globalLoading = true
    },
    
    // 隐藏全局加载
    hideLoading() {
      this.globalLoading = false
    },
    
    // 显示消息提示
    showMessage(text, type = 'info', duration = 3000) {
      this.globalMessage = {
        show: true,
        text,
        type,
        duration
      }
      
      // 自动隐藏消息
      setTimeout(() => {
        this.hideMessage()
      }, duration)
    },
    
    // 隐藏消息提示
    hideMessage() {
      this.globalMessage.show = false
    },
    
    // 切换侧边栏
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    
    // 设置侧边栏状态
    setSidebarCollapsed(collapsed) {
      this.sidebarCollapsed = collapsed
    },
    
    // 切换主题
    toggleTheme() {
      this.theme.mode = this.theme.mode === 'light' ? 'dark' : 'light'
      this.applyTheme()
    },
    
    // 应用主题
    applyTheme() {
      document.documentElement.setAttribute('data-theme', this.theme.mode)
    },
    
    // 显示上传进度
    showUploadProgress() {
      this.uploadProgress.show = true
      this.uploadProgress.percentage = 0
      this.uploadProgress.status = '' // 上传中使用空字符串（默认蓝色）
    },
    
    // 更新上传进度
    updateUploadProgress(percentage, status = '') {
      this.uploadProgress.percentage = percentage
      this.uploadProgress.status = status
      // status 可选值: '' (默认蓝色), 'success' (绿色), 'exception' (红色), 'warning' (黄色)
    },
    
    // 隐藏上传进度
    hideUploadProgress() {
      this.uploadProgress.show = false
    },
    
    // 初始化应用
    async initApp() {
      try {
        // 恢复主题设置
        const savedTheme = localStorage.getItem('app-theme')
        if (savedTheme) {
          this.theme = JSON.parse(savedTheme)
          this.applyTheme()
        }
        
        // 恢复侧边栏状态
        const savedSidebar = localStorage.getItem('sidebar-collapsed')
        if (savedSidebar !== null) {
          this.sidebarCollapsed = JSON.parse(savedSidebar)
        }
        
      } catch (error) {
        console.error('初始化应用失败:', error)
      }
    },
    
    // 保存设置到本地存储
    saveSettings() {
      localStorage.setItem('app-theme', JSON.stringify(this.theme))
      localStorage.setItem('sidebar-collapsed', JSON.stringify(this.sidebarCollapsed))
    }
  }
})
