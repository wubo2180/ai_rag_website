<template>
  <div class="profile-container">
    <div class="page-header">
      <h1 class="page-title">个人中心</h1>
    </div>

    <div class="profile-content">
      <div class="profile-left">
        <el-card class="profile-card">
          <div class="profile-header">
            <el-avatar :size="80" :src="authStore.user?.avatar_url">
              {{ authStore.displayName?.charAt(0) }}
            </el-avatar>
            <div class="profile-info">
              <h3>{{ authStore.displayName }}</h3>
              <p>{{ authStore.user?.email }}</p>
              <el-tag :type="authStore.isAdmin ? 'danger' : 'primary'">
                {{ authStore.isAdmin ? '管理员' : '普通用户' }}
              </el-tag>
            </div>
          </div>
        </el-card>

        <el-card class="settings-card">
          <template #header>
            <h3>基本信息</h3>
          </template>
          
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            label-width="80px"
          >
            <el-form-item label="用户名">
              <el-input
                v-model="profileForm.username"
                disabled
              />
            </el-form-item>

            <el-form-item label="邮箱">
              <el-input v-model="profileForm.email" />
            </el-form-item>

            <el-form-item label="真实姓名">
              <el-input v-model="profileForm.real_name" />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="saving"
                @click="saveProfile"
              >
                保存修改
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </div>

      <div class="profile-right">
        <el-card class="password-card">
          <template #header>
            <h3>修改密码</h3>
          </template>
          
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="80px"
          >
            <el-form-item label="旧密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                show-password
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                show-password
              />
            </el-form-item>

            <el-form-item label="确认密码" prop="confirm_password">
              <el-input
                v-model="passwordForm.confirm_password"
                type="password"
                show-password
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="changingPassword"
                @click="changePassword"
              >
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>

        <el-card class="stats-card">
          <template #header>
            <h3>使用统计</h3>
          </template>
          
          <div class="stats-grid" v-loading="loadingStats">
            <div class="stat-item">
              <div class="stat-value">{{ userStats.uploadedFiles }}</div>
              <div class="stat-label">已上传</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.assignedFiles }}</div>
              <div class="stat-label">被分配</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.pendingRecognition }}</div>
              <div class="stat-label">待识别</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ userStats.pendingReview }}</div>
              <div class="stat-label">待核对</div>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { filesApi } from '@/api/files'
import { ElMessage } from 'element-plus'

const authStore = useAuthStore()

const saving = ref(false)
const changingPassword = ref(false)
const loadingStats = ref(false)

const profileForm = reactive({
  username: authStore.user?.username || '',
  email: authStore.user?.email || '',
  real_name: authStore.user?.real_name || ''
})

const passwordForm = reactive({
  old_password: '',
  new_password: '',
  confirm_password: ''
})

const userStats = reactive({
  uploadedFiles: 0,      // 用户已上传的文件数
  assignedFiles: 0,      // 被分配给用户的文件数
  pendingRecognition: 0, // 被分配的文件中待识别的数量
  pendingReview: 0       // 被分配的文件中待核对的数量
})

const profileFormRef = ref()
const passwordFormRef = ref()

const passwordRules = {
  old_password: [
    { required: true, message: '请输入旧密码', trigger: 'blur' }
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.new_password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 获取用户统计数据
const fetchUserStats = async () => {
  try {
    loadingStats.value = true
    
    // 1. 获取用户已上传的文件数（view_mode=my_files表示我上传的）
    const uploadedResponse = await filesApi.getFiles({ 
      view_mode: 'my_files',
      page: 1, 
      per_page: 1 
    })
    if (uploadedResponse.data.success) {
      userStats.uploadedFiles = uploadedResponse.data.data.total || 0
      console.log('📊 [已上传统计]', {
        已上传文件数: userStats.uploadedFiles
      })
    }
    
    // 2. 获取被分配给用户的文件数（view_mode=assigned表示分配给我的）
    const assignedResponse = await filesApi.getFiles({ 
      view_mode: 'assigned',
      page: 1, 
      per_page: 1 
    })
    if (assignedResponse.data.success) {
      userStats.assignedFiles = assignedResponse.data.data.total || 0
      console.log('📊 [被分配统计]', {
        被分配文件数: userStats.assignedFiles
      })
    }
    
    // 3. 获取被分配的文件中待识别的数量（status=pending）
    const pendingRecognitionResponse = await filesApi.getFiles({ 
      view_mode: 'assigned',
      status: 'pending',
      page: 1, 
      per_page: 1 
    })
    if (pendingRecognitionResponse.data.success) {
      userStats.pendingRecognition = pendingRecognitionResponse.data.data.total || 0
      console.log('📊 [待识别统计]', {
        待识别文件数: userStats.pendingRecognition
      })
    }
    
    // 4. 获取被分配的文件中待核对的数量
    // 待核对 = 已识别但未完成核对的文件
    // 条件1: 分配给该用户 (view_mode='assigned')
    // 条件2: 文件已经识别 (ocr_status='completed')
    // 条件3: 文件未人工核对 (review_status!='completed')
    // 方法：获取已识别的文件总数 - 已完成核对的文件数
    const recognizedResponse = await filesApi.getFiles({ 
      view_mode: 'assigned',
      status: 'completed',  // OCR已完成
      page: 1, 
      per_page: 1 
    })
    
    const completedReviewResponse = await filesApi.getFiles({ 
      view_mode: 'assigned',
      status: 'completed',  // OCR已完成
      review_status: 'completed',  // 且核对已完成
      page: 1, 
      per_page: 1 
    })
    
    if (recognizedResponse.data.success && completedReviewResponse.data.success) {
      const recognizedTotal = recognizedResponse.data.data.total || 0
      const completedTotal = completedReviewResponse.data.data.total || 0
      userStats.pendingReview = recognizedTotal - completedTotal
      
      console.log('📊 [待核对统计]', {
        已识别文件总数: recognizedTotal,
        已完成核对数: completedTotal,
        待核对数: userStats.pendingReview
      })
    }
    
  } catch (error) {
    console.error('获取用户统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  } finally {
    loadingStats.value = false
  }
}

const saveProfile = async () => {
  try {
    saving.value = true
    // 模拟保存
    await new Promise(resolve => setTimeout(resolve, 1000))
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

const changePassword = async () => {
  const form = passwordFormRef.value
  if (!form) return

  try {
    await form.validate()
    changingPassword.value = true

    const result = await authStore.changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password
    })

    if (result.success) {
      // 重置表单
      Object.keys(passwordForm).forEach(key => {
        passwordForm[key] = ''
      })
      form.resetFields()
    }

  } catch (error) {
    console.error('修改密码失败:', error)
  } finally {
    changingPassword.value = false
  }
}

// 页面加载时获取统计数据
onMounted(() => {
  fetchUserStats()
})
</script>

<style lang="scss" scoped>

.profile-container {
  padding: $spacing-lg;
  background: $bg-color-page;
  min-height: calc(100vh - 60px);
}

.page-header {
  margin-bottom: $spacing-lg;
  
  .page-title {
    font-size: 24px;
    font-weight: 600;
    color: $text-color-primary;
    margin: 0;
  }
}

.profile-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $spacing-lg;
  
  @include respond-to(md) {
    grid-template-columns: 1fr;
  }
}

.profile-card {
  margin-bottom: $spacing-lg;

  .profile-header {
    @include flex-center;
    flex-direction: column;
    text-align: center;
    
    .profile-info {
      margin-top: $spacing-md;
      
      h3 {
        font-size: 18px;
        margin: 0 0 $spacing-xs;
      }
      
      p {
        color: $text-color-secondary;
        margin: 0 0 $spacing-sm;
      }
    }
  }
}

.settings-card,
.password-card {
  margin-bottom: $spacing-lg;
}

.stats-card {
  .stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: $spacing-md;
    
    .stat-item {
      text-align: center;
      
      .stat-value {
        font-size: 24px;
        font-weight: 600;
        color: $color-primary;
      }
      
      .stat-label {
        font-size: 12px;
        color: $text-color-secondary;
        margin-top: 4px;
      }
    }
  }
}
</style>
