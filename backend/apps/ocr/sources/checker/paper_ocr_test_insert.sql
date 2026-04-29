-- ==============================================================================
-- 论文OCR结果SQL导入脚本
-- 生成时间: 2025-11-11 16:50:48
-- ==============================================================================

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 开始事务
START TRANSACTION;

-- 1. 插入文献记录
INSERT INTO paper_articles (
    file_id,
    article_id,
    article_name,
    performance_trend,
    status,
    review_status,
    created_at,
    updated_at
) VALUES (
    5147,
    'A1',
    '双组分缩合型有机硅电子灌封胶的制备及其导热阻燃性能研究',
    '1、添加γ－氨丙基三乙氧基硅烷缩短封灌胶表干时间;2、降低甲基三甲氧基硅烷、或增大二甲基二乙氧基硅烷含量，延长封灌胶表干时间',
    'completed',
    'pending',
    NOW(),
    NOW()
);

-- 获取插入的文献ID
SET @article_id = LAST_INSERT_ID();

-- 2.1 插入材料/中间体记录
INSERT INTO paper_material_intermediates (
    article_id,
    material_id,
    material_name,
    cas_number,
    intermediate_id,
    intermediate_name,
    intermediate_composition,
    sort_order,
    created_at,
    updated_at
) VALUES (
    @article_id,
    'A1M1',
    'α，ω－二羟基聚二甲基硅氧烷，黏度4000MPa·s',
    '',
    'A1I1',
    'A组分：107基础胶+α-氧化铝+氢氧化镁+二甲基硅油',
    'A1I1：A1I2=10：1（质量比）',
    1,
    NOW(),
    NOW()
);

-- 获取插入的材料/中间体ID
SET @material_intermediate_id_1 = LAST_INSERT_ID();

-- 2.1.1 插入性能记录
INSERT INTO paper_properties (
    article_id,
    material_intermediate_id,
    property_id,
    property_name,
    property_value,
    unit,
    test_method,
    sort_order,
    created_at,
    updated_at
) VALUES (
    @article_id,
    @material_intermediate_id_1,
    'A1P1',
    '粘度／黏度 MPa·S',
    '1900',
    '',
    '',
    1,
    NOW(),
    NOW()
);

-- 2.1.2 插入性能记录
INSERT INTO paper_properties (
    article_id,
    material_intermediate_id,
    property_id,
    property_name,
    property_value,
    unit,
    test_method,
    sort_order,
    created_at,
    updated_at
) VALUES (
    @article_id,
    @material_intermediate_id_1,
    'A1P2',
    '热导率（Thermal Conductivity） W/(m·K)',
    '0.826',
    '',
    '',
    2,
    NOW(),
    NOW()
);

-- 2.2 插入材料/中间体记录
INSERT INTO paper_material_intermediates (
    article_id,
    material_id,
    material_name,
    cas_number,
    intermediate_id,
    intermediate_name,
    intermediate_composition,
    sort_order,
    created_at,
    updated_at
) VALUES (
    @article_id,
    'A1M2',
    'α－氧化铝, 粒径10μm',
    '1344-28-1',
    'A1I2',
    'B组分：甲基三甲氧基硅烷：二甲基二乙氧基硅烷：γ－氨丙基三乙氧基硅烷=85:6:15（质量比）、二月桂酸二丁基锡',
    'A1I1：A1I2=10:1（质量比）',
    2,
    NOW(),
    NOW()
);

-- 获取插入的材料/中间体ID
SET @material_intermediate_id_2 = LAST_INSERT_ID();


-- 提交事务
COMMIT;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- SQL脚本生成完成
-- ==============================================================================
