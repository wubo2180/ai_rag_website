<template>
  <div class="formula-generation-page-wrapper">
    <NavigationSidebar />
    <div class="process-optimization-container">
      <!-- 页面头部 -->
      <div class="page-header">
      <div class="back-navigation">
        <button @click="goBack" class="back-btn">
          <i class="fas fa-arrow-left"></i>
          返回
        </button>
      </div>
      
      <div class="header-content">
        <div class="agent-icon">
          <i class="fas fa-cogs"></i>
        </div>
        <div class="header-info">
          <h1>配方生成</h1>
          <p>根据输入参数生成材料配方建议</p>
        </div>
        <div class="header-actions">
          <button type="button" class="btn btn-outline" @click="loadDemoFormula">载入 Demo 方案</button>
        </div>
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
          <div class="form-group">
            <label for="product_performance">
              <i class="fas fa-chart-line"></i>
              产品性能要求
              <span class="required">*</span>
            </label>
            <textarea
              id="product_performance"
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

          <div class="form-grid">
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
      <div class="history-list">
        <div 
          v-for="item in historyList" 
          :key="item.id"
          class="history-item"
          @click="loadHistory(item)"
        >
          <div class="history-info">
            <div class="history-title">{{ item.title }}</div>
            <div class="history-date">{{ formatDate(item.created_at) }}</div>
          </div>
          <i class="fas fa-chevron-right"></i>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()

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
const formulaDetails = ref({
  materials: [],
  process: [],
  costs: []
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
  resultTime.value = new Date()
  conversationId.value = `demo-formula-${currentSystem}`
  applyFormulaResult(selectedDemo.result.answer, selectedDemo.result.details)
}

// 提交表单
const submitForm = async () => {
  loading.value = true
  showResult.value = true
  streaming.value = true
  streamingAnswer.value = ''
  result.value = ''
  formulaDetails.value = { materials: [], process: [], costs: [] }
  
  try {
    // 调用后端API（流式响应）
    const token = localStorage.getItem('token')
    const response = await fetch(`${API_BASE}/formula-generation/stream/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: JSON.stringify({
        product_performance_requirements: formData.value.product_performance_requirements,
        target_application_scenario: formData.value.target_application_scenario,
        cost_consideration: formData.value.cost_consideration,
        environmental_requirements: formData.value.environmental_requirements,
        // 兼容旧版后端字段
        product_performance: formData.value.product_performance_requirements,
        material_system: formData.value.material_system,
        system_specific_params: getSystemSpecificParams(),
        ...getSystemSpecificParams()
      })
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    // 处理流式响应
    const reader = response.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        streaming.value = false
        applyFormulaResult(streamingAnswer.value, {})
        resultTime.value = new Date()
        break
      }

      const chunk = decoder.decode(value, { stream: true })
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))
            
            if (data.event === 'task_created') {
              console.log('任务已创建:', data.task_id)
            } else if (data.event === 'message' || data.event === 'agent_message') {
              if (data.answer) {
                streamingAnswer.value += data.answer
              }
            } else if (data.event === 'message_end' || data.event === 'agent_message_end') {
              conversationId.value = data.conversation_id || ''
              messageId.value = data.id || ''
            } else if (data.event === 'agent_thought') {
              console.log('Agent 思考:', data.thought)
            } else if (data.event === 'error') {
              console.error('错误:', data.message)
              alert('处理失败: ' + (data.message || data.errors?.join(', ') || '未知错误'))
            } else if (data.event === 'done') {
              console.log('流式响应完成')
            }
          } catch (e) {
            console.error('解析JSON失败:', e)
          }
        }
      }
    }

    // 保存到历史记录
    saveToHistory()

  } catch (error) {
    console.error('请求失败:', error)
    alert('请求失败: ' + error.message + '，已为你载入 Demo 配方方案')
    streaming.value = false
    showResult.value = true
    const selectedDemo = demoFormulaPayloads[formData.value.material_system] || demoFormulaPayloads.lithium_battery_anode
    applyFormulaResult(selectedDemo.result.answer, selectedDemo.result.details)
    resultTime.value = new Date()
    conversationId.value = `demo-formula-${formData.value.material_system || 'lithium_battery_anode'}`
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
  formulaDetails.value = { materials: [], process: [], costs: [] }
  resetForm()
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
const saveToHistory = () => {
  const historyItem = {
    id: Date.now(),
    title: `${formData.value.target_application_scenario.substring(0, 30)}...`,
    inputs: { ...formData.value },
  result: result.value || streamingAnswer.value,
    details: { ...formulaDetails.value },
    conversation_id: conversationId.value,
    created_at: new Date()
  }
  
  const history = JSON.parse(localStorage.getItem('optimization_history') || '[]')
  history.unshift(historyItem)
  
  // 只保留最近20条
  if (history.length > 20) {
    history.pop()
  }
  
  localStorage.setItem('optimization_history', JSON.stringify(history))
  loadHistoryList()
}

// 加载历史记录列表
const loadHistoryList = () => {
  const history = JSON.parse(localStorage.getItem('optimization_history') || '[]')
  historyList.value = history
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
onMounted(() => {
  loadHistoryList()
  if (!historyList.value.length) {
    loadDemoFormula()
  }
})
</script>

<style scoped>
.formula-generation-page-wrapper {
  display: flex;
  min-height: 100vh;
  height: auto;
  background:
    radial-gradient(circle at 10% 8%, rgba(99, 102, 241, 0.08), transparent 36%),
    radial-gradient(circle at 85% 12%, rgba(59, 130, 246, 0.08), transparent 34%),
    #f5f7fb;
}

.process-optimization-container {
  flex: 1;
  width: 100%;
  min-width: 0;
  overflow: visible;
  margin: 0;
  padding: 24px 28px 40px;
  box-sizing: border-box;
}

.page-header {
  margin-bottom: 22px;
}

.back-navigation {
  margin-bottom: 14px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid #e6eaf5;
  color: #475569;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 10px;
  transition: all 0.3s;
  backdrop-filter: blur(4px);
}

.back-btn:hover {
  background: #fff;
  color: #1e293b;
  border-color: #cfd8ea;
  transform: translateY(-1px);
}

.header-content {
  display: flex;
  align-items: center;
  gap: 20px;
  background: linear-gradient(135deg, #5b74e8 0%, #655bd9 48%, #7a4ccd 100%);
  padding: 28px 30px;
  border-radius: 16px;
  color: white;
  box-shadow: 0 14px 30px rgba(93, 97, 211, 0.24);
}

.header-actions {
  margin-left: auto;
}

.agent-icon {
  width: 80px;
  height: 80px;
  background: rgba(255, 255, 255, 0.24);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  border: 1px solid rgba(255, 255, 255, 0.36);
}

.header-info h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 600;
}

.header-info p {
  margin: 0;
  opacity: 0.96;
  font-size: 16px;
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

.history-list {
  display: grid;
  gap: 12px;
}

.history-item {
  background: white;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.06);
  border: 1px solid #e8edf7;
}

.history-item:hover {
  transform: translateX(4px);
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.1);
}

.history-info {
  flex: 1;
}

.history-title {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.history-date {
  font-size: 12px;
  color: #999;
}

.history-item i {
  color: #ccc;
}

@media (max-width: 900px) {
  .process-optimization-container {
    padding: 18px 14px 28px;
  }

  .summary-kpi-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-grid,
  .process-grid {
    grid-template-columns: 1fr;
  }

  .header-content {
    flex-wrap: wrap;
  }

  .header-actions {
    margin-left: 0;
    width: 100%;
  }
}
</style>
