<template>
  <div class="decision-support-page-wrapper">
    <NavigationSidebar />

    <div class="decision-support-container">
      <div class="page-content">
        <div class="page-header">
          <div class="back-navigation">
            <button class="back-btn" @click="goBack">
              <i class="fas fa-arrow-left"></i>
              返回
            </button>
          </div>
          <h1 class="page-title"><i class="fas fa-compass"></i> 决策支持智能体</h1>
          <p class="page-description">根据性能、成本、风险、周期等维度进行多目标评分并输出建议路线。</p>
        </div>

        <div class="layout-grid">
          <section class="panel input-panel">
            <h3>决策输入</h3>
            <div class="form-grid">
              <label>
                任务目标
                <input v-model="form.goal" placeholder="如：选择下一阶段中试路线" />
              </label>
              <label>
                权重-性能 (0~1)
                <input v-model.number="form.weightPerformance" type="number" min="0" max="1" step="0.1" />
              </label>
              <label>
                权重-成本 (0~1)
                <input v-model.number="form.weightCost" type="number" min="0" max="1" step="0.1" />
              </label>
              <label>
                权重-风险 (0~1)
                <input v-model.number="form.weightRisk" type="number" min="0" max="1" step="0.1" />
              </label>
              <label>
                权重-交付周期 (0~1)
                <input v-model.number="form.weightSchedule" type="number" min="0" max="1" step="0.1" />
              </label>
              <label>
                关键约束
                <input v-model="form.constraints" placeholder="如：预算 < 900 元/kg" />
              </label>
            </div>

            <div class="actions">
              <button class="btn btn-secondary" @click="loadDemo">载入 Demo</button>
              <button class="btn btn-primary" @click="buildDecision" :disabled="loading">
                {{ loading ? '评估中...' : '生成决策建议' }}
              </button>
            </div>
          </section>

          <section class="panel result-panel">
            <h3>决策输出</h3>
            <div v-if="!hasResult" class="empty">先点击“载入 Demo”或“生成决策建议”。</div>
            <div v-else>
              <div class="summary-box">
                <h4>推荐结论</h4>
                <p>{{ result.summary }}</p>
              </div>

              <h4>方案评分排序</h4>
              <table class="result-table">
                <thead>
                  <tr>
                    <th>方案</th>
                    <th>总分</th>
                    <th>风险</th>
                    <th>下一步动作</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="row in result.ranking" :key="row.name">
                    <td>{{ row.name }}</td>
                    <td>{{ row.score }}</td>
                    <td>{{ row.risk }}</td>
                    <td>{{ row.next }}</td>
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
  goal: '',
  weightPerformance: 0.4,
  weightCost: 0.3,
  weightRisk: 0.2,
  weightSchedule: 0.1,
  constraints: ''
})

const result = ref({
  summary: '',
  ranking: []
})

const hasResult = computed(() => Boolean(result.value.summary))

const loadDemo = () => {
  form.goal = '选择下一阶段中试路线'
  form.weightPerformance = 0.45
  form.weightCost = 0.25
  form.weightRisk = 0.2
  form.weightSchedule = 0.1
  form.constraints = '预算 < 900 元/kg，优先 4 周内落地'

  result.value = {
    summary: '建议优先推进“方案 A（硅碳平衡路线）”，综合分最高且风险可控；“方案 B”作为性能冲刺备选。',
    ranking: [
      { name: '方案 A：硅碳平衡路线', score: '87.6', risk: '中低', next: '进入 30kg 级中试' },
      { name: '方案 B：高性能冲刺路线', score: '84.3', risk: '中高', next: '补做热稳定验证' },
      { name: '方案 C：成本优先路线', score: '80.1', risk: '低', next: '用于量产兜底' }
    ]
  }
}

const buildDecision = async () => {
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
.decision-support-page-wrapper { display: flex; min-height: 100dvh; background: #f6f8fb; }
.decision-support-container { flex: 1; padding: 20px; box-sizing: border-box; }
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
.summary-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; margin-bottom: 12px; }
.result-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.result-table th, .result-table td { border-bottom: 1px solid #eef2f7; padding: 8px 6px; text-align: left; }
.empty { color: #94a3b8; }
@media (max-width: 960px) {
  .layout-grid { grid-template-columns: 1fr; }
  .form-grid { grid-template-columns: 1fr; }
}
</style>
