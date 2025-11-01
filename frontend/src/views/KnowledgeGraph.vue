<template>
  <div class="knowledge-graph-container">
    <div class="header">
      <h1>🔗 材料知识图谱</h1>
      <p class="subtitle">原材料 → 中间体 → 配方 → 性能 四级关联数据链</p>
    </div>

    <!-- 控制面板 -->
    <div class="control-panel">
      <el-card class="stats-card">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-icon">🧪</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.rawMaterials }}</div>
              <div class="stat-label">原材料</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">⚗️</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.intermediates }}</div>
              <div class="stat-label">中间体</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">📋</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.formulas }}</div>
              <div class="stat-label">配方</div>
            </div>
          </div>
          <div class="stat-item">
            <div class="stat-icon">📊</div>
            <div class="stat-info">
              <div class="stat-value">{{ stats.performances }}</div>
              <div class="stat-label">性能数据</div>
            </div>
          </div>
        </div>
      </el-card>

      <el-card class="filter-card">
        <div class="filter-controls">
          <el-button type="primary" @click="loadGraphData" :loading="loading">
            <i class="el-icon-refresh"></i> 刷新图谱
          </el-button>
          <el-button @click="resetView">
            <i class="el-icon-refresh-right"></i> 重置视图
          </el-button>
          <el-select v-model="viewMode" placeholder="视图模式" style="width: 150px;">
            <el-option label="完整图谱" value="full"></el-option>
            <el-option label="仅原材料" value="materials"></el-option>
            <el-option label="仅配方" value="formulas"></el-option>
          </el-select>
        </div>
      </el-card>
    </div>

    <!-- 图谱可视化区域 -->
    <el-card class="graph-card" v-loading="loading">
      <div id="knowledge-graph" ref="graphContainer" style="width: 100%; height: 600px;"></div>
    </el-card>

    <!-- 详细信息面板 -->
    <el-drawer
      v-model="drawerVisible"
      :title="selectedNode ? selectedNode.name : '节点详情'"
      direction="rtl"
      size="40%"
    >
      <div v-if="selectedNode" class="node-details">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="编号">{{ selectedNode.code }}</el-descriptions-item>
          <el-descriptions-item label="名称">{{ selectedNode.name }}</el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getNodeTypeColor(selectedNode.type)">
              {{ getNodeTypeLabel(selectedNode.type) }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedNode.type === 'raw_material'" class="extra-info">
          <h3>原材料信息</h3>
          <p><strong>材料类型:</strong> {{ selectedNode.material_type }}</p>
          <p><strong>分子量:</strong> {{ selectedNode.molecular_weight }}</p>
          <p><strong>密度:</strong> {{ selectedNode.density }} g/cm³</p>
          <p><strong>供应商:</strong> {{ selectedNode.supplier }}</p>
          <p><strong>单价:</strong> ¥{{ selectedNode.unit_price }}/kg</p>
        </div>

        <div v-if="selectedNode.type === 'intermediate'" class="extra-info">
          <h3>中间体信息</h3>
          <p><strong>中间体类型:</strong> {{ selectedNode.intermediate_type }}</p>
          <p><strong>粘度:</strong> {{ selectedNode.viscosity }} cps</p>
          <p><strong>固含量:</strong> {{ selectedNode.solid_content }}%</p>
        </div>

        <div v-if="selectedNode.type === 'formula'" class="extra-info">
          <h3>配方信息</h3>
          <p><strong>版本:</strong> {{ selectedNode.version }}</p>
          <p><strong>状态:</strong> {{ selectedNode.status }}</p>
          <p><strong>应用类型:</strong> {{ selectedNode.application_type }}</p>
          <p><strong>混合温度:</strong> {{ selectedNode.mixing_temperature }}°C</p>
          <p><strong>固化时间:</strong> {{ selectedNode.curing_time }}h</p>
        </div>

        <div v-if="selectedNode.type === 'performance'" class="extra-info">
          <h3>性能测试数据</h3>
          <p><strong>测试批次:</strong> {{ selectedNode.test_batch }}</p>
          <p><strong>测试日期:</strong> {{ selectedNode.test_date }}</p>
          <p><strong>拉伸强度:</strong> {{ selectedNode.tensile_strength }} MPa</p>
          <p><strong>断裂伸长率:</strong> {{ selectedNode.elongation_at_break }}%</p>
          <p><strong>撕裂强度:</strong> {{ selectedNode.tear_strength }} kN/m</p>
          <p><strong>硬度:</strong> {{ selectedNode.hardness }} Shore A</p>
          <p><strong>综合评分:</strong> {{ selectedNode.overall_rating }}/5</p>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script>
import { ref, onMounted, reactive } from 'vue'
import * as echarts from 'echarts'
import apiClient from '@/utils/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'KnowledgeGraph',
  setup() {
    const graphContainer = ref(null)
    const loading = ref(false)
    const drawerVisible = ref(false)
    const selectedNode = ref(null)
    const viewMode = ref('full')
    let chartInstance = null

    const stats = reactive({
      rawMaterials: 0,
      intermediates: 0,
      formulas: 0,
      performances: 0
    })

    const graphData = reactive({
      nodes: [],
      edges: []
    })

    // 节点类型映射
    const nodeTypeConfig = {
      raw_material: { label: '原材料', color: '#5470c6', symbol: 'circle' },
      intermediate: { label: '中间体', color: '#91cc75', symbol: 'rect' },
      formula: { label: '配方', color: '#fac858', symbol: 'roundRect' },
      performance: { label: '性能数据', color: '#ee6666', symbol: 'diamond' }
    }

    const getNodeTypeLabel = (type) => {
      return nodeTypeConfig[type]?.label || type
    }

    const getNodeTypeColor = (type) => {
      const colorMap = {
        raw_material: 'primary',
        intermediate: 'success',
        formula: 'warning',
        performance: 'danger'
      }
      return colorMap[type] || 'info'
    }

    // 加载图谱数据
    const loadGraphData = async () => {
      loading.value = true
      try {
        const response = await apiClient.get('/knowledgegraph/graph/full_graph/')
        const data = response.data

        graphData.nodes = data.nodes || []
        graphData.edges = data.edges || []

        // 更新统计数据
        stats.rawMaterials = graphData.nodes.filter(n => n.type === 'raw_material').length
        stats.intermediates = graphData.nodes.filter(n => n.type === 'intermediate').length
        stats.formulas = graphData.nodes.filter(n => n.type === 'formula').length
        stats.performances = graphData.nodes.filter(n => n.type === 'performance').length

        renderGraph()
        ElMessage.success('知识图谱加载成功')
      } catch (error) {
        console.error('加载图谱失败:', error)
        ElMessage.error('加载图谱失败: ' + (error.response?.data?.message || error.message))
      } finally {
        loading.value = false
      }
    }

    // 渲染图谱
    const renderGraph = () => {
      if (!chartInstance) {
        chartInstance = echarts.init(graphContainer.value)
      }

      const nodes = graphData.nodes.map(node => ({
        id: node.id,
        name: node.name,
        symbolSize: node.type === 'formula' ? 60 : 40,
        symbol: nodeTypeConfig[node.type]?.symbol || 'circle',
        itemStyle: {
          color: nodeTypeConfig[node.type]?.color || '#999'
        },
        label: {
          show: true,
          fontSize: 12
        },
        data: node
      }))

      const edges = graphData.edges.map(edge => ({
        source: edge.source,
        target: edge.target,
        label: {
          show: true,
          formatter: edge.relation || ''
        },
        lineStyle: {
          curveness: 0.2
        }
      }))

      const option = {
        title: {
          text: '材料知识图谱',
          left: 'center',
          top: 10
        },
        tooltip: {
          formatter: (params) => {
            if (params.dataType === 'node') {
              const node = params.data.data
              return `${node.name}<br/>类型: ${getNodeTypeLabel(node.type)}<br/>编号: ${node.code}`
            }
            return params.data.label
          }
        },
        legend: {
          data: ['原材料', '中间体', '配方', '性能数据'],
          top: 40
        },
        series: [{
          type: 'graph',
          layout: 'force',
          data: nodes,
          links: edges,
          roam: true,
          draggable: true,
          force: {
            repulsion: 200,
            edgeLength: 150
          },
          emphasis: {
            focus: 'adjacency',
            lineStyle: {
              width: 5
            }
          }
        }]
      }

      chartInstance.setOption(option)

      // 点击节点显示详情
      chartInstance.off('click')
      chartInstance.on('click', (params) => {
        if (params.dataType === 'node') {
          selectedNode.value = params.data.data
          drawerVisible.value = true
        }
      })
    }

    const resetView = () => {
      if (chartInstance) {
        chartInstance.setOption({
          series: [{
            data: graphData.nodes,
            links: graphData.edges
          }]
        })
      }
    }

    onMounted(() => {
      loadGraphData()
      window.addEventListener('resize', () => {
        if (chartInstance) {
          chartInstance.resize()
        }
      })
    })

    return {
      graphContainer,
      loading,
      drawerVisible,
      selectedNode,
      viewMode,
      stats,
      loadGraphData,
      resetView,
      getNodeTypeLabel,
      getNodeTypeColor
    }
  }
}
</script>

<style scoped>
.knowledge-graph-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.header {
  text-align: center;
  margin-bottom: 30px;
}

.header h1 {
  font-size: 2.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 10px;
}

.subtitle {
  color: #666;
  font-size: 1.1rem;
}

.control-panel {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.stats-card {
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px;
  background: white;
  border-radius: 8px;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
}

.filter-card {
  display: flex;
  align-items: center;
}

.filter-controls {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  width: 100%;
}

.graph-card {
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.node-details {
  padding: 20px;
}

.extra-info {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.extra-info h3 {
  color: #667eea;
  margin-bottom: 15px;
}

.extra-info p {
  margin: 10px 0;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .control-panel {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
