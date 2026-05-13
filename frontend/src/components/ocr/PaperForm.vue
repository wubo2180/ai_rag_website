<template>
  <div class="paper-form">
    <el-form label-width="110px" label-position="left">
      <el-form-item label="文献编号">
        <el-input v-model="localData.article_id" :readonly="readonly" placeholder="如 A-3K7M9" />
      </el-form-item>
      <el-form-item label="文献名称">
        <el-input v-model="localData.article_name" :readonly="readonly" type="textarea" :rows="2" />
      </el-form-item>
      <el-form-item label="性能趋势">
        <el-input v-model="localData.performance_trend" :readonly="readonly" type="textarea" :rows="3" />
      </el-form-item>

      <div class="section-title">四级数据链（{{ localData.hierarchical_data.length }}）</div>
      <div class="actions" v-if="!readonly">
        <el-button size="small" type="primary" @click="addMaterial">添加材料/中间体</el-button>
      </div>

      <div
        v-for="(item, idx) in localData.hierarchical_data"
        :key="idx"
        class="material-card"
      >
        <div class="card-head">
          <strong>材料/中间体 #{{ idx + 1 }}</strong>
          <el-button v-if="!readonly" text type="danger" size="small" @click="removeMaterial(idx)">删除</el-button>
        </div>

        <div class="grid two-col">
          <el-input v-model="item.material_id" :readonly="readonly" placeholder="材料编号" />
          <el-input v-model="item.material_name" :readonly="readonly" placeholder="原材料名称" />
          <el-input v-model="item.cas_number" :readonly="readonly" placeholder="CAS号" />
          <el-input v-model="item.intermediate_id" :readonly="readonly" placeholder="中间体编号" />
        </div>

        <el-input
          v-model="item.intermediate_name"
          :readonly="readonly"
          type="textarea"
          :rows="2"
          placeholder="中间体名称"
          style="margin-top: 8px"
        />
        <el-input
          v-model="item.intermediate_composition"
          :readonly="readonly"
          type="textarea"
          :rows="2"
          placeholder="中间体组成"
          style="margin-top: 8px"
        />

        <div class="prop-head">
          <span>性能项（{{ (item.properties || []).length }}）</span>
          <el-button v-if="!readonly" text size="small" type="primary" @click="addProperty(item)">添加性能</el-button>
        </div>

        <div v-for="(p, pIdx) in item.properties" :key="pIdx" class="grid three-col prop-row">
          <el-input v-model="p.property_id" :readonly="readonly" placeholder="性能编号" />
          <el-input v-model="p.property_name" :readonly="readonly" placeholder="性能名称" />
          <div class="prop-value-wrap">
            <el-input v-model="p.property_value" :readonly="readonly" placeholder="性能值" />
            <el-button
              v-if="!readonly"
              text
              type="danger"
              size="small"
              @click="removeProperty(item, pIdx)"
            >删</el-button>
          </div>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      article_id: '',
      article_name: '',
      performance_trend: '',
      hierarchical_data: [],
    }),
  },
  readonly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const emptyPaper = () => ({
  article_id: '',
  article_name: '',
  performance_trend: '',
  hierarchical_data: [],
})

const localData = reactive(emptyPaper())
let syncingFromProps = false

const syncFromProps = (val) => {
  syncingFromProps = true
  const v = val || emptyPaper()
  localData.article_id = v.article_id || ''
  localData.article_name = v.article_name || ''
  localData.performance_trend = v.performance_trend || ''
  localData.hierarchical_data = Array.isArray(v.hierarchical_data)
    ? JSON.parse(JSON.stringify(v.hierarchical_data))
    : []
  queueMicrotask(() => {
    syncingFromProps = false
  })
}

watch(
  () => props.modelValue,
  (v) => syncFromProps(v),
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

const addMaterial = () => {
  localData.hierarchical_data.push({
    material_id: '',
    material_name: '',
    cas_number: '',
    intermediate_id: '',
    intermediate_name: '',
    intermediate_composition: '',
    properties: [],
  })
}

const removeMaterial = (idx) => {
  localData.hierarchical_data.splice(idx, 1)
}

const addProperty = (item) => {
  if (!Array.isArray(item.properties)) item.properties = []
  item.properties.push({ property_id: '', property_name: '', property_value: '' })
}

const removeProperty = (item, idx) => {
  item.properties.splice(idx, 1)
}
</script>

<style scoped>
.section-title { margin: 8px 0 10px; font-weight: 600; color: #334155; }
.actions { margin-bottom: 10px; }
.material-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
.card-head, .prop-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.grid { display: grid; gap: 8px; }
.grid.two-col { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
.grid.three-col { grid-template-columns: 140px 1fr 1fr; }
.prop-row { margin-top: 8px; }
.prop-value-wrap { display: flex; gap: 6px; align-items: center; }
</style>
