# 文件类型区分方案

## 📋 问题分析

在通用化重构后，系统需要支持多种文件类型（委托单、论文等），因此需要在文件上传时或之后明确文件的业务类型（document_type_code）。

当前File模型有：
- `file_type`: 存储文件格式（如：pdf, jpg等）
- **缺少**: `document_type_code`（业务文件类型：commission, paper等）

---

## 🎯 推荐方案（方案1+2组合）

### 方案概览

```
上传时 → 用户选择文件类型 → 保存到File.document_type_code
     ↓
识别时 → 根据document_type_code选择处理方式
     ↓
显示时 → 根据document_type_code显示对应表单
```

---

## 🔧 具体实施方案

### 1. 数据库层：修改File模型

#### 1.1 添加document_type_code字段

**SQL迁移脚本：**
```sql
-- 文件：backend/migrations/add_document_type_to_files.sql

-- 添加document_type_code字段
ALTER TABLE `files` 
ADD COLUMN `document_type_code` VARCHAR(50) 
COMMENT '文档类型代码（commission/paper等）' 
AFTER `file_type`;

-- 添加外键约束（可选，建议添加）
ALTER TABLE `files`
ADD CONSTRAINT `fk_files_document_type` 
FOREIGN KEY (`document_type_code`) 
REFERENCES `file_type_configs` (`type_code`) 
ON DELETE SET NULL;

-- 添加索引
ALTER TABLE `files` ADD INDEX `idx_document_type_code` (`document_type_code`);

-- 更新现有数据（将现有文件默认设置为委托单）
UPDATE `files` 
SET `document_type_code` = 'commission' 
WHERE `document_type_code` IS NULL;
```

#### 1.2 更新File模型（Python）

```python
# backend/app/models/file.py

class File(db.Model):
    """文件模型"""
    
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment='原始文件名')
    stored_filename = Column(String(255), nullable=False, comment='存储文件名（UUID）')
    file_path = Column(String(500), nullable=False, comment='MinIO中的文件路径')
    file_size = Column(BigInteger, nullable=False, comment='文件大小（字节）')
    file_type = Column(String(50), nullable=False, comment='文件格式类型（pdf/jpg等）')
    
    # 新增：文档业务类型
    document_type_code = Column(
        String(50), 
        ForeignKey('file_type_configs.type_code'),
        nullable=True,  # 允许为空，上传后可以修改
        comment='文档类型代码（commission/paper等）'
    )
    
    mime_type = Column(String(100), nullable=False, comment='MIME类型')
    # ... 其他字段保持不变
    
    # 添加关系
    document_type_config = db.relationship(
        'FileTypeConfig', 
        foreign_keys=[document_type_code],
        backref='files',
        lazy=True
    )
```

---

### 2. API层：修改上传接口

#### 2.1 单文件上传（支持类型参数）

```python
# backend/app/api/files.py

@api_bp.route('/files/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """单个文件上传"""
    try:
        current_user_id = get_jwt_identity()
        
        # 检查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        file = request.files['file']
        
        # 获取参数
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else None
        
        # 🆕 新增：获取文档类型
        document_type_code = request.form.get('document_type_code', 'commission')  # 默认委托单
        
        # 验证文档类型是否有效
        from models import get_models
        models = get_models()
        FileTypeConfig = models.get('FileTypeConfig')
        
        if FileTypeConfig:
            type_config = FileTypeConfig.query.filter_by(
                type_code=document_type_code,
                is_active=True
            ).first()
            
            if not type_config:
                return jsonify({
                    'success': False,
                    'message': f'无效的文档类型: {document_type_code}'
                }), 400
        
        # 处理文件名
        filename = secure_filename(file.filename)
        
        # 使用文件服务上传
        file_service = FileService()
        result = file_service.upload_file(
            file_obj=file,
            filename=filename,
            uploader_id=current_user_id,
            description=description,
            tags=tags,
            document_type_code=document_type_code  # 🆕 传递文档类型
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文件上传失败: {str(e)}'
        }), 500
```

#### 2.2 批量上传（支持类型参数）

```python
@api_bp.route('/files/batch-upload', methods=['POST'])
@jwt_required()
def batch_upload_files():
    """批量文件上传"""
    try:
        current_user_id = get_jwt_identity()
        
        # 检查文件
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        files = request.files.getlist('files')
        
        # 获取参数
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else None
        document_type_code = request.form.get('document_type_code', 'commission')  # 🆕
        
        # 准备文件数据
        files_data = []
        for file in files:
            if file.filename:
                filename = secure_filename(file.filename)
                files_data.append({
                    'file_obj': file,
                    'filename': filename
                })
        
        # 批量上传
        file_service = FileService()
        result = file_service.batch_upload_files(
            files_data=files_data,
            uploader_id=current_user_id,
            description=description,
            tags=tags,
            document_type_code=document_type_code  # 🆕
        )
        
        return jsonify({
            'success': True,
            'message': f'批量上传完成',
            'data': result
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'批量上传失败: {str(e)}'
        }), 500
```

#### 2.3 新增：更新文件类型接口

```python
@api_bp.route('/files/<int:file_id>/document-type', methods=['PUT'])
@jwt_required()
def update_file_document_type(file_id):
    """
    更新文件的文档类型
    用于上传后修改文件类型
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        document_type_code = data.get('document_type_code')
        if not document_type_code:
            return jsonify({
                'success': False,
                'message': '缺少document_type_code参数'
            }), 400
        
        # 验证类型是否有效
        from models import get_models
        models = get_models()
        FileTypeConfig = models.get('FileTypeConfig')
        File = models.get('File')
        
        type_config = FileTypeConfig.query.filter_by(
            type_code=document_type_code,
            is_active=True
        ).first()
        
        if not type_config:
            return jsonify({
                'success': False,
                'message': f'无效的文档类型: {document_type_code}'
            }), 400
        
        # 获取文件
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 权限检查：只有上传者和管理员可以修改
        from models.user import User
        user = User.query.get(current_user_id)
        if file_record.uploader_id != current_user_id and not user.is_admin():
            return jsonify({
                'success': False,
                'message': '无权限修改此文件'
            }), 403
        
        # 更新文档类型
        file_record.document_type_code = document_type_code
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文档类型更新成功',
            'data': {
                'file_id': file_id,
                'document_type_code': document_type_code,
                'document_type_name': type_config.type_name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500
```

---

### 3. 服务层：修改FileService

```python
# backend/app/services/file_service.py

class FileService:
    def upload_file(self, file_obj, filename, uploader_id, 
                   description=None, tags=None, document_type_code=None):  # 🆕
        """上传单个文件"""
        try:
            # ... 现有的上传逻辑 ...
            
            # 创建文件记录
            file_record = File(
                filename=filename,
                stored_filename=stored_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_extension,
                mime_type=mime_type,
                uploader_id=uploader_id,
                document_type_code=document_type_code  # 🆕 保存文档类型
            )
            
            if description:
                file_record.description = description
            if tags:
                file_record.set_tags_list(tags)
            
            # ... 保存到数据库 ...
```

---

### 4. 前端：上传页面修改

#### 4.1 添加文件类型选择器

```vue
<!-- frontend/src/views/FileUpload/index.vue -->

<template>
  <div class="file-upload-container">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">文件上传</h1>
        <p class="page-subtitle">支持 PDF、JPG、PNG、TIFF 格式</p>
      </div>
      
      <!-- 🆕 文件类型选择器 -->
      <div class="header-filters">
        <el-select
          v-model="selectedDocumentType"
          placeholder="选择文件类型"
          style="width: 200px"
          @change="handleDocumentTypeChange"
        >
          <el-option
            v-for="type in documentTypes"
            :key="type.type_code"
            :label="type.type_name"
            :value="type.type_code"
          >
            <span>{{ type.type_name }}</span>
            <span style="color: #8492a6; font-size: 13px">
              {{ type.type_description }}
            </span>
          </el-option>
        </el-select>
      </div>
      
      <div class="header-actions">
        <el-button @click="clearAllFiles">清空列表</el-button>
        <el-button
          type="primary"
          :disabled="!selectedDocumentType || fileList.length === 0"
          @click="startUpload"
        >
          开始上传
        </el-button>
      </div>
    </div>

    <!-- 上传区域 -->
    <el-upload
      ref="uploadRef"
      v-model:file-list="fileList"
      :auto-upload="false"
      :multiple="true"
      drag
    >
      <div class="upload-content">
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="upload-text">
          <p class="upload-title">
            当前上传类型：<strong>{{ currentTypeName }}</strong>
          </p>
          <p>将文件拖拽到此处，或点击上传</p>
        </div>
      </div>
    </el-upload>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getFileTypeConfigs } from '@/api/documents'  // 🆕 导入新API
import { uploadFile, batchUploadFiles } from '@/api/files'

export default {
  name: 'FileUpload',
  setup() {
    const fileList = ref([])
    const selectedDocumentType = ref('commission')  // 🆕 默认委托单
    const documentTypes = ref([])  // 🆕 文件类型列表
    
    // 🆕 加载文件类型配置
    const loadDocumentTypes = async () => {
      try {
        const res = await getFileTypeConfigs()
        if (res.success) {
          documentTypes.value = res.data
          // 如果有数据，默认选择第一个
          if (documentTypes.value.length > 0 && !selectedDocumentType.value) {
            selectedDocumentType.value = documentTypes.value[0].type_code
          }
        }
      } catch (error) {
        console.error('加载文件类型失败:', error)
        ElMessage.error('加载文件类型失败')
      }
    }
    
    // 🆕 当前类型名称
    const currentTypeName = computed(() => {
      const type = documentTypes.value.find(
        t => t.type_code === selectedDocumentType.value
      )
      return type ? type.type_name : '请选择'
    })
    
    // 🆕 文件类型改变
    const handleDocumentTypeChange = (value) => {
      console.log('选择文件类型:', value)
      ElMessage.success(`已切换到 ${currentTypeName.value} 类型`)
    }
    
    // 开始上传
    const startUpload = async () => {
      if (!selectedDocumentType.value) {
        ElMessage.warning('请先选择文件类型')
        return
      }
      
      if (fileList.value.length === 0) {
        ElMessage.warning('请先选择文件')
        return
      }
      
      try {
        const formData = new FormData()
        
        // 添加文件
        fileList.value.forEach(file => {
          formData.append('files', file.raw)
        })
        
        // 🆕 添加文档类型
        formData.append('document_type_code', selectedDocumentType.value)
        
        // 添加其他信息
        if (batchDescription.value) {
          formData.append('description', batchDescription.value)
        }
        if (batchTags.value) {
          formData.append('tags', batchTags.value)
        }
        
        // 调用上传API
        const res = await batchUploadFiles(formData)
        
        if (res.success) {
          ElMessage.success('文件上传成功')
          fileList.value = []
        } else {
          ElMessage.error(res.message || '上传失败')
        }
        
      } catch (error) {
        console.error('上传失败:', error)
        ElMessage.error('上传失败')
      }
    }
    
    onMounted(() => {
      loadDocumentTypes()  // 🆕 页面加载时获取类型列表
    })
    
    return {
      fileList,
      selectedDocumentType,
      documentTypes,
      currentTypeName,
      handleDocumentTypeChange,
      startUpload
    }
  }
}
</script>

<style scoped>
.header-filters {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 0 auto;
}

.upload-text strong {
  color: #409eff;
  font-size: 16px;
}
</style>
```

---

## 📊 完整流程示例

### 流程1：用户上传时选择类型

```
1. 用户打开上传页面
   ↓
2. 页面加载文件类型列表（GET /api/file-type-configs）
   返回：[{type_code: 'commission', type_name: '委托单'}, {type_code: 'paper', type_name: '论文'}]
   ↓
3. 用户选择"论文"类型
   ↓
4. 用户选择PDF文件并点击上传
   ↓
5. 前端调用上传API：POST /api/files/batch-upload
   FormData: {
     files: [file1.pdf, file2.pdf],
     document_type_code: 'paper'  // ← 关键参数
   }
   ↓
6. 后端保存文件记录时设置 document_type_code = 'paper'
   ↓
7. 文件列表显示时可以看到文件类型标签
```

### 流程2：识别时根据类型处理

```
1. 用户在识别页面选择文件
   ↓
2. 前端读取 file.document_type_code = 'paper'
   ↓
3. 调用识别API：POST /api/documents/recognize
   {
     file_id: 123,
     file_type_code: 'paper'  // 从file.document_type_code获取
   }
   ↓
4. 后端根据类型加载对应配置和表单
   ↓
5. 前端根据类型显示对应表单组件
   - commission → CommissionForm
   - paper → DynamicForm
```

---

## 🎯 优势总结

✅ **用户体验好** - 上传时明确选择类型  
✅ **数据准确** - 避免后续识别时类型不明  
✅ **灵活性高** - 可以后期修改类型  
✅ **向后兼容** - 现有数据默认为委托单  
✅ **易于扩展** - 添加新类型只需配置  

---

## 📝 待办清单

- [ ] 执行数据库迁移：添加document_type_code字段
- [ ] 更新File模型
- [ ] 修改上传API接口
- [ ] 修改FileService服务
- [ ] 更新前端上传页面
- [ ] 更新文件列表显示（显示类型标签）
- [ ] 测试上传和识别流程

---

**下一步**: 我可以帮您生成完整的迁移脚本和修改后的代码文件。


