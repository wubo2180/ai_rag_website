<template>
  <div class="dify-test-page">
    <div class="page-header">
      <h1>🤖 Dify AI服务测试</h1>
      <p class="subtitle">测试文件上传和AI工作流处理功能</p>
    </div>
    
    <div class="test-sections">
      <!-- 文档处理测试 -->
      <div class="test-section">
        <h2>📄 文档处理测试</h2>
        <DifyUpload />
      </div>
      
      <!-- API测试工具 -->
      <div class="test-section">
        <h2>🔧 API测试工具</h2>
        
        <div class="api-tests">
          <div class="test-card">
            <h3>知识库列表</h3>
            <button @click="testDatasets" :disabled="testing.datasets">
              {{ testing.datasets ? '测试中...' : '测试获取知识库' }}
            </button>
            <div v-if="results.datasets" class="test-result">
              <pre>{{ JSON.stringify(results.datasets, null, 2) }}</pre>
            </div>
          </div>
          
          <div class="test-card">
            <h3>文件上传测试</h3>
            <input 
              ref="testFileInput"
              type="file" 
              @change="handleTestFile"
              accept=".txt,.md"
              style="margin-bottom: 10px;"
            >
            <button @click="testFileUpload" :disabled="!testFile || testing.upload">
              {{ testing.upload ? '上传中...' : '测试文件上传' }}
            </button>
            <div v-if="results.upload" class="test-result">
              <pre>{{ JSON.stringify(results.upload, null, 2) }}</pre>
            </div>
          </div>
          
          <div class="test-card">
            <h3>工作流测试</h3>
            <textarea 
              v-model="workflowInput"
              placeholder="输入测试文本或JSON格式的inputs"
              rows="3"
            ></textarea>
            <button @click="testWorkflow" :disabled="!workflowInput || testing.workflow">
              {{ testing.workflow ? '执行中...' : '测试工作流' }}
            </button>
            <div v-if="results.workflow" class="test-result">
              <pre>{{ JSON.stringify(results.workflow, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 状态监控 -->
      <div class="test-section">
        <h2>📊 API状态监控</h2>
        <div class="status-grid">
          <div class="status-card" :class="apiStatus.connection">
            <i class="fas fa-wifi"></i>
            <h4>连接状态</h4>
            <p>{{ apiStatus.connection === 'success' ? '连接正常' : '连接失败' }}</p>
          </div>
          
          <div class="status-card" :class="apiStatus.auth">
            <i class="fas fa-key"></i>
            <h4>认证状态</h4>
            <p>{{ apiStatus.auth === 'success' ? '认证成功' : '认证失败' }}</p>
          </div>
          
          <div class="status-card" :class="apiStatus.endpoints">
            <i class="fas fa-server"></i>
            <h4>端点状态</h4>
            <p>{{ apiStatus.endpoints === 'success' ? '端点正常' : '端点异常' }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import DifyUpload from '@/components/DifyUpload.vue'
import difyAPI from '@/services/difyAPI'
import { ElMessage } from 'element-plus'

// 响应式数据
const testing = reactive({
  datasets: false,
  upload: false,
  workflow: false
})

const results = reactive({
  datasets: null,
  upload: null,
  workflow: null
})

const apiStatus = reactive({
  connection: 'unknown',
  auth: 'unknown',
  endpoints: 'unknown'
})

const testFile = ref(null)
const workflowInput = ref('')
const testFileInput = ref(null)

// 方法
const handleTestFile = (event) => {
  testFile.value = event.target.files[0]
}

const testDatasets = async () => {
  testing.datasets = true
  results.datasets = null
  
  try {
    const result = await difyAPI.getDatasets({ page: 1, limit: 5 })
    results.datasets = result
    apiStatus.endpoints = 'success'
    ElMessage.success('知识库API测试成功')
  } catch (error) {
    console.error('知识库测试失败:', error)
    results.datasets = { error: error.message }
    apiStatus.endpoints = 'error'
    ElMessage.error('知识库API测试失败')
  } finally {
    testing.datasets = false
  }
}

const testFileUpload = async () => {
  if (!testFile.value) {
    ElMessage.warning('请选择测试文件')
    return
  }
  
  testing.upload = true
  results.upload = null
  
  try {
    const result = await difyAPI.uploadFile(testFile.value, 'test_user')
    results.upload = result
    ElMessage.success('文件上传测试成功')
  } catch (error) {
    console.error('文件上传测试失败:', error)
    results.upload = { error: error.message }
    ElMessage.error('文件上传测试失败')
  } finally {
    testing.upload = false
  }
}

const testWorkflow = async () => {
  if (!workflowInput.value.trim()) {
    ElMessage.warning('请输入测试内容')
    return
  }
  
  testing.workflow = true
  results.workflow = null
  
  try {
    // 尝试解析输入为JSON，如果失败则作为普通文本处理
    let inputs
    try {
      inputs = JSON.parse(workflowInput.value)
    } catch {
      inputs = { message: workflowInput.value }
    }
    
    const result = await difyAPI.runWorkflow(inputs, 'test_user')
    results.workflow = result
    ElMessage.success('工作流测试成功')
  } catch (error) {
    console.error('工作流测试失败:', error)
    results.workflow = { error: error.message }
    ElMessage.error('工作流测试失败')
  } finally {
    testing.workflow = false
  }
}

const checkApiStatus = async () => {
  // 检查连接状态
  try {
    await difyAPI.getDatasets({ page: 1, limit: 1 })
    apiStatus.connection = 'success'
    apiStatus.auth = 'success'
    apiStatus.endpoints = 'success'
  } catch (error) {
    apiStatus.connection = 'error'
    apiStatus.auth = 'error' 
    apiStatus.endpoints = 'error'
    console.error('API状态检查失败:', error)
  }
}

// 生命周期
onMounted(() => {
  checkApiStatus()
  
  // 设置默认的工作流测试输入
  workflowInput.value = JSON.stringify({
    message: "请分析这段文本的主要内容"
  }, null, 2)
})
</script>

<style scoped>
.dify-test-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-header h1 {
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  color: #7f8c8d;
  font-size: 16px;
}

.test-sections {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.test-section {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.test-section h2 {
  color: #2c3e50;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #ecf0f1;
}

.api-tests {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.test-card {
  border: 1px solid #e8ecef;
  border-radius: 8px;
  padding: 20px;
  background: #f8f9fa;
}

.test-card h3 {
  color: #495057;
  margin-bottom: 15px;
}

.test-card button {
  width: 100%;
  padding: 10px 16px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.3s;
}

.test-card button:hover:not(:disabled) {
  background: #0056b3;
}

.test-card button:disabled {
  background: #6c757d;
  cursor: not-allowed;
}

.test-card textarea {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  margin-bottom: 10px;
  font-family: 'Monaco', 'Consolas', monospace;
  font-size: 12px;
}

.test-result {
  margin-top: 15px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  padding: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.test-result pre {
  margin: 0;
  font-size: 12px;
  line-height: 1.4;
  color: #495057;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.status-card {
  padding: 20px;
  border-radius: 8px;
  text-align: center;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.status-card.success {
  background: #d4edda;
  border-color: #c3e6cb;
  color: #155724;
}

.status-card.error {
  background: #f8d7da;
  border-color: #f5c6cb;
  color: #721c24;
}

.status-card.unknown {
  background: #fff3cd;
  border-color: #ffeeba;
  color: #856404;
}

.status-card i {
  font-size: 32px;
  margin-bottom: 10px;
  display: block;
}

.status-card h4 {
  margin: 10px 0 5px;
  font-size: 16px;
}

.status-card p {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}
</style>