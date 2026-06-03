<template>
  <div class="formula-generation-page-wrapper">
    <NavigationSidebar />
    <div class="process-optimization-container">
      <!-- 页面头部 -->
      <div class="page-header">
        <div class="header-main">
          <button @click="goBack" class="back-btn">
            <i class="fas fa-arrow-left"></i>
            返回
          </button>
          <div>
            <h1>配方生成智能体</h1>
            <p>根据输入参数生成材料配方建议</p>
          </div>
        </div>
        <div class="header-actions">
          <button type="button" class="action-btn secondary" @click="loadDemoFormula">载入 Demo 看板</button>
          <button type="button" class="action-btn ghost" @click="clearAll">清空结果</button>
        </div>
      </div>

    <!-- 输入表单 -->
    <div class="form-section">
      <div class="form-card">
        <h2>
          <i class="fas fa-edit"></i>
          输入参数
        </h2>
        
        <form @submit.prevent="submitForm">
          <div class="base-input-grid">
            <div class="form-group">
              <label for="product_performance_requirements">
                <i class="fas fa-chart-line"></i>
                产品性能要求
                <span class="required">*</span>
              </label>
              <textarea
                id="product_performance_requirements"
                v-model="formData.product_performance_requirements"
                placeholder="例如：高导电性、耐高温、循环寿命>1000次"
                rows="3"
                required
              ></textarea>
              <small class="field-hint">请描述产品的核心性能指标和要求</small>
            </div>

            <div class="form-group">
              <label for="target_application_scenario">
                <i class="fas fa-bullseye"></i>
                目标应用场景
                <span class="required">*</span>
              </label>
              <textarea
                id="target_application_scenario"
                v-model="formData.target_application_scenario"
                placeholder="例如：锂电池电解质材料，用于消费电子"
                rows="3"
                required
              ></textarea>
              <small class="field-hint">请说明产品的具体应用领域和使用场景</small>
            </div>

            <div class="form-group">
              <label for="cost_consideration">
                <i class="fas fa-dollar-sign"></i>
                成本考量
                <span class="required">*</span>
              </label>
              <textarea
                id="cost_consideration"
                v-model="formData.cost_consideration"
                placeholder="例如：单公斤成本控制在 200 元以内"
                rows="2"
                required
              ></textarea>
              <small class="field-hint">请明确成本预算和控制要求</small>
            </div>

            <div class="form-group">
              <label for="material_system">
                <i class="fas fa-layer-group"></i>
                材料体系
              </label>
              <select id="material_system" v-model="formData.material_system">
                <option value="">请选择</option>
                <option
                  v-for="system in materialSystemOptions"
                  :key="system.value"
                  :value="system.value"
                >
                  {{ system.label }}
                </option>
              </select>
              <small class="field-hint">选择体系后将自动切换专业参数模板</small>
            </div>
          </div>

          <div v-if="activeSystemTemplate.description" class="system-hint">
            <i class="fas fa-compass"></i>
            <span>{{ activeSystemTemplate.description }}</span>
          </div>

          <div class="form-grid" v-if="activeSystemTemplate.fields.length">
            <div class="form-group" v-for="field in activeSystemTemplate.fields" :key="field.key">
              <label :for="field.key">
                <i :class="field.icon"></i>
                {{ field.label }}
              </label>
              <input
                v-if="field.type !== 'select'"
                :id="field.key"
                v-model="formData[field.key]"
                type="text"
                :placeholder="field.placeholder"
              />
              <select
                v-else
                :id="field.key"
                v-model="formData[field.key]"
              >
                <option value="">请选择</option>
                <option v-for="option in field.options || []" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
              <small class="field-hint">{{ field.hint }}</small>
            </div>
          </div>

          <div class="form-group">
            <label for="environmental_requirements">
              <i class="fas fa-leaf"></i>
              环保要求
              <span class="required">*</span>
            </label>
            <textarea
              id="environmental_requirements"
              v-model="formData.environmental_requirements"
              placeholder="例如：符合 RoHS/REACH，无卤、低VOC 排放"
              rows="2"
              required
            ></textarea>
            <small class="field-hint">请说明环保标准和合规要求</small>
          </div>

          <div class="form-actions">
            <button 
              type="button" 
              class="btn btn-secondary"
              @click="resetForm"
              :disabled="loading"
            >
              <i class="fas fa-redo"></i>
              重置
            </button>
            <button 
              type="submit" 
              class="btn btn-primary"
              :disabled="loading"
            >
              <i class="fas fa-paper-plane" v-if="!loading"></i>
              <i class="fas fa-spinner fa-spin" v-else></i>
              {{ loading ? '分析中...' : '开始生成配方' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- 结果显示区域 -->
    <div v-if="showResult" class="result-section">
      <div class="result-card">
        <h2>
          <i class="fas fa-lightbulb"></i>
          优化建议
        </h2>
        
        <!-- 流式输出显示 -->
        <div v-if="streaming" class="streaming-output">
          <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <div class="stream-content" v-html="formatMarkdown(streamingAnswer)"></div>
        </div>

        <!-- 完整结果显示 -->
        <div v-else class="result-content">
          <div class="summary-kpi-grid">
            <div class="summary-kpi-card" v-for="item in formulaSummaryKpis" :key="item.label">
              <div class="summary-kpi-label">{{ item.label }}</div>
              <div class="summary-kpi-value">{{ item.value }}</div>
              <div class="summary-kpi-note">{{ item.note }}</div>
            </div>
          </div>

          <div class="result-text" v-html="formatMarkdown(result)"></div>

          <div class="strategy-matrix">
            <h3><i class="fas fa-border-all"></i> 配方策略矩阵</h3>
            <div class="table-wrap">
              <table class="matrix-table">
                <thead>
                  <tr>
                    <th>策略维度</th>
                    <th>性能优先</th>
                    <th>平衡优先</th>
                    <th>成本优先</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in strategyMatrixRows" :key="idx">
                    <td>{{ row.dimension }}</td>
                    <td>{{ row.performance }}</td>
                    <td>{{ row.balanced }}</td>
                    <td>{{ row.cost }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
          
          <div class="result-meta">
            <div class="meta-item">
              <i class="fas fa-clock"></i>
              <span>{{ formatDate(resultTime) }}</span>
            </div>
            <div class="meta-item">
              <i class="fas fa-comment"></i>
              <span>会话 ID: {{ conversationId }}</span>
            </div>
            <div class="meta-item validity-select-item" :class="{ disabled: !currentHistoryId }">
              <i class="fas fa-clipboard-check"></i>
              <label for="formula-validity-status">是否有效配方</label>
              <select
                id="formula-validity-status"
                v-model="currentValidityStatus"
                :disabled="!currentHistoryId"
              >
                <option value="pending">待确认</option>
                <option value="valid">有效</option>
                <option value="invalid">无效</option>
              </select>
            </div>
          </div>

          <div class="result-actions">
            <button 
              class="btn btn-outline"
              @click="copyResult"
            >
              <i class="fas fa-copy"></i>
              复制结果
            </button>
            <button 
              class="btn btn-outline"
              @click="downloadResult"
            >
              <i class="fas fa-download"></i>
              下载报告
            </button>
            <button 
              class="btn btn-primary"
              @click="newOptimization"
            >
              <i class="fas fa-plus"></i>
              新建优化
            </button>
          </div>

          <div v-if="formulaDetails.materials.length" class="detail-section">
            <h3><i class="fas fa-flask"></i> 推荐配方明细（Demo 样式）</h3>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>原材料品种</th>
                    <th>规格</th>
                    <th>配比(%)</th>
                    <th>参考价格(元/kg)</th>
                    <th>关键性质</th>
                    <th>作用说明</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, idx) in formulaDetails.materials" :key="`m-${idx}`">
                    <td>{{ item.name }}</td>
                    <td>{{ item.spec }}</td>
                    <td>{{ item.ratio }}</td>
                    <td>{{ item.price }}</td>
                    <td>{{ item.properties }}</td>
                    <td>{{ item.role }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div v-if="formulaDetails.process.length" class="detail-section">
            <h3><i class="fas fa-sliders-h"></i> 工艺参数建议</h3>
            <div class="process-grid">
              <div class="process-card" v-for="(p, idx) in formulaDetails.process" :key="`p-${idx}`">
                <div class="process-label">{{ p.label }}</div>
                <div class="process-value">{{ p.value }}</div>
                <div class="process-note">{{ p.note }}</div>
              </div>
            </div>
          </div>

          <div v-if="formulaDetails.costs.length" class="detail-section">
            <h3><i class="fas fa-coins"></i> 成本与性能平衡建议</h3>
            <div class="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>方案</th>
                    <th>估算成本(元/kg)</th>
                    <th>预计性能得分</th>
                    <th>适用场景</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, idx) in formulaDetails.costs" :key="`c-${idx}`">
                    <td>{{ row.plan }}</td>
                    <td>{{ row.cost }}</td>
                    <td>{{ row.score }}</td>
                    <td>{{ row.scenario }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 历史记录（可选） -->
    <div v-if="historyList.length > 0" class="history-section">
      <h2>
        <i class="fas fa-history"></i>
        历史记录
      </h2>
      <div class="history-table-wrap">
        <table class="history-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>配方简要</th>
              <th>时间</th>
              <th>任务状态</th>
              <th>是否有效配方</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in paginatedHistoryList"
              :key="item.id"
              class="history-row"
            >
              <td class="history-id">{{ item.id }}</td>
              <td class="history-brief">{{ item.brief }}</td>
              <td>{{ formatDate(item.created_at) }}</td>
              <td>
                <span :class="['task-status-badge', `status-${getTaskStatus(item)}`]">
                  {{ getTaskStatusLabel(item) }}
                </span>
              </td>
              <td>
                <span
                  :class="['valid-badge', `status-${getValidityStatus(item)}`]"
                >
                  {{ getValidityLabel(item) }}
                </span>
              </td>
              <td>
                <button class="history-view-btn" type="button" @click="openHistoryDetail(item)">
                  进入查看
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="totalHistoryPages > 1" class="history-pagination">
        <button class="page-btn" :disabled="historyPage === 1" @click="goToHistoryPage(historyPage - 1)">上一页</button>
        <button
          v-for="page in historyPageNumbers"
          :key="`history-page-${page}`"
          :class="['page-btn', { active: page === historyPage }]"
          @click="goToHistoryPage(page)"
        >
          {{ page }}
        </button>
        <button class="page-btn" :disabled="historyPage === totalHistoryPages" @click="goToHistoryPage(historyPage + 1)">下一页</button>
        <span class="page-summary">第 {{ historyPage }} / {{ totalHistoryPages }} 页</span>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()
const FORMULA_HISTORY_STORAGE_KEY = 'formula_generation_history'
const LOCAL_TASK_STORAGE_KEY = 'smart_agent_local_tasks'
const isPageLeaving = ref(false)
const RUNNING_STATUS_SYNC_INTERVAL_MS = 10000
const TASK_MATCH_WINDOW_MS = 5 * 60 * 1000
const RUNNING_STATUS_STALE_MS = 20 * 60 * 1000
let runningStatusSyncTimer = null

const getAuthToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || ''

const materialSystemOptions = [
  { value: 'lithium_battery_anode', label: '锂电负极体系' },
  { value: 'lithium_battery_cathode', label: '锂电正极体系' },
  { value: 'solid_electrolyte', label: '固态电解质体系' },
  { value: 'conductive_coating', label: '导电涂层体系' },
  { value: 'polymer_composite', label: '高分子复合体系' }
]

const systemFieldTemplates = {
  lithium_battery_anode: {
    description: '负极体系建议重点输入容量、导电网络、粒径及粘结体系。',
    fields: [
      { key: 'target_phase', label: '目标相/结构', icon: 'fas fa-atom', placeholder: '石墨化碳相 + 硅碳复合结构', hint: '明确目标晶相或复合结构' },
      { key: 'target_capacity', label: '目标比容量 (mAh/g)', icon: 'fas fa-battery-three-quarters', placeholder: '例如：≥ 520', hint: '用于约束容量目标' },
      { key: 'target_conductivity', label: '目标导电率 (S/cm)', icon: 'fas fa-bolt', placeholder: '例如：≥ 1.2e-2', hint: '用于平衡倍率性能' },
      { key: 'target_particle_size', label: '粒径要求', icon: 'fas fa-braille', placeholder: '例如：D50=9~11 μm', hint: '影响压实密度和循环寿命' },
      { key: 'process_route', label: '工艺路线偏好', icon: 'fas fa-industry', placeholder: '湿法混合 + 喷雾造粒 + 惰性烧结', hint: '可输入你的设备约束' },
      { key: 'doping_strategy', label: '掺杂/改性策略', icon: 'fas fa-vial', placeholder: '例如：B/N 协同掺杂', hint: '用于提升界面稳定性' }
    ]
  },
  lithium_battery_cathode: {
    description: '正极体系建议补充工作电压窗口、包覆策略及热稳定目标。',
    fields: [
      { key: 'target_phase', label: '目标晶相', icon: 'fas fa-atom', placeholder: '层状氧化物 / 橄榄石相', hint: '决定循环稳定与倍率性能' },
      { key: 'working_voltage', label: '工作电压区间 (V)', icon: 'fas fa-wave-square', placeholder: '例如：2.8~4.3', hint: '用于选择材料体系与电解液窗口' },
      { key: 'target_capacity', label: '目标比容量 (mAh/g)', icon: 'fas fa-battery-half', placeholder: '例如：≥ 170', hint: '建议给出最低可接受值' },
      { key: 'target_stability_temp', label: '热稳定目标 (°C)', icon: 'fas fa-temperature-high', placeholder: '例如：220℃以上', hint: '用于高温安全评估' },
      { key: 'doping_strategy', label: '元素掺杂策略', icon: 'fas fa-vial', placeholder: '例如：Al/Mg 共掺杂', hint: '降低相变与容量衰减' },
      { key: 'process_route', label: '烧结工艺偏好', icon: 'fas fa-fire', placeholder: '例如：两段烧结 500℃+780℃', hint: '有助于粒径与相纯度控制' }
    ]
  },
  solid_electrolyte: {
    description: '固态电解质需重点输入离子电导、界面阻抗和致密化工艺要求。',
    fields: [
      { key: 'electrolyte_type', label: '电解质类型', icon: 'fas fa-flask', type: 'select', hint: '优先选择明确体系', options: [
        { value: 'sulfide', label: '硫化物' },
        { value: 'oxide', label: '氧化物' },
        { value: 'polymer', label: '聚合物' },
        { value: 'composite', label: '复合电解质' }
      ] },
      { key: 'ionic_conductivity', label: '离子电导率 (S/cm)', icon: 'fas fa-bolt', placeholder: '例如：≥ 1.0e-3', hint: '室温离子导电指标' },
      { key: 'target_stability_temp', label: '热稳定目标 (°C)', icon: 'fas fa-temperature-high', placeholder: '例如：150℃以上', hint: '考虑安全和工艺窗口' },
      { key: 'process_route', label: '致密化工艺', icon: 'fas fa-compress-alt', placeholder: '例如：冷压 + 低温烧结', hint: '影响界面接触与阻抗' },
      { key: 'target_particle_size', label: '粉体粒径要求', icon: 'fas fa-braille', placeholder: '例如：D90 < 5 μm', hint: '细粉有助于膜致密化' },
      { key: 'doping_strategy', label: '界面改性策略', icon: 'fas fa-sitemap', placeholder: '例如：LiF 表面包覆', hint: '降低界面副反应' }
    ]
  },
  conductive_coating: {
    description: '导电涂层重点关注膜厚、方阻、附着力与涂布工艺窗口。',
    fields: [
      { key: 'film_thickness', label: '目标膜厚 (μm)', icon: 'fas fa-ruler-combined', placeholder: '例如：8~12', hint: '影响导电性与机械强度' },
      { key: 'surface_resistance', label: '目标方阻 (Ω/□)', icon: 'fas fa-bolt', placeholder: '例如：≤ 10', hint: '核心导电性能指标' },
      { key: 'target_stability_temp', label: '耐温目标 (°C)', icon: 'fas fa-temperature-high', placeholder: '例如：180℃', hint: '决定应用温区' },
      { key: 'process_route', label: '涂布工艺路线', icon: 'fas fa-paint-roller', placeholder: '例如：狭缝涂布 + 分段烘干', hint: '与现有产线兼容' },
      { key: 'doping_strategy', label: '导电填料策略', icon: 'fas fa-project-diagram', placeholder: '例如：CNT + 石墨烯复配', hint: '平衡成本和导电性能' }
    ]
  },
  polymer_composite: {
    description: '高分子复合体系建议明确基体树脂、填料类型与固化曲线。',
    fields: [
      { key: 'matrix_resin', label: '基体树脂类型', icon: 'fas fa-cubes', placeholder: '例如：环氧树脂 E51', hint: '决定加工和力学基线' },
      { key: 'filler_type', label: '填料类型', icon: 'fas fa-shapes', placeholder: '例如：Al2O3 + BN', hint: '决定导热/力学方向' },
      { key: 'filler_loading', label: '填料添加量 (%)', icon: 'fas fa-balance-scale', placeholder: '例如：45~55', hint: '过高会影响加工流动性' },
      { key: 'curing_profile', label: '固化制度', icon: 'fas fa-stopwatch', placeholder: '例如：80℃ 2h + 120℃ 3h', hint: '建议提供可实现温程' },
      { key: 'glass_transition_temp', label: '目标 Tg (°C)', icon: 'fas fa-thermometer-half', placeholder: '例如：≥ 140', hint: '评估热机械稳定性' },
      { key: 'target_conductivity', label: '目标导热率/导电率', icon: 'fas fa-bolt', placeholder: '例如：导热率 ≥ 2.5 W/m·K', hint: '按场景选填热导或电导' }
    ]
  }
}

const createEmptyFormData = () => ({
  product_performance_requirements: '',
  target_application_scenario: '',
  cost_consideration: '',
  environmental_requirements: '',
  material_system: '',
  target_phase: '',
  target_conductivity: '',
  target_stability_temp: '',
  target_particle_size: '',
  process_route: '',
  target_capacity: '',
  working_voltage: '',
  doping_strategy: '',
  electrolyte_type: '',
  ionic_conductivity: '',
  film_thickness: '',
  surface_resistance: '',
  matrix_resin: '',
  filler_type: '',
  filler_loading: '',
  curing_profile: '',
  glass_transition_temp: ''
})

// 表单数据
const formData = ref(createEmptyFormData())

// 状态管理
const loading = ref(false)
const showResult = ref(false)
const streaming = ref(false)
const streamingAnswer = ref('')
const result = ref('')
const conversationId = ref('')
const messageId = ref('')
const resultTime = ref(null)
const historyList = ref([])
const historyPage = ref(1)
const historyPageSize = 6
const currentHistoryId = ref(null)
const formulaDetails = ref({
  materials: [],
  process: [],
  costs: []
})

const totalHistoryPages = computed(() => Math.max(1, Math.ceil(historyList.value.length / historyPageSize)))
const paginatedHistoryList = computed(() => {
  const start = (historyPage.value - 1) * historyPageSize
  return historyList.value.slice(start, start + historyPageSize)
})
const historyPageNumbers = computed(() => {
  const pages = []
  for (let page = 1; page <= totalHistoryPages.value; page += 1) {
    pages.push(page)
  }
  return pages
})

const currentHistoryRecord = computed(() => {
  if (!currentHistoryId.value) return null
  return historyList.value.find((item) => item?.id === currentHistoryId.value) || null
})

const currentValidityStatus = computed({
  get() {
    return currentHistoryRecord.value ? getValidityStatus(currentHistoryRecord.value) : 'pending'
  },
  set(nextStatus) {
    updateHistoryValidity(currentHistoryId.value, nextStatus)
  }
})

const formulaSummaryKpis = computed(() => {
  const materialCount = formulaDetails.value.materials.length
  const processCount = formulaDetails.value.process.length
  const costPlans = formulaDetails.value.costs.length
  return [
    { label: '推荐原料数', value: `${materialCount}`, note: '覆盖核心功能组分' },
    { label: '关键工艺节点', value: `${processCount}`, note: '包含可执行工艺参数' },
    { label: '成本方案数', value: `${costPlans}`, note: '支持多场景权衡选择' },
    { label: '推荐可信度', value: materialCount ? '高' : '中', note: '基于输入完整度估计' }
  ]
})

const strategyMatrixRows = computed(() => [
  { dimension: '导电网络', performance: 'CNT+石墨烯复配', balanced: 'CNT+炭黑复配', cost: '高结构炭黑' },
  { dimension: '活性组分占比', performance: '高活性占比（>80%）', balanced: '中等活性占比（70~80%）', cost: '稳健占比（<70%）' },
  { dimension: '粘结体系', performance: '柔性高分子复配', balanced: 'SBR/CMC 标准组合', cost: '低成本水系体系' },
  { dimension: '工艺窗口', performance: '窄窗口精控', balanced: '中窗口稳态控制', cost: '宽窗口低复杂度' }
])
const suppressSystemWatch = ref(false)

const activeSystemTemplate = computed(() => {
  return systemFieldTemplates[formData.value.material_system] || { description: '', fields: [] }
})

// Dify API 配置 - 现在改用后端API
const API_BASE = '/api/smart-agent'  // 使用后端代理

const resetSystemFields = (system) => {
  const allFieldKeys = Array.from(
    new Set(Object.values(systemFieldTemplates).flatMap((tpl) => tpl.fields.map((field) => field.key)))
  )
  allFieldKeys.forEach((key) => {
    formData.value[key] = ''
  })

  if (!system) {
    return
  }

  const selectedTemplate = systemFieldTemplates[system]
  if (selectedTemplate?.fields?.length) {
    selectedTemplate.fields.forEach((field) => {
      if (field.type === 'select' && field.options?.length) {
        formData.value[field.key] = field.options[0].value
      }
    })
  }
}

const getSystemSpecificParams = () => {
  const params = {}
  activeSystemTemplate.value.fields.forEach((field) => {
    if (formData.value[field.key]) {
      params[field.key] = formData.value[field.key]
    }
  })
  return params
}

const demoFormulaPayloads = {
  lithium_battery_anode: {
    form: {
      product_performance_requirements: '高导电性、循环寿命>1200次、低温性能稳定',
      target_application_scenario: '消费电子锂电池负极材料',
      cost_consideration: '综合成本控制在 850 元/kg 以内',
      environmental_requirements: '符合 RoHS/REACH，无卤，低VOC',
      material_system: 'lithium_battery_anode',
      target_phase: '石墨化碳相 + 硅碳复合结构',
      target_capacity: '≥ 520',
      target_conductivity: '≥ 1.2e-2',
      target_particle_size: 'D50=9~11 μm',
      process_route: '湿法混合 + 喷雾造粒 + 惰性烧结',
      doping_strategy: 'B/N 协同掺杂'
    },
    result: {
      answer: `### 配方建议结论\n\n推荐采用“硅碳复合 + 导电网络增强 + 柔性粘结剂”路线。\n\n- 在保证导电率和循环稳定性的前提下，优先使用中位价位的人造石墨与纳米硅。\n- 通过少量 CNT + 导电炭黑复配，可显著降低界面阻抗。\n- 粘结剂采用 SBR/CMC 复配以平衡加工性与循环寿命。`,
      details: {
        materials: [
          { name: '人造石墨', spec: 'D50=10μm, 比表面积 2.5m²/g', ratio: '72', price: '420', properties: '导电性优、结构稳定', role: '主体储锂骨架' },
          { name: '纳米硅', spec: '粒径 80~120nm, 纯度≥99.5%', ratio: '12', price: '1600', properties: '高理论容量', role: '提升容量上限' },
          { name: '碳纳米管(CNT)', spec: '纯度≥95%, 长径比>1000', ratio: '3', price: '2200', properties: '导电网络构建能力强', role: '降低电荷传输阻抗' },
          { name: '导电炭黑', spec: '吸油值 280~320 ml/100g', ratio: '4', price: '180', properties: '分散性好', role: '补充导电通路' },
          { name: 'SBR/CMC 粘结剂', spec: 'SBR:CMC=2:1', ratio: '7', price: '95', properties: '柔性粘结、耐循环', role: '提升结构完整性' },
          { name: '功能添加剂', spec: '界面稳定剂，电池级', ratio: '2', price: '680', properties: '改善 SEI 膜稳定性', role: '提升首效与寿命' }
        ],
        process: [
          { label: '球磨混合', value: '350 rpm × 3h', note: '控制纳米硅团聚，提升分散均匀性' },
          { label: '浆料黏度', value: '1800~2500 mPa·s', note: '适配高速涂布，减少流挂' },
          { label: '干燥条件', value: '80℃ × 6h', note: '避免粘结剂过快失水导致裂纹' },
          { label: '烧结窗口', value: '700~760℃, N₂气氛', note: '形成稳定导电网络并抑制副反应' }
        ],
        costs: [
          { plan: '平衡方案（推荐）', cost: '约 820', score: '89/100', scenario: '消费电子主力型号' },
          { plan: '高性能方案', cost: '约 980', score: '93/100', scenario: '高端快充产品' },
          { plan: '成本优先方案', cost: '约 730', score: '84/100', scenario: '入门级产品线' }
        ]
      }
    }
  },
  solid_electrolyte: {
    form: {
      product_performance_requirements: '高离子电导、低界面阻抗、可室温成膜',
      target_application_scenario: '全固态锂电池电解质层',
      cost_consideration: '中试阶段成本可接受上限 1200 元/kg',
      environmental_requirements: '无卤、低毒、可满足 REACH',
      material_system: 'solid_electrolyte',
      electrolyte_type: 'composite',
      ionic_conductivity: '≥ 1.5e-3',
      target_stability_temp: '150℃以上',
      process_route: '冷压成膜 + 低温致密化',
      target_particle_size: 'D90 < 5 μm',
      doping_strategy: 'LiF 界面改性'
    },
    result: {
      answer: `### 配方建议结论\n\n建议采用“氧化物-聚合物复合固态电解质”路线，兼顾离子电导、界面接触与工艺可制造性。`,
      details: {
        materials: [
          { name: 'LLZO 粉体', spec: 'D50=1.2μm, 纯度≥99.9%', ratio: '58', price: '1800', properties: '高离子导电骨架', role: '提供主离子传输通道' },
          { name: 'PEO 基聚合物', spec: '分子量 60万', ratio: '18', price: '220', properties: '柔性成膜', role: '改善界面贴合' },
          { name: 'LiTFSI 锂盐', spec: '电池级, 水分<50ppm', ratio: '14', price: '980', properties: '提升离子迁移率', role: '提供可迁移锂离子' },
          { name: '界面改性剂(LiF)', spec: '纳米级', ratio: '3', price: '760', properties: '稳定界面层', role: '抑制副反应' },
          { name: '增韧助剂', spec: '弹性体共混', ratio: '7', price: '260', properties: '提高膜韧性', role: '抑制循环开裂' }
        ],
        process: [
          { label: '复合分散', value: '500 rpm × 2h', note: '保证无机/有机相均匀混合' },
          { label: '冷压条件', value: '250 MPa × 5 min', note: '提升片材致密性' },
          { label: '低温后处理', value: '85℃ × 4h', note: '去除残余溶剂并稳定界面' },
          { label: '目标界面阻抗', value: '< 80 Ω·cm²', note: '用于电芯集成筛选' }
        ],
        costs: [
          { plan: '实验验证方案', cost: '约 1160', score: '91/100', scenario: '全固态实验电芯' },
          { plan: '中试平衡方案', cost: '约 1020', score: '87/100', scenario: '中试小批量' },
          { plan: '成本优化方案', cost: '约 880', score: '82/100', scenario: '早期工程验证' }
        ]
      }
    }
  }
}

const applyFormulaResult = (answerText = '', details = {}) => {
  result.value = answerText
  formulaDetails.value = {
    materials: details.materials || [],
    process: details.process || [],
    costs: details.costs || []
  }
}

const loadDemoFormula = () => {
  const currentSystem = formData.value.material_system || 'lithium_battery_anode'
  const selectedDemo = demoFormulaPayloads[currentSystem] || demoFormulaPayloads.lithium_battery_anode
  suppressSystemWatch.value = true
  formData.value = {
    ...createEmptyFormData(),
    ...selectedDemo.form
  }
  suppressSystemWatch.value = false
  showResult.value = true
  streaming.value = false
  streamingAnswer.value = ''
  currentHistoryId.value = null
  resultTime.value = new Date()
  conversationId.value = `demo-formula-${currentSystem}`
  applyFormulaResult(selectedDemo.result.answer, selectedDemo.result.details)
}

// 提交表单
const submitForm = async () => {
  const inputSnapshot = {
    ...formData.value,
    system_specific_params: getSystemSpecificParams()
  }
  const taskId = `formula-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
  const taskCreatedAt = new Date()
  const createdHistory = saveToHistory({
    inputsSnapshot: inputSnapshot,
    taskId,
    taskStatus: 'pending',
    resultText: '任务已提交，正在生成配方建议，请稍候...',
    details: { materials: [], process: [], costs: [] },
    createdAt: taskCreatedAt
  })

  upsertLocalTask({
    id: taskId,
    agent_name: '配方生成智能体',
    title: `${(inputSnapshot.target_application_scenario || '配方生成任务').slice(0, 30)}...`,
  status: 'pending',
    category: 'formula_generation',
    created_at: taskCreatedAt.toISOString(),
    started_at: taskCreatedAt.toISOString(),
    completed_at: null,
    execution_time: 0
  })

  loading.value = true
  showResult.value = true
  streaming.value = true
  streamingAnswer.value = ''
  currentHistoryId.value = createdHistory?.id || null
  result.value = ''
  formulaDetails.value = { materials: [], process: [], costs: [] }
  resetForm()
  
  try {
    const token = getAuthToken()
    // 调用后端提交接口（阻塞执行，结果写入后端任务）
    const response = await fetch(`${API_BASE}/formula-generation/submit/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      credentials: 'include',
      body: JSON.stringify({
        product_performance_requirements: inputSnapshot.product_performance_requirements,
        // 兼容旧字段
        product_performance: inputSnapshot.product_performance_requirements,
        target_application_scenario: inputSnapshot.target_application_scenario,
        cost_consideration: inputSnapshot.cost_consideration,
        environmental_requirements: inputSnapshot.environmental_requirements,
        material_system: inputSnapshot.material_system,
        system_specific_params: inputSnapshot.system_specific_params || {},
        client_task_id: taskId,
        ...(inputSnapshot.system_specific_params || {})
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const payload = await response.json()
    const backendTaskId = String(payload?.task_id || payload?.task?.id || '').trim()
    const taskPayload = payload?.task || {}
    const outputData = taskPayload?.output_data || payload?.result || {}
    const answerText = String(outputData?.answer || '')
    const detailData = outputData?.details || { materials: [], process: [], costs: [] }
    const remoteStatus = getTaskStatus({ task_status: taskPayload?.status || 'completed' })

    if (backendTaskId && createdHistory?.id) {
      const target = historyList.value.find((item) => item?.id === createdHistory.id)
      if (target) {
        target.backend_task_id = backendTaskId
        target.task_id = taskId
      }
      upsertLocalTask({
        id: taskId,
        backend_task_id: backendTaskId,
        category: 'formula_generation',
        agent_name: '配方生成智能体'
      })
    }

    if (createdHistory?.id) {
      updateHistoryTaskStatus(createdHistory.id, 'running')
    }
    upsertLocalTask({
      id: taskId,
      status: 'running',
      category: 'formula_generation',
      agent_name: '配方生成智能体'
    })

    streamingAnswer.value = answerText
    streaming.value = false
    applyFormulaResult(answerText, detailData)
    resultTime.value = new Date()
    conversationId.value = outputData?.conversation_id || conversationId.value || ''
    messageId.value = outputData?.message_id || outputData?.id || messageId.value || ''

    if (createdHistory?.id) {
      const target = historyList.value.find((item) => item?.id === createdHistory.id)
      if (target) {
        target.result = answerText
        target.details = { ...detailData }
        target.conversation_id = conversationId.value
        target.task_id = taskId
        if (backendTaskId) {
          target.backend_task_id = backendTaskId
        }
      }
      updateHistoryTaskStatus(createdHistory.id, remoteStatus === 'failed' ? 'failed' : 'completed')
    }

    upsertLocalTask({
      id: taskId,
      status: remoteStatus === 'failed' ? 'failed' : 'completed',
      category: 'formula_generation',
      agent_name: '配方生成智能体',
      backend_task_id: backendTaskId || undefined,
      completed_at: new Date().toISOString(),
      execution_time: Math.max(1, Math.round((Date.now() - taskCreatedAt.getTime()) / 1000))
    })

  } catch (error) {
    console.error('请求失败:', error)
    if (isNavigationAbortError(error)) {
      if (createdHistory?.id) {
        updateHistoryTaskStatus(createdHistory.id, 'running')
      }

      upsertLocalTask({
        id: taskId,
        status: 'running',
        category: 'formula_generation',
        agent_name: '配方生成智能体'
      })
      return
    }

    if (createdHistory?.id) {
      updateHistoryTaskStatus(createdHistory.id, 'failed')
    }

    upsertLocalTask({
      id: taskId,
      status: 'failed',
      category: 'formula_generation',
      agent_name: '配方生成智能体',
      completed_at: new Date().toISOString(),
      execution_time: Math.max(1, Math.round((Date.now() - taskCreatedAt.getTime()) / 1000))
    })

    alert('请求失败: ' + error.message + '，已为你载入 Demo 配方方案')
    streaming.value = false
    showResult.value = true
    const selectedDemo = demoFormulaPayloads[inputSnapshot.material_system] || demoFormulaPayloads.lithium_battery_anode
    applyFormulaResult(selectedDemo.result.answer, selectedDemo.result.details)
    resultTime.value = new Date()
    conversationId.value = `demo-formula-${inputSnapshot.material_system || 'lithium_battery_anode'}`
  } finally {
    loading.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.value = createEmptyFormData()
}

// 新建优化
const newOptimization = () => {
  showResult.value = false
  streamingAnswer.value = ''
  result.value = ''
  conversationId.value = ''
  currentHistoryId.value = null
  formulaDetails.value = { materials: [], process: [], costs: [] }
  resetForm()
}

const clearAll = () => {
  showResult.value = false
  streaming.value = false
  streamingAnswer.value = ''
  result.value = ''
  conversationId.value = ''
  messageId.value = ''
  currentHistoryId.value = null
  resultTime.value = null
  formulaDetails.value = { materials: [], process: [], costs: [] }
}

// 复制结果
const copyResult = () => {
  navigator.clipboard.writeText(result.value)
    .then(() => {
      alert('已复制到剪贴板')
    })
    .catch(err => {
      console.error('复制失败:', err)
    })
}

// 下载结果
const downloadResult = () => {
  const blob = new Blob([result.value], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `产品配方生成_${new Date().toISOString().slice(0, 10)}.txt`
  a.click()
  URL.revokeObjectURL(url)
}

// 保存到历史记录
const saveToHistory = ({
  inputsSnapshot = null,
  taskId = '',
  taskStatus = 'pending',
  resultText = '',
  details = null,
  createdAt = new Date()
} = {}) => {
  const baseInputs = inputsSnapshot ? { ...inputsSnapshot } : { ...formData.value }
  const currentResultText = resultText || result.value || streamingAnswer.value
  const brief = (baseInputs.product_performance_requirements || currentResultText || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 60)

  const historyItem = {
    id: Date.now(),
    title: `${(baseInputs.target_application_scenario || '').substring(0, 30)}...`,
    brief: brief || '未提取到配方简要',
    inputs: baseInputs,
    result: currentResultText,
    details: details ? { ...details } : { ...formulaDetails.value },
    conversation_id: conversationId.value,
    created_at: createdAt,
    task_id: taskId || `formula-${Date.now()}`,
    task_status: taskStatus,
    validity_status: 'pending',
    is_valid_formula: false,
  }

  const history = JSON.parse(localStorage.getItem(FORMULA_HISTORY_STORAGE_KEY) || '[]')
  history.unshift(historyItem)

  // 只保留最近20条
  if (history.length > 20) {
    history.pop()
  }

  localStorage.setItem(FORMULA_HISTORY_STORAGE_KEY, JSON.stringify(history))
  loadHistoryList()
  currentHistoryId.value = historyItem.id
  return historyItem
}

const persistHistoryList = () => {
  localStorage.setItem(FORMULA_HISTORY_STORAGE_KEY, JSON.stringify(historyList.value || []))
}

const readLocalTasks = () => {
  const data = JSON.parse(localStorage.getItem(LOCAL_TASK_STORAGE_KEY) || '[]')
  return Array.isArray(data) ? data : []
}

const writeLocalTasks = (list) => {
  localStorage.setItem(LOCAL_TASK_STORAGE_KEY, JSON.stringify(Array.isArray(list) ? list : []))
}

const upsertLocalTask = (taskRecord) => {
  if (!taskRecord?.id) return
  const tasks = readLocalTasks()
  const idx = tasks.findIndex((item) => item?.id === taskRecord.id)
  if (idx >= 0) {
    tasks[idx] = { ...tasks[idx], ...taskRecord }
  } else {
    tasks.unshift(taskRecord)
  }
  writeLocalTasks(tasks.slice(0, 500))
}

const markPageLeaving = () => {
  isPageLeaving.value = true
}

const isNavigationAbortError = (error) => {
  if (isPageLeaving.value) return true
  const name = String(error?.name || '').toLowerCase()
  const msg = String(error?.message || '').toLowerCase()
  return name === 'aborterror' || msg.includes('aborted') || msg.includes('networkerror')
}

const resolveRemoteTaskCategory = (task) => {
  const rawCategory = String(task?.category || '').trim().toLowerCase()
  if (rawCategory) return rawCategory

  const text = `${task?.agent_name || ''} ${task?.title || ''}`.toLowerCase()
  if (text.includes('配方') || text.includes('formula')) return 'formula_generation'
  if (text.includes('工艺') || text.includes('process')) return 'process_optimization'

  const payload = task?.input_data || {}
  if (payload?.material_system || payload?.system_specific_params) return 'formula_generation'
  return ''
}

const isFormulaTask = (task) => {
  return resolveRemoteTaskCategory(task) === 'formula_generation'
}

const toTimestamp = (value) => {
  const ts = new Date(value).getTime()
  return Number.isFinite(ts) ? ts : 0
}

const syncRunningHistoryStatus = async () => {
  const runningHistory = historyList.value.filter((item) => ['pending', 'running'].includes(getTaskStatus(item)))
  if (!runningHistory.length) return

  const token = getAuthToken()
  const authHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }

  const fetchTaskDetail = async (taskUuid) => {
    if (!taskUuid) return null
    try {
      const detailResp = await fetch(`${API_BASE}/formula-generation/task/${taskUuid}/`, {
        method: 'GET',
        headers: authHeaders,
        credentials: 'include'
      })
      if (!detailResp.ok) return null
      const detailPayload = await detailResp.json()
      return detailPayload?.task || null
    } catch (error) {
      return null
    }
  }

  const fetchFormulaHistoryTasks = async () => {
    try {
      const historyResp = await fetch(`${API_BASE}/formula-generation/history/?limit=100`, {
        method: 'GET',
        headers: authHeaders,
        credentials: 'include'
      })
      if (!historyResp.ok) return []
      const payload = await historyResp.json()
      const list = payload?.tasks || payload?.results || payload || []
      return Array.isArray(list) ? list : []
    } catch (error) {
      return []
    }
  }

  let remoteTasks = []
  let tasksFetchSucceeded = false
  try {
    const response = await fetch(`${API_BASE}/tasks/`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include'
    })
    if (response.ok) {
      const payload = await response.json()
      remoteTasks = payload?.results || payload || []
      tasksFetchSucceeded = true
    }
  } catch (error) {
    console.warn('同步任务状态失败（后端不可达）:', error)
  }

  const historyTasks = await fetchFormulaHistoryTasks()

  const remoteMap = new Map(
    remoteTasks
      .filter((item) => item?.id !== undefined && item?.id !== null)
      .map((item) => [String(item.id), item])
  )
  const usedRemoteIds = new Set()

  let changed = false

  for (const item of historyList.value) {
    if (!['pending', 'running'].includes(getTaskStatus(item))) continue

    const backendTaskId = String(item?.backend_task_id || '').trim()
    const localTaskId = String(item?.task_id || '').trim()
    if (!backendTaskId) {
      const directMatch = historyTasks.find((task) => {
        const clientTaskId = String(task?.input_data?.client_task_id || '').trim()
        return clientTaskId && localTaskId && clientTaskId === localTaskId
      })

      if (directMatch) {
        const recoveredId = String(directMatch.id)
        const recoveredStatus = getTaskStatus({ task_status: directMatch?.status })
        item.backend_task_id = recoveredId
        item.task_status = recoveredStatus
        changed = true
        usedRemoteIds.add(recoveredId)

        upsertLocalTask({
          id: item.task_id || item.id,
          backend_task_id: recoveredId,
          status: recoveredStatus,
          category: 'formula_generation',
          agent_name: '配方生成智能体',
          completed_at: directMatch?.completed_at || undefined,
          execution_time: Number(directMatch?.execution_time || 0)
        })
        continue
      }
    }

    let remote = remoteMap.get(backendTaskId)
    if (!remote) {
      remote = await fetchTaskDetail(backendTaskId)
    }

    if (remote) {
      const remoteStatus = getTaskStatus({ task_status: remote?.status })
      if (remoteStatus !== getTaskStatus(item)) {
        item.task_status = remoteStatus
        changed = true
      }
      usedRemoteIds.add(String(remote.id))

      upsertLocalTask({
        id: item.task_id || item.id,
        backend_task_id: backendTaskId,
        status: remoteStatus,
        category: 'formula_generation',
        agent_name: '配方生成智能体',
        completed_at: remote?.completed_at || undefined,
        execution_time: Number(remote?.execution_time || 0)
      })
      continue
    }

    const localCreatedAt = toTimestamp(item?.created_at)
    const unresolvedCandidates = remoteTasks
      .filter((task) => {
        const remoteId = String(task?.id || '').trim()
        if (!remoteId || usedRemoteIds.has(remoteId)) return false
        if (!isFormulaTask(task)) return false
        if (!localCreatedAt) return true

        const remoteCreatedAt = toTimestamp(task?.created_at || task?.started_at)
        if (!remoteCreatedAt) return false

        return Math.abs(remoteCreatedAt - localCreatedAt) <= TASK_MATCH_WINDOW_MS
      })
      .sort((a, b) => {
        const diffA = Math.abs(toTimestamp(a?.created_at || a?.started_at) - localCreatedAt)
        const diffB = Math.abs(toTimestamp(b?.created_at || b?.started_at) - localCreatedAt)
        return diffA - diffB
      })

    const recoveredTask = unresolvedCandidates[0]
    if (!recoveredTask) {
      if (!backendTaskId && tasksFetchSucceeded) {
        const itemCreatedAt = toTimestamp(item?.created_at)
        if (itemCreatedAt && Date.now() - itemCreatedAt > RUNNING_STATUS_STALE_MS) {
          item.task_status = 'failed'
          changed = true
          upsertLocalTask({
            id: item.task_id || item.id,
            status: 'failed',
            category: 'formula_generation',
            agent_name: '配方生成智能体',
            completed_at: new Date().toISOString()
          })
        }
      }
      continue
    }

    const recoveredId = String(recoveredTask.id)
    const recoveredStatus = getTaskStatus({ task_status: recoveredTask?.status })
    item.backend_task_id = recoveredId
    item.task_status = recoveredStatus
    changed = true
    usedRemoteIds.add(recoveredId)

    upsertLocalTask({
      id: item.task_id || item.id,
      backend_task_id: recoveredId,
      status: recoveredStatus,
      category: 'formula_generation',
      agent_name: '配方生成智能体',
      completed_at: recoveredTask?.completed_at || undefined,
      execution_time: Number(recoveredTask?.execution_time || 0)
    })
  }

  if (changed) {
    persistHistoryList()
  }
}

const getTaskStatus = (item) => {
  const raw = String(item?.task_status || '').trim().toLowerCase()
  if (raw === 'cancelled') return 'failed'
  if (['pending', 'running', 'completed', 'failed'].includes(raw)) {
    return raw
  }
  return 'pending'
}

const getTaskStatusLabel = (item) => {
  const status = getTaskStatus(item)
  if (status === 'running') return '执行中'
  if (status === 'completed') return '已完成'
  if (status === 'failed') return '失败'
  return '等待中'
}

const updateHistoryTaskStatus = (targetId, nextStatus) => {
  if (!targetId) return
  if (nextStatus === 'cancelled') nextStatus = 'failed'
  if (!['pending', 'running', 'completed', 'failed'].includes(nextStatus)) return
  const target = historyList.value.find((record) => record?.id === targetId)
  if (!target) return
  target.task_status = nextStatus
  persistHistoryList()
}

const normalizeValidityStatus = (item, fallbackValid = false) => {
  const rawStatus = String(item?.validity_status || '').trim().toLowerCase()
  if (['pending', 'valid', 'invalid'].includes(rawStatus)) {
    return rawStatus
  }
  if (typeof item?.is_valid_formula === 'boolean') {
    return item.is_valid_formula ? 'valid' : 'pending'
  }
  return fallbackValid ? 'valid' : 'pending'
}

const getValidityStatus = (item) => normalizeValidityStatus(item)

const getValidityLabel = (item) => {
  const status = getValidityStatus(item)
  if (status === 'valid') return '有效'
  if (status === 'invalid') return '无效'
  return '待确认'
}

const normalizeBackendHistoryItem = (task) => {
  const inputData = task?.input_data || {}
  const outputData = task?.output_data || {}
  const details = outputData?.details || { materials: [], process: [], costs: [] }
  const answerText = outputData?.answer || ''
  const fallbackBrief = (inputData?.product_performance_requirements || task?.title || answerText || '')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, 60)

  return {
    id: String(task?.id || `history-${Date.now()}`),
    title: task?.title || '配方生成任务',
    brief: task?.brief_summary || fallbackBrief || '未提取到配方简要',
    inputs: inputData,
    result: answerText,
    details,
    conversation_id: outputData?.conversation_id || '',
    created_at: task?.created_at || new Date().toISOString(),
    task_id: String(inputData?.client_task_id || task?.id || ''),
    backend_task_id: String(task?.id || ''),
    task_status: getTaskStatus({ task_status: task?.status }),
    validity_status: normalizeValidityStatus({ validity_status: task?.validity_status }),
    is_valid_formula: normalizeValidityStatus({ validity_status: task?.validity_status }) === 'valid',
    created_by_name: task?.created_by_name || ''
  }
}

// 加载历史记录列表
const loadHistoryList = async () => {
  const token = getAuthToken()
  const authHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }

  try {
    const response = await fetch(`${API_BASE}/formula-generation/history/?limit=100`, {
      method: 'GET',
      headers: authHeaders,
      credentials: 'include'
    })

    if (response.ok) {
      const payload = await response.json()
      const remoteTasks = Array.isArray(payload?.tasks) ? payload.tasks : []
      historyList.value = remoteTasks.map((task) => normalizeBackendHistoryItem(task))
      persistHistoryList()
      if (historyPage.value > totalHistoryPages.value) {
        historyPage.value = totalHistoryPages.value
      }
      return
    }
  } catch (error) {
    console.warn('加载后端配方历史失败:', error)
  }
  historyList.value = []

  if (historyPage.value > totalHistoryPages.value) {
    historyPage.value = totalHistoryPages.value
  }
}

const goToHistoryPage = (page) => {
  if (page < 1 || page > totalHistoryPages.value) return
  historyPage.value = page
}

const updateHistoryValidity = (targetId, nextStatus) => {
  if (!targetId) return
  if (!['pending', 'valid', 'invalid'].includes(nextStatus)) return
  const target = historyList.value.find((record) => record?.id === targetId)
  if (!target) return
  target.validity_status = nextStatus
  target.is_valid_formula = nextStatus === 'valid'
  persistHistoryList()

  const backendTaskId = String(target?.backend_task_id || target?.id || '').trim()
  if (!backendTaskId) return

  const token = getAuthToken()
  const authHeaders = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {})
  }

  fetch(`${API_BASE}/tasks/${backendTaskId}/`, {
    method: 'PATCH',
    headers: authHeaders,
    credentials: 'include',
    body: JSON.stringify({ validity_status: nextStatus })
  }).catch((error) => {
    console.warn('回写有效性到后端失败:', error)
  })
}

const openHistoryDetail = (item) => {
  if (!item) return
  currentHistoryId.value = item.id
  loadHistory(item)
}

// 加载历史记录
const loadHistory = (item) => {
  suppressSystemWatch.value = true
  formData.value = { ...createEmptyFormData(), ...(item.inputs || {}) }
  suppressSystemWatch.value = false
  applyFormulaResult(item.result, item.details || {})
  conversationId.value = item.conversation_id
  resultTime.value = new Date(item.created_at)
  showResult.value = true
  streaming.value = false
  currentHistoryId.value = item?.id || null
}

watch(
  () => formData.value.material_system,
  (newSystem, oldSystem) => {
    if (!suppressSystemWatch.value && newSystem !== oldSystem) {
      resetSystemFields(newSystem)
    }
  }
)

// Markdown 格式化
const formatMarkdown = (text) => {
  if (!text) return ''
  return marked(text)
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return d.toLocaleString('zh-CN')
}

// 返回上一页
const goBack = () => {
  router.go(-1)
}

// 组件挂载时加载历史记录
onMounted(async () => {
  isPageLeaving.value = false
  window.addEventListener('beforeunload', markPageLeaving)
  window.addEventListener('pagehide', markPageLeaving)

  await loadHistoryList()
  await syncRunningHistoryStatus()
  runningStatusSyncTimer = setInterval(() => {
    syncRunningHistoryStatus()
  }, RUNNING_STATUS_SYNC_INTERVAL_MS)

  if (!historyList.value.length) {
    loadDemoFormula()
  }
})

onUnmounted(() => {
  window.removeEventListener('beforeunload', markPageLeaving)
  window.removeEventListener('pagehide', markPageLeaving)
  if (runningStatusSyncTimer) {
    clearInterval(runningStatusSyncTimer)
    runningStatusSyncTimer = null
  }
})
</script>

<style scoped>
.formula-generation-page-wrapper {
  display: flex;
  min-height: 100dvh;
  background: #f4f7fb;
}

.process-optimization-container {
  flex: 1;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: clamp(12px, 2vw, 24px);
  box-sizing: border-box;
  overflow-y: auto;
}

.page-header {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.header-main {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
  min-width: 280px;
  justify-content: flex-start;
}

.header-main > div {
  text-align: left;
}

.back-btn {
  border: none;
  background: #f3f4f6;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
}

.back-btn:hover {
  background: #e5e7eb;
}

.page-header h1 {
  margin: 0 0 6px;
}

.page-header p {
  margin: 0;
  color: #667085;
}

.header-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
  align-items: center;
}

.action-btn {
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
}

.action-btn.secondary {
  background: linear-gradient(135deg, #409eff, #5f8bff);
  color: #fff;
}

.action-btn.ghost {
  background: #eef2ff;
  color: #475569;
}

.form-section,
.result-section,
.history-section {
  margin-bottom: 30px;
}

.form-card,
.result-card {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 16px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  border: 1px solid #e8edf7;
}

.form-card h2,
.result-card h2 {
  margin: 0 0 24px 0;
  font-size: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #333;
}

.form-group {
  margin-bottom: 24px;
}

.form-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-weight: 500;
  color: #334155;
}

.required {
  color: #e74c3c;
}

.form-group textarea {
  width: 100%;
  padding: 12px;
  border: 1px solid #dbe3f2;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  transition: all 0.3s;
  background: #fff;
}

.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.14);
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #dbe3f2;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s;
  background: #fff;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.14);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.base-input-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.system-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #eef3ff;
  border: 1px solid #dbe4ff;
  border-radius: 8px;
  color: #44517a;
  padding: 10px 12px;
  margin-bottom: 14px;
  font-size: 13px;
}

.field-hint {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 30px;
}

.btn {
  padding: 12px 24px;
  border: 1px solid transparent;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover:not(:disabled) {
  background: #e5e5e5;
}

.btn-outline {
  background: white;
  color: #667eea;
  border-color: #a5b4fc;
}

.btn-outline:hover {
  background: #eef2ff;
  color: #4f46e5;
  border-color: #818cf8;
}

.streaming-output {
  position: relative;
}

.typing-indicator {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 12px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: #667eea;
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

.stream-content,
.result-text {
  line-height: 1.8;
  color: #333;
  font-size: 15px;
}

.result-text :deep(h1),
.result-text :deep(h2),
.result-text :deep(h3) {
  margin-top: 20px;
  margin-bottom: 10px;
  color: #222;
}

.result-text :deep(code) {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
}

.result-text :deep(pre) {
  background: #f5f5f5;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
}

.result-meta {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
  font-size: 13px;
  color: #64748b;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}

.summary-kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary-kpi-card {
  background: linear-gradient(180deg, #f8faff 0%, #ffffff 100%);
  border: 1px solid #e2e8f7;
  border-radius: 10px;
  padding: 10px 12px;
}

.summary-kpi-label {
  font-size: 12px;
  color: #64748b;
}

.summary-kpi-value {
  font-size: 22px;
  font-weight: 700;
  color: #1e293b;
  margin: 4px 0;
}

.summary-kpi-note {
  font-size: 12px;
  color: #94a3b8;
}

.strategy-matrix {
  margin-top: 14px;
  margin-bottom: 14px;
  border: 1px solid #e8edf7;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.strategy-matrix h3 {
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  color: #334155;
}

.matrix-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  font-size: 13px;
}

.matrix-table th,
.matrix-table td {
  border-bottom: 1px solid #e9edf5;
  padding: 8px 10px;
  text-align: left;
}

.matrix-table th {
  background: #f4f7ff;
  color: #334155;
  font-weight: 600;
}

.matrix-table tbody tr:nth-child(odd) {
  background: #fcfdff;
}

.detail-section {
  margin-top: 18px;
  border: 1px solid #e8edf7;
  border-radius: 12px;
  padding: 14px;
  background: linear-gradient(180deg, #ffffff 0%, #fbfcff 100%);
}

.detail-section h3 {
  margin: 0 0 12px;
  font-size: 15px;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 8px;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th,
td {
  border: 1px solid #e8edf5;
  padding: 8px;
  text-align: left;
  font-size: 13px;
  vertical-align: top;
}

th {
  background: #f6f9ff;
  color: #334155;
  font-weight: 600;
}

.process-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.process-card {
  border: 1px solid #e4e9f4;
  border-radius: 8px;
  padding: 10px;
  background: #fff;
  box-shadow: 0 3px 10px rgba(30, 41, 59, 0.05);
}

.process-label {
  font-size: 12px;
  color: #64748b;
}

.process-value {
  font-size: 16px;
  font-weight: 700;
  margin: 4px 0;
  color: #0f172a;
}

.process-note {
  font-size: 12px;
  color: #475569;
}

.history-section h2 {
  margin-bottom: 16px;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-table-wrap {
  overflow-x: auto;
  border: 1px solid #e8edf7;
  border-radius: 10px;
  background: #fff;
}

.history-table {
  width: 100%;
  border-collapse: collapse;
}

.history-table th,
.history-table td {
  border: 1px solid #e8edf5;
  padding: 10px;
  text-align: left;
  font-size: 13px;
  vertical-align: middle;
}

.history-table th {
  background: #f6f9ff;
  color: #334155;
  font-weight: 600;
}

.history-row {
  transition: background 0.2s;
}

.history-row:hover {
  background: #fff;
}

.history-id {
  width: 120px;
  color: #334155;
  font-weight: 600;
}

.history-brief {
  max-width: 480px;
  color: #0f172a;
}

.valid-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  user-select: none;
}

.task-status-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  user-select: none;
}

.task-status-badge.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.task-status-badge.status-running {
  background: #e0f2fe;
  color: #075985;
}

.task-status-badge.status-completed {
  background: #dcfce7;
  color: #166534;
}

.task-status-badge.status-failed {
  background: #fee2e2;
  color: #991b1b;
}

.history-view-btn {
  border: 1px solid #c9d8f5;
  background: #eef4ff;
  color: #1d4ed8;
  border-radius: 8px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.history-view-btn:hover {
  background: #dbeafe;
}

.validity-select-item {
  gap: 8px;
}

.validity-select-item label {
  color: #334155;
  font-size: 13px;
}

.validity-select-item select {
  border: 1px solid #d5deee;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 13px;
  background: #fff;
  color: #1f2937;
}

.validity-select-item.disabled {
  opacity: 0.65;
}

.valid-badge.status-valid {
  background: #dcfce7;
  color: #166534;
}

.valid-badge.status-pending {
  background: #fef3c7;
  color: #92400e;
}

.valid-badge.status-invalid {
  background: #fee2e2;
  color: #991b1b;
}

.history-pagination {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.page-btn {
  border: 1px solid #d5deee;
  background: #fff;
  color: #334155;
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 13px;
  cursor: pointer;
}

.page-btn.active {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-summary {
  margin-left: 8px;
  color: #64748b;
  font-size: 12px;
}

@media (max-width: 900px) {
  .summary-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .base-input-grid,
  .form-grid,
  .process-grid {
    grid-template-columns: 1fr;
  }

  .header-main {
    min-width: 100%;
  }

  .header-actions {
    margin-left: 0;
  }
}
</style>
