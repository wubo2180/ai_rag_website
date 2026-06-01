#!/usr/bin/env python3
"""
V3步骤3: 文字掩码处理
基于文本识别结果生成多种类型的掩码，为后续表格检测提供清洁的背景图像
"""

import cv2
import numpy as np
import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass

from utils.base_step import V3BaseStep
from visualization.step_visualizers import TextMaskingVisualizer
from .step2_text_recognition import TextBlock


@dataclass
class MaskingResult:
    """掩码处理结果"""
    text_removed_image_path: str
    masks: Dict[str, np.ndarray]
    statistics: Dict[str, Any]
    processing_metadata: Dict[str, Any]
    # 为下游步骤保留文本块信息
    text_blocks: List = None
    original_image_path: str = ""


class TextMaskingStep(V3BaseStep):
    """V3文字掩码处理步骤"""
    
    def __init__(self, config: Dict[str, Any], file_manager, logger):
        super().__init__(3, "文字掩码处理", config, file_manager, logger)
        
        # 初始化可视化器
        self.visualizer = TextMaskingVisualizer(
            self.step_number, config.visualization, file_manager, logger
        )
        
        # 处理参数配置
        self.processing_params = {
            # 掩码生成参数
            'mask_erosion_kernel_size': 3,
            'mask_erosion_iterations': 1,
            
            # 智能填充参数
            'brightness_threshold': 230,
            'min_bright_pixels': 5,
            'min_region_pixels': 10,
            'min_background_pixels': 100,
            
            # 默认背景色 (BGR格式)
            'default_background_color': [255, 255, 255],  # 白色
            
            # 高亮效果参数
            'highlight_alpha': 0.7,
            'highlight_beta': 0.3,
            
            # 置信度可视化
            'confidence_colormap': cv2.COLORMAP_JET
        }
        
        # 从配置中更新参数
        if hasattr(config, 'step_configs') and 3 in config.step_configs:
            step_config = config.step_configs[3]
            self.processing_params.update(step_config.get('processing', {}))
    
    def execute(self, input_data: Tuple[str, List[TextBlock]]) -> Tuple[str, MaskingResult]:
        """执行文字掩码处理"""
        try:
            self.progress("[步骤3] 开始文字掩码处理...")
            
            image_path, text_blocks = input_data
            
            # 3.1 加载和验证输入图像
            image = self._load_and_validate_image(image_path)
            height, width = image.shape[:2]
            self.debug(f"[步骤3] 图像尺寸: {width} x {height}")
            
            # 3.2 生成多种类型的掩码
            self.progress("[步骤3] 生成文字区域掩码...")
            masks = self._generate_masks(image, text_blocks)
            
            # 3.3 统计掩码信息
            statistics = self._calculate_mask_statistics(text_blocks, masks)
            
            # 3.4 生成掩码效果图像
            self.progress("[步骤3] 应用掩码效果...")
            effect_images = self._generate_mask_effects(image, masks)
            
            # 3.5 智能文字移除和背景填充
            self.progress("[步骤3] 智能背景填充...")
            text_removed_image = self._intelligent_text_removal(image, masks)
            
            # 3.6 保存结果文件
            result_files = self._save_mask_results(masks, effect_images, text_removed_image)
            
            # 3.7 生成可视化
            if self.visualizer.is_enabled():
                processing_data = {
                    'original_image': image,
                    'masks': masks,
                    'effect_images': effect_images,
                    'text_removed_image': text_removed_image,
                    'statistics': statistics,
                    'text_blocks': text_blocks
                }
                visualization_files = self.visualizer.visualize_results(
                    image_path, result_files, processing_data
                )
                self.visualizer.log_visualization_summary(visualization_files)
            
            # 3.8 创建结果对象
            masking_result = MaskingResult(
                text_removed_image_path=result_files['text_removed'],
                masks=masks,
                statistics=statistics,
                processing_metadata={
                    'processing_params': self.processing_params,
                    'image_dimensions': {'width': width, 'height': height},
                    'total_text_blocks': len(text_blocks)
                },
                # 为下游步骤保留数据
                text_blocks=text_blocks,
                original_image_path=image_path
            )
            
            # 3.9 保存调试数据
            if self.should_save_debug():
                debug_data = {
                    'processing_params': self.processing_params,
                    'statistics': statistics,
                    'text_blocks_data': [block.__dict__ for block in text_blocks],
                    'mask_statistics': {
                        name: {
                            'shape': mask.shape,
                            'dtype': str(mask.dtype),
                            'non_zero_count': int(np.count_nonzero(mask)),
                            'coverage_ratio': float(np.count_nonzero(mask) / mask.size)
                        }
                        for name, mask in masks.items()
                    }
                }
                self.save_debug_data(self._clean_data_types(debug_data), "text_masking_debug.json")
            
            self.logger.result_summary(f"文字掩码处理完成: {len(masks)} 种掩码类型")
            return result_files['text_removed'], masking_result
            
        except Exception as e:
            self.logger.error(f"文字掩码处理失败: {str(e)}")
            raise
    
    def _load_and_validate_image(self, image_path: str) -> np.ndarray:
        """加载和验证输入图像"""
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        return image
    
    def _generate_masks(self, image: np.ndarray, text_blocks: List[TextBlock]) -> Dict[str, np.ndarray]:
        """生成多种类型的掩码"""
        height, width = image.shape[:2]
        
        # 初始化掩码
        masks = {
            'text_mask': np.zeros((height, width), dtype=np.uint8),           # 所有文本区域
            'background_mask': np.ones((height, width), dtype=np.uint8) * 255, # 背景区域
            'confidence_mask': np.zeros((height, width), dtype=np.uint8),     # 置信度掩码
            'handwriting_mask': np.zeros((height, width), dtype=np.uint8),    # 手写内容掩码
            'printed_mask': np.zeros((height, width), dtype=np.uint8)         # 打印内容掩码
        }
        
        # 为每个文本块生成掩码
        for block in text_blocks:
            poly_np = np.array(block.poly, dtype=np.int32).reshape((-1, 1, 2))
            
            # 所有文本都加入文本掩码
            cv2.fillPoly(masks['text_mask'], [poly_np], 255)
            cv2.fillPoly(masks['background_mask'], [poly_np], 0)  # 从背景中移除
            
            # 根据文本类型分别处理
            if block.is_handwritten:
                cv2.fillPoly(masks['handwriting_mask'], [poly_np], 255)
                self.debug(f"[步骤3] 手写内容: '{block.text}' (置信度: {block.confidence:.3f})")
            else:
                cv2.fillPoly(masks['printed_mask'], [poly_np], 255)
            
            # 置信度掩码 - 根据置信度设置灰度值
            confidence_value = int(block.confidence * 255)
            cv2.fillPoly(masks['confidence_mask'], [poly_np], confidence_value)
        
        return masks
    
    def _calculate_mask_statistics(self, text_blocks: List[TextBlock], 
                                 masks: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """计算掩码统计信息"""
        printed_blocks = [b for b in text_blocks if not b.is_handwritten]
        handwritten_blocks = [b for b in text_blocks if b.is_handwritten]
        
        total_pixels = masks['text_mask'].size
        
        statistics = {
            'block_counts': {
                'total': len(text_blocks),
                'printed': len(printed_blocks),
                'handwritten': len(handwritten_blocks)
            },
            'confidence_stats': {
                'avg': float(np.mean([b.confidence for b in text_blocks])) if text_blocks else 0.0,
                'min': float(min([b.confidence for b in text_blocks])) if text_blocks else 0.0,
                'max': float(max([b.confidence for b in text_blocks])) if text_blocks else 0.0
            },
            'coverage_stats': {
                name: {
                    'non_zero_pixels': int(np.count_nonzero(mask)),
                    'coverage_ratio': float(np.count_nonzero(mask) / total_pixels)
                }
                for name, mask in masks.items()
            }
        }
        
        return statistics
    
    def _generate_mask_effects(self, image: np.ndarray, 
                             masks: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """生成掩码效果图像"""
        effects = {}
        
        # 1. 文字高亮效果 (绿色高亮)
        highlighted = image.copy()
        text_overlay = cv2.cvtColor(masks['text_mask'], cv2.COLOR_GRAY2BGR)
        text_overlay[:, :, 0] = 0  # 去掉蓝色通道
        text_overlay[:, :, 2] = 0  # 去掉红色通道 (保留绿色)
        effects['highlighted'] = cv2.addWeighted(
            highlighted, 
            self.processing_params['highlight_alpha'],
            text_overlay, 
            self.processing_params['highlight_beta'], 
            0
        )
        
        # 2. 置信度可视化
        effects['confidence_colored'] = cv2.applyColorMap(
            masks['confidence_mask'], 
            self.processing_params['confidence_colormap']
        )
        
        # 3. 手写内容高亮 (红色高亮)
        if np.any(masks['handwriting_mask']):
            handwriting_highlighted = image.copy()
            handwriting_overlay = cv2.cvtColor(masks['handwriting_mask'], cv2.COLOR_GRAY2BGR)
            handwriting_overlay[:, :, 0] = 0  # 去掉蓝色通道
            handwriting_overlay[:, :, 1] = 0  # 去掉绿色通道 (保留红色)
            effects['handwriting_highlighted'] = cv2.addWeighted(
                handwriting_highlighted, 0.7, handwriting_overlay, 0.3, 0
            )
        
        return effects
    
    def _intelligent_text_removal(self, image: np.ndarray, 
                                masks: Dict[str, np.ndarray]) -> np.ndarray:
        """智能文字移除和背景填充"""
        text_removed = image.copy()
        
        # 对文字掩码进行内缩，避免抗锯齿边界
        kernel_size = self.processing_params['mask_erosion_kernel_size']
        iterations = self.processing_params['mask_erosion_iterations']
        kernel = np.ones((kernel_size, kernel_size), np.uint8)
        text_mask_eroded = cv2.erode(masks['text_mask'], kernel, iterations=iterations)
        
        # 找到连通区域
        num_labels, labels = cv2.connectedComponents(text_mask_eroded)
        filled_regions = 0
        brightness_threshold = self.processing_params['brightness_threshold']
        
        self.debug(f"[步骤3] 开始智能填充，发现 {num_labels-1} 个连通区域")
        
        for label in range(1, num_labels):  # 跳过背景标签0
            region_mask = (labels == label).astype(np.uint8) * 255
            region_pixels = image[region_mask == 255]
            
            if len(region_pixels) >= self.processing_params['min_region_pixels']:
                # 策略1: 使用亮色像素计算局部背景色
                bright_pixels_mask = np.all(region_pixels >= brightness_threshold, axis=1)
                bright_pixels = region_pixels[bright_pixels_mask]
                
                if len(bright_pixels) >= self.processing_params['min_bright_pixels']:
                    local_bg_color = np.mean(bright_pixels, axis=0).astype(np.uint8)
                    self.debug(f"[步骤3] 区域{label}: 局部亮色背景 BGR{tuple(local_bg_color)} "
                             f"[总像素:{len(region_pixels)}, 亮色:{len(bright_pixels)}]")
                else:
                    # 策略2: 使用全部区域像素
                    local_bg_color = np.mean(region_pixels, axis=0).astype(np.uint8)
                    self.debug(f"[步骤3] 区域{label}: 局部全色背景 BGR{tuple(local_bg_color)} "
                             f"[总像素:{len(region_pixels)}, 亮色不足]")
                
                text_removed[region_mask == 255] = local_bg_color
                filled_regions += 1
            else:
                # 策略3: 使用全局纯背景色
                background_mask = masks['background_mask']
                handwriting_mask = masks['handwriting_mask']
                pure_background_mask = (background_mask == 255) & (handwriting_mask == 0)
                pure_background_pixels = image[pure_background_mask]
                
                if len(pure_background_pixels) >= self.processing_params['min_background_pixels']:
                    global_bg_color = np.mean(pure_background_pixels, axis=0).astype(np.uint8)
                    text_removed[region_mask == 255] = global_bg_color
                    self.debug(f"[步骤3] 区域{label}: 全局背景色 BGR{tuple(global_bg_color)} [区域像素不足]")
                else:
                    # 策略4: 使用默认背景色
                    default_color = self.processing_params['default_background_color']
                    text_removed[region_mask == 255] = default_color
                    self.debug(f"[步骤3] 区域{label}: 默认背景色 BGR{tuple(default_color)} [全局背景不足]")
                
                filled_regions += 1
        
        self.debug(f"[步骤3] 智能填充完成: {filled_regions}/{num_labels-1} 个文字区域")
        return text_removed
    
    def _save_mask_results(self, masks: Dict[str, np.ndarray], 
                         effect_images: Dict[str, np.ndarray],
                         text_removed_image: np.ndarray) -> Dict[str, str]:
        """保存掩码结果文件"""
        result_files = {}
        
        # 使用file_manager保存各种掩码到visualizations目录
        for mask_name, mask in masks.items():
            filename = f"3.1_{mask_name}.png"
            mask_path = self.file_manager.save_image(mask, filename, 3, "intermediate")
            if mask_path:
                result_files[mask_name] = str(mask_path)
                self.debug(f"[步骤3] 保存掩码: {mask_path}")
        
        # 使用file_manager保存效果图像到visualizations目录
        for effect_name, effect_image in effect_images.items():
            filename = f"3.2_{effect_name}.png"
            effect_path = self.file_manager.save_image(effect_image, filename, 3, "intermediate")
            if effect_path:
                result_files[effect_name] = str(effect_path)
                self.debug(f"[步骤3] 保存效果图: {effect_path}")
        
        # 使用file_manager保存文字移除图像到visualizations目录
        filename = "3.3_text_removed.png"
        text_removed_path = self.file_manager.save_image(text_removed_image, filename, 3, "intermediate")
        if text_removed_path:
            result_files['text_removed'] = str(text_removed_path)
            self.debug(f"[步骤3] 保存文字移除图: {text_removed_path}")
        
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
