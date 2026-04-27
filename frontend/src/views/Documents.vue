<template>
  <div class="documents-page-wrapper">
    <NavigationSidebar />
    <div class="documents-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-content">
          <h1>📚 文档管理系统</h1>
          <p>支持分类、文件夹管理和批量上传</p>
        </div>

        <div class="header-actions">
          <el-button type="primary" @click="showCategoryDialog">
            <el-icon><Plus /></el-icon> 新建分类
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
                <div class="stat-number">
                  {{ Object.keys(stats.file_type_stats || {}).length }}
                </div>
                <div class="stat-label">文件类型</div>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- 分类选择 -->
      <el-card class="category-section" shadow="hover">
        <template #header>
          <div class="card-header">
            <span>📁 文档分类</span>
            <el-button
              type="text"
              @click="loadCategories"
              :loading="categoriesLoading"
            >
              <el-icon><Refresh /></el-icon> 刷新
            </el-button>
          </div>
        </template>

        <el-scrollbar height="150px">
          <div class="categories-grid">
            <div
              v-for="category in categories"
              :key="category?.id || Math.random()"
              :class="[
                'category-item',
                { active: category && selectedCategory === category.id },
              ]"
              @click="category && selectCategory(category.id)"
            >
              <div
                class="category-color"
                :style="{ backgroundColor: category?.color || '#999' }"
              ></div>
              <div class="category-info">
                <div class="category-name">
                  {{ category?.name || '未知分类' }}
                </div>
                <div class="category-count">
                  {{ category?.document_count || 0 }} 文档
                  <span v-if="category?.folder_count">
                    · {{ category.folder_count }} 文件夹</span
                  >
                </div>
              </div>
            </div>
          </div>
        </el-scrollbar>
      </el-card>

      <!-- 当前路径面包屑 -->
      <el-card v-if="selectedCategory" class="path-breadcrumb" shadow="never">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item @click="navigateToRoot">
            <el-icon><HomeFilled /></el-icon> {{ currentCategoryName }}
          </el-breadcrumb-item>
          <el-breadcrumb-item
            v-for="(folder, index) in breadcrumbPath"
            :key="folder.id"
            @click="navigateToFolder(folder.id, index)"
          >
            {{ folder.name }}
          </el-breadcrumb-item>
        </el-breadcrumb>
      </el-card>

      <!-- 文件夹和文档列表 -->
      <el-card v-if="selectedCategory" v-loading="loading">
        <template #header>
          <div class="card-header">
            <span>📂 文件夹列表</span>
            <div class="toolbar">
              <el-button type="primary" size="small" @click="showUploadDialog">
                <el-icon><Upload /></el-icon> 上传文档
              </el-button>
              <el-button
                type="success"
                size="small"
                @click="showBatchUploadDialog"
              >
                <el-icon><FolderAdd /></el-icon> 批量上传
              </el-button>
              <el-button
                v-if="currentFolderId"
                size="small"
                @click="createFolder"
              >
                <el-icon><FolderAdd /></el-icon> 新建子文件夹
              </el-button>
              <el-button v-else size="small" @click="createFolder">
                <el-icon><FolderAdd /></el-icon> 新建文件夹
              </el-button>
            </div>
          </div>
        </template>

        <!-- 文件夹列表 -->
        <div v-if="folders.length > 0" class="folders-section">
          <h4>📁 文件夹</h4>
          <el-row :gutter="20">
            <el-col
              v-for="folder in folders"
              :key="'folder-' + folder.id"
              :span="6"
            >
              <div class="folder-card" @dblclick="navigateToFolder(folder.id)">
                <div class="folder-icon">📁</div>
                <div class="folder-name">{{ folder.name }}</div>
                <div class="folder-stats">
                  {{ folder.document_count }} 个文件
                </div>
                <div class="folder-actions">
                  <el-button
                    type="primary"
                    text
                    size="small"
                    @click.stop="navigateToFolder(folder.id)"
                  >
                    打开
                  </el-button>
                  <el-button
                    type="danger"
                    text
                    size="small"
                    @click.stop="deleteFolder(folder.id)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </el-col>
          </el-row>
          <el-divider />
        </div>

        <!-- 文档列表 -->
        <div v-if="documents.length > 0" class="documents-section">
          <div class="documents-header">
            <h4>📄 文档</h4>
            <div class="batch-actions" v-if="selectedDocuments.length > 0">
              <span class="selected-count"
                >已选择 {{ selectedDocuments.length }} 个CSV文件</span
              >
              <el-button
                type="success"
                size="small"
                @click="transferToKnowledgeGraph"
                :disabled="!hasCSVFiles"
              >
                <el-icon><Connection /></el-icon> 转到知识图谱
              </el-button>
            </div>
          </div>
          <el-table
            :data="documents"
            stripe
            row-key="id"
            @selection-change="handleSelectionChange"
          >
            <el-table-column
              type="selection"
              width="55"
              :selectable="isCSVFile"
              reserve-selection
            />
            <el-table-column label="文件名" min-width="200">
              <template #default="{ row }">
                <div class="file-info">
                  <span class="file-icon">{{ row.file_type_icon }}</span>
                  <span class="file-name">{{
                    row.original_filename || row.title
                  }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="大小" width="100">
              <template #default="{ row }">
                {{ row.file_size_human }}
              </template>
            </el-table-column>

            <el-table-column label="上传者" width="120">
              <template #default="{ row }">
                {{ row.uploaded_by_name }}
              </template>
            </el-table-column>

            <el-table-column label="上传时间" width="180">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  text
                  size="small"
                  @click="viewDocument(row)"
                >
                  <el-icon><View /></el-icon> 查看
                </el-button>
                <el-button
                  type="success"
                  text
                  size="small"
                  @click="downloadDocument(row.id)"
                >
                  <el-icon><Download /></el-icon> 下载
                </el-button>
                <el-button
                  type="danger"
                  text
                  size="small"
                  @click="deleteDocument(row.id)"
                >
                  <el-icon><Delete /></el-icon> 删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-empty
          v-if="folders.length === 0 && documents.length === 0"
          description="暂无数据"
        />
      </el-card>

      <!-- 上传对话框 -->
      <el-dialog v-model="uploadDialogVisible" title="上传文档" width="600px">
        <el-form
          :model="uploadForm"
          :rules="uploadRules"
          ref="uploadFormRef"
          label-width="100px"
        >
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
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将文件拖到此处，或<em>点击上传</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持
                  PDF、Word、Excel、PowerPoint、图片等格式，文件大小不超过50MB
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

          <el-form-item label="标签">
            <el-input
              v-model="uploadForm.tags"
              placeholder="请输入标签，用逗号分隔（可选）"
            />
          </el-form-item>

          <el-form-item label="权限设置">
            <el-radio-group v-model="uploadForm.is_public">
              <el-radio :value="false">私有</el-radio>
              <el-radio :value="true">公开</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-form>

        <template #footer>
          <span class="dialog-footer">
            <el-button @click="uploadDialogVisible = false">取消</el-button>
            <el-button
              type="primary"
              @click="handleUpload"
              :loading="uploading"
            >
              上传
            </el-button>
          </span>
        </template>
      </el-dialog>

      <!-- 批量上传对话框 -->
      <el-dialog
        v-model="batchUploadDialogVisible"
        title="批量上传文档"
        width="600px"
      >
        <el-form label-width="100px">
          <el-form-item label="选择文件">
            <el-upload
              class="upload-demo"
              drag
              :auto-upload="false"
              multiple
              :file-list="batchFileList"
              :on-change="handleBatchFileChange"
              :on-remove="handleBatchFileRemove"
              accept=".pdf,.doc,.docx,.txt,.md,.ppt,.pptx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.bmp"
            >
              <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
              <div class="el-upload__text">
                将多个文件拖到此处，或<em>点击选择</em>
              </div>
              <template #tip>
                <div class="el-upload__tip">
                  支持同时上传多个文件，文件大小不超过50MB
                </div>
              </template>
            </el-upload>
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="batchUploadDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleBatchUpload"
            :loading="batchUploading"
          >
            上传 {{ batchFileList.length }} 个文件
          </el-button>
        </template>
      </el-dialog>

      <!-- 新建分类对话框 -->
      <el-dialog v-model="categoryDialogVisible" title="新建分类" width="500px">
        <el-form :model="categoryForm" label-width="100px">
          <el-form-item label="分类名称">
            <el-input
              v-model="categoryForm.name"
              placeholder="请输入分类名称"
            />
          </el-form-item>

          <el-form-item label="分类颜色">
            <el-color-picker v-model="categoryForm.color" />
          </el-form-item>

          <el-form-item label="描述">
            <el-input
              v-model="categoryForm.description"
              type="textarea"
              :rows="3"
              placeholder="分类描述"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="categoryDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="createCategory"
            :loading="categoryCreating"
          >
            创建
          </el-button>
        </template>
      </el-dialog>

      <!-- 新建文件夹对话框 -->
      <el-dialog v-model="folderDialogVisible" title="新建文件夹" width="500px">
        <el-form :model="folderForm" label-width="100px">
          <el-form-item label="文件夹名称">
            <el-input
              v-model="folderForm.name"
              placeholder="请输入文件夹名称"
            />
          </el-form-item>

          <el-form-item label="描述">
            <el-input
              v-model="folderForm.description"
              type="textarea"
              :rows="3"
              placeholder="文件夹描述（可选）"
            />
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="folderDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="handleCreateFolder"
            :loading="folderCreating"
          >
            创建
          </el-button>
        </template>
      </el-dialog>

      <!-- 文档查看对话框 -->
      <el-dialog
        v-model="viewDialogVisible"
        :title="currentDocument?.title"
        width="800px"
      >
        <div v-if="currentDocument" class="document-detail">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="文件名">
              {{ currentDocument.original_filename }}
            </el-descriptions-item>
            <el-descriptions-item label="文件大小">
              {{ currentDocument.file_size_human }}
            </el-descriptions-item>
            <el-descriptions-item label="文件类型">
              {{ currentDocument.file_type_icon }}
              {{ currentDocument.file_type }}
            </el-descriptions-item>
            <el-descriptions-item label="上传者">
              {{ currentDocument.uploaded_by_name }}
            </el-descriptions-item>
            <el-descriptions-item label="上传时间" :span="2">
              {{ formatDate(currentDocument.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="描述" :span="2">
              {{ currentDocument.description || '无' }}
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <template #footer>
          <el-button @click="viewDialogVisible = false">关闭</el-button>
          <el-button
            type="primary"
            @click="downloadDocument(currentDocument.id)"
          >
            <el-icon><Download /></el-icon> 下载
          </el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup>
  import NavigationSidebar from '@/components/NavigationSidebar.vue'
  import { ref, reactive, onMounted, computed } from 'vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import {
    Upload,
    FolderAdd,
    Plus,
    Refresh,
    HomeFilled,
    View,
    Download,
    Delete,
    Search,
    UploadFilled,
    Connection,
  } from '@element-plus/icons-vue'
  import { useRouter } from 'vue-router'
  import { useUserStore } from '@/stores/user'
  import apiClient from '@/utils/api'

  const API_BASE = '/documents' // apiClient 已经包含 /api 前缀
  const router = useRouter()
  const userStore = useUserStore()

  // 数据
  const categories = ref([])
  const folders = ref([])
  const documents = ref([])
  const selectedCategory = ref(null)
  const currentFolderId = ref(null)
  const breadcrumbPath = ref([])
  const stats = ref({
    total_documents: 0,
    total_categories: 0,
    total_size_human: '0 B',
    file_type_stats: {},
  })

  // 文件选择相关
  const selectedDocuments = ref([])
  const hasCSVFiles = computed(() => {
    return selectedDocuments.value.some(
      (doc) =>
        doc.original_filename &&
        doc.original_filename.toLowerCase().endsWith('.csv')
    )
  })

  // 加载状态
  const loading = ref(false)
  const categoriesLoading = ref(false)
  const uploading = ref(false)
  const batchUploading = ref(false)
  const categoryCreating = ref(false)
  const folderCreating = ref(false)

  // 对话框
  const uploadDialogVisible = ref(false)
  const batchUploadDialogVisible = ref(false)
  const categoryDialogVisible = ref(false)
  const folderDialogVisible = ref(false)
  const viewDialogVisible = ref(false)

  // 表单
  const uploadForm = reactive({
    title: '',
    description: '',
    file: null,
    tags: '',
    is_public: false,
  })

  const batchFileList = ref([])
  const fileList = ref([])

  // 表单引用
  const uploadFormRef = ref()

  // 表单验证规则
  const uploadRules = {
    title: [{ required: true, message: '请输入文档标题', trigger: 'blur' }],
    file: [
      { required: true, message: '请选择要上传的文件', trigger: 'change' },
    ],
  }

  const categoryForm = reactive({
    name: '',
    color: '#1890ff',
    description: '',
  })

  const folderForm = reactive({
    name: '',
    description: '',
  })

  const currentDocument = ref(null)

  // 计算属性
  const currentCategoryName = computed(() => {
    if (!selectedCategory.value || !Array.isArray(categories.value)) {
      return ''
    }
    const category = categories.value.find(
      (c) => c && c.id === selectedCategory.value
    )
    return category ? category.name : ''
  })

  // 方法
  const loadCategories = async () => {
    categoriesLoading.value = true
    try {
      // 检查登录状态
      if (!userStore.isLoggedIn) {
        ElMessage.warning('请先登录')
        router.push('/login')
        return
      }

      const response = await apiClient.get(`${API_BASE}/categories/`)
      console.log('Categories response:', response.data) // 调试信息

      // 处理可能的分页格式或直接数组格式
      if (Array.isArray(response.data)) {
        categories.value = response.data
      } else if (response.data && Array.isArray(response.data.results)) {
        // 分页格式
        categories.value = response.data.results
      } else {
        console.error('Unexpected categories data format:', response.data)
        categories.value = []
      }

      console.log('Parsed categories:', categories.value) // 调试信息
    } catch (error) {
      console.error('Load categories error:', error) // 调试信息
      ElMessage.error(
        '加载分类失败: ' + (error.response?.data?.detail || error.message)
      )
      if (error.response?.status === 401) {
        router.push('/login')
      }
      categories.value = [] // 出错时设置为空数组
    } finally {
      categoriesLoading.value = false
    }
  }

  const fetchStats = async () => {
    try {
      const response = await apiClient.get(`${API_BASE}/stats/`)
      stats.value = response.data
    } catch (error) {
      console.error('Error fetching stats:', error)
      if (error.response?.status === 401) {
        router.push('/login')
      }
    }
  }

  const selectCategory = async (categoryId) => {
    console.log('Selecting category:', categoryId) // 调试信息
    selectedCategory.value = categoryId
    currentFolderId.value = null
    breadcrumbPath.value = []
    await loadCategoryContents()
  }

  const loadCategoryContents = async () => {
    loading.value = true
    try {
      let url = `${API_BASE}/categories/${selectedCategory.value}/documents/`

      if (currentFolderId.value) {
        url += `?folder=${currentFolderId.value}`
      }

      console.log('Loading category contents from:', url) // 调试信息
      const response = await apiClient.get(url)
      console.log('Category contents response:', response.data) // 调试信息

      folders.value = response.data.folders || []
      documents.value = response.data.documents || []

      // 调试输出
      console.log('加载的文档数据:', documents.value)
      console.log('文档数量:', documents.value.length)
    } catch (error) {
      console.error('Load category contents error:', error) // 调试信息
      console.error('Error response:', error.response) // 调试信息
      ElMessage.error(
        '加载内容失败: ' +
          (error.response?.data?.detail ||
            error.response?.data?.error ||
            error.message)
      )
    } finally {
      loading.value = false
    }
  }

  const navigateToRoot = () => {
    currentFolderId.value = null
    breadcrumbPath.value = []
    loadCategoryContents()
  }

  const navigateToFolder = async (folderId, breadcrumbIndex = null) => {
    if (breadcrumbIndex !== null) {
      breadcrumbPath.value = breadcrumbPath.value.slice(0, breadcrumbIndex + 1)
    } else {
      const folder = folders.value.find((f) => f.id === folderId)
      if (folder) {
        breadcrumbPath.value.push({ id: folder.id, name: folder.name })
      }
    }

    currentFolderId.value = folderId
    await loadCategoryContents()
  }

  const showUploadDialog = () => {
    if (!selectedCategory.value) {
      ElMessage.warning('请先选择一个分类')
      return
    }
    uploadDialogVisible.value = true
    // 重置表单
    uploadForm.title = ''
    uploadForm.description = ''
    uploadForm.file = null
    uploadForm.tags = ''
    uploadForm.is_public = false
    fileList.value = []
  }

  const showBatchUploadDialog = () => {
    if (!selectedCategory.value) {
      ElMessage.warning('请先选择一个分类')
      return
    }
    batchUploadDialogVisible.value = true
    batchFileList.value = []
  }

  const showCategoryDialog = () => {
    categoryDialogVisible.value = true
  }

  const handleFileChange = (file) => {
    uploadForm.file = file.raw
    // 自动填充标题
    if (!uploadForm.title) {
      uploadForm.title = file.name.split('.')[0]
    }
  }

  const handleBatchFileChange = (file, fileList) => {
    batchFileList.value = fileList
  }

  const handleBatchFileRemove = (file, fileList) => {
    batchFileList.value = fileList
  }

  const handleUpload = async () => {
    if (!uploadFormRef.value) return

    await uploadFormRef.value.validate(async (valid) => {
      if (valid) {
        uploading.value = true
        try {
          const formData = new FormData()
          formData.append('file', uploadForm.file)
          formData.append('title', uploadForm.title)
          formData.append('description', uploadForm.description)
          formData.append('tags', uploadForm.tags)
          formData.append('is_public', uploadForm.is_public)
          formData.append('category', selectedCategory.value)

          if (currentFolderId.value) {
            formData.append('folder', currentFolderId.value)
          }

          console.log('Upload data:', {
            file: uploadForm.file.name,
            title: uploadForm.title,
            category: selectedCategory.value,
            folder: currentFolderId.value,
            tags: uploadForm.tags,
            is_public: uploadForm.is_public,
          })

          await apiClient.post(`${API_BASE}/upload/`, formData, {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          })

          ElMessage.success('文档上传成功')
          uploadDialogVisible.value = false
          await loadCategoryContents()
          await fetchStats() // 更新统计数据
        } catch (error) {
          console.error('Upload error:', error.response?.data || error)

          let errorMessage = '上传失败'

          if (error.response?.data) {
            if (error.response.data.errors) {
              // 处理验证错误
              if (typeof error.response.data.errors === 'object') {
                const errorMessages = Object.values(error.response.data.errors)
                  .flat()
                  .join(', ')
                errorMessage = `上传失败: ${errorMessages}`
              } else {
                errorMessage = `上传失败: ${error.response.data.errors}`
              }
            } else if (error.response.data.error) {
              errorMessage = `上传失败: ${error.response.data.error}`
            } else if (error.response.data.message) {
              errorMessage = `上传失败: ${error.response.data.message}`
            } else if (typeof error.response.data === 'string') {
              errorMessage = `上传失败: ${error.response.data}`
            } else {
              errorMessage = `上传失败: ${JSON.stringify(error.response.data)}`
            }
          } else if (error.message) {
            errorMessage = `上传失败: ${error.message}`
          } else {
            errorMessage = '上传失败: 未知错误'
          }

          ElMessage.error(errorMessage)
        } finally {
          uploading.value = false
        }
      }
    })
  }

  const handleBatchUpload = async () => {
    if (batchFileList.value.length === 0) {
      ElMessage.warning('请选择要上传的文件')
      return
    }

    batchUploading.value = true
    try {
      const formData = new FormData()

      batchFileList.value.forEach((fileItem) => {
        formData.append('files', fileItem.raw)
      })

      formData.append('category', selectedCategory.value)
      if (currentFolderId.value) {
        formData.append('folder', currentFolderId.value)
      }

      console.log('Batch upload data:', {
        filesCount: batchFileList.value.length,
        category: selectedCategory.value,
        folder: currentFolderId.value,
      })

      const response = await apiClient.post(
        `${API_BASE}/batch-upload/`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      )

      ElMessage.success(response.data.message)
      batchUploadDialogVisible.value = false
      batchFileList.value = []
      await loadCategoryContents()
      await fetchStats() // 更新统计数据
    } catch (error) {
      console.error('Batch upload error:', error.response?.data || error)

      let errorMessage = '批量上传失败'

      if (error.response?.data) {
        if (error.response.data.errors) {
          // 处理验证错误
          if (typeof error.response.data.errors === 'object') {
            const errorMessages = Object.values(error.response.data.errors)
              .flat()
              .join(', ')
            errorMessage = `批量上传失败: ${errorMessages}`
          } else {
            errorMessage = `批量上传失败: ${error.response.data.errors}`
          }
        } else if (error.response.data.error) {
          errorMessage = `批量上传失败: ${error.response.data.error}`
        } else if (error.response.data.message) {
          errorMessage = `批量上传失败: ${error.response.data.message}`
        } else if (typeof error.response.data === 'string') {
          errorMessage = `批量上传失败: ${error.response.data}`
        } else {
          errorMessage = `批量上传失败: ${JSON.stringify(error.response.data)}`
        }
      } else if (error.message) {
        errorMessage = `批量上传失败: ${error.message}`
      } else {
        errorMessage = '批量上传失败: 未知错误'
      }

      ElMessage.error(errorMessage)
    } finally {
      batchUploading.value = false
    }
  }

  const createCategory = async () => {
    if (!categoryForm.name) {
      ElMessage.warning('请输入分类名称')
      return
    }

    categoryCreating.value = true
    try {
      const createResponse = await apiClient.post(
        `${API_BASE}/categories/`,
        categoryForm
      )
      console.log('Create category response:', createResponse.data) // 调试信息

      ElMessage.success('创建成功')
      categoryDialogVisible.value = false
      categoryForm.name = ''
      categoryForm.color = '#1890ff'
      categoryForm.description = ''
      await loadCategories()
      await fetchStats() // 更新统计数据
      console.log('Categories after reload:', categories.value) // 调试信息
    } catch (error) {
      console.error('Create category error:', error) // 调试信息
      ElMessage.error(
        '创建失败: ' + (error.response?.data?.detail || error.message)
      )
    } finally {
      categoryCreating.value = false
    }
  }

  const createFolder = () => {
    folderDialogVisible.value = true
  }

  const handleCreateFolder = async () => {
    if (!folderForm.name) {
      ElMessage.warning('请输入文件夹名称')
      return
    }

    folderCreating.value = true
    try {
      const data = {
        name: folderForm.name,
        description: folderForm.description,
        category: selectedCategory.value,
        parent: currentFolderId.value,
      }

      await apiClient.post(`${API_BASE}/folders/`, data)

      ElMessage.success('文件夹创建成功')
      folderDialogVisible.value = false
      folderForm.name = ''
      folderForm.description = ''
      await loadCategoryContents()
    } catch (error) {
      ElMessage.error(
        '创建失败: ' + (error.response?.data?.detail || error.message)
      )
    } finally {
      folderCreating.value = false
    }
  }

  const deleteFolder = async (folderId) => {
    try {
      await ElMessageBox.confirm('确定要删除此文件夹吗？', '提示', {
        type: 'warning',
      })

      await apiClient.delete(`${API_BASE}/folders/${folderId}/`)

      ElMessage.success('删除成功')
      await loadCategoryContents()
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(
          '删除失败: ' + (error.response?.data?.error || error.message)
        )
      }
    }
  }

  const viewDocument = (doc) => {
    currentDocument.value = doc
    viewDialogVisible.value = true
  }

  const downloadDocument = async (docId) => {
    try {
      const response = await apiClient.get(`${API_BASE}/${docId}/download/`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url

      const contentDisposition = response.headers['content-disposition']
      let filename = 'download'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      ElMessage.success('下载成功')
    } catch (error) {
      ElMessage.error(
        '下载失败: ' + (error.response?.data?.detail || error.message)
      )
    }
  }

  const deleteDocument = async (docId) => {
    try {
      await ElMessageBox.confirm('确定要删除此文档吗？', '提示', {
        type: 'warning',
      })

      await apiClient.delete(`${API_BASE}/${docId}/delete/`)

      ElMessage.success('删除成功')
      await loadCategoryContents()
      await fetchStats() // 更新统计数据
    } catch (error) {
      if (error !== 'cancel') {
        ElMessage.error(
          '删除失败: ' + (error.response?.data?.detail || error.message)
        )
      }
    }
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  }

  // 文件选择相关方法
  const handleSelectionChange = (selection) => {
    selectedDocuments.value = selection
  }

  const isCSVFile = (row) => {
    // 调试输出
    console.log('isCSVFile 检查行数据:', row)
    console.log('原始文件名:', row.original_filename)

    // 临时：让所有文件都可以选择，用于测试
    return true

    // 检查原始文件名而不是URL路径
    // const result = row.original_filename && row.original_filename.toLowerCase().endsWith('.csv')
    // return result
  }

  const transferToKnowledgeGraph = async () => {
    const csvFiles = selectedDocuments.value.filter(
      (doc) =>
        doc.original_filename &&
        doc.original_filename.toLowerCase().endsWith('.csv')
    )

    if (csvFiles.length === 0) {
      ElMessage.warning('请选择至少一个CSV文件')
      return
    }

    try {
      ElMessage({
        type: 'info',
        message: `正在处理 ${csvFiles.length} 个CSV文件...`,
        duration: 2000,
      })

      // 调用API处理CSV文件
      const response = await apiClient.post('/kg/process-csv-documents/', {
        document_ids: csvFiles.map((doc) => doc.id),
      })

      ElMessage.success(
        `成功处理 ${csvFiles.length} 个CSV文件，已转换为知识图谱数据`
      )

      // 跳转到知识图谱页面
      router.push('/knowledge-graph')
    } catch (error) {
      console.error('Transfer to knowledge graph error:', error)
      ElMessage.error(
        '处理CSV文件失败: ' + (error.response?.data?.detail || error.message)
      )
    }
  }

  // 生命周期
  onMounted(async () => {
    await loadCategories()
    await fetchStats()
  })
</script>

<style scoped>
  .documents-page-wrapper {
    display: flex;
    height: 100vh;
  }

  .documents-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    width: 100%;
    max-width: none;
    margin: 0;
    min-height: 100vh;
    box-sizing: border-box;
  }

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .header-content h1 {
    font-size: 2rem;
    margin: 0 0 5px 0;
    color: #333;
  }

  .header-content p {
    margin: 0;
    color: #666;
  }

  .header-actions {
    display: flex;
    gap: 10px;
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

  .stat-icon.documents {
    background: linear-gradient(45deg, #667eea, #764ba2);
  }
  .stat-icon.categories {
    background: linear-gradient(45deg, #f093fb, #f5576c);
  }
  .stat-icon.size {
    background: linear-gradient(45deg, #4facfe, #00f2fe);
  }
  .stat-icon.types {
    background: linear-gradient(45deg, #43e97b, #38f9d7);
  }

  .stat-content {
    flex: 1;
  }

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

  .category-section {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .categories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 15px;
  }

  .category-item {
    display: flex;
    align-items: center;
    padding: 15px;
    border: 2px solid #e4e7ed;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.3s;
  }

  .category-item:hover {
    border-color: #409eff;
    background: #f0f9ff;
  }

  .category-item.active {
    border-color: #409eff;
    background: #ecf5ff;
  }

  .category-color {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    margin-right: 15px;
  }

  .category-name {
    font-weight: 600;
    margin-bottom: 5px;
  }

  .category-count {
    font-size: 12px;
    color: #909399;
  }

  .path-breadcrumb {
    margin-bottom: 20px;
  }

  .folders-section,
  .documents-section {
    margin-bottom: 20px;
  }

  .folder-card {
    border: 1px solid #e4e7ed;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s;
    margin-bottom: 20px;
  }

  .folder-card:hover {
    border-color: #409eff;
    background: #f0f9ff;
    transform: translateY(-2px);
  }

  .folder-icon {
    font-size: 48px;
    margin-bottom: 10px;
  }

  .folder-name {
    font-weight: 600;
    margin-bottom: 5px;
  }

  .folder-stats {
    font-size: 12px;
    color: #909399;
    margin-bottom: 10px;
  }

  .folder-actions {
    display: flex;
    justify-content: center;
    gap: 10px;
  }

  .file-info {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .file-icon {
    font-size: 20px;
  }

  .toolbar {
    display: flex;
    gap: 10px;
  }

  .documents-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }

  .batch-actions {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .selected-count {
    color: #409eff;
    font-weight: 500;
    font-size: 14px;
  }
</style>
