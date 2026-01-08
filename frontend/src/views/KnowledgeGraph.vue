<template>
  <div class="knowledge-graph-page-wrapper">
    <NavigationSidebar />
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
            <el-select
              v-model="viewMode"
              placeholder="完整图谱"
              style="width: 180px"
              @change="handleViewModeChange"
            >
              <el-option label="完整图谱" value="full"></el-option>
              <el-option label="仅原材料" value="raw_material"></el-option>
              <el-option label="仅中间体" value="intermediate"></el-option>
              <el-option label="仅配方" value="formula"></el-option>
              <el-option label="仅性能数据" value="performance"></el-option>
            </el-select>
          </div>
        </el-card>
      </div>

      <!-- 主内容区域 - 左右布局 -->
      <div class="main-content-layout">
        <!-- 左侧：搜索和表格区域 -->
        <el-card class="table-card">
          <div class="search-section">
            <el-input
              v-model="searchQuery"
              placeholder="搜索名称、编号或供应商等信息"
              clearable
              prefix-icon="el-icon-search"
              style="width: 100%; margin-bottom: 10px"
              @input="handleSearch"
              size="small"
            />
            <div style="display: flex; gap: 8px;">
              <el-select
                v-model="currentTab"
                placeholder="选择数据类型"
                style="flex: 1"
                size="small"
              >
                <el-option label="全部" value="all"></el-option>
                <el-option label="原材料" value="raw_material"></el-option>
                <el-option label="中间体" value="intermediate"></el-option>
                <el-option label="配方" value="formula"></el-option>
                <el-option label="性能数据" value="performance"></el-option>
              </el-select>
              <el-button
                type="primary"
                @click="handleSearch"
                size="small"
              >
                搜索
              </el-button>
            </div>
          </div>

          <el-tabs
            v-model="currentTab"
            @tab-click="handleTabChange"
            style="margin-top: 8px"
          >
            <el-tab-pane label="全部" name="all">
              <el-table
                :data="filteredNodes"
                style="width: 100%"
                @row-click="handleRowClick"
                height="730"
                size="small"
              >
                <el-table-column
                  prop="id"
                  label="ID"
                  width="120"
                  show-overflow-tooltip
                ></el-table-column>
                <el-table-column
                  prop="name"
                  label="名称"
                  width="180"
                  show-overflow-tooltip
                ></el-table-column>
                <el-table-column
                  prop="code"
                  label="编号"
                  width="120"
                  show-overflow-tooltip
                ></el-table-column>
                <el-table-column prop="type" label="类型" width="100">
                  <template #default="scope">
                    <el-tag :type="getNodeTypeColor(scope.row.type)" size="small">
                      {{ getNodeTypeLabel(scope.row.type) }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="data" label="详细信息" min-width="150" show-overflow-tooltip>
                <template #default="scope">
                  <div v-if="scope.row.type === 'raw_material'">
                    {{ scope.row.data.supplier || '-' }}
                  </div>
                  <div v-else-if="scope.row.type === 'intermediate'">
                    {{ scope.row.data.intermediate_type || '-' }}
                  </div>
                  <div v-else-if="scope.row.type === 'formula'">
                    {{ scope.row.data.application_type || '-' }}
                  </div>
                  <div v-else-if="scope.row.type === 'performance'">
                    评分: {{ scope.row.data.rating || '-' }}
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="text" @click="viewNodeDetails(scope.row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="原材料" name="raw_material">
            <el-table
              :data="filteredRawMaterials"
              style="width: 100%"
              @row-click="handleRowClick"
            >
              <el-table-column
                prop="id"
                label="ID"
                width="180"
              ></el-table-column>
              <el-table-column
                prop="name"
                label="名称"
                width="200"
              ></el-table-column>
              <el-table-column
                prop="code"
                label="编号"
                width="150"
              ></el-table-column>
              <el-table-column
                prop="data.material_type"
                label="材料类型"
                width="120"
              ></el-table-column>
              <el-table-column
                prop="data.supplier"
                label="供应商"
                width="150"
              ></el-table-column>
              <el-table-column prop="data.density" label="密度" width="100">
                <template #default="scope">
                  {{ scope.row.data.density || '-' }} g/cm³
                </template>
              </el-table-column>
              <el-table-column prop="data.unit_price" label="单价" width="100">
                <template #default="scope">
                  ¥{{ scope.row.data.unit_price || '-' }}/kg
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="text" @click="viewNodeDetails(scope.row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="中间体" name="intermediate">
            <el-table
              :data="filteredIntermediates"
              style="width: 100%"
              @row-click="handleRowClick"
            >
              <el-table-column
                prop="id"
                label="ID"
                width="180"
              ></el-table-column>
              <el-table-column
                prop="name"
                label="名称"
                width="200"
              ></el-table-column>
              <el-table-column
                prop="code"
                label="编号"
                width="150"
              ></el-table-column>
              <el-table-column
                prop="data.intermediate_type"
                label="中间体类型"
                width="150"
              ></el-table-column>
              <el-table-column prop="data.viscosity" label="粘度" width="100">
                <template #default="scope">
                  {{ scope.row.data.viscosity || '-' }} cps
                </template>
              </el-table-column>
              <el-table-column
                prop="data.solid_content"
                label="固含量"
                width="100"
              >
                <template #default="scope">
                  {{ scope.row.data.solid_content || '-' }}%
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="text" @click="viewNodeDetails(scope.row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="配方" name="formula">
            <el-table
              :data="filteredFormulas"
              style="width: 100%"
              @row-click="handleRowClick"
            >
              <el-table-column
                prop="id"
                label="ID"
                width="180"
              ></el-table-column>
              <el-table-column
                prop="name"
                label="名称"
                width="200"
              ></el-table-column>
              <el-table-column
                prop="code"
                label="编号"
                width="150"
              ></el-table-column>
              <el-table-column
                prop="data.version"
                label="版本"
                width="100"
              ></el-table-column>
              <el-table-column
                prop="data.status"
                label="状态"
                width="100"
              ></el-table-column>
              <el-table-column
                prop="data.application_type"
                label="应用类型"
                width="150"
              ></el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="text" @click="viewNodeDetails(scope.row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="性能数据" name="performance">
            <el-table
              :data="filteredPerformances"
              style="width: 100%"
              @row-click="handleRowClick"
            >
              <el-table-column
                prop="id"
                label="ID"
                width="180"
              ></el-table-column>
              <el-table-column
                prop="name"
                label="批次名称"
                width="200"
              ></el-table-column>
              <el-table-column
                prop="data.test_batch"
                label="测试批次"
                width="150"
              ></el-table-column>
              <el-table-column
                prop="data.test_date"
                label="测试日期"
                width="150"
              ></el-table-column>
              <el-table-column
                prop="data.tensile_strength"
                label="拉伸强度"
                width="120"
              >
                <template #default="scope">
                  {{ scope.row.data.tensile_strength || '-' }} MPa
                </template>
              </el-table-column>
              <el-table-column
                prop="data.elongation"
                label="断裂伸长率"
                width="120"
              >
                <template #default="scope">
                  {{ scope.row.data.elongation || '-' }}%
                </template>
              </el-table-column>
              <el-table-column prop="data.hardness" label="硬度" width="100">
                <template #default="scope">
                  {{ scope.row.data.hardness || '-' }} Shore A
                </template>
              </el-table-column>
              <el-table-column prop="data.rating" label="评分" width="80">
                <template #default="scope">
                  <el-rate
                    :value="Number(scope.row.data.rating) || 0"
                    disabled
                    :max="5"
                  ></el-rate>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="80">
                <template #default="scope">
                  <el-button type="text" @click="viewNodeDetails(scope.row)">
                    详情
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
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
            <el-descriptions-item label="编号">{{
              selectedNode.code
            }}</el-descriptions-item>
            <el-descriptions-item label="名称">{{
              selectedNode.name
            }}</el-descriptions-item>
            <el-descriptions-item label="类型">
              <el-tag :type="getNodeTypeColor(selectedNode.type)">
                {{ getNodeTypeLabel(selectedNode.type) }}
              </el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <div v-if="selectedNode.type === 'raw_material'" class="extra-info">
            <h3>原材料信息</h3>
            <p>
              <strong>材料类型:</strong> {{ selectedNode.material_type || '-' }}
            </p>
            <p>
              <strong>分子量:</strong>
              {{ selectedNode.molecular_weight || '-' }}
            </p>
            <p>
              <strong>密度:</strong> {{ selectedNode.density || '-' }} g/cm³
            </p>
            <p><strong>供应商:</strong> {{ selectedNode.supplier || '-' }}</p>
            <p>
              <strong>单价:</strong> ¥{{ selectedNode.unit_price || '-' }}/kg
            </p>
          </div>

          <div v-if="selectedNode.type === 'intermediate'" class="extra-info">
            <h3>中间体信息</h3>
            <p>
              <strong>中间体类型:</strong>
              {{ selectedNode.intermediate_type || '-' }}
            </p>
            <p>
              <strong>粘度:</strong> {{ selectedNode.viscosity || '-' }} cps
            </p>
            <p>
              <strong>固含量:</strong> {{ selectedNode.solid_content || '-' }}%
            </p>
          </div>

          <div v-if="selectedNode.type === 'formula'" class="extra-info">
            <h3>配方信息</h3>
            <p><strong>版本:</strong> {{ selectedNode.version || '-' }}</p>
            <p><strong>状态:</strong> {{ selectedNode.status || '-' }}</p>
            <p>
              <strong>应用类型:</strong>
              {{ selectedNode.application_type || '-' }}
            </p>
            <p>
              <strong>混合温度:</strong>
              {{ selectedNode.mixing_temperature || '-' }}°C
            </p>
            <p>
              <strong>固化时间:</strong> {{ selectedNode.curing_time || '-' }}h
            </p>
          </div>

          <div v-if="selectedNode.type === 'performance'" class="extra-info">
            <h3>性能测试数据</h3>
            <p>
              <strong>测试批次:</strong> {{ selectedNode.test_batch || '-' }}
            </p>
            <p>
              <strong>测试日期:</strong> {{ selectedNode.test_date || '-' }}
            </p>
            <p>
              <strong>拉伸强度:</strong>
              {{ selectedNode.tensile_strength || '-' }} MPa
            </p>
            <p>
              <strong>断裂伸长率:</strong>
              {{ selectedNode.elongation_at_break || '-' }}%
            </p>
            <p>
              <strong>撕裂强度:</strong>
              {{ selectedNode.tear_strength || '-' }} kN/m
            </p>
            <p>
              <strong>硬度:</strong> {{ selectedNode.hardness || '-' }} Shore A
            </p>
            <p>
              <strong>综合评分:</strong>
              {{ selectedNode.overall_rating || '-' }}/5
            </p>
          </div>
        </div>
      </el-drawer>

        <!-- 右侧：图谱可视化区域 -->
        <el-card class="graph-card" v-loading="loading">
          <div
            id="knowledge-graph"
            ref="graphContainer"
            style="width: 100%; height: 850px"
          ></div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script>
  import NavigationSidebar from '@/components/NavigationSidebar.vue'
  import { ref, onMounted, reactive, nextTick } from 'vue'
  import * as echarts from 'echarts'
  import apiClient from '@/utils/api'
  import { ElMessage } from 'element-plus'

  export default {
    name: 'KnowledgeGraph',
    components: {
      NavigationSidebar,
    },
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
        performances: 0,
      })

      const graphData = reactive({
        nodes: [],
        edges: [],
      })

      // 搜索和表格相关数据
      const searchQuery = ref('')
      const currentTab = ref('all')
      const filteredNodes = ref([])
      const filteredRawMaterials = ref([])
      const filteredIntermediates = ref([])
      const filteredFormulas = ref([])
      const filteredPerformances = ref([])

      // 节点类型映射
      const nodeTypeConfig = {
        raw_material: { label: '原材料', color: '#5470c6', symbol: 'circle' },
        intermediate: { label: '中间体', color: '#91cc75', symbol: 'rect' },
        formula: { label: '配方', color: '#fac858', symbol: 'roundRect' },
        performance: { label: '性能数据', color: '#ee6666', symbol: 'diamond' },
      }

      const getNodeTypeLabel = (type) => {
        return nodeTypeConfig[type]?.label || type
      }

      const getNodeTypeColor = (type) => {
        const colorMap = {
          raw_material: 'primary',
          intermediate: 'success',
          formula: 'warning',
          performance: 'danger',
        }
        return colorMap[type] || 'info'
      }

      // 加载图谱数据
      const loadGraphData = async () => {
        loading.value = true
        try {
          console.log('开始加载知识图谱数据...')
          const response = await apiClient.get(
            '/knowledgegraph/graph/full_graph/'
          )
          const data = response.data

          console.log('收到的数据:', data)
          console.log('节点数量:', data.nodes?.length || 0)
          console.log('边数量:', data.edges?.length || 0)

          graphData.nodes = data.nodes || []
          graphData.edges = data.edges || []

          // 如果没有数据，使用示例数据进行测试
          if (graphData.nodes.length === 0) {
            console.warn('后端返回空数据，使用示例数据')
            graphData.nodes = [
              {
                id: 'rm_1',
                name: '聚醚多元醇',
                type: 'raw_material',
                code: 'RM001',
                data: { supplier: '示例供应商' },
              },
              {
                id: 'rm_2',
                name: '异氰酸酯',
                type: 'raw_material',
                code: 'RM002',
                data: { supplier: '示例供应商2' },
              },
              {
                id: 'int_1',
                name: '预聚体',
                type: 'intermediate',
                code: 'INT001',
                data: { intermediate_type: '预聚体' },
              },
              {
                id: 'formula_1',
                name: '配方A',
                type: 'formula',
                code: 'F001',
                data: { version: '1.0' },
              },
              {
                id: 'perf_1',
                name: '性能测试1',
                type: 'performance',
                code: 'P001',
                data: { rating: 4.5 },
              },
            ]
            graphData.edges = [
              { source: 'rm_1', target: 'int_1', relation: '组成' },
              { source: 'rm_2', target: 'int_1', relation: '组成' },
              { source: 'int_1', target: 'formula_1', relation: '配方成分' },
              { source: 'formula_1', target: 'perf_1', relation: '性能数据' },
            ]
            ElMessage.warning('后端暂无数据，显示示例数据')
          }

          // 更新统计数据
          stats.rawMaterials = graphData.nodes.filter(
            (n) => n.type === 'raw_material'
          ).length
          stats.intermediates = graphData.nodes.filter(
            (n) => n.type === 'intermediate'
          ).length
          stats.formulas = graphData.nodes.filter(
            (n) => n.type === 'formula'
          ).length
          stats.performances = graphData.nodes.filter(
            (n) => n.type === 'performance'
          ).length

          console.log('统计数据:', stats)

          if (graphData.nodes.length > 0) {
            renderGraph()
            // 初始化过滤数据
            filterData()
            ElMessage.success(
              `知识图谱加载成功：${graphData.nodes.length}个节点，${graphData.edges.length}条边`
            )
          } else {
            ElMessage.warning('暂无图谱数据')
          }
        } catch (error) {
          console.error('加载图谱失败:', error)
          ElMessage.error(
            '加载图谱失败: ' + (error.response?.data?.message || error.message)
          )

          // API失败时也使用示例数据
          console.log('使用备用示例数据')
          graphData.nodes = [
            {
              id: 'rm_1',
              name: '聚醚多元醇',
              type: 'raw_material',
              code: 'RM001',
              data: { supplier: '示例供应商' },
            },
            {
              id: 'rm_2',
              name: '异氰酸酯',
              type: 'raw_material',
              code: 'RM002',
              data: { supplier: '示例供应商2' },
            },
            {
              id: 'int_1',
              name: '预聚体',
              type: 'intermediate',
              code: 'INT001',
              data: { intermediate_type: '预聚体' },
            },
            {
              id: 'formula_1',
              name: '配方A',
              type: 'formula',
              code: 'F001',
              data: { version: '1.0' },
            },
            {
              id: 'perf_1',
              name: '性能测试1',
              type: 'performance',
              code: 'P001',
              data: { rating: 4.5 },
            },
          ]
          graphData.edges = [
            { source: 'rm_1', target: 'int_1', relation: '组成' },
            { source: 'rm_2', target: 'int_1', relation: '组成' },
            { source: 'int_1', target: 'formula_1', relation: '配方成分' },
            { source: 'formula_1', target: 'perf_1', relation: '性能数据' },
          ]

          stats.rawMaterials = 2
          stats.intermediates = 1
          stats.formulas = 1
          stats.performances = 1

          renderGraph()
          filterData()
        } finally {
          loading.value = false
        }
      }

      // 渲染图谱 - 优化版本
      const renderGraph = () => {
        console.log('开始渲染图谱...')
        console.log('图谱容器:', graphContainer.value)
        console.log('节点数据:', graphData.nodes.length)
        console.log('边数据:', graphData.edges.length)
        console.log('当前视图模式:', viewMode.value)

        if (!graphContainer.value) {
          console.error('图谱容器未找到！')
          ElMessage.error('图谱容器初始化失败')
          return
        }

        if (graphData.nodes.length === 0) {
          console.warn('没有节点数据，跳过渲染')
          return
        }

        if (!chartInstance) {
          console.log('初始化ECharts实例...')
          chartInstance = echarts.init(graphContainer.value)
        }

        // 根据视图模式过滤节点
        let filteredNodesData = graphData.nodes
        let filteredEdgesData = graphData.edges

        if (viewMode.value !== 'full') {
          // 只显示选中类型的节点
          filteredNodesData = graphData.nodes.filter(
            (node) => node.type === viewMode.value
          )
          const nodeIds = new Set(filteredNodesData.map((n) => n.id))

          // 只显示连接选中类型节点的边
          filteredEdgesData = graphData.edges.filter(
            (edge) => nodeIds.has(edge.source) && nodeIds.has(edge.target)
          )

          console.log(
            `过滤后节点: ${filteredNodesData.length}, 边: ${filteredEdgesData.length}`
          )
        }

        // 计算节点大小（基于连接数）
        const getNodeSize = (nodeId, nodeType) => {
          const connections = filteredEdgesData.filter(
            (e) => e.source === nodeId || e.target === nodeId
          ).length
          const baseSize =
            {
              raw_material: 35,
              intermediate: 40,
              formula: 50,
              performance: 30,
            }[nodeType] || 35

          return Math.max(baseSize, Math.min(baseSize + connections * 5, 80))
        }

        // 创建类别映射
        const categoryMap = {
          raw_material: 0,
          intermediate: 1,
          formula: 2,
          performance: 3,
        }

        // 节点样式优化 - 使用过滤后的数据
        const nodes = filteredNodesData.map((node) => ({
          id: node.id,
          name: node.name,
          symbolSize: getNodeSize(node.id, node.type),
          symbol: nodeTypeConfig[node.type]?.symbol || 'circle',
          itemStyle: {
            color: nodeTypeConfig[node.type]?.color || '#999',
            borderColor: '#fff',
            borderWidth: 2,
            shadowBlur: 10,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
          label: {
            show: true,
            fontSize: 11,
            fontWeight: 'bold',
            color: '#333',
            formatter: (params) => {
              // 限制标签长度
              const name = params.data.name
              return name.length > 15 ? name.substring(0, 12) + '...' : name
            },
            position: 'bottom',
            distance: 5,
          },
          category: categoryMap[node.type] || 0, // 使用索引而非字符串
          value: node, // 保存原始数据
          data: node, // 也保存在data中以便访问
        }))

        // 边样式优化 - 使用过滤后的数据
        const edges = filteredEdgesData.map((edge) => ({
          source: edge.source,
          target: edge.target,
          label: {
            show: false, // 默认隐藏边标签，鼠标悬停时显示
            formatter: edge.relation || '',
            fontSize: 10,
            color: '#666',
          },
          lineStyle: {
            color: '#ccc',
            width: 1.5,
            curveness: 0.3,
            opacity: 0.6,
          },
          emphasis: {
            label: {
              show: true,
            },
            lineStyle: {
              width: 3,
              opacity: 1,
            },
          },
        }))

        // 创建类别用于图例
        const categories = [
          { name: '原材料', itemStyle: { color: '#5470c6' } },
          { name: '中间体', itemStyle: { color: '#91cc75' } },
          { name: '配方', itemStyle: { color: '#fac858' } },
          { name: '性能数据', itemStyle: { color: '#ee6666' } },
        ]

        const option = {
          title: {
            text: '材料知识图谱',
            subtext: '原材料 → 中间体 → 配方 → 性能',
            left: 'center',
            top: 20,
            textStyle: {
              fontSize: 26,
              fontWeight: 'bold',
              color: '#2c3e50',
            },
            subtextStyle: {
              fontSize: 15,
              color: '#7f8c8d',
            },
          },
          tooltip: {
            trigger: 'item',
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            borderColor: '#ddd',
            borderWidth: 1,
            textStyle: {
              color: '#333',
            },
            formatter: (params) => {
              if (params.dataType === 'node') {
                const node = params.data.value || params.data // 兼容两种数据格式
                let html = `<div style="padding: 10px;">
                <h4 style="margin: 0 0 10px 0; color: ${
                  nodeTypeConfig[node.type]?.color
                };">
                  ${node.name}
                </h4>
                <p style="margin: 5px 0;"><strong>类型:</strong> ${getNodeTypeLabel(
                  node.type
                )}</p>
                <p style="margin: 5px 0;"><strong>编号:</strong> ${
                  node.code || '-'
                }</p>`

                // 根据节点类型显示额外信息
                if (node.type === 'raw_material' && node.data) {
                  html += `<p style="margin: 5px 0;"><strong>供应商:</strong> ${
                    node.data.supplier || '-'
                  }</p>`
                } else if (node.type === 'intermediate' && node.data) {
                  html += `<p style="margin: 5px 0;"><strong>固含量:</strong> ${
                    node.data.solid_content || '-'
                  }%</p>`
                } else if (node.type === 'formula' && node.data) {
                  html += `<p style="margin: 5px 0;"><strong>版本:</strong> ${
                    node.data.version || '-'
                  }</p>`
                } else if (node.type === 'performance' && node.data) {
                  html += `<p style="margin: 5px 0;"><strong>评分:</strong> ${
                    node.data.rating || '-'
                  }/5</p>`
                }

                html += `<p style="margin: 5px 0; color: #888; font-size: 12px;">点击查看详细信息</p></div>`
                return html
              } else if (params.dataType === 'edge') {
                return `<div style="padding: 8px;">
                <strong>关系:</strong> ${params.data.label.formatter || '关联'}
              </div>`
              }
              return ''
            },
          },
          legend: {
            data: categories.map((c) => c.name),
            orient: 'vertical',
            right: 20,
            top: 80,
            itemGap: 15,
            itemWidth: 20,
            itemHeight: 14,
            textStyle: {
              fontSize: 13,
              color: '#666',
            },
          },
          animationDuration: 1500,
          animationEasingUpdate: 'quinticInOut',
          series: [
            {
              type: 'graph',
              layout: 'force',
              data: nodes,
              links: edges,
              categories: categories,
              roam: true,
              draggable: true,
              label: {
                show: true,
              },
              force: {
                repulsion: 300, // 增加斥力，避免节点重叠
                gravity: 0.05, // 重力
                edgeLength: [100, 200], // 边长度范围
                layoutAnimation: true,
                friction: 0.6, // 摩擦力
              },
              emphasis: {
                focus: 'adjacency',
                blurScope: 'coordinateSystem',
                lineStyle: {
                  width: 4,
                  shadowBlur: 10,
                  shadowColor: 'rgba(0, 0, 0, 0.5)',
                },
                itemStyle: {
                  shadowBlur: 15,
                  shadowColor: 'rgba(0, 0, 0, 0.5)',
                },
              },
              lineStyle: {
                color: 'source',
                curveness: 0.3,
              },
              scaleLimit: {
                min: 0.5,
                max: 3,
              },
            },
          ],
        }

        console.log('ECharts配置选项:', option)
        console.log('节点数量:', nodes.length)
        console.log('边数量:', edges.length)

        try {
          chartInstance.setOption(option, true)
          console.log('图谱渲染成功！')
        } catch (error) {
          console.error('设置ECharts选项失败:', error)
          ElMessage.error('图谱渲染失败: ' + error.message)
        }

        // 点击节点显示详情
        chartInstance.off('click')
        chartInstance.on('click', (params) => {
          if (params.dataType === 'node') {
            const nodeData = params.data.value || params.data // 兼容两种数据格式
            selectedNode.value = nodeData
            drawerVisible.value = true
          }
        })

        // 鼠标悬停高亮效果
        chartInstance.off('mouseover')
        chartInstance.on('mouseover', (params) => {
          if (params.dataType === 'node') {
            chartInstance.dispatchAction({
              type: 'highlight',
              seriesIndex: 0,
              dataIndex: params.dataIndex,
            })
          }
        })

        chartInstance.off('mouseout')
        chartInstance.on('mouseout', (params) => {
          if (params.dataType === 'node') {
            chartInstance.dispatchAction({
              type: 'downplay',
              seriesIndex: 0,
              dataIndex: params.dataIndex,
            })
          }
        })
      }

      const resetView = () => {
        if (chartInstance) {
          chartInstance.setOption({
            series: [
              {
                data: graphData.nodes,
                links: graphData.edges,
              },
            ],
          })
        }
      }

      // 处理搜索
      const handleSearch = () => {
        filterData()
      }

      // 处理标签页切换
      const handleTabChange = () => {
        filterData()
      }

      // 过滤数据
      const filterData = () => {
        const query = searchQuery.value.toLowerCase().trim()

        // 全部节点过滤
        filteredNodes.value = graphData.nodes.filter((node) => {
          if (currentTab.value !== 'all' && node.type !== currentTab.value) {
            return false
          }
          return matchesSearch(node, query)
        })

        // 分类过滤
        filteredRawMaterials.value = graphData.nodes.filter(
          (node) => node.type === 'raw_material' && matchesSearch(node, query)
        )

        filteredIntermediates.value = graphData.nodes.filter(
          (node) => node.type === 'intermediate' && matchesSearch(node, query)
        )

        filteredFormulas.value = graphData.nodes.filter(
          (node) => node.type === 'formula' && matchesSearch(node, query)
        )

        filteredPerformances.value = graphData.nodes.filter(
          (node) => node.type === 'performance' && matchesSearch(node, query)
        )
      }

      // 模糊搜索匹配
      const matchesSearch = (node, query) => {
        if (!query) return true

        // 检查基本字段
        if (
          node.name?.toLowerCase().includes(query) ||
          node.code?.toLowerCase().includes(query)
        ) {
          return true
        }

        // 检查数据对象中的字段
        if (node.data) {
          const dataValues = Object.values(node.data)
          return dataValues.some(
            (value) =>
              value &&
              typeof value === 'string' &&
              value.toLowerCase().includes(query)
          )
        }

        return false
      }

      // 查看节点详情 - 统一处理表格和图谱点击
      const viewNodeDetails = (node) => {
        if (node && node.id) {
          // 从原始数据中查找完整的节点信息，确保包含所有详情
          const fullNode = graphData.nodes.find((n) => n.id === node.id)
          if (fullNode) {
            // 使用原始节点数据，确保包含所有详细信息
            selectedNode.value = fullNode
          } else {
            // 如果找不到完整节点，使用现有节点
            selectedNode.value = node
          }
        }
        drawerVisible.value = true

        // 找到并高亮对应节点
        if (chartInstance && node && node.id) {
          const nodeIndex = graphData.nodes.findIndex((n) => n.id === node.id)
          if (nodeIndex !== -1) {
            // 清除之前的高亮
            chartInstance.dispatchAction({
              type: 'downplay',
              seriesIndex: 0,
              dataIndex: null,
            })
            // 高亮当前节点
            chartInstance.dispatchAction({
              type: 'highlight',
              seriesIndex: 0,
              dataIndex: nodeIndex,
            })
          }
        }
      }

      // 表格行点击
      const handleRowClick = (row) => {
        viewNodeDetails(row)
      }

      // 处理视图模式切换
      const handleViewModeChange = (value) => {
        console.log('切换视图模式:', value)

        // 根据视图模式显示提示
        const modeLabels = {
          full: '完整图谱',
          raw_material: '仅原材料',
          intermediate: '仅中间体',
          formula: '仅配方',
          performance: '仅性能数据',
        }

        ElMessage.info(`切换到: ${modeLabels[value] || value}`)

        // 重新渲染图谱
        if (graphData.nodes.length > 0) {
          renderGraph()
        }
      }

      onMounted(async () => {
        console.log('组件已挂载，开始初始化...')

        // 等待DOM完全渲染
        await nextTick()

        console.log('DOM已渲染，容器元素:', graphContainer.value)

        // 加载数据
        await loadGraphData()

        // 添加窗口resize事件监听
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
        getNodeTypeColor,
        // 搜索和表格相关
        searchQuery,
        currentTab,
        filteredNodes,
        filteredRawMaterials,
        filteredIntermediates,
        filteredFormulas,
        filteredPerformances,
        handleSearch,
        handleTabChange,
        viewNodeDetails,
        handleRowClick,
        handleViewModeChange,
      }
    },
  }
</script>

<style scoped>
  .knowledge-graph-page-wrapper {
    display: flex;
    height: 100vh;
  }

  .knowledge-graph-container {
    flex: 1;
    overflow-y: auto;
    padding: 20px 60px;
    max-width: 100%;
    width: 100%;
    margin: 0 auto;
    background: linear-gradient(135deg, #f5f7fa 0%, #e8edf3 100%);
    min-height: 100vh;
  }

  .header {
    text-align: center;
    margin-bottom: 30px;
    padding: 30px 0;
    background: white;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .header h1 {
    font-size: 2.8rem;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 10px;
    font-weight: 700;
  }

  .subtitle {
    color: #666;
    font-size: 1.2rem;
    font-weight: 500;
  }

  .control-panel {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 20px;
    margin-bottom: 20px;
  }

  /* 主内容左右布局 */
  .main-content-layout {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
    align-items: start;
  }

  /* 统一左右两侧高度 */
  .table-card,
  .graph-card {
    height: 850px;
  }

  .stats-card {
    background: white;
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .stats-card :deep(.el-card__body) {
    padding: 25px;
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
    padding: 20px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 12px;
    transition: all 0.3s ease;
    border: 2px solid transparent;
  }

  .stat-item:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(102, 126, 234, 0.2);
    border-color: #667eea;
  }

  .stat-icon {
    font-size: 3rem;
    filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
  }

  .stat-value {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }

  .stat-label {
    color: #666;
    font-size: 0.95rem;
    font-weight: 500;
  }

  .filter-card {
    display: flex;
    align-items: center;
    background: white;
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  }

  .filter-card :deep(.el-card__body) {
    padding: 25px;
    width: 100%;
  }

  .filter-controls {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    width: 100%;
    align-items: center;
  }

  .filter-controls .el-button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.3s ease;
  }

  .filter-controls .el-button--primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
  }

  .filter-controls .el-button--primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
  }

  .graph-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 6px 30px rgba(0, 0, 0, 0.1);
    background: white;
    overflow: hidden;
  }

  .graph-card :deep(.el-card__body) {
    padding: 0;
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  #knowledge-graph {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    flex: 1;
  }

  .table-card {
    border: none;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    background: white;
    display: flex;
    flex-direction: column;
  }

  .table-card :deep(.el-card__body) {
    padding: 16px;
    height: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .table-card :deep(.el-tabs) {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .table-card :deep(.el-tabs__content) {
    flex: 1;
    overflow: hidden;
  }

  .search-section {
    display: flex;
    flex-direction: column;
    margin-bottom: 15px;
    padding: 12px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 8px;
  }

  .search-section .el-input {
    border-radius: 6px;
  }

  .search-section .el-button {
    border-radius: 8px;
    font-weight: 500;
  }

  .el-table {
    margin-top: 10px;
    border-radius: 8px;
    overflow: hidden;
  }

  .el-table :deep(th) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    font-weight: 600;
  }

  .el-table :deep(tr:hover) {
    background-color: rgba(102, 126, 234, 0.05);
  }

  .el-table .el-button--text {
    color: #667eea;
    font-weight: 500;
  }

  .el-table .el-button--text:hover {
    color: #764ba2;
  }

  .node-details {
    padding: 20px;
  }

  .node-details :deep(.el-descriptions__label) {
    font-weight: 600;
    color: #667eea;
  }

  .extra-info {
    margin-top: 25px;
    padding: 20px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    border-radius: 10px;
    border-left: 4px solid #667eea;
  }

  .extra-info h3 {
    color: #667eea;
    margin-bottom: 15px;
    font-size: 1.2rem;
    font-weight: 600;
  }

  .extra-info p {
    margin: 12px 0;
    line-height: 1.8;
    color: #555;
  }

  .extra-info strong {
    color: #333;
    font-weight: 600;
    min-width: 100px;
    display: inline-block;
  }

  /* 抽屉样式优化 */
  :deep(.el-drawer__header) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    margin-bottom: 0;
  }

  :deep(.el-drawer__title) {
    color: white;
    font-size: 1.3rem;
    font-weight: 600;
  }

  :deep(.el-drawer__close-btn) {
    color: white;
    font-size: 1.5rem;
  }

  /* 标签页样式优化 */
  :deep(.el-tabs__item) {
    font-size: 15px;
    font-weight: 500;
  }

  :deep(.el-tabs__item.is-active) {
    color: #667eea;
    font-weight: 600;
  }

  :deep(.el-tabs__active-bar) {
    background-color: #667eea;
  }

  /* Tag样式优化 */
  :deep(.el-tag) {
    border-radius: 6px;
    font-weight: 500;
    padding: 0 12px;
  }

  /* 响应式设计 */
  @media (max-width: 1200px) {
    .knowledge-graph-container {
      max-width: 100%;
    }
  }

  @media (max-width: 1400px) {
    .main-content-layout {
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
  }

  @media (max-width: 1200px) {
    .knowledge-graph-container {
      padding: 20px 30px;
    }

    .main-content-layout {
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
  }

  @media (max-width: 768px) {
    .control-panel {
      grid-template-columns: 1fr;
    }

    .knowledge-graph-container {
      padding: 15px;
    }

    .main-content-layout {
      grid-template-columns: 1fr;
    }

    .graph-card {
      position: static;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
      gap: 10px;
    }

    .stat-item {
      padding: 15px;
      gap: 10px;
    }

    .stat-icon {
      font-size: 2rem;
    }

    .stat-value {
      font-size: 1.5rem;
    }

    .header h1 {
      font-size: 2rem;
    }

    .subtitle {
      font-size: 1rem;
    }

    #knowledge-graph {
      height: 500px !important;
    }
  }
</style>
