<template>
  <div class="user-management-page-wrapper">
    <NavigationSidebar />
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
          <div class="table-container">
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
        </div>

        <!-- 部门维护 -->
        <div class="card dept-card">
          <h3>部门列表</h3>
          <div class="dept-content">
            <div v-if="loading.departments" class="loading">
              部门数据加载中...
            </div>
            <ul v-else class="dept-list">
              <li v-for="dept in departments" :key="dept.id" class="list-item">
                <strong>{{ dept.name }}</strong>
                <span>序号：#{{ dept.id }}</span>
                <small>权限：{{ dept.description || '暂无描述' }}</small>
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
                  placeholder="必填项，例如：研发部"
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
      </div>
    </section>
  </div>
</template>

<script setup>
  import NavigationSidebar from '@/components/NavigationSidebar.vue'
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
  .user-management-page-wrapper {
    display: flex;
    height: 100vh;
  }

  .role-dept-manager {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 2rem;
    padding: 2rem;
    height: 100%;
    background: linear-gradient(135deg, #f5f7fa 0%, #f0f2f5 100%);
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1.5rem;
    padding: 1.5rem 2rem;
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    flex-shrink: 0;
  }

  .header h2 {
    margin: 0;
    font-size: 1.75rem;
    font-weight: 700;
    color: #1e293b;
    background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .header p {
    margin: 0.5rem 0 0 0;
    color: #64748b;
    font-size: 0.95rem;
  }

  .header-actions button {
    border: 2px solid #e2e8f0;
    background: #fff;
    padding: 0.65rem 1.5rem;
    border-radius: 10px;
    font-weight: 600;
    color: #475569;
    transition: all 0.3s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.04);
  }

  .header-actions button:hover:not(:disabled) {
    background: #f8fafc;
    border-color: #2563eb;
    color: #2563eb;
    box-shadow: 0 4px 8px rgba(37, 99, 235, 0.2);
  }

  .header-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .content-grid {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
    flex: 1;
    overflow: hidden;
    min-height: 0;
  }

  .card {
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 0;
    background: #fff;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0;
    padding: 2rem 2rem 1rem 2rem;
    border-bottom: 2px solid #f1f5f9;
    flex-shrink: 0;
  }

  .card-header h3 {
    margin: 0;
    font-size: 1.4rem;
    font-weight: 700;
    color: #1e293b;
  }

  .badge {
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
    color: #fff;
    font-size: 0.85rem;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
  }

  .loading {
    padding: 2rem;
    color: #64748b;
    text-align: center;
    font-size: 1rem;
  }

  .empty {
    padding: 2rem;
    color: #94a3b8;
    text-align: center;
    font-size: 1rem;
  }

  .table-container {
    overflow-y: auto;
    flex: 1;
    padding: 0 2rem 2rem 2rem;
  }

  .user-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin-top: 0;
    overflow: visible;
    border-radius: 0;
  }

  .user-table thead {
    background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  }

  .user-table th {
    padding: 1rem 0.75rem;
    text-align: left;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    font-size: 0.8rem;
    letter-spacing: 0.05em;
    border-bottom: 2px solid #e2e8f0;
  }

  .user-table td {
    padding: 1rem 0.75rem;
    border-bottom: 1px solid #f1f5f9;
    text-align: left;
    color: #334155;
    font-size: 0.95rem;
  }

  .user-table tbody tr {
    transition: background 0.2s ease;
  }

  .user-table tbody tr:hover {
    background: #fafbfc;
  }

  .user-table td strong {
    color: #1e293b;
    font-weight: 600;
    margin-right: 0.5rem;
  }

  .user-table td small {
    color: #94a3b8;
    font-size: 0.85rem;
    margin-left: 0.25rem;
  }

  .user-table select {
    width: 100%;
    padding: 0.55rem 0.75rem;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    background: #fff;
    color: #334155;
    font-size: 0.9rem;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .user-table select:hover:not(:disabled) {
    border-color: #cbd5e1;
  }

  .user-table select:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .user-table button.primary {
    padding: 0.5rem 1.2rem;
    font-size: 0.9rem;
    font-weight: 600;
  }

  button.primary {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: #fff;
    border: none;
    border-radius: 10px;
    padding: 0.65rem 1.5rem;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  }

  button.primary:hover:not(:disabled) {
    box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4);
  }

  button.primary:active:not(:disabled) {
    transform: translateY(0);
  }

  button.primary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  button.ghost {
    cursor: pointer;
  }

  .dept-card h3 {
    margin: 0;
    padding: 2rem 2rem 1rem 2rem;
    font-size: 1.4rem;
    font-weight: 700;
    color: #1e293b;
    border-bottom: 2px solid #f1f5f9;
    flex-shrink: 0;
  }

  .dept-card .dept-content {
    overflow-y: auto;
    flex: 1;
    padding: 1.5rem 2rem;
  }

  .dept-card h4 {
    margin: 1.5rem 0 1rem 0;
    font-size: 1.1rem;
    font-weight: 700;
    color: #475569;
  }

  .dept-card .dept-list {
    list-style: none;
    margin: 0 0 1.5rem 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .dept-card li {
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.4rem;
    background: linear-gradient(135deg, #fafbfc 0%, #f8fafc 100%);
    transition: all 0.3s ease;
  }

  .dept-card li:hover {
    border-color: #cbd5e1;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }

  .dept-card li strong {
    color: #1e293b;
    font-size: 1.05rem;
    font-weight: 700;
  }

  .dept-card li span {
    color: #94a3b8;
    font-size: 0.85rem;
  }

  .dept-card li small {
    color: #94a3b8;
    font-size: 0.9rem;
    margin-top: 0.15rem;
  }

  .divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
    margin: 2rem 0;
  }

  .dept-form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .dept-form label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-weight: 600;
    color: #475569;
    font-size: 0.95rem;
  }

  .dept-form input,
  .dept-form select,
  .dept-form textarea {
    width: 100%;
    border: 2px solid #e2e8f0;
    border-radius: 10px;
    padding: 0.7rem 0.9rem;
    font-size: 0.95rem;
    color: #334155;
    transition: all 0.2s ease;
    background: #fff;
  }

  .dept-form input:focus,
  .dept-form select:focus,
  .dept-form textarea:focus {
    outline: none;
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }

  .dept-form textarea {
    resize: vertical;
    min-height: 80px;
    font-family: inherit;
  }

  .toast {
    position: fixed;
    top: 2rem;
    right: 2rem;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    font-size: 0.95rem;
    font-weight: 600;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    max-width: 400px;
  }

  .toast-success {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: #fff;
  }

  .toast-error {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: #fff;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: all 0.3s ease;
  }

  .fade-enter-from {
    opacity: 0;
    transform: translateY(-20px);
  }

  .fade-leave-to {
    opacity: 0;
    transform: translateY(20px);
  }

  @media (max-width: 960px) {
    .role-dept-manager {
      padding: 1rem;
    }

    .content-grid {
      grid-template-columns: 1fr;
    }

    .header {
      padding: 1rem 1.5rem;
    }

    .header h2 {
      font-size: 1.5rem;
    }

    .card {
      padding: 1.5rem;
    }

    .toast {
      right: 1rem;
      left: 1rem;
      max-width: none;
    }
  }
</style>
