<template>
  <div class="knowledge-base-page-wrapper">
    <NavigationSidebar />
    <div class="knowledge-base-container">
      <!-- 页面标题 -->
      <div class="page-header">
        <div class="header-top">
          <div class="breadcrumb">工艺 > 知识库管理 > 基础知识库</div>
          <div class="header-status"><span class="status-dot"></span> 后端在线</div>
        </div>
        <h1 class="page-title">基础知识库</h1>
        <p class="page-subtitle">汇总pdf文档中整理出的材料知识。</p>
      </div>

      <div class="overview-section">
        <div class="overview-left">
          <h3>模块概览</h3>
          <p>
            当前已接入 <strong>{{ totalDatasets }}</strong> 个基础工艺知识库，支持文档检索、详情查看与分页浏览。
          </p>
        </div>
        <div class="overview-right">
          <h3>待接入能力</h3>
          <ul>
            <li>工艺路线关键词：drilling、boring、reaming、milling</li>
            <li>常见材料族：SiC、CFRP、TitaniumAlloy、Copper</li>
            <li>后续支持规则编辑与规则库联动</li>
          </ul>
        </div>
      </div>

      <!-- 搜索和筛选区域 -->
      <div class="search-section">
        <div class="search-controls">
          <div class="search-input-group">
            <input
              v-model="searchKeyword"
              @keyup.enter="searchDatasets"
              type="text"
              class="search-input"
              placeholder="搜索知识库名称..."
            />
            <button @click="searchDatasets" class="search-btn">🔍 搜索</button>
          </div>
          <button @click="refreshDatasets" class="refresh-btn" :disabled="loading">
            🔄 刷新
          </button>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-section">
        <div class="loading-spinner"></div>
        <p>正在加载知识库列表...</p>
      </div>

      <!-- 错误提示 -->
      <div v-if="error" class="error-section">
        <div class="error-message">❌ {{ error }}</div>
        <button @click="refreshDatasets" class="retry-btn">重试</button>
      </div>

      <!-- 知识库列表 -->
      <div v-if="!loading && !error" class="datasets-section">
        <div class="stats-bar">
          <span class="stats-text">
            共找到 <strong>{{ totalDatasets }}</strong> 个知识库
          </span>
        </div>

        <div class="datasets-grid">
          <div
            v-for="dataset in datasets"
            :key="dataset.id"
            class="dataset-card"
            @click="viewDocuments(dataset)"
          >
            <div class="dataset-header">
              <div class="dataset-icon">📚</div>
              <div class="dataset-status" :class="getStatusClass(dataset)">
                {{ dataset.status || '可用' }}
              </div>
            </div>

            <div class="dataset-content">
              <h3 class="dataset-name">{{ dataset.name }}</h3>
              <p class="dataset-description">{{ dataset.description || '暂无描述' }}</p>

              <div class="dataset-meta">
                <div class="meta-item">
                  <span class="meta-label">文档数:</span>
                  <span class="meta-value">{{ dataset.document_count || 0 }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">创建时间:</span>
                  <span class="meta-value">{{ dataset.created_at_readable || '未知' }}</span>
                </div>
                <div class="meta-item">
                  <span class="meta-label">数据源:</span>
                  <span class="meta-value">{{ getDataSourceText(dataset.data_source_type) }}</span>
                </div>
              </div>
            </div>

            <div class="dataset-actions">
              <button @click.stop="viewDocuments(dataset)" class="action-btn view-docs">
                📄 查看文档
              </button>
              <button @click.stop="viewDatasetDetail(dataset)" class="action-btn view-detail">
                ℹ️ 详情
              </button>
            </div>
          </div>
        </div>

        <div v-if="totalPages > 1" class="pagination-section">
          <div class="pagination-controls">
            <button @click="changePage(currentPage - 1)" :disabled="currentPage <= 1" class="page-btn">
              ← 上一页
            </button>

            <div class="page-numbers">
              <span
                v-for="page in visiblePages"
                :key="page"
                @click="changePage(page)"
                :class="['page-number', { active: page === currentPage }]"
              >
                {{ page }}
              </span>
            </div>

            <button @click="changePage(currentPage + 1)" :disabled="currentPage >= totalPages" class="page-btn">
              下一页 →
            </button>
          </div>

          <div class="pagination-info">第 {{ currentPage }} 页，共 {{ totalPages }} 页</div>
        </div>

        <!-- 页面内嵌详情（替代弹窗） -->
        <div v-if="selectedDataset" class="inline-detail-section">
          <div class="inline-detail-header">
            <h2>📚 {{ selectedDataset.name }}</h2>
            <button @click="closeDetail" class="inline-close-btn">收起</button>
          </div>

          <div class="inline-detail-body">
            <div class="detail-section">
              <h3>基本信息</h3>
              <div class="detail-grid">
                <div class="detail-item">
                  <label>名称:</label>
                  <span>{{ selectedDataset.name }}</span>
                </div>
                <div class="detail-item">
                  <label>描述:</label>
                  <span>{{ selectedDataset.description || '暂无描述' }}</span>
                </div>
                <div class="detail-item">
                  <label>文档数量:</label>
                  <span>{{ selectedDataset.document_count || 0 }}</span>
                </div>
                <div class="detail-item">
                  <label>状态:</label>
                  <span :class="getStatusClass(selectedDataset)">{{ selectedDataset.status || '可用' }}</span>
                </div>
                <div class="detail-item">
                  <label>数据源类型:</label>
                  <span>{{ getDataSourceText(selectedDataset.data_source_type) }}</span>
                </div>
                <div class="detail-item">
                  <label>创建时间:</label>
                  <span>{{ selectedDataset.created_at_readable || '未知' }}</span>
                </div>
              </div>
            </div>

            <div class="detail-actions">
              <button @click="viewDocuments(selectedDataset)" class="detail-action-btn">
                📄 查看文档列表
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 页面内嵌文档列表（替代弹窗） -->
      <div v-if="showDocuments" class="inline-documents-section">
        <div class="inline-documents-header">
          <h2>📄 文档列表 - {{ currentDatasetName }}</h2>
          <button @click="closeDocuments" class="inline-close-btn">收起</button>
        </div>

        <div class="inline-documents-body">
          <div class="doc-search">
            <input
              v-model="docSearchKeyword"
              @keyup.enter="searchDocuments"
              type="text"
              class="search-input"
              placeholder="搜索文档名称..."
            />
            <button @click="searchDocuments" class="search-btn">🔍 搜索文档</button>
          </div>

          <div v-if="documentsLoading" class="loading-section">
            <div class="loading-spinner"></div>
            <p>正在加载文档列表...</p>
          </div>

          <div v-else-if="documents.length === 0" class="empty-state">
            暂无文档数据
          </div>

          <div v-else class="documents-list">
            <div v-for="doc in documents" :key="doc.id || doc.name" class="document-item">
              <div class="doc-icon">📄</div>
              <div class="doc-info">
                <h4 class="doc-name">{{ doc.name || '未命名文档' }}</h4>
                <p class="doc-meta">
                  状态：{{ getDocumentStatus(doc.indexing_status || doc.status) }}
                  <span v-if="doc.word_count">｜词数：{{ doc.word_count }}</span>
                  <span v-else-if="doc.size">｜大小：{{ formatFileSize(doc.size) }}</span>
                </p>
                <p class="doc-time">
                  更新时间：{{ formatTime(doc.updated_at || doc.created_at) }}
                </p>
              </div>
            </div>
          </div>

          <div v-if="totalDocPages > 1" class="pagination-section">
            <div class="pagination-controls">
              <button
                @click="changeDocPage(currentDocPage - 1)"
                :disabled="currentDocPage <= 1"
                class="page-btn"
              >
                ← 上一页
              </button>

              <span class="pagination-info">第 {{ currentDocPage }} 页，共 {{ totalDocPages }} 页</span>

              <button
                @click="changeDocPage(currentDocPage + 1)"
                :disabled="currentDocPage >= totalDocPages"
                class="page-btn"
              >
                下一页 →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
  import NavigationSidebar from '@/components/NavigationSidebar.vue'
  import api from '@/utils/api'

  export default {
    name: 'KnowledgeBase',
    components: {
      NavigationSidebar,
    },
    data() {
      return {
        // 数据集相关
        datasets: [],
        totalDatasets: 0,
        currentPage: 1,
        pageSize: 12,
        totalPages: 0,

        // 搜索和状态
        searchKeyword: '',
        loading: false,
        error: null,

        // 详情模态框
        selectedDataset: null,

        // 文档列表相关
        showDocuments: false,
        currentDatasetId: null,
        currentDatasetName: '',
        documents: [],
        totalDocuments: 0,
        currentDocPage: 1,
        docPageSize: 20,
        totalDocPages: 0,
        docSearchKeyword: '',
        documentsLoading: false,
      }
    },

    computed: {
      visiblePages() {
        const pages = []
        const start = Math.max(1, this.currentPage - 2)
        const end = Math.min(this.totalPages, this.currentPage + 2)

        for (let i = start; i <= end; i++) {
          pages.push(i)
        }
        return pages
      },
    },

    mounted() {
      console.log('🧠 知识库管理页面开始加载...')
      console.log('当前路由:', this.$route)
      this.loadDatasets()
    },

    methods: {
      async loadDatasets() {
        this.loading = true
        this.error = null

        try {
          const params = {
            page: this.currentPage,
            limit: this.pageSize,
          }

          if (this.searchKeyword.trim()) {
            params.keyword = this.searchKeyword.trim()
          }

          console.log('🔍 正在加载知识库列表...', params)

          const response = await api.get('knowledgebase/dify/datasets/', {
            params,
          })

          if (response.data.success) {
            const data = response.data.data
            this.datasets = data.data || []
            this.totalDatasets = data.total || 0
            this.totalPages = Math.ceil(this.totalDatasets / this.pageSize)

            console.log(`✅ 成功加载 ${this.datasets.length} 个知识库`)
          } else {
            this.error = response.data.error || '加载知识库失败'
          }
        } catch (error) {
          console.error('❌ 加载知识库失败:', error)
          this.error = '网络错误，请检查连接后重试'
        } finally {
          this.loading = false
        }
      },

      async searchDatasets() {
        this.currentPage = 1
        await this.loadDatasets()
      },

      async refreshDatasets() {
        this.searchKeyword = ''
        this.currentPage = 1
        await this.loadDatasets()
      },

      async changePage(page) {
        if (page >= 1 && page <= this.totalPages) {
          this.currentPage = page
          await this.loadDatasets()
        }
      },

      viewDatasetDetail(dataset) {
        this.selectedDataset = dataset
        console.log('📚 查看知识库详情:', dataset.name)

        this.$nextTick(() => {
          const section = this.$el.querySelector('.inline-detail-section')
          if (section) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        })
      },

      closeDetail() {
        this.selectedDataset = null
      },

      async viewDocuments(dataset) {
        this.currentDatasetId = dataset.id
        this.currentDatasetName = dataset.name
        this.showDocuments = true
        this.closeDetail() // 关闭详情框

        await this.loadDocuments()

        this.$nextTick(() => {
          const section = this.$el.querySelector('.inline-documents-section')
          if (section) {
            section.scrollIntoView({ behavior: 'smooth', block: 'start' })
          }
        })
      },

      closeDocuments() {
        this.showDocuments = false
        this.currentDatasetId = null
        this.currentDatasetName = ''
        this.documents = []
        this.docSearchKeyword = ''
        this.currentDocPage = 1
      },

      async loadDocuments() {
        if (!this.currentDatasetId) return

        this.documentsLoading = true

        try {
          const params = {
            page: this.currentDocPage,
            limit: this.docPageSize,
          }

          if (this.docSearchKeyword.trim()) {
            params.keyword = this.docSearchKeyword.trim()
          }

          console.log('📄 正在加载文档列表...', params)

          const response = await api.get(
            `knowledgebase/dify/datasets/${this.currentDatasetId}/documents/`,
            { params }
          )

          if (response.data.success) {
            const data = response.data.data
            this.documents = data.data || []
            this.totalDocuments = data.total || 0
            this.totalDocPages = Math.ceil(
              this.totalDocuments / this.docPageSize
            )

            console.log(`✅ 成功加载 ${this.documents.length} 个文档`)
          } else {
            console.error('❌ 加载文档失败:', response.data.error)
          }
        } catch (error) {
          console.error('❌ 加载文档失败:', error)
        } finally {
          this.documentsLoading = false
        }
      },

      async searchDocuments() {
        this.currentDocPage = 1
        await this.loadDocuments()
      },

      async changeDocPage(page) {
        if (page >= 1 && page <= this.totalDocPages) {
          this.currentDocPage = page
          await this.loadDocuments()
        }
      },

      getStatusClass(dataset) {
        const status = dataset.status || '可用'
        return {
          'status-available': status === '可用',
          'status-processing': status === '处理中',
          'status-error': status.includes('错误'),
        }
      },

      getDataSourceText(type) {
        const types = {
          upload_file: '上传文件',
          notion_import: 'Notion导入',
          web_crawl: '网页爬取',
          api: 'API接入',
        }
        return types[type] || type || '未知'
      },

      getDocumentStatus(status) {
        const statuses = {
          completed: '已完成',
          processing: '处理中',
          error: '错误',
          waiting: '等待中',
        }
        return statuses[status] || status || '未知'
      },

      formatFileSize(bytes) {
        if (!bytes) return '0 B'
        const k = 1024
        const sizes = ['B', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
      },

      formatTime(timestamp) {
        if (!timestamp) return '未知'
        try {
          return new Date(timestamp * 1000).toLocaleString('zh-CN')
        } catch {
          return '未知'
        }
      },
    },
  }
</script>

<style scoped>
  .knowledge-base-page-wrapper {
    display: flex;
    height: 100vh;
    background: #f4f7fb;
  }

  .knowledge-base-container {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    width: 100%;
    max-width: none;
    margin: 0;
    min-height: 100vh;
    box-sizing: border-box;
  }

  /* 页面标题 */
  .page-header {
    margin-bottom: 18px;
    background: #ffffff;
    border: 1px solid #e8edf5;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    padding: 18px 20px;
  }

  .header-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
    gap: 12px;
    flex-wrap: wrap;
  }

  .breadcrumb {
    color: #94a3b8;
    font-size: 12px;
  }

  .header-status {
    color: #334155;
    font-size: 12px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 10px;
    border: 1px solid #dfe7f3;
    border-radius: 999px;
    background: #f8fbff;
  }

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
  }

  .page-title {
    font-size: 30px;
    margin: 0 0 8px 0;
    font-weight: 700;
    color: #1f2937;
    text-shadow: none;
    letter-spacing: -0.2px;
  }

  .page-subtitle {
    font-size: 14px;
    color: #6b7280;
    opacity: 1;
    margin: 0;
  }

  .overview-section {
    background: #ffffff;
    border: 1px solid #e8edf5;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    padding: 16px 20px;
    margin-bottom: 16px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 18px;
  }

  .overview-section h3 {
    margin: 0 0 8px;
    color: #1e293b;
    font-size: 16px;
  }

  .overview-section p {
    margin: 0;
    color: #64748b;
    font-size: 13px;
    line-height: 1.65;
  }

  .overview-section ul {
    margin: 0;
    padding-left: 18px;
    color: #94a3b8;
    font-size: 13px;
    line-height: 1.65;
  }

  /* 搜索区域 */
  .search-section {
    background: #fff;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #e8edf5;
  }

  .search-controls {
    display: flex;
    gap: 15px;
    align-items: center;
    flex-wrap: wrap;
  }

  .search-input-group {
    display: flex;
    flex: 1;
    min-width: 300px;
  }

  .search-input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #dbe2ec;
    border-radius: 8px 0 0 8px;
    font-size: 14px;
    outline: none;
    transition: all 0.2s;
    background: #fcfdff;
  }

  .search-input:focus {
    border-color: #38bdf8;
    box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.12);
  }

  .search-btn,
  .refresh-btn {
    padding: 10px 18px;
    background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
    color: white;
    border: none;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.3s;
    box-shadow: 0 6px 14px rgba(59, 130, 246, 0.25);
  }

  .search-btn {
    border-radius: 0 8px 8px 0;
  }

  .refresh-btn {
    border-radius: 8px;
  }

  .search-btn:hover,
  .refresh-btn:hover {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    transform: translateY(-1px);
  }

  .refresh-btn:disabled {
    background: #a0a9c0;
    cursor: not-allowed;
    transform: none;
  }

  /* 加载和错误状态 */
  .loading-section,
  .error-section {
    text-align: center;
    padding: 40px;
    background: #fff;
    border-radius: 14px;
    margin-bottom: 20px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #e8edf5;
  }

  .loading-spinner {
    width: 40px;
    height: 40px;
    border: 4px solid #f3f3f3;
    border-top: 4px solid #667eea;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin: 0 auto 15px;
  }

  @keyframes spin {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }

  .error-message {
    color: #e53e3e;
    margin-bottom: 15px;
    font-size: 16px;
  }

  .retry-btn {
    padding: 10px 20px;
    background: #e53e3e;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
  }

  .retry-btn:hover {
    background: #c53030;
  }

  /* 数据集区域 */
  .datasets-section {
    background: #fff;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    border: 1px solid #e8edf5;
  }

  .stats-bar {
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1px solid #e1e5e9;
  }

  .stats-text {
    color: #4a5568;
    font-size: 14px;
  }

  /* 数据集网格 */
  .datasets-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 20px;
    margin-bottom: 30px;
  }

  .dataset-card {
    background: #fff;
    border: 1px solid #e6ebf2;
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.3s;
    box-shadow: 0 3px 12px rgba(15, 23, 42, 0.06);
  }

  .dataset-card:hover {
    border-color: #60a5fa;
    box-shadow: 0 8px 22px rgba(59, 130, 246, 0.2);
    transform: translateY(-2px);
  }

  .dataset-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
  }

  .dataset-icon {
    font-size: 24px;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #eef6ff;
    border-radius: 10px;
  }

  .dataset-status {
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 500;
  }

  .status-available {
    background: #c6f6d5;
    color: #22543d;
  }

  .status-processing {
    background: #fed7c4;
    color: #c05621;
  }

  .status-error {
    background: #fed7d7;
    color: #c53030;
  }

  .dataset-content {
    margin-bottom: 15px;
  }

  .dataset-name {
    font-size: 22px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: #1e293b;
  }

  .dataset-description {
    color: #64748b;
    font-size: 13px;
    margin: 0 0 12px 0;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .dataset-meta {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .meta-item {
    font-size: 12px;
  }

  .meta-label {
    color: #94a3b8;
    margin-right: 4px;
  }

  .meta-value {
    color: #334155;
    font-weight: 500;
  }

  .dataset-actions {
    display: flex;
    gap: 10px;
  }

  .action-btn {
    flex: 1;
    padding: 9px 12px;
    border: 1px solid #e2e8f0;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-size: 12px;
    transition: all 0.3s;
    font-weight: 600;
  }

  .view-docs {
    border-color: #48bb78;
    color: #48bb78;
  }

  .view-docs:hover {
    background: #48bb78;
    color: white;
  }

  .view-detail {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .view-detail:hover {
    background: #3b82f6;
    color: white;
  }

  /* 分页 */
  .pagination-section {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e1e5e9;
    flex-wrap: wrap;
    gap: 15px;
  }

  .pagination-controls {
    display: flex;
    align-items: center;
    gap: 15px;
  }

  .page-btn {
    padding: 8px 16px;
    border: 1px solid #dbe3ee;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
  }

  .page-btn:hover:not(:disabled) {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .page-btn:disabled {
    color: #a0aec0;
    cursor: not-allowed;
  }

  .page-numbers {
    display: flex;
    gap: 5px;
  }

  .page-number {
    padding: 8px 12px;
    border: 1px solid #e1e5e9;
    background: white;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
  }

  .page-number:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .page-number.active {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
  }

  .pagination-info {
    color: #718096;
    font-size: 14px;
  }

  /* 模态框 */
  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 20px;
  }

  .modal-content {
    background: white;
    border-radius: 12px;
    max-width: 600px;
    width: 100%;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
    border: 1px solid #e8edf5;
  }

  .modal-content.large {
    max-width: 900px;
  }

  .inline-documents-section {
    margin-top: 16px;
    background: #fff;
    border: 1px solid #e8edf5;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    overflow: hidden;
  }

  .inline-detail-section {
    margin-top: 16px;
    background: #fff;
    border: 1px solid #e8edf5;
    border-radius: 14px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
    overflow: hidden;
  }

  .inline-detail-header {
    padding: 16px 20px;
    border-bottom: 1px solid #e8edf5;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .inline-detail-header h2 {
    margin: 0;
    font-size: 18px;
    color: #1e293b;
  }

  .inline-detail-body {
    padding: 18px 20px;
  }

  .inline-documents-header {
    padding: 16px 20px;
    border-bottom: 1px solid #e8edf5;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
  }

  .inline-documents-header h2 {
    margin: 0;
    font-size: 18px;
    color: #1e293b;
  }

  .inline-close-btn {
    border: 1px solid #dbe3ee;
    background: #fff;
    color: #334155;
    border-radius: 8px;
    padding: 6px 12px;
    cursor: pointer;
    font-size: 13px;
  }

  .inline-close-btn:hover {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .inline-documents-body {
    padding: 18px 20px;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    border-bottom: 1px solid #e1e5e9;
  }

  .modal-header h2 {
    margin: 0;
    color: #2d3748;
    font-size: 20px;
  }

  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #a0aec0;
    transition: color 0.3s;
  }

  .close-btn:hover {
    color: #e53e3e;
  }

  .modal-body {
    padding: 20px;
  }

  /* 详情内容 */
  .detail-section h3 {
    margin: 0 0 15px 0;
    color: #2d3748;
    font-size: 16px;
  }

  .detail-grid {
    display: grid;
    gap: 12px;
  }

  .detail-item {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .detail-item label {
    min-width: 100px;
    color: #718096;
    font-size: 14px;
    font-weight: 500;
  }

  .detail-item span {
    color: #2d3748;
    font-size: 14px;
  }

  .detail-actions {
    margin-top: 20px;
    padding-top: 20px;
    border-top: 1px solid #e1e5e9;
  }

  .detail-action-btn {
    padding: 10px 20px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    transition: all 0.3s;
  }

  .detail-action-btn:hover {
    background: #2563eb;
    transform: translateY(-1px);
  }

  /* 文档相关 */
  .doc-search {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
  }

  .documents-list {
    max-height: 400px;
    overflow-y: auto;
  }

  .document-item {
    display: flex;
    align-items: center;
    gap: 15px;
    padding: 15px;
    border: 1px solid #e1e5e9;
    border-radius: 8px;
    margin-bottom: 10px;
    transition: all 0.3s;
  }

  .document-item:hover {
    border-color: #60a5fa;
    background: #f8faff;
  }

  .doc-icon {
    font-size: 24px;
    flex-shrink: 0;
  }

  .doc-info {
    flex: 1;
  }

  .doc-name {
    margin: 0 0 5px 0;
    color: #2d3748;
    font-size: 16px;
    font-weight: 500;
  }

  .doc-meta,
  .doc-time {
    margin: 0;
    color: #718096;
    font-size: 12px;
  }

  .empty-state {
    text-align: center;
    padding: 40px;
    color: #a0aec0;
  }

  /* 响应式设计 */
  @media (max-width: 768px) {
    .overview-section {
      grid-template-columns: 1fr;
    }

    .page-title {
      font-size: 24px;
    }

    .datasets-grid {
      grid-template-columns: 1fr;
    }

    .search-controls {
      flex-direction: column;
      align-items: stretch;
    }

    .search-input-group {
      min-width: auto;
    }

    .pagination-section {
      flex-direction: column;
      text-align: center;
    }

    .page-numbers {
      justify-content: center;
    }

    .dataset-meta {
      grid-template-columns: 1fr;
    }
  }
</style>
