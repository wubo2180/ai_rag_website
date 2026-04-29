-- 创建OCR任务表
-- 用于异步OCR识别任务队列

CREATE TABLE IF NOT EXISTS `ocr_tasks` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `file_id` INT NOT NULL COMMENT '关联文件ID',
  `task_id` VARCHAR(50) NOT NULL UNIQUE COMMENT '任务ID（UUID）',
  `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/processing/completed/failed',
  `progress` INT DEFAULT 0 COMMENT '进度百分比（0-100）',
  `current_step` VARCHAR(100) DEFAULT NULL COMMENT '当前处理步骤',
  `result` JSON DEFAULT NULL COMMENT '识别结果（JSON格式）',
  `error_message` TEXT DEFAULT NULL COMMENT '错误信息',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `started_at` DATETIME DEFAULT NULL COMMENT '开始时间',
  `completed_at` DATETIME DEFAULT NULL COMMENT '完成时间',
  `user_id` INT NOT NULL COMMENT '请求用户ID',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  KEY `idx_file_id` (`file_id`),
  KEY `idx_status` (`status`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_ocr_tasks_file_id` FOREIGN KEY (`file_id`) REFERENCES `files` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_ocr_tasks_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='OCR异步任务表';

-- 创建索引以提高查询性能
CREATE INDEX `idx_status_created_at` ON `ocr_tasks` (`status`, `created_at`);
CREATE INDEX `idx_user_status` ON `ocr_tasks` (`user_id`, `status`);



