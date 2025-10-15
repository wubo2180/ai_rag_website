<template>
  <div class="documents-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>
          <el-icon><Document /></el-icon>
          文献资料管理
        </h1>
        <p>管理您的文献资料，支持多种文件格式的上传和分类整理</p>
      </div>
      
      <div class="header-actions">
        <el-button type="primary" @click="showUploadDialog" icon="Plus">
          上传文档
        </el-button>
        <el-button @click="showCategoryDialog" icon="FolderAdd">
          新建分类
        </el-button>
      </div>
    </div>

    <!-- 统计信息卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon documents">📚</div>
            <div class="stat-content">
              <div class="stat-number">{{ stats.total_documents }}</div>
              <div class="stat-label">文档总数</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon categories">🗂️</div>
            <div class="stat-content">
              <div class="stat-number">{{ stats.total_categories }}</div>
              <div class="stat-label">分类数量</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon size">💾</div>
            <div class="stat-content">
              <div class="stat-number">{{ stats.total_size_human }}</div>
              <div class="stat-label">总存储</div>
            </div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-icon types">🎯</div>
            <div class="stat-content">
              <div class="stat-number">{{ Object.keys(stats.file_type_stats || {}).length }}</div>
              <div class="stat-label">文件类型</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-filter-section">
      <div class="search-bar">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索文档标题、描述或标签..."
          @input="handleSearch"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
      
      <div class="filter-controls">
        <el-select
          v-model="selectedCategory"
          placeholder="选择分类"
          @change="handleFilter"
          clearable
        >
          <el-option
            v-for="category in categories"
            :key="category.id"
            :label="category.name"
            :value="category.id"
          />
        </el-select>
        
        <el-select
          v-model="selectedFileType"
          placeholder="文件类型"
          @change="handleFilter"
          clearable
        >
          <el-option
            v-for="type in fileTypes"
            :key="type.value"
            :label="type.label"
            :value="type.value"
          />
        </el-select>
        
        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          @change="handleFilter"
        >
          <el-option label="最新上传" value="-created_at" />
          <el-option label="最早上传" value="created_at" />
          <el-option label="标题 A-Z" value="title" />
          <el-option label="标题 Z-A" value="-title" />
          <el-option label="文件大小" value="file_size" />
        </el-select>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="documents-content">
      <el-card class="documents-list-card">
        <template #header>
          <div class="card-header">
            <span>文档列表 ({{ documents.length }})</span>
            <div class="view-controls">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="card">卡片</el-radio-button>
                <el-radio-button label="list">列表</el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>

        <!-- 卡片视图 -->
        <div v-if="viewMode === 'card'" class="card-view">
          <el-row :gutter="20">
            <el-col :span="6" v-for="document in documents" :key="document.id">
              <div class="document-card">
                <div class="document-icon">
                  <span class="file-type-icon">{{ document.file_type_icon }}</span>
                  <span class="file-type">{{ document.file_type.toUpperCase() }}</span>
                </div>
                
                <div class="document-info">
                  <h3 class="document-title" :title="document.title">
                    {{ document.title }}
                  </h3>
                  
                  <p class="document-desc" v-if="document.description">
                    {{ document.description }}
                  </p>
                  
                  <div class="document-meta">
                    <div class="meta-item">
                      <el-icon><Clock /></el-icon>
                      {{ formatDate(document.created_at) }}
                    </div>
                    <div class="meta-item">
                      <el-icon><Folder /></el-icon>
                      {{ document.file_size_human }}
                    </div>
                  </div>
                  
                  <div class="document-category" v-if="document.category_name">
                    <el-tag :color="document.category_color" size="small">
                      {{ document.category_name }}
                    </el-tag>
                  </div>
                  
                  <div class="document-tags" v-if="document.tags_list.length">
                    <el-tag
                      v-for="tag in document.tags_list.slice(0, 3)"
                      :key="tag"
                      size="small"
                      type="info"
                    >
                      {{ tag }}
                    </el-tag>
                    <span v-if="document.tags_list.length > 3" class="more-tags">
                      +{{ document.tags_list.length - 3 }}
                    </span>
                  </div>
                </div>
                
                <div class="document-actions">
                  <el-button size="small" @click="viewDocument(document)">
                    查看
                  </el-button>
                  <el-button size="small" @click="downloadDocument(document)" type="primary">
                    下载
                  </el-button>
                  <el-dropdown @command="handleDocAction">
                    <el-button size="small" type="info">
                      更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{action: 'edit', doc: document}">
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item :command="{action: 'delete', doc: document}" divided>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>

        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table :data="documents" stripe>
            <el-table-column width="60">
              <template #default="{ row }">
                <span class="file-icon">{{ row.file_type_icon }}</span>
              </template>
            </el-table-column>
            
            <el-table-column label="文档名称" min-width="200">
              <template #default="{ row }">
                <div class="document-name">
                  <div class="title">{{ row.title }}</div>
                  <div class="filename">{{ row.original_filename }}</div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column label="分类" width="120">
              <template #default="{ row }">
                <el-tag v-if="row.category_name" :color="row.category_color" size="small">
                  {{ row.category_name }}
                </el-tag>
                <span v-else class="text-gray">未分类</span>
              </template>
            </el-table-column>
            
            <el-table-column label="文件大小" width="100">
              <template #default="{ row }">
                {{ row.file_size_human }}
              </template>
            </el-table-column>
            
            <el-table-column label="上传时间" width="150">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200">
              <template #default="{ row }">
                <el-button size="small" @click="viewDocument(row)">
                  查看
                </el-button>
                <el-button size="small" type="primary" @click="downloadDocument(row)">
                  下载
                </el-button>
                <el-button size="small" @click="editDocument(row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" @click="deleteDocument(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 空状态 -->
        <el-empty v-if="documents.length === 0" description="暂无文档，点击上传按钮开始添加文档" />
      </el-card>
    </div>

    <!-- 上传文档对话框 -->
    <el-dialog v-model="uploadDialogVisible" title="上传文档" width="600px">
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="选择文件" prop="file">
          <el-upload
            class="upload-demo"
            drag
            :auto-upload="false"
            :on-change="handleFileChange"
            :file-list="fileList"
            :limit="1"
            accept=".pdf,.doc,.docx,.txt,.md,.ppt,.pptx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.bmp"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 PDF、Word、Excel、PowerPoint、图片等格式，文件大小不超过50MB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="文档标题" prop="title">
          <el-input v-model="uploadForm.title" placeholder="请输入文档标题" />
        </el-form-item>
        
        <el-form-item label="文档描述">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入文档描述（可选）"
          />
        </el-form-item>
        
        <el-form-item label="选择分类">
          <el-select v-model="uploadForm.category" placeholder="选择分类" clearable>
            <el-option
              v-for="category in categories"
              :key="category.id"
              :label="category.name"
              :value="category.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="标签">
          <el-input
            v-model="uploadForm.tags"
            placeholder="请输入标签，用逗号分隔（可选）"
          />
        </el-form-item>
        
        <el-form-item label="权限设置">
          <el-radio-group v-model="uploadForm.is_public">
            <el-radio :label="false">私有</el-radio>
            <el-radio :label="true">公开</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload" :loading="uploading">
            上传
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 分类管理对话框 -->
    <el-dialog v-model="categoryDialogVisible" title="新建分类" width="500px">
      <el-form :model="categoryForm" :rules="categoryRules" ref="categoryFormRef" label-width="100px">
        <el-form-item label="分类名称" prop="name">
          <el-input v-model="categoryForm.name" placeholder="请输入分类名称" />
        </el-form-item>
        
        <el-form-item label="分类描述">
          <el-input
            v-model="categoryForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入分类描述（可选）"
          />
        </el-form-item>
        
        <el-form-item label="分类颜色">
          <el-color-picker v-model="categoryForm.color" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="categoryDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCategory">
            创建
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Plus,
  FolderAdd,
  Search,
  Clock,
  Folder,
  ArrowDown,
  UploadFilled
} from '@element-plus/icons-vue'
import apiClient from '@/utils/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

// 响应式数据
const documents = ref([])
const categories = ref([])
const stats = ref({})
const searchKeyword = ref('')
const selectedCategory = ref('')
const selectedFileType = ref('')
const sortBy = ref('-created_at')
const viewMode = ref('card')

// 对话框状态
const uploadDialogVisible = ref(false)
const categoryDialogVisible = ref(false)
const uploading = ref(false)

// 表单数据
const uploadForm = ref({
  title: '',
  description: '',
  file: null,
  category: '',
  tags: '',
  is_public: false
})

const categoryForm = ref({
  name: '',
  description: '',
  color: '#1890ff'
})

const fileList = ref([])

// 文件类型选项
const fileTypes = [
  { label: 'PDF文档', value: 'pdf' },
  { label: 'Word文档', value: 'doc' },
  { label: 'Word文档', value: 'docx' },
  { label: '文本文件', value: 'txt' },
  { label: 'Markdown', value: 'md' },
  { label: 'PowerPoint', value: 'ppt' },
  { label: 'PowerPoint', value: 'pptx' },
  { label: 'Excel表格', value: 'xls' },
  { label: 'Excel表格', value: 'xlsx' },
  { label: '图片文件', value: 'image' },
  { label: '其他文件', value: 'other' }
]

// 表单验证规则
const uploadRules = {
  title: [
    { required: true, message: '请输入文档标题', trigger: 'blur' }
  ],
  file: [
    { required: true, message: '请选择要上传的文件', trigger: 'change' }
  ]
}

const categoryRules = {
  name: [
    { required: true, message: '请输入分类名称', trigger: 'blur' }
  ]
}

const uploadFormRef = ref()
const categoryFormRef = ref()

// 方法
const fetchDocuments = async () => {
  try {
    const params = {
      search: searchKeyword.value,
      category: selectedCategory.value,
      file_type: selectedFileType.value,
      ordering: sortBy.value
    }
    
    const response = await apiClient.get('/documents/list/', { params })
    documents.value = response.data.results || response.data
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('登录已过期，请重新登录')
      userStore.clearAuth()
      router.push('/login')
    } else {
      ElMessage.error('获取文档列表失败')
    }
    console.error('Error fetching documents:', error)
  }
}

const fetchCategories = async () => {
  try {
    const response = await apiClient.get('/documents/categories/')
    categories.value = response.data.results || response.data
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('登录已过期，请重新登录')
      userStore.clearAuth()
      router.push('/login')
    } else {
      ElMessage.error('获取分类列表失败')
    }
    console.error('Error fetching categories:', error)
  }
}

const fetchStats = async () => {
  try {
    const response = await apiClient.get('/documents/stats/')
    stats.value = response.data
  } catch (error) {
    if (error.response?.status === 401) {
      ElMessage.warning('登录已过期，请重新登录')
      userStore.clearAuth()
      router.push('/login')
    } else {
      ElMessage.error('获取统计信息失败')
    }
    console.error('Error fetching stats:', error)
  }
}

const showUploadDialog = () => {
  uploadDialogVisible.value = true
  uploadForm.value = {
    title: '',
    description: '',
    file: null,
    category: '',
    tags: '',
    is_public: false
  }
  fileList.value = []
}

const showCategoryDialog = () => {
  categoryDialogVisible.value = true
  categoryForm.value = {
    name: '',
    description: '',
    color: '#1890ff'
  }
}

const handleFileChange = (file) => {
  uploadForm.value.file = file.raw
  if (!uploadForm.value.title) {
    uploadForm.value.title = file.name.split('.')[0]
  }
}

const submitUpload = async () => {
  if (!uploadFormRef.value) return
  
  await uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      uploading.value = true
      
      const formData = new FormData()
      formData.append('file', uploadForm.value.file)
      formData.append('title', uploadForm.value.title)
      formData.append('description', uploadForm.value.description)
      formData.append('tags', uploadForm.value.tags)
      formData.append('is_public', uploadForm.value.is_public)
      
      if (uploadForm.value.category) {
        formData.append('category', uploadForm.value.category)
      }
      
      try {
        await apiClient.post('/documents/upload/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        })
        
        ElMessage.success('文档上传成功')
        uploadDialogVisible.value = false
        fetchDocuments()
        fetchStats()
      } catch (error) {
        ElMessage.error(error.response?.data?.errors || '上传失败')
      } finally {
        uploading.value = false
      }
    }
  })
}

const submitCategory = async () => {
  if (!categoryFormRef.value) return
  
  await categoryFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await apiClient.post('/documents/categories/', categoryForm.value)
        ElMessage.success('分类创建成功')
        categoryDialogVisible.value = false
        fetchCategories()
        fetchStats()
      } catch (error) {
        ElMessage.error('创建分类失败')
      }
    }
  })
}

const handleSearch = () => {
  fetchDocuments()
}

const handleFilter = () => {
  fetchDocuments()
}

const viewDocument = async (document) => {
  try {
    await apiClient.get(`/documents/${document.id}/`)
    // 这里可以添加文档预览逻辑
    ElMessage.success('查看文档')
  } catch (error) {
    ElMessage.error('无法查看文档')
  }
}

const downloadDocument = async (document) => {
  try {
    const response = await apiClient.get(`/documents/${document.id}/download/`, {
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', document.original_filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    
    ElMessage.success('下载开始')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const editDocument = (document) => {
  // 编辑文档逻辑
  ElMessage.info('编辑功能开发中')
}

const deleteDocument = async (document) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除文档 "${document.title}" 吗？此操作不可撤销。`,
      '确认删除',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await apiClient.delete(`/documents/${document.id}/delete/`)
    ElMessage.success('文档删除成功')
    fetchDocuments()
    fetchStats()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

const handleDocAction = (command) => {
  if (command.action === 'edit') {
    editDocument(command.doc)
  } else if (command.action === 'delete') {
    deleteDocument(command.doc)
  }
}

const formatDate = (dateString) => {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

// 检查用户认证状态
const checkAuth = async () => {
  console.log('检查认证状态:', userStore.isLoggedIn)
  
  if (!userStore.isLoggedIn) {
    ElMessage.warning('请先登录后访问文档管理页面')
    router.push('/login')
    return false
  }
  
  // 验证token有效性
  const isValid = await userStore.validateToken()
  if (!isValid) {
    ElMessage.warning('登录已过期，请重新登录')
    router.push('/login')
    return false
  }
  
  return true
}

// 初始化数据加载
const initializeData = async () => {
  const authOk = await checkAuth()
  if (!authOk) return
  
  try {
    await Promise.all([
      fetchDocuments(),
      fetchCategories(),
      fetchStats()
    ])
  } catch (error) {
    console.error('初始化数据加载失败:', error)
    ElMessage.error('页面数据加载失败，请刷新重试')
  }
}

// 组件挂载时加载数据
onMounted(() => {
  initializeData()
})
</script>

<style scoped>
.documents-container {
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 30px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.header-content h1 {
  margin: 0;
  color: #2d3748;
  font-size: 28px;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-content p {
  margin: 8px 0 0 0;
  color: #718096;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 15px;
}

.stats-cards {
  margin-bottom: 30px;
}

.stat-card {
  display: flex;
  align-items: center;
  padding: 25px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  font-size: 36px;
  margin-right: 20px;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
}

.stat-icon.documents { background: linear-gradient(45deg, #667eea, #764ba2); }
.stat-icon.categories { background: linear-gradient(45deg, #f093fb, #f5576c); }
.stat-icon.size { background: linear-gradient(45deg, #4facfe, #00f2fe); }
.stat-icon.types { background: linear-gradient(45deg, #43e97b, #38f9d7); }

.stat-number {
  font-size: 28px;
  font-weight: 700;
  color: #2d3748;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #718096;
  margin-top: 4px;
}

.search-filter-section {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
  padding: 25px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
}

.search-bar {
  flex: 1;
}

.filter-controls {
  display: flex;
  gap: 15px;
  align-items: center;
}

.documents-content {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.documents-list-card {
  border: none;
  box-shadow: none;
  background: transparent;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-view {
  margin-top: 20px;
}

.document-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.document-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.document-icon {
  text-align: center;
  margin-bottom: 15px;
}

.file-type-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 8px;
}

.file-type {
  font-size: 12px;
  color: #718096;
  font-weight: 600;
}

.document-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #2d3748;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.document-desc {
  font-size: 14px;
  color: #718096;
  margin: 0 0 15px 0;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.document-meta {
  margin-bottom: 12px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #718096;
  margin-bottom: 4px;
}

.document-category {
  margin-bottom: 10px;
}

.document-tags {
  margin-bottom: 15px;
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.more-tags {
  font-size: 12px;
  color: #718096;
}

.document-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
  justify-content: center;
}

.list-view .file-icon {
  font-size: 24px;
}

.document-name .title {
  font-weight: 600;
  color: #2d3748;
}

.document-name .filename {
  font-size: 12px;
  color: #718096;
  margin-top: 2px;
}

.text-gray {
  color: #a0aec0;
}

.upload-demo {
  width: 100%;
}

.el-upload-dragger {
  width: 100% !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .stat-card {
    margin-bottom: 15px;
  }
}

@media (max-width: 768px) {
  .documents-container {
    padding: 15px;
  }

  .page-header {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .search-filter-section {
    flex-direction: column;
  }

  .filter-controls {
    justify-content: stretch;
  }

  .filter-controls > * {
    flex: 1;
  }
}
</style>