<template>
  <div class="paper-form">
    <section class="section-block">
      <div class="section-head">
        <div class="section-title">基本信息</div>
        <el-button text size="small" @click="toggleSection('basic')">
          {{ isSectionCollapsed('basic') ? '展开' : '折叠' }}
        </el-button>
      </div>
      <div v-show="!isSectionCollapsed('basic')" class="basic-grid">
        <label class="field-card">
          <span class="field-label">文献编号</span>
          <el-input
            v-model="localData.basic_info.article_id"
            :readonly="readonly"
            type="textarea"
            :rows="2"
            resize="none"
            class="scroll-box scroll-box-sm"
          />
        </label>
        <label class="field-card">
          <span class="field-label">文献出版年份</span>
          <el-input
            v-model="localData.basic_info.publish_year"
            :readonly="readonly"
            type="textarea"
            :rows="2"
            resize="none"
            class="scroll-box scroll-box-sm"
          />
        </label>
        <label class="field-card field-card-wide">
          <span class="field-label">文献名称</span>
          <el-input
            v-model="localData.basic_info.article_name"
            :readonly="readonly"
            type="textarea"
            resize="none"
            :rows="3"
            class="scroll-box scroll-box-md"
          />
        </label>
        <label class="field-card field-card-wide">
          <span class="field-label">文献 DOI 号</span>
          <el-input
            v-model="localData.basic_info.article_doi"
            :readonly="readonly"
            type="textarea"
            resize="none"
            :rows="3"
            class="scroll-box scroll-box-md"
          />
        </label>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head">
        <div class="section-title">原材料</div>
        <div class="section-actions">
          <el-button text size="small" @click="toggleSection('materials')">
            {{ isSectionCollapsed('materials') ? '展开' : '折叠' }}
          </el-button>
          <el-button v-if="!readonly" size="small" type="primary" @click="addMaterial">新增行</el-button>
        </div>
      </div>
      <div v-show="!isSectionCollapsed('materials')" class="table-wrap">
        <table class="grid-table" :style="{ minWidth: materialTableMinWidth }">
          <thead>
            <tr>
              <th class="short-col">原料编号</th>
              <th class="medium-col">原料名称</th>
              <th class="wide-col">原料特性</th>
              <th class="medium-col">CAS</th>
              <th v-if="!readonly" class="action-col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in localData.materials" :key="`material-${index}`">
              <td class="short-col">
                <el-input
                  v-model="item.material_id"
                  :readonly="readonly"
                  type="textarea"
                  :rows="2"
                  resize="none"
                  class="scroll-box scroll-box-sm"
                />
              </td>
              <td class="medium-col">
                <el-input
                  v-model="item.material_name"
                  :readonly="readonly"
                  type="textarea"
                  resize="none"
                  :rows="3"
                  class="scroll-box scroll-box-md"
                />
              </td>
              <td class="wide-col">
                <el-input
                  v-model="item.material_characteristic"
                  :readonly="readonly"
                  type="textarea"
                  resize="none"
                  :rows="4"
                  class="scroll-box scroll-box-lg"
                />
              </td>
              <td class="medium-col">
                <el-input
                  v-model="item.cas_number"
                  :readonly="readonly"
                  type="textarea"
                  resize="none"
                  :rows="2"
                  class="scroll-box scroll-box-sm"
                />
              </td>
              <td v-if="!readonly" class="action-col">
                <el-button text type="danger" size="small" @click="removeMaterial(index)">删除</el-button>
              </td>
            </tr>
            <tr v-if="!localData.materials.length">
              <td :colspan="readonly ? 4 : 5" class="empty-cell">暂无原材料数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head">
        <div class="section-title">制备工艺</div>
        <el-button text size="small" @click="toggleSection('process')">
          {{ isSectionCollapsed('process') ? '展开' : '折叠' }}
        </el-button>
      </div>
      <el-input
        v-show="!isSectionCollapsed('process')"
        v-model="localData.preparation_process"
        :readonly="readonly"
        type="textarea"
        resize="none"
        :rows="7"
        class="scroll-box scroll-box-xl"
        placeholder="自动识别文章中的制备工艺描述"
      />
    </section>

    <section class="section-block">
      <div class="section-head">
        <div class="section-title">中间体</div>
        <div class="section-actions">
          <el-button text size="small" @click="toggleSection('intermediates')">
            {{ isSectionCollapsed('intermediates') ? '展开' : '折叠' }}
          </el-button>
          <el-button v-if="!readonly" size="small" type="primary" @click="addIntermediate">新增行</el-button>
        </div>
      </div>
      <div v-show="!isSectionCollapsed('intermediates')" class="table-wrap">
        <table class="grid-table" :style="{ minWidth: intermediateTableMinWidth }">
          <thead>
            <tr>
              <th class="short-col">中间体编号</th>
              <th class="wide-col">配方</th>
              <th v-if="!readonly" class="action-col">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in localData.intermediates" :key="`intermediate-${index}`">
              <td class="short-col">
                <el-input
                  v-model="item.intermediate_id"
                  :readonly="readonly"
                  type="textarea"
                  :rows="2"
                  resize="none"
                  class="scroll-box scroll-box-sm"
                />
              </td>
              <td class="wide-col">
                <el-input
                  v-model="item.formula"
                  :readonly="readonly"
                  type="textarea"
                  resize="none"
                  :rows="4"
                  class="scroll-box scroll-box-lg"
                />
              </td>
              <td v-if="!readonly" class="action-col">
                <el-button text type="danger" size="small" @click="removeIntermediate(index)">删除</el-button>
              </td>
            </tr>
            <tr v-if="!localData.intermediates.length">
              <td :colspan="readonly ? 2 : 3" class="empty-cell">暂无中间体数据</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head">
        <div class="section-title">性能</div>
        <div class="section-actions">
          <el-button text size="small" @click="toggleSection('properties')">
            {{ isSectionCollapsed('properties') ? '展开' : '折叠' }}
          </el-button>
          <el-button v-if="!readonly" size="small" @click="addPropertyColumn">新增性能列</el-button>
          <el-button v-if="!readonly" size="small" type="primary" @click="addPropertyRow">新增行</el-button>
        </div>
      </div>
      <div v-show="!isSectionCollapsed('properties')" class="performance-layout">
        <div v-if="localData.properties.columns.length" class="metric-config-grid">
          <div v-for="(column, index) in localData.properties.columns" :key="column.key" class="metric-config-item">
            <span class="field-label">性能名称 {{ index + 1 }}</span>
            <el-input
              v-model="column.name"
              :readonly="readonly"
              placeholder="性能名称"
              type="textarea"
              resize="none"
              :rows="2"
              class="scroll-box scroll-box-sm"
            />
            <el-button v-if="!readonly" text type="danger" size="small" @click="removePropertyColumn(index)">
              删除此列
            </el-button>
          </div>
        </div>
        <div v-else class="empty-cell">暂无性能列</div>

        <div v-if="localData.properties.rows.length" class="property-row-list">
          <div v-for="(row, rowIndex) in localData.properties.rows" :key="`property-row-${rowIndex}`" class="property-card">
            <div class="property-card-head">
              <span class="property-card-title">性能记录 {{ rowIndex + 1 }}</span>
              <el-button v-if="!readonly" text type="danger" size="small" @click="removePropertyRow(rowIndex)">删除</el-button>
            </div>
            <label class="field-card">
              <span class="field-label">产物（中间体配比）</span>
              <el-input
                v-model="row.product_name"
                :readonly="readonly"
                type="textarea"
                resize="none"
                :rows="4"
                class="scroll-box scroll-box-lg"
              />
            </label>
            <div class="metric-value-grid">
              <label v-for="column in localData.properties.columns" :key="`${rowIndex}-${column.key}`" class="field-card">
                <span class="field-label">{{ column.name || '性能值' }}</span>
                <el-input
                  v-model="row.values[column.key]"
                  :readonly="readonly"
                  type="textarea"
                  resize="none"
                  :rows="4"
                  class="scroll-box scroll-box-lg"
                />
              </label>
            </div>
          </div>
        </div>
        <div v-else class="empty-cell">暂无性能数据</div>
      </div>
    </section>

    <section class="section-block">
      <div class="section-head">
        <div class="section-title">备注</div>
        <el-button text size="small" @click="toggleSection('notes')">
          {{ isSectionCollapsed('notes') ? '展开' : '折叠' }}
        </el-button>
      </div>
      <el-input
        v-show="!isSectionCollapsed('notes')"
        v-model="localData.notes"
        :readonly="readonly"
        type="textarea"
        resize="none"
        :rows="7"
        class="scroll-box scroll-box-xl"
        placeholder="例如规律性结论、补充说明等"
      />
    </section>
  </div>
</template>

<script setup>
import { computed, reactive, watch } from 'vue'
import { createPaperTemplate, normalizePaperData } from '@/views/ocr/paperTemplate'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => createPaperTemplate(''),
  },
  readonly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const localData = reactive(createPaperTemplate(''))
const collapsedSections = reactive({
  basic: false,
  materials: false,
  process: false,
  intermediates: false,
  properties: false,
  notes: false,
})
let syncingFromProps = false
let columnSeed = 1
let previousArticleCode = ''

const materialTableMinWidth = computed(() => (props.readonly ? '880px' : '960px'))
const intermediateTableMinWidth = computed(() => (props.readonly ? '720px' : '800px'))

const nextColumnKey = () => {
  const key = `metric_${columnSeed}`
  columnSeed += 1
  return key
}

const ensurePropertyShape = () => {
  if (!localData.properties || typeof localData.properties !== 'object') {
    localData.properties = { columns: [], rows: [] }
  }
  if (!Array.isArray(localData.properties.columns)) {
    localData.properties.columns = []
  }
  if (!Array.isArray(localData.properties.rows)) {
    localData.properties.rows = []
  }
}

const toggleSection = (sectionKey) => {
  collapsedSections[sectionKey] = !collapsedSections[sectionKey]
}

const isSectionCollapsed = (sectionKey) => Boolean(collapsedSections[sectionKey])

const escapeRegExp = (value) => String(value).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

const articleCode = () => String(localData.basic_info?.article_id || '').trim()

const nextGeneratedId = (rows, fieldName, suffix) => {
  const baseCode = articleCode()
  if (!baseCode) return ''

  const pattern = new RegExp(`^${escapeRegExp(baseCode)}${suffix}-(\\d+)$`, 'i')
  const maxIndex = rows.reduce((maxValue, row) => {
    const current = String(row?.[fieldName] || '').trim()
    const matched = current.match(pattern)
    return matched ? Math.max(maxValue, Number(matched[1]) || 0) : maxValue
  }, 0)

  return `${baseCode}${suffix}-${maxIndex + 1}`
}

const nextMaterialId = () => nextGeneratedId(localData.materials, 'material_id', 'M')
const nextIntermediateId = () => nextGeneratedId(localData.intermediates, 'intermediate_id', 'IM')

const isGeneratedId = (value, baseCode, suffix) => {
  const text = String(value || '').trim()
  if (!text) return true
  if (!baseCode) return false
  return new RegExp(`^${escapeRegExp(baseCode)}${suffix}-\\d+$`, 'i').test(text)
}

const refreshGeneratedIdsForArticle = (nextCode, previousCode) => {
  if (!nextCode) return

  localData.materials.forEach((row, index) => {
    if (isGeneratedId(row.material_id, previousCode, 'M')) {
      row.material_id = `${nextCode}M-${index + 1}`
    }
  })

  localData.intermediates.forEach((row, index) => {
    if (isGeneratedId(row.intermediate_id, previousCode, 'IM')) {
      row.intermediate_id = `${nextCode}IM-${index + 1}`
    }
  })
}

const syncFromProps = (value) => {
  syncingFromProps = true
  const normalized = normalizePaperData(value || {}, '')
  localData.template_type = normalized.template_type
  localData.basic_info = JSON.parse(JSON.stringify(normalized.basic_info))
  localData.materials = JSON.parse(JSON.stringify(normalized.materials))
  localData.preparation_process = normalized.preparation_process
  localData.intermediates = JSON.parse(JSON.stringify(normalized.intermediates))
  localData.properties = JSON.parse(JSON.stringify(normalized.properties))
  localData.notes = normalized.notes

  const maxSeed = normalized.properties.columns.reduce((maxValue, column) => {
    const matched = String(column.key || '').match(/metric_(\d+)/)
    return matched ? Math.max(maxValue, Number(matched[1])) : maxValue
  }, 0)
  columnSeed = maxSeed + 1
  previousArticleCode = articleCode()
  refreshGeneratedIdsForArticle(previousArticleCode, '')

  queueMicrotask(() => {
    syncingFromProps = false
  })
}

watch(
  () => props.modelValue,
  (value) => syncFromProps(value),
  { immediate: true, deep: true },
)

watch(
  localData,
  () => {
    if (syncingFromProps) return
    emit('update:modelValue', JSON.parse(JSON.stringify(localData)))
  },
  { deep: true },
)

watch(
  () => localData.basic_info.article_id,
  (nextValue, previousValue) => {
    if (syncingFromProps) return

    const nextCode = String(nextValue || '').trim()
    const oldCode = String(previousValue || previousArticleCode || '').trim()
    refreshGeneratedIdsForArticle(nextCode, oldCode)
    previousArticleCode = nextCode
  },
)

const addMaterial = () => {
  localData.materials.push({
    material_id: nextMaterialId(),
    material_name: '',
    material_characteristic: '',
    cas_number: '',
  })
}

const removeMaterial = (index) => {
  localData.materials.splice(index, 1)
}

const addIntermediate = () => {
  localData.intermediates.push({
    intermediate_id: nextIntermediateId(),
    formula: '',
  })
}

const removeIntermediate = (index) => {
  localData.intermediates.splice(index, 1)
}

const addPropertyColumn = () => {
  ensurePropertyShape()
  const key = nextColumnKey()
  localData.properties.columns.push({
    key,
    name: '',
  })
  localData.properties.rows.forEach((row) => {
    if (!row.values || typeof row.values !== 'object') {
      row.values = {}
    }
    row.values[key] = ''
  })
}

const removePropertyColumn = (index) => {
  ensurePropertyShape()
  const [removed] = localData.properties.columns.splice(index, 1)
  if (!removed) return
  localData.properties.rows.forEach((row) => {
    if (row.values && typeof row.values === 'object') {
      delete row.values[removed.key]
    }
  })
}

const addPropertyRow = () => {
  ensurePropertyShape()
  const values = {}
  localData.properties.columns.forEach((column) => {
    values[column.key] = ''
  })
  localData.properties.rows.push({
    product_name: '',
    values,
  })
}

const removePropertyRow = (index) => {
  localData.properties.rows.splice(index, 1)
}
</script>

<style scoped>
.paper-form {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-width: 0;
  max-width: 100%;
}

.section-block {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #fbfcfe;
  min-width: 0;
  max-width: 100%;
  box-sizing: border-box;
}

.section-title {
  color: #0f172a;
  font-size: 16px;
  font-weight: 600;
}

.section-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.section-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.basic-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(220px, 1fr));
  gap: 10px;
}

.field-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-card-wide {
  grid-column: span 2;
}

.field-label {
  color: #475569;
  font-size: 13px;
}

.table-wrap {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  max-width: 100%;
}

.grid-table {
  width: 100%;
  border-collapse: collapse;
  table-layout: fixed;
}

.grid-table th,
.grid-table td {
  border: 1px solid #dbe4f0;
  padding: 8px;
  vertical-align: top;
  background: #fff;
  word-break: break-word;
  overflow-wrap: anywhere;
}

.grid-table th {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}

.short-col {
  width: 160px;
  min-width: 160px;
}

.medium-col {
  width: 220px;
  min-width: 220px;
}

.wide-col {
  width: 320px;
  min-width: 320px;
}

.action-col {
  width: 88px;
  min-width: 88px;
  text-align: center;
  white-space: nowrap;
}

.empty-cell {
  color: #94a3b8;
  text-align: center;
  padding: 18px 12px;
}

.performance-layout {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 0;
}

.metric-config-grid,
.metric-value-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 10px;
  min-width: 0;
}

.metric-config-item,
.property-card {
  border: 1px solid #dbe4f0;
  border-radius: 8px;
  background: #fff;
  padding: 10px;
  min-width: 0;
  box-sizing: border-box;
}

.metric-config-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.property-row-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.property-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.property-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.property-card-title {
  color: #0f172a;
  font-size: 14px;
  font-weight: 600;
}

.paper-form :deep(.el-input__wrapper) {
  align-items: flex-start;
  min-height: 34px;
  width: 100%;
  box-sizing: border-box;
}

.paper-form :deep(.scroll-box) {
  width: 100%;
}

.paper-form :deep(.el-textarea__inner) {
  line-height: 1.5;
  word-break: break-word;
  overflow-wrap: anywhere;
  padding-top: 6px;
  padding-bottom: 6px;
  width: 100%;
  box-sizing: border-box;
  overflow: auto;
}

.paper-form :deep(.scroll-box-sm .el-textarea__inner) {
  min-height: 54px;
  max-height: 54px;
}

.paper-form :deep(.scroll-box-md .el-textarea__inner) {
  min-height: 76px;
  max-height: 76px;
}

.paper-form :deep(.scroll-box-lg .el-textarea__inner) {
  min-height: 98px;
  max-height: 98px;
}

.paper-form :deep(.scroll-box-xl .el-textarea__inner) {
  min-height: 146px;
  max-height: 146px;
}

@media (max-width: 1100px) {
  .basic-grid {
    grid-template-columns: 1fr;
  }

  .field-card-wide {
    grid-column: auto;
  }
}
</style>
