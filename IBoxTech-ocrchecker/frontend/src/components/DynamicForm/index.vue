<template>
  <div class="dynamic-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      :label-width="config.labelWidth || '120px'"
      :label-position="config.labelPosition || 'right'"
    >
      <!-- 遍历所有分组 -->
      <div
        v-for="(section, sectionIndex) in config.sections"
        :key="sectionIndex"
        class="form-section"
      >
        <!-- 分组标题 -->
        <div v-if="section.title" class="section-header">
          <h3>{{ section.title }}</h3>
          <span v-if="section.description" class="section-description">
            {{ section.description }}
          </span>
        </div>

        <!-- 字段列表 -->
        <el-row :gutter="20">
          <el-col
            v-for="(field, fieldIndex) in section.fields"
            :key="fieldIndex"
            :span="field.span || 12"
          >
            <el-form-item
              :label="field.label"
              :prop="field.name"
              :required="field.required"
            >
              <!-- 文本输入框 -->
              <el-input
                v-if="field.type === 'text'"
                v-model="formData[field.name]"
                :placeholder="field.placeholder || `请输入${field.label}`"
                :disabled="readonly || field.disabled"
                :maxlength="field.maxLength"
                :show-word-limit="!!field.maxLength"
              />

              <!-- 多行文本 -->
              <el-input
                v-else-if="field.type === 'textarea'"
                v-model="formData[field.name]"
                type="textarea"
                :rows="field.rows || 3"
                :placeholder="field.placeholder || `请输入${field.label}`"
                :disabled="readonly || field.disabled"
                :maxlength="field.maxLength"
                :show-word-limit="!!field.maxLength"
              />

              <!-- 数字输入 -->
              <el-input-number
                v-else-if="field.type === 'number'"
                v-model="formData[field.name]"
                :min="field.min"
                :max="field.max"
                :step="field.step || 1"
                :precision="field.precision"
                :disabled="readonly || field.disabled"
                style="width: 100%"
              />

              <!-- 下拉选择 -->
              <el-select
                v-else-if="field.type === 'select'"
                v-model="formData[field.name]"
                :placeholder="field.placeholder || `请选择${field.label}`"
                :disabled="readonly || field.disabled"
                :multiple="field.multiple"
                :clearable="field.clearable !== false"
                style="width: 100%"
              >
                <el-option
                  v-for="option in field.options"
                  :key="option.value"
                  :label="option.label"
                  :value="option.value"
                />
              </el-select>

              <!-- 日期选择 -->
              <el-date-picker
                v-else-if="field.type === 'date'"
                v-model="formData[field.name]"
                type="date"
                :placeholder="field.placeholder || `请选择${field.label}`"
                :disabled="readonly || field.disabled"
                :format="field.format || 'YYYY-MM-DD'"
                :value-format="field.valueFormat || 'YYYY-MM-DD'"
                style="width: 100%"
              />

              <!-- 日期时间选择 -->
              <el-date-picker
                v-else-if="field.type === 'datetime'"
                v-model="formData[field.name]"
                type="datetime"
                :placeholder="field.placeholder || `请选择${field.label}`"
                :disabled="readonly || field.disabled"
                :format="field.format || 'YYYY-MM-DD HH:mm:ss'"
                :value-format="field.valueFormat || 'YYYY-MM-DD HH:mm:ss'"
                style="width: 100%"
              />

              <!-- 开关 -->
              <el-switch
                v-else-if="field.type === 'switch'"
                v-model="formData[field.name]"
                :disabled="readonly || field.disabled"
                :active-text="field.activeText"
                :inactive-text="field.inactiveText"
              />

              <!-- 单选框组 -->
              <el-radio-group
                v-else-if="field.type === 'radio'"
                v-model="formData[field.name]"
                :disabled="readonly || field.disabled"
              >
                <el-radio
                  v-for="option in field.options"
                  :key="option.value"
                  :label="option.value"
                >
                  {{ option.label }}
                </el-radio>
              </el-radio-group>

              <!-- 复选框组 -->
              <el-checkbox-group
                v-else-if="field.type === 'checkbox'"
                v-model="formData[field.name]"
                :disabled="readonly || field.disabled"
              >
                <el-checkbox
                  v-for="option in field.options"
                  :key="option.value"
                  :label="option.value"
                >
                  {{ option.label }}
                </el-checkbox>
              </el-checkbox-group>

              <!-- 滑块 -->
              <el-slider
                v-else-if="field.type === 'slider'"
                v-model="formData[field.name]"
                :min="field.min || 0"
                :max="field.max || 100"
                :step="field.step || 1"
                :disabled="readonly || field.disabled"
                :show-input="field.showInput"
              />

              <!-- 评分 -->
              <el-rate
                v-else-if="field.type === 'rate'"
                v-model="formData[field.name]"
                :max="field.max || 5"
                :disabled="readonly || field.disabled"
                :show-text="field.showText"
                :texts="field.texts"
              />

              <!-- 不支持的字段类型 -->
              <el-alert
                v-else
                :title="`不支持的字段类型: ${field.type}`"
                type="warning"
                :closable="false"
              />

              <!-- 字段提示 -->
              <div v-if="field.tip" class="field-tip">
                <el-icon><InfoFilled /></el-icon>
                {{ field.tip }}
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 空状态 -->
      <el-empty
        v-if="!config.sections || config.sections.length === 0"
        description="暂无表单配置"
        :image-size="100"
      />
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

const props = defineProps({
  // 表单配置（JSON格式）
  config: {
    type: Object,
    required: true,
    default: () => ({
      sections: [],
      labelWidth: '120px',
      labelPosition: 'right'
    })
  },
  
  // 表单数据（v-model）
  modelValue: {
    type: Object,
    default: () => ({})
  },
  
  // 是否只读
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

const formRef = ref(null)
const formData = reactive({})

// 初始化表单数据
const initFormData = () => {
  // 清空现有数据
  Object.keys(formData).forEach(key => {
    delete formData[key]
  })
  
  // 从配置中提取所有字段，设置初始值
  if (props.config.sections) {
    props.config.sections.forEach(section => {
      if (section.fields) {
        section.fields.forEach(field => {
          // 使用 props.modelValue 中的值，或字段的默认值
          formData[field.name] = props.modelValue[field.name] ?? field.defaultValue ?? getDefaultValueByType(field.type)
        })
      }
    })
  }
}

// 根据字段类型获取默认值
const getDefaultValueByType = (type) => {
  switch (type) {
    case 'number':
      return 0
    case 'switch':
      return false
    case 'checkbox':
      return []
    case 'slider':
      return 0
    case 'rate':
      return 0
    default:
      return ''
  }
}

// 生成表单验证规则
const formRules = computed(() => {
  const rules = {}
  
  if (props.config.sections) {
    props.config.sections.forEach(section => {
      if (section.fields) {
        section.fields.forEach(field => {
          const fieldRules = []
          
          // 必填验证
          if (field.required) {
            fieldRules.push({
              required: true,
              message: `${field.label}不能为空`,
              trigger: ['blur', 'change']
            })
          }
          
          // 长度验证
          if (field.minLength || field.maxLength) {
            fieldRules.push({
              min: field.minLength,
              max: field.maxLength,
              message: `${field.label}长度应在 ${field.minLength || 0} 到 ${field.maxLength || '无限'} 之间`,
              trigger: 'blur'
            })
          }
          
          // 正则验证
          if (field.pattern) {
            fieldRules.push({
              pattern: new RegExp(field.pattern),
              message: field.patternMessage || `${field.label}格式不正确`,
              trigger: 'blur'
            })
          }
          
          // 自定义验证
          if (field.validator) {
            fieldRules.push({
              validator: field.validator,
              trigger: 'blur'
            })
          }
          
          if (fieldRules.length > 0) {
            rules[field.name] = fieldRules
          }
        })
      }
    })
  }
  
  return rules
})

// 标志：是否正在从props同步数据
let isSyncingFromProps = false

// 监听配置变化，重新初始化表单
watch(
  () => props.config,
  () => {
    isSyncingFromProps = true
    initFormData()
    setTimeout(() => {
      isSyncingFromProps = false
    }, 100)
  },
  { deep: true, immediate: true }
)

// 监听 modelValue 变化
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && !isSyncingFromProps) {
      isSyncingFromProps = true
      Object.assign(formData, newVal)
      setTimeout(() => {
        isSyncingFromProps = false
      }, 100)
    }
  },
  { deep: true }
)

// 监听 formData 变化，触发 update
watch(
  formData,
  (newVal) => {
    // 如果正在从 props 同步数据，不触发 emit（避免循环更新）
    if (isSyncingFromProps) {
      return
    }
    
    // 将数据发送给父组件
    emit('update:modelValue', { ...newVal })
  },
  { deep: true }
)

// 表单验证
const validate = async () => {
  try {
    await formRef.value.validate()
    return true
  } catch (error) {
    return false
  }
}

// 重置表单
const resetFields = () => {
  formRef.value.resetFields()
}

// 清空验证
const clearValidate = () => {
  formRef.value.clearValidate()
}

// 暴露方法给父组件
defineExpose({
  validate,
  resetFields,
  clearValidate,
  formData
})

onMounted(() => {
  initFormData()
})
</script>

<style lang="scss" scoped>
.dynamic-form {
  .form-section {
    margin-bottom: 30px;
    
    &:last-child {
      margin-bottom: 0;
    }
    
    .section-header {
      margin-bottom: 20px;
      padding-bottom: 10px;
      border-bottom: 2px solid #409eff;
      
      h3 {
        margin: 0;
        font-size: 16px;
        color: #303133;
        display: flex;
        align-items: center;
        
        .el-icon {
          margin-right: 8px;
        }
      }
      
      .section-description {
        display: block;
        margin-top: 5px;
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .field-tip {
    margin-top: 5px;
    font-size: 12px;
    color: #909399;
    display: flex;
    align-items: center;
    
    .el-icon {
      margin-right: 4px;
    }
  }
}
</style>
