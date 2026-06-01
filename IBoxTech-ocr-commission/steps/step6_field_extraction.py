#!/usr/bin/env python3
"""
V3步骤6: 字段提取
整合智能网格分析、内容单元格匹配和智能字段提取，完全复制原版本算法
"""

import cv2
import numpy as np
import json
import math
import datetime
import re
import os
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

from utils.base_step import V3BaseStep
from visualization.step_visualizers import FieldExtractionVisualizer
from .step5_text_aggregation import TextAggregationResult
from .step4_table_line_detection import LineDetectionResult


@dataclass
class FieldExtractionResult:
    """字段提取处理结果"""
    extraction_results_path: str
    grid_analysis_path: str
    content_match_path: str
    visualization_path: str
    extracted_fields: Dict[str, Any]
    processing_metadata: Dict[str, Any]


class FieldExtractionStep(V3BaseStep):
    """V3字段提取步骤 - 完全复制原版本实现"""

    def __init__(self, config: Dict[str, Any], file_manager, logger):
        super().__init__(6, "字段提取", config, file_manager, logger)
        self.visualizer = FieldExtractionVisualizer(
            self.step_number, config.visualization, file_manager, logger
        )
        
        # 原版本算法参数 - 完全不变
        self.processing_params = {
            # SmartGridAnalysis参数
            'vertical_effectiveness_threshold': 0.5,
            
            # ContentCellMatcher参数  
            'overlap_threshold': 0.3,
            'center_containment_weight': 0.7,
            'area_overlap_weight': 0.3,
            
            # SmartFieldExtractor参数
            'fuzzy_match_threshold': 0.8,
            'handwritten_confidence_threshold': 0.8
        }

    def execute(self, input_data: TextAggregationResult) -> FieldExtractionResult:
        """执行字段提取"""
        # 从step5获取内容数据
        content_blocks = input_data.content_blocks
        
        # 从文件系统加载step4的线段数据（需要原始图像路径和线段数据）
        step4_dir = self.file_manager.get_step_dir(4)
        step4_theoretical_line_path = step4_dir / '4.2_theoretical_line_data.json'
        if not step4_theoretical_line_path.exists():
            raise ValueError(f"无法找到step4的线段数据文件: {step4_theoretical_line_path}")
        
        with open(step4_theoretical_line_path, 'r', encoding='utf-8') as f:
            line_data = json.load(f)
        
        # 从visualizations目录获取原始图像路径（新文件组织结构）
        step1_vis_dir = self.file_manager.get_visualization_dir(1)
        step1_output_path = step1_vis_dir / '1.7_final_preprocessed.png'
        if not step1_output_path.exists():
            # 尝试从visualizations/step03获取text_removed图像
            step3_vis_dir = self.file_manager.get_visualization_dir(3)
            step3_output_path = step3_vis_dir / '3.3_text_removed.png'
            if step3_output_path.exists():
                original_image_path = str(step3_output_path)
            else:
                # 向后兼容：尝试旧的steps目录结构
                step1_dir = self.file_manager.get_step_dir(1)
                old_step1_path = step1_dir / '1.7_final_preprocessed.png'
                original_image_path = str(old_step1_path)
        else:
            original_image_path = str(step1_output_path)
        
        self.debug(f"输入数据：{len(content_blocks)}个内容块，{len(line_data.get('horizontal_lines', []))}条水平线，{len(line_data.get('vertical_lines', []))}条垂直线")
        
        # 6.1 智能网格分析（完全复制smart_grid_analysis.py）
        self.debug("执行智能网格分析...")
        grid_analysis_result = self._smart_grid_analysis(original_image_path, line_data)
        
        # 保存网格分析结果
        grid_analysis_path = self.save_result_json(grid_analysis_result, "6.1_smart_grid_analysis.json")
        self.info(f"智能网格分析完成: {len(grid_analysis_result.get('cells', []))}个单元格")
        
        # 6.2 内容单元格匹配（完全复制content_cell_matcher.py）
        self.debug("执行内容单元格匹配...")
        content_match_result = self._content_cell_matching(content_blocks, grid_analysis_result, original_image_path)
        
        # 保存内容匹配结果
        content_match_path = self.save_result_json(content_match_result, "6.2_content_cell_matching.json")
        matched_cells_count = content_match_result.get('match_statistics', {}).get('cells_with_content', 0)
        self.info(f"内容单元格匹配完成: {matched_cells_count}个单元格含有内容")
        
        # 6.3 智能字段提取（完全复制smart_field_extractor.py）
        self.debug("执行智能字段提取...")
        extracted_fields = self._smart_field_extraction(content_match_result)
        
        # 6.3.1 处理未分配到单元格的内容块
        self.debug("处理未分配到单元格的内容块...")
        uncelled_fields = self._extract_uncelled_content_fields(content_blocks, content_match_result, extracted_fields)
        
        # 合并结果
        extracted_fields.update(uncelled_fields)
        
        # 6.4 生成最终结果
        extraction_results = {
            'extraction_timestamp': str(datetime.datetime.now()),
            'source_content_blocks': len(content_blocks),
            'grid_cells_count': len(grid_analysis_result.get('cells', [])),
            'matched_cells_count': matched_cells_count,
            'total_fields_extracted': len(extracted_fields),
            'extraction_statistics': {
                'single_cell_fields': len([f for f in extracted_fields.values() if isinstance(f, dict) and f.get('type') == 'single_cell']),
                'adjacent_cell_fields': len([f for f in extracted_fields.values() if isinstance(f, dict) and f.get('type') == 'adjacent_cells']),
                'handwritten_fields': len([f for f in extracted_fields.values() if isinstance(f, dict) and f.get('type') == 'handwritten']),
                'table_data_count': len([f for f in extracted_fields.values() if isinstance(f, list)]),
            },
            'extracted_fields': extracted_fields
        }
        
        # 保存最终提取结果
        extraction_results_path = self.save_result_json(extraction_results, "6.3_field_extraction_results.json")
        
        # 6.5 生成可视化
        self.debug("生成字段提取可视化...")
        processing_data = {
            'content_blocks': content_blocks,
            'grid_analysis': grid_analysis_result,
            'content_match': content_match_result,
            'extracted_fields': extracted_fields,
            'line_data': line_data,  # 添加原始线段数据用于垂直线分析
            'processing_params': self.processing_params  # 添加处理参数用于阈值显示
        }
        visualization_files = self.visualizer.visualize_results(
            original_image_path, 
            {
                'extraction_results': extraction_results_path,
                'grid_analysis': grid_analysis_path,
                'content_match': content_match_path
            }, 
            processing_data
        )
        self.visualizer.log_visualization_summary(visualization_files)
        
        vis_path = visualization_files.get('field_extraction_visualization', '')
        
        # 输出统计信息
        field_count = len(extracted_fields)
        single_cell_count = extraction_results['extraction_statistics']['single_cell_fields']
        adjacent_cell_count = extraction_results['extraction_statistics']['adjacent_cell_fields'] 
        handwritten_count = extraction_results['extraction_statistics']['handwritten_fields']
        table_count = extraction_results['extraction_statistics']['table_data_count']
        
        self.info(f"字段提取完成: {field_count}个字段")
        self.info(f"字段统计:")
        self.info(f"  • 单格字段: {single_cell_count}个")
        self.info(f"  • 邻格字段: {adjacent_cell_count}个")
        self.info(f"  • 手写字段: {handwritten_count}个")
        self.info(f"  • 表格数据: {table_count}个")
        
        self.logger.result_summary(f"提取结构化字段: {field_count}个")
        
        return FieldExtractionResult(
            extraction_results_path=str(extraction_results_path),
            grid_analysis_path=str(grid_analysis_path),
            content_match_path=str(content_match_path),
            visualization_path=str(vis_path),
            extracted_fields=extracted_fields,
            processing_metadata={
                'processing_params': self.processing_params,
                'grid_cells_count': len(grid_analysis_result.get('cells', [])),
                'matched_cells_count': matched_cells_count,
                'total_fields_extracted': field_count,
                'field_statistics': extraction_results['extraction_statistics']
            }
        )

    def _smart_grid_analysis(self, image_path: str, line_data: Dict) -> Dict[str, Any]:
        """智能网格分析 - 完全复制smart_grid_analysis.py算法"""
        self.debug("🧠 智能网格分析器（行优先 + 动态列识别）")
        
        # 获取参数
        vertical_effectiveness_threshold = self.processing_params['vertical_effectiveness_threshold']
        
        # 1. 加载数据
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        horizontal_lines = line_data.get('horizontal_lines', [])
        vertical_lines = line_data.get('vertical_lines', [])
        
        self.debug(f"图像尺寸: {image.shape[1]} × {image.shape[0]}")
        self.debug(f"线段数据: {len(horizontal_lines)}条水平线, {len(vertical_lines)}条垂直线")
        
        # 2. 分析行结构
        self.debug("🔍 分析行结构...")
        
        # 提取水平线Y坐标并排序
        h_y_positions = []
        for line in horizontal_lines:
            y1, y2 = line['endpoints'][0][1], line['endpoints'][1][1]
            avg_y = (y1 + y2) / 2
            h_y_positions.append(avg_y)
        
        h_y_positions = sorted(set(h_y_positions))
        self.debug(f"发现 {len(h_y_positions)} 个唯一水平位置")
        
        # 生成行信息
        rows_info = []
        for i in range(len(h_y_positions) - 1):
            row_info = {
                'row_id': i,
                'top_y': h_y_positions[i],
                'bottom_y': h_y_positions[i + 1],
                'height': h_y_positions[i + 1] - h_y_positions[i],
                'center_y': (h_y_positions[i] + h_y_positions[i + 1]) / 2,
                'effective_verticals': [],  # 将在下一步填充
                'columns': []  # 将在下一步填充
            }
            rows_info.append(row_info)
        
        self.debug(f"识别到 {len(rows_info)} 行")
        
        # 3. 为每行分析列结构
        self.debug("🔍 为每行分析有效垂直线...")
        
        total_effective_lines = 0
        
        for row in rows_info:
            row_top = row['top_y']
            row_bottom = row['bottom_y']
            row_height = row['height']
            
            # 找出在此行内有效的垂直线
            effective_verticals = []
            
            for v_line in vertical_lines:
                v_y1, v_y2 = v_line['endpoints'][0][1], v_line['endpoints'][1][1]
                v_top = min(v_y1, v_y2)
                v_bottom = max(v_y1, v_y2)
                
                # 计算垂直线与当前行的交集
                overlap_top = max(row_top, v_top)
                overlap_bottom = min(row_bottom, v_bottom)
                
                if overlap_bottom > overlap_top:
                    overlap_height = overlap_bottom - overlap_top
                    effectiveness = overlap_height / row_height
                    
                    if effectiveness >= vertical_effectiveness_threshold:
                        v_x1, v_x2 = v_line['endpoints'][0][0], v_line['endpoints'][1][0]
                        avg_x = (v_x1 + v_x2) / 2
                        
                        effective_verticals.append({
                            'line': v_line,
                            'x_position': avg_x,
                            'effectiveness': effectiveness,
                            'overlap_height': overlap_height
                        })
            
            # 按X坐标排序
            effective_verticals.sort(key=lambda x: x['x_position'])
            row['effective_verticals'] = effective_verticals
            
            # 生成列信息
            columns = []
            for i in range(len(effective_verticals) - 1):
                column_info = {
                    'column_id': i,
                    'left_x': effective_verticals[i]['x_position'],
                    'right_x': effective_verticals[i + 1]['x_position'],
                    'width': effective_verticals[i + 1]['x_position'] - effective_verticals[i]['x_position'],
                    'center_x': (effective_verticals[i]['x_position'] + effective_verticals[i + 1]['x_position']) / 2
                }
                columns.append(column_info)
            
            row['columns'] = columns
            total_effective_lines += len(effective_verticals)
            
            self.debug(f"行{row['row_id']}: {len(effective_verticals)}条有效垂直线 → {len(columns)}列")
        
        self.debug(f"总计发现 {total_effective_lines} 条有效垂直线")
        
        # 4. 生成单元格
        self.debug("🔢 生成单元格...")
        
        cells = []
        cell_id = 0
        total_cells = 0
        
        for row in rows_info:
            row_cells = []
            
            for col in row['columns']:
                cell_info = {
                    'cell_id': cell_id,
                    'row_id': row['row_id'],
                    'column_id': col['column_id'],
                    'coordinates': f"({row['row_id']},{col['column_id']})",
                    'bbox': {
                        'x1': int(col['left_x']),
                        'y1': int(row['top_y']),
                        'x2': int(col['right_x']),
                        'y2': int(row['bottom_y']),
                        'width': int(col['width']),
                        'height': int(row['height'])
                    },
                    'center': {
                        'x': int(col['center_x']),
                        'y': int(row['center_y'])
                    },
                    'area': int(col['width'] * row['height']),
                    'row_info': {
                        'y_range': f"{row['top_y']:.0f}~{row['bottom_y']:.0f}",
                        'height': row['height']
                    },
                    'column_info': {
                        'x_range': f"{col['left_x']:.0f}~{col['right_x']:.0f}",
                        'width': col['width']
                    }
                }
                
                row_cells.append(cell_info)
                cells.append(cell_info)
                cell_id += 1
            
            total_cells += len(row_cells)
            self.debug(f"行{row['row_id']}: 生成 {len(row_cells)} 个单元格")
        
        self.debug(f"总计生成 {total_cells} 个单元格")
        
        # 5. 生成统计信息
        stats = {
            'total_rows': len(rows_info),
            'total_cells': len(cells),
            'avg_columns_per_row': sum(len(row['columns']) for row in rows_info) / len(rows_info) if rows_info else 0,
            'vertical_effectiveness_threshold': vertical_effectiveness_threshold,
            'total_effective_lines': total_effective_lines
        }
        
        # 返回结果
        return {
            'analysis_timestamp': str(datetime.datetime.now()),
            'image_dimensions': {'width': image.shape[1], 'height': image.shape[0]},
            'input_lines': {
                'horizontal_count': len(horizontal_lines),
                'vertical_count': len(vertical_lines)
            },
            'processing_parameters': {
                'vertical_effectiveness_threshold': vertical_effectiveness_threshold
            },
            'statistics': stats,
            'rows_info': rows_info,
            'cells': cells
        }

    def _content_cell_matching(self, content_blocks: List[Dict], grid_analysis: Dict, image_path: str) -> Dict[str, Any]:
        """内容单元格匹配 - 完全复制content_cell_matcher.py算法"""  
        self.debug("🔗 内容-单元格匹配器")
        
        # 获取网格单元格
        grid_cells = grid_analysis.get('cells', [])
        self.debug(f"网格单元格: {len(grid_cells)}个")
        self.debug(f"内容块: {len(content_blocks)}个")
        
        # 执行匹配逻辑
        # 为每个单元格初始化内容列表
        cell_contents = {cell['cell_id']: [] for cell in grid_cells}
        
        matched_count = 0
        unmatched_blocks = []
        
        for content_block in content_blocks:
            # 尝试匹配内容块到单元格
            matched_cell_id = self._find_best_matching_cell(content_block, grid_cells)
            
            if matched_cell_id is not None:
                cell_contents[matched_cell_id].append(content_block)
                matched_count += 1
            else:
                unmatched_blocks.append(content_block)
        
        self.debug(f"成功匹配: {matched_count}/{len(content_blocks)} 个内容块")
        self.debug(f"未匹配: {len(unmatched_blocks)} 个内容块")
        
        # 统计单元格内容情况
        cells_with_content = sum(1 for contents in cell_contents.values() if contents)
        multi_content_cells = sum(1 for contents in cell_contents.values() if len(contents) > 1)
        
        self.debug(f"有内容的单元格: {cells_with_content}/{len(grid_cells)} 个")
        self.debug(f"多内容单元格: {multi_content_cells} 个")
        
        # 生成增强的单元格数据（包含内容）
        self.debug("🔧 生成增强单元格数据...")
        
        matched_cells = []
        
        for cell in grid_cells:
            cell_id = cell['cell_id']
            contents = cell_contents[cell_id]
            
            # 创建增强的单元格数据
            enhanced_cell = cell.copy()
            enhanced_cell['content'] = {
                'block_count': len(contents),
                'has_content': len(contents) > 0,
                'is_multi_content': len(contents) > 1,
                'content_blocks': []
            }
            
            # 处理内容块
            if contents:
                # 按confidence排序，置信度高的在前
                sorted_contents = sorted(contents, key=lambda x: x['confidence'], reverse=True)
                
                for content_block in sorted_contents:
                    content_info = {
                        'id': content_block['id'],
                        'text': content_block['text'],
                        'confidence': content_block['confidence'],
                        'is_handwritten': content_block['is_handwritten'],
                        'type': content_block['type'],
                        'center': (content_block['center_x'], content_block['center_y']),
                        'bbox': content_block['bbox']
                    }
                    enhanced_cell['content']['content_blocks'].append(content_info)
                
                # 生成合并文本（多个内容块的情况）
                if len(contents) > 1:
                    combined_text = ' '.join([block['text'] for block in sorted_contents])
                    enhanced_cell['content']['combined_text'] = combined_text
                else:
                    enhanced_cell['content']['combined_text'] = contents[0]['text']
                
                # 计算平均置信度
                avg_confidence = sum(block['confidence'] for block in contents) / len(contents)
                enhanced_cell['content']['average_confidence'] = avg_confidence
                
                # 判断是否包含手写内容
                has_handwritten = any(block['is_handwritten'] for block in contents)
                enhanced_cell['content']['has_handwritten'] = has_handwritten
            
            matched_cells.append(enhanced_cell)
        
        # 生成统计信息
        match_stats = {
            'total_content_blocks': len(content_blocks),
            'total_cells': len(grid_cells),
            'matched_content_blocks': matched_count,
            'cells_with_content': cells_with_content,
            'empty_cells': len(grid_cells) - cells_with_content,
            'multi_content_cells': multi_content_cells,
            'unmatched_blocks_count': len(unmatched_blocks)
        }
        
        self.debug(f"匹配完成: {cells_with_content}个单元格含有内容")
        
        return {
            'matching_timestamp': str(datetime.datetime.now()),
            'match_statistics': match_stats,
            'matched_cells': matched_cells,
            'unmatched_blocks': unmatched_blocks,
            'cell_contents': cell_contents
        }
    
    def _find_best_matching_cell(self, content_block: Dict, grid_cells: List[Dict]) -> Optional[int]:
        """
        找到与内容块最佳匹配的单元格
        """
        content_bbox = content_block['bbox']
        content_center = (content_block['center_x'], content_block['center_y'])
        
        best_cell_id = None
        best_overlap_ratio = 0.0
        
        for cell in grid_cells:
            cell_bbox = cell['bbox']
            
            # 方法1: 检查中心点是否在单元格内
            if (cell_bbox['x1'] <= content_center[0] <= cell_bbox['x2'] and
                cell_bbox['y1'] <= content_center[1] <= cell_bbox['y2']):
                return cell['cell_id']  # 中心点匹配优先级最高
            
            # 方法2: 计算边界框重叠比例
            overlap_ratio = self._calculate_overlap_ratio(content_bbox, cell_bbox)
            
            if overlap_ratio > best_overlap_ratio and overlap_ratio > 0.1:  # 至少10%重叠
                best_overlap_ratio = overlap_ratio
                best_cell_id = cell['cell_id']
        
        return best_cell_id
    
    def _calculate_overlap_ratio(self, content_bbox: Dict, cell_bbox: Dict) -> float:
        """
        计算两个边界框的重叠比例
        """
        # 转换坐标格式
        content_left = content_bbox['min_x']
        content_right = content_bbox['max_x'] 
        content_top = content_bbox['min_y']
        content_bottom = content_bbox['max_y']
        
        cell_left = cell_bbox['x1']
        cell_right = cell_bbox['x2']
        cell_top = cell_bbox['y1'] 
        cell_bottom = cell_bbox['y2']
        
        # 计算重叠区域
        overlap_left = max(content_left, cell_left)
        overlap_right = min(content_right, cell_right)
        overlap_top = max(content_top, cell_top)
        overlap_bottom = min(content_bottom, cell_bottom)
        
        # 检查是否有重叠
        if overlap_right <= overlap_left or overlap_bottom <= overlap_top:
            return 0.0
        
        # 计算面积
        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
        content_area = (content_right - content_left) * (content_bottom - content_top)
        
        return overlap_area / content_area if content_area > 0 else 0.0

    def _smart_field_extraction(self, content_match_result: Dict) -> Dict[str, Any]:
        """智能字段提取 - 完全复制smart_field_extractor.py算法"""
        self.debug("🔍 智能字段提取器（基于单元格匹配）")
        
        # 获取增强的单元格数据
        matched_cells = content_match_result.get('matched_cells', [])
        unmatched_blocks = content_match_result.get('unmatched_blocks', [])
        
        # 只处理有内容的单元格
        enhanced_cells = [cell for cell in matched_cells if cell.get('content', {}).get('has_content', False)]
        
        self.debug(f"加载 {len(enhanced_cells)} 个有内容的单元格")
        self.debug(f"加载 {len(unmatched_blocks)} 个未匹配的内容块")
        
        # 建立单元格索引
        cells_by_position = {}
        cells_by_row = {}
        
        # 按位置索引
        for cell in enhanced_cells:
            row_id = cell['row_id']
            col_id = cell['column_id']
            cells_by_position[(row_id, col_id)] = cell
        
        # 按行索引
        for cell in enhanced_cells:
            row_id = cell['row_id']
            if row_id not in cells_by_row:
                cells_by_row[row_id] = []
            cells_by_row[row_id].append(cell)
        
        # 按列ID排序
        for row_id in cells_by_row:
            cells_by_row[row_id].sort(key=lambda x: x['column_id'])
        
        self.debug(f"建立索引: {len(cells_by_position)}个位置, {len(cells_by_row)}行")
        
        # 初始化字段定义
        field_definitions = self._initialize_field_definitions()
        
        # 执行字段提取
        self.debug("执行字段提取...")
        extracted_fields = {}
        
        for field_name, field_def in field_definitions.items():
            try:
                if field_def['type'] == 'single_cell':
                    result = self._extract_single_cell_field_impl(field_name, field_def, enhanced_cells)
                elif field_def['type'] == 'adjacent_cells':
                    result = self._extract_adjacent_cells_field_impl(field_name, field_def, enhanced_cells, cells_by_position)
                elif field_def['type'] == 'handwritten':
                    result = self._extract_handwritten_field_impl(field_name, field_def, enhanced_cells, cells_by_position)
                elif field_def['type'] == 'choice_field':
                    result = self._extract_choice_field_impl(field_name, field_def, enhanced_cells, cells_by_position)
                elif field_def['type'] == 'multi_row_table':
                    result = self._extract_multi_row_table_impl(field_name, field_def, enhanced_cells, cells_by_row)
                else:
                    result = None
                
                if result is not None:
                    extracted_fields[field_name] = result
                    self.debug(f"✅ {field_name}: {self._format_extraction_result_preview(result)}")
                else:
                    if field_def.get('required', False):
                        self.debug(f"❌ {field_name}: 必填字段未找到")
                        
            except Exception as e:
                self.debug(f"❌ {field_name}: 提取失败 - {str(e)}")
        
        # 注意：智能表格识别已通过新的multi_row_table实现，无需重复执行
        # self.debug("智能表格识别和提取...")
        # table_results = self._extract_intelligent_tables_impl(enhanced_cells, cells_by_row)
        # extracted_fields.update(table_results)
        
        # 处理未匹配的内容块
        self.debug("处理未匹配的内容块...")
        unmatched_results = self._process_unmatched_blocks_impl(unmatched_blocks, field_definitions, extracted_fields)
        extracted_fields.update(unmatched_results)
        
        self.debug(f"字段提取完成: {len(extracted_fields)} 个字段")
        
        return extracted_fields

    def _initialize_field_definitions(self) -> Dict[str, Dict]:
        """初始化字段定义 - 根据用户重申的34个字段规则优化"""
        return {
            # 一格横向字段（字段名和内容在同一格子中，用":"分隔）
            '表格编号': {'type': 'single_cell', 'pattern': r'表格编号[：:](.+)', 'required': True},
            '研发项目': {'type': 'single_cell', 'pattern': r'研发项目[：:](.+)', 'required': False},
            '物料代码': {'type': 'single_cell', 'pattern': r'物料代码[：:](.+)', 'required': False},
            '委托编号': {'type': 'single_cell', 'pattern': r'委托编号[：:](.+)', 'required': True},
            '服务类型': {'type': 'single_cell', 'pattern': r'服务类型[：:](.+)', 'required': True},
            '是否需要报告': {'type': 'single_cell', 'pattern': r'是否需要报告[：:](.+)', 'required': True},
            
            # 邻格横向字段（字段名和内容在相邻格子中，内容在右侧）
            '委托部门': {'type': 'adjacent_cells', 'label': '委托部门', 'required': True, 'direction': 'right'},
            '委托人': {'type': 'adjacent_cells', 'label': '委托人', 'required': True, 'direction': 'right'},
            '委托日期': {'type': 'adjacent_cells', 'label': '委托日期', 'required': True, 'direction': 'right'},
            '样品名称': {'type': 'adjacent_cells', 'label': '样品名称', 'required': True, 'direction': 'right'},
            '样品数量': {'type': 'adjacent_cells', 'label': '样品数量', 'required': True, 'direction': 'right'},
            '样品代码': {'type': 'adjacent_cells', 'label': '样品代码', 'required': False, 'direction': 'right'},
            '产品或原材料型号': {'type': 'adjacent_cells', 'label': '产品或原材料型号', 'required': False, 'direction': 'right'},
            '样品批次': {'type': 'adjacent_cells', 'label': '样品批次', 'required': False, 'direction': 'right'},
            '送样时间': {'type': 'adjacent_cells', 'label': '送样时间', 'required': True, 'direction': 'right'},
            '需求时间': {'type': 'adjacent_cells', 'label': '需求时间', 'required': True, 'direction': 'right'},
            '余样处理': {'type': 'adjacent_cells', 'label': '余样处理', 'required': False, 'direction': 'right'},
            '测试性质': {'type': 'adjacent_cells', 'label': '测试性质', 'required': False, 'direction': 'right'},
            '样品重量': {'type': 'adjacent_cells', 'label': '样品重量', 'required': False, 'direction': 'right'},
            '样品储存方式': {'type': 'adjacent_cells', 'label': '样品储存方式', 'required': False, 'direction': 'right'},
            '此次投产数量': {'type': 'adjacent_cells', 'label': '此次投产数量', 'required': False, 'direction': 'right'},
            '委托地址': {'type': 'adjacent_cells', 'label': '委托地址', 'required': False, 'direction': 'right'},
            '测试说明': {'type': 'adjacent_cells', 'label': '测试说明', 'required': False, 'direction': 'right'},
            '有无特殊条件': {'type': 'adjacent_cells', 'label': '有无特殊条件', 'required': False, 'direction': 'right'},
            '条件是': {'type': 'adjacent_cells', 'label': '条件是', 'required': False, 'direction': 'right'},
            
            # 手写字段（字段名打印，内容手写，横向排布）
            '测试员': {'type': 'handwritten', 'label': '测试员', 'required': True, 'format': 'single_cell_horizontal'},
            '数据复核人': {'type': 'handwritten', 'label': '数据复核人', 'required': True, 'format': 'single_cell_horizontal'},
            '复核日期': {'type': 'handwritten', 'label': '复核日期', 'required': True, 'format': 'single_cell_horizontal'},
            # 签名字段（横向手写）
            '送样人签名': {'type': 'handwritten', 'label': '送样人签名/日期', 'required': True, 'format': 'horizontal_handwritten'},
            '业务受理人签字': {'type': 'handwritten', 'label': '业务受理人签字/日期', 'required': True, 'format': 'horizontal_handwritten'},
            
            # 测试中心填写内容（单选项类型，横向邻格中选择"是"或"否"）
            '申请单是否填写完整': {'type': 'choice_field', 'label': '申请单是否填写完整？无缺项或少项？', 'choices': ['是', '否'], 'required': False},
            '样品实物信息是否一致': {'type': 'choice_field', 'label': '样品实物信息与委托单表述是否一致？', 'choices': ['是', '否'], 'required': False},
            '样品是否完好': {'type': 'choice_field', 'label': '样品是否完好并无多余附带物，是否满足测试条件？', 'choices': ['是', '否'], 'required': False},
            '其他检查项': {'type': 'choice_field', 'label': '其他：', 'choices': ['是', '否'], 'required': False},
            
            # 多行内容字段（二维表格）
            '测试项目表': {
                'type': 'multi_row_table', 
                'table_type': 'type1',  # 第一类表格
                'header_fields': ['测试项目', '测试设备', '测试标准', '测试条件', '产品标准', '单位', '测试结果', '测试员', '备注'], 
                'required': False
            },
            '测试结果表': {
                'type': 'multi_row_table',
                'table_type': 'type2',  # 第二类表格（复杂多测试结构）
                'header_fields': ['元素名称', '标准', '实测', '备注'],
                'test_types': 'from_config',  # 从配置文件获取测试类型列表
                'required': False
            },
        }

    def _extract_single_cell_field_impl(self, field_name: str, field_def: Dict, enhanced_cells: List[Dict]) -> Optional[Dict]:
        """提取一格横向字段（字段名:内容在同一单元格中）"""
        pattern = field_def['pattern']
        
        for cell in enhanced_cells:
            text = cell['content']['combined_text']
            match = re.search(pattern, text)
            if match:
                return {
                    'type': 'single_cell',
                    'value': match.group(1).strip(),
                    'source_cell': {
                        'coordinates': cell['coordinates'],
                        'full_text': text,
                        'confidence': cell['content'].get('average_confidence', 0.0)
                    },
                    'extraction_method': 'single_cell_pattern'
                }
        return None

    def _extract_adjacent_cells_field_impl(self, field_name: str, field_def: Dict, enhanced_cells: List[Dict], cells_by_position: Dict) -> Optional[Dict]:
        """严格按照用户规则的邻格字段提取（字段名和内容在相邻格子，内容在横向右侧）"""
        label = field_def['label']
        direction = field_def.get('direction', 'right')  # 默认右侧
        
        self.debug(f"查找邻格字段: {field_name}, 标签: '{label}', 方向: {direction}")
        
        # 查找包含字段名的单元格（更严格的匹配）
        label_candidates = []
        for cell in enhanced_cells:
            text = cell['content']['combined_text'].strip()
            confidence = cell['content'].get('average_confidence', 0.0)
            
            # 更严格的标签匹配逻辑
            label_match_score = self._calculate_strict_label_match(text, label)
            if label_match_score > 0.7:  # 只有高匹配度的才考虑
                label_candidates.append((cell, confidence, label_match_score))
                self.debug(f"找到标签候选: '{text}' 匹配度: {label_match_score:.2f}")
        
        if not label_candidates:
            self.debug(f"未找到标签 '{label}' 的匹配单元格")
            return None
        
        # 按匹配质量和置信度排序
        label_candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
        
        # 尝试每个标签候选，严格按方向寻找内容
        for label_cell, label_conf, match_score in label_candidates:
            row_id = label_cell['row_id']
            col_id = label_cell['column_id']
            
            # 严格按照指定方向搜索（用户明确指定横向右侧）
            if direction == 'right':
                content_pos = (row_id, col_id + 1)
            elif direction == 'down':
                content_pos = (row_id + 1, col_id)
            elif direction == 'left':
                content_pos = (row_id, col_id - 1)
            else:  # up
                content_pos = (row_id - 1, col_id)
            
            content_cell = cells_by_position.get(content_pos)
            if content_cell:
                content_text = content_cell['content']['combined_text'].strip()
                content_conf = content_cell['content'].get('average_confidence', 0.0)
                
                # 严格的内容验证
                if self._is_valid_field_content(content_text, label, field_name):
                    self.debug(f"✅ 找到有效内容: '{content_text}'")
                    return {
                        'type': 'adjacent_cells',
                        'value': content_text,
                        'label_cell': {
                            'coordinates': label_cell['coordinates'],
                            'text': label_cell['content']['combined_text'],
                            'confidence': label_conf
                        },
                        'content_cell': {
                            'coordinates': content_cell['coordinates'],
                            'text': content_text,
                            'confidence': content_conf
                        },
                        'extraction_method': 'adjacent_cells_optimized',
                        'match_quality': {
                            'label_match_score': match_score,
                            'content_quality_score': content_conf
                        }
                    }
                else:
                    self.debug(f"❌ 内容无效: '{content_text}' (可能是标签或无关内容)")
        
        self.debug(f"未找到有效的邻格内容")
        return None
    
    def _calculate_label_match_score(self, text: str, label: str) -> float:
        """计算标签匹配分数"""
        text = text.strip()
        label = label.strip()
        
        if not text or not label:
            return 0.0
        
        # 完全匹配（去除可能的冒号）
        clean_text = text.rstrip('：:')
        if clean_text == label:
            return 1.0
        
        # 包含匹配
        if label in text:
            # 计算相似度
            similarity = len(label) / len(text)
            return max(0.8, similarity)
        
        # 部分匹配（至少50%字符相同）
        matching_chars = sum(1 for c in label if c in text)
        if matching_chars / len(label) >= 0.5:
            return 0.6
        
        return 0.0
    
    def _calculate_strict_label_match(self, text: str, label: str) -> float:
        """更灵活的标签匹配分数计算（支持带冒号的字段名）"""
        text = text.strip()
        label = label.strip()
        
        if not text or not label:
            return 0.0
        
        # 预处理：去除可能的冒号和空格进行标准化
        clean_text = text.rstrip('：: /').strip()
        clean_label = label.rstrip('：: /').strip()
        
        # 1. 完全匹配（最高优先级）
        if clean_text == clean_label:
            return 1.0
        
        # 2. 标签包含在文本中（考虑OCR可能识别出额外内容）
        if clean_label in clean_text:
            # 计算标签在文本中的比例
            ratio = len(clean_label) / len(clean_text)
            return 0.95 if ratio > 0.8 else 0.9
        
        # 3. 文本包含在标签中（处理字段定义更详细的情况）
        if clean_text in clean_label:
            ratio = len(clean_text) / len(clean_label)
            return 0.85 if ratio > 0.7 else 0.8
        
        # 4. 支持部分词汇匹配（处理复合字段名）
        # 比如 "业务受理人签字/日期" 可以匹配 "业务受理人签字"
        text_words = self._split_chinese_words(clean_text)
        label_words = self._split_chinese_words(clean_label)
        
        if text_words and label_words:
            # 计算词汇级别的重叠
            text_set = set(text_words)
            label_set = set(label_words)
            
            common_words = text_set & label_set
            if common_words:
                # 要求至少有一个关键词匹配，且总体匹配度较高
                overlap_ratio = len(common_words) / max(len(text_set), len(label_set))
                if overlap_ratio >= 0.6:
                    return 0.8
        
        # 5. 字符级别的相似度匹配（处理OCR识别错误）
        if len(label) >= 3:
            matching_chars = sum(1 for c in clean_label if c in clean_text)
            match_ratio = matching_chars / len(clean_label)
            if match_ratio >= 0.8:
                return 0.7
        
        return 0.0
    
    def _split_chinese_words(self, text: str) -> List[str]:
        """简单的中文分词（基于常见词汇）"""
        if not text:
            return []
        
        # 常见的字段关键词
        keywords = [
            '委托', '编号', '日期', '时间', '部门', '样品', '名称', '数量', '代码', 
            '批次', '送样', '需求', '余样', '处理', '测试', '性质', '重量', '储存',
            '投产', '地址', '说明', '条件', '复核', '签字', '签名', '受理', '业务',
            '申请单', '实物', '信息', '完好', '附带物', '满足', '检测', '报告'
        ]
        
        words = []
        i = 0
        while i < len(text):
            found_keyword = False
            # 尝试匹配最长的关键词
            for keyword in sorted(keywords, key=len, reverse=True):
                if text[i:].startswith(keyword):
                    words.append(keyword)
                    i += len(keyword)
                    found_keyword = True
                    break
            
            if not found_keyword:
                # 单个字符作为词
                words.append(text[i])
                i += 1
        
        return [w for w in words if len(w) > 1]  # 过滤单字符
    
    def _is_valid_field_content(self, content_text: str, label: str, field_name: str) -> bool:
        """验证字段内容是否有效"""
        if not content_text or len(content_text.strip()) == 0:
            return False
        
        content_text = content_text.strip()
        
        # 不能与标签相同
        if content_text == label or content_text.rstrip('：: ') == label:
            return False
        
        # 不能是明显的标签格式
        if self._is_obvious_label(content_text):
            return False
        
        # 不能包含其他字段的标签名
        if self._contains_other_field_labels(content_text, field_name):
            return False
        
        # 长度合理性检查
        if len(content_text) > 100:  # 避免过长的误匹配文本
            return False
        
        return True
    
    def _is_obvious_label(self, text: str) -> bool:
        """判断文本是否明显是标签"""
        text = text.strip()
        
        # 以冒号结尾的很可能是标签
        if text.endswith('：') or text.endswith(':'):
            return True
        
        # 包含明显标签特征词的
        label_keywords = ['编号', '日期', '时间', '名称', '部门', '数量', '批次', '方式', '类型', '说明', '条件', '处理', '性质', '重量', '地址', '储存']
        for keyword in label_keywords:
            if keyword in text and len(text) <= len(keyword) + 3:  # 短文本且包含标签词
                return True
        
        return False
    
    def _contains_other_field_labels(self, text: str, current_field: str) -> bool:
        """检查文本是否包含其他字段的标签名"""
        # 定义一些常见的字段标签
        common_field_labels = [
            '委托编号', '服务类型', '是否需要报告', '委托部门', '委托人', '委托日期',
            '样品名称', '样品数量', '样品代码', '样品批次', '送样时间', '需求时间',
            '测试员', '数据复核人', '复核日期', '申请单是否填写完整'
        ]
        
        for label in common_field_labels:
            if label != current_field and label in text:
                # 如果包含其他字段的标签，很可能是错误匹配
                return True
        
        return False
    
    def _is_likely_field_label(self, text: str) -> bool:
        """判断文本是否可能是字段标签"""
        # 获取所有字段定义的标签
        field_definitions = self._initialize_field_definitions()
        labels = [field_def.get('label', '') for field_def in field_definitions.values()]
        labels.extend(['委托编号', '服务类型', '表格编号', '研发项目', '物料代码', '是否需要报告'])
        
        text = text.strip().rstrip('：:')
        
        # 检查是否与已知标签匹配
        for label in labels:
            if label and (text == label or label in text):
                return True
        
        return False

    def _extract_handwritten_field_impl(self, field_name: str, field_def: Dict, enhanced_cells: List[Dict], cells_by_position: Dict) -> Optional[Dict]:
        """严格按照用户规则的手写字段提取（字段名打印，内容手写，横向排布）"""
        label = field_def['label']
        format_type = field_def.get('format', 'single_cell_horizontal')
        
        self.debug(f"查找手写字段: {field_name}, 标签: '{label}', 格式: {format_type}")
        
        # 查找包含字段名的单元格（使用严格匹配）
        label_candidates = []
        for cell in enhanced_cells:
            text = cell['content']['combined_text'].strip()
            confidence = cell['content'].get('average_confidence', 0.0)
            
            # 使用严格的标签匹配
            label_match_score = self._calculate_strict_label_match(text, label)
            if label_match_score > 0.7:  # 只考虑高匹配度
                label_candidates.append((cell, confidence, label_match_score))
                self.debug(f"找到手写字段标签候选: '{text}' 匹配度: {label_match_score:.2f}")
        
        if not label_candidates:
            self.debug(f"未找到手写字段标签 '{label}' 的匹配单元格")
            return None
        
        # 按匹配质量排序
        label_candidates.sort(key=lambda x: (x[2], x[1]), reverse=True)
        
        # 尝试每个标签候选
        for label_cell, label_conf, match_score in label_candidates:
            text = label_cell['content']['combined_text']
            has_handwritten = label_cell['content']['has_handwritten']
            
            if format_type == 'single_cell_horizontal':
                # 一格横向：字段名和手写内容在同一格子中（不依赖has_handwritten标志）
                
                # 优先尝试获取明确的手写块
                if has_handwritten:
                    handwritten_text = []
                    for block in label_cell['content']['content_blocks']:
                        if block.get('is_handwritten', False):
                            handwritten_text.append(block['text'])
                    
                    if handwritten_text:
                        value = ' '.join(handwritten_text).strip()
                        # 从手写内容中移除字段名标签（如果存在）
                        clean_value = self._clean_handwritten_value(value, label)
                        self.debug(f"✅ 找到单格横向手写内容: '{clean_value}' (原始: '{value}')")
                        return {
                            'type': 'handwritten',
                            'value': clean_value,
                            'source_cell': {
                                'coordinates': label_cell['coordinates'],
                                'full_text': text,
                                'confidence': label_conf
                            },
                            'extraction_method': 'handwritten_content',
                            'is_handwritten': True
                        }
                
                # 如果没有明确的手写块，或has_handwritten=false，从整个文本中提取内容部分
                full_text = label_cell['content']['combined_text']
                clean_value = self._clean_handwritten_value(full_text, label)
                if clean_value and clean_value != label.rstrip('：:'):
                    self.debug(f"✅ 从单格内完整文本提取手写内容: '{clean_value}' (来源: '{full_text}')")
                    return {
                        'type': 'handwritten',
                        'value': clean_value,
                        'source_cell': {
                            'coordinates': label_cell['coordinates'],
                            'full_text': full_text,
                            'confidence': label_conf
                        },
                        'extraction_method': 'handwritten_content_from_full_text',
                        'is_handwritten': True  # 根据字段定义认为是手写
                    }
            
            elif format_type == 'horizontal_handwritten' or format_type == 'adjacent_handwritten':
                # 横向手写：尝试找右侧相邻单元格的手写内容
                row_id = label_cell['row_id']
                col_id = label_cell['column_id']
                content_cell = cells_by_position.get((row_id, col_id + 1))
                
                if content_cell:
                    content_has_handwritten = content_cell['content']['has_handwritten']
                    content_text = content_cell['content']['combined_text'].strip()
                    
                    # 检查右侧格子是否有手写内容或者看起来像手写签名
                    if content_has_handwritten:
                        handwritten_text = []
                        for block in content_cell['content']['content_blocks']:
                            if block.get('is_handwritten', False):
                                handwritten_text.append(block['text'])
                        
                        if handwritten_text:
                            value = ' '.join(handwritten_text).strip()
                            clean_value = self._clean_handwritten_value(value, label)
                            self.debug(f"✅ 找到横向手写签名: '{clean_value}' (原始: '{value}')")
                            return {
                                'type': 'handwritten',
                                'value': clean_value,
                                'label_cell': {
                                    'coordinates': label_cell['coordinates'],
                                    'text': text
                                },
                                'content_cell': {
                                    'coordinates': content_cell['coordinates'],
                                    'text': content_text
                                },
                                'extraction_method': 'adjacent_handwritten',
                                'is_handwritten': True
                            }
                    elif content_text and self._looks_like_signature(content_text):
                        # 即使没有明确标记为手写，但内容看起来像签名
                        clean_value = self._clean_handwritten_value(content_text, label)
                        self.debug(f"✅ 找到疑似签名内容: '{clean_value}' (原始: '{content_text}')")
                        return {
                            'type': 'handwritten',
                            'value': clean_value,
                            'label_cell': {
                                'coordinates': label_cell['coordinates'],
                                'text': text
                            },
                            'content_cell': {
                                'coordinates': content_cell['coordinates'],
                                'text': content_text
                            },
                            'extraction_method': 'adjacent_handwritten',
                            'is_handwritten': True
                        }
                    else:
                        # 如果右侧没有内容，可能是字段名单独成行，内容在下方
                        down_cell = cells_by_position.get((row_id + 1, col_id))
                        if down_cell:
                            down_content = down_cell['content']['combined_text'].strip()
                            down_has_handwritten = down_cell['content']['has_handwritten']
                            
                            if down_has_handwritten or self._looks_like_signature(down_content):
                                clean_value = self._clean_handwritten_value(down_content, label)
                                self.debug(f"✅ 找到下方手写内容: '{clean_value}' (原始: '{down_content}')")
                                return {
                                    'type': 'handwritten',
                                    'value': clean_value,
                                    'label_cell': {
                                        'coordinates': label_cell['coordinates'],
                                        'text': text
                                    },
                                    'content_cell': {
                                        'coordinates': down_cell['coordinates'],
                                        'text': down_content
                                    },
                                    'extraction_method': 'below_handwritten',
                                    'is_handwritten': True
                                }
                
                # 尝试在标签单元格附近搜索相关的手写内容
                # 扩大搜索范围（考虑OCR可能将字段名和内容分别识别）
                nearby_positions = [
                    (row_id + 1, col_id + 1),  # 右下
                    (row_id - 1, col_id + 1),  # 右上  
                    (row_id, col_id + 2),      # 右侧两格
                ]
                
                for search_pos in nearby_positions:
                    nearby_cell = cells_by_position.get(search_pos)
                    if nearby_cell:
                        nearby_text = nearby_cell['content']['combined_text'].strip()
                        nearby_has_handwritten = nearby_cell['content']['has_handwritten']
                        
                        if nearby_text and (nearby_has_handwritten or self._looks_like_signature(nearby_text)):
                            # 检查是否与其他已识别字段冲突
                            if not self._contains_other_field_labels(nearby_text, field_name):
                                clean_value = self._clean_handwritten_value(nearby_text, label)
                                self.debug(f"✅ 在附近找到手写内容: '{clean_value}' (原始: '{nearby_text}')")
                                return {
                                    'type': 'handwritten',
                                    'value': clean_value,
                                    'label_cell': {
                                        'coordinates': label_cell['coordinates'],
                                        'text': text
                                    },
                                    'content_cell': {
                                        'coordinates': nearby_cell['coordinates'],
                                        'text': nearby_text
                                    },
                                    'extraction_method': 'nearby_handwritten',
                                    'is_handwritten': True
                                }
        
        self.debug(f"未找到有效的手写内容")
        return None
    
    def _looks_like_signature(self, text: str) -> bool:
        """判断文本是否看起来像签名或日期信息"""
        text = text.strip()
        if not text:
            return False
        
        # 1. 长度合理性检查（签名+日期通常不会太长）
        if len(text) > 30:
            return False
        
        # 2. 签名+日期的典型模式
        import re
        
        # 包含日期格式的模式（如：2023.4.18, 2023-04-18, 23.4.18等）
        date_patterns = [
            r'\d{4}[\.-]\d{1,2}[\.-]\d{1,2}',  # 2023.4.18 或 2023-04-18
            r'\d{2,4}[\.-]\d{1,2}[\.-]\d{1,2}',  # 23.4.18 或 2023.4.18
            r'\d{1,2}[\.-]\d{1,2}[\.-]\d{2,4}',  # 4.18.23 或 04.18.2023
        ]
        
        has_date = any(re.search(pattern, text) for pattern in date_patterns)
        
        # 3. 主要由中文字符、字母、数字、点号组成
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_chars = sum(1 for c in text if c.isalpha())
        digits = sum(1 for c in text if c.isdigit())
        punctuation = sum(1 for c in text if c in './-')
        
        total_chars = len(text)
        valid_chars = chinese_chars + english_chars + digits + punctuation
        
        # 如果大部分字符都是有效的签名字符
        if valid_chars >= total_chars * 0.9:
            # 4. 包含人名特征（中文字符）或日期
            if chinese_chars > 0 or has_date:
                # 5. 不包含明显的非签名词汇  
                non_signature_keywords = ['编号', '批次', '条件', '标准', '结果', '测试', '样品', '委托', '申请']
                for keyword in non_signature_keywords:
                    if keyword in text:
                        return False
                
                # 6. 典型签名模式
                # 人名+日期（如：张三2023.4.18）
                # 或纯人名（如：张三）
                # 或纯日期（如：2023.4.18）
                if has_date or (chinese_chars >= 2 and english_chars == 0) or re.match(r'^[\u4e00-\u9fff]+\d+[\.\-]\d+[\.\-]\d+$', text):
                    return True
        
        return False
    
    def _clean_handwritten_value(self, value: str, label: str) -> str:
        """从手写内容中清理掉字段名标签部分"""
        if not value or not label:
            return value
        
        value = value.strip()
        label_clean = label.rstrip('：:/').strip()
        
        import re
        
        # 1. 直接移除标签和冒号
        patterns_to_remove = [
            f'{re.escape(label_clean)}[：:]*\\s*',  # 完整标签+冒号
            f'{re.escape(label)}[：:]*\\s*',       # 原始标签+冒号
        ]
        
        for pattern in patterns_to_remove:
            cleaned = re.sub(f'^{pattern}', '', value, flags=re.IGNORECASE)
            if cleaned != value and cleaned.strip():
                return cleaned.strip()
        
        # 2. 如果标签在文本中间或者末尾，也尝试移除
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, '', value, flags=re.IGNORECASE)
            if cleaned != value and cleaned.strip():
                return cleaned.strip()
        
        # 3. 通用的冒号分割处理（针对"字段名：内容"格式）
        if '：' in value:
            parts = value.split('：', 1)
            if len(parts) == 2 and parts[1].strip():
                # 检查第一部分是否包含标签的关键词
                first_part = parts[0].strip()
                label_keywords = self._split_chinese_words(label_clean)
                
                # 如果第一部分包含标签的主要关键词，则返回第二部分
                if label_keywords and any(keyword in first_part for keyword in label_keywords if len(keyword) > 1):
                    return parts[1].strip()
        
        # 4. 如果没有成功清理，但值明显包含标签，尝试提取非标签部分
        if label_clean in value:
            # 找到标签后的内容
            label_index = value.find(label_clean)
            after_label = value[label_index + len(label_clean):].lstrip('：: ')
            if after_label and len(after_label) > 1:
                return after_label
        
        return value
    
    def _extract_uncelled_content_fields(self, content_blocks: List[Dict], content_match_result: Dict, existing_fields: Dict) -> Dict[str, Any]:
        """处理未分配到单元格的内容块，寻找遗漏的字段"""
        uncelled_fields = {}
        
        # 获取所有已分配到单元格的内容块ID
        matched_content_ids = set()
        matched_cells = content_match_result.get('matched_cells', [])
        
        for cell in matched_cells:
            cell_contents = cell.get('content', {})
            if 'content_blocks' in cell_contents:
                for block in cell_contents['content_blocks']:
                    block_id = block.get('id', '')
                    if block_id:
                        matched_content_ids.add(block_id)
        
        # 增强所有content_blocks的元数据
        enhanced_content_blocks = []
        unmatched_blocks = []
        
        for i, block in enumerate(content_blocks):
            # 为content_blocks添加必要的元数据
            block_enhanced = block.copy()
            block_enhanced['block_index'] = i
            
            # 添加ID (如果原始没有)
            if 'id' not in block_enhanced:
                block_enhanced['id'] = f"content_{i}"
            
            # 标准化bbox格式
            if 'bbox' in block and isinstance(block['bbox'], list) and len(block['bbox']) == 4:
                # 转换从[x1, y1, x2, y2]格式到字典格式
                x1, y1, x2, y2 = block['bbox']
                block_enhanced['bbox'] = {
                    'min_x': x1, 'min_y': y1, 'max_x': x2, 'max_y': y2,
                    'center_x': (x1 + x2) / 2, 'center_y': (y1 + y2) / 2
                }
            
            enhanced_content_blocks.append(block_enhanced)
            
            # 检查是否已经分配到单元格
            block_id = block_enhanced.get('id', f"content_{i}")
            if block_id not in matched_content_ids:
                unmatched_blocks.append(block_enhanced)
                self.debug(f"未分配内容块 {block_id}: '{block.get('text', '')[:50]}...'")
        
        self.debug(f"发现 {len(unmatched_blocks)} 个未分配到单元格的内容块")
        
        # 获取字段定义
        field_definitions = self._initialize_field_definitions()
        
        # 对每个未分配的内容块进行字段识别
        for block in unmatched_blocks:
            block_text = block.get('text', '').strip()
            if not block_text:
                continue
            
            # 检查是否包含字段标签
            for field_name, field_def in field_definitions.items():
                # 跳过已经提取的字段
                if field_name in existing_fields:
                    continue
                
                field_result = self._analyze_uncelled_block_for_field(block, field_def, field_name, enhanced_content_blocks)
                if field_result:
                    uncelled_fields[field_name] = field_result
                    self.debug(f"从未分配内容块中提取字段: {field_name} = '{field_result.get('value', '')}'")
                    break  # 每个block只匹配一个字段
        
        return uncelled_fields
    
    def _analyze_uncelled_block_for_field(self, block: Dict, field_def: Dict, field_name: str, all_content_blocks: List[Dict]) -> Optional[Dict]:
        """分析单个未分配内容块是否包含特定字段"""
        block_text = block.get('text', '').strip()
        block_index = block.get('block_index', -1)
        
        field_type = field_def.get('type', '')
        
        # 根据字段类型进行不同的处理
        if field_type == 'single_cell':
            return self._analyze_uncelled_single_cell_field(block, field_def, field_name)
        elif field_type == 'adjacent_cells':
            return self._analyze_uncelled_adjacent_field(block, field_def, field_name, all_content_blocks)
        elif field_type == 'handwritten':
            return self._analyze_uncelled_handwritten_field(block, field_def, field_name, all_content_blocks)
        elif field_type == 'choice_field':
            return self._analyze_uncelled_choice_field(block, field_def, field_name, all_content_blocks)
        
        return None
    
    def _analyze_uncelled_single_cell_field(self, block: Dict, field_def: Dict, field_name: str) -> Optional[Dict]:
        """分析未分配内容块中的单格字段"""
        block_text = block.get('text', '').strip()
        pattern = field_def.get('pattern', '')
        
        if pattern:
            import re
            match = re.search(pattern, block_text)
            if match:
                return {
                    'type': 'single_cell',
                    'value': match.group(1).strip(),
                    'source_block': {
                        'id': block.get('id'),
                        'text': block_text,
                        'bbox': block.get('bbox', {}),
                        'confidence': block.get('confidence', 0.0)
                    },
                    'extraction_method': 'uncelled_single_cell'
                }
        
        return None
    
    def _analyze_uncelled_adjacent_field(self, block: Dict, field_def: Dict, field_name: str, all_content_blocks: List[Dict]) -> Optional[Dict]:
        """分析未分配内容块中的邻格字段"""
        block_text = block.get('text', '').strip()
        label = field_def.get('label', '')
        block_index = block.get('block_index', -1)
        
        # 检查当前块是否包含字段标签
        label_match_score = self._calculate_strict_label_match(block_text, label)
        
        if label_match_score > 0.7:
            # 寻找右侧相邻的内容块作为字段值
            content_block = self._find_adjacent_content_block(block, all_content_blocks, 'right')
            
            if content_block:
                content_text = content_block.get('text', '').strip()
                
                # 验证内容有效性
                if content_text and self._is_valid_field_content(content_text, label, field_name):
                    clean_value = self._clean_handwritten_value(content_text, label)
                    
                    return {
                        'type': 'adjacent_cells',
                        'value': clean_value,
                        'label_block': {
                            'id': block.get('id'),
                            'text': block_text,
                            'bbox': block.get('bbox', {}),
                            'confidence': block.get('confidence', 0.0)
                        },
                        'content_block': {
                            'id': content_block.get('id'),
                            'text': content_text,
                            'bbox': content_block.get('bbox', {}),
                            'confidence': content_block.get('confidence', 0.0)
                        },
                        'extraction_method': 'uncelled_adjacent_cells'
                    }
        
        return None
    
    def _analyze_uncelled_handwritten_field(self, block: Dict, field_def: Dict, field_name: str, all_content_blocks: List[Dict]) -> Optional[Dict]:
        """分析未分配内容块中的手写字段"""
        block_text = block.get('text', '').strip()
        label = field_def.get('label', '')
        format_type = field_def.get('format', 'single_cell_horizontal')
        
        # 检查当前块是否包含字段标签
        label_match_score = self._calculate_strict_label_match(block_text, label)
        
        if label_match_score > 0.7:
            if format_type == 'single_cell_horizontal':
                # 检查当前块是否包含手写内容
                is_handwritten = block.get('is_handwritten', False)
                
                if is_handwritten:
                    # 从当前块提取手写部分
                    clean_value = self._clean_handwritten_value(block_text, label)
                    if clean_value and clean_value != label:
                        return {
                            'type': 'handwritten',
                            'value': clean_value,
                            'source_block': {
                                'id': block.get('id'),
                                'text': block_text,
                                'bbox': block.get('bbox', {}),
                                'confidence': block.get('confidence', 0.0)
                            },
                            'extraction_method': 'uncelled_handwritten_single',
                            'is_handwritten': True
                        }
                
            elif format_type in ['horizontal_handwritten', 'adjacent_handwritten']:
                # 寻找右侧相邻的手写内容块
                content_block = self._find_adjacent_content_block(block, all_content_blocks, 'right')
                
                if content_block:
                    content_text = content_block.get('text', '').strip()
                    is_handwritten = content_block.get('is_handwritten', False)
                    
                    if content_text and (is_handwritten or self._looks_like_signature(content_text)):
                        clean_value = self._clean_handwritten_value(content_text, label)
                        
                        return {
                            'type': 'handwritten',
                            'value': clean_value,
                            'label_block': {
                                'id': block.get('id'),
                                'text': block_text,
                                'bbox': block.get('bbox', {}),
                                'confidence': block.get('confidence', 0.0)
                            },
                            'content_block': {
                                'id': content_block.get('id'),
                                'text': content_text,
                                'bbox': content_block.get('bbox', {}),
                                'confidence': content_block.get('confidence', 0.0)
                            },
                            'extraction_method': 'uncelled_handwritten_adjacent',
                            'is_handwritten': True
                        }
                else:
                    # 没有找到相邻内容，返回空值结果（表示字段存在但未填写）
                    self.debug(f"⚠️  {field_name} 字段标签已找到，但未找到相邻的手写内容")
                    return {
                        'type': 'handwritten',
                        'value': '',  # 空值
                        'label_block': {
                            'id': block.get('id'),
                            'text': block_text,
                            'bbox': block.get('bbox', {}),
                            'confidence': block.get('confidence', 0.0)
                        },
                        'extraction_method': 'uncelled_handwritten_no_content',
                        'is_handwritten': False,
                        'note': '字段标签已识别，但未找到相应的手写内容'
                    }
        
        return None
    
    def _analyze_uncelled_choice_field(self, block: Dict, field_def: Dict, field_name: str, all_content_blocks: List[Dict]) -> Optional[Dict]:
        """分析未分配内容块中的选择字段"""
        block_text = block.get('text', '').strip()
        label = field_def.get('label', '')
        choices = field_def.get('choices', [])
        
        # 检查当前块是否包含字段标签
        label_match_score = self._calculate_strict_label_match(block_text, label)
        
        if label_match_score > 0.7:
            # 寻找右侧相邻的选择内容块
            content_block = self._find_adjacent_content_block(block, all_content_blocks, 'right')
            
            if content_block:
                content_text = content_block.get('text', '').strip()
                
                # 从选择文本中提取选中的值
                for choice in choices:
                    if choice in content_text:
                        return {
                            'type': 'choice_field',
                            'value': choice,
                            'label_block': {
                                'id': block.get('id'),
                                'text': block_text,
                                'bbox': block.get('bbox', {}),
                                'confidence': block.get('confidence', 0.0)
                            },
                            'choice_block': {
                                'id': content_block.get('id'),
                                'text': content_text,
                                'bbox': content_block.get('bbox', {}),
                                'confidence': content_block.get('confidence', 0.0)
                            },
                            'extraction_method': 'uncelled_choice_field'
                        }
        
        return None
    
    def _find_adjacent_content_block(self, block: Dict, all_content_blocks: List[Dict], direction: str = 'right') -> Optional[Dict]:
        """寻找相邻的内容块"""
        block_bbox = block.get('bbox', {})
        if not block_bbox:
            return None
        
        block_x = block_bbox.get('center_x', (block_bbox.get('min_x', 0) + block_bbox.get('max_x', 0)) / 2)
        block_y = block_bbox.get('center_y', (block_bbox.get('min_y', 0) + block_bbox.get('max_y', 0)) / 2)
        
        best_candidate = None
        best_distance = float('inf')
        
        for candidate in all_content_blocks:
            if candidate.get('id') == block.get('id'):  # 跳过自己
                continue
            
            candidate_bbox = candidate.get('bbox', {})
            if not candidate_bbox:
                continue
            
            cand_x = candidate_bbox.get('center_x', (candidate_bbox.get('min_x', 0) + candidate_bbox.get('max_x', 0)) / 2)
            cand_y = candidate_bbox.get('center_y', (candidate_bbox.get('min_y', 0) + candidate_bbox.get('max_y', 0)) / 2)
            
            if direction == 'right':
                # 寻找右侧的块：x坐标更大，y坐标相近
                if cand_x > block_x:
                    y_diff = abs(cand_y - block_y)
                    x_diff = cand_x - block_x
                    
                    # 综合距离评分：优先考虑y轴距离小的，然后考虑x轴距离小的
                    distance = y_diff * 2 + x_diff
                    
                    if distance < best_distance and y_diff < 50:  # y轴差距不能太大
                        best_distance = distance
                        best_candidate = candidate
        
        return best_candidate

    def _extract_intelligent_tables_impl(self, enhanced_cells: List[Dict], cells_by_row: Dict) -> Dict[str, Any]:
        """智能提取两种类型的表格 - 简化版本"""
        table_results = {}
        
        # 表格类型定义
        table_type1_headers = ['测试项目', '测试设备', '测试标准', '测试条件', '产品标准', '单位', '测试结果', '测试员', '备注']
        table_type2_headers = ['元素名称', '标准', '实测', '备注']
        
        # 简化的表格检测：寻找包含表格头的行
        for row_id, cells in cells_by_row.items():
            row_text = ' '.join([cell['content']['combined_text'] for cell in cells])
            
            # 检查第一类表格
            type1_matches = sum(1 for header in table_type1_headers if header in row_text)
            if type1_matches >= 3:
                self.debug(f"发现测试项目表表头 (行 {row_id}): {row_text[:100]}...")
                if '测试项目表' not in table_results:
                    table_results['测试项目表'] = {
                        'type': 'table_data',
                        'header_row': row_id,
                        'headers': [header for header in table_type1_headers if header in row_text],
                        'rows': []  # 简化版本暂不提取具体数据行
                    }
            
            # 检查第二类表格
            type2_matches = sum(1 for header in table_type2_headers if header in row_text)
            if type2_matches >= 2:
                self.debug(f"发现测试内容表表头 (行 {row_id}): {row_text[:100]}...")
                if '测试内容表' not in table_results:
                    table_results['测试内容表'] = {
                        'type': 'table_data',
                        'header_row': row_id,
                        'headers': [header for header in table_type2_headers if header in row_text],
                        'rows': []  # 简化版本暂不提取具体数据行
                    }
        
        return table_results

    def _process_unmatched_blocks_impl(self, unmatched_blocks: List[Dict], field_definitions: Dict, extracted_fields: Dict) -> Dict[str, Any]:
        """处理未匹配的内容块，尝试根据字段名和规则提取"""
        additional_fields = {}
        
        for block in unmatched_blocks:
            text = block['text']
            
            # 尝试单格字段提取
            for field_name, field_def in field_definitions.items():
                if field_def['type'] == 'single_cell' and field_name not in extracted_fields:
                    pattern = field_def['pattern']
                    match = re.search(pattern, text)
                    if match:
                        additional_fields[field_name] = {
                            'type': 'single_cell',
                            'value': match.group(1).strip(),
                            'source_block': {
                                'id': block['id'],
                                'text': text,
                                'confidence': block['confidence'],
                                'center': (block['center_x'], block['center_y'])
                            },
                            'extraction_method': 'unmatched_block_pattern'
                        }
                        self.debug(f"从未匹配块提取字段 {field_name}: {match.group(1).strip()}")
                        break
        
        return additional_fields

    def _fuzzy_match_label_impl(self, text: str, label: str) -> bool:
        """模糊匹配标签"""
        # 移除标点符号和空格进行比较
        clean_text = re.sub(r'[^\w]', '', text)
        clean_label = re.sub(r'[^\w]', '', label)
        
        return clean_label in clean_text or clean_text in clean_label

    def _format_extraction_result_preview(self, result: Dict) -> str:
        """格式化提取结果预览"""
        if isinstance(result, dict) and 'value' in result:
            value = result['value']
            if len(value) > 50:
                return f"{value[:47]}..."
            return value
        return str(result)[:50]
    
    def _extract_choice_field_impl(self, field_name: str, field_def: Dict, enhanced_cells: List[Dict], cells_by_position: Dict) -> Optional[Dict]:
        """提取选择字段（是/否类型）"""
        label = field_def['label']
        choices = field_def['choices']
        
        self.debug(f"查找选择字段: {field_name}, 标签: '{label}', 选项: {choices}")
        
        # 找到标签单元格
        label_cell = None
        for cell in enhanced_cells:
            text = cell['content']['combined_text'].strip()
            if self._calculate_label_match_score(text, label) > 0.8:
                label_cell = cell
                break
        
        if not label_cell:
            self.debug(f"❌ 未找到标签单元格: '{label}'")
            return None
        
        # 在标签单元格周围搜索选择项
        label_row = label_cell['row_id']
        label_col = label_cell['column_id']
        
        # 搜索右侧的几个单元格，寻找选择选项
        selected_choice = None
        choice_cell = None
        
        for offset in range(1, 4):  # 搜索右侧1-3个单元格
            search_pos = (label_row, label_col + offset)
            candidate_cell = cells_by_position.get(search_pos)
            
            if candidate_cell and candidate_cell.get('content', {}).get('has_content', False):
                text = candidate_cell['content']['combined_text'].strip()
                
                # 检查是否包含任何选择项
                for choice in choices:
                    if choice in text:
                        selected_choice = choice
                        choice_cell = candidate_cell
                        break
                
                if selected_choice:
                    break
        
        if selected_choice:
            self.debug(f"✅ 找到选择: '{selected_choice}'")
            return {
                'type': 'choice_field',
                'value': selected_choice,
                'label_cell': {
                    'coordinates': f"({label_cell['row_id']},{label_cell['column_id']})",
                    'text': label_cell['content']['combined_text'],
                    'confidence': label_cell['content'].get('avg_confidence', 0.0)
                },
                'choice_cell': {
                    'coordinates': f"({choice_cell['row_id']},{choice_cell['column_id']})",
                    'text': choice_cell['content']['combined_text'],
                    'confidence': choice_cell['content'].get('avg_confidence', 0.0)
                },
                'extraction_method': 'choice_field_pattern'
            }
        
        self.debug(f"❌ 未找到任何选择项")
        return None
    
    def _extract_multi_row_table_impl(self, field_name: str, field_def: Dict, enhanced_cells: List[Dict], cells_by_row: Dict) -> Optional[Dict]:
        """提取多行表格数据 - 支持两种复杂表格结构"""
        table_type = field_def.get('table_type', 'type1')
        header_fields = field_def['header_fields']
        
        self.debug(f"查找多行表格: {field_name}, 类型: {table_type}, 维度字段: {header_fields}")
        
        if table_type == 'type1':
            return self._extract_type1_table(field_name, header_fields, cells_by_row)
        elif table_type == 'type2':
            test_types_raw = field_def.get('test_types', [])
            
            # 如果配置为从配置文件获取测试类型
            if test_types_raw == 'from_config':
                test_types = self.config.test_types.known_test_types.copy()
            else:
                test_types = test_types_raw if isinstance(test_types_raw, list) else []
            
            self.debug(f"使用测试类型列表: {test_types}")
            return self._extract_type2_table(field_name, header_fields, test_types, cells_by_row)
        else:
            self.debug(f"❌ 未知表格类型: {table_type}")
            return None
    
    def _extract_type1_table(self, field_name: str, header_fields: List[str], cells_by_row: Dict) -> Optional[Dict]:
        """提取第一类表格：简单维度行开始
        
        对于"测试项目表"使用双检验方式
        """
        self.debug(f"开始提取第一类表格: {field_name}")
        
        # 只对"测试项目表"执行双检验
        if field_name == "测试项目表":
            self.debug(f"🔍 对'{field_name}'执行双检验")
            cells_by_row = self._dual_verify_table_structure(cells_by_row, field_name)
        
        # 查找维度行（表头）
        header_row_id = None
        matched_headers = []
        
        for row_id in sorted(cells_by_row.keys()):
            cells_in_row = cells_by_row[row_id]
            row_texts = []
            
            for cell in cells_in_row:
                if cell.get('content', {}).get('has_content', False):
                    text = cell['content']['combined_text'].strip()
                    row_texts.append(text)
            
            if len(row_texts) < 3:  # 至少需要3个单元格
                continue
            
            # 检查是否匹配表头（至少匹配一半的字段）
            matches = 0
            for expected_header in header_fields:
                for cell_text in row_texts:
                    if expected_header in cell_text:
                        matches += 1
                        break
            
            if matches >= len(header_fields) // 2:
                header_row_id = row_id
                matched_headers = row_texts
                self.debug(f"✅ 找到第一类表格维度行 {header_row_id}: {matched_headers}")
                break
        
        if header_row_id is None:
            self.debug(f"❌ 未找到第一类表格维度行")
            return None
        
        # 提取数据行
        data_rows = []
        current_row = header_row_id + 1
        
        while current_row in cells_by_row:
            # 检查表格结束条件
            if self._is_table_end(current_row, cells_by_row):
                break
            
            cells_in_row = cells_by_row[current_row]
            row_data = []
            has_data = False
            
            for cell in cells_in_row:
                if cell.get('content', {}).get('has_content', False):
                    text = cell['content']['combined_text'].strip()
                    row_data.append(text)
                    if text and not self._is_likely_field_label(text):
                        has_data = True
                else:
                    row_data.append("")
            
            if has_data and len(row_data) > 0:
                # 将行数据转换为字典格式，与表头字段对应
                row_dict = {}
                for i, header in enumerate(matched_headers):
                    if i < len(row_data):
                        row_dict[header] = row_data[i]
                    else:
                        row_dict[header] = ""  # 空cell处理
                
                data_rows.append(row_dict)
                self.debug(f"第一类表格数据行 {current_row}: {row_dict}")
            
            current_row += 1
        
        self.debug(f"✅ 第一类表格提取完成: {len(data_rows)} 行数据")
        
        return {
            'type': 'multi_row_table',
            'table_type': 'type1',
            'header': matched_headers,
            'data': data_rows,
            'header_row_id': header_row_id,
            'total_data_rows': len(data_rows),
            'extraction_method': 'type1_table_pattern'
        }
    
    def _extract_type2_table(self, field_name: str, header_fields: List[str], test_types: List[str], cells_by_row: Dict) -> Optional[Dict]:
        """提取第二类表格：复杂多测试结构
        
        对于"测试项目表"使用双检验方式：
        1. 基于cell识别的方式（现有）
        2. 基于位置对应关系的补充验证
        """
        self.debug(f"开始提取第二类表格: {field_name}, 测试类型: {test_types}")
        
        # 只对"测试项目表"执行双检验
        if field_name == "测试项目表":
            self.debug(f"🔍 对'{field_name}'执行双检验")
            cells_by_row = self._dual_verify_table_structure(cells_by_row, field_name)
        
        all_tests = []
        
        for row_id in sorted(cells_by_row.keys()):
            # 检查是否是测试名单cell行
            test_name = self._is_test_name_row(row_id, cells_by_row, test_types)
            if not test_name:
                continue
            
            self.debug(f"✅ 发现测试名: '{test_name}' 在行 {row_id}")
            
            # 查找下一行的维度行
            dimension_row_id = row_id + 1
            if dimension_row_id not in cells_by_row:
                continue
            
            dimension_headers = self._extract_dimension_row(dimension_row_id, cells_by_row, header_fields)
            if not dimension_headers:
                continue
            
            self.debug(f"✅ 找到维度行 {dimension_row_id}: {dimension_headers}")
            
            # 提取该测试的数据行
            test_data_rows = []
            current_row = dimension_row_id + 1
            
            while current_row in cells_by_row:
                # 检查表格结束条件
                if self._is_table_end(current_row, cells_by_row):
                    break
                
                # 检查是否遇到新的测试名（第二类表格内的多个测试）
                if self._is_test_name_row(current_row, cells_by_row, test_types):
                    break
                
                # 检查是否是包含'测试员'的结束行
                if self._is_test_end_row(current_row, cells_by_row):
                    self.debug(f"✅ 找到测试结束行 {current_row}")
                    break
                
                cells_in_row = cells_by_row[current_row]
                row_data = []
                has_data = False
                
                for cell in cells_in_row:
                    if cell.get('content', {}).get('has_content', False):
                        text = cell['content']['combined_text'].strip()
                        row_data.append(text)
                        if text and not self._is_likely_field_label(text):
                            has_data = True
                    else:
                        row_data.append("")
                
                if has_data and len(row_data) > 0:
                    # 将行数据转换为字典格式，仅使用基础维度字段
                    basic_fields = ['元素名称', '标准', '实测', '备注']
                    row_dict = {}
                    
                    # 只处理基础字段，保持数据结构一致性
                    for i, field in enumerate(basic_fields):
                        if i < len(row_data):
                            row_dict[field] = row_data[i]
                        else:
                            row_dict[field] = ""  # 空cell处理
                    
                    test_data_rows.append(row_dict)
                    self.debug(f"测试 '{test_name}' 数据行 {current_row}: {row_dict}")
                
                current_row += 1
            
            # 检测额外字段（超出基础4个字段的部分）
            basic_fields = ['元素名称', '标准', '实测', '备注']
            extra_fields = []
            
            for header in dimension_headers:
                if header.strip() and header not in basic_fields:
                    extra_fields.append(header)
            
            # 保存该测试的数据
            test_result = {
                'test_name': test_name,
                'header': basic_fields,  # 只保留基础字段作为标准表头
                'data': test_data_rows,
                'test_start_row': row_id,
                'dimension_row': dimension_row_id,
                'total_data_rows': len(test_data_rows)
            }
            
            # 如果有额外字段，单独存储
            if extra_fields:
                test_result['extra_info'] = extra_fields
                self.debug(f"测试 '{test_name}' 发现额外信息: {extra_fields}")
            all_tests.append(test_result)
            
            self.debug(f"✅ 测试 '{test_name}' 提取完成: {len(test_data_rows)} 行数据")
        
        if not all_tests:
            self.debug(f"❌ 未找到第二类表格数据")
            return None
        
        self.debug(f"✅ 第二类表格提取完成: {len(all_tests)} 个测试")
        
        return {
            'type': 'multi_row_table',
            'table_type': 'type2',
            'tests': all_tests,
            'total_tests': len(all_tests),
            'extraction_method': 'type2_table_pattern'
        }
    
    def _is_table_end(self, row_id: int, cells_by_row: Dict) -> bool:
        """判断表格是否结束"""
        if row_id not in cells_by_row:
            return True  # 没有行，表格结束
        
        cells_in_row = cells_by_row[row_id]
        
        # 检查是否是空行（没有cell或所有cell都为空）
        has_content = False
        for cell in cells_in_row:
            if cell.get('content', {}).get('has_content', False):
                text = cell['content']['combined_text'].strip()
                if text:
                    has_content = True
                    break
        
        if not has_content:
            self.debug(f"表格结束：空行 {row_id}")
            return True
        
        # 检查是否包含字段名
        for cell in cells_in_row:
            if cell.get('content', {}).get('has_content', False):
                text = cell['content']['combined_text'].strip()
                if text and self._is_likely_field_label(text):
                    self.debug(f"表格结束：发现字段名 '{text}' 在行 {row_id}")
                    return True
        
        return False
    
    def _is_test_name_row(self, row_id: int, cells_by_row: Dict, test_types: List[str]) -> Optional[str]:
        """判断是否是测试名单cell行，返回测试名
        
        基于结构判断逻辑：
        1. 当前行是单cell行（只有一个有内容的单元格）
        2. 下一行是维度行（多个有内容的单元格，类似表头）
        3. 再下一行是内容行
        """
        if row_id not in cells_by_row:
            return None
        
        cells_in_row = cells_by_row[row_id]
        
        # 统计有内容的单元格数量
        content_cells = []
        for cell in cells_in_row:
            if cell.get('content', {}).get('has_content', False):
                text = cell['content']['combined_text'].strip()
                if text:
                    content_cells.append(text)
        
        # 单cell行：只有一个有内容的单元格
        if len(content_cells) == 1:
            test_name = content_cells[0]
            
            # 检查下一行是否是维度行
            next_row_id = row_id + 1
            if self._is_dimension_row_structure(next_row_id, cells_by_row):
                self.debug(f"✅ 基于结构识别测试类型: '{test_name}' (单cell行 + 维度行结构)")
                return test_name
            
            # 备用：精确匹配已知测试类型
            for known_test in test_types:
                if known_test.lower() in test_name.lower() or test_name.lower() in known_test.lower():
                    self.debug(f"✅ 识别已知测试类型: '{test_name}' 匹配 '{known_test}'")
                    return test_name
            
            # 如果不符合结构要求，且不是已知类型，则不识别
            self.debug(f"⚠️ 单cell行 '{test_name}' 但下一行不是维度行结构，跳过")
        
        return None
    
    def _is_dimension_row_structure(self, row_id: int, cells_by_row: Dict) -> bool:
        """检查指定行是否符合维度行结构
        
        维度行特征：
        1. 有多个有内容的单元格（>=2个）
        2. 内容长度适中，不是很长的数据文本
        3. 不包含明显的数值或特殊符号
        """
        if row_id not in cells_by_row:
            return False
        
        cells_in_row = cells_by_row[row_id]
        
        # 统计有内容的单元格
        content_cells = []
        for cell in cells_in_row:
            if cell.get('content', {}).get('has_content', False):
                text = cell['content']['combined_text'].strip()
                if text:
                    content_cells.append(text)
        
        # 维度行至少需要2个有内容的单元格
        if len(content_cells) < 2:
            return False
        
        # 检查内容是否像表头字段
        dimension_indicators = 0
        for text in content_cells:
            # 表头字段通常比较短（1-10个字符）
            if 1 <= len(text) <= 10:
                dimension_indicators += 1
            
            # 常见的表头关键词
            if any(keyword in text for keyword in ['名称', '标准', '实测', '备注', '项目', '结果', '单位', '要求']):
                dimension_indicators += 1
            
            # 如果包含很长的文本或数值，可能不是表头
            if len(text) > 15 or any(char.isdigit() for char in text if char not in ['年', '月', '日']):
                dimension_indicators -= 1
        
        # 如果大部分内容符合表头特征，则认为是维度行
        is_dimension = dimension_indicators >= len(content_cells) * 0.5
        
        if is_dimension:
            self.debug(f"✅ 行 {row_id} 符合维度行结构: {content_cells}")
        else:
            self.debug(f"❌ 行 {row_id} 不符合维度行结构: {content_cells}")
        
        return is_dimension
    
    def _dual_verify_table_structure(self, cells_by_row: Dict, field_name: str) -> Dict:
        """双检验表格结构 - 专门针对测试项目表
        
        维度行cell数量为准，内容行cell与维度行不同就是缺失
        """
        self.debug(f"🔍 开始双检验表格结构: {field_name}")
        
        # 加载未匹配内容块和水平线数据
        unmatched_blocks = self._load_unmatched_content_blocks()
        horizontal_lines = self._load_horizontal_lines()
        
        verified_cells_by_row = cells_by_row.copy()
        
        # 找到维度行（表头行）- 对于测试项目表，应该包含"测试项目"等字段的行
        dimension_row_id = None
        max_cell_count = 0
        
        for row_id in sorted(cells_by_row.keys()):
            row_cells = cells_by_row[row_id]
            # 检查是否包含表头关键字段
            row_texts = []
            for cell in row_cells:
                if cell.get('content', {}).get('has_content', False):
                    text = cell['content']['combined_text'].strip()
                    row_texts.append(text)
            
            # 对于测试项目表，维度行应包含"测试项目"等关键字段
            if any('测试项目' in text or '测试标准' in text or '测试设备' in text for text in row_texts):
                dimension_row_id = row_id
                max_cell_count = len(row_cells)
                self.debug(f"📋 发现测试项目表维度行: Row {row_id}, 包含{max_cell_count}个cell")
                self.debug(f"    内容: {row_texts}")
                break
        
        if dimension_row_id is None:
            self.debug("⚠️ 未找到测试项目表维度行，跳过双检验")
            return verified_cells_by_row
        
        # 获取维度行的列结构
        reference_columns = [cell.get('column_id', 0) for cell in cells_by_row[dimension_row_id]]
        expected_columns = sorted(reference_columns)
        self.debug(f"📏 维度行{dimension_row_id}标准列: {expected_columns} (共{len(expected_columns)}列)")
        
        # 检查每行是否有缺失的cell
        for row_id in sorted(cells_by_row.keys()):
            if row_id == dimension_row_id:
                continue  # 跳过维度行本身
                
            row_cells = cells_by_row[row_id]
            current_columns = [cell.get('column_id', 0) for cell in row_cells]
            
            if len(current_columns) < len(expected_columns):
                self.debug(f"⚠️ Row {row_id} 缺失列: (现有{len(current_columns)}列，需要{len(expected_columns)}列)")
                self.debug(f"   当前列结构有错误，基于位置重新构建该行数据")
                
                # 当发现缺失时，说明cell位置识别有错误，基于位置坐标重新建立对应关系
                reconstructed_row = self._reconstruct_row_by_position(
                    row_id, dimension_row_id, cells_by_row, unmatched_blocks, horizontal_lines
                )
                
                if reconstructed_row:
                    verified_cells_by_row[row_id] = reconstructed_row
                    self.debug(f"✅ Row {row_id} 基于位置重构完成，包含{len(reconstructed_row)}个cell")
        
        self.debug(f"✅ 双检验完成")
        return verified_cells_by_row
    
    def _reconstruct_row_by_position(self, row_id: int, dimension_row_id: int, cells_by_row: Dict, 
                                   unmatched_blocks: List[Dict], horizontal_lines: List[Dict]) -> Optional[List[Dict]]:
        """基于位置坐标重新构建行数据
        
        当发现cell识别错误时，抛弃原有的cell-内容块匹配，
        改为基于水平线条和x坐标距离重新建立对应关系
        """
        self.debug(f"🔧 开始基于位置重构Row {row_id}")
        
        # 1. 获取维度行的字段x坐标作为参考
        dimension_row_cells = cells_by_row[dimension_row_id]
        dimension_fields_x = []
        for cell in dimension_row_cells:
            if cell.get('content', {}).get('has_content', False):
                field_name = cell['content']['combined_text'].strip()
                cell_bbox = cell.get('bbox', {})
                if cell_bbox:
                    # 使用cell中心x坐标
                    center_x = (cell_bbox['x1'] + cell_bbox['x2']) / 2
                    dimension_fields_x.append({
                        'field_name': field_name,
                        'x': center_x,
                        'column_id': cell.get('column_id', 0)
                    })
        
        dimension_fields_x.sort(key=lambda x: x['x'])  # 按x坐标排序
        self.debug(f"📏 维度行字段x坐标: {[(f['field_name'], f['x']) for f in dimension_fields_x]}")
        
        # 2. 根据水平线条确定目标行的Y范围
        row_y_range = self._get_row_y_range(row_id, cells_by_row, horizontal_lines)
        if not row_y_range:
            self.debug(f"❌ 无法确定Row {row_id}的Y范围")
            return None
        
        self.debug(f"📐 Row {row_id} Y范围: {row_y_range['min_y']} - {row_y_range['max_y']}")
        
        # 3. 收集该行范围内的所有内容块（包括已匹配和未匹配的）
        row_content_blocks = []
        
        # 从原有cells中收集已匹配的内容块
        for cell in cells_by_row.get(row_id, []):
            if cell.get('content', {}).get('has_content', False):
                content_text = cell['content']['combined_text'].strip()
                if content_text:
                    # 估算内容块的x坐标（使用cell的中心）
                    cell_bbox = cell.get('bbox', {})
                    if cell_bbox:
                        center_x = (cell_bbox['x1'] + cell_bbox['x2']) / 2
                        center_y = (cell_bbox['y1'] + cell_bbox['y2']) / 2
                        row_content_blocks.append({
                            'text': content_text,
                            'x': center_x,
                            'y': center_y,
                            'source': 'matched_cell'
                        })
        
        # 从未匹配内容块中收集
        for block in unmatched_blocks:
            block_y = block.get('bbox', {}).get('center_y', block.get('center_y', 0))
            if row_y_range['min_y'] <= block_y <= row_y_range['max_y']:
                content_text = block.get('text', '').strip()
                if content_text:
                    block_x = block.get('bbox', {}).get('center_x', block.get('center_x', 0))
                    row_content_blocks.append({
                        'text': content_text,
                        'x': block_x,
                        'y': block_y,
                        'source': 'unmatched_block'
                    })
        
        row_content_blocks.sort(key=lambda x: x['x'])  # 按x坐标排序
        self.debug(f"📊 Row {row_id}内容块: {[(b['text'], b['x']) for b in row_content_blocks]}")
        
        # 4. 根据x距离建立内容块与维度字段的对应关系
        reconstructed_cells = []
        for field_info in dimension_fields_x:
            field_name = field_info['field_name']
            field_x = field_info['x']
            column_id = field_info['column_id']
            
            # 找到距离该字段x坐标最近的内容块
            best_block = None
            min_distance = float('inf')
            
            for block in row_content_blocks:
                distance = abs(block['x'] - field_x)
                if distance < min_distance:
                    min_distance = distance
                    best_block = block
            
            # 如果距离合理（不超过字段宽度的2倍），则建立对应关系
            max_reasonable_distance = 200  # 可调整的阈值
            content_text = ""
            
            if best_block and min_distance < max_reasonable_distance:
                content_text = best_block['text']
                # 避免重复使用同一个内容块
                row_content_blocks.remove(best_block)
                self.debug(f"   {field_name} ← \"{content_text}\" (距离: {min_distance:.1f})")
            else:
                self.debug(f"   {field_name} ← \"\" (无匹配内容)")
            
            # 构建cell结构
            reconstructed_cell = {
                'row_id': row_id,
                'column_id': column_id,
                'cell_id': f"r{row_id}_c{column_id}",
                'bbox': {
                    'x1': field_x - 50,  # 估算bbox
                    'y1': row_y_range['min_y'],
                    'x2': field_x + 50,
                    'y2': row_y_range['max_y']
                },
                'content': {
                    'has_content': bool(content_text),
                    'combined_text': content_text,
                    'is_handwritten': False  # 基于位置重构的内容默认为印刷体
                },
                'reconstruction_method': 'position_based'
            }
            
            reconstructed_cells.append(reconstructed_cell)
        
        self.debug(f"✅ Row {row_id}重构完成: {len(reconstructed_cells)}个cell")
        return reconstructed_cells
    
    
    def _load_unmatched_content_blocks(self) -> List[Dict]:
        """加载未匹配的内容块"""
        try:
            import json
            step6_dir = self.file_manager.get_step_dir(6)
            match_file = step6_dir / '6.2_content_cell_matching.json'
            with open(match_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('unmatched_blocks', [])
        except Exception as e:
            self.debug(f"⚠️ 无法加载未匹配内容块: {e}")
            return []
    
    def _load_horizontal_lines(self) -> List[Dict]:
        """加载水平线数据"""
        try:
            import json
            step4_dir = self.file_manager.get_step_dir(4)
            line_file = step4_dir / '4.2_theoretical_line_data.json'
            with open(line_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data.get('horizontal_lines', [])
        except Exception as e:
            self.debug(f"⚠️ 无法加载水平线数据: {e}")
            return []
    
    def _supplement_missing_cells(self, row_id: int, missing_columns: List[int], 
                                  unmatched_blocks: List[Dict], horizontal_lines: List[Dict], 
                                  cells_by_row: Dict) -> List[Dict]:
        """为缺失的列补充cell内容"""
        supplemented_cells = []
        
        # 获取当前行的y坐标范围
        row_y_range = self._get_row_y_range(row_id, cells_by_row, horizontal_lines)
        if not row_y_range:
            return supplemented_cells
        
        # 获取各列的x坐标范围（基于维度行的列位置）
        column_x_ranges = self._estimate_column_x_ranges_from_dimension_row(missing_columns, cells_by_row)
        
        # 为每个缺失的列寻找匹配的未分配内容块
        for col_id in missing_columns:
            if col_id not in column_x_ranges:
                continue
                
            x_range = column_x_ranges[col_id]
            matching_blocks = self._find_blocks_in_region(
                unmatched_blocks, x_range, row_y_range
            )
            
            if matching_blocks:
                # 创建补充的cell
                cell = self._create_supplemented_cell(
                    row_id, col_id, matching_blocks, x_range, row_y_range
                )
                supplemented_cells.append(cell)
                self.debug(f"✅ 为Row {row_id}列{col_id}补充内容: {[b['text'] for b in matching_blocks]}")
        
        return supplemented_cells
    
    def _get_row_y_range(self, row_id: int, cells_by_row: Dict, horizontal_lines: List[Dict]) -> Optional[Dict]:
        """获取指定行的y坐标范围"""
        if row_id in cells_by_row and cells_by_row[row_id]:
            # 基于现有cell确定y范围
            cells = cells_by_row[row_id]
            min_y = min(cell.get('bbox', {}).get('y1', 0) for cell in cells if 'bbox' in cell)
            max_y = max(cell.get('bbox', {}).get('y2', 0) for cell in cells if 'bbox' in cell)
            return {'min_y': min_y, 'max_y': max_y}
        
        # 基于水平线估计y范围
        sorted_lines = sorted(horizontal_lines, key=lambda x: x.get('y', x.get('start_y', 0)))
        if row_id < len(sorted_lines) - 1:
            current_y = sorted_lines[row_id].get('y', sorted_lines[row_id].get('start_y', 0))
            next_y = sorted_lines[row_id + 1].get('y', sorted_lines[row_id + 1].get('start_y', 0))
            return {'min_y': current_y, 'max_y': next_y}
        
        return None
    
    def _estimate_column_x_ranges_from_dimension_row(self, missing_columns: List[int], cells_by_row: Dict) -> Dict:
        """基于维度行的列位置估计缺失列的x范围"""
        # 找到维度行 - 包含"测试项目"等关键字段的行
        dim_row_id = None
        for row_id in sorted(cells_by_row.keys()):
            row_cells = cells_by_row[row_id]
            row_texts = []
            for cell in row_cells:
                if cell.get('content', {}).get('has_content', False):
                    text = cell['content']['combined_text'].strip()
                    row_texts.append(text)
            
            if any('测试项目' in text or '测试标准' in text or '测试设备' in text for text in row_texts):
                dim_row_id = row_id
                break
        
        if dim_row_id is None:
            return self._estimate_column_x_ranges(missing_columns, cells_by_row)
        
        # 使用维度行作为参考
        dim_row_cells = cells_by_row.get(dim_row_id, [])
        
        column_x_ranges = {}
        for cell in dim_row_cells:
            col_id = cell.get('column_id', 0)
            bbox = cell.get('bbox', {})
            if bbox and col_id in missing_columns:
                column_x_ranges[col_id] = {
                    'min_x': bbox['x1'],
                    'max_x': bbox['x2']
                }
        
        self.debug(f"📏 基于维度行{dim_row_id}估计缺失列范围: {column_x_ranges}")
        return column_x_ranges
    
    def _estimate_column_x_ranges(self, missing_columns: List[int], cells_by_row: Dict) -> Dict:
        """基于其他行的列位置估计缺失列的x范围（备用方法）"""
        column_x_stats = {}
        
        # 收集各列的x坐标统计
        for row_cells in cells_by_row.values():
            for cell in row_cells:
                col_id = cell.get('column_id', 0)
                bbox = cell.get('bbox', {})
                if bbox:
                    x1, x2 = bbox.get('x1', 0), bbox.get('x2', 0)
                    if col_id not in column_x_stats:
                        column_x_stats[col_id] = {'x1_list': [], 'x2_list': []}
                    column_x_stats[col_id]['x1_list'].append(x1)
                    column_x_stats[col_id]['x2_list'].append(x2)
        
        # 为缺失列估计x范围
        estimated_ranges = {}
        for col_id in missing_columns:
            if col_id in column_x_stats:
                stats = column_x_stats[col_id]
                avg_x1 = sum(stats['x1_list']) / len(stats['x1_list'])
                avg_x2 = sum(stats['x2_list']) / len(stats['x2_list'])
                estimated_ranges[col_id] = {'min_x': avg_x1, 'max_x': avg_x2}
        
        return estimated_ranges
    
    def _find_blocks_in_region(self, unmatched_blocks: List[Dict], x_range: Dict, y_range: Dict) -> List[Dict]:
        """在指定区域内查找未匹配的内容块"""
        matching_blocks = []
        
        for block in unmatched_blocks:
            bbox = block.get('bbox', {})
            center_x = block.get('center_x', (bbox.get('min_x', 0) + bbox.get('max_x', 0)) / 2)
            center_y = block.get('center_y', (bbox.get('min_y', 0) + bbox.get('max_y', 0)) / 2)
            
            # 检查是否在指定区域内
            x_in_range = x_range['min_x'] <= center_x <= x_range['max_x']
            y_in_range = y_range['min_y'] <= center_y <= y_range['max_y']
            
            if x_in_range and y_in_range:
                matching_blocks.append(block)
        
        return matching_blocks
    
    def _create_supplemented_cell(self, row_id: int, col_id: int, blocks: List[Dict], 
                                  x_range: Dict, y_range: Dict) -> Dict:
        """创建补充的cell"""
        combined_text = ' '.join(block['text'] for block in blocks)
        avg_confidence = sum(block.get('confidence', 0.5) for block in blocks) / len(blocks)
        has_handwritten = any(block.get('is_handwritten', False) for block in blocks)
        
        return {
            'row_id': row_id,
            'column_id': col_id,
            'bbox': {
                'x1': int(x_range['min_x']),
                'y1': int(y_range['min_y']),
                'x2': int(x_range['max_x']),
                'y2': int(y_range['max_y'])
            },
            'content': {
                'has_content': True,
                'combined_text': combined_text,
                'average_confidence': avg_confidence,
                'has_handwritten': has_handwritten,
                'content_blocks': blocks,
                'extraction_method': 'dual_verification_supplement'
            }
        }
    
    
    def _verify_row_alignment(self, dim_row_id: int, cells_by_row: Dict, unmatched_blocks: List[Dict]):
        """基于维度行验证其他行的对齐情况"""
        # 这里可以实现更复杂的对齐验证逻辑
        # 暂时只做记录
        self.debug(f"📏 验证基于维度行 {dim_row_id} 的对齐情况")
    
    def _extract_dimension_row(self, row_id: int, cells_by_row: Dict, expected_headers: List[str]) -> Optional[List[str]]:
        """提取维度行"""
        if row_id not in cells_by_row:
            return None
        
        cells_in_row = cells_by_row[row_id]
        row_texts = []
        
        for cell in cells_in_row:
            if cell.get('content', {}).get('has_content', False):
                text = cell['content']['combined_text'].strip()
                row_texts.append(text)
            else:
                row_texts.append("")
        
        if len(row_texts) < 2:  # 至少需要2个字段
            return None
        
        # 检查是否匹配期望的维度字段
        matches = 0
        for expected_header in expected_headers:
            for cell_text in row_texts:
                if expected_header in cell_text:
                    matches += 1
                    break
        
        if matches >= len(expected_headers) // 2:  # 至少匹配一半
            return row_texts
        
        return None
    
    def _is_test_end_row(self, row_id: int, cells_by_row: Dict) -> bool:
        """判断是否是包含'测试员'的测试结束行"""
        if row_id not in cells_by_row:
            return False
        
        cells_in_row = cells_by_row[row_id]
        
        for cell in cells_in_row:
            if cell.get('content', {}).get('has_content', False):
                text = cell['content']['combined_text'].strip()
                if '测试员' in text:
                    return True
        
        return False
