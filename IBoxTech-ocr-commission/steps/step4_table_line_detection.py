#!/usr/bin/env python3
"""
V3步骤4: 表格边线识别
基于文字移除后的图像检测表格边线，包括LSM检测、KNN分组、理论重建等功能
整合process_g8_text_removed_refactored的改进和V2版本的功能
"""

import cv2
import numpy as np
import json
import math
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

from utils.base_step import V3BaseStep
from visualization.step_visualizers import TableLineVisualizer
from steps.step3_text_masking import MaskingResult


@dataclass
class LineDetectionResult:
    """线条检测结果"""
    line_data_path: str
    theoretical_line_data_path: str
    table_analysis_path: str
    line_data: Dict[str, List]
    theoretical_line_data: Dict[str, List]
    table_analysis: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    # 为下游步骤保留文本块信息
    text_blocks: List = None
    original_image_path: str = ""


class TableLineDetectionStep(V3BaseStep):
    """V3表格边线识别步骤"""
    
    def __init__(self, config: Dict[str, Any], file_manager, logger):
        super().__init__(4, "表格边线识别", config, file_manager, logger)
        
        # 初始化可视化器
        self.visualizer = TableLineVisualizer(
            self.step_number, config.visualization, file_manager, logger
        )
        
        # 处理参数配置
        self.processing_params = {
            # 边缘检测参数
            'canny_low_threshold': 80,
            'canny_high_threshold': 200,
            'canny_aperture_size': 3,
            
            # LSM检测参数
            'lsd_refine': cv2.LSD_REFINE_STD,
            'lsd_scale': 0.8,
            'lsd_sigma_scale': 0.8,
            'lsd_quant': 8.0,
            'lsd_ang_th': 8.0,
            'lsd_log_eps': 0,
            'lsd_density_th': 0.8,
            
            # 线条分类参数
            'horizontal_angle_tolerance': 15,
            'vertical_angle_tolerance': 15,
            
            # 折痕过滤参数
            'crease_coverage_threshold': 0.8,
            'crease_proximity_to_edge': 50,
            
            # KNN分组参数  
            'knn_distance_threshold': 15.0,  # 与原版本保持一致
            'min_group_size': 2,
            
            # 理论重建参数
            'merge_distance_threshold': 10.0,
            'extend_line_pixels': 20,
            
            # 表格分析参数
            'min_table_lines': 3,
            'line_intersection_tolerance': 5
        }
        
        # 从配置中更新参数
        if hasattr(config, 'step_configs') and 4 in config.step_configs:
            step_config = config.step_configs[4]
            self.processing_params.update(step_config.get('processing', {}))
    
    def execute(self, input_data: Tuple[str, MaskingResult]) -> Tuple[str, LineDetectionResult]:
        """执行表格边线识别"""
        try:
            self.progress("[步骤4] 开始表格边线识别...")
            
            text_removed_image_path, masking_result = input_data
            
            # 4.1 加载和验证输入图像
            clean_image, original_image, gray_clean = self._load_images(text_removed_image_path)
            height, width = gray_clean.shape
            self.debug(f"[步骤4] 图像尺寸: {width} x {height}")
            
            # 4.2 边缘检测
            self.progress("[步骤4] 边缘检测...")
            edges = self._edge_detection(gray_clean)
            
            # 4.3 LSM直线检测
            self.progress("[步骤4] LSM直线检测...")
            line_data = self._lsd_line_detection(gray_clean)
            
            # 4.4 KNN分组处理
            self.progress("[步骤4] KNN分组处理...")
            grouped_lines = self._process_line_grouping(line_data)
            
            # 4.5 理论重建处理
            self.progress("[步骤4] 理论重建处理...")
            theoretical_line_data = self._process_theoretical_reconstruction(grouped_lines)
            
            # 4.6 表格结构分析
            self.progress("[步骤4] 表格结构分析...")
            table_analysis = self._analyze_table_structure(theoretical_line_data)
            
            # 4.7 保存结果文件
            result_files = self._save_detection_results(line_data, theoretical_line_data, table_analysis)
            
            # 4.8 生成可视化
            if self.visualizer.is_enabled():
                processing_data = {
                    'original_image': original_image,
                    'clean_image': clean_image,
                    'edges': edges,
                    'line_data': line_data,
                    'grouped_lines': grouped_lines,
                    'theoretical_line_data': theoretical_line_data,
                    'table_analysis': table_analysis,
                    'masking_result': masking_result
                }
                visualization_files = self.visualizer.visualize_results(
                    text_removed_image_path, result_files, processing_data
                )
                self.visualizer.log_visualization_summary(visualization_files)
            
            # 4.9 创建结果对象
            detection_result = LineDetectionResult(
                line_data_path=result_files['line_data'],
                theoretical_line_data_path=result_files['theoretical_line_data'],
                table_analysis_path=result_files['table_analysis'],
                line_data=line_data,
                theoretical_line_data=theoretical_line_data,
                table_analysis=table_analysis,
                processing_metadata={
                    'processing_params': self.processing_params,
                    'image_dimensions': {'width': width, 'height': height},
                    'detection_statistics': {
                        'original_lines': len(line_data['horizontal_lines']) + len(line_data['vertical_lines']),
                        'final_horizontal': len(theoretical_line_data['horizontal_lines']),
                        'final_vertical': len(theoretical_line_data['vertical_lines']),
                        'detected_tables': table_analysis.get('table_count', 0)
                    }
                },
                # 从上游步骤传递数据
                text_blocks=masking_result.text_blocks,
                original_image_path=masking_result.original_image_path
            )
            
            # 4.10 保存调试数据
            if self.should_save_debug():
                debug_data = {
                    'processing_params': self.processing_params,
                    'line_statistics': detection_result.processing_metadata['detection_statistics'],
                    'table_analysis': table_analysis,
                    'line_data_summary': {
                        'horizontal_count': len(line_data['horizontal_lines']),
                        'vertical_count': len(line_data['vertical_lines']),
                        'total_detected': len(line_data['all_lines'])
                    }
                }
                self.save_debug_data(self._clean_data_types(debug_data), "table_line_detection_debug.json")
            
            stats = detection_result.processing_metadata['detection_statistics']
            self.logger.result_summary(
                f"线条检测完成: {stats['original_lines']}→{stats['final_horizontal']+stats['final_vertical']} 条"
            )
            return result_files['theoretical_line_data'], detection_result
            
        except Exception as e:
            self.logger.error(f"表格边线识别失败: {str(e)}")
            raise
    
    def _load_images(self, text_removed_image_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """加载输入图像"""
        # 加载清洁图像（文字已移除）
        clean_image = cv2.imread(text_removed_image_path)
        if clean_image is None:
            raise ValueError(f"无法加载文字移除图像: {text_removed_image_path}")
        
        # 尝试从同级目录加载原始图像
        text_removed_path = Path(text_removed_image_path)
        # 现在text_removed保存在visualizations/step03/，需要找到steps/step01/目录
        # 从visualizations/step03回到根目录再找steps/step01
        if "visualizations" in text_removed_path.parts:
            # 新路径结构：visualizations/step03/3.3_text_removed.png -> steps/step01/
            step1_dir = text_removed_path.parent.parent.parent / "steps" / "step01"
        else:
            # 旧路径结构（向后兼容）：steps/step03/3.3_text_removed.png -> steps/step01/
            step1_dir = text_removed_path.parent.parent / "step01"
        original_candidates = [
            step1_dir / "1.7_final_preprocessed.png",
            step1_dir / "1.6_deskewed.png",
            Path(text_removed_image_path)  # 备用，确保是Path对象
        ]
        
        original_image = None
        for candidate in original_candidates:
            if candidate.exists():
                original_image = cv2.imread(str(candidate))
                if original_image is not None:
                    self.debug(f"[步骤4] 加载原始图像: {candidate}")
                    break
        
        if original_image is None:
            # 使用清洁图像作为备用
            original_image = clean_image.copy()
            self.debug(f"[步骤4] 使用清洁图像作为原始图像")
        
        gray_clean = cv2.cvtColor(clean_image, cv2.COLOR_BGR2GRAY)
        
        return clean_image, original_image, gray_clean
    
    def _edge_detection(self, gray_image: np.ndarray) -> np.ndarray:
        """边缘检测"""
        edges = cv2.Canny(
            gray_image,
            self.processing_params['canny_low_threshold'],
            self.processing_params['canny_high_threshold'],
            apertureSize=self.processing_params['canny_aperture_size']
        )
        
        # 保存边缘检测结果
        edges_path = self.save_result_image(edges, "4.1_edges.png")
        self.debug(f"[步骤4] 边缘检测结果: {edges_path}")
        
        return edges
    
    def _lsd_line_detection(self, gray_image: np.ndarray) -> Dict[str, List]:
        """LSM直线检测"""
        # 创建LSM检测器
        lsd = cv2.createLineSegmentDetector(
            refine=self.processing_params['lsd_refine'],
            scale=self.processing_params['lsd_scale'],
            sigma_scale=self.processing_params['lsd_sigma_scale'],
            quant=self.processing_params['lsd_quant'],
            ang_th=self.processing_params['lsd_ang_th'],
            log_eps=self.processing_params['lsd_log_eps'],
            density_th=self.processing_params['lsd_density_th']
        )
        
        lines_result = lsd.detect(gray_image)
        
        line_data = {
            'horizontal_lines': [],
            'vertical_lines': [],
            'all_lines': []
        }
        
        img_height, img_width = gray_image.shape
        
        if lines_result is not None:
            detected_lines = lines_result[0] if isinstance(lines_result, tuple) else lines_result
            
            if detected_lines is not None and len(detected_lines) > 0:
                self.debug(f"[步骤4] LSM检测到 {len(detected_lines)} 条直线")
                
                crease_count = 0
                
                for line_segment in detected_lines:
                    if line_segment.shape == (1, 4):
                        coords = line_segment[0]
                        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
                        
                        angle = math.atan2(y2 - y1, x2 - x1) * 180 / np.pi
                        length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                        
                        line_info = {
                            'endpoints': [[int(x1), int(y1)], [int(x2), int(y2)]],
                            'angle_degrees': float(angle),
                            'length': float(length)
                        }
                        
                        # 折痕过滤
                        if self._is_crease_line(line_info, img_width, img_height):
                            crease_count += 1
                            continue
                        
                        line_data['all_lines'].append(line_info)
                        
                        # 分类
                        h_tol = self.processing_params['horizontal_angle_tolerance']
                        v_tol = self.processing_params['vertical_angle_tolerance']
                        
                        if abs(angle) < h_tol or abs(angle - 180) < h_tol:
                            line_data['horizontal_lines'].append(line_info)
                        elif abs(angle - 90) < v_tol or abs(angle + 90) < v_tol:
                            line_data['vertical_lines'].append(line_info)
                
                self.debug(f"[步骤4] 过滤折痕: {crease_count} 条")
                self.debug(f"[步骤4] 分类结果: 水平{len(line_data['horizontal_lines'])}, 垂直{len(line_data['vertical_lines'])}")
        
        return line_data
    
    def _is_crease_line(self, line_info: Dict, img_width: int, img_height: int) -> bool:
        """
        检测线段是否为折痕（基于原版本更严格的算法）
        """
        endpoints = line_info['endpoints']
        x1, y1 = endpoints[0]
        x2, y2 = endpoints[1]
        length = line_info['length']
        angle = line_info['angle_degrees']
        
        # 1. 长度阈值：折痕通常很长，接近图像的宽度或高度
        length_threshold_ratio = 0.7  # 长度超过图像对应维度的70%
        
        # 2. 根据角度判断是水平还是垂直折痕
        if abs(angle) < 15 or abs(angle - 180) < 15:
            # 水平折痕：长度接近图像宽度
            min_crease_length = img_width * length_threshold_ratio
            # 额外检查：折痕通常从左边界到右边界
            span_x = abs(x2 - x1)
            coverage_ratio = span_x / img_width
            if length >= min_crease_length and coverage_ratio >= 0.6:
                return True
                
        elif abs(angle - 90) < 15 or abs(angle + 90) < 15:
            # 垂直折痕：长度接近图像高度  
            min_crease_length = img_height * length_threshold_ratio
            # 额外检查：折痕通常从上边界到下边界
            span_y = abs(y2 - y1)
            coverage_ratio = span_y / img_height
            if length >= min_crease_length and coverage_ratio >= 0.6:
                return True
        
        return False
    
    def _process_line_grouping(self, line_data: Dict[str, List]) -> Dict[str, Any]:
        """处理线条分组"""
        grouped_lines = {
            'horizontal_groups': {},
            'vertical_lines': line_data['vertical_lines'].copy(),
            'grouping_stats': {}
        }
        
        # 水平线KNN分组
        if len(line_data['horizontal_lines']) > 1:
            h_groups = self._group_horizontal_lines_knn(
                line_data['horizontal_lines'], 
                distance_threshold=15.0  # 使用原版本的距离阈值
            )
            grouped_lines['horizontal_groups'] = h_groups
            remaining_lines = sum(len(lines) for lines in h_groups.values())
            grouped_lines['grouping_stats']['horizontal'] = {
                'original_count': len(line_data['horizontal_lines']),
                'group_count': len(h_groups),
                'remaining_lines': remaining_lines
            }
            self.debug(f"[步骤4] 水平线KNN分组: {len(line_data['horizontal_lines'])} → {len(h_groups)} 组")
            if remaining_lines < len(line_data['horizontal_lines']):
                self.debug(f"[步骤4] Y值跨度过滤: {len(line_data['horizontal_lines'])} → {remaining_lines} 条线段")
        else:
            grouped_lines['horizontal_groups'] = {}
            grouped_lines['grouping_stats']['horizontal'] = {
                'original_count': len(line_data['horizontal_lines']),
                'group_count': 0,
                'remaining_lines': len(line_data['horizontal_lines'])
            }
        
        return grouped_lines
    
    def _group_horizontal_lines_knn(self, horizontal_lines: List[Dict], 
                                    distance_threshold: float = None) -> Dict[float, List[Dict]]:
        """
        使用基于距离的聚类对水平线进行分组（完全复制原版本算法）
        
        Args:
            horizontal_lines: 水平线列表
            distance_threshold: Y值距离阈值，小于此值的线段归为同一组
            
        Returns:
            字典，键为组的Y中心值，值为该组的线段列表
        """
        if not horizontal_lines:
            return {}
        
        # 使用配置的距离阈值
        if distance_threshold is None:
            distance_threshold = self.processing_params['knn_distance_threshold']
        
        # 计算每条线的Y中心值
        line_y_centers = []
        for line in horizontal_lines:
            y1, y2 = line['endpoints'][0][1], line['endpoints'][1][1]
            y_center = (y1 + y2) / 2
            line_y_centers.append(y_center)
        
        # 基于Y值进行简单聚类（使用距离阈值）
        groups = defaultdict(list)
        used = set()
        
        for i, line in enumerate(horizontal_lines):
            if i in used:
                continue
                
            current_y = line_y_centers[i]
            group_lines = [line]
            group_y_values = [current_y]
            used.add(i)
            
            # 寻找相近的线段
            for j, other_line in enumerate(horizontal_lines):
                if j in used or j == i:
                    continue
                    
                other_y = line_y_centers[j]
                if abs(current_y - other_y) <= distance_threshold:
                    group_lines.append(other_line)
                    group_y_values.append(other_y)
                    used.add(j)
            
            # 计算组的Y中心值
            group_y_center = sum(group_y_values) / len(group_y_values)
            groups[group_y_center] = group_lines
        
        # 按Y值排序
        sorted_groups = dict(sorted(groups.items()))
        
        # 过滤Y值跨度过大的分组（使用优化的跨度阈值）
        max_y_span = 1000.0
        filtered_groups = {}
        
        for group_y_center, lines in sorted_groups.items():
            if len(lines) <= 1:
                # 单线段组直接保留
                filtered_groups[group_y_center] = lines
                continue
                
            # 计算组内Y值跨度
            y_values = []
            for line in lines:
                y1, y2 = line['endpoints'][0][1], line['endpoints'][1][1]
                y_center = (y1 + y2) / 2
                y_values.append(y_center)
            
            y_span = max(y_values) - min(y_values)
            
            if y_span <= max_y_span:
                # 跨度合理，保留该组
                filtered_groups[group_y_center] = lines
        
        return filtered_groups
    
    def _get_all_y_positions(self, horizontal_lines: List[Dict]) -> set:
        """获取所有Y位置（用于统计）- 完全复制refactored版本算法"""
        y_positions = set()
        y_tolerance = 3
        
        for line in horizontal_lines:
            x1, y1 = line['endpoints'][0]
            x2, y2 = line['endpoints'][1]
            avg_y = (y1 + y2) // 2
            
            # 找到相近的Y位置
            found_y = None
            for existing_y in y_positions:
                if abs(avg_y - existing_y) <= y_tolerance:
                    found_y = existing_y
                    break
            
            if found_y is not None:
                y_positions.remove(found_y)
                y_positions.add((found_y + avg_y) // 2)
            else:
                y_positions.add(avg_y)
        
        return y_positions
    
    def _filter_important_y_positions(self, horizontal_lines: List[Dict], vertical_lines: List[Dict], table_width: int) -> set:
        """智能筛选重要的Y位置，过滤装饰性短线 - 完全复制refactored版本算法"""
        
        # 1. 按Y坐标分组
        y_groups = self._group_horizontal_lines_knn(horizontal_lines, distance_threshold=15.0)
        
        important_y_positions = set()
        filtered_count = 0
        
        for group_y, group_lines in y_groups.items():
            # 2. 计算组的质量指标
            group_stats = self._calculate_group_quality(group_lines, table_width, vertical_lines)
            
            # 3. 智能筛选条件
            is_important = self._is_important_line_group(group_stats, group_lines)
            
            if is_important:
                important_y_positions.add(int(group_y))
                self.debug(f"    ✅ 保留组 Y≈{group_y:.0f}: {len(group_lines)}线, 覆盖率{group_stats['coverage_ratio']:.1f}%")
            else:
                filtered_count += 1
                self.debug(f"    🚫 过滤组 Y≈{group_y:.0f}: {len(group_lines)}线, {group_stats['filter_reason']}")
        
        self.debug(f"    📊 筛选结果: {len(y_groups)} → {len(important_y_positions)} 个重要Y位置，过滤 {filtered_count} 个装饰线组")
        
        return important_y_positions
    
    def _calculate_group_quality(self, group_lines: List[Dict], table_width: int, vertical_lines: List[Dict]) -> Dict:
        """计算线段组的质量指标 - 完全复制refactored版本算法"""
        if not group_lines:
            return {'coverage_ratio': 0, 'filter_reason': '空组'}
        
        # 1. 计算总覆盖率
        total_length = sum(line['length'] for line in group_lines)
        coverage_ratio = (total_length / table_width) * 100
        
        # 2. 计算X坐标跨度
        min_x = float('inf')
        max_x = float('-inf')
        for line in group_lines:
            x1, x2 = line['endpoints'][0][0], line['endpoints'][1][0]
            min_x = min(min_x, x1, x2)
            max_x = max(max_x, x1, x2)
        
        span_ratio = ((max_x - min_x) / table_width) * 100 if max_x > min_x else 0
        
        # 3. 计算平均线长
        avg_length = total_length / len(group_lines)
        
        # 4. 计算与垂直线的交点数
        intersection_count = self._count_vertical_intersections(group_lines, vertical_lines)
        
        return {
            'coverage_ratio': coverage_ratio,
            'span_ratio': span_ratio,
            'avg_length': avg_length,
            'line_count': len(group_lines),
            'intersection_count': intersection_count,
            'filter_reason': ''
        }
    
    def _is_important_line_group(self, stats: Dict, group_lines: List[Dict]) -> bool:
        """判断线段组是否重要（是否应该扩展为完整横线）- 完全复制refactored版本算法"""
        
        # 条件1: 覆盖率足够高
        if stats['coverage_ratio'] >= 25.0:
            return True
            
        # 条件2: 跨度大且有足够的线段数量
        if stats['span_ratio'] >= 60.0 and stats['line_count'] >= 5:
            return True
            
        # 条件3: 有较多垂直线交点（说明是重要的表格分隔线）
        if stats['intersection_count'] >= 3:
            return True
        
        # 条件4: 线段数量多且平均长度合理
        if stats['line_count'] >= 8 and stats['avg_length'] >= 20:
            return True
        
        # 其他情况判定为装饰性短线
        if stats['coverage_ratio'] < 3.0:
            stats['filter_reason'] = f"覆盖率过低({stats['coverage_ratio']:.1f}%)"
        elif stats['span_ratio'] < 10.0:
            stats['filter_reason'] = f"跨度过小({stats['span_ratio']:.1f}%)"
        elif stats['line_count'] <= 2 and stats['avg_length'] < 30:
            stats['filter_reason'] = f"短线组(平均{stats['avg_length']:.0f}px)"
        elif stats['intersection_count'] == 0:
            stats['filter_reason'] = f"无垂直线交点"
        else:
            stats['filter_reason'] = f"综合评分不足"
            
        return False
    
    def _count_vertical_intersections(self, horizontal_lines: List[Dict], vertical_lines: List[Dict]) -> int:
        """计算水平线组与垂直线的交点数量 - 完全复制refactored版本算法"""
        if not horizontal_lines or not vertical_lines:
            return 0
        
        # 获取水平线组的Y坐标范围
        y_values = []
        for line in horizontal_lines:
            y1, y2 = line['endpoints'][0][1], line['endpoints'][1][1]
            y_values.extend([y1, y2])
        
        group_y_min = min(y_values) - 15  # 允许一些误差
        group_y_max = max(y_values) + 15
        
        # 获取水平线组的X坐标范围
        x_values = []
        for line in horizontal_lines:
            x1, x2 = line['endpoints'][0][0], line['endpoints'][1][0]
            x_values.extend([x1, x2])
        
        group_x_min = min(x_values)
        group_x_max = max(x_values)
        
        # 计算交点
        intersection_count = 0
        for v_line in vertical_lines:
            v_x1, v_y1 = v_line['endpoints'][0]
            v_x2, v_y2 = v_line['endpoints'][1]
            
            v_x_avg = (v_x1 + v_x2) / 2
            v_y_min = min(v_y1, v_y2)
            v_y_max = max(v_y1, v_y2)
            
            # 检查垂直线是否与水平线组相交
            x_intersects = group_x_min <= v_x_avg <= group_x_max
            y_intersects = not (group_y_max < v_y_min or group_y_min > v_y_max)
            
            if x_intersects and y_intersects:
                intersection_count += 1
        
        return intersection_count
    
    def _merge_horizontal_lines_refactored(self, horizontal_lines: List[Dict], 
                                          vertical_lines: List[Dict] = None) -> List[Dict]:
        """
        基于表格理论重建横向边线 - 改进版：智能筛选装饰性短线
        完全复制refactored版本算法
        """
        if not horizontal_lines:
            return []
        
        self.debug("  🔍 分析表格边界和横向线分布...")
        
        # 确定表格边界
        left_boundary = None
        right_boundary = None
        table_width = 0
        
        if vertical_lines:
            self.debug("  📏 使用纵向线段确定表格边界...")
            vertical_x_coords = []
            
            for line in vertical_lines:
                x1, y1 = line['endpoints'][0]
                x2, y2 = line['endpoints'][1]
                avg_x = (x1 + x2) // 2
                vertical_x_coords.append(avg_x)
            
            if vertical_x_coords:
                left_boundary = min(vertical_x_coords)
                right_boundary = max(vertical_x_coords)
                table_width = right_boundary - left_boundary
                self.debug(f"  ✅ 基于纵向线段确定边界: X={left_boundary} 到 X={right_boundary}")
        
        # 如果没有纵向线段信息，回退到横向线段端点分析
        if left_boundary is None or right_boundary is None:
            self.debug("  ⚠️  未找到纵向线段，使用横向线段端点分析...")
            all_x_points = []
            
            for line in horizontal_lines:
                x1, y1 = line['endpoints'][0]
                x2, y2 = line['endpoints'][1]
                all_x_points.extend([x1, x2])
            
            if all_x_points:
                sorted_x = sorted(all_x_points)
                left_boundary = sorted_x[int(len(sorted_x) * 0.05)]
                right_boundary = sorted_x[int(len(sorted_x) * 0.95)]
                table_width = right_boundary - left_boundary
            else:
                return horizontal_lines
        
        # 🧠 智能筛选重要的水平线组
        self.debug("  🧠 智能筛选重要的水平线组...")
        important_y_positions = self._filter_important_y_positions(horizontal_lines, vertical_lines, table_width)
        
        self.debug(f"  📐 表格边界: X={left_boundary} 到 X={right_boundary}")
        self.debug(f"  📏 表格宽度: {table_width}px")
        self.debug(f"  📊 原始Y位置: {len(self._get_all_y_positions(horizontal_lines))} 个")
        self.debug(f"  🎯 重要Y位置: {len(important_y_positions)} 个（过滤装饰性短线）")
        
        # 生成理论线段（只为重要位置）
        theoretical_lines = []
        for y in sorted(important_y_positions):
            theoretical_line = {
                'endpoints': [[left_boundary, y], [right_boundary, y]],
                'angle_degrees': 0.0,
                'length': float(table_width),
                'type': 'important_theoretical'
            }
            theoretical_lines.append(theoretical_line)
        
        filtered_count = len(self._get_all_y_positions(horizontal_lines)) - len(important_y_positions)
        self.debug(f"  ✅ 智能重建: {len(horizontal_lines)} → {len(theoretical_lines)} 条 (过滤{filtered_count}个装饰线组)")
        return theoretical_lines
    
    def _process_theoretical_reconstruction(self, grouped_lines: Dict[str, Any]) -> Dict[str, List]:
        """理论重建处理（基于原版本的复杂算法）"""
        # 1. 基于表格理论重建横向边线
        horizontal_lines = []
        for group_y_center, group_lines in grouped_lines['horizontal_groups'].items():
            horizontal_lines.extend(group_lines)
        
        self.debug(f"[步骤4] 开始理论重建: 水平{len(horizontal_lines)}, 垂直{len(grouped_lines['vertical_lines'])}")
        
        # 使用改进版本的理论重建算法（智能筛选装饰性短线）
        theoretical_horizontal = self._merge_horizontal_lines_refactored(
            horizontal_lines, 
            grouped_lines['vertical_lines']
        )
        
        # 2. 完整处理横向边线
        final_horizontal = self._process_horizontal_lines_complete(theoretical_horizontal)
        
        # 3. 基于横向边线上下文处理垂直线（使用改进版本）
        final_vertical = self._process_vertical_lines_with_horizontal_context_refactored(
            grouped_lines['vertical_lines'], 
            final_horizontal
        )
        
        theoretical_line_data = {
            'horizontal_lines': final_horizontal,
            'vertical_lines': final_vertical
        }
        
        self.debug(f"[步骤4] 理论重建结果: 水平{len(final_horizontal)}, 垂直{len(final_vertical)}")
        
        return theoretical_line_data
    
    def _group_vertical_lines_simple(self, vertical_lines: List[Dict]) -> Dict[str, List[Dict]]:
        """简化的垂直线分组 - 完全复制refactored版本算法"""
        if not vertical_lines:
            return {}
        
        groups = defaultdict(list)
        for line in vertical_lines:
            x1, x2 = line['endpoints'][0][0], line['endpoints'][1][0]
            avg_x = (x1 + x2) // 2
            
            # 找到相近的组
            found_group = None
            for group_x in groups.keys():
                if abs(avg_x - int(group_x.split('_')[1])) <= 20:
                    found_group = group_x
                    break
            
            if found_group is not None:
                groups[found_group].append(line)
            else:
                groups[f"group_{avg_x}"] = [line]
        
        return dict(groups)
    
    def _merge_vertical_group_simple(self, group_lines: List[Dict]) -> List[Dict]:
        """智能垂直线分组合并 - 检查连续性，避免跨越空隙 - 完全复制refactored版本算法"""
        if not group_lines:
            return []
        
        if len(group_lines) == 1:
            return group_lines
        
        # 计算平均X坐标
        x_values = []
        for line in group_lines:
            x1, x2 = line['endpoints'][0][0], line['endpoints'][1][0]
            x_values.extend([x1, x2])
        avg_x = int(sum(x_values) / len(x_values))
        
        # 🔍 按连续性分析，将线段分为连续的子组
        continuous_segments = self._find_continuous_vertical_segments(group_lines, gap_threshold=30)
        
        # 📊 为每个连续段生成合并线段
        merged_lines = []
        for segment_idx, segment_lines in enumerate(continuous_segments):
            if not segment_lines:
                continue
                
            # 计算该连续段的Y范围
            segment_y_values = []
            for line in segment_lines:
                y1, y2 = line['endpoints'][0][1], line['endpoints'][1][1]
                segment_y_values.extend([y1, y2])
            
            min_y = min(segment_y_values)
            max_y = max(segment_y_values)
            
            merged_line = {
                'endpoints': [[avg_x, min_y], [avg_x, max_y]],
                'angle_degrees': 90.0,
                'length': max_y - min_y,
                'type': 'continuous_vertical',
                'merged_from': len(segment_lines),
                'segment_id': segment_idx + 1,
                'is_continuous': True
            }
            merged_lines.append(merged_line)
        
        return merged_lines
    
    def _find_continuous_vertical_segments(self, group_lines: List[Dict], gap_threshold: float = 30) -> List[List[Dict]]:
        """找到垂直线组中的连续段 - 完全复制refactored版本算法"""
        if not group_lines:
            return []
        
        # 1. 收集所有Y坐标区间并排序
        y_intervals = []
        for i, line in enumerate(group_lines):
            y1, y2 = line['endpoints'][0][1], line['endpoints'][1][1]
            min_y, max_y = min(y1, y2), max(y1, y2)
            y_intervals.append({
                'min_y': min_y,
                'max_y': max_y,
                'line': line,
                'line_idx': i
            })
        
        # 按起始Y坐标排序
        y_intervals.sort(key=lambda x: x['min_y'])
        
        # 2. 基于连续性分组
        continuous_segments = []
        current_segment = []
        
        for i, interval in enumerate(y_intervals):
            if not current_segment:
                # 开始新段
                current_segment = [interval['line']]
            else:
                # 检查是否与当前段连续
                last_interval = None
                for prev_interval in y_intervals[:i]:
                    if prev_interval['line'] in current_segment:
                        if last_interval is None or prev_interval['max_y'] > last_interval['max_y']:
                            last_interval = prev_interval
                
                if last_interval is not None:
                    gap = interval['min_y'] - last_interval['max_y']
                    
                    if gap <= gap_threshold:
                        # 连续，加入当前段
                        current_segment.append(interval['line'])
                    else:
                        # 不连续，结束当前段，开始新段
                        if current_segment:
                            continuous_segments.append(current_segment)
                        current_segment = [interval['line']]
        
        # 添加最后一段
        if current_segment:
            continuous_segments.append(current_segment)
        
        return continuous_segments
    
    def _extend_vertical_lines_through_horizontal(self, vertical_lines: List[Dict], 
                                                horizontal_lines: List[Dict], 
                                                intersection_threshold: float = 15.0,
                                                extension_threshold: float = 20.0) -> List[Dict]:
        """
        智能延伸垂直线：当垂直线距离水平线较远时，延伸到相邻水平线
        ✅ 已升级为refactored版本的高级算法（基于相交分析的智能延伸）
        
        Args:
            vertical_lines: 垂直线列表
            horizontal_lines: 水平线列表  
            intersection_threshold: 相交判断阈值（px）
            extension_threshold: 延伸判断阈值（px，距离≥此值才延伸）
        """
        if not vertical_lines or not horizontal_lines:
            return vertical_lines
        
        # 对水平线按Y坐标排序，便于查找相邻线
        sorted_h_lines = sorted(horizontal_lines, key=lambda line: (line['endpoints'][0][1] + line['endpoints'][1][1]) / 2)
        
        extended_lines = []
        extension_count = 0
        
        for v_idx, v_line in enumerate(vertical_lines):
            # 获取垂直线的基本信息
            v_x1, v_y1 = v_line['endpoints'][0]
            v_x2, v_y2 = v_line['endpoints'][1]
            v_x_avg = (v_x1 + v_x2) / 2
            v_y_min = min(v_y1, v_y2)
            v_y_max = max(v_y1, v_y2)
            
            # 查找与该垂直线相交的水平线
            intersections = []
            
            for h_line in horizontal_lines:
                h_x1, h_y1 = h_line['endpoints'][0]
                h_x2, h_y2 = h_line['endpoints'][1]
                h_y_avg = (h_y1 + h_y2) / 2
                h_x_min = min(h_x1, h_x2)
                h_x_max = max(h_x1, h_x2)
                
                # 检查是否真正相交（垂直线穿过水平线）
                x_intersects = h_x_min <= v_x_avg <= h_x_max
                # 修正：只有当水平线真正在垂直线范围内时才算相交
                y_intersects = v_y_min <= h_y_avg <= v_y_max
                
                if x_intersects and y_intersects:
                    intersections.append({
                        'h_line': h_line,
                        'h_y': h_y_avg,
                        'intersection_y': h_y_avg
                    })
            
            # 确定是否需要延伸以及延伸方向
            new_v_y_min = v_y_min
            new_v_y_max = v_y_max
            extended_up = False
            extended_down = False
            
            for intersection in intersections:
                intersect_y = intersection['intersection_y']
                
                # 检查是否需要向上延伸（只有距离足够远才延伸）
                if abs(intersect_y - v_y_min) >= extension_threshold:
                    # 寻找上方最近的水平线
                    upper_h_line = self._find_nearest_horizontal_line(intersect_y, sorted_h_lines, direction='up')
                    if upper_h_line:
                        upper_y = (upper_h_line['endpoints'][0][1] + upper_h_line['endpoints'][1][1]) / 2
                        if upper_y < new_v_y_min:
                            new_v_y_min = upper_y
                            extended_up = True
                
                # 检查是否需要向下延伸（只有距离足够远才延伸）
                if abs(intersect_y - v_y_max) >= extension_threshold:
                    # 寻找下方最近的水平线
                    lower_h_line = self._find_nearest_horizontal_line(intersect_y, sorted_h_lines, direction='down')
                    if lower_h_line:
                        lower_y = (lower_h_line['endpoints'][0][1] + lower_h_line['endpoints'][1][1]) / 2
                        if lower_y > new_v_y_max:
                            new_v_y_max = lower_y
                            extended_down = True
            
            # 创建延伸后的垂直线
            if extended_up or extended_down:
                extended_line = v_line.copy()
                extended_line['endpoints'] = [[int(v_x_avg), int(new_v_y_min)], [int(v_x_avg), int(new_v_y_max)]]
                extended_line['length'] = new_v_y_max - new_v_y_min
                extended_line['type'] = 'extended_vertical'
                extended_line['original_length'] = v_line['length']
                extended_line['extended_up'] = extended_up
                extended_line['extended_down'] = extended_down
                extended_line['extension_info'] = {
                    'original_y_min': v_y_min,
                    'original_y_max': v_y_max,
                    'new_y_min': new_v_y_min,
                    'new_y_max': new_v_y_max,
                    'intersections': len(intersections)
                }
                extended_lines.append(extended_line)
                extension_count += 1
                
                # 详细报告延伸情况
                extension_info = []
                if extended_up:
                    extension_info.append(f"向上{v_y_min - new_v_y_min:.0f}px")
                if extended_down:
                    extension_info.append(f"向下{new_v_y_max - v_y_max:.0f}px")
                
                self.debug(f"    🔄 V线 X≈{v_x_avg:.0f}: {len(intersections)}交点 → {'+'.join(extension_info)}")
            else:
                # 无需延伸的垂直线
                extended_lines.append(v_line)
        
        self.debug(f"    ✅ 延伸统计: {extension_count}/{len(vertical_lines)} 条垂直线被延伸")
        return extended_lines
    
    def _find_nearest_horizontal_line(self, reference_y: float, sorted_h_lines: List[Dict], 
                                    direction: str = 'up') -> Dict:
        """
        查找最近的水平线
        
        Args:
            reference_y: 参考Y坐标
            sorted_h_lines: 按Y坐标排序的水平线列表
            direction: 'up' 或 'down'
        """
        if direction == 'up':
            # 查找上方最近的水平线
            for h_line in reversed(sorted_h_lines):
                h_y = (h_line['endpoints'][0][1] + h_line['endpoints'][1][1]) / 2
                if h_y < reference_y:
                    return h_line
        elif direction == 'down':
            # 查找下方最近的水平线
            for h_line in sorted_h_lines:
                h_y = (h_line['endpoints'][0][1] + h_line['endpoints'][1][1]) / 2
                if h_y > reference_y:
                    return h_line
        
        return None
    
    def _process_vertical_lines_with_horizontal_context_refactored(self, vertical_lines: List[Dict], 
                                                                 horizontal_lines: List[Dict]) -> List[Dict]:
        """
        基于已处理的横向边线上下文，智能处理纵向边线
        完全复制refactored版本算法
        """
        if not vertical_lines:
            return []
        
        self.debug("  🔄 纵向边线智能分组...")
        v_groups = self._group_vertical_lines_simple(vertical_lines)
        self.debug(f"    📊 纵向线分组结果: {len(vertical_lines)} 条 → {len(v_groups)} 个组")
        
        # 🔄 纵向边线智能合并（基于连续性）
        self.debug("\n🔄 纵向边线智能合并（检查连续性）...")
        merged_vertical = []
        total_segments = 0
        
        for group_key, group_lines in v_groups.items():
            if not group_lines:
                continue
            
            # 使用新的连续性合并方法（返回多个连续段）
            continuous_lines = self._merge_vertical_group_simple(group_lines)
            if continuous_lines:
                merged_vertical.extend(continuous_lines)
                total_segments += len(continuous_lines)
                
                # 报告该组的合并结果
                group_x = int(group_key.split('_')[1])
                if len(continuous_lines) > 1:
                    self.debug(f"    🔀 组 X≈{group_x}: {len(group_lines)}线段 → {len(continuous_lines)}条连续段（存在间隙）")
                else:
                    self.debug(f"    ✅ 组 X≈{group_x}: {len(group_lines)}线段 → 1条连续线")
        
        self.debug(f"    📊 纵向线智能合并完成: {len(v_groups)}个组 → {total_segments}条连续垂直线")
        
        # 🔄 垂直线智能延伸（穿过水平线时延伸到相邻水平线）
        self.debug("\n🔄 垂直线智能延伸检查...")
        extended_vertical = self._extend_vertical_lines_through_horizontal(merged_vertical, horizontal_lines)
        self.debug(f"    📊 垂直线延伸完成: {len(merged_vertical)} → {len(extended_vertical)} 条")
        
        return extended_vertical
    
    def _merge_horizontal_lines_v2(self, horizontal_lines: List[Dict], 
                                  vertical_lines: List[Dict] = None) -> List[Dict]:
        """
        基于表格理论重建横向边线（原版本算法）
        使用最左最右纵向线段作为横向线段端点参考
        """
        if not horizontal_lines:
            return []
        
        self.debug(f"[步骤4] 分析表格边界和横向线分布...")
        
        # 1. 优先使用纵向线段确定表格的左右边界
        left_boundary = None
        right_boundary = None
        
        if vertical_lines:
            self.debug(f"[步骤4] 使用纵向线段确定表格边界...")
            vertical_x_coords = []
            
            for line in vertical_lines:
                x1, y1 = line['endpoints'][0]
                x2, y2 = line['endpoints'][1]
                # 纵向线段的X坐标应该相同或非常接近
                avg_x = (x1 + x2) // 2
                vertical_x_coords.append(avg_x)
            
            if vertical_x_coords:
                sorted_x = sorted(vertical_x_coords)
                left_boundary = min(sorted_x)    # 最左纵向线段
                right_boundary = max(sorted_x)   # 最右纵向线段
                self.debug(f"[步骤4] 基于纵向线段确定边界: X={left_boundary} 到 X={right_boundary}")
        
        # 2. 如果没有纵向线段信息，回退到横向线段端点分析
        if left_boundary is None or right_boundary is None:
            self.debug(f"[步骤4] 未找到纵向线段，使用横向线段端点分析...")
            all_x_points = []
            
            for line in horizontal_lines:
                x1, y1 = line['endpoints'][0]
                x2, y2 = line['endpoints'][1]
                all_x_points.extend([x1, x2])
            
            if all_x_points:
                sorted_x = sorted(all_x_points)
                left_boundary = sorted_x[int(len(sorted_x) * 0.05)]    # 排除最左5%的异常点
                right_boundary = sorted_x[int(len(sorted_x) * 0.95)]   # 排除最右5%的异常点
            else:
                return horizontal_lines
        
        # 3. 分析横向线的Y位置分布
        y_positions = set()
        y_tolerance = 3  # Y坐标容差
        
        for line in horizontal_lines:
            x1, y1 = line['endpoints'][0]
            x2, y2 = line['endpoints'][1]
            
            # 收集Y位置（取平均值并按容差分组）
            avg_y = (y1 + y2) // 2
            
            # 找到相近的Y位置
            found_y = None
            for existing_y in y_positions:
                if abs(avg_y - existing_y) <= y_tolerance:
                    found_y = existing_y
                    break
            
            if found_y is not None:
                # 如果找到相近的Y位置，可能需要更新为平均值
                y_positions.remove(found_y)
                y_positions.add((found_y + avg_y) // 2)
            else:
                y_positions.add(avg_y)
        
        self.debug(f"[步骤4] 表格边界: X={left_boundary} 到 X={right_boundary}")
        self.debug(f"[步骤4] 发现 {len(y_positions)} 个不同高度的横向线")
        
        # 4. 质量过滤：检查每个高度的线段覆盖率
        table_width = right_boundary - left_boundary
        coverage_threshold = 0.35  # 35%覆盖率阈值
        
        # 重新分析Y位置，计算每个高度的线段覆盖率
        valid_y_positions = []
        
        for check_y in y_positions:
            # 计算这个Y高度所有线段的总覆盖长度
            total_coverage = 0
            for check_line in horizontal_lines:
                cx1, cy1 = check_line['endpoints'][0]
                cx2, cy2 = check_line['endpoints'][1]
                check_avg_y = (cy1 + cy2) // 2
                
                if abs(check_avg_y - check_y) <= y_tolerance:
                    # 计算线段长度
                    line_length = abs(cx2 - cx1)
                    total_coverage += line_length
            
            # 检查覆盖率
            coverage_ratio = total_coverage / table_width if table_width > 0 else 0
            
            if coverage_ratio >= coverage_threshold:
                valid_y_positions.append(check_y)
        
        self.debug(f"[步骤4] 质量过滤完成：保留 {len(valid_y_positions)} 条")
        
        # 5. 为通过质量检查的Y位置生成完整的理论横向线段
        theoretical_lines = []
        
        for y in sorted(valid_y_positions):
            # 创建从左边界到右边界的完整线段
            theoretical_line = {
                'endpoints': [[left_boundary, y], [right_boundary, y]],
                'angle_degrees': 0.0,
                'length': float(right_boundary - left_boundary),
                'type': 'theoretical',  # 标记为理论重建线段
                'quality_checked': True  # 标记为通过质量检查
            }
            theoretical_lines.append(theoretical_line)
        
        self.debug(f"[步骤4] 横向线重建: {len(horizontal_lines)} → {len(theoretical_lines)} 条")
        
        return theoretical_lines
    
    def _process_horizontal_lines_complete(self, horizontal_lines: List[Dict]) -> List[Dict]:
        """完整处理横向边线：合并和补全操作"""
        if not horizontal_lines:
            return []
        
        self.debug(f"[步骤4] 横向边线完整处理...")
        
        # 对于理论重建的线条，直接返回（已经处理过了）
        theoretical_lines = [line for line in horizontal_lines if line.get('type') == 'theoretical']
        if theoretical_lines:
            return theoretical_lines
        
        # 对于其他线条，进行KNN分组和合并  
        if len(horizontal_lines) > 1:
            h_groups = self._group_horizontal_lines_knn(horizontal_lines, distance_threshold=15.0)
            merged_horizontal = []
            for group_y_center, group_lines in h_groups.items():
                merged_line = self._merge_horizontal_group(group_lines)
                if merged_line:
                    merged_horizontal.append(merged_line)
            return merged_horizontal
        
        return horizontal_lines
    
    def _process_vertical_lines_with_horizontal_context(self, vertical_lines: List[Dict], 
                                                      horizontal_lines: List[Dict]) -> List[Dict]:
        """基于已处理的横向边线上下文，智能处理纵向边线"""
        if not vertical_lines:
            return []
        
        self.debug(f"[步骤4] 纵向边线智能处理...")
        
        # 简化处理：过滤太短的垂直线，并基于长度进一步筛选
        if not horizontal_lines:
            # 如果没有水平线参考，使用基本长度过滤
            min_length = 30
            filtered_lines = [line for line in vertical_lines if line['length'] >= min_length]
        else:
            # 计算水平线的平均长度作为参考
            avg_h_length = sum(line['length'] for line in horizontal_lines) / len(horizontal_lines)
            min_length = max(30, avg_h_length * 0.2)  # 至少是水平线平均长度的20%
            
            filtered_lines = [line for line in vertical_lines if line['length'] >= min_length]
        
        self.debug(f"[步骤4] 垂直线智能处理: {len(vertical_lines)} → {len(filtered_lines)} 条")
        
        return filtered_lines
    
    def _merge_horizontal_group(self, group_lines: List[Dict]) -> Dict:
        """合并水平线分组为单条线段（完全复制原版本算法）"""
        if not group_lines:
            return None
        
        if len(group_lines) == 1:
            return group_lines[0]
        
        # 计算平均Y坐标
        y_values = []
        min_x = float('inf')
        max_x = float('-inf')
        
        for line in group_lines:
            x1, y1 = line['endpoints'][0]
            x2, y2 = line['endpoints'][1]
            
            # 收集Y坐标
            y_values.extend([y1, y2])
            
            # 找到最左和最右的X坐标
            min_x = min(min_x, x1, x2)
            max_x = max(max_x, x1, x2)
        
        # 使用平均Y坐标
        avg_y = int(sum(y_values) / len(y_values))
        
        # 创建合并后的线段
        merged_line = {
            'endpoints': [[min_x, avg_y], [max_x, avg_y]],
            'angle_degrees': 0.0,
            'length': max_x - min_x,
            'type': 'merged_horizontal',
            'merged_from': len(group_lines)
        }
        
        return merged_line
    
    def _merge_horizontal_lines(self, group_lines: List[Dict]) -> Optional[Dict]:
        """合并同组的水平线"""
        if not group_lines:
            return None
        
        if len(group_lines) == 1:
            return group_lines[0]
        
        # 计算平均Y坐标
        total_y = 0
        total_weight = 0
        min_x = float('inf')
        max_x = float('-inf')
        
        for line in group_lines:
            x1, y1 = line['endpoints'][0]
            x2, y2 = line['endpoints'][1]
            
            # 使用线段长度作为权重
            weight = line['length']
            avg_y = (y1 + y2) / 2
            
            total_y += avg_y * weight
            total_weight += weight
            
            min_x = min(min_x, min(x1, x2))
            max_x = max(max_x, max(x1, x2))
        
        merged_y = int(total_y / total_weight)
        
        # 扩展线段
        extend_pixels = self.processing_params['extend_line_pixels']
        final_x1 = max(0, min_x - extend_pixels)
        final_x2 = max_x + extend_pixels
        
        merged_line = {
            'endpoints': [[int(final_x1), merged_y], [int(final_x2), merged_y]],
            'angle_degrees': 0.0,
            'length': float(final_x2 - final_x1),
            'merged_from': len(group_lines)
        }
        
        return merged_line
    
    def _process_vertical_lines_with_context(self, vertical_lines: List[Dict], 
                                           horizontal_lines: List[Dict]) -> List[Dict]:
        """基于水平线上下文处理垂直线"""
        if not vertical_lines:
            return []
        
        # 简化处理：过滤太短的垂直线
        min_length = 30  # 最小长度阈值
        filtered_lines = [line for line in vertical_lines if line['length'] >= min_length]
        
        return filtered_lines
    
    def _analyze_table_structure(self, theoretical_line_data: Dict[str, List]) -> Dict[str, Any]:
        """分析表格结构"""
        h_lines = theoretical_line_data['horizontal_lines']
        v_lines = theoretical_line_data['vertical_lines']
        
        analysis = {
            'line_counts': {
                'horizontal': len(h_lines),
                'vertical': len(v_lines),
                'total': len(h_lines) + len(v_lines)
            },
            'table_count': 0,
            'grid_cells': 0,
            'table_quality': 'none'
        }
        
        # 简单的表格识别
        min_lines = self.processing_params['min_table_lines']
        
        if len(h_lines) >= min_lines and len(v_lines) >= min_lines:
            analysis['table_count'] = 1
            analysis['grid_cells'] = (len(h_lines) - 1) * (len(v_lines) - 1)
            
            if analysis['grid_cells'] > 20:
                analysis['table_quality'] = 'complex'
            elif analysis['grid_cells'] > 5:
                analysis['table_quality'] = 'moderate'
            else:
                analysis['table_quality'] = 'simple'
        
        return analysis
    
    def _save_detection_results(self, line_data: Dict[str, List], 
                               theoretical_line_data: Dict[str, List],
                               table_analysis: Dict[str, Any]) -> Dict[str, str]:
        """保存检测结果文件"""
        result_files = {}
        
        # 保存原始线条数据
        line_data_path = self.save_result_json(line_data, "4.1_line_data.json")
        result_files['line_data'] = str(line_data_path) if line_data_path else ""
        
        # 保存理论重建线条数据
        theoretical_path = self.save_result_json(theoretical_line_data, "4.2_theoretical_line_data.json")
        result_files['theoretical_line_data'] = str(theoretical_path) if theoretical_path else ""
        
        # 保存表格分析结果
        analysis_path = self.save_result_json(table_analysis, "4.3_table_analysis.json")
        result_files['table_analysis'] = str(analysis_path) if analysis_path else ""
        
        self.debug(f"[步骤4] 保存结果: {len(result_files)} 个文件")
        
        return result_files
    
    def _clean_data_types(self, data: Any) -> Any:
        """清理数据类型，确保JSON可序列化"""
        if isinstance(data, dict):
            return {key: self._clean_data_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_data_types(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, (np.integer, np.int32, np.int64)):
            return int(data)
        elif isinstance(data, (np.floating, np.float32, np.float64)):
            return float(data)
        else:
            return data
