#!/usr/bin/env python3
"""
V3 Step2: 文本识别
- 使用PaddleOCR进行文本检测和识别
- 智能区分手写与打印文本
- 业务逻辑与可视化分离
- 支持配置驱动的参数调优
"""

import cv2
import numpy as np
import json
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
import time

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("⚠️  PaddleOCR未安装，请运行: pip install paddleocr")
    PaddleOCR = None

from utils.base_step import V3BaseStep
from visualization.step_visualizers import TextRecognitionVisualizer

@dataclass
class TextBlock:
    """V3文本块数据结构"""
    text: str
    poly: List[List[int]]
    confidence: float
    index: int
    is_handwritten: bool = False
    handwriting_score: int = 0
    avg_char_area: float = 0.0
    
    def __post_init__(self):
        """计算边界框和几何属性"""
        self.bbox = self._normalize_bbox(self.poly)
        self.x1, self.y1, self.x2, self.y2 = self.bbox
        self.center_x = (self.x1 + self.x2) / 2
        self.center_y = (self.y1 + self.y2) / 2
        self.width = self.x2 - self.x1
        self.height = self.y2 - self.y1
        self.area = self.width * self.height
    
    def _normalize_bbox(self, poly: List[List[int]]) -> List[int]:
        """将多边形转换为边界框"""
        x_coords = [p[0] for p in poly]
        y_coords = [p[1] for p in poly]
        return [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于JSON序列化"""
        return {
            'text': self.text,
            'poly': self.poly,
            'confidence': float(self.confidence),
            'index': self.index,
            'is_handwritten': self.is_handwritten,
            'handwriting_score': self.handwriting_score,
            'avg_char_area': float(self.avg_char_area),
            'bbox': self.bbox,
            'center_x': float(self.center_x),
            'center_y': float(self.center_y),
            'width': float(self.width),
            'height': float(self.height),
            'area': float(self.area)
        }

class TextRecognitionStep(V3BaseStep):
    """V3文本识别步骤"""
    
    def __init__(self, config, file_manager, logger):
        super().__init__(2, "文本识别", config, file_manager, logger)
        
        # 初始化可视化器
        self.visualizer = TextRecognitionVisualizer(
            self.step_number, config.visualization, file_manager, logger
        )
        
        # 处理参数（可配置）
        self.processing_params = {
            # PaddleOCR配置
            'use_doc_orientation_classify': False,
            'use_doc_unwarping': False, 
            'use_textline_orientation': True,
            'lang': "ch",
            'device': "cpu",
            
            # 手写检测配置
            'handwriting_confidence_threshold_low': 0.4,   # 低置信度阈值
            'handwriting_confidence_threshold_high': 0.6,  # 高置信度阈值
            'handwriting_area_threshold_large': 5000,      # 大面积阈值
            'handwriting_area_threshold_medium': 3000,     # 中等面积阈值
            'handwriting_area_threshold_small': 1000,      # 小面积阈值
            'handwriting_score_threshold': 3,              # 手写判定阈值
            
            # 文本过滤配置
            'min_text_length': 1,                          # 最小文本长度
            'min_confidence': 0.1,                         # 最小置信度
            'filter_empty_text': True,                     # 过滤空文本
            
            # 调试输出配置
            'debug_handwriting_detection': True,           # 调试手写检测
            'save_intermediate_results': True,             # 保存中间结果
        }
        
        # 更新用户配置的参数
        user_params = self.step_config.get('processing_params', {})
        self.processing_params.update(user_params)
        
        # 初始化OCR引擎（延迟加载）
        self._ocr_engine = None
    
    def execute(self, image_path: str) -> Tuple[str, List[TextBlock]]:
        """执行文本识别 - 纯业务逻辑"""
        
        self.progress("开始文本识别...")
        
        # 存储中间数据用于可视化和调试
        processing_data = {
            'input_image_path': image_path,
            'text_blocks': [],
            'ocr_raw_data': {},
            'statistics': {},
            'handwriting_analysis': {}
        }
        
        try:
            # 1. 初始化OCR引擎
            ocr_engine = self._get_ocr_engine()
            
            # 2. 执行文本识别
            self.progress("执行OCR识别...")
            text_blocks, ocr_raw_data = self._perform_ocr_recognition(image_path, ocr_engine)
            processing_data['text_blocks'] = text_blocks
            processing_data['ocr_raw_data'] = ocr_raw_data
            
            self.logger.info(f"📊 检测到 {len(text_blocks)} 个有效文本块")
            
            # 3. 手写检测分析
            self.progress("分析手写与打印文本...")
            handwriting_stats = self._analyze_handwriting(text_blocks)
            processing_data['handwriting_analysis'] = handwriting_stats
            
            # 4. 生成统计信息
            statistics = self._generate_statistics(text_blocks)
            processing_data['statistics'] = statistics
            
            # 5. 保存处理结果
            result_path = self._save_processing_results(processing_data)
            
            # 6. 可视化结果（业务逻辑与可视化分离）
            if self.visualizer.is_enabled():
                visualization_files = self.visualizer.visualize_results(
                    image_path, text_blocks, processing_data
                )
                self.visualizer.log_visualization_summary(visualization_files)
            
            # 7. 保存调试数据
            if self.should_save_debug():
                debug_data = {
                    'processing_params': self.processing_params,
                    'text_blocks_data': text_blocks,  # 直接传入，让_clean_data_types自动处理
                    'statistics': statistics,
                    'handwriting_analysis': handwriting_stats,
                    'performance_metrics': {
                        'total_blocks': len(text_blocks),
                        'handwritten_blocks': len([b for b in text_blocks if b.is_handwritten]),
                        'avg_confidence': statistics.get('confidence_stats', {}).get('avg', 0)
                    }
                }
                self.save_debug_data(self._clean_data_types(debug_data), "text_recognition_debug.json")
            
            # 8. 记录性能指标 (使用debug级别)
            self.debug(f"[步骤{self.step_number}] 性能指标: 文本块={len(text_blocks)}, 手写={len([b for b in text_blocks if b.is_handwritten])}, 平均置信度={statistics.get('confidence_stats', {}).get('avg', 0):.3f}")
            
            self.logger.result_summary(f"识别文本块: {len(text_blocks)} 个")
            # 返回原始图像路径供后续步骤使用，而不是统计JSON路径
            return image_path, text_blocks
            
        except Exception as e:
            self.logger.error(f"文本识别失败: {str(e)}")
            import traceback
            self.logger.error("完整错误堆栈:")
            self.logger.error(traceback.format_exc())
            raise
    
    def _get_ocr_engine(self) -> 'PaddleOCR':
        """获取OCR引擎实例（单例模式）"""
        
        if PaddleOCR is None:
            raise ImportError("PaddleOCR未安装，请运行: pip install paddleocr")
        
        if self._ocr_engine is None:
            self.progress("初始化PaddleOCR引擎...")
            
            # 使用与V2版本完全一致的参数，避免兼容性问题
            ocr_params = {
                'use_doc_orientation_classify': self.processing_params['use_doc_orientation_classify'],
                'use_doc_unwarping': self.processing_params['use_doc_unwarping'],
                'use_textline_orientation': self.processing_params['use_textline_orientation'],
                'lang': self.processing_params['lang'],
                'device': self.processing_params['device']
            }
            
            self._ocr_engine = PaddleOCR(**ocr_params)
            self.debug("PaddleOCR引擎初始化完成")
        
        return self._ocr_engine
    
    def _perform_ocr_recognition(self, image_path: str, ocr_engine: 'PaddleOCR') -> Tuple[List[TextBlock], Dict[str, Any]]:
        """执行OCR识别"""
        
        # 直接使用原始图像，不进行缩放
        self.debug(f"使用原始图像进行OCR识别: {image_path}")
        result = ocr_engine.predict(image_path)
        
        if not result or len(result) == 0:
            raise ValueError("OCR识别失败：未获取到有效结果")
        
        ocr_result = result[0]
        ocr_data = ocr_result.json['res']
        
        dt_polys = ocr_data.get('dt_polys', [])
        rec_texts = ocr_data.get('rec_texts', [])
        rec_scores = ocr_data.get('rec_scores', [])
        
        self.debug(f"OCR原始检测: {len(dt_polys)} 个区域")
        
        # 创建文本块对象
        text_blocks = []
        for i, (poly, text, score) in enumerate(zip(dt_polys, rec_texts, rec_scores)):
            # 文本过滤
            if not self._should_keep_text(text, score):
                continue
            
            # 手写检测
            is_handwritten, handwriting_score, avg_char_area = self._detect_handwriting(
                text.strip(), score, poly
            )
            
            # 创建文本块
            text_block = TextBlock(
                text=text.strip(),
                poly=poly,
                confidence=float(score),
                index=i,
                is_handwritten=is_handwritten,
                handwriting_score=handwriting_score,
                avg_char_area=avg_char_area
            )
            
            text_blocks.append(text_block)
        
        return text_blocks, ocr_data
    
    def _should_keep_text(self, text: str, confidence: float) -> bool:
        """判断是否保留文本块"""
        
        # 过滤空文本
        if self.processing_params['filter_empty_text'] and not text.strip():
            return False
        
        # 过滤过短文本
        if len(text.strip()) < self.processing_params['min_text_length']:
            return False
        
        # 过滤低置信度文本
        if confidence < self.processing_params['min_confidence']:
            return False
        
        return True
    
    def _detect_handwriting(self, text: str, confidence: float, poly: List[List[int]]) -> Tuple[bool, int, float]:
        """V3改进的手写检测算法"""
        
        # 计算几何特征
        poly_array = np.array(poly)
        x_coords = poly_array[:, 0]
        y_coords = poly_array[:, 1]
        width = float(max(x_coords) - min(x_coords))
        height = float(max(y_coords) - min(y_coords))
        area = width * height
        
        # 计算单字平均面积
        text_length = len(text.strip())
        avg_char_area = area / text_length if text_length > 0 else 0
        
        # 特征评分系统
        handwriting_score = 0
        
        # 1. 置信度特征分析
        if confidence < self.processing_params['handwriting_confidence_threshold_low']:
            handwriting_score += 2  # 强烈暗示手写
        elif confidence < self.processing_params['handwriting_confidence_threshold_high']:
            handwriting_score += 1  # 轻微暗示手写
        elif confidence > 0.99:
            handwriting_score -= 1  # 暗示打印
        
        # 2. 单字平均面积特征
        if avg_char_area > self.processing_params['handwriting_area_threshold_large']:
            handwriting_score += 5  # 强烈暗示手写
        elif avg_char_area > self.processing_params['handwriting_area_threshold_medium']:
            handwriting_score += 3  # 暗示手写
        elif avg_char_area > self.processing_params['handwriting_area_threshold_small']:
            handwriting_score += 1  # 轻微暗示手写
        elif avg_char_area < 500:
            handwriting_score -= 1  # 暗示打印
        
        # 3. 最终判断
        is_handwritten = handwriting_score >= self.processing_params['handwriting_score_threshold']
        
        # 调试输出
        if self.processing_params['debug_handwriting_detection'] and (is_handwritten or handwriting_score >= 1):
            self.debug(f"手写检测: '{text}' | 得分={handwriting_score} | 面积={area:.0f} | "
                      f"单字面积={avg_char_area:.0f} | 结果={'手写' if is_handwritten else '打印'}")
        
        return is_handwritten, handwriting_score, avg_char_area
    
    def _analyze_handwriting(self, text_blocks: List[TextBlock]) -> Dict[str, Any]:
        """分析手写文本分布"""
        
        total_blocks = len(text_blocks)
        handwritten_blocks = [b for b in text_blocks if b.is_handwritten]
        printed_blocks = [b for b in text_blocks if not b.is_handwritten]
        
        handwriting_analysis = {
            'total_blocks': total_blocks,
            'handwritten_count': len(handwritten_blocks),
            'printed_count': len(printed_blocks),
            'handwriting_ratio': len(handwritten_blocks) / total_blocks if total_blocks > 0 else 0,
            
            # 手写文本特征统计
            'handwritten_stats': {
                'avg_confidence': np.mean([b.confidence for b in handwritten_blocks]) if handwritten_blocks else 0,
                'avg_area': np.mean([b.avg_char_area for b in handwritten_blocks]) if handwritten_blocks else 0,
                'score_distribution': [b.handwriting_score for b in handwritten_blocks]
            },
            
            # 打印文本特征统计
            'printed_stats': {
                'avg_confidence': np.mean([b.confidence for b in printed_blocks]) if printed_blocks else 0,
                'avg_area': np.mean([b.avg_char_area for b in printed_blocks]) if printed_blocks else 0
            }
        }
        
        return handwriting_analysis
    
    def _generate_statistics(self, text_blocks: List[TextBlock]) -> Dict[str, Any]:
        """生成文本统计信息"""
        
        if not text_blocks:
            return {
                'total_blocks': 0,
                'confidence_stats': {'min': 0, 'max': 0, 'avg': 0},
                'text_lengths': [],
                'all_texts': []
            }
        
        # 置信度统计
        confidences = [b.confidence for b in text_blocks]
        confidence_stats = {
            'min': float(min(confidences)),
            'max': float(max(confidences)),
            'avg': float(np.mean(confidences)),
            'std': float(np.std(confidences))
        }
        
        # 文本长度统计
        text_lengths = [len(b.text) for b in text_blocks]
        
        # 所有识别的文本
        all_texts = [b.text for b in text_blocks]
        
        statistics = {
            'total_blocks': len(text_blocks),
            'confidence_stats': confidence_stats,
            'text_lengths': text_lengths,
            'all_texts': all_texts,
            'length_stats': {
                'min': min(text_lengths),
                'max': max(text_lengths),
                'avg': float(np.mean(text_lengths))
            }
        }
        
        return statistics
    
    def _save_processing_results(self, processing_data: Dict[str, Any]) -> str:
        """保存处理结果"""
        
        text_blocks = processing_data['text_blocks']
        
        # 保存OCR原始数据
        if self.processing_params['save_intermediate_results']:
            ocr_data_path = self.save_result_json(
                processing_data['ocr_raw_data'], "2.1_ocr_raw_data.json"
            )
            if ocr_data_path:
                self.logger.file_saved(ocr_data_path, "OCR原始数据")
        
        # 保存文本统计
        stats_path = self.save_result_json(
            processing_data['statistics'], "2.5_text_statistics.json"
        )
        if stats_path:
            self.logger.file_saved(stats_path, "文本统计")
        
        # 返回主要结果文件路径
        return str(self.step_dir / "2.5_text_statistics.json")
    
    def _clean_data_types(self, data: Any) -> Any:
        """清理数据类型，确保JSON可序列化"""
        try:
            if isinstance(data, dict):
                return {key: self._clean_data_types(value) for key, value in data.items()}
            elif isinstance(data, list):
                return [self._clean_data_types(item) for item in data]
            elif isinstance(data, tuple):
                return [self._clean_data_types(item) for item in data]
            elif hasattr(data, 'to_dict') and callable(getattr(data, 'to_dict')):
                # 处理有to_dict方法的自定义对象（如TextBlock）
                return self._clean_data_types(data.to_dict())
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
        except Exception as e:
            import traceback
            self.logger.error(f"数据类型清理失败: {type(data)} = {repr(data)[:100]}, 错误: {e}")
            self.logger.error("_clean_data_types 错误堆栈:")
            self.logger.error(traceback.format_exc())
            # 如果清理失败，尝试简化处理
            if hasattr(data, '__dict__'):
                try:
                    return str(data)
                except:
                    return f"<{type(data).__name__} object>"
            return str(data)
    

