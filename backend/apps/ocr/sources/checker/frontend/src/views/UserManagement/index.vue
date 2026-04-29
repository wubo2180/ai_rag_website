<template>
  <div class="user-management-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">用户管理</h1>
        <p class="page-subtitle">管理系统用户和权限分配</p>
      </div>
      <div class="header-actions">
        <el-button @click="refreshUsers">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
        <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
          新增用户
        </el-button>
      </div>
    </div>

    <el-card class="user-table-card">
      <el-table :data="userList" v-loading="loading">
        <el-table-column label="用户信息" min-width="200">
          <template #default="{ row }">
            <div class="user-info">
              <el-avatar :size="40" :src="row.avatar_url">
                {{ row.real_name?.charAt(0) || row.username?.charAt(0) }}
              </el-avatar>
              <div class="user-details">
                <div class="username">{{ row.username }}</div>
                <div class="real-name">{{ row.real_name }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="邮箱" prop="email" width="200" />
        
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.role === 'admin' ? 'danger' : 'primary'">
              {{ row.role === 'admin' ? '管理员' : '普通用户' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login_at ? formatTime(row.last_login_at) : '从未登录' }}
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button
              size="small"
              type="danger"
              @click="deleteUser(row)"
              :disabled="row.id === authStore.user?.id"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑用户对话框 -->
    <el-dialog
      v-model="userDialog.visible"
      :title="userDialog.isEdit ? '编辑用户' : '新增用户'"
      width="500px"
    >
      <el-form
        ref="userFormRef"
        :model="userDialog.form"
        :rules="userFormRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="userDialog.form.username"
            :disabled="userDialog.isEdit"
          />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="userDialog.form.email" />
        </el-form-item>

        <el-form-item label="真实姓名" prop="real_name">
          <el-input v-model="userDialog.form.real_name" />
        </el-form-item>

        <el-form-item v-if="!userDialog.isEdit" label="密码" prop="password">
          <el-input
            v-model="userDialog.form.password"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="userDialog.form.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-switch
            v-model="userDialog.form.is_active"
            active-text="启用"
            inactive-text="禁用"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="userDialog.visible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="userDialog.saving"
          @click="saveUser"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import { usersApi } from '@/api/users'
import dayjs from 'dayjs'

const authStore = useAuthStore()

const loading = ref(false)
const userList = ref([])

const userDialog = reactive({
  visible: false,
  isEdit: false,
  saving: false,
  currentUser: null,
  form: {
    username: '',
    email: '',
    real_name: '',
    password: '',
    role: 'user',
    is_active: true
  }
})

const userFormRef = ref()

const userFormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在3到20个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  real_name: [
    { required: true, message: '请输入真实姓名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ]
}

const refreshUsers = async () => {
  try {
    loading.value = true
    const response = await usersApi.getUsers({
      page: 1,
      per_page: 100
    })
    
    if (response.data.success) {
      userList.value = response.data.data.users
    }
  } catch (error) {
    console.error('获取用户列表失败:', error)
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  userDialog.isEdit = false
  userDialog.form = {
    username: '',
    email: '',
    real_name: '',
    password: '',
    role: 'user',
    is_active: true
  }
  userDialog.visible = true
}

const editUser = (user) => {
  userDialog.isEdit = true
  userDialog.currentUser = user
  userDialog.form = {
    username: user.username,
    email: user.email,
    real_name: user.real_name,
    password: '',
    role: user.role,
    is_active: user.is_active
  }
  userDialog.visible = true
}

const saveUser = async () => {
  const form = userFormRef.value
  if (!form) return

  try {
    await form.validate()
    userDialog.saving = true

    if (userDialog.isEdit) {
      // 更新用户
      const response = await usersApi.updateUser(
        userDialog.currentUser.id,
        {
          email: userDialog.form.email,
          real_name: userDialog.form.real_name,
          role: userDialog.form.role,
          is_active: userDialog.form.is_active
        }
      )
      
      if (response.data.success) {
        ElMessage.success('用户更新成功')
        userDialog.visible = false
        refreshUsers()
      } else {
        ElMessage.error(response.data.message || '更新失败')
      }
    } else {
      // 创建新用户
      const response = await usersApi.createUser({
        username: userDialog.form.username,
        email: userDialog.form.email,
        real_name: userDialog.form.real_name,
        password: userDialog.form.password,
        role: userDialog.form.role,
        is_active: userDialog.form.is_active
      })
      
      if (response.data.success) {
        ElMessage.success('用户创建成功')
        userDialog.visible = false
        refreshUsers()
      } else {
        ElMessage.error(response.data.message || '创建失败')
      }
    }

  } catch (error) {
    console.error('保存用户失败:', error)
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    userDialog.saving = false
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确认删除用户 "${user.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确认删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await usersApi.deleteUser(user.id)
    
    if (response.data.success) {
      ElMessage.success('删除成功')
      refreshUsers()
    } else {
      ElMessage.error(response.data.message || '删除失败')
    }

  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除用户失败:', error)
      if (error.response?.data?.message) {
        ElMessage.error(error.response.data.message)
      } else {
        ElMessage.error('删除失败')
      }
    }
  }
}

const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm')
}

onMounted(() => {
  refreshUsers()
})
</script>

<style lang="scss" scoped>
.user-management-container {
  padding: $spacing-lg;
  background: $bg-color-page;
  min-height: calc(100vh - 60px);
}

.page-header {
  @include flex-between;
  margin-bottom: $spacing-lg;
  
  .header-content {
    .page-title {
      font-size: 24px;
      font-weight: 600;
      color: $text-color-primary;
      margin: 0 0 $spacing-xs;
    }
    
    .page-subtitle {
      font-size: 14px;
      color: $text-color-secondary;
      margin: 0;
    }
  }
  
  .header-actions {
    display: flex;
    gap: $spacing-sm;
  }
}

.user-info {
  display: flex;
  align-items: center;
  gap: $spacing-md;
  
  .user-details {
    .username {
      font-size: 14px;
      font-weight: 500;
      color: $text-color-primary;
    }
    
    .real-name {
      font-size: 12px;
      color: $text-color-secondary;
      margin-top: 2px;
    }
  }
}
</style>
