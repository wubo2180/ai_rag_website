<template>
  <div class="commission-form">
    <el-form label-width="110px" label-position="left">
      <div class="section-title">委托基本信息</div>
      <div class="grid two-col">
        <el-input v-model="localData.basic_info.form_number" :readonly="readonly" placeholder="表格编号" />
        <el-input v-model="localData.basic_info.commission_number" :readonly="readonly" placeholder="委托编号" />
        <el-input v-model="localData.basic_info.service_type" :readonly="readonly" placeholder="服务类型" />
        <el-input v-model="localData.basic_info.commission_department" :readonly="readonly" placeholder="委托部门" />
        <el-input v-model="localData.basic_info.commissioner" :readonly="readonly" placeholder="委托人" />
        <el-input v-model="localData.basic_info.project_number" :readonly="readonly" placeholder="研发项目" />
        <el-input v-model="localData.basic_info.sample_name" :readonly="readonly" placeholder="样品名称" />
        <el-input v-model="localData.basic_info.sample_code" :readonly="readonly" placeholder="样品代码" />
      </div>

      <el-input
        v-model="localData.basic_info.test_description"
        :readonly="readonly"
        type="textarea"
        :rows="3"
        placeholder="测试说明"
        style="margin-top: 8px"
      />

      <div class="section-title">测试项目（{{ localData.test_items.length }}）</div>
      <div class="actions" v-if="!readonly">
        <el-button size="small" type="primary" @click="addTestItem">添加测试项目</el-button>
      </div>
      <div v-for="(item, idx) in localData.test_items" :key="idx" class="row-card">
        <div class="card-head">
          <strong>项目 #{{ idx + 1 }}</strong>
          <el-button v-if="!readonly" text type="danger" size="small" @click="removeTestItem(idx)">删除</el-button>
        </div>
        <div class="grid two-col">
          <el-input v-model="item.test_item" :readonly="readonly" placeholder="测试项目" />
          <el-input v-model="item.test_standard" :readonly="readonly" placeholder="测试标准" />
          <el-input v-model="item.test_equipment" :readonly="readonly" placeholder="测试设备" />
          <el-input v-model="item.tester" :readonly="readonly" placeholder="测试员" />
        </div>
        <el-input v-model="item.test_result" :readonly="readonly" type="textarea" :rows="2" placeholder="测试结果" style="margin-top:8px" />
      </div>

      <div class="section-title">特殊测试（{{ localData.special_tests.length }}）</div>
      <div class="actions" v-if="!readonly">
        <el-button size="small" type="primary" @click="addSpecialTest">添加特殊测试</el-button>
      </div>
      <div v-for="(item, idx) in localData.special_tests" :key="idx" class="row-card">
        <div class="card-head">
          <strong>特殊测试 #{{ idx + 1 }}</strong>
          <el-button v-if="!readonly" text type="danger" size="small" @click="removeSpecialTest(idx)">删除</el-button>
        </div>
        <div class="grid two-col">
          <el-input v-model="item.test_type" :readonly="readonly" placeholder="测试类型" />
          <el-input v-model="item.element_name" :readonly="readonly" placeholder="元素名称" />
          <el-input v-model="item.standard_value" :readonly="readonly" placeholder="标准值" />
          <el-input v-model="item.measured_value" :readonly="readonly" placeholder="测试值" />
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
    default: () => ({ basic_info: {}, test_items: [], special_tests: [] }),
  },
  readonly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const emptyCommission = () => ({ basic_info: {}, test_items: [], special_tests: [] })

const localData = reactive(emptyCommission())
let syncingFromProps = false

const syncFromProps = (value) => {
  syncingFromProps = true
  const v = value || emptyCommission()
  localData.basic_info = { ...(v.basic_info || {}) }
  localData.test_items = Array.isArray(v.test_items) ? JSON.parse(JSON.stringify(v.test_items)) : []
  localData.special_tests = Array.isArray(v.special_tests)
    ? JSON.parse(JSON.stringify(v.special_tests))
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

const addTestItem = () => {
  localData.test_items.push({
    test_item: '',
    test_equipment: '',
    test_standard: '',
    test_condition: '',
    product_standard: '',
    unit: '',
    tester: '',
    test_result: '',
    remark: '',
  })
}

const removeTestItem = (idx) => {
  localData.test_items.splice(idx, 1)
}

const addSpecialTest = () => {
  localData.special_tests.push({
    test_type: '',
    element_name: '',
    standard_value: '',
    measured_value: '',
    remark: '',
  })
}

const removeSpecialTest = (idx) => {
  localData.special_tests.splice(idx, 1)
}
</script>

<style scoped>
.section-title { margin: 8px 0 10px; font-weight: 600; color: #334155; }
.actions { margin-bottom: 10px; }
.grid { display: grid; gap: 8px; }
.grid.two-col { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
.row-card { border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
</style>
