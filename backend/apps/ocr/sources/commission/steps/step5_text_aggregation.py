#!/usr/bin/env python3
"""
V3版本 - 步骤5: 文本聚合
完全不做变更地复制原版本核心逻辑
"""
import cv2
import numpy as np
import json
import math
import datetime
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from utils.base_step import V3BaseStep
from visualization.step_visualizers import TextAggregationVisualizer
from .step2_text_recognition import TextBlock
from .step4_table_line_detection import LineDetectionResult


@dataclass
class TextAggregationResult:
    """文本聚合处理结果"""
    dataset_path: str
    total_content_blocks: int
    merged_blocks: int
    single_blocks: int
    handwritten_blocks: int
    printed_blocks: int
    content_blocks: List[Dict]


class TextAggregationStep(V3BaseStep):
    """V3文本聚合步骤 - 完全复制原版本实现"""
    
    def __init__(self, config: Dict[str, Any], file_manager, logger):
        super().__init__(5, "文本聚合", config, file_manager, logger)
        self.visualizer = TextAggregationVisualizer(
            self.step_number, config.visualization, file_manager, logger
        )
        
        # 原版本算法参数 - 完全不变
        self.processing_params = {
            'max_distance': 200,
            'alignment_tolerance': 80,
            'line_intersection_margin': 20,
            'horizontal_alignment_threshold': 30,
            'short_text_length_threshold': 3
        }
    
    def execute(self, input_data: Tuple[str, LineDetectionResult]) -> TextAggregationResult:
        """执行文本聚合"""
        line_data_path, detection_result = input_data
        
        # 从detection_result中提取所需数据
        text_blocks = detection_result.text_blocks
        image_path = detection_result.original_image_path
        line_data = detection_result.theoretical_line_data  # 使用理论重建后的线条数据
        
        # 5.2 执行智能文本聚合（完全复制原版本算法）
        self.debug("执行智能文本聚合...")
        merge_result = self._intelligent_text_merge(text_blocks, line_data)
        merged_groups = merge_result['merged_groups']  # 只包含真正合并的组
        all_groups = merge_result['all_groups']  # 包含所有组
        
        # 5.3 生成统一的内容块数据集
        self.debug("生成统一内容块数据集...")
        content_blocks = []
        block_id = 1
        
        # 处理所有文本块（包括合并的和单独的）
        processed_indices = set()
        
        # 添加合并的组
        for group in merged_groups:
            if len(group) > 1:
                # 合并组
                group_blocks = [text_blocks[i] for i in group]
                combined_text = ''.join([block.text.strip() for block in group_blocks])
                
                # 计算组的中心位置和边界
                avg_x = sum([block.center_x for block in group_blocks]) / len(group_blocks)
                avg_y = sum([block.center_y for block in group_blocks]) / len(group_blocks)
                min_x = min([block.center_x for block in group_blocks]) - 30
                max_x = max([block.center_x for block in group_blocks]) + 30
                min_y = min([block.center_y for block in group_blocks]) - 15
                max_y = max([block.center_y for block in group_blocks]) + 15
                avg_confidence = sum([block.confidence for block in group_blocks]) / len(group_blocks)
                
                # 判断内容类型
                is_handwritten = any(block.is_handwritten for block in group_blocks)
                
                content_blocks.append({
                    'id': f'content_{block_id}',
                    'text': combined_text,
                    'center_x': avg_x,
                    'center_y': avg_y,
                    'confidence': avg_confidence,
                    'is_handwritten': is_handwritten,
                    'bbox': {'min_x': min_x, 'max_x': max_x, 'min_y': min_y, 'max_y': max_y},
                    'type': 'merged',
                    'block_count': len(group),
                    'merged_from': group
                })
                
                processed_indices.update(group)
                block_id += 1
        
        # 添加未合并的单独块
        for i, block in enumerate(text_blocks):
            if i not in processed_indices:
                content_blocks.append({
                    'id': f'content_{block_id}',
                    'text': block.text.strip(),
                    'center_x': block.center_x,
                    'center_y': block.center_y,
                    'confidence': block.confidence,
                    'is_handwritten': block.is_handwritten,
                    'bbox': {'min_x': block.center_x-30, 'max_x': block.center_x+30, 
                            'min_y': block.center_y-15, 'max_y': block.center_y+15},
                    'type': 'single',
                    'block_count': 1,
                    'merged_from': [i]
                })
                block_id += 1
        
        # 按Y坐标排序，便于后续处理
        content_blocks.sort(key=lambda x: x['center_y'])
        
        # 保存内容块数据集
        dataset = {
            'generation_timestamp': str(datetime.datetime.now()),
            'total_content_blocks': len(content_blocks),
            'merged_blocks': len([b for b in content_blocks if b['type'] == 'merged']),
            'single_blocks': len([b for b in content_blocks if b['type'] == 'single']),
            'handwritten_blocks': len([b for b in content_blocks if b['is_handwritten']]),
            'printed_blocks': len([b for b in content_blocks if not b['is_handwritten']]),
            'content_blocks': content_blocks
        }
        
        dataset_path = self.save_result_json(dataset, "5.1_content_dataset.json")
        
        self.info(f"内容数据集: {dataset_path}")
        self.info(f"  📊 数据集统计:")
        self.info(f"    • 总内容块: {len(content_blocks)} 个")
        self.info(f"    • 手写内容块: {len([b for b in content_blocks if b['is_handwritten']])} 个")
        self.info(f"    • 打印内容块: {len([b for b in content_blocks if not b['is_handwritten']])} 个")
        
        # 创建增强的聚合可视化
        self.debug("生成聚合可视化...")
        vis_results = self.visualizer.visualize_results(
            image_path, text_blocks, merged_groups, line_data, content_blocks
        )
        
        merged_count = len([b for b in content_blocks if b['type'] == 'merged'])
        single_count = len([b for b in content_blocks if b['type'] == 'single'])
        
        self.info(f"内容数据集生成完成: {len(content_blocks)} 个块")
        self.info(f"合并统计:")
        self.info(f"  • 合并组: {merged_count} 个")
        self.info(f"  • 单独文本块: {single_count} 个")
        
        self.logger.result_summary(f"生成内容数据集: {len(content_blocks)} 个块")
        
        return TextAggregationResult(
            dataset_path=dataset_path,
            total_content_blocks=len(content_blocks),
            merged_blocks=merged_count,
            single_blocks=single_count,
            handwritten_blocks=len([b for b in content_blocks if b['is_handwritten']]),
            printed_blocks=len([b for b in content_blocks if not b['is_handwritten']]),
            content_blocks=content_blocks
        )
    
    def _intelligent_text_merge(self, text_blocks: List[TextBlock], line_data: Dict) -> Dict:
        """增强的智能文本合并算法 - 完全复制原版本"""
        self.debug("🧠 使用增强算法查找可合并文本块组...")
        
        n = len(text_blocks)
        parent = list(range(n))
        
        # 合并算法参数 - 完全复制原版本
        max_distance = self.processing_params['max_distance']
        alignment_tolerance = self.processing_params['alignment_tolerance']
        line_intersection_margin = self.processing_params['line_intersection_margin']
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        def is_likely_continuation(block1: TextBlock, block2: TextBlock) -> bool:
            """检查是否可能是内容的延续"""
            # 1. 语义延续检查
            if self._is_semantic_continuation(block1.text, block2.text):
                return True
            
            # 2. 位置关系检查
            horizontal_dist = abs(block1.center_x - block2.center_x)
            vertical_dist = abs(block1.center_y - block2.center_y)
            
            if horizontal_dist < 200 and vertical_dist < 100:
                return True
            
            if vertical_dist < 80 and horizontal_dist < 300:
                return True
            
            return False
        
        def has_major_line_separation(block1: TextBlock, block2: TextBlock) -> bool:
            """检查边界线是否与两个文本块中心连线相交"""
            center1 = (block1.center_x, block1.center_y)
            center2 = (block2.center_x, block2.center_y)
            
            # 创建线段列表
            boundary_lines = []
            for line in line_data.get('horizontal_lines', []):
                endpoints = line['endpoints']
                boundary_lines.append({
                    'start': (endpoints[0][0], endpoints[0][1]),
                    'end': (endpoints[1][0], endpoints[1][1]),
                    'type': 'horizontal',
                    'length': line['length']
                })
            
            for line in line_data.get('vertical_lines', []):
                endpoints = line['endpoints']
                boundary_lines.append({
                    'start': (endpoints[0][0], endpoints[0][1]), 
                    'end': (endpoints[1][0], endpoints[1][1]),
                    'type': 'vertical',
                    'length': line['length']
                })
            
            # 检查有多少条边界线与中心连线相交
            intersection_count = 0
            
            for boundary_line in boundary_lines:
                if self._segments_intersect(center1, center2, 
                                          boundary_line['start'], boundary_line['end']):
                    intersection_count += 1
                    # 如果有重要的边界线分割（长度>50），更容易判断为分割
                    if boundary_line['length'] > 50:
                        return True
            
            # 如果有多条线相交，也认为是分割
            return intersection_count >= 2
        
        # 执行合并判断
        merge_count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                block1, block2 = text_blocks[i], text_blocks[j]
                
                # 0. 手写内容约束检查 - 打印和手写内容不能合并
                if block1.is_handwritten != block2.is_handwritten:
                    continue
                
                # 1. 基础距离检查
                distance = math.sqrt((block1.center_x - block2.center_x)**2 + 
                                   (block1.center_y - block2.center_y)**2)
                if distance > max_distance:
                    continue
                
                # 2. 横向内容限制 - 某些特定横向内容不合并
                if not self._allow_horizontal_merge(block1, block2):
                    continue
                
                # 3. 语义延续检查 - 优先级最高
                if is_likely_continuation(block1, block2):
                    self.debug(f"    🎯 语义延续: '{block1.text}' + '{block2.text}'")
                    if not has_major_line_separation(block1, block2):
                        union(i, j)
                        merge_count += 1
                        content_type = "手写" if block1.is_handwritten else "打印"
                        self.debug(f"  🔗 合并({content_type}): '{block1.text}' + '{block2.text}'")
                    continue
                
                # 4. 对齐检查
                h_aligned = abs(block1.center_y - block2.center_y) < alignment_tolerance
                v_aligned = abs(block1.center_x - block2.center_x) < alignment_tolerance
                
                if not (h_aligned or v_aligned):
                    continue
                
                # 5. 线条分割检查
                if has_major_line_separation(block1, block2):
                    continue
                
                union(i, j)
                merge_count += 1
                content_type = "手写" if block1.is_handwritten else "打印"
                self.debug(f"  🔗 合并({content_type}): '{block1.text}' + '{block2.text}'")
        
        # 分组
        groups = {}
        for i in range(n):
            root = find(i)
            if root not in groups:
                groups[root] = []
            groups[root].append(i)
        
        groups_list = list(groups.values())
        merged_groups = [group for group in groups_list if len(group) > 1]
        
        self.info(f"  📊 发现 {len(merged_groups)} 个可合并组，涉及 {merge_count} 次合并")
        
        # 返回所有组信息，包括单个元素组（用于完整性）
        return {
            'all_groups': groups_list,
            'merged_groups': merged_groups,
            'single_groups': [group for group in groups_list if len(group) == 1]
        }
    
    def _segments_intersect(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                          p3: Tuple[float, float], p4: Tuple[float, float]) -> bool:
        """
        判断两条线段是否相交 - 完全复制原版本算法
        p1,p2 是第一条线段的端点（文本块中心连线）
        p3,p4 是第二条线段的端点（边界线）
        """
        def ccw(A, B, C):
            """计算三点的方向（逆时针返回True）"""
            return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])
        
        def on_segment(p, q, r):
            """检查点q是否在线段pr上"""
            return (q[0] <= max(p[0], r[0]) and q[0] >= min(p[0], r[0]) and
                    q[1] <= max(p[1], r[1]) and q[1] >= min(p[1], r[1]))
        
        # 获取四个方向
        d1 = ccw(p3, p4, p1)
        d2 = ccw(p3, p4, p2)
        d3 = ccw(p1, p2, p3)
        d4 = ccw(p1, p2, p4)
        
        # 一般情况：线段相交
        if d1 != d2 and d3 != d4:
            return True
        
        # 特殊情况：共线且重叠
        if (not d1 and on_segment(p3, p1, p4)) or \
           (not d2 and on_segment(p3, p2, p4)) or \
           (not d3 and on_segment(p1, p3, p2)) or \
           (not d4 and on_segment(p1, p4, p2)):
            return True
        
        return False
    
    def _allow_horizontal_merge(self, block1: TextBlock, block2: TextBlock) -> bool:
        """检查是否允许横向合并 - 完全复制原版本算法"""
        # 某些表格头部、标题等横向内容不应合并
        restricted_keywords = [
            '测试项目', '测试设备', '测试标准', '测试条件', 
            '产品标准', '单位', '测试结果', '测试员', '备注',
            '元素名称', '标准', '实测',
            '是否填写完整', '样品实物信息', '样品是否完好'
        ]
        
        for keyword in restricted_keywords:
            if keyword in block1.text or keyword in block2.text:
                return False
        
        # 如果两个块都在同一水平线上且都是单字或短语，通常不应合并
        h_aligned = abs(block1.center_y - block2.center_y) < self.processing_params['horizontal_alignment_threshold']
        short_text_threshold = self.processing_params['short_text_length_threshold']
        if h_aligned and len(block1.text) <= short_text_threshold and len(block2.text) <= short_text_threshold:
            return False
        
        return True
    
    def _is_semantic_continuation(self, text1: str, text2: str) -> bool:
        """检查语义上是否可能是延续 - 完全复制原版本算法"""
        import re
        
        continuation_patterns = [
            (r'\d+$', r'^[个件只台套批次公斤克毫升升吨]'),
            (r'[路街道区市]$', r'^[0-9]'),
            (r'科技园$', r'^[A-Z、]'),
            (r'液$', r'^体'),
            (r'投产$', r'^数量'),
            (r'测试$', r'^结果|项目|方法'),
            (r'样品$', r'^名称|编号|批次'),
            (r'委托$', r'^地址|部门|人'),
            (r'红外$', r'^扫描|光谱'),
            (r'GB/T$', r'^[0-9]'),
        ]
        
        for pattern1, pattern2 in continuation_patterns:
            if re.search(pattern1, text1) and re.search(pattern2, text2):
                return True
            if re.search(pattern1, text2) and re.search(pattern2, text1):
                return True
        
        return False
