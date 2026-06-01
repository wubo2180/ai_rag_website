#!/usr/bin/env python3
"""
V3步骤专用可视化器 - 每个步骤的可视化实现
"""

from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
import numpy as np
import cv2

from .base_visualizer import BaseVisualizer

class PreprocessingVisualizer(BaseVisualizer):
    """预处理步骤可视化器"""
    
    def visualize_results(self, input_data: Any, output_data: Any, 
                         intermediate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
        """可视化预处理结果"""
        saved_files = {}
        
        if not self.is_enabled():
            return saved_files
        
        # 从中间数据获取各阶段图像
        if intermediate_data:
            stages = intermediate_data.get('processing_stages', {})
            
            # 1. 创建处理流程对比图
            if self.should_save_intermediate():
                comparison_images = []
                
                # 收集各阶段图像
                stage_names = ['原始图像', '灰度图', '去噪图', '对比度增强', '锐化图', '倾斜校正']
                stage_keys = ['original', 'grayscale', 'denoised', 'enhanced', 'sharpened', 'deskewed']
                
                for name, key in zip(stage_names, stage_keys):
                    if key in stages:
                        img = stages[key]
                        # 确保图像为BGR格式用于显示
                        if len(img.shape) == 2:
                            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                        comparison_images.append((name, img))
                
                if comparison_images:
                    comparison_path = self.create_comparison_visualization(
                        comparison_images, 
                        "preprocessing_pipeline.png",
                        "预处理流水线对比"
                    )
                    if comparison_path:
                        saved_files['pipeline_comparison'] = comparison_path
            
            # 2. 创建质量提升对比图（前后对比）
            if 'original' in stages and 'deskewed' in stages:
                original = stages['original']
                final = stages['deskewed']
                
                # 确保格式一致
                if len(original.shape) == 3 and len(final.shape) == 2:
                    original_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
                    comparison = self._create_side_by_side(
                        original_gray, final, 
                        "原始图像", "预处理后"
                    )
                else:
                    comparison = self._create_side_by_side(
                        original, final, 
                        "原始图像", "预处理后"
                    )
                
                comparison_path = self.save_visualization(
                    comparison, 
                    "before_after_comparison.png",
                    "预处理前后对比"
                )
                if comparison_path:
                    saved_files['before_after'] = comparison_path
            
            # 3. 创建质量分析可视化（如果有统计信息）
            if self.should_save_debug():
                stats = intermediate_data.get('quality_stats', {})
                if stats:
                    analysis_img = self._create_quality_analysis(stages, stats)
                    if analysis_img is not None:
                        analysis_path = self.save_visualization(
                            analysis_img,
                            "quality_analysis.png",
                            "图像质量分析"
                        )
                        if analysis_path:
                            saved_files['quality_analysis'] = analysis_path
        
        return saved_files
    
    def _create_quality_analysis(self, stages: Dict[str, np.ndarray], 
                               stats: Dict[str, Any]) -> Optional[np.ndarray]:
        """创建质量分析可视化"""
        try:
            # 创建分析画布
            canvas_height = 800
            canvas_width = 1200
            canvas = np.ones((canvas_height, canvas_width, 3), dtype=np.uint8) * 255
            
            # 标题
            cv2.putText(canvas, "Image Quality Analysis", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
            
            y_offset = 80
            
            # 显示各阶段统计信息
            for stage_name, stage_data in stats.items():
                if isinstance(stage_data, dict):
                    # 阶段标题
                    cv2.putText(canvas, f"{stage_name}:", (20, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 100, 0), 2)
                    y_offset += 30
                    
                    # 统计信息
                    for key, value in stage_data.items():
                        if isinstance(value, (int, float)):
                            text = f"  {key}: {value:.2f}" if isinstance(value, float) else f"  {key}: {value}"
                            cv2.putText(canvas, text, (40, y_offset),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
                            y_offset += 25
                    
                    y_offset += 20
            
            # 如果有倾斜校正信息，显示角度信息
            if 'deskew_info' in stats:
                deskew_info = stats['deskew_info']
                cv2.putText(canvas, "Deskew Information:", (20, y_offset),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 150), 2)
                y_offset += 30
                
                for key, value in deskew_info.items():
                    text = f"  {key}: {value}"
                    cv2.putText(canvas, text, (40, y_offset),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (50, 50, 50), 1)
                    y_offset += 25
            
            return canvas
            
        except Exception as e:
            self.logger.debug(f"创建质量分析可视化失败: {e}")
            return None
    
    def visualize_deskew_process(self, original_img: np.ndarray, 
                               deskewed_img: np.ndarray, 
                               angle: float, 
                               lines_info: Dict[str, Any]) -> Optional[Path]:
        """可视化倾斜校正过程"""
        if not self.should_save_debug():
            return None
        
        try:
            # 创建倾斜校正可视化
            comparison = self._create_side_by_side(
                original_img, deskewed_img,
                f"Original (detected angle: {angle:.2f}°)",
                "Deskewed"
            )
            
            # 添加检测线条信息
            info_text = f"Lines detected: {lines_info.get('total_lines', 0)}, " \
                       f"Valid angles: {lines_info.get('valid_angles', 0)}"
            
            comparison = self._add_text_overlay(
                comparison, info_text, 
                (10, comparison.shape[0] - 20),
                (0, 0, 255), 0.5
            )
            
            return self.save_visualization(
                comparison,
                "deskew_process.png", 
                "倾斜校正过程"
            )
            
        except Exception as e:
            self.logger.debug(f"倾斜校正可视化失败: {e}")
            return None
    
    def visualize_noise_reduction(self, before: np.ndarray, 
                                after: np.ndarray,
                                method: str = "bilateral") -> Optional[Path]:
        """可视化噪声减少效果"""
        if not self.should_save_debug():
            return None
        
        try:
            # 计算噪声减少效果
            noise_diff = cv2.absdiff(before, after)
            
            # 创建三图对比
            images = [
                ("Original", before),
                ("Denoised", after),
                ("Noise Removed", noise_diff)
            ]
            
            grid_img = self._create_grid_visualization(images, cols=3)
            
            # 添加方法信息
            grid_img = self._add_text_overlay(
                grid_img, f"Method: {method}",
                (10, 10), (0, 0, 255), 0.6
            )
            
            return self.save_visualization(
                grid_img,
                "noise_reduction.png",
                "噪声减少效果"
            )
            
        except Exception as e:
            self.logger.debug(f"噪声减少可视化失败: {e}")
            return None
    
    def create_processing_summary(self, processing_stats: Dict[str, Any]) -> Optional[Path]:
        """创建处理摘要可视化"""
        if not self.should_save_intermediate():
            return None
        
        try:
            # 创建摘要画布
            canvas = np.ones((400, 800, 3), dtype=np.uint8) * 255
            
            # 标题
            cv2.putText(canvas, "Preprocessing Summary", (20, 40),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 0), 2)
            
            y_pos = 80
            
            # 处理统计
            for key, value in processing_stats.items():
                if isinstance(value, (int, float)):
                    if isinstance(value, float):
                        text = f"{key}: {value:.3f}"
                    else:
                        text = f"{key}: {value}"
                    
                    cv2.putText(canvas, text, (20, y_pos),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 50, 50), 2)
                    y_pos += 35
            
            return self.save_visualization(
                canvas,
                "processing_summary.png", 
                "处理摘要"
            )
            
        except Exception as e:
            self.logger.debug(f"处理摘要可视化失败: {e}")
            return None


class TextRecognitionVisualizer(BaseVisualizer):
    """Step2文本识别可视化器"""
    
    def __init__(self, step_number: int, config: Any, file_manager: Any, logger: Any):
        super().__init__(step_number, config, file_manager, logger)
        self.config = config  # 保存完整配置
    
    def visualize_results(self, image_path: str, text_blocks: List, 
                         processing_data: Dict[str, Any]) -> List[Path]:
        """生成文本识别可视化结果"""
        
        if not self.is_enabled():
            return []
        
        self.logger.debug(f"开始生成步骤 {self.step_number} 可视化结果...")
        generated_files = []
        
        try:
            # 读取原始图像
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                self.logger.warning(f"无法读取图像: {image_path}")
                return []
            
            # 1. 基础文本检测可视化
            basic_detection_path = self._create_basic_detection_visualization(image, text_blocks)
            if basic_detection_path:
                generated_files.append(basic_detection_path)
            
            # 2. 带文本内容的检测可视化
            text_content_path = self._create_text_content_visualization(image, text_blocks)
            if text_content_path:
                generated_files.append(text_content_path)
            
            # 3. 手写体检测可视化
            handwriting_path = self._create_handwriting_detection_visualization(image, text_blocks)
            if handwriting_path:
                generated_files.append(handwriting_path)
            
            # 4. 统计信息可视化
            if processing_data.get('statistics'):
                stats_path = self._create_statistics_visualization(processing_data['statistics'])
                if stats_path:
                    generated_files.append(stats_path)
            
            # 5. 文本分布分析图
            distribution_path = self._create_text_distribution_visualization(text_blocks, image.shape)
            if distribution_path:
                generated_files.append(distribution_path)
            
            self.logger.debug(f"步骤 {self.step_number} 可视化完成，生成 {len(generated_files)} 个文件")
            
        except Exception as e:
            self.logger.error(f"可视化生成失败: {str(e)}")
        
        return generated_files
    
    def _create_basic_detection_visualization(self, image: np.ndarray, text_blocks: List) -> Optional[Path]:
        """创建基础检测可视化"""
        
        vis_image = image.copy()
        
        for block in text_blocks:
            # 获取多边形点
            poly_np = np.array(block.poly, dtype=np.int32).reshape((-1, 1, 2))
            
            # 根据手写状态选择颜色
            color = (0, 0, 255) if block.is_handwritten else (0, 255, 0)  # 红色：手写，绿色：打印
            
            # 绘制边框
            cv2.polylines(vis_image, [poly_np], True, color, 2)
            
            # 添加索引标签
            center_x, center_y = int(block.center_x), int(block.center_y)
            cv2.putText(vis_image, str(block.index), (center_x-10, center_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return self.save_visualization(vis_image, "2.2_text_detection_basic.png")
    
    def _create_text_content_visualization(self, image: np.ndarray, text_blocks: List) -> Optional[Path]:
        """创建带文本内容的可视化"""
        
        vis_image = image.copy()
        
        for block in text_blocks:
            poly_np = np.array(block.poly, dtype=np.int32).reshape((-1, 1, 2))
            color = (0, 0, 255) if block.is_handwritten else (0, 255, 0)
            
            # 绘制边框
            cv2.polylines(vis_image, [poly_np], True, color, 2)
            
            # 添加文本内容（限制长度避免过长）
            display_text = block.text[:10] + "..." if len(block.text) > 10 else block.text
            text_pos = (int(block.x1), int(block.y1) - 5)
            cv2.putText(vis_image, display_text, text_pos, 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
        
        return self.save_visualization(vis_image, "2.3_text_detection_with_text.png")
    
    def _create_handwriting_detection_visualization(self, image: np.ndarray, text_blocks: List) -> Optional[Path]:
        """创建手写体检测可视化"""
        
        vis_image = image.copy()
        
        # 创建手写标记叠加层
        handwriting_overlay = np.zeros_like(image)
        
        for block in text_blocks:
            if block.is_handwritten:
                poly_np = np.array(block.poly, dtype=np.int32).reshape((-1, 1, 2))
                
                # 填充红色区域
                cv2.fillPoly(handwriting_overlay, [poly_np], (0, 0, 255))
                
                # 绘制红色边框
                cv2.polylines(vis_image, [poly_np], True, (0, 0, 255), 3)
                
                # 添加手写得分标签
                score_text = f"H:{block.handwriting_score}"
                cv2.putText(vis_image, score_text, 
                           (int(block.center_x)-20, int(block.center_y)), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        # 叠加半透明手写标记
        vis_image = cv2.addWeighted(vis_image, 0.7, handwriting_overlay, 0.3, 0)
        
        return self.save_visualization(vis_image, "2.4_handwriting_detection.png")
    
    def _create_statistics_visualization(self, statistics: Dict[str, Any]) -> Optional[Path]:
        """创建统计信息可视化"""
        
        try:
            import matplotlib.pyplot as plt
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
            
            # 1. 置信度分布直方图
            if statistics.get('confidence_stats'):
                confidence_stats = statistics['confidence_stats']
                ax1.bar(['最小值', '平均值', '最大值'], 
                       [confidence_stats['min'], confidence_stats['avg'], confidence_stats['max']],
                       color=['red', 'blue', 'green'])
                ax1.set_title('置信度统计')
                ax1.set_ylabel('置信度')
                ax1.set_ylim(0, 1)
                
                # 添加数值标签
                for i, v in enumerate([confidence_stats['min'], confidence_stats['avg'], confidence_stats['max']]):
                    ax1.text(i, v + 0.02, f'{v:.3f}', ha='center')
            
            # 2. 文本长度分布
            if statistics.get('text_lengths'):
                ax2.hist(statistics['text_lengths'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
                ax2.set_title('文本长度分布')
                ax2.set_xlabel('文本长度（字符数）')
                ax2.set_ylabel('频次')
            
            # 3. 文本块总数饼图
            total_blocks = statistics.get('total_blocks', 0)
            if total_blocks > 0:
                # 模拟手写vs打印的比例（这里需要从text_blocks获取实际数据）
                ax3.pie([total_blocks], labels=[f'总文本块: {total_blocks}'], autopct='%1.0f%%')
                ax3.set_title('文本块概览')
            
            # 4. 长度统计条形图
            if statistics.get('length_stats'):
                length_stats = statistics['length_stats']
                ax4.bar(['最小长度', '平均长度', '最大长度'],
                       [length_stats['min'], length_stats['avg'], length_stats['max']],
                       color=['orange', 'purple', 'brown'])
                ax4.set_title('文本长度统计')
                ax4.set_ylabel('字符数')
                
                # 添加数值标签
                for i, v in enumerate([length_stats['min'], length_stats['avg'], length_stats['max']]):
                    ax4.text(i, v + 0.5, f'{v:.1f}', ha='center')
            
            plt.tight_layout()
            
            # 保存图表
            import io
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # 转为图像数组并保存
            import PIL.Image
            image_pil = PIL.Image.open(buffer)
            image_array = np.array(image_pil)
            
            output_path = self.save_visualization(image_array, "2.6_text_statistics_chart.png", "统计图表")
            plt.close()
            buffer.close()
            
            self.logger.file_saved(output_path, "文本统计图表")
            return output_path
            
        except Exception as e:
            self.logger.error(f"统计图表生成失败: {e}")
            return None
    
    def _create_text_distribution_visualization(self, text_blocks: List, image_shape: Tuple) -> Optional[Path]:
        """创建文本分布可视化"""
        
        try:
            import matplotlib.pyplot as plt
            
            # 提取文本块中心点坐标
            centers_x = [block.center_x for block in text_blocks]
            centers_y = [block.center_y for block in text_blocks]
            
            # 区分手写和打印文本
            handwritten_x = [block.center_x for block in text_blocks if block.is_handwritten]
            handwritten_y = [block.center_y for block in text_blocks if block.is_handwritten]
            printed_x = [block.center_x for block in text_blocks if not block.is_handwritten]
            printed_y = [block.center_y for block in text_blocks if not block.is_handwritten]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # 1. 整体文本分布
            ax1.scatter(centers_x, centers_y, alpha=0.6, s=50)
            ax1.set_xlim(0, image_shape[1])
            ax1.set_ylim(image_shape[0], 0)  # 翻转Y轴匹配图像坐标
            ax1.set_title('文本块分布图')
            ax1.set_xlabel('X坐标')
            ax1.set_ylabel('Y坐标')
            ax1.grid(True, alpha=0.3)
            
            # 2. 手写vs打印分布
            if handwritten_x:
                ax2.scatter(handwritten_x, handwritten_y, color='red', alpha=0.7, s=50, label='手写文本')
            if printed_x:
                ax2.scatter(printed_x, printed_y, color='green', alpha=0.7, s=50, label='打印文本')
            
            ax2.set_xlim(0, image_shape[1])
            ax2.set_ylim(image_shape[0], 0)
            ax2.set_title('手写vs打印文本分布')
            ax2.set_xlabel('X坐标')
            ax2.set_ylabel('Y坐标')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # 保存图表
            import io
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # 转为图像数组并保存
            import PIL.Image
            image_pil = PIL.Image.open(buffer)
            image_array = np.array(image_pil)
            
            output_path = self.save_visualization(image_array, "2.7_text_distribution.png", "文本分布图")
            plt.close()
            buffer.close()
            
            self.logger.file_saved(output_path, "文本分布图")
            return output_path
            
        except Exception as e:
            self.logger.error(f"文本分布图生成失败: {e}")
            return None


class TextMaskingVisualizer(BaseVisualizer):
    """文字掩码处理可视化器"""
    
    def __init__(self, step_number: int, config: Any, file_manager: Any, logger: Any):
        super().__init__(step_number, config, file_manager, logger)
        self.config = config
    
    def visualize_results(self, image_path: str, result_files: Dict[str, str], 
                         processing_data: Dict[str, Any]) -> List[Path]:
        """生成文字掩码处理可视化结果"""
        
        if not self.is_enabled():
            return []
        
        self.logger.debug(f"开始生成步骤 {self.step_number} 可视化结果...")
        generated_files = []
        
        try:
            original_image = processing_data['original_image']
            masks = processing_data['masks']
            effect_images = processing_data['effect_images']
            text_removed_image = processing_data['text_removed_image']
            statistics = processing_data['statistics']
            
            # 1. 掩码对比可视化
            mask_comparison_path = self._create_mask_comparison_visualization(
                original_image, masks, text_removed_image
            )
            if mask_comparison_path:
                generated_files.append(mask_comparison_path)
            
            # 2. 效果对比可视化
            effect_comparison_path = self._create_effect_comparison_visualization(
                original_image, effect_images
            )
            if effect_comparison_path:
                generated_files.append(effect_comparison_path)
            
            # 3. 处理流程可视化
            process_flow_path = self._create_process_flow_visualization(
                original_image, masks, effect_images, text_removed_image
            )
            if process_flow_path:
                generated_files.append(process_flow_path)
            
            # 4. 统计信息图表
            statistics_chart_path = self._create_statistics_visualization(statistics)
            if statistics_chart_path:
                generated_files.append(statistics_chart_path)
            
            # 5. 掩码覆盖分析图
            coverage_analysis_path = self._create_coverage_analysis_visualization(
                masks, statistics
            )
            if coverage_analysis_path:
                generated_files.append(coverage_analysis_path)
            
            self.logger.debug(f"步骤 {self.step_number} 可视化完成，生成 {len(generated_files)} 个文件")
            
        except Exception as e:
            self.logger.error(f"可视化生成失败: {str(e)}")
        
        return generated_files
    
    def _create_mask_comparison_visualization(self, original_image: np.ndarray, 
                                           masks: Dict[str, np.ndarray],
                                           text_removed_image: np.ndarray) -> Optional[Path]:
        """创建掩码对比可视化"""
        try:
            # 准备图像数据
            images_data = [
                ("原始图像", original_image),
                ("文本掩码", cv2.cvtColor(masks['text_mask'], cv2.COLOR_GRAY2BGR)),
                ("背景掩码", cv2.cvtColor(masks['background_mask'], cv2.COLOR_GRAY2BGR)),
                ("文字移除", text_removed_image)
            ]
            
            # 如果有手写内容，也显示手写掩码
            if np.any(masks['handwriting_mask']):
                images_data.insert(3, ("手写掩码", cv2.cvtColor(masks['handwriting_mask'], cv2.COLOR_GRAY2BGR)))
            
            # 创建对比图像
            comparison_image = self._create_multi_image_comparison(images_data, max_cols=3)
            if comparison_image is None:
                return None
            
            output_path = self.save_visualization(comparison_image, "3.5_mask_comparison.png", "掩码对比")
            return output_path
            
        except Exception as e:
            self.logger.error(f"掩码对比可视化生成失败: {e}")
            return None
    
    def _create_effect_comparison_visualization(self, original_image: np.ndarray,
                                             effect_images: Dict[str, np.ndarray]) -> Optional[Path]:
        """创建效果对比可视化"""
        try:
            images_data = [("原始图像", original_image)]
            
            # 添加各种效果图像
            effect_map = {
                'highlighted': '文字高亮',
                'confidence_colored': '置信度可视化',
                'handwriting_highlighted': '手写高亮'
            }
            
            for effect_name, effect_title in effect_map.items():
                if effect_name in effect_images:
                    images_data.append((effect_title, effect_images[effect_name]))
            
            # 创建对比图像
            comparison_image = self._create_multi_image_comparison(images_data, max_cols=2)
            if comparison_image is None:
                return None
            
            output_path = self.save_visualization(comparison_image, "3.6_effect_comparison.png", "效果对比")
            return output_path
            
        except Exception as e:
            self.logger.error(f"效果对比可视化生成失败: {e}")
            return None
    
    def _create_process_flow_visualization(self, original_image: np.ndarray,
                                        masks: Dict[str, np.ndarray],
                                        effect_images: Dict[str, np.ndarray],
                                        text_removed_image: np.ndarray) -> Optional[Path]:
        """创建处理流程可视化"""
        try:
            # 创建处理流程：原图 → 文本掩码 → 高亮效果 → 文字移除
            flow_images = [
                ("1. 原始图像", original_image),
                ("2. 文本掩码", cv2.cvtColor(masks['text_mask'], cv2.COLOR_GRAY2BGR)),
                ("3. 文字高亮", effect_images.get('highlighted', original_image)),
                ("4. 文字移除", text_removed_image)
            ]
            
            # 创建流程图像 (横向排列)
            flow_image = self._create_multi_image_comparison(flow_images, max_cols=4)
            if flow_image is None:
                return None
            
            output_path = self.save_visualization(flow_image, "3.7_process_flow.png", "处理流程")
            return output_path
            
        except Exception as e:
            self.logger.error(f"处理流程可视化生成失败: {e}")
            return None
    
    def _create_statistics_visualization(self, statistics: Dict[str, Any]) -> Optional[Path]:
        """创建统计信息可视化"""
        try:
            import matplotlib.pyplot as plt
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # 1. 文本块数量分布
            block_counts = statistics['block_counts']
            ax1.pie([block_counts['printed'], block_counts['handwritten']], 
                   labels=['打印文本', '手写文本'],
                   autopct='%1.1f%%',
                   colors=['lightblue', 'lightcoral'])
            ax1.set_title(f"文本类型分布 (总计: {block_counts['total']} 个)")
            
            # 2. 置信度统计
            conf_stats = statistics['confidence_stats']
            ax2.bar(['平均', '最小', '最大'], 
                   [conf_stats['avg'], conf_stats['min'], conf_stats['max']],
                   color=['green', 'orange', 'blue'])
            ax2.set_title("文本置信度统计")
            ax2.set_ylabel("置信度")
            ax2.set_ylim(0, 1)
            
            # 3. 掩码覆盖率
            coverage_stats = statistics['coverage_stats']
            mask_names = list(coverage_stats.keys())
            coverage_ratios = [coverage_stats[name]['coverage_ratio'] for name in mask_names]
            
            ax3.barh(mask_names, coverage_ratios, color='lightgreen')
            ax3.set_title("掩码覆盖率统计")
            ax3.set_xlabel("覆盖率 (%)")
            ax3.set_xlim(0, max(coverage_ratios) * 1.1 if coverage_ratios else 1)
            
            # 4. 像素数量对比
            pixel_counts = [coverage_stats[name]['non_zero_pixels'] for name in mask_names]
            ax4.bar(range(len(mask_names)), pixel_counts, color='skyblue')
            ax4.set_title("掩码像素数量")
            ax4.set_ylabel("像素数量")
            ax4.set_xticks(range(len(mask_names)))
            ax4.set_xticklabels([name.replace('_', '\n') for name in mask_names], rotation=0)
            
            plt.tight_layout()
            
            # 保存图表
            import io
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # 转为图像数组并保存
            import PIL.Image
            image_pil = PIL.Image.open(buffer)
            image_array = np.array(image_pil)
            
            output_path = self.save_visualization(image_array, "3.8_statistics_chart.png", "统计图表")
            plt.close()
            buffer.close()
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"统计图表生成失败: {e}")
            return None
    
    def _create_coverage_analysis_visualization(self, masks: Dict[str, np.ndarray],
                                              statistics: Dict[str, Any]) -> Optional[Path]:
        """创建掩码覆盖分析可视化"""
        try:
            # 创建掩码叠加分析图
            coverage_images = []
            
            # 为每个掩码创建彩色版本
            color_map = {
                'text_mask': [0, 255, 0],      # 绿色
                'handwriting_mask': [0, 0, 255], # 红色
                'background_mask': [255, 255, 255], # 白色
                'confidence_mask': None  # 特殊处理
            }
            
            for mask_name, mask in masks.items():
                if mask_name == 'confidence_mask':
                    # 置信度掩码使用热力图颜色
                    colored_mask = cv2.applyColorMap(mask, cv2.COLORMAP_JET)
                elif mask_name in color_map and color_map[mask_name]:
                    # 其他掩码使用固定颜色
                    colored_mask = np.zeros((*mask.shape, 3), dtype=np.uint8)
                    colored_mask[mask > 0] = color_map[mask_name]
                else:
                    # 默认灰度
                    colored_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                
                coverage_ratio = statistics['coverage_stats'][mask_name]['coverage_ratio']
                title = f"{mask_name.replace('_', ' ').title()}\n覆盖率: {coverage_ratio:.2%}"
                coverage_images.append((title, colored_mask))
            
            # 创建覆盖分析对比图
            analysis_image = self._create_multi_image_comparison(coverage_images, max_cols=2)
            if analysis_image is None:
                return None
            
            output_path = self.save_visualization(analysis_image, "3.9_coverage_analysis.png", "覆盖分析")
            return output_path
            
        except Exception as e:
            self.logger.error(f"覆盖分析可视化生成失败: {e}")
            return None
    
    def _create_multi_image_comparison(self, images_with_titles: List[Tuple[str, np.ndarray]], 
                                     max_cols: int = 3) -> Optional[np.ndarray]:
        """创建多图像对比可视化"""
        if not images_with_titles:
            return None
        
        try:
            num_images = len(images_with_titles)
            cols = min(max_cols, num_images)
            rows = (num_images + cols - 1) // cols
            
            # 统一图像尺寸
            target_height = 300
            processed_images = []
            
            for title, img in images_with_titles:
                # 确保图像为3通道
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif len(img.shape) == 3 and img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                
                # 调整尺寸
                h, w = img.shape[:2]
                if h > 0:
                    target_width = int(w * target_height / h)
                    resized = cv2.resize(img, (target_width, target_height))
                    
                    # 添加标题
                    title_height = 40
                    title_img = np.ones((title_height, target_width, 3), dtype=np.uint8) * 255
                    
                    # 处理多行标题
                    title_lines = title.split('\n')
                    line_height = title_height // len(title_lines)
                    for i, line in enumerate(title_lines):
                        y_pos = (i + 1) * line_height - 5
                        cv2.putText(title_img, line, (10, y_pos), 
                                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
                    
                    combined = np.vstack([title_img, resized])
                    processed_images.append(combined)
            
            if not processed_images:
                return None
            
            # 拼接图像
            result_rows = []
            for row in range(rows):
                row_images = []
                for col in range(cols):
                    idx = row * cols + col
                    if idx < len(processed_images):
                        row_images.append(processed_images[idx])
                    else:
                        # 填充空白
                        if processed_images:
                            blank = np.ones_like(processed_images[0]) * 255
                            row_images.append(blank)
                
                if row_images:
                    # 确保同一行的图像高度一致
                    max_height = max(img.shape[0] for img in row_images)
                    padded_images = []
                    for img in row_images:
                        if img.shape[0] < max_height:
                            padding = np.ones((max_height - img.shape[0], img.shape[1], 3), 
                                            dtype=np.uint8) * 255
                            img = np.vstack([img, padding])
                        padded_images.append(img)
                    
                    result_rows.append(np.hstack(padded_images))
            
            if result_rows:
                final_image = np.vstack(result_rows)
                return final_image
            
            return None
            
        except Exception as e:
            self.logger.error(f"多图像对比创建失败: {e}")
            return None


class TableLineVisualizer(BaseVisualizer):
    """表格边线识别可视化器"""
    
    def __init__(self, step_number: int, config: Any, file_manager: Any, logger: Any):
        super().__init__(step_number, config, file_manager, logger)
        self.config = config
    
    def visualize_results(self, image_path: str, result_files: Dict[str, str], 
                         processing_data: Dict[str, Any]) -> List[Path]:
        """生成表格边线识别可视化结果"""
        
        if not self.is_enabled():
            return []
        
        self.logger.debug(f"开始生成步骤 {self.step_number} 可视化结果...")
        generated_files = []
        
        try:
            original_image = processing_data['original_image']
            clean_image = processing_data['clean_image']
            edges = processing_data['edges']
            line_data = processing_data['line_data']
            grouped_lines = processing_data['grouped_lines']
            theoretical_line_data = processing_data['theoretical_line_data']
            table_analysis = processing_data['table_analysis']
            
            # 1. 原始LSM检测可视化
            raw_detection_path = self._create_raw_detection_visualization(
                original_image, line_data
            )
            if raw_detection_path:
                generated_files.append(raw_detection_path)
            
            # 2. KNN分组可视化
            if grouped_lines.get('horizontal_groups'):
                knn_grouping_path = self._create_knn_grouping_visualization(
                    original_image, grouped_lines
                )
                if knn_grouping_path:
                    generated_files.append(knn_grouping_path)
            
            # 3. 理论重建后的最终可视化
            final_lines_path = self._create_final_lines_visualization(
                original_image, theoretical_line_data
            )
            if final_lines_path:
                generated_files.append(final_lines_path)
            
            # 4. 处理流程对比可视化
            process_flow_path = self._create_process_flow_visualization(
                clean_image, edges, line_data, theoretical_line_data
            )
            if process_flow_path:
                generated_files.append(process_flow_path)
            
            # 5. 表格结构分析图
            analysis_chart_path = self._create_analysis_chart(table_analysis, line_data, theoretical_line_data)
            if analysis_chart_path:
                generated_files.append(analysis_chart_path)
            
            self.logger.debug(f"步骤 {self.step_number} 可视化完成，生成 {len(generated_files)} 个文件")
            
        except Exception as e:
            self.logger.error(f"可视化生成失败: {str(e)}")
        
        return generated_files
    
    def _create_raw_detection_visualization(self, original_image: np.ndarray, 
                                          line_data: Dict[str, List]) -> Optional[Path]:
        """创建原始LSM检测结果可视化"""
        try:
            # 创建白色背景图像
            vis_image = np.ones_like(original_image) * 255
            
            # 绘制水平线（红色）
            horizontal_count = 0
            for i, line in enumerate(line_data['horizontal_lines']):
                pt1 = tuple(line['endpoints'][0])
                pt2 = tuple(line['endpoints'][1])
                
                # 绘制线段
                cv2.line(vis_image, pt1, pt2, (0, 0, 255), 2)  # 红色
                
                # 绘制端点
                cv2.circle(vis_image, pt1, 4, (0, 255, 0), -1)  # 绿色起点
                cv2.circle(vis_image, pt2, 4, (0, 255, 255), -1)  # 黄色终点
                
                # 添加编号（每50条标记一次）
                if i % 50 == 0:
                    mid_x = (pt1[0] + pt2[0]) // 2
                    mid_y = (pt1[1] + pt2[1]) // 2
                    cv2.putText(vis_image, f"H{i+1}", (mid_x-15, mid_y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                horizontal_count += 1
            
            # 绘制垂直线（蓝色）
            vertical_count = 0
            for i, line in enumerate(line_data['vertical_lines']):
                pt1 = tuple(line['endpoints'][0])
                pt2 = tuple(line['endpoints'][1])
                
                # 绘制线段
                cv2.line(vis_image, pt1, pt2, (255, 0, 0), 2)  # 蓝色
                
                # 绘制端点（方形标记区分）
                cv2.rectangle(vis_image, (pt1[0]-3, pt1[1]-3), (pt1[0]+3, pt1[1]+3), (0, 255, 0), -1)
                cv2.rectangle(vis_image, (pt2[0]-3, pt2[1]-3), (pt2[0]+3, pt2[1]+3), (0, 255, 255), -1)
                
                # 添加编号（每50条标记一次）
                if i % 50 == 0:
                    mid_x = (pt1[0] + pt2[0]) // 2
                    mid_y = (pt1[1] + pt2[1]) // 2
                    cv2.putText(vis_image, f"V{i+1}", (mid_x-15, mid_y-10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
                vertical_count += 1
            
            # 添加统计信息
            font = cv2.FONT_HERSHEY_SIMPLEX
            y_offset = 30
            cv2.putText(vis_image, f"Raw LSM Detection Results", (10, y_offset), 
                       font, 0.8, (0, 0, 0), 2)
            y_offset += 30
            cv2.putText(vis_image, f"Horizontal: {horizontal_count} (Red)", (10, y_offset), 
                       font, 0.6, (0, 0, 255), 2)
            y_offset += 25
            cv2.putText(vis_image, f"Vertical: {vertical_count} (Blue)", (10, y_offset), 
                       font, 0.6, (255, 0, 0), 2)
            y_offset += 25
            cv2.putText(vis_image, f"Green/Yellow: Start/End points", (10, y_offset), 
                       font, 0.5, (0, 128, 0), 2)
            
            output_path = self.save_visualization(vis_image, "4.2_raw_lsd_detection.png", "原始LSM检测")
            return output_path
            
        except Exception as e:
            self.logger.error(f"原始检测可视化生成失败: {e}")
            return None
    
    def _create_knn_grouping_visualization(self, original_image: np.ndarray,
                                         grouped_lines: Dict[str, Any]) -> Optional[Path]:
        """创建KNN分组可视化"""
        try:
            vis_image = original_image.copy()
            overlay = vis_image.copy()
            
            # 生成彩色调色板
            horizontal_groups = grouped_lines['horizontal_groups']
            num_groups = len(horizontal_groups)
            colors = self._generate_distinct_colors(num_groups)
            
            # 绘制各组水平线（使用不同颜色）
            for i, (group_name, group_lines) in enumerate(horizontal_groups.items()):
                color = colors[i]
                bgr_color = (int(color[2]*255), int(color[1]*255), int(color[0]*255))  # RGB到BGR
                
                for line in group_lines:
                    pt1 = tuple(line['endpoints'][0])
                    pt2 = tuple(line['endpoints'][1])
                    cv2.line(overlay, pt1, pt2, bgr_color, 4)
                    
                    # 添加组标签
                    mid_x = (pt1[0] + pt2[0]) // 2
                    mid_y = (pt1[1] + pt2[1]) // 2
                    cv2.putText(overlay, group_name[-1], (mid_x-10, mid_y-15), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)
            
            # 绘制垂直线（灰色）
            vertical_lines = grouped_lines.get('vertical_lines', [])
            for line in vertical_lines:
                pt1 = tuple(line['endpoints'][0])
                pt2 = tuple(line['endpoints'][1])
                cv2.line(overlay, pt1, pt2, (128, 128, 128), 2)
            
            # 混合图像
            vis_image = cv2.addWeighted(vis_image, 0.3, overlay, 0.7, 0)
            
            # 添加说明文字
            font = cv2.FONT_HERSHEY_SIMPLEX
            y_offset = 30
            cv2.putText(vis_image, f"KNN Grouping Results", (10, y_offset), 
                       font, 0.8, (0, 0, 0), 2)
            y_offset += 30
            cv2.putText(vis_image, f"Groups: {num_groups}", (10, y_offset), 
                       font, 0.6, (0, 0, 255), 2)
            y_offset += 25
            cv2.putText(vis_image, f"Vertical lines: {len(vertical_lines)} (Gray)", (10, y_offset), 
                       font, 0.6, (128, 128, 128), 2)
            
            output_path = self.save_visualization(vis_image, "4.3_knn_grouping.png", "KNN分组")
            return output_path
            
        except Exception as e:
            self.logger.error(f"KNN分组可视化生成失败: {e}")
            return None
    
    def _create_final_lines_visualization(self, original_image: np.ndarray,
                                        theoretical_line_data: Dict[str, List]) -> Optional[Path]:
        """创建最终线条可视化"""
        try:
            vis_image = original_image.copy()
            overlay = vis_image.copy()
            
            # 绘制最终水平线（红色粗线）
            h_lines = theoretical_line_data['horizontal_lines']
            for line in h_lines:
                pt1 = tuple(line['endpoints'][0])
                pt2 = tuple(line['endpoints'][1])
                cv2.line(overlay, pt1, pt2, (0, 0, 255), 6)  # 红色粗线
                
                # 绘制端点
                cv2.circle(overlay, pt1, 6, (0, 255, 0), -1)  # 绿色起点
                cv2.circle(overlay, pt2, 6, (0, 255, 255), -1)  # 黄色终点
                cv2.circle(overlay, pt1, 8, (0, 0, 0), 2)  # 黑色边框
                cv2.circle(overlay, pt2, 8, (0, 0, 0), 2)
            
            # 绘制最终垂直线（蓝色中等线）
            v_lines = theoretical_line_data['vertical_lines']
            for line in v_lines:
                pt1 = tuple(line['endpoints'][0])
                pt2 = tuple(line['endpoints'][1])
                cv2.line(overlay, pt1, pt2, (255, 0, 0), 4)  # 蓝色中线
                
                # 绘制端点（方形标记）
                cv2.rectangle(overlay, (pt1[0]-4, pt1[1]-4), (pt1[0]+4, pt1[1]+4), (0, 255, 0), -1)
                cv2.rectangle(overlay, (pt2[0]-4, pt2[1]-4), (pt2[0]+4, pt2[1]+4), (0, 255, 255), -1)
                cv2.rectangle(overlay, (pt1[0]-5, pt1[1]-5), (pt1[0]+5, pt1[1]+5), (0, 0, 0), 2)
                cv2.rectangle(overlay, (pt2[0]-5, pt2[1]-5), (pt2[0]+5, pt2[1]+5), (0, 0, 0), 2)
            
            # 混合图像（更突出线条）
            vis_image = cv2.addWeighted(vis_image, 0.3, overlay, 0.7, 0)
            
            # 添加统计信息
            font = cv2.FONT_HERSHEY_SIMPLEX
            y_offset = 30
            cv2.putText(vis_image, f"Final Reconstructed Lines", (10, y_offset), 
                       font, 0.8, (0, 0, 0), 2)
            y_offset += 30
            cv2.putText(vis_image, f"Horizontal: {len(h_lines)} (Red thick)", (10, y_offset), 
                       font, 0.6, (0, 0, 255), 2)
            y_offset += 25
            cv2.putText(vis_image, f"Vertical: {len(v_lines)} (Blue medium)", (10, y_offset), 
                       font, 0.6, (255, 0, 0), 2)
            y_offset += 25
            cv2.putText(vis_image, f"Green/Yellow: Line endpoints", (10, y_offset), 
                       font, 0.5, (0, 128, 0), 2)
            
            output_path = self.save_visualization(vis_image, "4.4_final_lines.png", "最终线条")
            return output_path
            
        except Exception as e:
            self.logger.error(f"最终线条可视化生成失败: {e}")
            return None
    
    def _create_process_flow_visualization(self, clean_image: np.ndarray, edges: np.ndarray,
                                         line_data: Dict[str, List], 
                                         theoretical_line_data: Dict[str, List]) -> Optional[Path]:
        """创建处理流程对比可视化"""
        try:
            # 准备4个处理阶段的图像
            flow_images = []
            
            # 1. 清洁图像
            flow_images.append(("1. 清洁图像", clean_image))
            
            # 2. 边缘检测
            edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            flow_images.append(("2. 边缘检测", edges_bgr))
            
            # 3. 原始线条检测
            raw_lines_vis = np.ones_like(clean_image) * 255
            # 绘制原始检测的线条（简化版本）
            for line in line_data['horizontal_lines']:
                pt1, pt2 = tuple(line['endpoints'][0]), tuple(line['endpoints'][1])
                cv2.line(raw_lines_vis, pt1, pt2, (0, 0, 255), 1)
            for line in line_data['vertical_lines']:
                pt1, pt2 = tuple(line['endpoints'][0]), tuple(line['endpoints'][1])
                cv2.line(raw_lines_vis, pt1, pt2, (255, 0, 0), 1)
            flow_images.append(("3. 原始检测", raw_lines_vis))
            
            # 4. 最终结果
            final_vis = clean_image.copy()
            overlay = final_vis.copy()
            # 绘制最终线条
            for line in theoretical_line_data['horizontal_lines']:
                pt1, pt2 = tuple(line['endpoints'][0]), tuple(line['endpoints'][1])
                cv2.line(overlay, pt1, pt2, (0, 0, 255), 3)
            for line in theoretical_line_data['vertical_lines']:
                pt1, pt2 = tuple(line['endpoints'][0]), tuple(line['endpoints'][1])
                cv2.line(overlay, pt1, pt2, (255, 0, 0), 2)
            final_vis = cv2.addWeighted(final_vis, 0.5, overlay, 0.5, 0)
            flow_images.append(("4. 最终结果", final_vis))
            
            # 创建流程图像
            flow_image = self._create_multi_image_comparison(flow_images, max_cols=2)
            if flow_image is None:
                return None
            
            output_path = self.save_visualization(flow_image, "4.5_process_flow.png", "处理流程")
            return output_path
            
        except Exception as e:
            self.logger.error(f"处理流程可视化生成失败: {e}")
            return None
    
    def _create_analysis_chart(self, table_analysis: Dict[str, Any], 
                             line_data: Dict[str, List],
                             theoretical_line_data: Dict[str, List]) -> Optional[Path]:
        """创建表格结构分析图表"""
        try:
            import matplotlib.pyplot as plt
            
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'WenQuanYi Micro Hei']
            plt.rcParams['axes.unicode_minus'] = False
            
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # 1. 线条处理前后对比
            categories = ['水平线', '垂直线']
            original_counts = [len(line_data['horizontal_lines']), len(line_data['vertical_lines'])]
            final_counts = [len(theoretical_line_data['horizontal_lines']), len(theoretical_line_data['vertical_lines'])]
            
            x = np.arange(len(categories))
            width = 0.35
            
            ax1.bar(x - width/2, original_counts, width, label='原始检测', color='lightcoral')
            ax1.bar(x + width/2, final_counts, width, label='理论重建', color='skyblue')
            ax1.set_title('线条处理前后对比')
            ax1.set_ylabel('数量')
            ax1.set_xticks(x)
            ax1.set_xticklabels(categories)
            ax1.legend()
            
            # 2. 表格质量评估
            quality_data = {
                '总线条数': table_analysis['line_counts']['total'],
                '表格数量': table_analysis['table_count'],
                '网格单元': table_analysis['grid_cells']
            }
            
            ax2.pie(quality_data.values(), labels=quality_data.keys(), autopct='%1.0f', startangle=90)
            ax2.set_title('表格结构分析')
            
            # 3. 线条长度分布（如果有数据）
            if line_data['horizontal_lines']:
                h_lengths = [line['length'] for line in line_data['horizontal_lines']]
                ax3.hist(h_lengths, bins=20, alpha=0.7, color='red', label='水平线')
            if line_data['vertical_lines']:
                v_lengths = [line['length'] for line in line_data['vertical_lines']]
                ax3.hist(v_lengths, bins=20, alpha=0.7, color='blue', label='垂直线')
            ax3.set_title('线条长度分布')
            ax3.set_xlabel('长度')
            ax3.set_ylabel('频次')
            ax3.legend()
            
            # 4. 处理统计信息
            stats_labels = ['原始检测', '折痕过滤', '理论重建', '最终输出']
            stats_values = [
                len(line_data['all_lines']),
                len(line_data['horizontal_lines']) + len(line_data['vertical_lines']),
                len(theoretical_line_data['horizontal_lines']) + len(theoretical_line_data['vertical_lines']),
                table_analysis['line_counts']['total']
            ]
            
            ax4.bar(range(len(stats_labels)), stats_values, color=['orange', 'yellow', 'lightgreen', 'lightblue'])
            ax4.set_title('处理流程统计')
            ax4.set_ylabel('线条数量')
            ax4.set_xticks(range(len(stats_labels)))
            ax4.set_xticklabels(stats_labels, rotation=45)
            
            plt.tight_layout()
            
            # 保存图表
            import io
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # 转为图像数组并保存
            import PIL.Image
            image_pil = PIL.Image.open(buffer)
            image_array = np.array(image_pil)
            
            output_path = self.save_visualization(image_array, "4.6_analysis_chart.png", "分析图表")
            plt.close()
            buffer.close()
            
            return output_path
            
        except Exception as e:
            self.logger.error(f"分析图表生成失败: {e}")
            return None
    
    def _generate_distinct_colors(self, n_colors: int) -> List[Tuple[float, float, float]]:
        """生成n个不同的颜色"""
        import colorsys
        
        colors = []
        for i in range(n_colors):
            hue = i / n_colors
            saturation = 0.7 + (i % 3) * 0.1  # 在0.7-1.0之间变化
            value = 0.8 + (i % 2) * 0.2       # 在0.8-1.0之间变化
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            colors.append(rgb)
        
        return colors
    
    def _create_multi_image_comparison(self, images_with_titles: List[Tuple[str, np.ndarray]], 
                                     max_cols: int = 2) -> Optional[np.ndarray]:
        """创建多图像对比可视化"""
        if not images_with_titles:
            return None
        
        try:
            num_images = len(images_with_titles)
            cols = min(max_cols, num_images)
            rows = (num_images + cols - 1) // cols
            
            # 统一图像尺寸
            target_height = 300
            processed_images = []
            
            for title, img in images_with_titles:
                # 确保图像为3通道
                if len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                elif len(img.shape) == 3 and img.shape[2] == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
                
                # 调整尺寸
                h, w = img.shape[:2]
                if h > 0:
                    target_width = int(w * target_height / h)
                    resized = cv2.resize(img, (target_width, target_height))
                    
                    # 添加标题
                    title_height = 40
                    title_img = np.ones((title_height, target_width, 3), dtype=np.uint8) * 255
                    cv2.putText(title_img, title, (10, 30), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2, cv2.LINE_AA)
                    
                    combined = np.vstack([title_img, resized])
                    processed_images.append(combined)
            
            if not processed_images:
                return None
            
            # 拼接图像
            result_rows = []
            for row in range(rows):
                row_images = []
                for col in range(cols):
                    idx = row * cols + col
                    if idx < len(processed_images):
                        row_images.append(processed_images[idx])
                    else:
                        # 填充空白
                        if processed_images:
                            blank = np.ones_like(processed_images[0]) * 255
                            row_images.append(blank)
                
                if row_images:
                    # 确保同一行的图像高度一致
                    max_height = max(img.shape[0] for img in row_images)
                    padded_images = []
                    for img in row_images:
                        if img.shape[0] < max_height:
                            padding = np.ones((max_height - img.shape[0], img.shape[1], 3), 
                                            dtype=np.uint8) * 255
                            img = np.vstack([img, padding])
                        padded_images.append(img)
                    
                    result_rows.append(np.hstack(padded_images))
            
            if result_rows:
                final_image = np.vstack(result_rows)
                return final_image
            
            return None
            
        except Exception as e:
            self.logger.error(f"多图像对比创建失败: {e}")
            return None


class TextAggregationVisualizer(BaseVisualizer):
    """文本聚合步骤可视化器 - 完全复制原版本可视化算法"""
    
    def visualize_results(self, image_path: str, text_blocks: List[Any], 
                         merged_groups: List[List[int]], line_data: Dict, 
                         content_blocks: List[Dict]) -> Dict[str, Path]:
        """可视化文本聚合结果"""
        saved_files = {}
        
        # 1. 生成主聚合可视化
        aggregation_path = self._create_text_aggregation_visualization(
            image_path, text_blocks, merged_groups, line_data
        )
        saved_files['aggregation'] = aggregation_path
        
        # 2. 生成合并统计图
        stats_path = self._create_aggregation_statistics(
            text_blocks, content_blocks
        )
        saved_files['statistics'] = stats_path
        
        # 3. 生成处理流程图
        process_path = self._create_process_flow(
            len(text_blocks), merged_groups, content_blocks
        )
        saved_files['process_flow'] = process_path
        
        self.log_visualization_summary(saved_files)
        return saved_files
    
    def _create_text_aggregation_visualization(self, image_path: str, text_blocks: List[Any],
                                             merged_groups: List[List[int]], line_data: Dict) -> Path:
        """增强的文本聚合结果可视化（突出显示合并内容块）- 完全复制原版本"""
        self.logger.debug("🎨 生成增强的聚合可视化...")
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"无法加载图像: {image_path}")
        
        height, width = image.shape[:2]
        self.logger.debug(f"  📐 图像尺寸: {width} x {height}")
        
        # 创建图层
        vis_image = image.copy()
        
        # 生成不同颜色用于区分合并组
        merge_colors = self._generate_merge_colors(len(merged_groups))
        
        # === 第1步：绘制所有单独文本块（灰色） ===
        processed_indices = set()
        for group in merged_groups:
            processed_indices.update(group)
        
        # 绘制未合并的单独文本块
        for i, block in enumerate(text_blocks):
            if i not in processed_indices:
                poly_np = np.array(block.poly, dtype=np.int32).reshape((-1, 1, 2))
                color = (128, 128, 128)  # 灰色表示单独块
                cv2.polylines(vis_image, [poly_np], True, color, 2)
        
        # === 第2步：绘制合并组（彩色突出显示） ===
        merge_info = []
        
        for group_idx, group in enumerate(merged_groups):
            if len(group) <= 1:  # 跳过单元素组
                continue
                
            color = merge_colors[group_idx % len(merge_colors)]
            group_blocks = [text_blocks[i] for i in group]
            
            # 绘制组内所有文本块
            for i in group:
                poly_np = np.array(text_blocks[i].poly, dtype=np.int32).reshape((-1, 1, 2))
                cv2.polylines(vis_image, [poly_np], True, color, 3)  # 粗线突出显示
            
            # 计算组的边界框
            all_points = []
            for i in group:
                all_points.extend(text_blocks[i].poly)
            
            if all_points:
                all_points_np = np.array(all_points)
                x_coords = all_points_np[:, 0]
                y_coords = all_points_np[:, 1]
                min_x, max_x = int(min(x_coords)), int(max(x_coords))
                min_y, max_y = int(min(y_coords)), int(max(y_coords))
                
                # 绘制组边界框
                cv2.rectangle(vis_image, (min_x-10, min_y-10), (max_x+10, max_y+10), color, 2)
                
                # 添加组标签
                label = f"M{group_idx+1}({len(group)})"
                label_pos = (min_x-10, min_y-25)
                cv2.putText(vis_image, label, label_pos, cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, color, 2, cv2.LINE_AA)
                
                # 绘制连线连接组内文本块
                if len(group) > 1:
                    centers = []
                    for i in group:
                        centers.append((int(text_blocks[i].center_x), int(text_blocks[i].center_y)))
                    
                    # 连接所有中心点
                    for j in range(len(centers) - 1):
                        cv2.line(vis_image, centers[j], centers[j+1], color, 2)
                
                # 记录合并信息
                group_texts = [text_blocks[i].text for i in group]
                merge_info.append({
                    'group_id': group_idx + 1,
                    'texts': group_texts,
                    'combined_text': ''.join([t.strip() for t in group_texts]),
                    'count': len(group),
                    'bbox': [min_x, min_y, max_x, max_y]
                })
        
        # === 第3步：添加图例 ===
        legend_y = 50
        cv2.putText(vis_image, "Text Aggregation Results:", (20, legend_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2, cv2.LINE_AA)
        
        legend_y += 30
        cv2.putText(vis_image, f"Gray: Single blocks ({len(text_blocks) - len(processed_indices)})", 
                   (20, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (128, 128, 128), 2, cv2.LINE_AA)
        
        legend_y += 25
        cv2.putText(vis_image, f"Colored: Merged groups ({len([g for g in merged_groups if len(g) > 1])})", 
                   (20, legend_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 150, 0), 2, cv2.LINE_AA)
        
        # === 第4步：保存可视化结果 ===
        vis_path = self.save_visualization(vis_image, "5.1_text_aggregation.png")
        
        # === 第5步：保存详细的合并信息 ===
        merge_details = {
            'total_groups': len(merged_groups),
            'merged_groups': len([g for g in merged_groups if len(g) > 1]),
            'single_blocks': len(text_blocks) - len(processed_indices),
            'merge_info': merge_info
        }
        
        # 输出合并详情到日志
        self.logger.info("🔗 文本合并详情:")
        for info in merge_info:
            self.logger.info(f"  • 组M{info['group_id']}: \"{info['combined_text'][:50]}...\" ({info['count']}个块)")
        
        return vis_path
    
    def _create_aggregation_statistics(self, text_blocks: List[Any], 
                                     content_blocks: List[Dict]) -> Path:
        """创建聚合统计图表"""
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
        fig.suptitle('文本聚合统计分析', fontsize=16, fontweight='bold')
        
        # 1. 合并统计饼图
        merged_count = len([b for b in content_blocks if b['type'] == 'merged'])
        single_count = len([b for b in content_blocks if b['type'] == 'single'])
        
        ax1.pie([merged_count, single_count], 
               labels=['合并块', '单独块'],
               colors=['#ff9999', '#66b3ff'],
               autopct='%1.1f%%',
               startangle=90)
        ax1.set_title('内容块类型分布')
        
        # 2. 手写vs打印统计
        handwritten_count = len([b for b in content_blocks if b['is_handwritten']])
        printed_count = len(content_blocks) - handwritten_count
        
        ax2.bar(['手写', '打印'], [handwritten_count, printed_count],
               color=['#ffcc99', '#99ffcc'])
        ax2.set_title('文本类型分布')
        ax2.set_ylabel('数量')
        
        # 3. 置信度分布
        confidences = [b['confidence'] for b in content_blocks]
        ax3.hist(confidences, bins=20, alpha=0.7, color='lightblue', edgecolor='black')
        ax3.set_title('置信度分布')
        ax3.set_xlabel('置信度')
        ax3.set_ylabel('数量')
        
        # 4. 合并效率统计
        original_blocks = len(text_blocks)
        final_blocks = len(content_blocks)
        reduction_rate = ((original_blocks - final_blocks) / original_blocks) * 100 if original_blocks > 0 else 0
        
        ax4.bar(['原始文本块', '最终内容块'], [original_blocks, final_blocks],
               color=['#ff6666', '#66ff66'])
        ax4.set_title(f'合并效率 ({reduction_rate:.1f}% 减少)')
        ax4.set_ylabel('数量')
        
        # 添加数值标签
        for i, v in enumerate([original_blocks, final_blocks]):
            ax4.text(i, v + 0.5, str(v), ha='center', va='bottom')
        
        plt.tight_layout()
        
        # 保存图表
        stats_path = self.save_visualization(fig, "5.2_aggregation_statistics.png")
        plt.close(fig)
        
        return stats_path
    
    def _create_process_flow(self, total_blocks: int, merged_groups: List[List[int]], 
                           content_blocks: List[Dict]) -> Path:
        """创建处理流程图"""
        import matplotlib.pyplot as plt
        from matplotlib.patches import Rectangle, FancyBboxPatch
        import matplotlib.patches as mpatches
        
        fig, ax = plt.subplots(figsize=(14, 8))
        ax.set_xlim(0, 10)
        ax.set_ylim(0, 6)
        ax.axis('off')
        
        # 标题
        ax.text(5, 5.5, '文本聚合处理流程', ha='center', va='center',
               fontsize=18, fontweight='bold')
        
        # 流程步骤
        steps = [
            {'x': 1, 'y': 4, 'width': 1.5, 'height': 0.8, 'text': f'输入文本块\n{total_blocks}个', 'color': '#ffcccc'},
            {'x': 3.5, 'y': 4, 'width': 1.5, 'height': 0.8, 'text': '智能合并算法\n(并查集)', 'color': '#ccffcc'},
            {'x': 6, 'y': 4, 'width': 1.5, 'height': 0.8, 'text': f'输出内容块\n{len(content_blocks)}个', 'color': '#ccccff'},
        ]
        
        # 绘制步骤框
        for step in steps:
            box = FancyBboxPatch(
                (step['x'] - step['width']/2, step['y'] - step['height']/2),
                step['width'], step['height'],
                boxstyle="round,pad=0.1",
                facecolor=step['color'],
                edgecolor='black',
                linewidth=2
            )
            ax.add_patch(box)
            ax.text(step['x'], step['y'], step['text'], ha='center', va='center',
                   fontsize=10, fontweight='bold')
        
        # 绘制箭头
        arrow_props = dict(arrowstyle='->', lw=2, color='black')
        ax.annotate('', xy=(3, 4), xytext=(2.25, 4), arrowprops=arrow_props)
        ax.annotate('', xy=(5.25, 4), xytext=(4.25, 4), arrowprops=arrow_props)
        
        # 统计信息
        merged_groups_count = len([g for g in merged_groups if len(g) > 1])
        single_blocks_count = len(content_blocks) - merged_groups_count
        
        stats_text = f"""
处理统计:
• 合并组: {merged_groups_count} 个
• 单独块: {single_blocks_count} 个
• 总压缩率: {((total_blocks - len(content_blocks)) / total_blocks * 100):.1f}%
        """
        
        ax.text(1, 2.5, stats_text.strip(), ha='left', va='top',
               fontsize=11, bbox=dict(boxstyle="round,pad=0.5", facecolor='lightyellow'))
        
        # 合并策略说明
        strategy_text = """
合并策略:
• 语义延续检查
• 空间距离约束
• 边界线分割检测
• 手写/打印类型匹配
        """
        
        ax.text(8.5, 2.5, strategy_text.strip(), ha='left', va='top',
               fontsize=11, bbox=dict(boxstyle="round,pad=0.5", facecolor='lightcyan'))
        
        plt.tight_layout()
        
        # 保存流程图
        process_path = self.save_visualization(fig, "5.3_process_flow.png")
        plt.close(fig)
        
        return process_path
    
    def _generate_merge_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """生成用于区分合并组的颜色 - 完全复制原版本"""
        if num_colors == 0:
            return []
        
        import colorsys
        colors = []
        for i in range(num_colors):
            # 生成HSV颜色，然后转换为BGR
            hue = i / num_colors
            saturation = 0.8
            value = 0.9
            
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            # OpenCV使用BGR格式
            bgr = (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
            colors.append(bgr)
        
        return colors


class FieldExtractionVisualizer(BaseVisualizer):
    """字段提取可视化器"""

    def __init__(self, step_number: int, config, file_manager, logger):
        super().__init__(step_number, config, file_manager, logger)

    def visualize_results(self, image_path: str, result_files: Dict[str, str], 
                         processing_data: Dict[str, Any]) -> Dict[str, str]:
        """生成字段提取可视化"""
        if not self.is_enabled():
            return {}

        visualization_files = {}

        # 主要可视化：字段提取总览
        extraction_vis = self._create_field_extraction_visualization(
            image_path, processing_data
        )
        if extraction_vis:
            visualization_files['field_extraction_visualization'] = extraction_vis

        # 网格分析可视化
        grid_vis = self._create_grid_analysis_visualization(
            image_path, processing_data
        )
        if grid_vis:
            visualization_files['grid_analysis'] = grid_vis
        
        # 单元格标注可视化
        if self.should_save_intermediate():
            cell_annotation_vis = self._create_cell_annotation_visualization(
                image_path, processing_data
            )
            if cell_annotation_vis:
                visualization_files['cell_annotations'] = cell_annotation_vis
        
        # 有效垂直线分析可视化
        if self.should_save_intermediate():
            vertical_analysis_vis = self._create_effective_vertical_analysis(
                image_path, processing_data
            )
            if vertical_analysis_vis:
                visualization_files['vertical_analysis'] = vertical_analysis_vis

        # 内容匹配可视化
        match_vis = self._create_content_matching_visualization(
            image_path, processing_data
        )
        if match_vis:
            visualization_files['content_matching'] = match_vis

        # 统计图表
        if self.should_save_intermediate():
            stats_chart = self._create_extraction_statistics_chart(processing_data)
            if stats_chart:
                visualization_files['statistics_chart'] = stats_chart

        return visualization_files

    def _create_field_extraction_visualization(self, image_path: str, 
                                             processing_data: Dict[str, Any]) -> Optional[str]:
        """创建字段提取主要可视化"""
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return None

            vis_image = image.copy()
            
            # 绘制网格
            grid_analysis = processing_data.get('grid_analysis', {})
            cells = grid_analysis.get('cells', [])
            
            # 绘制单元格边界
            for cell in cells:
                bbox = cell.get('bbox', {})
                x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
                cv2.rectangle(vis_image, (int(x1), int(y1)), (int(x2), int(y2)), (200, 200, 200), 1)

            # 绘制提取的字段
            extracted_fields = processing_data.get('extracted_fields', {})
            colors = self._generate_field_colors(len(extracted_fields))
            
            color_idx = 0
            for field_name, field_data in extracted_fields.items():
                if isinstance(field_data, dict) and 'bbox' in field_data:
                    bbox = field_data['bbox']
                    color = colors[color_idx % len(colors)]
                    
                    # 绘制字段边界框
                    x1, y1 = int(bbox.get('x1', 0)), int(bbox.get('y1', 0))
                    x2, y2 = int(bbox.get('x2', 0)), int(bbox.get('y2', 0))
                    cv2.rectangle(vis_image, (x1, y1), (x2, y2), color, 2)
                    
                    # 添加字段名称标签
                    label_y = y1 - 10 if y1 > 20 else y2 + 20
                    cv2.putText(vis_image, field_name, (x1, label_y),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
                    color_idx += 1

            return self.save_visualization(vis_image, "6.1_field_extraction_visualization.png",
                                         "字段提取总览可视化")

        except Exception as e:
            self.logger.debug(f"创建字段提取可视化失败: {e}")
            return None

    def _create_grid_analysis_visualization(self, image_path: str, 
                                          processing_data: Dict[str, Any]) -> Optional[str]:
        """创建增强的网格分析可视化 - 复制smart_grid_analysis的丰富可视化"""
        try:
            import cv2
            import numpy as np
            image = cv2.imread(image_path)
            if image is None:
                return None

            grid_analysis = processing_data.get('grid_analysis', {})
            
            # 1. 创建行-列结构可视化
            vis_image = image.copy()
            
            # 获取行信息和单元格
            rows_info = grid_analysis.get('rows_analysis', [])
            cells = grid_analysis.get('cells', [])
            
            # 绘制所有水平线（红色）
            for row in rows_info:
                y_top = int(row.get('top_y', 0))
                y_bottom = int(row.get('bottom_y', 0))
                cv2.line(vis_image, (0, y_top), (vis_image.shape[1], y_top), (0, 0, 255), 2)
                cv2.line(vis_image, (0, y_bottom), (vis_image.shape[1], y_bottom), (0, 0, 255), 2)
            
            # 为每行绘制有效垂直线（不同颜色）
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
            
            for row in rows_info:
                row_id = row.get('row_id', 0)
                color = colors[row_id % len(colors)]
                
                effective_verticals = row.get('effective_verticals', [])
                for v_info in effective_verticals:
                    line = v_info.get('line', {})
                    endpoints = line.get('endpoints', [[0, 0], [0, 0]])
                    pt1 = tuple(map(int, endpoints[0]))
                    pt2 = tuple(map(int, endpoints[1]))
                    cv2.line(vis_image, pt1, pt2, color, 3)
            
            # 添加增强的标题和统计信息
            title = f"Smart Grid Analysis: {len(rows_info)} rows, {len(cells)} cells"
            cv2.putText(vis_image, title, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
            cv2.putText(vis_image, title, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 2)
            
            # 添加行统计信息
            for i, row in enumerate(rows_info[:10]):  # 只显示前10行
                y_pos = int(row.get('center_y', 0))
                cols_count = len(row.get('columns', []))
                stats_text = f"R{i}: {cols_count}cols"
                cv2.putText(vis_image, stats_text, (10, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

            return self.save_visualization(vis_image, "6.2_grid_analysis.png",
                                         "增强网格分析可视化")

        except Exception as e:
            self.logger.debug(f"创建网格分析可视化失败: {e}")
            return None
    
    def _create_cell_annotation_visualization(self, image_path: str, 
                                            processing_data: Dict[str, Any]) -> Optional[str]:
        """创建单元格标注可视化 - 复制smart_grid_analysis的单元格标注功能"""
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return None

            vis_image = image.copy()
            grid_analysis = processing_data.get('grid_analysis', {})
            cells = grid_analysis.get('cells', [])
            
            # 绘制每个单元格的边界框和坐标
            for cell in cells:
                bbox = cell.get('bbox', {})
                left = bbox.get('left', 0)
                top = bbox.get('top', 0) 
                right = bbox.get('right', 0)
                bottom = bbox.get('bottom', 0)
                width = bbox.get('width', 0)
                height = bbox.get('height', 0)
                
                center = cell.get('center', {})
                center_x = center.get('x', 0)
                center_y = center.get('y', 0)
                
                # 绘制单元格边界（绿色）
                cv2.rectangle(vis_image, (int(left), int(top)), (int(right), int(bottom)), (0, 255, 0), 2)
                
                # 绘制中心点
                cv2.circle(vis_image, (int(center_x), int(center_y)), 3, (0, 255, 255), -1)
                
                # 标注坐标（如果单元格足够大）
                if width > 60 and height > 30:
                    coord_text = cell.get('coordinates', '')
                    font_scale = min(width / 200, height / 100, 1.0)
                    
                    text_size = cv2.getTextSize(coord_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
                    text_x = int(center_x - text_size[0] // 2)
                    text_y = int(center_y + text_size[1] // 2)
                    
                    # 白色背景
                    padding = 3
                    cv2.rectangle(vis_image,
                                 (text_x - padding, text_y - text_size[1] - padding),
                                 (text_x + text_size[0] + padding, text_y + padding),
                                 (255, 255, 255), -1)
                    
                    # 黑色文字
                    cv2.putText(vis_image, coord_text, (text_x, text_y),
                               cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 1)
            
            return self.save_visualization(vis_image, "6.3_cell_annotations.png",
                                         "单元格标注可视化")

        except Exception as e:
            self.logger.debug(f"创建单元格标注可视化失败: {e}")
            return None
    
    def _create_effective_vertical_analysis(self, image_path: str, 
                                          processing_data: Dict[str, Any]) -> Optional[str]:
        """创建有效垂直线分析可视化 - 复制smart_grid_analysis的垂直线分析功能"""
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return None

            vis_image = image.copy()
            grid_analysis = processing_data.get('grid_analysis', {})
            rows_info = grid_analysis.get('rows_analysis', [])
            
            # 绘制行边界（淡红色）
            for i, row in enumerate(rows_info):
                y_top = int(row.get('top_y', 0))
                y_bottom = int(row.get('bottom_y', 0))
                cv2.line(vis_image, (0, y_top), (vis_image.shape[1], y_top), (0, 100, 255), 1)
                
                # 标注行号
                cv2.putText(vis_image, f"Row{i}", (10, y_top + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 100, 255), 2)
            
            # 收集所有有效垂直线的X位置
            all_effective_x = set()
            for row in rows_info:
                effective_verticals = row.get('effective_verticals', [])
                for v_info in effective_verticals:
                    x_pos = v_info.get('x_position', 0)
                    all_effective_x.add(x_pos)
            
            # 绘制有效垂直线（绿色粗线）和无效垂直线（灰色细线）
            # 注意：这里需要从原始线段数据获取所有垂直线
            line_data = processing_data.get('line_data', {})
            vertical_lines = line_data.get('vertical_lines', [])
            
            for v_line in vertical_lines:
                endpoints = v_line.get('endpoints', [[0, 0], [0, 0]])
                v_x1, v_x2 = endpoints[0][0], endpoints[1][0]
                avg_x = (v_x1 + v_x2) / 2
                
                pt1 = tuple(map(int, endpoints[0]))
                pt2 = tuple(map(int, endpoints[1]))
                
                if avg_x in all_effective_x:
                    cv2.line(vis_image, pt1, pt2, (0, 255, 0), 3)  # 绿色粗线：有效
                else:
                    cv2.line(vis_image, pt1, pt2, (128, 128, 128), 1)  # 灰色细线：无效
            
            # 添加图例
            legend_y = 80
            cv2.putText(vis_image, "Green: Effective verticals", (50, legend_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(vis_image, "Gray: Ineffective verticals", (50, legend_y + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (128, 128, 128), 2)
            
            # 从处理参数获取阈值
            threshold = processing_data.get('processing_params', {}).get('vertical_effectiveness_threshold', 0.5)
            cv2.putText(vis_image, f"Threshold: {threshold:.0%}", (50, legend_y + 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            return self.save_visualization(vis_image, "6.4_effective_vertical_analysis.png",
                                         "有效垂直线分析可视化")

        except Exception as e:
            self.logger.debug(f"创建有效垂直线分析可视化失败: {e}")
            return None

    def _create_content_matching_visualization(self, image_path: str, 
                                             processing_data: Dict[str, Any]) -> Optional[str]:
        """创建增强的内容匹配可视化 - 复制content_cell_matcher的丰富可视化"""
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return None

            vis_image = image.copy()
            content_match = processing_data.get('content_match', {})
            grid_analysis = processing_data.get('grid_analysis', {})
            content_blocks = processing_data.get('content_blocks', [])
            
            # 1. 绘制所有单元格边界（淡蓝色）
            all_cells = grid_analysis.get('cells', [])
            for cell in all_cells:
                bbox = cell.get('bbox', {})
                # 处理不同的bbox格式
                if 'left' in bbox:
                    x1, y1, x2, y2 = bbox['left'], bbox['top'], bbox['right'], bbox['bottom']
                else:
                    x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
                
                cv2.rectangle(vis_image, (int(x1), int(y1)), (int(x2), int(y2)), (255, 200, 100), 1)
            
            # 2. 绘制有内容的单元格（绿色粗边框）
            matched_cells = content_match.get('matched_cells', [])
            for cell in matched_cells:
                if cell.get('content', {}).get('has_content', False):
                    bbox = cell.get('bbox', {})
                    # 处理不同的bbox格式
                    if 'left' in bbox:
                        x1, y1, x2, y2 = bbox['left'], bbox['top'], bbox['right'], bbox['bottom']
                    else:
                        x1, y1, x2, y2 = bbox.get('x1', 0), bbox.get('y1', 0), bbox.get('x2', 0), bbox.get('y2', 0)
                    
                    cv2.rectangle(vis_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 3)
            
            # 3. 绘制内容块位置（红色边框和中心点）
            for content_block in content_blocks:
                bbox = content_block.get('bbox', {})
                center_x = content_block.get('center_x', 0)
                center_y = content_block.get('center_y', 0)
                center = (int(center_x), int(center_y))
                
                # 绘制内容边界框（红色）
                min_x = bbox.get('min_x', 0)
                max_x = bbox.get('max_x', 0)
                min_y = bbox.get('min_y', 0)
                max_y = bbox.get('max_y', 0)
                
                cv2.rectangle(vis_image, (int(min_x), int(min_y)), (int(max_x), int(max_y)), (0, 0, 255), 1)
                
                # 绘制中心点
                cv2.circle(vis_image, center, 3, (0, 0, 255), -1)
            
            # 4. 添加图例和统计信息
            match_statistics = content_match.get('match_statistics', {})
            legend_texts = [
                f"Total cells: {match_statistics.get('total_cells', 0)}",
                f"Cells with content: {match_statistics.get('cells_with_content', 0)}",
                f"Content blocks: {match_statistics.get('total_content_blocks', 0)}",
                f"Matched blocks: {match_statistics.get('matched_content_blocks', 0)}",
                f"Empty cells: {match_statistics.get('empty_cells', 0)}"
            ]
            
            for i, text in enumerate(legend_texts):
                y_pos = 30 + i * 25
                # 白色背景文字
                cv2.putText(vis_image, text, (20, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                # 黑色前景文字
                cv2.putText(vis_image, text, (20, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
            
            # 5. 添加颜色图例
            legend_y_start = 200
            legend_items = [
                ("Light Blue: All cells", (255, 200, 100)),
                ("Green: Cells with content", (0, 255, 0)),
                ("Red: Content blocks", (0, 0, 255))
            ]
            
            for i, (text, color) in enumerate(legend_items):
                y_pos = legend_y_start + i * 25
                # 绘制颜色块
                cv2.rectangle(vis_image, (20, y_pos - 15), (40, y_pos - 5), color, -1)
                # 绘制文字
                cv2.putText(vis_image, text, (50, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                cv2.putText(vis_image, text, (50, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

            return self.save_visualization(vis_image, "6.3_content_matching.png",
                                         "增强内容匹配可视化")

        except Exception as e:
            self.logger.debug(f"创建内容匹配可视化失败: {e}")
            return None

    def _create_extraction_statistics_chart(self, processing_data: Dict[str, Any]) -> Optional[str]:
        """创建提取统计图表"""
        try:
            import matplotlib.pyplot as plt
            import numpy as np

            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
            
            # 1. 字段类型分布
            extracted_fields = processing_data.get('extracted_fields', {})
            field_types = {}
            for field_data in extracted_fields.values():
                if isinstance(field_data, dict):
                    field_type = field_data.get('type', 'unknown')
                    field_types[field_type] = field_types.get(field_type, 0) + 1
                elif isinstance(field_data, list):
                    field_types['table_data'] = field_types.get('table_data', 0) + 1

            if field_types:
                ax1.pie(field_types.values(), labels=field_types.keys(), autopct='%1.1f%%')
                ax1.set_title('字段类型分布')

            # 2. 网格统计
            grid_analysis = processing_data.get('grid_analysis', {})
            total_cells = len(grid_analysis.get('cells', []))
            content_match = processing_data.get('content_match', {})
            matched_cells = len([c for c in content_match.get('matched_cells', []) if c.get('content_blocks')])
            empty_cells = total_cells - matched_cells

            ax2.bar(['总单元格', '含内容', '空单元格'], [total_cells, matched_cells, empty_cells])
            ax2.set_title('单元格统计')
            ax2.set_ylabel('数量')

            # 3. 提取成功率
            total_expected_fields = 20  # 预期字段数量
            extracted_count = len(extracted_fields)
            success_rate = (extracted_count / total_expected_fields) * 100 if total_expected_fields > 0 else 0

            ax3.bar(['提取字段', '未提取'], [extracted_count, total_expected_fields - extracted_count])
            ax3.set_title(f'字段提取成功率: {success_rate:.1f}%')
            ax3.set_ylabel('字段数量')

            # 4. 内容块处理状态
            content_blocks = processing_data.get('content_blocks', [])
            total_blocks = len(content_blocks)
            matched_blocks = sum(len(cell.get('content_blocks', [])) for cell in content_match.get('matched_cells', []))
            unmatched_blocks = total_blocks - matched_blocks

            ax4.bar(['总内容块', '已匹配', '未匹配'], [total_blocks, matched_blocks, unmatched_blocks])
            ax4.set_title('内容块处理状态')
            ax4.set_ylabel('内容块数量')

            plt.tight_layout()
            
            # 保存图表
            stats_path = self.save_visualization(fig, "6.4_extraction_statistics.png")
            plt.close(fig)
            
            return stats_path

        except Exception as e:
            self.logger.debug(f"创建统计图表失败: {e}")
            return None

    def _generate_field_colors(self, num_colors: int) -> List[Tuple[int, int, int]]:
        """生成字段可视化颜色"""
        import colorsys
        colors = []
        for i in range(num_colors):
            hue = i / max(num_colors, 1)
            saturation = 0.7
            value = 0.9
            
            rgb = colorsys.hsv_to_rgb(hue, saturation, value)
            bgr = (int(rgb[2] * 255), int(rgb[1] * 255), int(rgb[0] * 255))
            colors.append(bgr)
        
        return colors if colors else [(0, 255, 0)]
