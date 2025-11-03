<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-container">
      <div class="modal-header">
        <h3>
          <i class="fas fa-chart-bar"></i>
          任务执行结果
        </h3>
        <button class="close-btn" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>

      <div class="modal-body">
        <div v-if="task && task.output_data" class="result-container">
          <!-- 结果概览 -->
          <div class="result-overview">
            <div class="overview-item">
              <i class="fas fa-check-circle success"></i>
              <div>
                <h4>执行成功</h4>
                <p>{{ formatDateTime(task.completed_at) }}</p>
              </div>
            </div>
            
            <div class="overview-item">
              <i class="fas fa-clock"></i>
              <div>
                <h4>执行时长</h4>
                <p>{{ formatDuration(task.execution_time) }}</p>
              </div>
            </div>
            
            <div class="overview-item">
              <i class="fas fa-robot"></i>
              <div>
                <h4>智能体</h4>
                <p>{{ task.agent_name }}</p>
              </div>
            </div>
          </div>

          <!-- 根据结果类型展示不同的内容 -->
          <div class="result-content">
            <!-- 数据分析结果 -->
            <div v-if="isDataAnalysisResult" class="analysis-results">
              <div class="result-section">
                <h4>
                  <i class="fas fa-chart-line"></i>
                  关联分析结果
                </h4>
                <div class="correlation-grid">
                  <div v-for="corr in task.output_data.correlation_matrix" :key="corr[0] + corr[1]" class="correlation-item">
                    <div class="correlation-labels">
                      <span>{{ corr[0] }}</span>
                      <i class="fas fa-arrow-right"></i>
                      <span>{{ corr[1] }}</span>
                    </div>
                    <div class="correlation-value">
                      <div class="correlation-bar">
                        <div 
                          class="correlation-fill"
                          :style="{ width: `${corr[2] * 100}%` }"
                        ></div>
                      </div>
                      <span>{{ (corr[2] * 100).toFixed(1) }}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="result-section">
                <h4>
                  <i class="fas fa-lightbulb"></i>
                  优化建议
                </h4>
                <ul class="recommendations">
                  <li v-for="rec in task.output_data.recommendations" :key="rec">
                    {{ rec }}
                  </li>
                </ul>
              </div>

              <div class="analysis-details">
                <div class="detail-card">
                  <h5>成分分析</h5>
                  <div v-if="task.output_data.composition_analysis" class="analysis-data">
                    <p><strong>主要元素：</strong>{{ task.output_data.composition_analysis.main_elements?.join(', ') }}</p>
                    <p><strong>微量元素：</strong>{{ task.output_data.composition_analysis.trace_elements?.join(', ') }}</p>
                    <p><strong>相组成：</strong>{{ task.output_data.composition_analysis.phase_composition }}</p>
                  </div>
                </div>

                <div class="detail-card">
                  <h5>工艺参数</h5>
                  <div v-if="task.output_data.process_parameters" class="analysis-data">
                    <p v-for="(value, key) in task.output_data.process_parameters" :key="key">
                      <strong>{{ getParameterName(key) }}：</strong>{{ value }}
                    </p>
                  </div>
                </div>

                <div class="detail-card">
                  <h5>性能指标</h5>
                  <div v-if="task.output_data.performance_properties" class="analysis-data">
                    <p v-for="(value, key) in task.output_data.performance_properties" :key="key">
                      <strong>{{ getPropertyName(key) }}：</strong>{{ value }}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <!-- 性质预测结果 -->
            <div v-else-if="isPropertyPredictionResult" class="prediction-results">
              <div v-if="task.output_data.mechanical_properties" class="result-section">
                <h4>
                  <i class="fas fa-wrench"></i>
                  力学性能预测
                </h4>
                <div class="property-grid">
                  <div v-for="(prop, key) in task.output_data.mechanical_properties" :key="key" class="property-card">
                    <h5>{{ getPropertyName(key) }}</h5>
                    <div class="property-value">
                      <span class="value">{{ prop.value }}</span>
                      <span class="unit">{{ prop.unit }}</span>
                    </div>
                    <div class="confidence-info">
                      <span>置信区间：{{ prop.confidence_interval?.join(' - ') }} {{ prop.unit }}</span>
                      <span>置信度：{{ (prop.confidence_level * 100).toFixed(0) }}%</span>
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="task.output_data.optimization_suggestions" class="result-section">
                <h4>
                  <i class="fas fa-lightbulb"></i>
                  优化建议
                </h4>
                <ul class="suggestions">
                  <li v-for="suggestion in task.output_data.optimization_suggestions" :key="suggestion">
                    {{ suggestion }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 工艺优化结果 -->
            <div v-else-if="isProcessOptimizationResult" class="optimization-results">
              <div class="result-section">
                <h4>
                  <i class="fas fa-cogs"></i>
                  优化参数对比
                </h4>
                <div class="parameter-comparison">
                  <div v-for="(param, key) in task.output_data.optimized_parameters" :key="key" class="param-compare">
                    <h5>{{ getParameterName(key) }}</h5>
                    <div class="compare-values">
                      <div class="value-item current">
                        <label>当前值</label>
                        <span>{{ param.current }} {{ param.unit }}</span>
                      </div>
                      <i class="fas fa-arrow-right"></i>
                      <div class="value-item optimized">
                        <label>优化值</label>
                        <span>{{ param.optimized }} {{ param.unit }}</span>
                      </div>
                      <div class="improvement">
                        <span :class="getImprovementClass(param.improvement)">
                          {{ param.improvement }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="result-section">
                <h4>
                  <i class="fas fa-chart-pie"></i>
                  预期改善效果
                </h4>
                <div class="improvement-grid">
                  <div v-for="(value, key) in task.output_data.expected_improvements" :key="key" class="improvement-card">
                    <h5>{{ getImprovementName(key) }}</h5>
                    <span class="improvement-value">{{ value }}</span>
                  </div>
                </div>
              </div>

              <div class="result-section">
                <h4>
                  <i class="fas fa-list-ol"></i>
                  实施计划
                </h4>
                <div class="implementation-plan">
                  <div v-for="(phase, index) in task.output_data.implementation_plan" :key="index" class="phase-item">
                    <span class="phase-number">{{ index + 1 }}</span>
                    <span class="phase-text">{{ phase }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 决策支持结果 -->
            <div v-else-if="isDecisionSupportResult" class="decision-results">
              <div class="result-section">
                <h4>
                  <i class="fas fa-medal"></i>
                  推荐材料排行
                </h4>
                <div class="material-ranking">
                  <div v-for="material in task.output_data.recommended_materials" :key="material.rank" class="material-card">
                    <div class="material-header">
                      <span class="rank">#{{ material.rank }}</span>
                      <h5>{{ material.material }}</h5>
                      <span class="match-score">匹配度：{{ (material.match_score * 100).toFixed(1) }}%</span>
                    </div>
                    
                    <div class="material-details">
                      <div class="advantages">
                        <strong>优点：</strong>
                        <span>{{ material.advantages.join('、') }}</span>
                      </div>
                      <div class="disadvantages">
                        <strong>缺点：</strong>
                        <span>{{ material.disadvantages.join('、') }}</span>
                      </div>
                    </div>
                    
                    <div class="material-scores">
                      <div class="score-item">
                        <span>成本指数</span>
                        <div class="score-bar">
                          <div class="score-fill" :style="{ width: `${material.cost_index * 10}%` }"></div>
                        </div>
                        <span>{{ material.cost_index }}/10</span>
                      </div>
                      <div class="score-item">
                        <span>性能指数</span>
                        <div class="score-bar">
                          <div class="score-fill" :style="{ width: `${material.performance_index * 10}%` }"></div>
                        </div>
                        <span>{{ material.performance_index }}/10</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 知识抽取结果 -->
            <div v-else-if="isKnowledgeExtractionResult" class="extraction-results">
              <div v-if="task.output_data.extracted_materials" class="result-section">
                <h4>
                  <i class="fas fa-cube"></i>
                  识别的材料
                </h4>
                <div class="material-list">
                  <div v-for="material in task.output_data.extracted_materials" :key="material.name" class="material-item">
                    <div class="material-info">
                      <h5>{{ material.name }}</h5>
                      <p><strong>成分：</strong>{{ material.composition }}</p>
                      <p><strong>应用：</strong>{{ material.applications.join('、') }}</p>
                    </div>
                    <div class="confidence-badge">
                      {{ (material.confidence * 100).toFixed(0) }}%
                    </div>
                  </div>
                </div>
              </div>

              <div v-if="task.output_data.key_findings" class="result-section">
                <h4>
                  <i class="fas fa-key"></i>
                  关键发现
                </h4>
                <ul class="key-findings">
                  <li v-for="finding in task.output_data.key_findings" :key="finding">
                    {{ finding }}
                  </li>
                </ul>
              </div>
            </div>

            <!-- 通用JSON显示 -->
            <div v-else class="generic-result">
              <div class="result-section">
                <h4>
                  <i class="fas fa-code"></i>
                  执行结果
                </h4>
                <div class="json-viewer">
                  <pre>{{ JSON.stringify(task.output_data, null, 2) }}</pre>
                </div>
              </div>
            </div>
          </div>

          <!-- 导出选项 -->
          <div class="export-section">
            <h4>
              <i class="fas fa-download"></i>
              导出结果
            </h4>
            <div class="export-buttons">
              <button class="btn btn-primary" @click="exportAsJSON">
                <i class="fas fa-file-code"></i>
                JSON格式
              </button>
              <button class="btn btn-success" @click="exportAsExcel">
                <i class="fas fa-file-excel"></i>
                Excel表格
              </button>
              <button class="btn btn-info" @click="exportAsPDF">
                <i class="fas fa-file-pdf"></i>
                PDF报告
              </button>
            </div>
          </div>
        </div>
        
        <div v-else class="no-result">
          <i class="fas fa-question-circle"></i>
          <h4>暂无执行结果</h4>
          <p>该任务还未完成或没有生成结果数据</p>
        </div>
      </div>

      <div class="modal-footer">
        <button class="btn btn-secondary" @click="$emit('close')">
          关闭
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

// 计算属性 - 判断结果类型
const isDataAnalysisResult = computed(() => {
  return props.task?.output_data?.analysis_type === '四级关联数据链分析'
})

const isPropertyPredictionResult = computed(() => {
  return props.task?.output_data?.prediction_type === '材料性质预测'
})

const isProcessOptimizationResult = computed(() => {
  return props.task?.output_data?.optimization_type === '生产工艺优化'
})

const isDecisionSupportResult = computed(() => {
  return props.task?.output_data?.decision_type === '材料选择决策支持'
})

const isKnowledgeExtractionResult = computed(() => {
  return props.task?.output_data?.extraction_type === '科技文献知识抽取'
})

// 方法
const formatDateTime = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '-'
  if (seconds < 60) return `${seconds.toFixed(1)}s`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${(seconds % 60).toFixed(0)}s`
  return `${Math.floor(seconds / 3600)}h ${Math.floor((seconds % 3600) / 60)}m`
}

const getParameterName = (key) => {
  const nameMap = {
    temperature: '温度',
    pressure: '压力',
    duration: '时间',
    cooling_rate: '冷却速率'
  }
  return nameMap[key] || key
}

const getPropertyName = (key) => {
  const nameMap = {
    tensile_strength: '拉伸强度',
    yield_strength: '屈服强度',
    elongation: '延伸率',
    hardness: '硬度',
    impact_toughness: '冲击韧性'
  }
  return nameMap[key] || key
}

const getImprovementName = (key) => {
  const nameMap = {
    quality_increase: '质量提升',
    cost_reduction: '成本降低',
    energy_savings: '能耗节约',
    production_efficiency: '生产效率'
  }
  return nameMap[key] || key
}

const getImprovementClass = (improvement) => {
  if (improvement.includes('+')) return 'positive'
  if (improvement.includes('-')) return 'negative'
  return 'neutral'
}

// 导出功能
const exportAsJSON = () => {
  const data = JSON.stringify(props.task.output_data, null, 2)
  const blob = new Blob([data], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.task.title}_结果.json`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const exportAsExcel = () => {
  // 这里可以实现Excel导出功能
  console.log('导出Excel功能待实现')
}

const exportAsPDF = () => {
  // 这里可以实现PDF导出功能
  console.log('导出PDF功能待实现')
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
  max-width: 1000px;
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
  background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
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

.result-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  border-radius: 15px;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.overview-item i {
  font-size: 2rem;
  color: #667eea;
}

.overview-item i.success {
  color: #27ae60;
}

.overview-item h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 1rem;
}

.overview-item p {
  margin: 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.result-section {
  margin-bottom: 2rem;
  background: white;
  border-radius: 15px;
  padding: 1.5rem;
  border: 1px solid #ecf0f1;
}

.result-section h4 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem 0;
  color: #2c3e50;
  font-size: 1.1rem;
}

/* 关联分析结果样式 */
.correlation-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.correlation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 10px;
}

.correlation-labels {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
}

.correlation-value {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 200px;
}

.correlation-bar {
  flex: 1;
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  overflow: hidden;
}

.correlation-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.5s ease;
}

/* 分析详情样式 */
.analysis-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.detail-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1rem;
}

.detail-card h5 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.analysis-data p {
  margin: 0.25rem 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* 性质预测样式 */
.property-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.property-card {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-radius: 15px;
  padding: 1.5rem;
  text-align: center;
}

.property-card h5 {
  margin: 0 0 1rem 0;
  font-size: 0.9rem;
  opacity: 0.9;
}

.property-value {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.property-value .value {
  font-size: 2rem;
  font-weight: 700;
}

.property-value .unit {
  font-size: 0.9rem;
  opacity: 0.8;
}

.confidence-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  font-size: 0.8rem;
  opacity: 0.9;
}

/* 工艺优化样式 */
.parameter-comparison {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.param-compare h5 {
  margin: 0 0 0.5rem 0;
  color: #2c3e50;
}

.compare-values {
  display: grid;
  grid-template-columns: 1fr auto 1fr auto;
  gap: 1rem;
  align-items: center;
}

.value-item {
  text-align: center;
  padding: 1rem;
  border-radius: 10px;
}

.value-item.current {
  background: #f8d7da;
  color: #721c24;
}

.value-item.optimized {
  background: #d4edda;
  color: #155724;
}

.value-item label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.improvement {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
}

.improvement.positive {
  background: #d4edda;
  color: #155724;
}

.improvement.negative {
  background: #fff3cd;
  color: #856404;
}

.improvement-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.improvement-card {
  background: #f8f9fa;
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
}

.improvement-card h5 {
  margin: 0 0 0.5rem 0;
  color: #7f8c8d;
  font-size: 0.9rem;
}

.improvement-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #27ae60;
}

.implementation-plan {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.phase-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 10px;
}

.phase-number {
  background: #667eea;
  color: white;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

/* 决策支持样式 */
.material-ranking {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.material-card {
  background: #f8f9fa;
  border-radius: 15px;
  padding: 1.5rem;
  border-left: 4px solid #667eea;
}

.material-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.rank {
  background: #667eea;
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 600;
}

.material-header h5 {
  flex: 1;
  margin: 0;
  color: #2c3e50;
}

.match-score {
  background: #d4edda;
  color: #155724;
  padding: 0.25rem 0.75rem;
  border-radius: 15px;
  font-size: 0.8rem;
  font-weight: 600;
}

.material-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.material-scores {
  display: flex;
  gap: 2rem;
}

.score-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.9rem;
}

.score-bar {
  flex: 1;
  height: 6px;
  background: #ecf0f1;
  border-radius: 3px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: #667eea;
}

/* 通用样式 */
.recommendations,
.suggestions,
.key-findings {
  margin: 0;
  padding-left: 1.5rem;
}

.recommendations li,
.suggestions li,
.key-findings li {
  margin-bottom: 0.5rem;
  color: #2c3e50;
  line-height: 1.5;
}

.json-viewer {
  background: #2c3e50;
  color: #ecf0f1;
  border-radius: 10px;
  padding: 1rem;
  overflow-x: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9rem;
  max-height: 400px;
  overflow-y: auto;
}

.json-viewer pre {
  margin: 0;
  white-space: pre-wrap;
  line-height: 1.4;
}

.export-section {
  margin-top: 2rem;
  padding: 1.5rem;
  background: #f8f9fa;
  border-radius: 15px;
}

.export-section h4 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 1rem 0;
  color: #2c3e50;
}

.export-buttons {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.no-result {
  text-align: center;
  padding: 4rem 2rem;
  color: #7f8c8d;
}

.no-result i {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.modal-footer {
  padding: 1.5rem 2rem;
  border-top: 1px solid #ecf0f1;
  display: flex;
  justify-content: flex-end;
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

.btn-success {
  background: #27ae60;
  color: white;
}

.btn-info {
  background: #3498db;
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
  
  .result-overview {
    grid-template-columns: 1fr;
  }
  
  .property-grid,
  .improvement-grid {
    grid-template-columns: 1fr;
  }
  
  .compare-values {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
  
  .material-scores {
    flex-direction: column;
    gap: 1rem;
  }
  
  .export-buttons {
    flex-direction: column;
  }
}
</style>