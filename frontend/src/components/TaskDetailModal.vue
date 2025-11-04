<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <h3>
          <i class="fas fa-info-circle"></i>
          任务详情
        </h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <div v-if="task" class="task-detail">
          <!-- 基本信息 -->
          <div class="detail-section">
            <h4>
              <i class="fas fa-file-alt"></i>
              基本信息
            </h4>
            <div class="info-grid">
              <div class="info-item">
                <label>任务标题：</label>
                <span>{{ task.title }}</span>
              </div>
              <div class="info-item">
                <label>智能体：</label>
                <span>{{ task.agent_name }}</span>
              </div>
              <div class="info-item">
                <label>状态：</label>
                <span :class="['status-badge', task.status]">
                  <i :class="getStatusIcon(task.status)"></i>
                  {{ getStatusText(task.status) }}
                </span>
              </div>
              <div class="info-item">
                <label>创建时间：</label>
                <span>{{ formatDateTime(task.created_at) }}</span>
              </div>
              <div v-if="task.started_at" class="info-item">
                <label>开始时间：</label>
                <span>{{ formatDateTime(task.started_at) }}</span>
              </div>
              <div v-if="task.completed_at" class="info-item">
                <label>完成时间：</label>
                <span>{{ formatDateTime(task.completed_at) }}</span>
              </div>
              <div v-if="task.execution_time" class="info-item">
                <label>执行时长：</label>
                <span>{{ formatDuration(task.execution_time) }}</span>
              </div>
            </div>
            
            <div v-if="task.description" class="description">
              <label>任务描述：</label>
              <p>{{ task.description }}</p>
            </div>
          </div>

          <!-- 进度信息 -->
          <div v-if="task.status === 'running'" class="detail-section">
            <h4>
              <i class="fas fa-chart-line"></i>
              执行进度
            </h4>
            <div class="progress-info">
              <div class="progress-label">
                <span>当前进度</span>
                <span>{{ task.progress.toFixed(1) }}%</span>
              </div>
              <div class="progress-bar">
                <div 
                  class="progress-fill"
                  :style="{ width: `${task.progress}%` }"
                ></div>
              </div>
            </div>
          </div>

          <!-- 输入数据 -->
          <div class="detail-section">
            <h4>
              <i class="fas fa-download"></i>
              输入数据
            </h4>
            <div class="data-viewer">
              <pre>{{ JSON.stringify(task.input_data, null, 2) }}</pre>
            </div>
          </div>

          <!-- 输出结果 -->
          <div v-if="task.output_data" class="detail-section">
            <h4>
              <i class="fas fa-upload"></i>
              执行结果
            </h4>
            <div class="data-viewer result-viewer">
              <pre>{{ JSON.stringify(task.output_data, null, 2) }}</pre>
            </div>
          </div>

          <!-- 错误信息 -->
          <div v-if="task.status === 'failed'" class="detail-section">
            <h4>
              <i class="fas fa-exclamation-triangle"></i>
              错误信息
            </h4>
            <div class="error-info">
              <div v-if="task.error_message" class="error-message">
                <label>错误消息：</label>
                <p>{{ task.error_message }}</p>
              </div>
              <div v-if="task.error_traceback" class="error-traceback">
                <label>错误堆栈：</label>
                <pre>{{ task.error_traceback }}</pre>
              </div>
            </div>
          </div>

          <!-- 执行步骤 -->
          <div v-if="executions.length > 0" class="detail-section">
            <h4>
              <i class="fas fa-list-ol"></i>
              执行步骤
              <button 
                class="btn-refresh"
                @click="fetchExecutions"
                title="刷新执行步骤"
              >
                <i class="fas fa-sync"></i>
              </button>
            </h4>
            <div class="execution-list">
              <div 
                v-for="execution in executions"
                :key="execution.id"
                class="execution-item"
              >
                <div class="execution-header">
                  <div class="step-info">
                    <span class="step-number">{{ execution.step_order }}</span>
                    <span class="step-name">{{ execution.step_name }}</span>
                  </div>
                  <span :class="['step-status', execution.status]">
                    {{ getStatusText(execution.status) }}
                  </span>
                </div>
                
                <div v-if="execution.logs" class="execution-logs">
                  <p>{{ execution.logs }}</p>
                </div>
                
                <div class="execution-time">
                  <span>开始：{{ formatDateTime(execution.started_at) }}</span>
                  <span v-if="execution.completed_at">
                    完成：{{ formatDateTime(execution.completed_at) }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button 
          v-if="task && ['pending', 'running'].includes(task.status)"
          class="btn btn-warning"
          @click="cancelTask"
        >
          <i class="fas fa-stop"></i>
          取消任务
        </button>
        
        <button 
          v-if="task && task.status === 'failed'"
          class="btn btn-danger"
          @click="retryTask"
        >
          <i class="fas fa-redo"></i>
          重试任务
        </button>
        
        <button class="btn btn-secondary" @click="$emit('close')">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import apiClient from '@/utils/api'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'task-updated'])

// 响应式数据
const executions = ref([])
const loading = ref(false)

// 方法
const fetchExecutions = async () => {
  if (!props.task?.id) return
  
  try {
    const response = await apiClient.get(`/smart-agent/tasks/${props.task.id}/executions/`)
    executions.value = response.data
  } catch (error) {
    console.error('获取执行步骤失败:', error)
  }
}

const cancelTask = async () => {
  if (!confirm('确定要取消这个任务吗？')) return
  
  try {
    await apiClient.post(`/smart-agent/tasks/${props.task.id}/cancel/`)
    emit('task-updated')
    emit('close')
  } catch (error) {
    console.error('取消任务失败:', error)
  }
}

const retryTask = async () => {
  if (!confirm('确定要重试这个任务吗？')) return
  
  try {
    const payload = {
      title: `重试 - ${props.task.title}`,
      description: props.task.description,
      input_data: props.task.input_data
    }
    
    const response = await apiClient.post(`/smart-agent/agents/${props.task.agent}/execute/`, payload)
    emit('task-updated')
    emit('close')
  } catch (error) {
    console.error('重试任务失败:', error)
  }
}

// 辅助函数
const getStatusIcon = (status) => {
  const iconMap = {
    pending: 'fas fa-clock',
    running: 'fas fa-spinner fa-spin',
    completed: 'fas fa-check-circle',
    failed: 'fas fa-times-circle',
    cancelled: 'fas fa-ban'
  }
  return iconMap[status] || 'fas fa-question-circle'
}

const getStatusText = (status) => {
  const statusMap = {
    pending: '等待中',
    running: '执行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return statusMap[status] || status
}

const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

// 监听任务变化
watch(() => props.task, (newTask) => {
  if (newTask?.id) {
    fetchExecutions()
  }
}, { immediate: true })

// 如果任务正在执行，定时刷新
let refreshInterval = null

onMounted(() => {
  if (props.task?.status === 'running') {
    refreshInterval = setInterval(() => {
      fetchExecutions()
    }, 3000) // 每3秒刷新一次
  }
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
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
  max-width: 800px;
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

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h4 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

.btn-refresh {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  padding: 0.25rem;
  border-radius: 4px;
  margin-left: auto;
  transition: background 0.3s ease;
}

.btn-refresh:hover {
  background: rgba(102, 126, 234, 0.1);
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.info-item label {
  font-weight: 600;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.description {
  margin-top: 1rem;
}

.description label {
  font-weight: 600;
  color: #7f8c8d;
  font-size: 0.9rem;
  display: block;
  margin-bottom: 0.5rem;
}

.description p {
  margin: 0;
  color: #2c3e50;
  line-height: 1.5;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  width: fit-content;
}

.status-badge.pending {
  background: #fff3cd;
  color: #856404;
}

.status-badge.running {
  background: #d1ecf1;
  color: #0c5460;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.progress-info {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1rem;
}

.progress-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-weight: 600;
  color: #2c3e50;
}

.progress-bar {
  height: 12px;
  background: #ecf0f1;
  border-radius: 6px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.5s ease;
}

.data-viewer {
  background: #2c3e50;
  color: #ecf0f1;
  border-radius: 10px;
  padding: 1rem;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9rem;
  max-height: 300px;
  overflow-y: auto;
}

.result-viewer {
  background: #27ae60;
  color: white;
}

.data-viewer pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.4;
}

.error-info {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
  border-radius: 10px;
  padding: 1rem;
}

.error-message,
.error-traceback {
  margin-bottom: 1rem;
}

.error-message:last-child,
.error-traceback:last-child {
  margin-bottom: 0;
}

.error-message label,
.error-traceback label {
  font-weight: 600;
  color: #721c24;
  display: block;
  margin-bottom: 0.5rem;
}

.error-message p {
  margin: 0;
  color: #721c24;
  line-height: 1.4;
}

.error-traceback pre {
  margin: 0;
  color: #721c24;
  background: rgba(114, 28, 36, 0.1);
  padding: 0.5rem;
  border-radius: 5px;
  font-size: 0.8rem;
  line-height: 1.3;
  overflow-x: auto;
}

.execution-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.execution-item {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1rem;
  border-left: 4px solid #667eea;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.step-number {
  background: #667eea;
  color: white;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  font-weight: 600;
}

.step-name {
  font-weight: 600;
  color: #2c3e50;
}

.step-status {
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
}

.step-status.completed {
  background: #d4edda;
  color: #155724;
}

.step-status.running {
  background: #d1ecf1;
  color: #0c5460;
}

.step-status.failed {
  background: #f8d7da;
  color: #721c24;
}

.execution-logs {
  margin: 0.5rem 0;
}

.execution-logs p {
  margin: 0;
  color: #7f8c8d;
  line-height: 1.4;
  font-size: 0.9rem;
}

.execution-time {
  display: flex;
  gap: 1rem;
  font-size: 0.8rem;
  color: #95a5a6;
  margin-top: 0.5rem;
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

.btn-warning {
  background: #f39c12;
  color: white;
}

.btn-danger {
  background: #e74c3c;
  color: white;
}

.btn-secondary {
  background: #95a5a6;
  color: white;
}

.btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .modal-overlay {
    padding: 1rem;
  }
  
  .modal-body {
    padding: 1rem;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
  
  .execution-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
  
  .execution-time {
    flex-direction: column;
    gap: 0.25rem;
  }
}
</style>