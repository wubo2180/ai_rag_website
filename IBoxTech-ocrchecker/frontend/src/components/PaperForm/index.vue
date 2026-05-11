<template>
  <div class="paper-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
      label-position="left"
    >
      <!-- 文献基本信息 -->
      <div class="form-section">
        <div class="section-header">
          <h3>文献基本信息</h3>
        </div>
        
        <el-form-item label="文献编号" prop="article_id" required>
          <el-input
            v-model="formData.article_id"
            placeholder="格式：A-XXXXX，如 A-3K7M9"
            :disabled="readonly"
          />
        </el-form-item>
        
        <el-form-item label="文献名称" prop="article_name" required>
          <el-input
            v-model="formData.article_name"
            type="textarea"
            :rows="2"
            placeholder="请输入文献标题"
            :disabled="readonly"
          />
        </el-form-item>
        
        <el-form-item label="性能趋势" prop="performance_trend">
          <el-input
            v-model="formData.performance_trend"
            type="textarea"
            :rows="3"
            placeholder="请输入性能趋势描述"
            :disabled="readonly"
          />
        </el-form-item>
      </div>

      <!-- 四级数据连接 -->
      <div class="form-section">
        <div class="section-header">
          <h3>四级数据连接（Material-Intermediate-Property）</h3>
          <el-button
            v-if="!readonly"
            type="primary"
            size="small"
            @click="addMaterial"
          >
            <el-icon><Plus /></el-icon>
            添加材料/中间体
          </el-button>
        </div>

        <!-- 材料/中间体列表 -->
        <div
          v-for="(material, mIndex) in formData.hierarchical_data"
          :key="mIndex"
          class="material-item"
        >
          <div class="material-header">
            <span class="material-index">材料/中间体 #{{ mIndex + 1 }}</span>
            <el-button
              v-if="!readonly"
              type="danger"
              size="small"
              text
              @click="removeMaterial(mIndex)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>

          <el-row :gutter="20">
            <!-- 材料信息 -->
            <el-col :span="8">
              <el-form-item
                :label="`材料编号`"
                :prop="`hierarchical_data.${mIndex}.material_id`"
                :rules="[{ required: true, message: '请输入材料编号', trigger: 'blur' }]"
              >
                <el-input
                  v-model="material.material_id"
                  placeholder="如：A1M1"
                  :disabled="readonly"
                />
              </el-form-item>
            </el-col>

            <el-col :span="16">
              <el-form-item
                :label="`原材料名称`"
                :prop="`hierarchical_data.${mIndex}.material_name`"
              >
                <el-input
                  v-model="material.material_name"
                  type="textarea"
                  :rows="1"
                  placeholder="请输入原材料名称及规格"
                  :disabled="readonly"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item :label="`CAS号`" :prop="`hierarchical_data.${mIndex}.cas_number`">
                <el-input
                  v-model="material.cas_number"
                  placeholder="如：1344-28-1"
                  :disabled="readonly"
                />
              </el-form-item>
            </el-col>

            <el-col :span="8">
              <el-form-item
                :label="`中间体编号`"
                :prop="`hierarchical_data.${mIndex}.intermediate_id`"
              >
                <el-input
                  v-model="material.intermediate_id"
                  placeholder="如：A1I1"
                  :disabled="readonly"
                />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item
            :label="`中间体名称`"
            :prop="`hierarchical_data.${mIndex}.intermediate_name`"
          >
            <el-input
              v-model="material.intermediate_name"
              type="textarea"
              :rows="2"
              placeholder="请输入中间体名称及组成"
              :disabled="readonly"
            />
          </el-form-item>

          <el-form-item
            :label="`中间体组成`"
            :prop="`hierarchical_data.${mIndex}.intermediate_composition`"
          >
            <el-input
              v-model="material.intermediate_composition"
              type="textarea"
              :rows="1"
              placeholder="如：A1I1：A1I2=10:1（质量比）"
              :disabled="readonly"
            />
          </el-form-item>

          <!-- 性能数据表格 -->
          <div class="properties-section">
            <div class="properties-header">
              <label class="properties-label">性能数据（Properties）</label>
              <el-button
                v-if="!readonly"
                type="primary"
                size="small"
                text
                @click="addProperty(mIndex)"
              >
                <el-icon><Plus /></el-icon>
                添加性能
              </el-button>
            </div>

            <el-table
              :data="material.properties"
              border
              size="small"
              class="properties-table"
            >
              <el-table-column label="序号" type="index" width="60" align="center" />
              
              <el-table-column label="性能编号" width="120">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.property_id"
                    placeholder="如：A1P1"
                    size="small"
                    :disabled="readonly"
                  />
                </template>
              </el-table-column>

              <el-table-column label="性能名称" min-width="200">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.property_name"
                    placeholder="如：粘度／黏度 MPa·S"
                    size="small"
                    :disabled="readonly"
                  />
                </template>
              </el-table-column>

              <el-table-column label="性能值" width="150">
                <template #default="{ row, $index }">
                  <el-input
                    v-model="row.property_value"
                    placeholder="如：1900"
                    size="small"
                    :disabled="readonly"
                  />
                </template>
              </el-table-column>

              <el-table-column
                v-if="!readonly"
                label="操作"
                width="80"
                align="center"
                fixed="right"
              >
                <template #default="{ row, $index }">
                  <el-button
                    type="danger"
                    size="small"
                    text
                    @click="removeProperty(mIndex, $index)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <el-empty
              v-if="!material.properties || material.properties.length === 0"
              description="暂无性能数据"
              :image-size="80"
            />
          </div>
        </div>

        <el-empty
          v-if="!formData.hierarchical_data || formData.hierarchical_data.length === 0"
          description="暂无材料/中间体数据，点击上方按钮添加"
          :image-size="100"
        />
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from 'vue'
import { Plus, Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  // 表单数据（v-model）
  modelValue: {
    type: Object,
    default: () => ({
      article_id: '',
      article_name: '',
      performance_trend: '',
      hierarchical_data: []
    })
  },
  // 是否只读
  readonly: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'validate'])

// 表单引用
const formRef = ref(null)

// 表单数据
const formData = reactive({
  article_id: '',
  article_name: '',
  performance_trend: '',
  hierarchical_data: []
})

// 验证规则
const rules = {
  article_id: [
    { required: true, message: '请输入文献编号', trigger: 'blur' },
    { pattern: /^A-[A-Z0-9]{5}$/, message: '格式：A-XXXXX（A-后跟5位大写字母或数字），如 A-3K7M9', trigger: 'blur' }
  ],
  article_name: [
    { required: true, message: '请输入文献名称', trigger: 'blur' }
  ]
}

// 初始化表单数据
const initFormData = () => {
  if (props.modelValue) {
    Object.assign(formData, {
      article_id: props.modelValue.article_id || '',
      article_name: props.modelValue.article_name || '',
      performance_trend: props.modelValue.performance_trend || '',
      hierarchical_data: props.modelValue.hierarchical_data || []
    })
  }
}

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
    emit('update:modelValue', { ...newVal })
  },
  { deep: true }
)

// 添加材料/中间体
const addMaterial = () => {
  formData.hierarchical_data.push({
    material_id: '',
    material_name: '',
    cas_number: '',
    intermediate_id: '',
    intermediate_name: '',
    intermediate_composition: '',
    properties: []
  })
  ElMessage.success('已添加材料/中间体')
}

// 删除材料/中间体
const removeMaterial = (index) => {
  formData.hierarchical_data.splice(index, 1)
  ElMessage.success('已删除材料/中间体')
}

// 添加性能数据
const addProperty = (materialIndex) => {
  if (!formData.hierarchical_data[materialIndex].properties) {
    formData.hierarchical_data[materialIndex].properties = []
  }
  formData.hierarchical_data[materialIndex].properties.push({
    property_id: '',
    property_name: '',
    property_value: ''
  })
}

// 删除性能数据
const removeProperty = (materialIndex, propertyIndex) => {
  formData.hierarchical_data[materialIndex].properties.splice(propertyIndex, 1)
}

// 表单验证
const validate = async () => {
  if (!formRef.value) return false
  
  try {
    await formRef.value.validate()
    
    // 额外验证：至少有一个材料/中间体
    if (!formData.hierarchical_data || formData.hierarchical_data.length === 0) {
      ElMessage.warning('请至少添加一个材料/中间体')
      return false
    }
    
    // 验证每个材料的必填字段
    for (let i = 0; i < formData.hierarchical_data.length; i++) {
      const material = formData.hierarchical_data[i]
      if (!material.material_id) {
        ElMessage.warning(`材料/中间体 #${i + 1} 的材料编号不能为空`)
        return false
      }
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
  formData.article_id = ''
  formData.article_name = ''
  formData.performance_trend = ''
  formData.hierarchical_data = []
}

// 获取表单数据
const getFormData = () => {
  return { ...formData }
}

// 暴露方法给父组件
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
.paper-form {
  width: 100%;
  padding: 20px;
  background: #fff;
  border-radius: 8px;

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
      }
    }

    .material-item {
      margin-bottom: 30px;
      padding: 20px;
      background: #fff;
      border-radius: 6px;
      border: 1px solid #dcdfe6;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);

      &:last-child {
        margin-bottom: 0;
      }

      .material-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 15px;
        padding-bottom: 10px;
        border-bottom: 1px solid #ebeef5;

        .material-index {
          font-size: 14px;
          font-weight: 600;
          color: #606266;
        }
      }

      .properties-section {
        margin-top: 20px;
        padding: 15px;
        background: #f5f7fa;
        border-radius: 4px;

        .properties-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;

          .properties-label {
            font-size: 14px;
            font-weight: 600;
            color: #606266;
          }
        }

        .properties-table {
          margin-top: 10px;

          :deep(.el-input__inner) {
            padding: 0 8px;
          }
        }
      }
    }
  }

  :deep(.el-form-item) {
    margin-bottom: 18px;

    .el-form-item__label {
      font-weight: 500;
      color: #606266;
    }
  }

  :deep(.el-textarea__inner) {
    font-family: inherit;
  }

  :deep(.el-empty) {
    padding: 20px 0;
  }
}
</style>


