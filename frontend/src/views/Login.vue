<template>
  <div class="login2-container" :style="bgStyle">
    <div class="login2-card" :class="{ 'login-view-style': isLogin }">
      <div class="card-header">
        <h1 class="title">{{ isLogin ? '登录' : '注册' }}</h1>
        <img :src="brandImg" alt="IBOX Materix" class="brand-img" />
      </div>

      <form @submit.prevent="handleSubmit" class="login2-form">
        <template v-if="isLogin">
          <div class="form-group">
            <label class="label">账户</label>
            <input
              id="username"
              v-model="formData.username"
              type="text"
              placeholder="请输入邮箱/手机号"
              class="input"
              required
            />
          </div>

          <div class="form-group password-wrap">
            <label class="label">密码</label>
            <div class="input-with-action">
              <input
                id="password"
                v-model="formData.password"
                type="password"
                placeholder="请输入密码"
                class="input"
                required
              />
              <a href="#" class="forgot-link" @click.prevent="forgotPassword"
                >忘记密码？</a
              >
            </div>
          </div>
        </template>

        <template v-else>
          <div class="form-group">
            <label class="label">我的昵称</label>
            <input
              id="nickname"
              v-model="formData.nickname"
              type="text"
              placeholder="请输入昵称"
              class="input"
              @blur="markTouched('nickname')"
              @keyup.enter="markTouched('nickname')"
              required
            />
            <p v-if="showNicknameError" class="error-hint">
              {{ nicknameError }}
            </p>
          </div>

          <div class="form-group">
            <label class="label">账户</label>
            <input
              id="reg-username"
              v-model="formData.username"
              type="text"
              placeholder="请输入邮箱/手机号"
              class="input"
              required
            />
          </div>

          <div class="form-group">
            <label class="label">密码</label>
            <input
              id="reg-password"
              v-model="formData.password"
              type="password"
              placeholder="请输入密码"
              class="input"
              @blur="markTouched('password')"
              @keyup.enter="markTouched('password')"
              required
            />
            <p v-if="showPasswordError" class="error-hint">
              {{ passwordError }}
            </p>
          </div>

          <div class="form-group">
            <label class="label">确认密码</label>
            <input
              id="confirm-password"
              v-model="formData.confirmPassword"
              type="password"
              placeholder="再次输入密码"
              class="input"
              @blur="markTouched('confirmPassword')"
              @keyup.enter="markTouched('confirmPassword')"
              required
            />
            <p v-if="showConfirmPasswordError" class="error-hint">
              {{ confirmPasswordError }}
            </p>
          </div>

          <div class="form-group">
            <label class="label">验证码</label>
            <div class="input-with-action">
              <input
                id="verification-code"
                v-model="formData.verificationCode"
                type="text"
                placeholder="请输入验证码"
                class="input"
                required
              />
              <button
                class="code-btn"
                type="button"
                @click="getVerificationCode"
              >
                获取验证码
              </button>
            </div>
          </div>
        </template>

        <label class="terms">
          <input type="checkbox" v-model="formData.agreeTerms" />
          <span
            >我同意
            <a href="#" class="link" @click.prevent="showTerms"
              >《IBOX用户协议》</a
            >
            与
            <a href="#" class="link" @click.prevent="showPrivacy"
              >《隐私政策》</a
            >
          </span>
        </label>

        <button type="submit" class="submit-btn" :disabled="!canSubmit">
          {{ isLogin ? '登录' : '立即注册' }}
        </button>
      </form>

      <div class="divider" v-if="isLogin"></div>

      <div class="footer" :class="{ 'register-footer': !isLogin }">
        <template v-if="isLogin">
          <a href="#" class="link" @click.prevent="switchToRegister"
            >立即注册</a
          >
        </template>
        <template v-else>
          <span class="have-account">我已有账户，现在</span>
          <a href="#" class="link" @click.prevent="switchToLogin"
            >登录&gt;&gt;</a
          >
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted } from 'vue'
  import { useRouter, useRoute } from 'vue-router'
  import { useUserStore } from '@/stores/user'
  import { ElMessage } from 'element-plus'
  import loginBg from '@/assets/login/background.png'
  import brandImg from '@/assets/login/login@3X_19.png'

  const router = useRouter()
  const route = useRoute()
  const userStore = useUserStore()

  const isLogin = ref(true)
  const formData = reactive({
    username: '',
    password: '',
    confirmPassword: '',
    nickname: '',
    verificationCode: '',
    agreeTerms: false,
  })

  const bgStyle = computed(() => ({
    backgroundImage: `url(${loginBg})`,
  }))

  onMounted(() => {
    if (route.query.mode === 'register') {
      isLogin.value = false
    }
  })

  // 表单校验错误提示（注册）
  const nicknameError = computed(() => {
    const v = formData.nickname || ''
    if (!v.trim()) return '昵称不能为空'
    if (/\s/.test(v)) return '昵称禁止包含空格'
    const len = v.length
    if (len < 4 || len > 20) return '昵称长度需为 4–20 个字符'
    return ''
  })

  const passwordError = computed(() => {
    const v = formData.password || ''
    if (!v.trim()) return '密码不能为空'
    if (v.length < 8) return '密码至少 8 位'
    const hasNumber = /\d/.test(v)
    const hasLetter = /[A-Za-z]/.test(v)
    const hasSpecial = /[^A-Za-z0-9]/.test(v)
    if (!hasNumber || !hasLetter || !hasSpecial)
      return '密码必须包含数字、英文和特殊字符'
    return ''
  })

  const confirmPasswordError = computed(() => {
    const cp = formData.confirmPassword || ''
    if (!cp.trim()) return '请再次输入密码'
    if (formData.password !== cp) return '确认密码与密码不一致'
    return ''
  })

  // 仅在输入完成（失焦或按下 Enter）后显示错误提示
  const touched = reactive({
    nickname: false,
    password: false,
    confirmPassword: false,
  })
  const markTouched = (field) => {
    touched[field] = true
  }
  const showNicknameError = computed(
    () => touched.nickname && !!nicknameError.value,
  )
  const showPasswordError = computed(
    () => touched.password && !!passwordError.value,
  )
  const showConfirmPasswordError = computed(
    () => touched.confirmPassword && !!confirmPasswordError.value,
  )

  const canSubmit = computed(() => {
    if (isLogin.value) {
      return (
        !!formData.username.trim() &&
        !!formData.password.trim() &&
        formData.agreeTerms
      )
    }
    // 注册校验：用户名、密码、确认密码一致、验证码
    return (
      !!formData.username.trim() &&
      !nicknameError.value &&
      !passwordError.value &&
      !confirmPasswordError.value &&
      !!formData.verificationCode.trim() &&
      formData.agreeTerms
    )
  })

  const showTerms = () => {
    window.open(router.resolve({ name: 'Terms' }).href, '_blank')
  }
  const showPrivacy = () => {
    window.open(router.resolve({ name: 'Privacy' }).href, '_blank')
  }
  const forgotPassword = () => {
    alert('请联系管理员或使用重置流程（示例）')
  }

  const switchToRegister = () => {
    isLogin.value = false
    router.replace({ path: '/login', query: { mode: 'register' } })
  }

  const switchToLogin = () => {
    isLogin.value = true
    router.replace({ path: '/login', query: { mode: 'login' } })
  }

  const getVerificationCode = () => {
    alert('验证码已发送（示例）')
  }

  const handleSubmit = async () => {
    if (!canSubmit.value) return

    try {
      if (isLogin.value) {
        // 登录逻辑
        const result = await userStore.login({
          username: formData.username,
          password: formData.password,
        })

        if (result.success) {
          ElMessage.success('登录成功')
          // 同时保存到旧的 localStorage 以兼容 Chat.vue 的历史记录
          const userData = {
            username: userStore.user?.username || formData.username,
            profile: userStore.user?.profile,
            loginTime: new Date().toISOString(),
          }
          localStorage.setItem('ai-chat-user', JSON.stringify(userData))
          router.push('/chat')
        } else {
          ElMessage.error(result.error || '登录失败')
        }
      } else {
        // 注册逻辑
        const result = await userStore.register({
          username: formData.username,
          password: formData.password,
          nickname: formData.nickname,
          verification_code: formData.verificationCode,
        })

        if (result.success) {
          ElMessage.success('注册成功')
          // 同时保存到旧的 localStorage 以兼容 Chat.vue 的历史记录
          const userData = {
            username: userStore.user?.username || formData.nickname,
            profile: userStore.user?.profile,
            loginTime: new Date().toISOString(),
          }
          localStorage.setItem('ai-chat-user', JSON.stringify(userData))
          router.push('/chat')
        } else {
          ElMessage.error(result.error || '注册失败')
        }
      }
    } catch (error) {
      console.error('提交失败:', error)
      ElMessage.error('操作失败，请重试')
    }
  }
</script>

<style scoped>
  .login2-container {
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: top left;
    background-repeat: no-repeat;
    display: flex;
    flex-direction: column;
    position: relative;
    justify-content: flex-start; /* 从顶部开始排列 */
    overflow-y: auto;
  }

  .login2-card {
    width: 100%;
    max-width: 370px; /* 增加宽度 */
    background: rgba(255, 255, 255, 0.35); /* 进一步降低透明度 */
    border-radius: 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18);
    border: 1px solid rgba(255, 255, 255, 0.6);
    padding: 40px 35px 30px; /* 调整内边距 */
    position: absolute;
    left: 65%;
    top: 12%;
    top: clamp(20px, 12%, 120px); /* 注册卡片：最少距顶20px，最多120px */
    margin-bottom: 40px; /* 底部留白，防止滚动时贴边 */
  }

  .login-view-style {
    top: 250px; /* 登录组件位置 */
  }

  .card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 28px; /* 增加标题与表单的间距 */
  }
  .title {
    margin: 0;
    font-size: 32px; /* 增大字体 */
    font-weight: 800;
    color: #3b82f6;
  }
  .brand-img {
    height: 36px;
    width: auto;
  } /* 稍微增大品牌图片 */

  .login2-form {
    display: flex;
    flex-direction: column;
    gap: 24px;
  } /* 增加表单项间距 */
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .label {
    color: #374151;
    font-size: 16px;
  } /* 增大字体 */
  .input {
    width: 100%;
    box-sizing: border-box;
    padding: 14px 16px; /* 增大内边距 */
    font-size: 16px; /* 增大字体 */
    border-radius: 12px;
    border: 2px solid rgba(229, 231, 235, 0.7); /* 略微加粗边框 */
    outline: none;
    background: rgba(240, 244, 248, 0.3);
  }
  .password-wrap {
    position: relative;
  }
  .input-with-action {
    position: relative;
  }
  .input-with-action .input {
    padding-right: 110px;
  }
  .code-btn {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid #bfdbfe;
    background: #e0f2fe;
    color: #3b82f6;
    font-size: 12px;
    cursor: pointer;
  }
  .code-btn:hover {
    background: #bae6fd;
  }
  .have-account {
    color: #6b7280;
    margin-right: 6px;
  }
  .forgot-link {
    position: absolute;
    right: 16px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 14px;
    color: #60a5fa;
    text-decoration: none;
    white-space: nowrap;
  }
  .forgot-link:hover {
    text-decoration: underline;
  }
  .link {
    color: #3b82f6;
    text-decoration: none;
    font-weight: 600;
  }
  .link.minor {
    font-weight: 500;
    color: #60a5fa;
  }
  .link:hover {
    text-decoration: underline;
  }

  .terms {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #6b7280;
    font-size: 14px;
  } /* 增大字体 */
  .terms input {
    width: 18px;
    height: 18px;
  } /* 增大复选框 */

  .submit-btn {
    margin-top: 12px; /* 增加按钮与上方元素的间距 */
    padding: 16px 20px; /* 增大内边距 */
    font-size: 18px; /* 增大字体 */
    border-radius: 12px;
    border: 1px solid #bfdbfe; /* 边框更淡 */
    background: #93c5fd; /* 背景更淡 */
    color: #fff;
    cursor: pointer;
  }
  .submit-btn:disabled {
    background: #e5e7eb;
    border-color: #e5e7eb;
    color: #9ca3af;
    cursor: not-allowed;
  }
  .submit-btn:not(:disabled):hover {
    background: #60a5fa;
    border-color: #60a5fa;
  }

  .footer {
    text-align: center;
  }
  .register-footer {
    margin-top: 24px;
  }

  .divider {
    height: 1px;
    background-color: #e5e7eb; /* 浅灰色 */
    margin-top: 80px; /* 增加与登录按钮的间距 */
    margin-bottom: 16px; /* 减小与“立即注册”的间距 */
  }

  /* 输入校验错误提示：红色感叹号开头 */
  .error-hint {
    color: #ef4444; /* 红色 */
    font-size: 13px;
    line-height: 1.4;
    margin-top: -4px; /* 靠近输入框 */
    margin-bottom: -10px; /* 抵消与下方元素的间距 */
  }
  .error-hint::before {
    content: '!';
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    margin-right: 6px;
    border-radius: 50%;
    border: 1px solid #ef4444;
    color: #ef4444;
    font-size: 12px;
    font-weight: 700;
    line-height: 1;
  }
</style>
