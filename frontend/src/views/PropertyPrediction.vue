<template>
  <div class="property-prediction-page-wrapper">
    <NavigationSidebar />

    <div class="property-prediction-container">
      <div class="page-content">
        <div class="page-header">
          <div class="back-navigation">
            <button class="back-btn" @click="goBack">
              <i class="fas fa-arrow-left"></i>
              返回
            </button>
          </div>
          <h1 class="page-title"><i class="fas fa-chart-area"></i> 性质预测智能体</h1>
          <p class="page-description">输入材料与工艺参数，快速获得关键性能预测与候选方案排序。</p>
        </div>

        <div class="layout-grid">
          <section class="panel input-panel">
            <h3>预测输入</h3>
            <div class="form-grid">
              <label>
                材料体系
                <input v-model="form.materialSystem" placeholder="如：硅碳负极" />
              </label>
              <label>
                目标性质
                <input v-model="form.targetProperty" placeholder="如：首次库伦效率" />
              </label>
              <label>
                工作温度 (℃)
                <input v-model="form.temperature" type="number" placeholder="25" />
              </label>
              <label>
                粒径 D50 (μm)
                <input v-model="form.particleSize" type="number" placeholder="10" />
              </label>
              <label>
                掺杂策略
                <input v-model="form.doping" placeholder="B/N 协同掺杂" />
              </label>
              <label>
                备注
                <input v-model="form.note" placeholder="关注循环寿命 > 1000 次" />
              </label>
            </div>

            <div class="actions">
              <button class="btn btn-secondary" @click="loadDemo">载入 Demo</button>
              <button class="btn btn-primary" @click="runPrediction" :disabled="loading">
                {{ loading ? '预测中...' : '开始预测' }}
              </button>
            </div>
          </section>

          <section class="panel result-panel">
            <h3>预测结果</h3>
            <div v-if="!hasResult" class="empty">先点击“载入 Demo”或“开始预测”查看结果。</div>
            <div v-else>
              <div class="kpi-grid">
                <div class="kpi-item">
                  <span>目标性质预测值</span>
                  <strong>{{ result.predictedValue }}</strong>
                </div>
                <div class="kpi-item">
                  <span>置信区间</span>
                  <strong>{{ result.confidence }}</strong>
                </div>
                <div class="kpi-item">
                  <span>模型评分</span>
                  <strong>{{ result.modelScore }}</strong>
                </div>
              </div>

              <h4>候选方案排序</h4>
              <table class="result-table">
                <thead>
                  <tr>
                    <th>方案</th>
                    <th>预测值</th>
                    <th>风险</th>
                    <th>建议</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="item in result.candidates" :key="item.name">
                    <td>{{ item.name }}</td>
                    <td>{{ item.value }}</td>
                    <td>{{ item.risk }}</td>
                    <td>{{ item.suggestion }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()
const loading = ref(false)
const form = reactive({
  materialSystem: '',
  targetProperty: '',
  temperature: 25,
  particleSize: 10,
  doping: '',
  note: ''
})

const result = ref({
  predictedValue: '',
  confidence: '',
  modelScore: '',
  candidates: []
})

const hasResult = computed(() => Boolean(result.value.predictedValue))

const loadDemo = () => {
  form.materialSystem = '硅碳负极'
  form.targetProperty = '首次库伦效率'
  form.temperature = 25
  form.particleSize = 9.8
  form.doping = 'B/N 协同掺杂'
  form.note = '循环寿命目标 > 1000 次'

  result.value = {
    predictedValue: '92.4%'
    ,confidence: '90.8% ~ 93.6%'
    ,modelScore: 'R² = 0.89'
    ,candidates: [
      { name: '方案 A：石墨 72% + Si 12%', value: '92.4%', risk: '低', suggestion: '优先中试' },
      { name: '方案 B：石墨 68% + Si 16%', value: '93.1%', risk: '中', suggestion: '关注膨胀管理' },
      { name: '方案 C：石墨 75% + Si 10%', value: '91.6%', risk: '低', suggestion: '成本优先可选' }
    ]
  }
}

const runPrediction = async () => {
  loading.value = true
  try {
    await new Promise((resolve) => setTimeout(resolve, 500))
    if (!hasResult.value) {
      loadDemo()
    }
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push({ name: 'SmartAgents' })
}
</script>

<style scoped>
.property-prediction-page-wrapper { display: flex; min-height: 100dvh; background: #f6f8fb; }
.property-prediction-container { flex: 1; padding: 20px; box-sizing: border-box; }
.page-content { width: 100%; }
.page-header { background: #fff; border: 1px solid #eef3fb; border-radius: 12px; padding: 16px 18px; margin-bottom: 16px; }
.back-navigation { margin-bottom: 10px; }
.back-btn { border: 1px solid #e2e8f0; background: #f8fafc; color: #334155; border-radius: 8px; padding: 6px 10px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.back-btn:hover { background: #eef2ff; border-color: #c7d2fe; }
.page-title { margin: 0; font-size: 1.45rem; display: flex; align-items: center; gap: 10px; color: #0f172a; }
.page-description { margin: 8px 0 0; color: #64748b; }
.layout-grid { display: grid; grid-template-columns: 1fr 1.2fr; gap: 16px; }
.panel { background: #fff; border: 1px solid #eef3fb; border-radius: 12px; padding: 14px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
label { display: flex; flex-direction: column; gap: 6px; color: #334155; font-size: 0.88rem; }
input { border: 1px solid #dbe7ff; border-radius: 8px; padding: 8px 10px; }
.actions { margin-top: 12px; display: flex; gap: 8px; }
.btn { border: none; border-radius: 8px; padding: 8px 12px; cursor: pointer; font-weight: 700; }
.btn-primary { background: #4f46e5; color: #fff; }
.btn-secondary { background: #eef2ff; color: #3730a3; }
.kpi-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 12px; }
.kpi-item { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; display: flex; flex-direction: column; gap: 6px; }
.kpi-item strong { color: #1e293b; }
.result-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.result-table th, .result-table td { border-bottom: 1px solid #eef2f7; padding: 8px 6px; text-align: left; }
.empty { color: #94a3b8; }
@media (max-width: 960px) {
  .layout-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
  .kpi-grid { grid-template-columns: 1fr; }
}
</style>
