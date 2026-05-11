#!/usr/bin/env python3
"""
V3 Step1: 图像预处理 - 业务逻辑与可视化分离版本
"""

import cv2
import numpy as np
import pdf2image
import math
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

from utils.base_step import V3BaseStep
from visualization.step_visualizers import PreprocessingVisualizer

class PreprocessingStep(V3BaseStep):
    """V3图像预处理步骤 - 纯业务逻辑"""
    
    def __init__(self, config, file_manager, logger):
        super().__init__(1, "图像预处理", config, file_manager, logger)
        
        # 初始化可视化器（业务逻辑与可视化分离）
        self.visualizer = PreprocessingVisualizer(
            self.step_number, config.visualization, file_manager, logger
        )
        
        # 处理参数（可配置）
        self.processing_params = {
            'pdf_dpi': 300,
            'bilateral_d': 9,
            'bilateral_sigma_color': 75,
            'bilateral_sigma_space': 75,
            'clahe_clip_limit': 2.0,
            'clahe_tile_grid_size': (8, 8),
            'deskew_min_angle': 0.1,
            'hough_threshold': 100,
            'angle_filter_threshold': 15,
            'min_horizontal_lines': 0,
            
            # 分层校正配置
            'use_layered_deskewing': True,  # 是否使用分层校正
            'layered_method': 'stepwise',  # 分层方法：'stepwise', 'weighted', 'best_angle'
            'structure_weight': 0.6,       # 结构层权重（用于加权平均）
            'document_weight': 0.2,        # 文档层权重
            'content_weight': 0.2,         # 内容层权重
            'projection_angle_range': 3.0, # 投影分析的角度范围（±度数）
            'projection_angle_step': 0.2   # 投影分析的角度步长
        }
        
        # 更新用户配置的参数
        user_params = self.step_config.get('processing_params', {})
        self.processing_params.update(user_params)
    
    def execute(self, input_path: str) -> str:
        """执行图像预处理 - 纯业务逻辑"""
        
        # 存储中间数据用于可视化
        intermediate_data = {
            'processing_stages': {},
            'quality_stats': {},
            'deskew_info': {}
        }
        
        try:
            # 1. 加载图像（支持PDF和图像文件）
            self.progress("加载输入文件...")
            image_bgr = self._load_input_file(input_path)
            intermediate_data['processing_stages']['original'] = image_bgr.copy()
            
            # 2. 预处理流水线
            processed_image, processing_stats = self._execute_preprocessing_pipeline(
                image_bgr, intermediate_data
            )
            
            # 3. 保存最终结果
            final_path = self.save_result_image(processed_image, "1.7_final_preprocessed.png")
            
            # 4. 计算质量统计
            quality_stats = self._calculate_quality_metrics(
                image_bgr, processed_image, processing_stats
            )
            intermediate_data['quality_stats'] = quality_stats
            
            # 5. 可视化结果（业务逻辑与可视化分离）
            if self.visualizer.is_enabled():
                visualization_files = self.visualizer.visualize_results(
                    input_path, str(final_path), intermediate_data
                )
                self.visualizer.log_visualization_summary(visualization_files)
            
            # 6. 保存处理统计
            if self.should_save_debug():
                debug_data = {
                    'processing_params': self.processing_params,
                    'quality_stats': quality_stats,
                    'processing_stats': processing_stats,
                    'file_info': {
                        'input_file': input_path,
                        'output_file': str(final_path),
                        'image_shape': list(processed_image.shape)  # 转换为列表
                    }
                }
                
                # 清理所有numpy类型
                clean_debug_data = self._clean_numpy_types(debug_data)
                self.save_debug_data(clean_debug_data, "preprocessing_stats.json")
            
            # 7. 记录性能指标
            self.log_performance("图像尺寸", f"{processed_image.shape[1]}x{processed_image.shape[0]}")
            self.log_performance("处理阶段", len(intermediate_data['processing_stages']))
            
            self.success(f"预处理完成，输出: {final_path}")
            return str(final_path)
            
        except Exception as e:
            self.error(f"预处理执行失败: {e}")
            raise
    
    def _load_input_file(self, input_path: str) -> np.ndarray:
        """加载输入文件（支持PDF和图像文件）"""
        input_file = Path(input_path)
        file_extension = input_file.suffix.lower()
        
        try:
            if file_extension == '.pdf':
                # 处理PDF文件
                return self._convert_pdf_to_image(input_path)
            elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                # 处理图像文件
                return self._load_image_file(input_path)
            else:
                raise ValueError(f"不支持的文件格式: {file_extension}")
                
        except Exception as e:
            raise ValueError(f"文件加载失败: {e}")
    
    def _load_image_file(self, image_path: str) -> np.ndarray:
        """加载图像文件"""
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("图像文件读取失败")
            
            self.debug(f"图像加载成功，尺寸: {image.shape}")
            return image
            
        except Exception as e:
            raise ValueError(f"图像文件加载失败: {e}")
    
    def _convert_pdf_to_image(self, pdf_path: str) -> np.ndarray:
        """PDF转图像"""
        try:
            images = pdf2image.convert_from_path(
                pdf_path, 
                dpi=self.processing_params['pdf_dpi']
            )
            
            if not images:
                raise ValueError("PDF转换失败 - 无图像输出")
            
            # 转换第一页为BGR格式
            image = images[0]
            image_np = np.array(image)
            image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            self.debug(f"PDF转换成功，图像尺寸: {image_bgr.shape}")
            return image_bgr
            
        except Exception as e:
            raise ValueError(f"PDF转换失败: {e}")
    
    def _execute_preprocessing_pipeline(self, image_bgr: np.ndarray, 
                                     intermediate_data: Dict[str, Any]) -> Tuple[np.ndarray, Dict[str, Any]]:
        """执行预处理流水线"""
        
        processing_stats = {'pipeline_steps': []}
        current_image = image_bgr
        
        # 1. 灰度转换
        self.progress("转换为灰度图...")
        gray = cv2.cvtColor(current_image, cv2.COLOR_BGR2GRAY)
        intermediate_data['processing_stages']['grayscale'] = gray.copy()
        processing_stats['pipeline_steps'].append('grayscale_conversion')
        
        # 保存中间结果
        if self.should_save_intermediate():
            self.save_result_image(gray, "1.2_grayscale.png")
        
        # 2. 去噪处理
        self.progress("图像去噪...")
        denoised = self._apply_bilateral_filter(gray)
        intermediate_data['processing_stages']['denoised'] = denoised.copy()
        processing_stats['pipeline_steps'].append('noise_reduction')
        
        if self.should_save_intermediate():
            self.save_result_image(denoised, "1.3_denoised.png")
        
        # 3. 对比度增强
        self.progress("对比度增强...")
        enhanced = self._apply_clahe(denoised)
        intermediate_data['processing_stages']['enhanced'] = enhanced.copy()
        processing_stats['pipeline_steps'].append('contrast_enhancement')
        
        if self.should_save_intermediate():
            self.save_result_image(enhanced, "1.4_enhanced_contrast.png")
        
        # 4. 锐化处理
        self.progress("图像锐化...")
        sharpened = self._apply_sharpening(enhanced)
        intermediate_data['processing_stages']['sharpened'] = sharpened.copy()
        processing_stats['pipeline_steps'].append('sharpening')
        
        if self.should_save_intermediate():
            self.save_result_image(sharpened, "1.5_sharpened.png")
        
        # 5. 倾斜校正
        self.progress("页面倾斜校正...")
        deskewed, deskew_info = self._apply_deskewing(sharpened)
        intermediate_data['processing_stages']['deskewed'] = deskewed.copy()
        intermediate_data['deskew_info'] = deskew_info
        processing_stats['pipeline_steps'].append('deskewing')
        processing_stats['deskew_angle'] = deskew_info.get('angle', 0)
        
        if self.should_save_intermediate():
            self.save_result_image(deskewed, "1.6_deskewed.png")
        
        # 6. 转换回BGR格式用于后续处理
        final_preprocessed = cv2.cvtColor(deskewed, cv2.COLOR_GRAY2BGR)
        
        return final_preprocessed, processing_stats
    
    def _apply_bilateral_filter(self, image: np.ndarray) -> np.ndarray:
        """应用双边滤波去噪"""
        return cv2.bilateralFilter(
            image, 
            d=self.processing_params['bilateral_d'],
            sigmaColor=self.processing_params['bilateral_sigma_color'],
            sigmaSpace=self.processing_params['bilateral_sigma_space']
        )
    
    def _apply_clahe(self, image: np.ndarray) -> np.ndarray:
        """应用CLAHE对比度增强"""
        clahe = cv2.createCLAHE(
            clipLimit=self.processing_params['clahe_clip_limit'], 
            tileGridSize=self.processing_params['clahe_tile_grid_size']
        )
        return clahe.apply(image)
    
    def _apply_sharpening(self, image: np.ndarray) -> np.ndarray:
        """应用图像锐化"""
        kernel_sharpen = np.array([[-1, -1, -1],
                                  [-1,  9, -1],
                                  [-1, -1, -1]])
        return cv2.filter2D(image, -1, kernel_sharpen)
    
    def _apply_deskewing(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """应用倾斜校正 - 支持传统方法和分层校正"""
        
        # 检查是否使用分层校正
        if self.processing_params.get('use_layered_deskewing', False):
            return self._apply_layered_deskewing(image)
        else:
            return self._apply_traditional_deskewing(image)
    
    def _apply_traditional_deskewing(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """应用传统倾斜校正方法"""
        
        deskew_info = {
            'angle': 0.0,
            'total_lines': 0,
            'valid_angles': 0,
            'horizontal_angles': [],
            'correction_applied': False,
            'method': 'traditional'
        }
        
        try:
            # 边缘检测
            edges = cv2.Canny(image, 50, 150, apertureSize=3)
            
            # 霍夫直线检测
            lines = cv2.HoughLines(
                edges, 1, np.pi/180, 
                threshold=self.processing_params['hough_threshold']
            )
            
            if lines is None or len(lines) == 0:
                self.warning("未检测到线条，跳过倾斜校正")
                return image, deskew_info
            
            deskew_info['total_lines'] = len(lines)
            
            # 分析角度
            angles = self._analyze_line_angles(lines)
            deskew_info['all_angles'] = angles
            
            # 第1步：过滤异常角度（保留接近水平和垂直的线条）
            filtered_angles = self._filter_anomaly_angles(angles)
            deskew_info['filtered_angles'] = filtered_angles
            
            # 添加调试输出
            if self.is_debug_enabled():
                self.debug(f"检测到 {len(lines)} 条线段，有效角度 {len(filtered_angles)} 个")
            
            if len(filtered_angles) == 0:
                self.warning("无有效参考线条，跳过倾斜校正")
                return image, deskew_info
            
            # 第2步：过滤水平角度
            horizontal_angles = self._filter_horizontal_angles(filtered_angles)
            deskew_info['horizontal_angles'] = horizontal_angles
            deskew_info['valid_angles'] = len(horizontal_angles)
            
            if len(horizontal_angles) < self.processing_params['min_horizontal_lines']:
                self.warning(f"有效水平线过少 ({len(horizontal_angles)})，跳过倾斜校正")
                return image, deskew_info
            
            # 计算倾斜角度
            skew_angle = self._calculate_skew_angle(horizontal_angles)
            deskew_info['angle'] = skew_angle
            
            # 检查是否需要校正
            if abs(skew_angle) < self.processing_params['deskew_min_angle']:
                self.debug(f"倾斜角度过小 ({skew_angle:.3f}°)，无需校正")
                return image, deskew_info
            
            # 执行校正
            corrected_image = self._rotate_image(image, skew_angle, deskew_info)
            deskew_info['correction_applied'] = True
            
            self.debug(f"传统倾斜校正完成，角度: {skew_angle:.2f}°")
            
            # 可视化倾斜校正过程（如果启用调试）
            if self.visualizer.should_save_debug():
                self.visualizer.visualize_deskew_process(
                    image, corrected_image, skew_angle, deskew_info
                )
            
            return corrected_image, deskew_info
            
        except Exception as e:
            self.warning(f"传统倾斜校正失败: {e}")
            return image, deskew_info
    
    def _analyze_line_angles(self, lines: np.ndarray) -> list:
        """分析线条角度"""
        angles = []
        for rho, theta in lines[:, 0]:
            angle_deg = np.degrees(theta)
            # 归一化到[-90, 90]范围
            if angle_deg > 90:
                angle_deg = angle_deg - 180
            elif angle_deg < -90:
                angle_deg = angle_deg + 180
            angles.append(angle_deg)
        return angles
    
    def _filter_anomaly_angles(self, angles: list) -> list:
        """过滤异常角度（保留接近水平和垂直的线条）- 完全复制原版本逻辑"""
        threshold = self.processing_params['angle_filter_threshold']  # 15度
        filtered_angles = []
        for angle in angles:
            # 保留接近水平（0°±15°）和垂直（90°±15°）的线条
            if abs(angle) <= threshold or abs(abs(angle) - 90) <= threshold:
                filtered_angles.append(angle)
        return filtered_angles
    
    def _filter_horizontal_angles(self, angles: list) -> list:
        """过滤水平角度（从已过滤的异常角度中筛选）"""
        threshold = self.processing_params['angle_filter_threshold']
        return [angle for angle in angles if abs(angle) <= threshold]
    
    def _calculate_skew_angle(self, horizontal_angles: list) -> float:
        """计算倾斜角度 - 完全复制原版本逻辑"""
        # 改进的倾斜角度计算
        if len(horizontal_angles) >= 10:
            # 对于足够多的角度，使用统计方法去除异常值
            angles_array = np.array(horizontal_angles)
            # 去除离群值
            q75, q25 = np.percentile(angles_array, [75, 25])
            iqr = q75 - q25
            lower_bound = q25 - 1.5 * iqr
            upper_bound = q75 + 1.5 * iqr
            filtered_horizontal = angles_array[(angles_array >= lower_bound) & (angles_array <= upper_bound)]
            
            if len(filtered_horizontal) > 0:
                skew_angle = np.mean(filtered_horizontal)  # 使用均值而非中位数
            else:
                skew_angle = np.median(horizontal_angles)
        else:
            # 对于较少的角度，直接使用中位数
            skew_angle = np.median(horizontal_angles)
        
        # 添加调试信息（使用V3的日志系统）
        if self.is_debug_enabled():
            self.debug(f"水平线角度统计: 总数{len(horizontal_angles)}, 范围[{min(horizontal_angles):.3f}°, {max(horizontal_angles):.3f}°]")
            self.debug(f"计算倾斜角度: {skew_angle:.2f}°")
        
        return skew_angle
    
    def _rotate_image(self, image: np.ndarray, angle: float, deskew_info: dict) -> np.ndarray:
        """旋转图像 - 完全复制原版本逻辑"""
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        # 创建旋转矩阵 (修正旋转方向)
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 计算新的边界框大小
        cos_val = abs(rotation_matrix[0, 0])
        sin_val = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_val) + (width * cos_val))
        new_height = int((height * cos_val) + (width * sin_val))
        
        # 调整旋转矩阵的平移部分
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # 执行旋转校正（完全复制原版本的通道检查逻辑）
        if len(image.shape) == 3:
            deskewed = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                    flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        else:
            deskewed = cv2.warpAffine(image, rotation_matrix, (new_width, new_height),
                                    flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        # 添加调试输出（使用V3的日志系统）
        if self.is_debug_enabled():
            self.debug(f"校正完成，角度调整: {angle:.2f}°")
            self.debug(f"图像尺寸变化: {width}x{height} → {new_width}x{new_height}")
        
        # 保存尺寸信息到deskew_info
        deskew_info['original_size'] = (width, height)
        deskew_info['new_size'] = (new_width, new_height)
        
        return deskewed
    
    def _calculate_quality_metrics(self, original: np.ndarray, 
                                 processed: np.ndarray, 
                                 processing_stats: Dict[str, Any]) -> Dict[str, Any]:
        """计算图像质量指标"""
        
        quality_stats = {}
        
        try:
            # 转换为灰度进行比较
            if len(original.shape) == 3:
                orig_gray = cv2.cvtColor(original, cv2.COLOR_BGR2GRAY)
            else:
                orig_gray = original
                
            if len(processed.shape) == 3:
                proc_gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
            else:
                proc_gray = processed
            
            # 基本统计信息 - 确保JSON可序列化
            quality_stats['original'] = {
                'mean': float(np.mean(orig_gray)),
                'std': float(np.std(orig_gray)),
                'min': int(np.min(orig_gray)),
                'max': int(np.max(orig_gray))
            }
            
            quality_stats['processed'] = {
                'mean': float(np.mean(proc_gray)),
                'std': float(np.std(proc_gray)),
                'min': int(np.min(proc_gray)),
                'max': int(np.max(proc_gray))
            }
            
            # 对比度改善 - 确保是Python原生float
            orig_contrast = float(np.std(orig_gray))
            proc_contrast = float(np.std(proc_gray))
            quality_stats['contrast_improvement'] = float(proc_contrast / orig_contrast)
            
            # 处理统计 - 清理numpy数据类型
            quality_stats['processing_summary'] = self._clean_numpy_types(processing_stats)
            
        except Exception as e:
            self.debug(f"质量指标计算失败: {e}")
        
        return quality_stats
    
    def _clean_numpy_types(self, data: Any) -> Any:
        """清理numpy数据类型，确保JSON可序列化"""
        if isinstance(data, dict):
            return {key: self._clean_numpy_types(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._clean_numpy_types(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        elif isinstance(data, np.integer):
            return int(data)
        elif isinstance(data, np.floating):
            return float(data)
        elif isinstance(data, (np.float32, np.float64)):
            return float(data)
        else:
            return data
    
    # ================== 分层校正方法 ==================
    
    def _apply_layered_deskewing(self, image: np.ndarray) -> Tuple[np.ndarray, Dict[str, Any]]:
        """应用分层倾斜校正方法"""
        
        method = self.processing_params.get('layered_method', 'stepwise')
        
        # 检测各层倾斜角度
        self.debug(f"开始分层倾斜校正，方法: {method}")
        angles = self._detect_layered_angles(image)
        
        deskew_info = {
            'method': f'layered_{method}',
            'detected_angles': angles,
            'final_angle': 0.0,
            'correction_applied': False,
            'angle_selection_reason': ''
        }
        
        try:
            # 根据方法选择最终角度
            if method == 'stepwise':
                # 分步校正：先结构层，再内容层微调
                corrected_image, final_angle = self._apply_stepwise_correction(image, angles)
                deskew_info['angle_selection_reason'] = f"分步校正：结构层({angles['structure']:.3f}°) + 内容层调整"
                
            elif method == 'weighted':
                # 加权平均
                final_angle = self._calculate_weighted_angle(angles)
                corrected_image = self._rotate_image_precise(image, final_angle)
                deskew_info['angle_selection_reason'] = f"加权平均：结构({self.processing_params['structure_weight']}) + 文档({self.processing_params['document_weight']}) + 内容({self.processing_params['content_weight']})"
                
            elif method == 'best_angle':
                # 选择最佳单一角度（基于投影方差）
                corrected_image, final_angle, best_layer = self._select_best_angle(image, angles)
                deskew_info['angle_selection_reason'] = f"最佳单一角度：选择{best_layer}层({final_angle:.3f}°)"
                
            else:
                self.warning(f"未知的分层校正方法: {method}，使用分步校正")
                corrected_image, final_angle = self._apply_stepwise_correction(image, angles)
                deskew_info['angle_selection_reason'] = "默认使用分步校正"
            
            deskew_info['final_angle'] = final_angle
            deskew_info['angle'] = final_angle  # 保持兼容性
            
            # 检查是否需要校正
            if abs(final_angle) < self.processing_params['deskew_min_angle']:
                self.debug(f"分层校正角度过小 ({final_angle:.3f}°)，无需校正")
                return image, deskew_info
            
            deskew_info['correction_applied'] = True
            
            self.debug(f"分层校正完成，最终角度: {final_angle:.3f}°")
            self.debug(f"角度选择策略: {deskew_info['angle_selection_reason']}")
            
            # 可视化分层校正过程（如果启用调试）
            if self.visualizer.should_save_debug():
                self._visualize_layered_correction(image, corrected_image, angles, final_angle, method)
            
            return corrected_image, deskew_info
            
        except Exception as e:
            self.warning(f"分层倾斜校正失败: {e}")
            return image, deskew_info
    
    def _detect_layered_angles(self, image: np.ndarray) -> Dict[str, float]:
        """检测各层倾斜角度"""
        
        angles = {}
        
        # 1. 结构层倾斜（长直线检测）
        angles['structure'] = self._detect_structure_angle(image)
        
        # 2. 文档层倾斜（边缘点群分析）
        angles['document'] = self._detect_document_angle(image)
        
        # 3. 内容层倾斜（投影分析）
        angles['content'] = self._detect_content_angle(image)
        
        if self.is_debug_enabled():
            self.debug(f"检测到的倾斜角度：")
            self.debug(f"  结构层: {angles['structure']:.3f}°")
            self.debug(f"  文档层: {angles['document']:.3f}°") 
            self.debug(f"  内容层: {angles['content']:.3f}°")
        
        return angles
    
    def _detect_structure_angle(self, image: np.ndarray) -> float:
        """检测结构层倾斜角度（基于长直线）"""
        
        edges = cv2.Canny(image, 50, 150)
        
        # 使用HoughLinesP检测长直线
        lines = cv2.HoughLinesP(
            edges, 
            rho=1, 
            theta=np.pi/180, 
            threshold=100,
            minLineLength=min(image.shape) // 4,  # 最小线长为图像较短边的1/4
            maxLineGap=20
        )
        
        if lines is None:
            return 0.0
        
        # 计算线段角度和长度，进行长度加权
        line_angles = []
        line_lengths = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
            angle = np.degrees(np.arctan2(y2-y1, x2-x1))
            
            # 归一化角度到[-90, 90]
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180
            
            # 只考虑接近水平的长直线
            if abs(angle) <= 30:
                line_angles.append(angle)
                line_lengths.append(length)
        
        if not line_angles:
            return 0.0
        
        # 长度加权平均
        total_weight = sum(line_lengths)
        if total_weight == 0:
            return 0.0
            
        weighted_angle = sum(angle * length for angle, length in zip(line_angles, line_lengths)) / total_weight
        
        return weighted_angle
    
    def _detect_document_angle(self, image: np.ndarray) -> float:
        """检测文档层倾斜角度（基于边缘点群）"""
        
        h, w = image.shape
        left_points = []
        right_points = []
        
        # 采样边缘点（每10行采样一次，提高效率）
        for y in range(0, h, 10):
            row = image[y, :]
            
            # 左边缘
            for x in range(w):
                if row[x] < 240:  # 非白色像素
                    left_points.append([x, y])
                    break
            
            # 右边缘
            for x in range(w-1, -1, -1):
                if row[x] < 240:  # 非白色像素
                    right_points.append([x, y])
                    break
        
        if len(left_points) < 10 or len(right_points) < 10:
            return 0.0
        
        # 简化线性拟合
        def fit_line_angle(points):
            if len(points) < 2:
                return 0.0
            points = np.array(points)
            
            # 使用最小二乘法拟合直线 x = slope * y + intercept
            A = np.vstack([points[:, 1], np.ones(len(points))]).T
            try:
                slope, _ = np.linalg.lstsq(A, points[:, 0], rcond=None)[0]
                return np.degrees(np.arctan(slope))
            except:
                return 0.0
        
        left_angle = fit_line_angle(left_points)
        right_angle = fit_line_angle(right_points)
        
        # 返回两边的平均值
        return (left_angle + right_angle) / 2
    
    def _detect_content_angle(self, image: np.ndarray) -> float:
        """检测内容层倾斜角度（基于投影分析）"""
        
        h, w = image.shape
        
        # 测试角度范围
        angle_range = self.processing_params.get('projection_angle_range', 3.0)
        angle_step = self.processing_params.get('projection_angle_step', 0.2)
        angles_to_test = np.arange(-angle_range, angle_range + angle_step, angle_step)
        
        variances = []
        
        for angle in angles_to_test:
            # 旋转图像
            center = (w//2, h//2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, rotation_matrix, (w, h), 
                                   flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            
            # 水平投影（文本行密度分析）
            projection = np.sum(255 - rotated, axis=1)
            variance = np.var(projection)
            variances.append(variance)
        
        # 找到最大方差对应的角度
        max_idx = np.argmax(variances)
        optimal_angle = angles_to_test[max_idx]
        
        return optimal_angle
    
    def _apply_stepwise_correction(self, image: np.ndarray, angles: Dict[str, float]) -> Tuple[np.ndarray, float]:
        """应用分步校正：先结构层，再内容层微调"""
        
        structure_angle = angles['structure']
        content_angle = angles['content']
        
        # 第一步：结构层校正
        if abs(structure_angle) > self.processing_params['deskew_min_angle']:
            step1_corrected = self._rotate_image_precise(image, structure_angle)
            self.debug(f"分步校正 - 第一步（结构层）: {structure_angle:.3f}°")
        else:
            step1_corrected = image
            structure_angle = 0.0
        
        # 第二步：内容层微调
        content_adjustment = content_angle - structure_angle
        if abs(content_adjustment) > self.processing_params['deskew_min_angle']:
            final_corrected = self._rotate_image_precise(step1_corrected, content_adjustment)
            final_angle = structure_angle + content_adjustment
            self.debug(f"分步校正 - 第二步（内容层微调）: {content_adjustment:.3f}°")
        else:
            final_corrected = step1_corrected
            final_angle = structure_angle
        
        return final_corrected, final_angle
    
    def _calculate_weighted_angle(self, angles: Dict[str, float]) -> float:
        """计算加权平均角度"""
        
        structure_weight = self.processing_params.get('structure_weight', 0.6)
        document_weight = self.processing_params.get('document_weight', 0.2)
        content_weight = self.processing_params.get('content_weight', 0.2)
        
        weighted_angle = (
            angles['structure'] * structure_weight +
            angles['document'] * document_weight +
            angles['content'] * content_weight
        )
        
        return weighted_angle
    
    def _select_best_angle(self, image: np.ndarray, angles: Dict[str, float]) -> Tuple[np.ndarray, float, str]:
        """选择最佳单一角度（基于投影方差）"""
        
        best_variance = 0
        best_angle = 0.0
        best_layer = 'none'
        best_corrected = image
        
        for layer_name, angle in angles.items():
            if abs(angle) < self.processing_params['deskew_min_angle']:
                continue
                
            # 校正图像
            corrected = self._rotate_image_precise(image, angle)
            
            # 计算水平投影方差
            projection = np.sum(255 - corrected, axis=1)
            variance = np.var(projection)
            
            if variance > best_variance:
                best_variance = variance
                best_angle = angle
                best_layer = layer_name
                best_corrected = corrected
        
        return best_corrected, best_angle, best_layer
    
    def _rotate_image_precise(self, image: np.ndarray, angle: float) -> np.ndarray:
        """精确图像旋转"""
        
        if abs(angle) < 0.01:
            return image.copy()
            
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        
        rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # 计算新的边界框
        cos_val = abs(rotation_matrix[0, 0])
        sin_val = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_val) + (width * cos_val))
        new_height = int((height * cos_val) + (width * sin_val))
        
        # 调整变换矩阵
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        rotated = cv2.warpAffine(
            image, rotation_matrix, (new_width, new_height),
            flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    def _visualize_layered_correction(self, original: np.ndarray, corrected: np.ndarray, 
                                    angles: Dict[str, float], final_angle: float, method: str):
        """可视化分层校正过程"""
        
        # 这里可以调用可视化器生成专门的分层校正可视化
        # 暂时使用现有的可视化方法
        self.visualizer.visualize_deskew_process(
            original, corrected, final_angle, {
                'angle': final_angle,
                'method': f'layered_{method}',
                'detected_angles': angles,
                'correction_applied': True
            }
        )
