<template>
  <div id="app" class="app-container">
    <router-view />
    
    <!-- 全局加载动画 -->
    <el-loading 
      v-if="appStore.globalLoading"
      :lock="true"
      text="加载中..."
      background="rgba(0, 0, 0, 0.7)"
    />
    
    <!-- 全局提示消息 -->
    <Teleport to="body">
      <Transition name="message" appear>
        <div 
          v-if="appStore.globalMessage.show"
          :class="['global-message', `global-message--${appStore.globalMessage.type}`]"
        >
          <el-icon class="global-message__icon">
            <SuccessFilled v-if="appStore.globalMessage.type === 'success'" />
            <WarningFilled v-else-if="appStore.globalMessage.type === 'warning'" />
            <CircleCloseFilled v-else-if="appStore.globalMessage.type === 'error'" />
            <InfoFilled v-else />
          </el-icon>
          <span class="global-message__text">{{ appStore.globalMessage.text }}</span>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { useAppStore } from '@/stores/app'

const appStore = useAppStore()

// 全局错误处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
  appStore.showMessage('系统发生错误，请稍后重试', 'error')
})

window.addEventListener('error', (event) => {
  console.error('Global error:', event.error)
  appStore.showMessage('系统发生错误，请稍后重试', 'error')
})
</script>

<style lang="scss">
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
  font-family: 'Helvetica Neue', Helvetica, 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', '微软雅黑', Arial, sans-serif;
}

#app {
  height: 100%;
}

.app-container {
  height: 100%;
  background-color: #f5f7fa;
}

// 全局提示消息样式
.global-message {
  position: fixed;
  top: 50px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  padding: 12px 20px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  color: white;
  font-size: 14px;
  
  &--success {
    background-color: #67c23a;
  }
  
  &--warning {
    background-color: #e6a23c;
  }
  
  &--error {
    background-color: #f56c6c;
  }
  
  &--info {
    background-color: #409eff;
  }
  
  &__icon {
    margin-right: 8px;
    font-size: 16px;
  }
  
  &__text {
    flex: 1;
  }
}

// 消息动画
.message-enter-active,
.message-leave-active {
  transition: all 0.3s ease;
}

.message-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.message-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

// 工具类
.text-center {
  text-align: center;
}

.text-left {
  text-align: left;
}

.text-right {
  text-align: right;
}

.flex {
  display: flex;
}

.flex-center {
  display: flex;
  align-items: center;
  justify-content: center;
}

.flex-between {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.full-height {
  height: 100%;
}

.full-width {
  width: 100%;
}

// 响应式
@media (max-width: 768px) {
  .global-message {
    left: 10px;
    right: 10px;
    transform: none;
  }
}
</style>
