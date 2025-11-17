<template>
  <section class="role-dept-manager">
    <header class="header">
      <div>
        <h2>用户角色与部门管理</h2>
        <p>仅管理员可见：批量查看 & 分配角色/部门</p>
      </div>
      <div class="header-actions">
        <button class="ghost" :disabled="isAnyLoading" @click="refreshAll">
          刷新数据
        </button>
      </div>
    </header>

    <!-- 全局提示 -->
    <transition name="fade">
      <div
        v-if="toast.message"
        class="toast"
        :class="toast.type === 'success' ? 'toast-success' : 'toast-error'"
      >
        {{ toast.message }}
      </div>
    </transition>

    <div class="content-grid">
      <!-- 用户列表 -->
      <div class="card users-card">
        <div class="card-header">
          <h3>用户列表</h3>
          <span class="badge">{{ users.length }} 人</span>
        </div>
        <div v-if="loading.users" class="loading">用户数据加载中...</div>
        <div v-else-if="!users.length" class="empty">暂无用户数据</div>
        <table v-else class="user-table">
          <thead>
            <tr>
              <th>用户名</th>
              <th>邮箱</th>
              <th>当前角色</th>
              <th>所属部门</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>
                <strong>{{ user.username }}</strong>
                <small>#{{ user.id }}</small>
              </td>
              <td>{{ user.email || '—' }}</td>
              <td>
                <select
                  v-model="formState[user.id].role"
                  :disabled="loading.savingId === user.id"
                >
                  <option
                    v-for="role in roleOptions"
                    :key="role.value"
                    :value="role.value"
                  >
                    {{ role.label }}
                  </option>
                </select>
              </td>
              <td>
                <select
                  v-model="formState[user.id].department_id"
                  :disabled="loading.savingId === user.id"
                >
                  <option :value="null">未分配</option>
                  <option
                    v-for="dept in departments"
                    :key="dept.id"
                    :value="dept.id"
                  >
                    {{ dept.name }}
                  </option>
                </select>
              </td>
              <td>
                <button
                  class="primary"
                  :disabled="loading.savingId === user.id"
                  @click="assignRole(user.id)"
                >
                  {{ loading.savingId === user.id ? '保存中…' : '保存' }}
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 部门维护 -->
      <div class="card dept-card">
        <h3>部门列表</h3>
        <div v-if="loading.departments" class="loading">部门数据加载中...</div>
        <ul v-else class="dept-list">
          <li v-for="dept in departments" :key="dept.id">
            <strong>{{ dept.name }}</strong>
            <span>#{{ dept.id }}</span>
            <small>{{ dept.description || '暂无描述' }}</small>
            <small v-if="dept.parent"
              >上级：{{ resolveParentName(dept.parent) }}</small
            >
          </li>
        </ul>

        <div class="divider"></div>

        <h4>新建部门</h4>
        <form class="dept-form" @submit.prevent="createDepartment">
          <label>
            名称
            <input
              v-model="newDept.name"
              type="text"
              placeholder="例如：研发部"
              required
            />
          </label>
          <label>
            描述
            <textarea
              v-model="newDept.description"
              rows="2"
              placeholder="职责说明，可选"
            ></textarea>
          </label>
          <label>
            上级部门（可选）
            <select v-model="newDept.parent">
              <option :value="null">无</option>
              <option
                v-for="dept in departments"
                :key="`parent-${dept.id}`"
                :value="dept.id"
              >
                {{ dept.name }}
              </option>
            </select>
          </label>
          <button class="primary" :disabled="loading.creatingDept">
            {{ loading.creatingDept ? '创建中…' : '创建部门' }}
          </button>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
  import { ref, reactive, onMounted, computed } from 'vue'
  import apiClient from '@/utils/api'

  const users = ref([])
  const departments = ref([])
  const formState = reactive({})
  const toast = reactive({ type: '', message: '' })

  const loading = reactive({
    users: false,
    departments: false,
    savingId: null,
    creatingDept: false,
  })

  const isAnyLoading = computed(
    () => loading.users || loading.departments || loading.creatingDept
  )

  const roleOptions = [
    { value: 'ADMIN', label: '管理员' },
    { value: 'SUPERVISOR', label: '部门主管' },
    { value: 'EMPLOYEE', label: '普通员工' },
  ]

  const setToast = (type, message) => {
    toast.type = type
    toast.message = message
    setTimeout(() => {
      toast.message = ''
    }, 3500)
  }

  const hydrateFormState = () => {
    users.value.forEach((user) => {
      formState[user.id] = {
        role: user.profile?.role ?? 'EMPLOYEE',
        department_id: user.profile?.department?.id ?? null,
      }
    })
  }

  const fetchUsers = async () => {
    loading.users = true
    try {
      const { data } = await apiClient.get('/auth/users/')
      // 若后端开启分页，这里兼容 data.results
      users.value = Array.isArray(data) ? data : data.results ?? []
      hydrateFormState()
    } catch (error) {
      setToast('error', error.response?.data?.detail || '获取用户列表失败')
    } finally {
      loading.users = false
    }
  }

  const fetchDepartments = async () => {
    loading.departments = true
    try {
      const { data } = await apiClient.get('/auth/departments/')
      departments.value = data.results ?? data // 同样兼容分页/非分页
    } catch (error) {
      setToast('error', error.response?.data?.detail || '获取部门列表失败')
    } finally {
      loading.departments = false
    }
  }

  const assignRole = async (userId) => {
    const payload = {
      user_id: userId,
      role: formState[userId].role,
      department_id: formState[userId].department_id,
    }

    loading.savingId = userId
    try {
      await apiClient.post('/auth/users/assign-role/', payload)
      setToast('success', `用户 #${userId} 更新成功`)
      await fetchUsers() // 确保界面反映后端最新数据
    } catch (error) {
      const err =
        error.response?.data?.role ||
        error.response?.data?.department_id ||
        error.response?.data?.detail ||
        '更新失败'
      setToast('error', Array.isArray(err) ? err.join('; ') : err)
    } finally {
      loading.savingId = null
    }
  }

  const createDepartment = async () => {
    if (!newDept.name.trim()) return
    loading.creatingDept = true
    try {
      await apiClient.post('/auth/departments/', newDept)
      setToast('success', `部门「${newDept.name}」已创建`)
      newDept.name = ''
      newDept.description = ''
      newDept.parent = null
      await fetchDepartments()
    } catch (error) {
      const err =
        error.response?.data?.name ||
        error.response?.data?.detail ||
        '创建部门失败'
      setToast('error', Array.isArray(err) ? err.join('; ') : err)
    } finally {
      loading.creatingDept = false
    }
  }

  const newDept = reactive({
    name: '',
    description: '',
    parent: null,
  })

  const resolveParentName = (parentId) =>
    departments.value.find((d) => d.id === parentId)?.name || `#${parentId}`

  const refreshAll = () => {
    fetchUsers()
    fetchDepartments()
  }

  onMounted(() => {
    refreshAll()
  })
</script>

<style scoped>
  .role-dept-manager {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .header h2 {
    margin: 0;
  }

  .header-actions button {
    border: 1px solid #d0d5dd;
    background: transparent;
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
  }

  .content-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 1.5rem;
  }

  .card {
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 1.5rem;
    background: #fff;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.08);
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .badge {
    padding: 0.1rem 0.6rem;
    border-radius: 999px;
    background: #f4f4f5;
    font-size: 0.85rem;
  }

  .loading {
    padding: 1rem;
    color: #475467;
  }

  .empty {
    padding: 1rem;
    color: #a0aec0;
    text-align: center;
  }

  .user-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
  }

  .user-table th,
  .user-table td {
    padding: 0.65rem;
    border-bottom: 1px solid #f1f5f9;
    text-align: left;
  }

  .user-table select {
    width: 100%;
    padding: 0.4rem;
  }

  .user-table button.primary {
    padding: 0.35rem 0.9rem;
  }

  button.primary {
    background: #2563eb;
    color: #fff;
    border: none;
    border-radius: 0.5rem;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }

  button.primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  button.ghost {
    cursor: pointer;
  }

  .dept-card .dept-list {
    list-style: none;
    margin: 1rem 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .dept-card li {
    border: 1px dashed #e2e8f0;
    border-radius: 0.75rem;
    padding: 0.75rem;
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .divider {
    height: 1px;
    background: #e5e7eb;
    margin: 1rem 0;
  }

  .dept-form {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .dept-form input,
  .dept-form select,
  .dept-form textarea {
    width: 100%;
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 0.5rem;
  }

  .toast {
    padding: 0.8rem 1rem;
    border-radius: 0.6rem;
    font-size: 0.95rem;
  }

  .toast-success {
    background: #ecfdf3;
    color: #027a48;
  }

  .toast-error {
    background: #fef3f2;
    color: #b42318;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.2s;
  }

  .fade-enter-from,
  .fade-leave-to {
    opacity: 0;
  }

  @media (max-width: 960px) {
    .content-grid {
      grid-template-columns: 1fr;
    }
  }
</style>
