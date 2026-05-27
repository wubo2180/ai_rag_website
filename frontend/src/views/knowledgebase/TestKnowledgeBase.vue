<template>
  <div class="test-knowledge-base">
    <h1>🧠 知识库测试页面</h1>
    <p>这是一个简化的知识库页面，用于测试路由是否正常工作。</p>
    <div class="test-content">
      <h2>测试信息</h2>
      <p>当前时间: {{ currentTime }}</p>
      <p>路由路径: {{ $route.path }}</p>
      <p>页面标题: {{ $route.meta.title }}</p>
      
      <div class="navigation-test">
        <h3>导航测试</h3>
        <button @click="goToChat" class="test-btn">返回聊天页面</button>
        <button @click="testConsole" class="test-btn">控制台测试</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'TestKnowledgeBase',
  data() {
    return {
      currentTime: new Date().toLocaleString()
    }
  },
  mounted() {
    console.log('🧠 知识库测试页面已加载')
    console.log('当前路由:', this.$route)
  },
  methods: {
    goToChat() {
      this.$router.push('/chat')
    },
    testConsole() {
      console.log('🔍 知识库页面控制台测试')
      alert('知识库页面JavaScript运行正常!')
    }
  }
}
</script>

<style scoped>
.test-knowledge-base {
  padding: 40px;
  max-width: 800px;
  margin: 0 auto;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: white;
}

.test-content {
  background: rgba(255, 255, 255, 0.1);
  padding: 30px;
  border-radius: 15px;
  margin-top: 30px;
}

.navigation-test {
  margin-top: 30px;
}

.test-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  cursor: pointer;
  margin-right: 10px;
  margin-bottom: 10px;
  transition: all 0.3s;
}

.test-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}
</style>