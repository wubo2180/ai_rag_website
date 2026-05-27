<template>
  <div class="profile-page-wrapper">
    <NavigationSidebar />
    <div class="profile-container">
      <div class="profile-card">
        <div class="profile-header">
          <h2>个人资料中心</h2>
          <el-button @click="$router.go(-1)" icon="ArrowLeft">返回</el-button>
        </div>

        <div class="avatar-section">
          <div class="avatar-preview" :style="avatarStyle"></div>
          <div class="avatar-actions">
            <input ref="avatarInputRef" type="file" accept="image/*" style="display: none" @change="handleAvatarSelected" />
            <el-button @click="triggerAvatarUpload">上传头像</el-button>
            <p class="avatar-tip">支持 JPG/PNG，大小不超过2MB</p>
          </div>
        </div>

        <div class="stats-grid">
          <div class="stat-card"><span class="label">历史对话</span><span class="value">{{ dashboard.summary.total_sessions }}</span></div>
          <div class="stat-card"><span class="label">消息总数</span><span class="value">{{ dashboard.summary.total_messages }}</span></div>
          <div class="stat-card"><span class="label">智能体任务</span><span class="value">{{ dashboard.summary.total_tasks }}</span></div>
          <div class="stat-card"><span class="label">任务成功率</span><span class="value">{{ dashboard.summary.success_rate }}%</span></div>
        </div>

        <div class="recent-section">
          <h3>最近对话</h3>
          <ul>
            <li v-for="item in dashboard.recent_sessions" :key="item.id">
              <span>{{ item.title }}</span>
              <small>{{ formatDate(item.updated_at) }}</small>
            </li>
            <li v-if="dashboard.recent_sessions.length === 0" class="empty">暂无历史对话</li>
          </ul>
        </div>

        <div class="recent-section">
          <h3>最近智能体任务</h3>
          <ul>
            <li v-for="item in dashboard.recent_tasks" :key="item.id">
              <span>{{ item.title }}（{{ item.agent_name || '未知智能体' }}）</span>
              <small>{{ item.status }}</small>
            </li>
            <li v-if="dashboard.recent_tasks.length === 0" class="empty">暂无智能体任务</li>
          </ul>
        </div>

        <el-form :model="userInfo" :rules="rules" ref="formRef" label-width="100px">
          <el-form-item label="用户名" prop="username">
            <el-input v-model="userInfo.username" disabled />
          </el-form-item>

          <el-form-item label="邮箱" prop="email">
            <el-input v-model="userInfo.email" disabled />
          </el-form-item>

          <el-form-item label="昵称" prop="nickname">
            <el-input v-model="profile.nickname" placeholder="请输入昵称" />
          </el-form-item>

          <el-form-item label="个人简介" prop="bio">
            <el-input
              v-model="profile.bio"
              type="textarea"
              :rows="4"
              placeholder="请输入个人简介"
            />
          </el-form-item>

          <el-form-item>
            <el-button type="primary" @click="updateProfile" :loading="loading">
              保存资料
            </el-button>
          </el-form-item>
        </el-form>

        <el-divider />

        <div class="password-section">
          <h3>修改密码</h3>
          <el-form :model="passwordForm" :rules="passwordRules" ref="passwordFormRef" label-width="100px">
            <el-form-item label="当前密码" prop="oldPassword">
              <el-input
                v-model="passwordForm.oldPassword"
                type="password"
                show-password
                placeholder="请输入当前密码"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="newPassword">
              <el-input
                v-model="passwordForm.newPassword"
                type="password"
                show-password
                placeholder="请输入新密码"
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirmPassword">
              <el-input
                v-model="passwordForm.confirmPassword"
                type="password"
                show-password
                placeholder="请再次输入新密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button type="primary" @click="changePassword" :loading="passwordLoading">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import apiClient from '@/utils/api'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const passwordFormRef = ref()
const avatarInputRef = ref()
const loading = ref(false)
const passwordLoading = ref(false)

const dashboard = reactive({
  summary: {
    total_sessions: 0,
    total_messages: 0,
    total_tasks: 0,
    success_rate: 0,
  },
  recent_sessions: [],
  recent_tasks: [],
})

const avatarStyle = computed(() => {
  const avatarUrl = profile.avatar_url
  return avatarUrl
    ? { backgroundImage: `url(${avatarUrl})` }
    : {}
})

const userInfo = reactive({
  username: '',
  email: ''
})

const profile = reactive({
  avatar_url: '',
  nickname: '',
  bio: ''
})

const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入新密码'))
  } else if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  nickname: [
    { max: 50, message: '昵称长度不能超过50个字符', trigger: 'blur' }
  ],
  bio: [
    { max: 200, message: '个人简介不能超过200个字符', trigger: 'blur' }
  ]
}

const passwordRules = {
  oldPassword: [
    { required: true, message: '请输入当前密码', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 获取用户信息
const fetchUserInfo = async () => {
  try {
    const result = await userStore.fetchUserInfo()
    if (result.success) {
      const data = result.data
      userInfo.username = data.user.username
      userInfo.email = data.user.email
      
      if (data.profile) {
        profile.avatar_url = data.profile.avatar_url || ''
        profile.nickname = data.profile.nickname || ''
        profile.bio = data.profile.bio || ''
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

const fetchDashboardStats = async () => {
  try {
    const response = await apiClient.get('/auth/dashboard-stats/')
    const data = response.data || {}
    dashboard.summary = {
      ...dashboard.summary,
      ...(data.summary || {}),
    }
    dashboard.recent_sessions = data.recent_sessions || []
    dashboard.recent_tasks = data.recent_tasks || []
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const triggerAvatarUpload = () => {
  avatarInputRef.value?.click()
}

const handleAvatarSelected = async (e) => {
  const file = e.target.files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('avatar', file)

  try {
    const response = await apiClient.post('/auth/avatar-upload/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    profile.avatar_url = response.data.avatar_url || ''
    await userStore.fetchUserInfo()
    ElMessage.success('头像更新成功')
  } catch (error) {
    const errorMsg = error.response?.data?.error || '头像上传失败'
    ElMessage.error(errorMsg)
  } finally {
    if (avatarInputRef.value) {
      avatarInputRef.value.value = ''
    }
  }
}

// 更新资料
const updateProfile = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const response = await apiClient.put('/auth/profile/', {
      avatar_url: profile.avatar_url,
      nickname: profile.nickname,
      bio: profile.bio
    })
    
    await userStore.fetchUserInfo()
    ElMessage.success('资料更新成功')
  } catch (error) {
    console.error('更新资料失败:', error)
    ElMessage.error('更新资料失败')
  } finally {
    loading.value = false
  }
}

// 修改密码
const changePassword = async () => {
  if (!passwordFormRef.value) return
  
  try {
    await passwordFormRef.value.validate()
    passwordLoading.value = true
    
    const response = await apiClient.post('/auth/change-password/', {
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword,
      confirm_password: passwordForm.confirmPassword,
    })
    
    ElMessage.success('密码修改成功')
    
    // 清空表单
  passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
    
  } catch (error) {
    console.error('修改密码失败:', error)
    const errorMsg = error.response?.data?.error || '修改密码失败'
    ElMessage.error(errorMsg)
  } finally {
    passwordLoading.value = false
  }
}

const formatDate = (value) => {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN')
}

onMounted(() => {
  fetchUserInfo()
  fetchDashboardStats()
})
</script>

<style scoped>
.profile-page-wrapper {
  display: flex;
  height: 100vh;
}

.profile-container {
  flex: 1;
  overflow-y: auto;
  display: block;
  width: 100%;
  padding: 20px 24px;
  min-height: 100vh;
  background: #f5f5f5;
  box-sizing: border-box;
}

.profile-card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: none;
  min-height: calc(100vh - 40px);
  box-sizing: border-box;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #f0f2f5;
  border-radius: 8px;
}

.avatar-preview {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background-color: #e5e7eb;
  background-image: url('@/assets/talk page/talk@3x_08.png');
  background-size: cover;
  background-position: center;
}

.avatar-tip {
  font-size: 12px;
  color: #888;
  margin: 8px 0 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: #f8fafc;
  border: 1px solid #eef2f7;
  border-radius: 8px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stat-card .label {
  font-size: 12px;
  color: #666;
}

.stat-card .value {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
}

.recent-section {
  margin-bottom: 18px;
}

.recent-section h3 {
  margin: 0 0 10px;
  color: #333;
}

.recent-section ul {
  list-style: none;
  margin: 0;
  padding: 0;
  border: 1px solid #eef2f7;
  border-radius: 8px;
}

.recent-section li {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 12px;
  border-bottom: 1px solid #f3f4f6;
}

.recent-section li:last-child {
  border-bottom: none;
}

.recent-section li.empty {
  color: #999;
}

.recent-section small {
  color: #888;
  white-space: nowrap;
}

.profile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.profile-header h2 {
  margin: 0;
  color: #333;
}

.password-section {
  margin-top: 20px;
}

.password-section h3 {
  margin-bottom: 20px;
  color: #333;
}

@media (max-width: 900px) {
  .profile-container {
    padding: 16px;
  }

  .profile-card {
    padding: 20px;
    min-height: auto;
  }

  .stats-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .avatar-section {
    flex-direction: column;
    align-items: flex-start;
  }
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>