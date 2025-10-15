<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1 class="login-title">iBox Materix</h1>
        <p class="login-subtitle">欢迎使用iBox Materix系统</p>
      </div>
      
      <div class="login-tabs">
        <button 
          :class="['tab-btn', { active: isLogin }]" 
          @click="switchToLogin"
        >
          登录
        </button>
        <button 
          :class="['tab-btn', { active: !isLogin }]" 
          @click="switchToRegister"
        >
          注册
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="login-form">
        <div class="form-group">
          <label for="username">用户名</label>
          <input
            id="username"
            v-model="formData.username"
            type="text"
            placeholder="请输入用户名"
            required
          />
        </div>

        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            required
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            v-model="formData.confirmPassword"
            type="password"
            placeholder="请再次输入密码"
            required
          />
        </div>

        <div v-if="!isLogin" class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="formData.email"
            type="email"
            placeholder="请输入邮箱地址"
            required
          />
        </div>

        <div class="terms-group">
          <label class="terms-checkbox">
            <input
              type="checkbox"
              v-model="formData.agreeTerms"
              required
            />
            <span class="checkmark"></span>
            <span class="terms-text">
              我已阅读并同意
              <a href="#" @click.prevent="showTerms" class="terms-link">《用户服务条款》</a>
              和
              <a href="#" @click.prevent="showPrivacy" class="terms-link">《隐私协议》</a>
            </span>
          </label>
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading || !formData.agreeTerms">
          <span v-if="isLoading" class="loading-spinner"></span>
          {{ isLoading ? '处理中...' : (isLogin ? '登录' : '注册') }}
        </button>
      </form>

      <div class="login-footer">
        <p class="demo-notice">
          🎯 这是一个演示版本，输入任意信息即可{{ isLogin ? '登录' : '注册' }}成功
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const isLogin = ref(true)
const isLoading = ref(false)

const formData = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  agreeTerms: false
})

const switchToLogin = () => {
  isLogin.value = true
  resetForm()
}

const switchToRegister = () => {
  isLogin.value = false
  resetForm()
}

const resetForm = () => {
  formData.username = ''
  formData.password = ''
  formData.confirmPassword = ''
  formData.email = ''
  formData.agreeTerms = false
}

const showTerms = () => {
  window.open(router.resolve({ name: 'Terms' }).href, '_blank')
}

const showPrivacy = () => {
  window.open(router.resolve({ name: 'Privacy' }).href, '_blank')
}

const handleSubmit = async () => {
  // 简单的表单验证
  if (!formData.username.trim() || !formData.password.trim()) {
    alert('请填写用户名和密码')
    return
  }

  if (!formData.agreeTerms) {
    alert('请先同意用户服务条款和隐私协议')
    return
  }

  if (!isLogin.value) {
    if (formData.password !== formData.confirmPassword) {
      alert('两次输入的密码不一致')
      return
    }
    if (!formData.email.trim()) {
      alert('请填写邮箱地址')
      return
    }
  }

  isLoading.value = true

  //发生请求到地址http://127.0.0.1:8000/accounts/login/
  const apiUrl = "http://127.0.0.1:8000/accounts/login/"
  const payload = {
    username: formData.username,
    password: formData.password
  }
  if (!isLogin.value) {
    payload.email = formData.email
  }
  try {
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    if (!response.ok) {
      throw new Error('网络响应失败')
    }
    const data = await response.json()
    if (data.error) {
      throw new Error(data.error)
    }
  } catch (error) {
    isLoading.value = false
    alert(`请求失败: ${error.message}`)
    return
  }
  // 模拟API请求延迟
  setTimeout(() => {
    // 保存用户登录状态到localStorage
    const userData = {
      username: formData.username,
      email: formData.email || '',
      loginTime: new Date().toISOString()
    }

    localStorage.setItem('ai-chat-user', JSON.stringify(userData))
    
    isLoading.value = false
    
    // 直接跳转到聊天界面
    router.push('/chat')
  }, 1000)
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  width: 100vw;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  padding: 12px;
  box-sizing: border-box;
  position: fixed;
  top: 0;
  left: 0;
  margin: 0;
  overflow-y: auto;
}

.login-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  padding: 28px 20px;
  width: 100%;
  max-width: 400px;
  animation: slideUp 0.6s ease-out;
  position: relative;
  margin: 12px auto;
  box-sizing: border-box;
  max-height: calc(100vh - 24px);
  overflow-y: auto;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-header {
  text-align: center;
  margin-bottom: 20px;
}

.login-title {
  font-size: 24px;
  font-weight: 700;
  color: #2d3748;
  margin: 0 0 8px 0;
}

.login-subtitle {
  color: #718096;
  margin: 0;
  font-size: 16px;
}

.login-tabs {
  display: flex;
  background: #f7fafc;
  border-radius: 12px;
  padding: 4px;
  margin-bottom: 20px;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  color: #718096;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn.active {
  background: white;
  color: #4f46e5;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 500;
  color: #2d3748;
  font-size: 14px;
}

.form-group input {
  padding: 12px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 16px;
  transition: all 0.3s ease;
  background: #f7fafc;
}

.form-group input:focus {
  outline: none;
  border-color: #4f46e5;
  background: white;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.submit-btn {
  padding: 16px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 10px;
}

.submit-btn:hover:not(:disabled) {
  background: #4338ca;
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(79, 70, 229, 0.3);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.login-footer {
  margin-top: 20px;
  text-align: center;
}

.demo-notice {
  background: #f0f9ff;
  color: #0369a1;
  padding: 12px 16px;
  border-radius: 8px;
  font-size: 14px;
  margin: 0;
  border-left: 4px solid #0ea5e9;
}

.terms-group {
  margin: 16px 0;
}

.terms-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1.5;
}

.terms-checkbox input[type="checkbox"] {
  display: none;
}

.checkmark {
  width: 18px;
  height: 18px;
  border: 2px solid #e2e8f0;
  border-radius: 4px;
  background: white;
  position: relative;
  flex-shrink: 0;
  margin-top: 2px;
  transition: all 0.3s ease;
}

.terms-checkbox input[type="checkbox"]:checked + .checkmark {
  background: #4f46e5;
  border-color: #4f46e5;
}

.terms-checkbox input[type="checkbox"]:checked + .checkmark::after {
  content: '';
  position: absolute;
  left: 5px;
  top: 2px;
  width: 4px;
  height: 8px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}

.terms-text {
  color: #4a5568;
  flex: 1;
}

.terms-link {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s ease;
}

.terms-link:hover {
  color: #4338ca;
  text-decoration: underline;
}

/* 响应式设计优化 */
@media (max-width: 480px) {
  .login-container {
    padding: 12px;
    align-items: flex-start;
    padding-top: 20px;
  }
  
  .login-card {
    padding: 24px 20px;
    margin: 8px auto;
    max-width: 100%;
  }
  
  .login-title {
    font-size: 22px;
  }
  
  .login-header {
    margin-bottom: 20px;
  }
  
  .login-tabs {
    margin-bottom: 20px;
  }
  
  .login-form {
    gap: 16px;
  }
  
  .form-group input {
    padding: 12px 14px;
    font-size: 16px;
  }
  
  .submit-btn {
    padding: 14px;
    font-size: 16px;
  }
}

@media (max-width: 360px) {
  .login-card {
    padding: 20px 16px;
  }
  
  .login-title {
    font-size: 20px;
  }
  
  .login-subtitle {
    font-size: 14px;
  }
}

/* 针对高度较小的屏幕优化 */
@media (max-height: 700px) {
  .login-container {
    align-items: flex-start;
    padding-top: 20px;
  }
  
  .login-card {
    margin: 10px auto;
  }
  
  .login-header {
    margin-bottom: 20px;
  }
  
  .login-tabs {
    margin-bottom: 20px;
  }
  
  .login-form {
    gap: 16px;
  }
  
  .login-footer {
    margin-top: 20px;
  }
}
</style>