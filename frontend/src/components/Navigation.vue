<template>
  <nav class="navigation">
    <div class="nav-brand">
      <h1>AI RAG 智能对话</h1>
    </div>
    <div class="nav-links">
      <router-link to="/chat" class="nav-link">
        <i class="icon">💬</i>
        基础聊天
      </router-link>
      <router-link to="/enhanced-chat" class="nav-link featured">
        <i class="icon">🧠</i>
        智能对话
        <span class="badge">增强版</span>
      </router-link>
      <router-link to="/sessions" class="nav-link" v-if="isAuthenticated">
        <i class="icon">📝</i>
        历史记录
      </router-link>
      <router-link to="/documents" class="nav-link" v-if="isAuthenticated">
        <i class="icon">📁</i>
        文档管理
      </router-link>
    </div>
    <div class="nav-user">
      <template v-if="isAuthenticated">
        <router-link to="/profile" class="nav-link">
          <i class="icon">👤</i>
          个人资料
        </router-link>
        <button @click="handleLogout" class="nav-link logout-btn">
          <i class="icon">🚪</i>
          退出登录
        </button>
      </template>
      <template v-else>
        <router-link to="/login" class="nav-link">
          <i class="icon">🔑</i>
          登录
        </router-link>
        <router-link to="/register" class="nav-link">
          <i class="icon">✨</i>
          注册
        </router-link>
      </template>
    </div>
  </nav>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

export default {
  name: 'Navigation',
  setup() {
    const router = useRouter()
    const userStore = useUserStore()

    const isAuthenticated = computed(() => userStore.isAuthenticated)

    const handleLogout = async () => {
      try {
        await userStore.logout()
        ElMessage.success('退出登录成功')
        router.push('/login')
      } catch (error) {
        console.error('退出登录失败:', error)
        ElMessage.error('退出登录失败')
      }
    }

    return {
      isAuthenticated,
      handleLogout
    }
  }
}
</script>

<style scoped>
.navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.nav-brand h1 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.nav-links, .nav-user {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  color: white;
  text-decoration: none;
  transition: all 0.3s ease;
  position: relative;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 0.9rem;
}

.nav-link:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.nav-link.router-link-active {
  background: rgba(255, 255, 255, 0.3);
}

.nav-link.featured {
  background: linear-gradient(135deg, #ff6b6b, #ff8e8e);
  font-weight: 600;
}

.nav-link.featured:hover {
  background: linear-gradient(135deg, #ff5252, #ff7979);
}

.badge {
  background: rgba(255, 255, 255, 0.9);
  color: #ff6b6b;
  font-size: 0.7rem;
  padding: 0.2rem 0.4rem;
  border-radius: 12px;
  font-weight: bold;
}

.icon {
  font-size: 1.2rem;
}

.logout-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.logout-btn:hover {
  background: rgba(255, 107, 107, 0.8);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .navigation {
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }

  .nav-links, .nav-user {
    flex-wrap: wrap;
    justify-content: center;
  }

  .nav-brand h1 {
    font-size: 1.2rem;
  }

  .nav-link {
    font-size: 0.8rem;
    padding: 0.4rem 0.8rem;
  }
}
</style>