<template>
  <div class="login-container">
    <div class="login-wrapper">
      <div class="login-header">
        <img src="/logo.svg" alt="Logo" class="logo" />
        <h1 class="title">OCR数据识别系统</h1>
        <p class="subtitle">基于AI的文档识别与数据提取平台</p>
      </div>

      <el-card class="login-card">
        <el-tabs v-model="activeTab" class="login-tabs">
          <!-- 登录表单 -->
          <el-tab-pane label="登录" name="login">
            <el-form
              ref="loginFormRef"
              :model="loginForm"
              :rules="loginRules"
              class="login-form"
              @submit.prevent="handleLogin"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="loginForm.username"
                  placeholder="请输入用户名或邮箱"
                  size="large"
                  prefix-icon="User"
                  :disabled="authStore.isLoggingIn"
                />
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="loginForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                  :disabled="authStore.isLoggingIn"
                  @keyup.enter="handleLogin"
                />
              </el-form-item>

              <el-form-item>
                <div class="form-options">
                  <el-checkbox v-model="loginForm.rememberMe">
                    记住我
                  </el-checkbox>
                  <el-link type="primary" :underline="false">
                    忘记密码？
                  </el-link>
                </div>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="login-btn"
                  :loading="authStore.isLoggingIn"
                  @click="handleLogin"
                >
                  {{ authStore.isLoggingIn ? '登录中...' : '登录' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>

          <!-- 注册表单 -->
          <el-tab-pane label="注册" name="register">
            <el-form
              ref="registerFormRef"
              :model="registerForm"
              :rules="registerRules"
              class="register-form"
            >
              <el-form-item prop="username">
                <el-input
                  v-model="registerForm.username"
                  placeholder="请输入用户名"
                  size="large"
                  prefix-icon="User"
                />
              </el-form-item>

              <el-form-item prop="email">
                <el-input
                  v-model="registerForm.email"
                  placeholder="请输入邮箱地址"
                  size="large"
                  prefix-icon="Message"
                />
              </el-form-item>

              <el-form-item prop="realName">
                <el-input
                  v-model="registerForm.realName"
                  placeholder="请输入真实姓名"
                  size="large"
                  prefix-icon="UserFilled"
                />
              </el-form-item>

              <el-form-item prop="password">
                <el-input
                  v-model="registerForm.password"
                  type="password"
                  placeholder="请输入密码"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item prop="confirmPassword">
                <el-input
                  v-model="registerForm.confirmPassword"
                  type="password"
                  placeholder="请确认密码"
                  size="large"
                  prefix-icon="Lock"
                  show-password
                />
              </el-form-item>

              <el-form-item>
                <el-checkbox v-model="registerForm.agreement">
                  我已阅读并同意
                  <el-link type="primary" :underline="false">用户协议</el-link>
                  和
                  <el-link type="primary" :underline="false">隐私政策</el-link>
                </el-checkbox>
              </el-form-item>

              <el-form-item>
                <el-button
                  type="primary"
                  size="large"
                  class="register-btn"
                  :loading="isRegistering"
                  @click="handleRegister"
                >
                  {{ isRegistering ? '注册中...' : '注册' }}
                </el-button>
              </el-form-item>
            </el-form>
          </el-tab-pane>
        </el-tabs>
      </el-card>

      <div class="login-footer">
        <p class="copyright">© 2024 IBoxTech. All rights reserved.</p>
        <div class="links">
          <el-link href="#" :underline="false">关于我们</el-link>
          <el-divider direction="vertical" />
          <el-link href="#" :underline="false">帮助中心</el-link>
          <el-divider direction="vertical" />
          <el-link href="#" :underline="false">联系我们</el-link>
        </div>
      </div>
    </div>

    <!-- 背景装饰 -->
    <div class="background-decoration">
      <div class="decoration-circle circle-1"></div>
      <div class="decoration-circle circle-2"></div>
      <div class="decoration-circle circle-3"></div>
    </div>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter, useRoute } from 'vue-router'

const authStore = useAuthStore()
const router = useRouter()
const route = useRoute()

// 响应式数据
const activeTab = ref('login')
const isRegistering = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  rememberMe: false
})

// 注册表单
const registerForm = reactive({
  username: '',
  email: '',
  realName: '',
  password: '',
  confirmPassword: '',
  agreement: false
})

// 表单验证规则
const loginRules = {
  username: [
    { required: true, message: '请输入用户名或邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const registerRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  realName: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' },
    { min: 2, max: 10, message: '姓名长度在2到10个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在6到20个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 表单引用
const loginFormRef = ref()
const registerFormRef = ref()

// 登录处理
const handleLogin = async () => {
  const form = unref(loginFormRef)
  if (!form) return
  
  try {
    await form.validate()
    
    const result = await authStore.login({
      username: loginForm.username,
      password: loginForm.password
    })
    
    if (result.success) {
      // 登录成功，跳转到目标页面
      const redirect = route.query.redirect || '/dashboard'
      router.push(redirect)
    }
  } catch (error) {
    console.error('登录失败:', error)
  }
}

// 注册处理
const handleRegister = async () => {
  const form = unref(registerFormRef)
  if (!form) return
  
  try {
    await form.validate()
    
    if (!registerForm.agreement) {
      ElMessage.warning('请先同意用户协议和隐私政策')
      return
    }
    
    isRegistering.value = true
    
    const result = await authStore.register({
      username: registerForm.username,
      email: registerForm.email,
      real_name: registerForm.realName,
      password: registerForm.password
    })
    
    if (result.success) {
      // 注册成功，切换到登录标签
      activeTab.value = 'login'
      
      // 清空注册表单
      Object.keys(registerForm).forEach(key => {
        registerForm[key] = key === 'agreement' ? false : ''
      })
      
      form.clearValidate()
    }
    
  } catch (error) {
    console.error('注册失败:', error)
  } finally {
    isRegistering.value = false
  }
}

// 如果用户已登录，直接跳转
onMounted(() => {
  if (authStore.checkAuth()) {
    const redirect = route.query.redirect || '/dashboard'
    router.replace(redirect)
  }
})
</script>

<style lang="scss" scoped>

.login-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.login-wrapper {
  width: 100%;
  max-width: 400px;
  padding: $spacing-md;
  position: relative;
  z-index: 2;
}

.login-header {
  text-align: center;
  margin-bottom: $spacing-xl;
  
  .logo {
    width: 64px;
    height: 64px;
    margin-bottom: $spacing-md;
  }
  
  .title {
    font-size: 28px;
    font-weight: 600;
    color: white;
    margin-bottom: $spacing-sm;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }
  
  .subtitle {
    font-size: 14px;
    color: rgba(255, 255, 255, 0.8);
    margin: 0;
  }
}

.login-card {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  border: none;
  border-radius: 16px;
  
  :deep(.el-card__body) {
    padding: $spacing-xl;
  }
}

.login-tabs {
  :deep(.el-tabs__nav-wrap::after) {
    display: none;
  }
  
  :deep(.el-tabs__nav) {
    width: 100%;
    display: flex;
  }
  
  :deep(.el-tabs__item) {
    flex: 1;
    text-align: center;
    font-size: 16px;
    font-weight: 500;
  }
}

.login-form,
.register-form {
  margin-top: $spacing-lg;
  
  .el-form-item {
    margin-bottom: $spacing-lg;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .form-options {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
  }
  
  .login-btn,
  .register-btn {
    width: 100%;
    height: 44px;
    font-size: 16px;
    font-weight: 500;
    border-radius: 8px;
  }
}

.login-footer {
  text-align: center;
  margin-top: $spacing-xl;
  
  .copyright {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.6);
    margin-bottom: $spacing-sm;
  }
  
  .links {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
    
    .el-link {
      font-size: 12px;
      color: rgba(255, 255, 255, 0.8);
      
      &:hover {
        color: white;
      }
    }
    
    .el-divider {
      margin: 0;
      border-color: rgba(255, 255, 255, 0.3);
    }
  }
}

// 背景装饰
.background-decoration {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  
  .decoration-circle {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.1);
    
    &.circle-1 {
      width: 200px;
      height: 200px;
      top: -100px;
      right: -100px;
      animation: float 6s ease-in-out infinite;
    }
    
    &.circle-2 {
      width: 150px;
      height: 150px;
      bottom: -75px;
      left: -75px;
      animation: float 8s ease-in-out infinite reverse;
    }
    
    &.circle-3 {
      width: 100px;
      height: 100px;
      top: 20%;
      left: 10%;
      animation: float 10s ease-in-out infinite;
    }
  }
}

// 响应式设计
@include respond-to(sm) {
  .login-wrapper {
    padding: $spacing-sm;
  }
  
  .login-header {
    .title {
      font-size: 24px;
    }
  }
  
  .login-card {
    :deep(.el-card__body) {
      padding: $spacing-lg;
    }
  }
}

// 动画
@keyframes float {
  0%, 100% {
    transform: translateY(0px);
  }
  50% {
    transform: translateY(-20px);
  }
}

// 表单验证样式
:deep(.el-form-item.is-error) {
  .el-input__inner {
    border-color: $color-danger;
  }
}

:deep(.el-form-item__error) {
  position: absolute;
  top: 100%;
  left: 0;
  font-size: 12px;
  color: $color-danger;
  line-height: 1;
  padding-top: 4px;
}
</style>
