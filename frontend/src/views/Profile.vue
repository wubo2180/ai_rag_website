<template>
  <div class="profile-container">
    <div class="profile-card">
      <div class="profile-header">
        <h2>个人资料</h2>
        <el-button @click="$router.go(-1)" icon="ArrowLeft">返回</el-button>
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
          <el-form-item label="当前密码" prop="currentPassword">
            <el-input 
              v-model="passwordForm.currentPassword" 
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
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import apiClient from '@/utils/api'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref()
const passwordFormRef = ref()
const loading = ref(false)
const passwordLoading = ref(false)

const userInfo = reactive({
  username: '',
  email: ''
})

const profile = reactive({
  nickname: '',
  bio: ''
})

const passwordForm = reactive({
  currentPassword: '',
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
  currentPassword: [
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
        profile.nickname = data.profile.nickname || ''
        profile.bio = data.profile.bio || ''
      }
    }
  } catch (error) {
    console.error('获取用户信息失败:', error)
    ElMessage.error('获取用户信息失败')
  }
}

// 更新资料
const updateProfile = async () => {
  if (!formRef.value) return
  
  try {
    await formRef.value.validate()
    loading.value = true
    
    const response = await apiClient.put('/auth/profile/', {
      nickname: profile.nickname,
      bio: profile.bio
    })
    
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
      current_password: passwordForm.currentPassword,
      new_password: passwordForm.newPassword
    })
    
    ElMessage.success('密码修改成功')
    
    // 清空表单
    passwordForm.currentPassword = ''
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

onMounted(() => {
  fetchUserInfo()
})
</script>

<style scoped>
.profile-container {
  display: flex;
  justify-content: center;
  padding: 20px;
  min-height: 100vh;
  background: #f5f5f5;
}

.profile-card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 600px;
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
</style>