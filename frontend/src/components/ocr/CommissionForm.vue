<template>
  <div class="commission-form">
    <el-form label-width="110px" label-position="left" class="form-root">
      <section class="section-block">
        <div class="section-head">
          <h4>委托单基本信息</h4>
        </div>
        <div class="section-body">
          <div class="grid two-col">
            <el-input v-model="localData.basic_info.form_number" :readonly="readonly" placeholder="表格编号" />
            <el-input v-model="localData.basic_info.commission_number" :readonly="readonly" placeholder="委托编号" />
            <el-input v-model="localData.basic_info.service_type" :readonly="readonly" placeholder="服务类型" />
            <el-input v-model="localData.basic_info.need_report" :readonly="readonly" placeholder="是否提交报告" />
            <el-input v-model="localData.basic_info.commission_department" :readonly="readonly" placeholder="委托部门" />
            <el-input v-model="localData.basic_info.commissioner" :readonly="readonly" placeholder="委托人" />
            <el-input v-model="localData.basic_info.commission_date" :readonly="readonly" placeholder="委托日期" />
            <el-input v-model="localData.basic_info.commission_address" :readonly="readonly" placeholder="委托地址" />
            <el-input v-model="localData.basic_info.project_number" :readonly="readonly" placeholder="研发项目" />
            <el-input v-model="localData.basic_info.material_number" :readonly="readonly" placeholder="材质编号" />
            <el-input v-model="localData.basic_info.sample_name" :readonly="readonly" placeholder="样品名称" />
            <el-input v-model="localData.basic_info.sample_quantity" :readonly="readonly" placeholder="样品数量" />
            <el-input v-model="localData.basic_info.sample_code" :readonly="readonly" placeholder="样品代码" />
            <el-input v-model="localData.basic_info.sample_batch" :readonly="readonly" placeholder="样品批号" />
            <el-input v-model="localData.basic_info.product_number" :readonly="readonly" placeholder="产品型号" />
            <el-input v-model="localData.basic_info.product_quantity" :readonly="readonly" placeholder="样品数量/件" />
            <el-input v-model="localData.basic_info.sample_weight" :readonly="readonly" placeholder="样品规格/重量" />
            <el-input v-model="localData.basic_info.delivery_time" :readonly="readonly" placeholder="样品到达时间" />
            <el-input v-model="localData.basic_info.required_time" :readonly="readonly" placeholder="要求完成时间" />
            <el-input v-model="localData.basic_info.sample_disposal" :readonly="readonly" placeholder="样品处理" />
            <el-input v-model="localData.basic_info.storage_method" :readonly="readonly" placeholder="样品储存方式" />
            <el-input v-model="localData.basic_info.test_nature" :readonly="readonly" placeholder="测试性质" />
            <el-input v-model="localData.basic_info.special_condition_flag" :readonly="readonly" placeholder="是否有特殊测试" />
            <el-input v-model="localData.basic_info.tester" :readonly="readonly" placeholder="测试员" />
            <el-input v-model="localData.basic_info.data_reviewer" :readonly="readonly" placeholder="报告审核" />
            <el-input v-model="localData.basic_info.review_date" :readonly="readonly" placeholder="报告日期" />
          </div>

          <el-input
            v-model="localData.basic_info.test_description"
            :readonly="readonly"
            type="textarea"
            :rows="3"
            placeholder="测试说明"
            style="margin-top: 8px"
          />
          <el-input
            v-model="localData.basic_info.special_condition_detail"
            :readonly="readonly"
            type="textarea"
            :rows="2"
            placeholder="特殊测试要求"
            style="margin-top: 8px"
          />
        </div>
      </section>

      <section class="section-block">
        <div class="section-head">
          <h4>测试项目 ({{ localData.test_items.length }})</h4>
          <el-button v-if="!readonly" size="small" type="primary" @click="addTestItem">添加测试项目</el-button>
        </div>
        <div class="section-body">
          <div v-if="!localData.test_items.length" class="empty-hint">
            <p>暂无测试项目</p>
            <el-button v-if="!readonly" size="small" type="primary" @click="addTestItem">添加第一个测试项目</el-button>
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
              <el-input v-model="item.test_condition" :readonly="readonly" placeholder="测试条件" />
              <el-input v-model="item.product_standard" :readonly="readonly" placeholder="判定标准" />
              <el-input v-model="item.unit" :readonly="readonly" placeholder="单位" />
              <el-input v-model="item.tester" :readonly="readonly" placeholder="测试员" />
            </div>
            <el-input v-model="item.test_result" :readonly="readonly" type="textarea" :rows="2" placeholder="测试结果" style="margin-top: 8px" />
            <el-input v-model="item.remark" :readonly="readonly" type="textarea" :rows="2" placeholder="备注" style="margin-top: 8px" />
          </div>
        </div>
      </section>

      <section class="section-block">
        <div class="section-head">
          <h4>特殊测试 ({{ localData.special_tests.length }})</h4>
          <el-button v-if="!readonly" size="small" type="primary" @click="addSpecialTest">添加特殊测试</el-button>
        </div>
        <div class="section-body">
          <div v-if="!localData.special_tests.length" class="empty-hint">
            <p>暂无特殊测试</p>
            <el-button v-if="!readonly" size="small" type="primary" @click="addSpecialTest">添加第一个特殊测试</el-button>
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
            <el-input v-model="item.remark" :readonly="readonly" type="textarea" :rows="2" placeholder="备注" style="margin-top: 8px" />
          </div>
        </div>
      </section>

      <section class="section-block">
        <div class="section-head">
          <h4>人员信息</h4>
        </div>
        <div class="section-body">
          <div class="grid two-col">
            <el-input v-model="localData.basic_info.form_complete" :readonly="readonly" placeholder="表单完整" />
            <el-input v-model="localData.basic_info.sample_info_consistent" :readonly="readonly" placeholder="样品信息与实物一致" />
            <el-input v-model="localData.basic_info.sample_condition_ok" :readonly="readonly" placeholder="样品状态符合测试要求" />
            <el-input v-model="localData.basic_info.other_notes" :readonly="readonly" placeholder="其他备注" />
            <el-input v-model="localData.basic_info.delivery_person_signature" :readonly="readonly" placeholder="送样人签名" />
            <el-input v-model="localData.basic_info.business_receiver_signature" :readonly="readonly" placeholder="业务受理人签字" />
          </div>
        </div>
      </section>
    </el-form>
  </div>
</template>

<script setup>
import { reactive, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      basic_info: {},
      test_items: [],
      special_tests: [],
    }),
  },
  readonly: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['update:modelValue'])

const toNormalizedData = (source = {}) => ({
  basic_info: source?.basic_info && typeof source.basic_info === 'object'
    ? { ...source.basic_info }
    : {},
  test_items: Array.isArray(source?.test_items)
    ? source.test_items.map((item) => ({ ...(item || {}) }))
    : [],
  special_tests: Array.isArray(source?.special_tests)
    ? source.special_tests.map((item) => ({ ...(item || {}) }))
    : [],
})

const localData = reactive(toNormalizedData(props.modelValue))
let syncingFromProps = false

const syncFromProps = (nextValue) => {
  syncingFromProps = true
  const normalized = toNormalizedData(nextValue)
  localData.basic_info = normalized.basic_info
  localData.test_items = normalized.test_items
  localData.special_tests = normalized.special_tests
  syncingFromProps = false
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

const removeTestItem = (index) => {
  localData.test_items.splice(index, 1)
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

const removeSpecialTest = (index) => {
  localData.special_tests.splice(index, 1)
}
</script>

<style scoped>
.form-root {
  padding: 0;
}

.section-block {
  border: 1px solid #dfe7f3;
  border-radius: 8px;
  background: #fff;
  margin-bottom: 12px;
  overflow: hidden;
}

.section-head {
  border-top: 2px solid #5ba6ff;
  background: #f8fbff;
  padding: 8px 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-head h4 {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.section-body {
  padding: 10px;
}

.grid {
  display: grid;
  gap: 8px;
}

.grid.two-col {
  grid-template-columns: repeat(2, minmax(140px, 1fr));
}

.row-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
  margin-bottom: 10px;
}

.card-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.empty-hint {
  min-height: 88px;
  border: 1px dashed #d5e0f1;
  border-radius: 8px;
  background: #fafcff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #94a3b8;
  margin-bottom: 10px;
}

@media (max-width: 900px) {
  .grid.two-col {
    grid-template-columns: 1fr;
  }
}
</style>
