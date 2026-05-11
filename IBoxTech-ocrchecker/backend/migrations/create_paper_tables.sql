-- =====================================================
-- 论文数据存储表结构 - 三表方案
-- =====================================================
-- 文件: create_paper_tables.sql
-- 说明: 创建论文专用的关系型数据表（3张表）
-- 表结构: paper_articles (文献) -> paper_material_intermediates (材料/中间体) -> paper_properties (性能)
-- =====================================================

-- =====================================================
-- 1. 论文文献表 (paper_articles)
-- =====================================================
DROP TABLE IF EXISTS `paper_properties`;
DROP TABLE IF EXISTS `paper_material_intermediates`;
DROP TABLE IF EXISTS `paper_articles`;

CREATE TABLE `paper_articles` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  
  -- 关联文件
  `file_id` INT NOT NULL COMMENT '关联的文件ID',
  
  -- 文献基本信息
  `article_id` VARCHAR(50) NOT NULL COMMENT '文献编号，如：A1',
  `article_name` TEXT NOT NULL COMMENT '文献名称/标题',
  `performance_trend` TEXT COMMENT '性能趋势描述',
  
  -- 审核状态
  `status` VARCHAR(20) DEFAULT 'pending' COMMENT '数据状态：pending/completed/failed',
  `review_status` VARCHAR(20) DEFAULT 'pending' COMMENT '审核状态：pending/approved/rejected',
  `reviewer_id` INT COMMENT '审核人ID',
  `reviewed_at` DATETIME COMMENT '审核时间',
  `review_comments` TEXT COMMENT '审核意见',
  
  -- 系统字段
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_article_id` (`article_id`),
  KEY `idx_file_id` (`file_id`),
  KEY `idx_review_status` (`review_status`),
  KEY `idx_created_at` (`created_at`),
  
  -- 外键约束
  CONSTRAINT `fk_paper_article_file` 
    FOREIGN KEY (`file_id`) 
    REFERENCES `files` (`id`) 
    ON DELETE CASCADE,
  CONSTRAINT `fk_paper_article_reviewer` 
    FOREIGN KEY (`reviewer_id`) 
    REFERENCES `users` (`id`) 
    ON DELETE SET NULL
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='论文文献表';


-- =====================================================
-- 2. 材料/中间体表 (paper_material_intermediates)
-- =====================================================
CREATE TABLE `paper_material_intermediates` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  
  -- 关联文献
  `article_id` VARCHAR(50) NOT NULL COMMENT '关联的文献编号',
  
  -- 实体类型标识
  `entity_type` VARCHAR(20) NOT NULL DEFAULT 'material' COMMENT '实体类型：material(原材料)/intermediate(中间体)',
  
  -- 材料信息
  `material_id` VARCHAR(50) NOT NULL COMMENT '材料编号，如：A1M1',
  `material_name` TEXT COMMENT '原材料名称及规格',
  `cas_number` VARCHAR(50) COMMENT 'CAS号',
  
  -- 中间体信息
  `intermediate_id` VARCHAR(50) COMMENT '中间体编号，如：A1I1',
  `intermediate_name` TEXT COMMENT '中间体名称',
  `intermediate_composition` TEXT COMMENT '中间体组成/配方',
  
  -- 层级关系（可选，用于表示材料和中间体的关系）
  `parent_id` INT COMMENT '父级ID（用于关联材料和中间体的关系）',
  `sort_order` INT DEFAULT 0 COMMENT '排序序号',
  
  -- 系统字段
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_material_id` (`material_id`),
  KEY `idx_article_id` (`article_id`),
  KEY `idx_entity_type` (`entity_type`),
  KEY `idx_intermediate_id` (`intermediate_id`),
  KEY `idx_parent_id` (`parent_id`),
  KEY `idx_sort_order` (`sort_order`),
  
  -- 外键约束
  CONSTRAINT `fk_paper_mi_article` 
    FOREIGN KEY (`article_id`) 
    REFERENCES `paper_articles` (`article_id`) 
    ON DELETE CASCADE,
  CONSTRAINT `fk_paper_mi_parent` 
    FOREIGN KEY (`parent_id`) 
    REFERENCES `paper_material_intermediates` (`id`) 
    ON DELETE SET NULL
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='论文材料和中间体表';


-- =====================================================
-- 3. 性能数据表 (paper_properties)
-- =====================================================
CREATE TABLE `paper_properties` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  
  -- 关联材料/中间体
  `material_intermediate_id` INT NOT NULL COMMENT '关联的材料/中间体ID',
  `article_id` VARCHAR(50) NOT NULL COMMENT '关联的文献编号（冗余字段，便于查询）',
  
  -- 性能信息
  `property_id` VARCHAR(50) NOT NULL COMMENT '性能编号，如：A1P1',
  `property_name` VARCHAR(200) NOT NULL COMMENT '性能名称，如：粘度/黏度 MPa·S',
  `property_value` VARCHAR(500) COMMENT '性能值',
  `property_unit` VARCHAR(50) COMMENT '单位（可选，从property_name中提取）',
  
  -- 排序
  `sort_order` INT DEFAULT 0 COMMENT '排序序号',
  
  -- 系统字段
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_property_id` (`property_id`),
  KEY `idx_material_intermediate_id` (`material_intermediate_id`),
  KEY `idx_article_id` (`article_id`),
  KEY `idx_property_name` (`property_name`),
  KEY `idx_sort_order` (`sort_order`),
  
  -- 外键约束
  CONSTRAINT `fk_paper_property_mi` 
    FOREIGN KEY (`material_intermediate_id`) 
    REFERENCES `paper_material_intermediates` (`id`) 
    ON DELETE CASCADE,
  CONSTRAINT `fk_paper_property_article` 
    FOREIGN KEY (`article_id`) 
    REFERENCES `paper_articles` (`article_id`) 
    ON DELETE CASCADE
    
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='论文性能数据表';


-- =====================================================
-- 示例数据插入
-- =====================================================

-- 插入测试文献
INSERT INTO `paper_articles` 
  (`file_id`, `article_id`, `article_name`, `performance_trend`, `status`, `review_status`)
VALUES 
  (1, 'A1', '双组分缩合型有机硅电子灌封胶的制备及其导热阻燃性能研究', 
   '1、添加γ－氨丙基三乙氧基硅烷缩短封灌胶表干时间;2、降低甲基三甲氧基硅烷、或增大二甲基二乙氧基硅烷含量，延长封灌胶表干时间', 
   'pending', 'pending');

-- 插入材料/中间体（方式1：扁平化存储）
-- 材料1
INSERT INTO `paper_material_intermediates` 
  (`article_id`, `entity_type`, `material_id`, `material_name`, `cas_number`, 
   `intermediate_id`, `intermediate_name`, `intermediate_composition`, `sort_order`)
VALUES 
  ('A1', 'material', 'A1M1', 'α，ω－二羟基聚二甲基硅氧烷，黏度4000MPa·s', '', 
   'A1I1', 'A组分：107基础胶+α-氧化铝+氢氧化镁+二甲基硅油', 'A1I1：A1I2=10：1（质量比）', 1);

-- 材料2
INSERT INTO `paper_material_intermediates` 
  (`article_id`, `entity_type`, `material_id`, `material_name`, `cas_number`, 
   `intermediate_id`, `intermediate_name`, `intermediate_composition`, `sort_order`)
VALUES 
  ('A1', 'material', 'A1M2', 'α－氧化铝, 粒径10μm', '1344-28-1', 
   'A1I2', 'B组分：甲基三甲氧基硅烷：二甲基二乙氧基硅烷：γ－氨丙基三乙氧基硅烷=85:6:15（质量比）、二月桂酸二丁基锡', 
   'A1I1：A1I2=10:1（质量比）', 2);

-- 插入性能数据
INSERT INTO `paper_properties` 
  (`material_intermediate_id`, `article_id`, `property_id`, `property_name`, `property_value`, `sort_order`)
VALUES 
  (1, 'A1', 'A1P1', '粘度／黏度 MPa·S', '1900', 1),
  (1, 'A1', 'A1P2', '热导率（Thermal Conductivity） W/(m·K)', '0.826', 2),
  (1, 'A1', 'A1P3', '失重率（weight loss）%', '', 3),
  (1, 'A1', 'A1P4', '拉伸强度(Tensile Strength) MPa', '0.73', 4),
  (1, 'A1', 'A1P5', '介电强度（Dielectric Strength） kV/mm', '', 5),
  (1, 'A1', 'A1P6', '硬度（Hardness） °', '21', 6),
  (1, 'A1', 'A1P7', '其他性能（Others）', '断裂伸长率104%，表干时间29min，垂直燃烧等级FV-0', 7),
  (2, 'A1', 'A1P8', '粘度／黏度 MPa·S', '', 8),
  (2, 'A1', 'A1P9', '热导率（Thermal Conductivity） W/(m·K)', '', 9);


-- =====================================================
-- 查询示例
-- =====================================================

-- 查询1：获取完整的文献数据（包含所有层级）
SELECT 
  a.article_id,
  a.article_name,
  a.performance_trend,
  mi.material_id,
  mi.material_name,
  mi.cas_number,
  mi.intermediate_id,
  mi.intermediate_name,
  mi.intermediate_composition,
  p.property_id,
  p.property_name,
  p.property_value
FROM paper_articles a
LEFT JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
LEFT JOIN paper_properties p ON mi.id = p.material_intermediate_id
WHERE a.article_id = 'A1'
ORDER BY mi.sort_order, p.sort_order;


-- 查询2：按材料名称搜索
SELECT 
  a.article_id,
  a.article_name,
  mi.material_name,
  mi.cas_number
FROM paper_articles a
JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
WHERE mi.material_name LIKE '%氧化铝%';


-- 查询3：按性能名称搜索
SELECT 
  a.article_id,
  a.article_name,
  mi.material_name,
  p.property_name,
  p.property_value
FROM paper_articles a
JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
JOIN paper_properties p ON mi.id = p.material_intermediate_id
WHERE p.property_name LIKE '%热导率%';


-- 查询4：统计每篇文献的材料和性能数量
SELECT 
  a.article_id,
  a.article_name,
  COUNT(DISTINCT mi.id) AS material_count,
  COUNT(DISTINCT p.id) AS property_count
FROM paper_articles a
LEFT JOIN paper_material_intermediates mi ON a.article_id = mi.article_id
LEFT JOIN paper_properties p ON mi.id = p.material_intermediate_id
GROUP BY a.article_id, a.article_name;


-- =====================================================
-- 索引和性能优化建议
-- =====================================================

-- 如果需要全文搜索，可以添加全文索引
-- ALTER TABLE paper_articles ADD FULLTEXT INDEX ft_article_name (article_name);
-- ALTER TABLE paper_material_intermediates ADD FULLTEXT INDEX ft_material_name (material_name);

-- 如果需要按CAS号精确查询，添加唯一索引
-- ALTER TABLE paper_material_intermediates ADD UNIQUE INDEX uk_cas_number (cas_number);


-- =====================================================
-- 回滚脚本
-- =====================================================
-- DROP TABLE IF EXISTS `paper_properties`;
-- DROP TABLE IF EXISTS `paper_material_intermediates`;
-- DROP TABLE IF EXISTS `paper_articles`;



