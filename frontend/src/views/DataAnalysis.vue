<template>
	<div class="data-analysis-page-wrapper">
		<NavigationSidebar />
		<div class="data-analysis-container">
			<div class="page-header">
				<button @click="goBack" class="back-btn">
					<i class="fas fa-arrow-left"></i>
					返回
				</button>
				<h1>数据分析智能体</h1>
				<p>分析材料数据，发现隐藏模式与趋势，并生成可视化结果</p>
			</div>

			<div class="panel">
				<h2>输入材料数据</h2>
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
			</div>

			<div v-if="error" class="error-box">{{ error }}</div>

			<div v-if="analysisText || visualization.charts.length || visualization.tables.length" class="panel">
				<h2>分析结果</h2>
				<div class="summary" v-if="visualization.summary || analysisText">
					{{ visualization.summary || analysisText }}
				</div>

				<div v-if="visualization.charts.length" class="chart-grid">
					<div class="chart-card" v-for="(chart, idx) in visualization.charts" :key="idx">
						<h3>{{ chart.title || `图表 ${idx + 1}` }}</h3>
						<div class="chart" :ref="el => setChartRef(el, idx)"></div>
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
			</div>
		</div>
	</div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, reactive, ref } from 'vue'
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
	summary: ''
})

const chartRefs = ref([])
const chartInstances = ref([])

const setChartRef = (el, index) => {
	if (el) {
		chartRefs.value[index] = el
	}
}

const clearChartInstances = () => {
	chartInstances.value.forEach((ins) => ins && ins.dispose())
	chartInstances.value = []
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
		const el = chartRefs.value[index]
		if (!el) return
		const ins = echarts.init(el)
		ins.setOption(buildOption(chart))
		chartInstances.value.push(ins)
	})
}

const submitAnalysis = async () => {
	loading.value = true
	error.value = ''
	analysisText.value = ''
	visualization.charts = []
	visualization.tables = []
	visualization.summary = ''

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

		const result = data.result || {}
		analysisText.value = result.answer || ''
		const vis = result.visualization || {}
		visualization.charts = vis.charts || []
		visualization.tables = vis.tables || []
		visualization.summary = vis.summary || ''

		if (visualization.charts.length) {
			await renderCharts()
		}
	} catch (e) {
		error.value = `请求失败：${e.message}`
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
</script>

<style scoped>
.data-analysis-page-wrapper {
	display: flex;
	height: 100vh;
}

.data-analysis-container {
	flex: 1;
	max-width: 1200px;
	margin: 0 auto;
	padding: 20px;
	overflow-y: auto;
}

.page-header { margin-bottom: 16px; }
.page-header h1 { margin: 12px 0 8px; }
.page-header p { color: #666; margin: 0; }

.back-btn {
	border: none;
	background: #f3f4f6;
	padding: 8px 12px;
	border-radius: 8px;
	cursor: pointer;
}

.panel {
	background: #fff;
	border-radius: 12px;
	padding: 20px;
	box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
	margin-bottom: 16px;
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

.submit-btn {
	border: none;
	background: linear-gradient(135deg, #667eea, #764ba2);
	color: #fff;
	padding: 10px 16px;
	border-radius: 8px;
	cursor: pointer;
}

.submit-btn:disabled { opacity: 0.7; cursor: not-allowed; }

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
	.form-inline,
	.chart-grid {
		grid-template-columns: 1fr;
	}
}
</style>
