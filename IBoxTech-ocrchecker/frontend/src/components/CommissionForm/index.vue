<template>
  <div class="commission-form">
    <el-form
      ref="formRef"
      :model="formData"
      label-width="80px"
      label-position="left"
    >
      <!-- 委托基本信息 -->
      <div class="form-section">
        <div class="section-header">
          <h3><el-icon><Document /></el-icon>委托基本信息</h3>
        </div>
        
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="表格编号" prop="basic_info.form_number" required>
              <el-input
                v-model="formData.basic_info.form_number"
                :readonly="readonly"
                placeholder="请输入表格编号"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="委托编号" prop="basic_info.commission_number" required>
              <el-input
                v-model="formData.basic_info.commission_number"
                :readonly="readonly"
                placeholder="请输入委托编号"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="服务类型" prop="basic_info.service_type">
              <el-input
                v-model="formData.basic_info.service_type"
                :readonly="readonly"
                placeholder="请输入服务类型"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="需要报告">
              <el-select
                v-model="formData.basic_info.need_report"
                :disabled="readonly"
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option label="是" value="是" />
                <el-option label="否" value="否" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="研发项目">
              <el-input
                v-model="formData.basic_info.project_number"
                :readonly="readonly"
                placeholder="请输入研发项目"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="委托部门">
              <el-input
                v-model="formData.basic_info.commission_department"
                :readonly="readonly"
                placeholder="请输入委托部门"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="委托人">
              <el-input
                v-model="formData.basic_info.commissioner"
                :readonly="readonly"
                placeholder="请输入委托人"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="委托日期">
              <el-date-picker
                v-model="formData.basic_info.commission_date"
                :disabled="readonly"
                type="date"
                placeholder="选择日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="物料代码">
              <el-input
                v-model="formData.basic_info.material_number"
                :readonly="readonly"
                placeholder="请输入物料代码"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品或原材料型号">
              <el-input
                v-model="formData.basic_info.product_number"
                :readonly="readonly"
                placeholder="请输入产品或原材料型号"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="样品重量">
              <el-input
                v-model="formData.basic_info.sample_weight"
                :readonly="readonly"
                placeholder="请输入样品重量"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="样品名称">
              <el-input
                v-model="formData.basic_info.sample_name"
                :readonly="readonly"
                placeholder="请输入样品名称"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="样品数量">
              <el-input
                v-model="formData.basic_info.sample_quantity"
                :readonly="readonly"
                placeholder="请输入样品数量"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="样品代码">
              <el-input
                v-model="formData.basic_info.sample_code"
                :readonly="readonly"
                placeholder="请输入样品代码"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="样品批次">
              <el-input
                v-model="formData.basic_info.sample_batch"
                :readonly="readonly"
                placeholder="请输入样品批次"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="送样时间">
              <el-date-picker
                v-model="formData.basic_info.delivery_time"
                :disabled="readonly"
                type="date"
                placeholder="选择送样时间"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="需求时间">
              <el-date-picker
                v-model="formData.basic_info.required_time"
                :disabled="readonly"
                type="date"
                placeholder="选择需求时间"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="余样处理">
              <el-select
                v-model="formData.basic_info.sample_disposal"
                :disabled="readonly"
                placeholder="请选择余样处理方式"
                style="width: 100%"
              >
                <el-option label="退回" value="退回" />
                <el-option label="销毁" value="销毁" />
                <el-option label="留存" value="留存" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="样品存储方式">
              <el-select
                v-model="formData.basic_info.storage_method"
                :disabled="readonly"
                placeholder="请选择存储方式"
                style="width: 100%"
              >
                <el-option label="常温" value="常温" />
                <el-option label="冷藏" value="冷藏" />
                <el-option label="冷冻" value="冷冻" />
                <el-option label="避光" value="避光" />
                <el-option label="干燥" value="干燥" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="委托地址">
              <el-input
                v-model="formData.basic_info.commission_address"
                :readonly="readonly"
                placeholder="请输入委托地址"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="测试性质">
              <el-input
                v-model="formData.basic_info.test_nature"
                :readonly="readonly"
                placeholder="请输入测试性质"
              />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="测试说明">
              <el-input
                v-model="formData.basic_info.test_description"
                :readonly="readonly"
                type="textarea"
                :rows="3"
                placeholder="请输入测试说明"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-section-title">测试基本信息</div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="有无特殊条件">
              <el-select
                v-model="formData.basic_info.special_condition_flag"
                :disabled="readonly"
                placeholder="请选择"
                style="width: 100%"
              >
                <el-option label="是" value="是" />
                <el-option label="否" value="否" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="24" v-if="formData.basic_info.special_condition_flag === '是'">
            <el-form-item label="条件是">
              <el-input
                v-model="formData.basic_info.special_condition_detail"
                :readonly="readonly"
                type="textarea"
                :rows="2"
                placeholder="请详细说明特殊条件要求"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 测试项目 -->
      <div class="form-section">
        <div class="section-header">
          <h3><el-icon><Operation /></el-icon>测试项目 ({{ formData.test_items.length }})</h3>
          <el-button
            v-if="!readonly"
            type="primary"
            size="small"
            @click="addTestItem"
          >
            <el-icon><Plus /></el-icon>
            添加项目
          </el-button>
        </div>

        <div class="test-items-list">
          <div
            v-for="(item, index) in formData.test_items"
            :key="index"
            class="test-item-card"
          >
            <div class="card-header">
              <span class="item-number">项目 {{ index + 1 }}</span>
              <el-button
                v-if="!readonly"
                type="danger"
                size="small"
                text
                @click="removeTestItem(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>

            <el-row :gutter="16">
              <el-col :span="24">
                <el-form-item label="测试项目" required>
                  <el-input
                    v-model="item.test_item"
                    :readonly="readonly"
                    placeholder="请输入测试项目"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="测试设备">
                  <el-input
                    v-model="item.test_equipment"
                    :readonly="readonly"
                    placeholder="请输入测试设备"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="测试标准">
                  <el-input
                    v-model="item.test_standard"
                    :readonly="readonly"
                    placeholder="请输入测试标准"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="测试条件">
                  <el-input
                    v-model="item.test_condition"
                    :readonly="readonly"
                    placeholder="请输入测试条件"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="产品标准">
                  <el-input
                    v-model="item.product_standard"
                    :readonly="readonly"
                    placeholder="请输入产品标准"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="单位">
                  <el-input
                    v-model="item.unit"
                    :readonly="readonly"
                    placeholder="请输入单位"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="测试员">
                  <el-input
                    v-model="item.tester"
                    :readonly="readonly"
                    placeholder="请输入测试员"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="测试结果">
                  <el-input
                    v-model="item.test_result"
                    :readonly="readonly"
                    type="textarea"
                    :rows="2"
                    placeholder="请输入测试结果"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="备注">
                  <el-input
                    v-model="item.remark"
                    :readonly="readonly"
                    placeholder="请输入备注"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <el-empty
            v-if="formData.test_items.length === 0"
            description="暂无测试项目"
            :image-size="80"
          >
            <el-button
              v-if="!readonly"
              type="primary"
              @click="addTestItem"
            >
              <el-icon><Plus /></el-icon>
              添加第一个测试项目
            </el-button>
          </el-empty>
        </div>
      </div>

      <!-- 特殊测试 -->
      <div class="form-section">
        <div class="section-header">
          <h3><el-icon><MagicStick /></el-icon>特殊测试 ({{ formData.special_tests.length }})</h3>
          <el-button
            v-if="!readonly"
            type="primary"
            size="small"
            @click="addSpecialTest"
          >
            <el-icon><Plus /></el-icon>
            添加测试
          </el-button>
        </div>

        <div class="special-tests-list">
          <div
            v-for="(test, index) in formData.special_tests"
            :key="index"
            class="special-test-card"
          >
            <div class="card-header">
              <span class="item-number">测试 {{ index + 1 }}</span>
              <el-button
                v-if="!readonly"
                type="danger"
                size="small"
                text
                @click="removeSpecialTest(index)"
              >
                <el-icon><Delete /></el-icon>
              </el-button>
            </div>

            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="测试类型">
                  <el-input
                    v-model="test.test_type"
                    :readonly="readonly"
                    placeholder="请输入测试类型"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="元素名称">
                  <el-input
                    v-model="test.element_name"
                    :readonly="readonly"
                    placeholder="请输入元素名称"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="标准值">
                  <el-input
                    v-model="test.standard_value"
                    :readonly="readonly"
                    placeholder="请输入标准值"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="测试值">
                  <el-input
                    v-model="test.measured_value"
                    :readonly="readonly"
                    placeholder="请输入测试值"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="24">
                <el-form-item label="备注">
                  <el-input
                    v-model="test.remark"
                    :readonly="readonly"
                    placeholder="请输入备注"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <el-empty
            v-if="formData.special_tests.length === 0"
            description="暂无特殊测试"
            :image-size="80"
          >
            <el-button
              v-if="!readonly"
              type="primary"
              @click="addSpecialTest"
            >
              <el-icon><Plus /></el-icon>
              添加第一个特殊测试
            </el-button>
          </el-empty>
        </div>
      </div>

      <div class="form-section">
        <div class="form-section-title">人员信息</div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="测试员">
              <el-input
                v-model="formData.basic_info.tester"
                :readonly="readonly"
                placeholder="请输入测试员"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="数据复核人">
              <el-input
                v-model="formData.basic_info.data_reviewer"
                :readonly="readonly"
                placeholder="请输入数据复核人"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="复核日期">
              <el-date-picker
                v-model="formData.basic_info.review_date"
                :disabled="readonly"
                type="date"
                placeholder="选择复核日期"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="form-section-title">测试确认</div>
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="样品是否完好" label-width="400px">
              <el-checkbox-group 
                v-model="formData.basic_info.sample_condition_checkboxes"
                :disabled="readonly"
                style="width: 100%"
              >
                <el-checkbox label="是" style="margin-right: 40px">是</el-checkbox>
                <el-checkbox label="否">否</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="样品实物信息是否一致" label-width="400px">
              <el-checkbox-group 
                v-model="formData.basic_info.sample_info_consistent_checkboxes"
                :disabled="readonly"
                style="width: 100%"
              >
                <el-checkbox label="是" style="margin-right: 40px">是</el-checkbox>
                <el-checkbox label="否">否</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="申请单是否填写完整" label-width="400px">
              <el-checkbox-group 
                v-model="formData.basic_info.form_complete_checkboxes"
                :disabled="readonly"
                style="width: 100%"
              >
                <el-checkbox label="是" style="margin-right: 40px">是</el-checkbox>
                <el-checkbox label="否">否</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="其他" label-width="400px">
              <el-checkbox-group 
                v-model="formData.basic_info.other_notes"
                :disabled="readonly"
                style="width: 100%"
              >
                <el-checkbox label="是" style="margin-right: 40px">是</el-checkbox>
                <el-checkbox label="否">否</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="送样人签名">
              <el-input
                v-model="formData.basic_info.delivery_person_signature"
                :readonly="readonly"
                placeholder="请输入送样人签名"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="业务受理人签字">
              <el-input
                v-model="formData.basic_info.business_handler_signature"
                :readonly="readonly"
                placeholder="请输入业务受理人签字"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted, nextTick } from 'vue'
import { Document, Operation, MagicStick, Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      basic_info: {},
      test_items: [],
      special_tests: []
    })
  },
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

const formRef = ref(null)

// 表单数据
const formData = reactive({
  basic_info: {
    form_number: '',
    commission_number: '',
    service_type: '',
    need_report: '',
    project_number: '',
    material_number: '',
    product_number: '',
    sample_weight: '',
    commission_department: '',
    commissioner: '',
    commission_date: '',
    commission_address: '',
    sample_name: '',
    sample_quantity: '',
    sample_code: '',
    sample_batch: '',
    delivery_time: '',
    required_time: '',
    sample_disposal: '',
    storage_method: '',
    test_nature: '',
    test_description: '',
    special_condition_flag: '',
    special_condition_detail: '',
    tester: '',
    data_reviewer: '',
    review_date: '',
    // 新增：签字确认字段
    delivery_person_signature: '',
    business_handler_signature: '',
    sample_condition: '',
    sample_info_consistent: '',
    form_complete: '',
    // 其他信息
    other_notes: '',
    // Checkbox 数组字段（用于 el-checkbox-group）
    sample_condition_checkboxes: [],
    sample_info_consistent_checkboxes: [],
    form_complete_checkboxes: []
  },
  test_items: [],
  special_tests: []
})

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue) {
    Object.assign(formData.basic_info, props.modelValue.basic_info || {})
    formData.test_items = props.modelValue.test_items || []
    formData.special_tests = props.modelValue.special_tests || []
  }
  
  // 始终确保 checkbox 数组字段被正确初始化
  formData.basic_info.sample_condition_checkboxes = formData.basic_info.sample_condition ? [formData.basic_info.sample_condition] : []
  formData.basic_info.sample_info_consistent_checkboxes = formData.basic_info.sample_info_consistent ? [formData.basic_info.sample_info_consistent] : []
  formData.basic_info.form_complete_checkboxes = formData.basic_info.form_complete ? [formData.basic_info.form_complete] : []
}

// 监听 checkbox 数组变化，同步到字符串字段
watch(
  () => formData.basic_info.sample_condition_checkboxes,
  (newVal) => {
    // 只保留最后一个选中的值（模拟单选行为）
    if (newVal.length > 1) {
      formData.basic_info.sample_condition_checkboxes = [newVal[newVal.length - 1]]
    }
    formData.basic_info.sample_condition = newVal.length > 0 ? newVal[0] : ''
  }
)

watch(
  () => formData.basic_info.sample_info_consistent_checkboxes,
  (newVal) => {
    // 只保留最后一个选中的值（模拟单选行为）
    if (newVal.length > 1) {
      formData.basic_info.sample_info_consistent_checkboxes = [newVal[newVal.length - 1]]
    }
    formData.basic_info.sample_info_consistent = newVal.length > 0 ? newVal[0] : ''
  }
)

watch(
  () => formData.basic_info.form_complete_checkboxes,
  (newVal) => {
    // 只保留最后一个选中的值（模拟单选行为）
    if (newVal.length > 1) {
      formData.basic_info.form_complete_checkboxes = [newVal[newVal.length - 1]]
    }
    formData.basic_info.form_complete = newVal.length > 0 ? newVal[0] : ''
  }
)

// 标志：是否正在从props同步数据
let isSyncingFromProps = false

// 监听props变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      isSyncingFromProps = true
      initFormData()
      // 使用 nextTick 确保数据更新完成后再重置标志
      nextTick(() => {
        isSyncingFromProps = false
      })
    }
  },
  { deep: true, immediate: true }
)

// 监听formData变化，触发update
watch(
  formData,
  (newVal) => {
    // 如果正在从 props 同步数据，不触发 emit（避免循环更新）
    if (isSyncingFromProps) {
      return
    }
    
    // 将数据发送给父组件
    emit('update:modelValue', JSON.parse(JSON.stringify(newVal)))
  },
  { deep: true }
)

// 添加测试项目
const addTestItem = () => {
  formData.test_items.push({
    test_item: '',
    test_equipment: '',
    test_standard: '',
    test_condition: '',
    product_standard: '',
    unit: '',
    test_result: '',
    tester: '',
    remark: '',
    sort_order: formData.test_items.length
  })
  ElMessage.success('已添加测试项目')
}

// 删除测试项目
const removeTestItem = (index) => {
  formData.test_items.splice(index, 1)
  ElMessage.success('已删除测试项目')
}

// 添加特殊测试
const addSpecialTest = () => {
  formData.special_tests.push({
    test_type: '',
    element_name: '',
    standard_value: '',
    measured_value: '',
    remark: '',
    sort_order: formData.special_tests.length
  })
  ElMessage.success('已添加特殊测试')
}

// 删除特殊测试
const removeSpecialTest = (index) => {
  formData.special_tests.splice(index, 1)
  ElMessage.success('已删除特殊测试')
}

// 表单验证
const validate = async () => {
  if (!formRef.value) return false

  try {
    await formRef.value.validate()

    // 额外验证
    if (!formData.basic_info.form_number) {
      ElMessage.warning('请输入表格编号')
      return false
    }
    if (!formData.basic_info.commission_number) {
      ElMessage.warning('请输入委托编号')
      return false
    }

    emit('validate', true)
    return true
  } catch (error) {
    console.error('表单验证失败:', error)
    emit('validate', false)
    return false
  }
}

// 重置表单
const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  formData.basic_info = {}
  formData.test_items = []
  formData.special_tests = []
}

// 获取表单数据
const getFormData = () => {
  return JSON.parse(JSON.stringify(formData))
}

// 暴露方法
defineExpose({
  validate,
  resetForm,
  getFormData
})

onMounted(() => {
  initFormData()
})
</script>

<style scoped lang="scss">
.commission-form {
  width: 100%;
  padding: 20px;
  background: #fff;

  .form-section {
    margin-bottom: 30px;
    padding: 20px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e4e7ed;

    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid #409eff;

      h3 {
        margin: 0;
        font-size: 16px;
        font-weight: 600;
        color: #303133;
        display: flex;
        align-items: center;
        gap: 8px;
      }
    }

    .form-section-title {
      font-size: 14px;
      font-weight: 600;
      color: #606266;
      margin: 16px 0 12px 0;
      padding-left: 8px;
      border-left: 3px solid #409eff;
    }

    .test-items-list,
    .special-tests-list {
      display: flex;
      flex-direction: column;
      gap: 16px;

      .test-item-card,
      .special-test-card {
        padding: 16px;
        background: #fff;
        border-radius: 6px;
        border: 1px solid #dcdfe6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

        .card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
          padding-bottom: 8px;
          border-bottom: 1px solid #ebeef5;

          .item-number {
            font-size: 14px;
            font-weight: 600;
            color: #606266;
          }
        }
      }
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 12px;

    .el-form-item__label {
      font-weight: 500;
      color: #606266;
      line-height: 1.2;  // 减小行间距
      display: flex;
      align-items: center;  // 垂直居中
    }
  }
}
</style>


