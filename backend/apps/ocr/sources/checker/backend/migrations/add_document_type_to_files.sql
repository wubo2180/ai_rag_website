-- ========================================
-- 为files表添加document_type_code字段
-- ========================================
-- 执行日期: 2025-11-05
-- 说明: 添加文档业务类型字段，用于区分不同类型的文档（委托单、论文等）
-- ========================================

-- 1. 添加document_type_code字段
ALTER TABLE `files` 
ADD COLUMN `document_type_code` VARCHAR(50) NULL COMMENT '文档类型代码（commission/paper等）' AFTER `file_type`;

-- 2. 为现有的委托单文件设置默认类型（可选，根据实际需求执行）
-- UPDATE `files` SET `document_type_code` = 'commission' WHERE `document_type_code` IS NULL;

-- 3. 创建索引以提升查询性能
CREATE INDEX `idx_document_type_code` ON `files` (`document_type_code`);

-- 4. 验证字段是否添加成功
SELECT 
    COLUMN_NAME, 
    COLUMN_TYPE, 
    IS_NULLABLE, 
    COLUMN_COMMENT 
FROM 
    INFORMATION_SCHEMA.COLUMNS 
WHERE 
    TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME = 'files' 
    AND COLUMN_NAME = 'document_type_code';

-- ========================================
-- 回滚脚本（如果需要撤销更改）
-- ========================================
-- ALTER TABLE `files` DROP INDEX `idx_document_type_code`;
-- ALTER TABLE `files` DROP COLUMN `document_type_code`;


