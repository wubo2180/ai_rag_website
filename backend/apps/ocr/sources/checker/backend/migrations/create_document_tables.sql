-- =====================================================
-- OCR系统通用化重构 - 数据库表创建SQL
-- =====================================================
-- 文件: create_document_tables.sql
-- 说明: 创建文件类型配置表和通用文档表
-- 执行顺序: 1. file_type_configs  2. document_basic
-- =====================================================

-- =====================================================
-- 1. 文件类型配置表 (file_type_configs)
-- =====================================================
CREATE TABLE IF NOT EXISTS `file_type_configs` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  
  -- 基本信息
  `type_code` VARCHAR(50) NOT NULL UNIQUE COMMENT '类型代码，如：commission、paper',
  `type_name` VARCHAR(100) NOT NULL COMMENT '类型名称，如：委托单、论文',
  `type_description` TEXT COMMENT '类型描述',
  
  -- OCR配置
  `ocr_model_api` VARCHAR(200) COMMENT 'OCR模型API地址',
  `ocr_model_type` VARCHAR(50) DEFAULT 'internal' COMMENT '模型类型：internal（内部）/external（外部）',
  `ocr_config` JSON COMMENT 'OCR配置参数（JSON格式）',
  
  -- 数据存储配置
  `storage_table_basic` VARCHAR(100) NOT NULL COMMENT '基本信息存储表名',
  `storage_table_items` VARCHAR(100) COMMENT '子项目存储表名（如测试项目）',
  `storage_table_details` VARCHAR(100) COMMENT '详情存储表名（如特殊测试）',
  
  -- 表单配置
  `form_config` JSON COMMENT '表单配置（JSON格式），定义表单字段和布局',
  `form_component` VARCHAR(200) COMMENT '前端表单组件路径',
  
  -- 字段映射配置
  `field_mapping` JSON COMMENT 'OCR结果到数据库字段的映射配置',
  
  -- 验证规则
  `validation_rules` JSON COMMENT '数据验证规则（JSON格式）',
  
  -- 状态字段
  `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
  `sort_order` INT DEFAULT 0 COMMENT '排序序号',
  
  -- 系统字段
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_type_code` (`type_code`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_sort_order` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='文件类型配置表';


-- =====================================================
-- 2. 通用文档数据表 (document_basic)
-- =====================================================
CREATE TABLE IF NOT EXISTS `document_basic` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  
  -- 文件关联
  `file_id` INT NOT NULL COMMENT '文件ID',
  `file_type_code` VARCHAR(50) NOT NULL COMMENT '文件类型代码',
  
  -- 文档唯一标识
  `document_number` VARCHAR(100) NOT NULL UNIQUE COMMENT '文档编号（唯一）',
  
  -- 文档数据（JSON格式存储）
  `basic_data` JSON COMMENT '基本数据（JSON格式）',
  `items_data` JSON COMMENT '子项目数据（JSON格式）',
  `details_data` JSON COMMENT '详细数据（JSON格式）',
  
  -- OCR相关
  `ocr_raw_data` TEXT COMMENT 'OCR原始识别数据（JSON格式）',
  `ocr_confidence` VARCHAR(10) COMMENT '平均置信度',
  
  -- 状态信息
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '文档状态',
  `review_status` VARCHAR(20) DEFAULT 'pending' COMMENT '审核状态',
  `reviewer_id` INT COMMENT '审核人ID',
  `reviewed_at` DATETIME COMMENT '审核时间',
  `review_comments` TEXT COMMENT '审核意见',
  
  -- 系统字段
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_document_number` (`document_number`),
  KEY `idx_file_id` (`file_id`),
  KEY `idx_file_type_code` (`file_type_code`),
  KEY `idx_status` (`status`),
  KEY `idx_review_status` (`review_status`),
  KEY `idx_reviewer_id` (`reviewer_id`),
  KEY `idx_created_at` (`created_at`),
  
  -- 外键约束
  CONSTRAINT `fk_document_file` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_document_file_type` FOREIGN KEY (`file_type_code`) REFERENCES `file_type_configs` (`type_code`) ON DELETE RESTRICT,
  CONSTRAINT `fk_document_reviewer` FOREIGN KEY (`reviewer_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='通用文档数据表';


-- =====================================================
-- 3. 初始化数据 - 委托单类型配置
-- =====================================================
INSERT INTO `file_type_configs` (
  `type_code`,
  `type_name`,
  `type_description`,
  `ocr_model_api`,
  `ocr_model_type`,
  `storage_table_basic`,
  `storage_table_items`,
  `storage_table_details`,
  `form_component`,
  `ocr_config`,
  `form_config`,
  `field_mapping`,
  `is_active`,
  `sort_order`
) VALUES (
  'commission',
  '委托单',
  '检测委托测试申请单',
  '/api/external-ocr/recognize',
  'external',
  'commission_basic',
  'test_items',
  'special_tests',
  'CommissionForm',
  JSON_OBJECT(
    'timeout', 300,
    'retry', 3
  ),
  JSON_OBJECT(
    'use_dynamic_form', FALSE,
    'component_path', '/views/FileRecognize/components/CommissionForm.vue'
  ),
  JSON_OBJECT(
    'commission_number', 'basic_info.commission_number',
    'form_number', 'basic_info.form_number',
    'commissioner', 'basic_info.commissioner'
  ),
  1,
  1
) ON DUPLICATE KEY UPDATE
  `type_name` = VALUES(`type_name`),
  `type_description` = VALUES(`type_description`);


-- =====================================================
-- 4. 初始化数据 - 论文类型配置
-- =====================================================
INSERT INTO `file_type_configs` (
  `type_code`,
  `type_name`,
  `type_description`,
  `ocr_model_api`,
  `ocr_model_type`,
  `storage_table_basic`,
  `storage_table_items`,
  `storage_table_details`,
  `form_component`,
  `ocr_config`,
  `form_config`,
  `field_mapping`,
  `validation_rules`,
  `is_active`,
  `sort_order`
) VALUES (
  'paper',
  '论文',
  '学术论文检测分析',
  '/api/ocr/paper',
  'internal',
  'document_basic',
  NULL,
  NULL,
  NULL,
  JSON_OBJECT(
    'timeout', 300,
    'retry', 3,
    'language', 'ch'
  ),
  JSON_OBJECT(
    'use_dynamic_form', TRUE,
    'sections', JSON_ARRAY(
      JSON_OBJECT(
        'title', '基本信息',
        'fields', JSON_ARRAY(
          JSON_OBJECT('name', 'paper_title', 'label', '论文标题', 'type', 'text', 'required', TRUE, 'span', 24, 'placeholder', '请输入论文标题'),
          JSON_OBJECT('name', 'paper_number', 'label', '论文编号', 'type', 'text', 'required', TRUE, 'span', 12, 'placeholder', '系统自动生成或手动输入'),
          JSON_OBJECT(
            'name', 'paper_type', 
            'label', '论文类型', 
            'type', 'select', 
            'required', TRUE, 
            'span', 12,
            'options', JSON_ARRAY(
              JSON_OBJECT('label', '期刊论文', 'value', 'journal'),
              JSON_OBJECT('label', '会议论文', 'value', 'conference'),
              JSON_OBJECT('label', '学位论文', 'value', 'thesis'),
              JSON_OBJECT('label', '其他', 'value', 'other')
            )
          )
        )
      ),
      JSON_OBJECT(
        'title', '作者信息',
        'fields', JSON_ARRAY(
          JSON_OBJECT('name', 'author', 'label', '作者', 'type', 'text', 'required', TRUE, 'span', 12, 'placeholder', '请输入作者姓名'),
          JSON_OBJECT('name', 'co_authors', 'label', '共同作者', 'type', 'text', 'span', 12, 'placeholder', '多个作者用逗号分隔'),
          JSON_OBJECT('name', 'institution', 'label', '所属机构', 'type', 'text', 'required', TRUE, 'span', 24, 'placeholder', '请输入所属机构'),
          JSON_OBJECT('name', 'email', 'label', '联系邮箱', 'type', 'text', 'span', 12, 'placeholder', '请输入联系邮箱'),
          JSON_OBJECT('name', 'phone', 'label', '联系电话', 'type', 'text', 'span', 12, 'placeholder', '请输入联系电话')
        )
      ),
      JSON_OBJECT(
        'title', '发表信息',
        'fields', JSON_ARRAY(
          JSON_OBJECT('name', 'journal_name', 'label', '期刊/会议名称', 'type', 'text', 'span', 12, 'placeholder', '请输入期刊或会议名称'),
          JSON_OBJECT('name', 'publish_date', 'label', '发表日期', 'type', 'date', 'span', 12, 'placeholder', '请选择发表日期'),
          JSON_OBJECT('name', 'volume_issue', 'label', '卷期', 'type', 'text', 'span', 12, 'placeholder', '例如：Vol.10, No.3'),
          JSON_OBJECT('name', 'page_range', 'label', '页码范围', 'type', 'text', 'span', 12, 'placeholder', '例如：123-135'),
          JSON_OBJECT('name', 'doi', 'label', 'DOI', 'type', 'text', 'span', 24, 'placeholder', '请输入DOI')
        )
      ),
      JSON_OBJECT(
        'title', '内容信息',
        'fields', JSON_ARRAY(
          JSON_OBJECT('name', 'keywords', 'label', '关键词', 'type', 'text', 'required', TRUE, 'span', 24, 'placeholder', '多个关键词用逗号分隔'),
          JSON_OBJECT('name', 'abstract', 'label', '摘要', 'type', 'textarea', 'required', TRUE, 'span', 24, 'rows', 5, 'placeholder', '请输入论文摘要'),
          JSON_OBJECT(
            'name', 'research_field',
            'label', '研究领域',
            'type', 'select',
            'span', 12,
            'options', JSON_ARRAY(
              JSON_OBJECT('label', '计算机科学', 'value', 'cs'),
              JSON_OBJECT('label', '电子工程', 'value', 'ee'),
              JSON_OBJECT('label', '材料科学', 'value', 'ms'),
              JSON_OBJECT('label', '化学', 'value', 'chem'),
              JSON_OBJECT('label', '物理', 'value', 'phys'),
              JSON_OBJECT('label', '生物', 'value', 'bio'),
              JSON_OBJECT('label', '其他', 'value', 'other')
            )
          ),
          JSON_OBJECT(
            'name', 'language',
            'label', '语言',
            'type', 'select',
            'span', 12,
            'options', JSON_ARRAY(
              JSON_OBJECT('label', '中文', 'value', 'zh'),
              JSON_OBJECT('label', '英文', 'value', 'en'),
              JSON_OBJECT('label', '其他', 'value', 'other')
            )
          )
        )
      ),
      JSON_OBJECT(
        'title', '质量评估',
        'fields', JSON_ARRAY(
          JSON_OBJECT('name', 'impact_factor', 'label', '影响因子', 'type', 'number', 'span', 12, 'min', 0, 'placeholder', '请输入影响因子'),
          JSON_OBJECT('name', 'citation_count', 'label', '引用次数', 'type', 'number', 'span', 12, 'min', 0, 'placeholder', '请输入引用次数'),
          JSON_OBJECT(
            'name', 'peer_reviewed',
            'label', '是否同行评审',
            'type', 'radio',
            'span', 12,
            'options', JSON_ARRAY(
              JSON_OBJECT('label', '是', 'value', '是'),
              JSON_OBJECT('label', '否', 'value', '否')
            )
          ),
          JSON_OBJECT(
            'name', 'open_access',
            'label', '开放获取',
            'type', 'radio',
            'span', 12,
            'options', JSON_ARRAY(
              JSON_OBJECT('label', '是', 'value', '是'),
              JSON_OBJECT('label', '否', 'value', '否')
            )
          )
        )
      ),
      JSON_OBJECT(
        'title', '备注信息',
        'fields', JSON_ARRAY(
          JSON_OBJECT('name', 'notes', 'label', '备注', 'type', 'textarea', 'span', 24, 'rows', 3, 'placeholder', '请输入备注信息')
        )
      )
    )
  ),
  JSON_OBJECT(
    'paper_title', 'basic_data.paper_title',
    'paper_number', 'basic_data.paper_number',
    'author', 'basic_data.author',
    'institution', 'basic_data.institution'
  ),
  JSON_OBJECT(
    'paper_title', JSON_OBJECT('required', TRUE, 'min_length', 5),
    'paper_number', JSON_OBJECT('required', TRUE, 'pattern', '^PAPER[0-9]{14}$'),
    'author', JSON_OBJECT('required', TRUE),
    'email', JSON_OBJECT('pattern', '^[\\w-\\.]+@([\\w-]+\\.)+[\\w-]{2,4}$')
  ),
  1,
  2
) ON DUPLICATE KEY UPDATE
  `type_name` = VALUES(`type_name`),
  `type_description` = VALUES(`type_description`);


-- =====================================================
-- 5. 查询验证
-- =====================================================
-- 查看创建的表
-- SHOW TABLES LIKE 'file_type_configs';
-- SHOW TABLES LIKE 'document_basic';

-- 查看表结构
-- DESC file_type_configs;
-- DESC document_basic;

-- 查看初始化的配置数据
-- SELECT type_code, type_name, is_active FROM file_type_configs;

-- =====================================================
-- 执行说明：
-- =====================================================
-- 1. 在MySQL中执行此SQL文件：
--    mysql -u用户名 -p数据库名 < create_document_tables.sql
--
-- 2. 或者在MySQL命令行中：
--    USE ocr_system;
--    SOURCE /path/to/create_document_tables.sql;
--
-- 3. Python脚本方式（推荐）：
--    python backend/migrations/create_document_tables.py
--    python backend/migrations/create_paper_config.py
-- =====================================================


