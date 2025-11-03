<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <h3>
          <i :class="agent?.icon || 'fas fa-robot'" :style="{ color: getThemeColor(agent?.color_theme) }"></i>
          执行任务 - {{ agent?.display_name }}
        </h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <!-- 智能体信息 -->
        <div class="agent-info-card">
          <div class="agent-description">
            <p>{{ agent?.description }}</p>
          </div>
          <div class="agent-capabilities">
            <h4>支持的功能：</h4>
            <div class="capability-list">
              <span 
                v-for="capability in agent?.capabilities"
                :key="capability"
                class="capability-tag"
              >
                {{ capability }}
              </span>
            </div>
          </div>
        </div>

        <!-- 任务配置表单 -->
        <form @submit.prevent="submitTask" class="task-form">
          <div class="form-group">
            <label for="taskTitle">任务标题 *</label>
            <input 
              id="taskTitle"
              v-model="taskData.title"
              type="text" 
              placeholder="请输入任务标题"
              required
            />
          </div>

          <div class="form-group">
            <label for="taskDescription">任务描述</label>
            <textarea 
              id="taskDescription"
              v-model="taskData.description"
              placeholder="请描述您的任务需求..."
              rows="3"
            ></textarea>
          </div>

          <!-- 动态输入字段 -->
          <div class="input-section">
            <h4>输入数据</h4>
            <div class="input-types">
              <span 
                v-for="inputType in agent?.supported_inputs"
                :key="inputType"
                class="input-type-tag"
              >
                支持：{{ inputType }}
              </span>
            </div>

            <!-- 根据智能体类型显示不同的输入表单 -->
            <div v-if="agent?.category === 'data_analysis'" class="category-inputs">
              <div class="form-group">
                <label>数据文件</label>
                <div class="file-upload">
                  <input 
                    type="file" 
                    @change="handleFileUpload"
                    accept=".csv,.xlsx,.json"
                    ref="fileInput"
                  />
                  <div v-if="uploadedFile" class="file-info">
                    <i class="fas fa-file"></i>
                    <span>{{ uploadedFile.name }}</span>
                    <button type="button" @click="removeFile" class="remove-file">
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>分析类型</label>
                <select v-model="taskData.input_data.analysis_type">
                  <option value="composition_process">成分-工艺关联</option>
                  <option value="structure_property">结构-性能关联</option>
                  <option value="full_chain">完整四级关联</option>
                </select>
              </div>
            </div>

            <div v-else-if="agent?.category === 'property_prediction'" class="category-inputs">
              <div class="form-group">
                <label>材料成分</label>
                <textarea 
                  v-model="taskData.input_data.composition"
                  placeholder="请输入材料成分信息，如：Fe-18Cr-12Ni-2.5Mo"
                  rows="2"
                ></textarea>
              </div>
              
              <div class="form-group">
                <label>预测性质</label>
                <div class="checkbox-group">
                  <label v-for="property in propertyTypes" :key="property.value" class="checkbox-label">
                    <input 
                      type="checkbox" 
                      :value="property.value"
                      v-model="taskData.input_data.properties"
                    />
                    {{ property.label }}
                  </label>
                </div>
              </div>
            </div>

            <div v-else-if="agent?.category === 'process_optimization'" class="category-inputs">
              <div class="form-group">
                <label>当前工艺参数</label>
                <div class="parameter-inputs">
                  <div class="param-row">
                    <label>温度 (°C)</label>
                    <input 
                      type="number" 
                      v-model="taskData.input_data.current_params.temperature"
                      placeholder="1200"
                    />
                  </div>
                  <div class="param-row">
                    <label>压力 (MPa)</label>
                    <input 
                      type="number" 
                      v-model="taskData.input_data.current_params.pressure"
                      placeholder="150"
                    />
                  </div>
                  <div class="param-row">
                    <label>时间 (min)</label>
                    <input 
                      type="number" 
                      v-model="taskData.input_data.current_params.duration"
                      placeholder="120"
                    />
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>优化目标</label>
                <div class="checkbox-group">
                  <label v-for="goal in optimizationGoals" :key="goal.value" class="checkbox-label">
                    <input 
                      type="checkbox" 
                      :value="goal.value"
                      v-model="taskData.input_data.optimization_goals"
                    />
                    {{ goal.label }}
                  </label>
                </div>
              </div>
            </div>

            <div v-else-if="agent?.category === 'knowledge_extraction'" class="category-inputs">
              <div class="form-group">
                <label>文献文件</label>
                <div class="file-upload">
                  <input 
                    type="file" 
                    @change="handleFileUpload"
                    accept=".pdf,.txt,.docx"
                    ref="fileInput"
                  />
                  <div v-if="uploadedFile" class="file-info">
                    <i class="fas fa-file"></i>
                    <span>{{ uploadedFile.name }}</span>
                    <button type="button" @click="removeFile" class="remove-file">
                      <i class="fas fa-times"></i>
                    </button>
                  </div>
                </div>
              </div>
              
              <div class="form-group">
                <label>抽取内容</label>
                <div class="checkbox-group">
                  <label v-for="content in extractionContents" :key="content.value" class="checkbox-label">
                    <input 
                      type="checkbox" 
                      :value="content.value"
                      v-model="taskData.input_data.extraction_targets"
                    />
                    {{ content.label }}
                  </label>
                </div>
              </div>
            </div>

            <div v-else-if="agent?.category === 'decision_support'" class="category-inputs">
              <div class="form-group">
                <label>应用需求</label>
                <textarea 
                  v-model="taskData.input_data.requirements.description"
                  placeholder="请详细描述您的应用需求和约束条件..."
                  rows="3"
                ></textarea>
              </div>
              
              <div class="form-group">
                <label>性能要求</label>
                <div class="requirement-inputs">
                  <div class="req-row">
                    <label>强度要求 (MPa)</label>
                    <input 
                      type="number" 
                      v-model="taskData.input_data.requirements.strength_min"
                      placeholder="500"
                    />
                  </div>
                  <div class="req-row">
                    <label>预算限制 (万元)</label>
                    <input 
                      type="number" 
                      v-model="taskData.input_data.requirements.budget_max"
                      placeholder="100"
                    />
                  </div>
                </div>
              </div>
            </div>

            <!-- 通用文本输入 -->
            <div v-else class="category-inputs">
              <div class="form-group">
                <label>输入数据</label>
                <textarea 
                  v-model="taskData.input_data.content"
                  placeholder="请输入相关数据或描述..."
                  rows="4"
                ></textarea>
              </div>
            </div>
          </div>
        </form>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn btn-secondary" @click="$emit('close')">
          取消
        </button>
        <button 
          type="button" 
          class="btn btn-primary" 
          @click="submitTask"
          :disabled="loading || !isFormValid"
        >
          <i v-if="loading" class="fas fa-spinner fa-spin"></i>
          <i v-else class="fas fa-play"></i>
          {{ loading ? '创建中...' : '开始执行' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  agent: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'task-created'])

// 响应式数据
const loading = ref(false)
const uploadedFile = ref(null)

const taskData = reactive({
  title: '',
  description: '',
  input_data: {}
})

// 选项数据
const propertyTypes = [
  { value: 'mechanical', label: '力学性能' },
  { value: 'electrical', label: '电学性能' },
  { value: 'thermal', label: '热学性能' },
  { value: 'chemical', label: '化学稳定性' }
]

const optimizationGoals = [
  { value: 'quality', label: '提高质量' },
  { value: 'cost', label: '降低成本' },
  { value: 'efficiency', label: '提升效率' },
  { value: 'energy', label: '节能减排' }
]

const extractionContents = [
  { value: 'materials', label: '材料信息' },
  { value: 'properties', label: '性能数据' },
  { value: 'processes', label: '工艺参数' },
  { value: 'applications', label: '应用领域' }
]

// 计算属性
const isFormValid = computed(() => {
  return taskData.title.trim() !== ''
})

// 监听智能体变化，初始化输入数据
watch(() => props.agent, (newAgent) => {
  if (newAgent) {
    initializeInputData()
  }
}, { immediate: true })

// 方法
const initializeInputData = () => {
  const category = props.agent?.category
  
  switch (category) {
    case 'data_analysis':
      taskData.input_data = {
        analysis_type: 'full_chain',
        data_file: null
      }
      break
    case 'property_prediction':
      taskData.input_data = {
        composition: '',
        properties: []
      }
      break
    case 'process_optimization':
      taskData.input_data = {
        current_params: {
          temperature: null,
          pressure: null,
          duration: null
        },
        optimization_goals: []
      }
      break
    case 'knowledge_extraction':
      taskData.input_data = {
        document_file: null,
        extraction_targets: []
      }
      break
    case 'decision_support':
      taskData.input_data = {
        requirements: {
          description: '',
          strength_min: null,
          budget_max: null
        }
      }
      break
    default:
      taskData.input_data = {
        content: ''
      }
  }
}

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    uploadedFile.value = file
    // 这里可以添加文件上传到服务器的逻辑
  }
}

const removeFile = () => {
  uploadedFile.value = null
  if (refs.fileInput) {
    refs.fileInput.value = ''
  }
}

const submitTask = async () => {
  if (!isFormValid.value) return
  
  try {
    loading.value = true
    
    // 准备任务数据
    const payload = {
      title: taskData.title,
      description: taskData.description,
      input_data: taskData.input_data
    }
    
    // 如果有文件，先上传文件
    if (uploadedFile.value) {
      // 这里应该先上传文件并获取文件URL
      // payload.input_data.file_url = await uploadFile(uploadedFile.value)
    }
    
    // 执行智能体任务
    const response = await axios.post(`/api/smart-agent/agents/${props.agent.id}/execute/`, payload)
    
    emit('task-created', response.data.task)
    emit('close')
    
  } catch (error) {
    console.error('创建任务失败:', error)
    // 这里可以添加错误提示
  } finally {
    loading.value = false
  }
}

const getThemeColor = (theme) => {
  const colors = {
    blue: '#3498db',
    green: '#27ae60',
    orange: '#f39c12',
    purple: '#9b59b6',
    red: '#e74c3c',
    teal: '#1abc9c'
  }
  return colors[theme] || colors.blue
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-container {
  background: white;
  border-radius: 20px;
  width: 100%;
  max-width: 600px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  padding: 1.5rem 2rem;
  border-bottom: 1px solid #ecf0f1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h3 {
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: background 0.3s ease;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.modal-body {
  padding: 2rem;
  max-height: calc(90vh - 200px);
  overflow-y: auto;
}

.agent-info-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.agent-description {
  margin-bottom: 1rem;
}

.agent-description p {
  color: #5a6c7d;
  line-height: 1.6;
  margin: 0;
}

.capability-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.capability-tag {
  background: #e8f4fd;
  color: #2980b9;
  padding: 0.3rem 0.8rem;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 500;
}

.task-form {
  margin-bottom: 2rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #ecf0f1;
  border-radius: 10px;
  font-size: 1rem;
  outline: none;
  transition: border-color 0.3s ease;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  border-color: #667eea;
}

.input-section {
  border-top: 1px solid #ecf0f1;
  padding-top: 1.5rem;
  margin-top: 1.5rem;
}

.input-section h4 {
  margin-bottom: 1rem;
  color: #2c3e50;
}

.input-types {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.input-type-tag {
  background: #d4edda;
  color: #155724;
  padding: 0.3rem 0.8rem;
  border-radius: 15px;
  font-size: 0.85rem;
  font-weight: 500;
}

.file-upload {
  border: 2px dashed #bdc3c7;
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
  transition: border-color 0.3s ease;
}

.file-upload:hover {
  border-color: #667eea;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 8px;
  margin-top: 0.5rem;
}

.remove-file {
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: auto;
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 0.5rem;
}

.checkbox-label {
  display: flex !important;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  font-weight: normal !important;
}

.parameter-inputs,
.requirement-inputs {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.param-row,
.req-row {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.param-row label,
.req-row label {
  font-size: 0.9rem;
  color: #7f8c8d;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #ecf0f1;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  background: #f8f9fa;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #667eea;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #5a6fd8;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.btn-secondary {
  background: #ecf0f1;
  color: #2c3e50;
}

.btn-secondary:hover {
  background: #d5dbdb;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-overlay {
    padding: 1rem;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .parameter-inputs,
  .requirement-inputs {
    grid-template-columns: 1fr;
  }
  
  .checkbox-group {
    grid-template-columns: 1fr;
  }
}
</style>