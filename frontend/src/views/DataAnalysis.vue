<template>
	<div class="data-analysis-page-wrapper">
		<NavigationSidebar />
		<div class="data-analysis-container">
			<div class="page-header">
				<div class="header-main">
					<button @click="goBack" class="back-btn">
						<i class="fas fa-arrow-left"></i>
						返回
					</button>
					<div>
						<h1>数据分析智能体</h1>
						<p>分析材料数据，发现隐藏模式与趋势，并生成可视化结果</p>
					</div>
				</div>
				<div class="header-actions">
					<button @click="loadDemoDashboard" class="action-btn secondary">载入 Demo 看板</button>
					<button @click="clearAll" class="action-btn ghost">清空结果</button>
				</div>
			</div>

			<div v-if="hasResult" class="kpi-grid">
				<div class="kpi-card" v-for="item in kpis" :key="item.label">
					<div class="kpi-label">{{ item.label }}</div>
					<div class="kpi-value">{{ item.value }}</div>
					<div class="kpi-trend" :class="item.trendClass">{{ item.trend }}</div>
				</div>
			</div>

			<div class="panel">
				<h2>输入材料数据</h2>
				<div class="demo-hint">
					建议先点“载入 Demo 看板”查看完整图表、列表和表格，再按你的数据发起分析。
				</div>
				<form @submit.prevent="submitAnalysis">
					<div class="form-group">
						<label>材料数据内容（CSV/JSON/文本）</label>
						<textarea
							v-model="form.data_content"
							rows="8"
							required
							placeholder="例如：材料,导电率,热稳定性,成本\n石墨烯,95,90,1200\n碳纳米管,88,82,900"
						></textarea>
					</div>

					<div class="form-inline">
						<div class="form-group">
							<label>分析类型</label>
							<select v-model="form.analysis_type">
								<option value="comprehensive">综合分析</option>
								<option value="trend">趋势分析</option>
								<option value="pattern">模式识别</option>
								<option value="comparison">对比分析</option>
								<option value="distribution">分布分析</option>
								<option value="correlation">相关性分析</option>
							</select>
						</div>
						<div class="form-group">
							<label>分析目标</label>
							<input
								v-model="form.analysis_goal"
								type="text"
								required
								placeholder="例如：找出高性价比材料并分析性能趋势"
							/>
						</div>
					</div>

					<div class="form-group">
						<label>数据背景说明（可选）</label>
						<textarea
							v-model="form.data_description"
							rows="3"
							placeholder="例如：这是锂电池负极材料在不同温度下的实验数据"
						></textarea>
					</div>

					<button type="submit" class="submit-btn" :disabled="loading">
						<i :class="loading ? 'fas fa-spinner fa-spin' : 'fas fa-play'"></i>
						{{ loading ? '分析中...' : '开始分析' }}
					</button>
				</form>

				<div class="quick-list">
					<h3>推荐分析清单</h3>
					<ul>
						<li v-for="(item, idx) in checklist" :key="idx">{{ item }}</li>
					</ul>
				</div>
			</div>

			<div v-if="error" class="error-box">{{ error }}</div>

			<div v-if="hasResult" class="panel">
				<h2>分析结果</h2>
				<div class="summary" v-if="visualization.summary || analysisText">
					{{ visualization.summary || analysisText }}
				</div>

				<div v-if="visualization.insights.length" class="insights-box">
					<h3>关键洞察</h3>
					<ol>
						<li v-for="(item, idx) in visualization.insights" :key="`ins-${idx}`">{{ item }}</li>
					</ol>
				</div>

				<div v-if="visualization.charts.length" class="chart-grid">
					<div class="chart-card" v-for="(chart, idx) in visualization.charts" :key="idx">
						<h3>{{ chart.title || `图表 ${idx + 1}` }}</h3>
						<div class="chart" :id="`chart-container-${idx}`"></div>
					</div>
				</div>

				<div v-if="visualization.rankings.length" class="ranking-list">
					<h3>材料综合评分排行榜</h3>
					<div class="ranking-item" v-for="(item, idx) in visualization.rankings" :key="item.name">
						<div class="rank-index">#{{ idx + 1 }}</div>
						<div class="rank-name">{{ item.name }}</div>
						<div class="rank-score">{{ item.score }}</div>
						<div class="rank-tag">{{ item.tag }}</div>
					</div>
				</div>

				<div v-if="visualization.tables.length" class="table-list">
					<div class="table-card" v-for="(table, idx) in visualization.tables" :key="`table-${idx}`">
						<h3>{{ table.title || `表格 ${idx + 1}` }}</h3>
						<div class="table-wrap">
							<table>
								<thead>
									<tr>
										<th v-for="(col, cIdx) in table.columns || []" :key="cIdx">{{ col }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="(row, rIdx) in table.rows || []" :key="rIdx">
										<td v-for="(cell, cIdx) in row" :key="`${rIdx}-${cIdx}`">{{ cell }}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</div>

				<div v-if="visualization.anomalies.length" class="table-card">
					<h3>异常点监测列表</h3>
					<div class="table-wrap">
						<table>
							<thead>
								<tr>
									<th>材料</th>
									<th>异常指标</th>
									<th>偏离度</th>
									<th>建议动作</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="(item, idx) in visualization.anomalies" :key="`ab-${idx}`">
									<td>{{ item.name }}</td>
									<td>{{ item.metric }}</td>
									<td>{{ item.delta }}</td>
									<td>{{ item.action }}</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as echarts from 'echarts'
import NavigationSidebar from '@/components/NavigationSidebar.vue'

const router = useRouter()
const API_BASE = '/api/smart-agent'

const form = reactive({
	data_content: '',
	analysis_type: 'comprehensive',
	data_description: '',
	analysis_goal: ''
})

const loading = ref(false)
const error = ref('')
const analysisText = ref('')
const visualization = reactive({
	charts: [],
	tables: [],
	summary: '',
	insights: [],
	rankings: [],
	anomalies: []
})

const checklist = [
	'先看综合评分排行榜，筛选出高性价比材料候选集',
	'结合成本-性能散点关系，排查“高成本低收益”材料',
	'对异常点列表中的样本进行二次实验验证',
	'优先推进热稳定性与导电率协同提升的工艺路线'
]

const kpis = ref([])

const hasResult = computed(() => {
	return Boolean(
		analysisText.value ||
		visualization.summary ||
		visualization.charts.length ||
		visualization.tables.length ||
		visualization.insights.length ||
		visualization.rankings.length ||
		visualization.anomalies.length
	)
})

const chartInstances = ref([])

const clearChartInstances = () => {
	chartInstances.value.forEach((ins) => ins && ins.dispose())
	chartInstances.value = []
}

const demoPayload = {
	form: {
		data_content:
			'材料,导电率,热稳定性,成本,良率\n石墨烯复合体,95,92,1280,91\n碳纳米管增强体,89,84,980,88\n硅碳复合体,84,87,760,86\n钛酸锂改性体,78,93,830,90\n多孔碳骨架,82,79,620,83\n氮掺杂碳材料,87,85,710,89',
		analysis_type: 'comprehensive',
		analysis_goal: '找出高性能与成本平衡最优的材料方案',
		data_description: '负极候选材料在同一工艺窗口下的实验统计数据'
	},
	result: {
		answer: '基于样本数据，石墨烯复合体性能上限最高，但成本偏高；硅碳复合体和氮掺杂碳材料在综合得分、成本与良率之间更平衡，适合作为优先中试对象。',
		visualization: {
			summary: 'Demo 数据分析完成：已生成 4 个图表、3 张表格、1 份排行榜与异常点列表，可直接用于演示分析流程。',
			insights: [
				'导电率与良率呈中强正相关，相关系数约 0.68。',
				'钛酸锂改性体热稳定性最高，但导电率偏低，适合高安全场景。',
				'多孔碳骨架成本最低，但性能短板明显，建议用于低成本产品线。'
			],
			charts: [
				{
					title: '材料综合评分对比（柱状图）',
					type: 'bar',
					data: {
						labels: ['石墨烯复合体', '碳纳米管增强体', '硅碳复合体', '钛酸锂改性体', '多孔碳骨架', '氮掺杂碳材料'],
						datasets: [{ label: '综合评分', data: [92, 86, 88, 84, 76, 89] }]
					}
				},
				{
					title: '关键指标趋势（折线图）',
					type: 'line',
					data: {
						labels: ['石墨烯复合体', '碳纳米管增强体', '硅碳复合体', '钛酸锂改性体', '多孔碳骨架', '氮掺杂碳材料'],
						datasets: [
							{ label: '导电率', data: [95, 89, 84, 78, 82, 87] },
							{ label: '热稳定性', data: [92, 84, 87, 93, 79, 85] },
							{ label: '良率', data: [91, 88, 86, 90, 83, 89] }
						]
					}
				},
				{
					title: '成本占比（饼图）',
					type: 'pie',
					data: {
						labels: ['石墨烯复合体', '碳纳米管增强体', '硅碳复合体', '钛酸锂改性体', '多孔碳骨架', '氮掺杂碳材料'],
						datasets: [{ data: [1280, 980, 760, 830, 620, 710] }]
					}
				},
				{
					title: '材料-指标热力图',
					type: 'heatmap',
					data: {
						xLabels: ['导电率', '热稳定性', '良率', '成本反向分'],
						yLabels: ['石墨烯复合体', '碳纳米管增强体', '硅碳复合体', '钛酸锂改性体', '多孔碳骨架', '氮掺杂碳材料'],
						values: [
							[0.95, 0.92, 0.91, 0.4],
							[0.89, 0.84, 0.88, 0.55],
							[0.84, 0.87, 0.86, 0.72],
							[0.78, 0.93, 0.9, 0.68],
							[0.82, 0.79, 0.83, 0.84],
							[0.87, 0.85, 0.89, 0.76]
						]
					}
				}
			],
			tables: [
				{
					title: '材料明细表',
					columns: ['材料', '导电率', '热稳定性', '成本', '良率', '综合评分'],
					rows: [
						['石墨烯复合体', 95, 92, 1280, '91%', 92],
						['碳纳米管增强体', 89, 84, 980, '88%', 86],
						['硅碳复合体', 84, 87, 760, '86%', 88],
						['钛酸锂改性体', 78, 93, 830, '90%', 84],
						['多孔碳骨架', 82, 79, 620, '83%', 76],
						['氮掺杂碳材料', 87, 85, 710, '89%', 89]
					]
				},
				{
					title: '分组统计（按成本区间）',
					columns: ['成本区间', '样本数', '平均综合评分', '平均良率'],
					rows: [
						['600~800', 3, 84.3, '86.0%'],
						['801~1000', 2, 85.0, '89.0%'],
						['1001~1300', 1, 92.0, '91.0%']
					]
				},
				{
					title: '推荐投产优先级清单',
					columns: ['优先级', '材料', '建议原因', '下一步动作'],
					rows: [
						['P1', '氮掺杂碳材料', '性能与成本均衡，良率高', '进入中试放大'],
						['P1', '硅碳复合体', '性价比优，成本可控', '优化循环寿命'],
						['P2', '钛酸锂改性体', '热稳定性突出', '用于高安全场景验证']
					]
				}
			],
			rankings: [
				{ name: '石墨烯复合体', score: 92, tag: '性能上限最高' },
				{ name: '氮掺杂碳材料', score: 89, tag: '平衡最优' },
				{ name: '硅碳复合体', score: 88, tag: '高性价比' },
				{ name: '碳纳米管增强体', score: 86, tag: '稳定成熟' }
			],
			anomalies: [
				{ name: '石墨烯复合体', metric: '成本', delta: '+35%', action: '优化配方/替代前驱体' },
				{ name: '多孔碳骨架', metric: '热稳定性', delta: '-12%', action: '增加结构改性处理' }
			]
		}
	}
}

const buildOption = (chart) => {
	const type = chart?.type
	const data = chart?.data || {}

	if (type === 'pie') {
		const labels = data.labels || []
		const values = data?.datasets?.[0]?.data || []
		return {
			tooltip: { trigger: 'item' },
			legend: { top: 'bottom' },
			series: [
				{
					type: 'pie',
					radius: '60%',
					data: labels.map((name, i) => ({ name, value: values[i] ?? 0 }))
				}
			]
		}
	}

	if (type === 'heatmap') {
		const xLabels = data.xLabels || []
		const yLabels = data.yLabels || []
		const values = data.values || []
		const heatData = []
		yLabels.forEach((_, y) => {
			xLabels.forEach((_, x) => {
				heatData.push([x, y, values?.[y]?.[x] ?? 0])
			})
		})
		return {
			tooltip: { position: 'top' },
			xAxis: { type: 'category', data: xLabels },
			yAxis: { type: 'category', data: yLabels },
			visualMap: { min: 0, max: 1, calculable: true, orient: 'horizontal', left: 'center', bottom: 0 },
			series: [{ type: 'heatmap', data: heatData }]
		}
	}

	const labels = data.labels || []
	const datasets = data.datasets || []
	return {
		tooltip: { trigger: 'axis' },
		legend: {},
		xAxis: { type: 'category', data: labels },
		yAxis: { type: 'value' },
		series: datasets.map((d) => ({
			name: d.label || '数据集',
			type: type === 'line' ? 'line' : 'bar',
			data: d.data || []
		}))
	}
}

const renderCharts = async () => {
	await nextTick()
	clearChartInstances()

	visualization.charts.forEach((chart, index) => {
		const el = document.getElementById(`chart-container-${index}`)
		if (!el) return
		const ins = echarts.init(el)
		ins.setOption(buildOption(chart))
		chartInstances.value.push(ins)
	})
}

const applyResult = async (result) => {
	analysisText.value = result.answer || ''
	const vis = result.visualization || {}
	visualization.charts = vis.charts || []
	visualization.tables = vis.tables || []
	visualization.summary = vis.summary || ''
	visualization.insights = vis.insights || []
	visualization.rankings = vis.rankings || []
	visualization.anomalies = vis.anomalies || []

	kpis.value = [
		{ label: '图表数量', value: `${visualization.charts.length}`, trend: '可视化覆盖', trendClass: 'neutral' },
		{ label: '表格数量', value: `${visualization.tables.length}`, trend: '结构化结果', trendClass: 'neutral' },
		{ label: '关键洞察', value: `${visualization.insights.length}`, trend: '可解释结论', trendClass: 'up' },
		{ label: '异常点', value: `${visualization.anomalies.length}`, trend: '需重点关注', trendClass: visualization.anomalies.length ? 'down' : 'up' }
	]

	if (visualization.charts.length) {
		await renderCharts()
	}
}

const loadDemoDashboard = async () => {
	Object.assign(form, demoPayload.form)
	error.value = ''
	await applyResult(demoPayload.result)
}

const clearAll = () => {
	error.value = ''
	analysisText.value = ''
	visualization.charts = []
	visualization.tables = []
	visualization.summary = ''
	visualization.insights = []
	visualization.rankings = []
	visualization.anomalies = []
	kpis.value = []
	clearChartInstances()
}

const submitAnalysis = async () => {
	loading.value = true
	error.value = ''
	clearAll()

	try {
		const response = await fetch(`${API_BASE}/data-analysis/submit/`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ ...form })
		})

		const data = await response.json()
		if (!response.ok || !data.success) {
			throw new Error(data.error || data.message || '分析失败')
		}

		await applyResult(data.result || {})
	} catch (e) {
		error.value = `请求失败：${e.message}（已为你加载 Demo 数据）`
		await applyResult(demoPayload.result)
	} finally {
		loading.value = false
	}
}

const goBack = () => {
	router.push({ name: 'SmartAgents' })
}

onBeforeUnmount(() => {
	clearChartInstances()
})

onMounted(() => {
	loadDemoDashboard()
})
</script>

<style scoped>
.data-analysis-page-wrapper {
	display: flex;
	min-height: 100dvh;
	width: 100%;
	background: #f4f7fb;
}

.data-analysis-container {
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
}

.page-header h1 { margin: 0 0 6px; }
.page-header p { color: #667085; margin: 0; }

.header-actions {
	display: flex;
	gap: 8px;
}

.back-btn {
	border: none;
	background: #f3f4f6;
	padding: 8px 12px;
	border-radius: 8px;
	cursor: pointer;
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

.kpi-grid {
	display: grid;
	grid-template-columns: repeat(4, minmax(0, 1fr));
	gap: 12px;
	margin-bottom: 16px;
}

.kpi-card {
	background: #fff;
	border-radius: 12px;
	padding: 14px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.kpi-label {
	font-size: 12px;
	color: #64748b;
}

.kpi-value {
	font-size: 28px;
	font-weight: 700;
	margin: 6px 0;
}

.kpi-trend {
	font-size: 12px;
}

.kpi-trend.up { color: #16a34a; }
.kpi-trend.down { color: #dc2626; }
.kpi-trend.neutral { color: #475569; }

.panel {
	background: #fff;
	border-radius: 12px;
	padding: 20px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
	margin-bottom: 16px;
}

.demo-hint {
	background: #f5f7ff;
	border: 1px solid #dbe4ff;
	padding: 10px 12px;
	border-radius: 8px;
	font-size: 13px;
	color: #4b5563;
	margin-bottom: 14px;
}

.form-group { margin-bottom: 14px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 500; }

textarea, input, select {
	width: 100%;
	border: 1px solid #dcdfe6;
	border-radius: 8px;
	padding: 10px 12px;
	font-size: 14px;
}

.form-inline {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 12px;
}

.quick-list {
	margin-top: 14px;
	padding-top: 12px;
	border-top: 1px dashed #e5e7eb;
}

.quick-list h3 {
	margin: 0 0 8px;
	font-size: 15px;
}

.quick-list ul {
	margin: 0;
	padding-left: 18px;
	color: #475569;
	line-height: 1.7;
	font-size: 13px;
}

.submit-btn {
	border: none;
	background: linear-gradient(135deg, #667eea, #764ba2);
	color: #fff;
	padding: 10px 16px;
	border-radius: 8px;
	cursor: pointer;
}

.submit-btn:disabled {
	opacity: 0.7;
	cursor: not-allowed;
}

.error-box {
	background: #fff1f0;
	color: #cf1322;
	border: 1px solid #ffa39e;
	border-radius: 8px;
	padding: 10px;
	margin-bottom: 12px;
}

.summary {
	line-height: 1.8;
	color: #333;
	margin-bottom: 12px;
	white-space: pre-wrap;
}

.insights-box {
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 10px;
	padding: 12px;
	margin-bottom: 12px;
}

.insights-box h3 {
	margin: 0 0 8px;
	font-size: 15px;
}

.insights-box ol {
	margin: 0;
	padding-left: 18px;
	font-size: 13px;
	line-height: 1.8;
	color: #334155;
}

.chart-grid {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 12px;
}

.chart-card {
	border: 1px solid #eee;
	border-radius: 10px;
	padding: 10px;
}

.chart {
	width: 100%;
	height: 320px;
}

.table-card {
	margin-top: 12px;
	border: 1px solid #eee;
	border-radius: 10px;
	padding: 10px;
}

.ranking-list {
	margin-top: 12px;
	border: 1px solid #e5e7eb;
	border-radius: 10px;
	padding: 12px;
	background: #fcfdff;
}

.ranking-list h3 {
	margin: 0 0 10px;
}

.ranking-item {
	display: grid;
	grid-template-columns: 60px 1fr 80px 140px;
	gap: 10px;
	padding: 8px 10px;
	border-radius: 8px;
	background: #fff;
	border: 1px solid #eceff5;
	margin-bottom: 8px;
	align-items: center;
	font-size: 13px;
}

.rank-index {
	font-weight: 700;
	color: #4f46e5;
}

.rank-name {
	font-weight: 500;
}

.rank-score {
	font-weight: 700;
	color: #0f766e;
}

.rank-tag {
	color: #475569;
}

.table-wrap { overflow-x: auto; }

table {
	width: 100%;
	border-collapse: collapse;
}

th, td {
	border: 1px solid #e8e8e8;
	padding: 8px;
	text-align: left;
	font-size: 13px;
}

@media (max-width: 900px) {
	.kpi-grid,
	.form-inline,
	.chart-grid {
		grid-template-columns: 1fr;
	}

	.ranking-item {
		grid-template-columns: 1fr 1fr;
	}
}
</style>
