<template>
  <div class="layout-container">
    <!-- 顶部导航栏 -->
    <el-container class="layout-wrapper">
      <el-header class="layout-header">
        <div class="header-left">
          <el-button
            type="text"
            @click="toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon><Expand v-if="appStore.sidebarCollapsed" /><Fold v-else /></el-icon>
          </el-button>
          
          <h1 class="app-title">{{ appStore.appConfig.title }}</h1>
        </div>
        
        <div class="header-right">
          <!-- 上传进度 -->
          <div v-if="appStore.uploadProgress.show" class="upload-progress">
            <el-progress
              :percentage="appStore.uploadProgress.percentage"
              :status="appStore.uploadProgress.status"
              :stroke-width="4"
              class="progress-bar"
            />
            <span class="progress-text">上传中...</span>
          </div>
          
          <!-- 用户菜单 -->
          <el-dropdown @command="handleUserMenuCommand" placement="bottom-end">
            <div class="user-info">
              <el-avatar :size="32" :src="authStore.user?.avatar_url">
                {{ authStore.displayName?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ authStore.displayName }}</span>
              <el-icon><CaretBottom /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-container class="layout-body">
        <!-- 侧边栏 -->
        <el-aside 
          :width="appStore.sidebarCollapsed ? '64px' : '200px'"
          class="layout-sidebar"
        >
          <el-menu
            :default-active="activeMenu"
            :collapse="appStore.sidebarCollapsed"
            router
            class="sidebar-menu"
          >
            <template v-for="route in menuRoutes" :key="route.path">
              <!-- 有子菜单的项 -->
              <el-sub-menu
                v-if="route.children && route.children.length > 0 && !route.meta?.hidden"
                :index="route.path"
              >
                <template #title>
                  <el-icon v-if="route.meta?.icon">
                    <component :is="route.meta.icon" />
                  </el-icon>
                  <span>{{ route.meta?.title }}</span>
                </template>
                <el-menu-item
                  v-for="child in route.children"
                  :key="child.path"
                  :index="child.path"
                >
                  <el-icon v-if="child.meta?.icon">
                    <component :is="child.meta.icon" />
                  </el-icon>
                  <template #title>{{ child.meta?.title }}</template>
                </el-menu-item>
              </el-sub-menu>
              
              <!-- 没有子菜单的项 -->
              <el-menu-item
                v-else-if="!route.meta?.hidden"
                :index="route.path"
              >
                <el-icon v-if="route.meta?.icon">
                  <component :is="route.meta.icon" />
                </el-icon>
                <template #title>{{ route.meta?.title }}</template>
              </el-menu-item>
            </template>
          </el-menu>
        </el-aside>

        <!-- 主要内容区域 -->
        <el-main class="layout-main">
          <div class="main-content">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </div>
        </el-main>
      </el-container>
    </el-container>

    <!-- 全局加载遮罩 -->
    <el-backtop :right="40" :bottom="40" />
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAppStore } from '@/stores/app'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const appStore = useAppStore()
const router = useRouter()
const route = useRoute()

// 从路由配置中获取菜单
const menuRoutes = computed(() => {
  const mainRoute = router.options.routes.find(r => r.path === '/')
  if (!mainRoute || !mainRoute.children) return []
  
  return mainRoute.children.filter(route => {
    // 过滤掉没有标题的路由
    if (!route.meta?.title) return false
    
    // 过滤掉隐藏的路由
    if (route.meta?.hidden) return false
    
    // 过滤掉需要管理员权限但用户不是管理员的路由
    if (route.meta?.requiresAdmin && !authStore.isAdmin) return false
    
    // 对于有子菜单的路由，过滤子菜单
    if (route.children && route.children.length > 0) {
      route.children = route.children.filter(child => {
        if (!child.meta?.title) return false
        if (child.meta?.hidden) return false
        if (child.meta?.requiresAdmin && !authStore.isAdmin) return false
        return true
      })
    }
    
    return true
  }).map(route => {
    // 确保路径以 / 开头
    return {
      ...route,
      path: route.path.startsWith('/') ? route.path : `/${route.path}`,
      children: route.children?.map(child => ({
        ...child,
        path: child.path.startsWith('/') ? child.path : `/${child.path}`
      }))
    }
  })
})

// 当前激活的菜单项
const activeMenu = computed(() => {
  const path = route.path
  
  // 检查是否在子菜单中
  for (const menuRoute of menuRoutes.value) {
    if (menuRoute.children && menuRoute.children.length > 0) {
      for (const child of menuRoute.children) {
        if (path === child.path || path.startsWith(child.path + '/')) {
          return child.path
        }
      }
    }
  }
  
  return path
})

// 切换侧边栏
const toggleSidebar = () => {
  appStore.toggleSidebar()
  appStore.saveSettings()
}

// 处理用户菜单命令
const handleUserMenuCommand = (command) => {
  switch (command) {
    case 'profile':
      router.push('/profile')
      break
    case 'settings':
      // 打开设置对话框
      break
    case 'logout':
      handleLogout()
      break
  }
}

// 退出登录
const handleLogout = async () => {
  try {
    await authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}

// 初始化应用
onMounted(() => {
  appStore.initApp()
})
</script>

<style lang="scss" scoped>
.layout-container {
  height: 100vh;
  
  .layout-wrapper {
    height: 100%;
  }
}

.layout-header {
  background: $bg-color-white;
  border-bottom: 1px solid $border-color-lighter;
  padding: 0 $spacing-md;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
  
  .header-left {
    display: flex;
    align-items: center;
    
    .sidebar-toggle {
      margin-right: $spacing-md;
      font-size: 18px;
      
      .el-icon {
        font-size: 18px;
      }
    }
    
    .app-title {
      font-size: 20px;
      font-weight: 600;
      color: $text-color-primary;
      margin: 0;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    
    .upload-progress {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      
      .progress-bar {
        width: 120px;
      }
      
      .progress-text {
        font-size: 12px;
        color: $text-color-secondary;
      }
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      cursor: pointer;
      padding: $spacing-sm;
      border-radius: $border-radius-base;
      transition: $transition-base;
      
      &:hover {
        background-color: $bg-color-hover;
      }
      
      .username {
        font-size: 14px;
        color: $text-color-primary;
        
        @include respond-to(sm) {
          display: none;
        }
      }
    }
  }
}

.layout-body {
  height: calc(100vh - 60px);
}

.layout-sidebar {
  background: $bg-color-white;
  border-right: 1px solid $border-color-lighter;
  transition: width 0.3s ease;
  
  .sidebar-menu {
    border-right: none;
    height: 100%;
    
    .el-menu-item {
      &.is-active {
        background-color: rgba($color-primary, 0.1);
        color: $color-primary;
        
        .el-icon {
          color: $color-primary;
        }
      }
    }
  }
}

.layout-main {
  background: $bg-color-page;
  padding: 0;
  overflow-y: auto;
  
  .main-content {
    height: 100%;
    min-height: calc(100vh - 60px);
  }
}

// 响应式设计
@include respond-to(sm) {
  .layout-header {
    padding: 0 $spacing-sm;
    
    .header-left {
      .app-title {
        font-size: 16px;
      }
    }
  }
}

// 深色主题支持
[data-theme='dark'] {
  .layout-header,
  .layout-sidebar {
    background: #2d2d2d;
    border-color: #404040;
  }
  
  .layout-main {
    background: #1a1a1a;
  }
  
  .user-info {
    &:hover {
      background-color: rgba(255, 255, 255, 0.1);
    }
  }
}
</style>
