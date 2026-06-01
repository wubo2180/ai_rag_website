#!/usr/bin/env python3
"""
V3基础可视化器 - 所有可视化的基础类
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import numpy as np

from config.settings import V3Config
from utils.file_manager import V3FileManager
from utils.logger import V3Logger

class BaseVisualizer(ABC):
    """基础可视化器 - 所有可视化器的基类"""
    
    def __init__(self, step_number: int, config: V3Config, 
                 file_manager: V3FileManager, logger: V3Logger):
        self.step_number = step_number
        self.config = config
        self.file_manager = file_manager
        self.logger = logger
        
        # 可视化相关配置
        self.visualization_enabled = config.enabled
        self.save_intermediate = config.save_intermediate
        self.save_debug = config.save_debug_images
        
    def is_enabled(self) -> bool:
        """检查可视化是否启用"""
        return self.visualization_enabled
    
    def should_save_intermediate(self) -> bool:
        """是否应该保存中间可视化结果"""
        return self.save_intermediate and self.is_enabled()
    
    def should_save_debug(self) -> bool:
        """是否应该保存调试可视化结果"""
        return self.save_debug and self.is_enabled()
    
    def save_visualization(self, image, filename: str, 
                          description: str = "") -> Optional[Path]:
        """保存可视化图像"""
        if not self.is_enabled():
            return None
        
        # 检测输入类型并转换为numpy数组
        if hasattr(image, 'savefig'):  # matplotlib Figure对象
            import io
            import cv2
            
            # 将matplotlib图保存到内存buffer
            buffer = io.BytesIO()
            image.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
            buffer.seek(0)
            
            # 从buffer读取为numpy数组
            import numpy as np
            from PIL import Image
            pil_image = Image.open(buffer)
            # 转换为RGB模式（去除透明通道）
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
            # 转换为numpy数组并调整为OpenCV的BGR格式
            image_array = np.array(pil_image)
            if len(image_array.shape) == 3:
                image_array = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            
            path = self.file_manager.save_image(image_array, filename, self.step_number, "visualization")
        else:  # 假设是numpy数组
            path = self.file_manager.save_image(image, filename, self.step_number, "visualization")
            
        if path and description:
            self.logger.file_saved(path, f"可视化: {description}")
        return path
    
    def create_comparison_visualization(self, image_pairs: List[Tuple[str, np.ndarray]], 
                                     filename: str, description: str = "") -> Optional[Path]:
        """创建对比可视化"""
        if not self.should_save_intermediate():
            return None
            
        path = self.file_manager.create_comparison_image(image_pairs, filename, self.step_number)
        if path and description:
            self.logger.file_saved(path, f"对比可视化: {description}")
        return path
    
    @abstractmethod
    def visualize_results(self, input_data: Any, output_data: Any, 
                         intermediate_data: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
        """可视化处理结果 - 子类必须实现"""
        pass
    
    def log_visualization_summary(self, saved_files):
        """输出可视化摘要 - 支持Dict或List类型"""
        if not self.is_enabled() or not saved_files:
            return
            
        self.logger.info(f"可视化完成，生成 {len(saved_files)} 个文件:")
        
        if isinstance(saved_files, dict):
            # 处理字典类型 (Dict[str, Path])
            for name, path in saved_files.items():
                self.logger.info(f"  - {name}: {path}")
        elif isinstance(saved_files, list):
            # 处理列表类型 (List[Path]) 
            for path in saved_files:
                filename = Path(path).name if hasattr(path, 'name') else str(path).split('/')[-1]
                self.logger.info(f"  - {filename}: {path}")
        else:
            self.logger.warning(f"不支持的可视化文件类型: {type(saved_files)}")
    
    # 便捷的可视化方法
    def _add_text_overlay(self, image: np.ndarray, text: str, 
                         position: Tuple[int, int] = (10, 30),
                         color: Tuple[int, int, int] = (0, 255, 0),
                         font_scale: float = 0.7) -> np.ndarray:
        """在图像上添加文本覆盖"""
        import cv2
        result = image.copy()
        cv2.putText(result, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, color, 2, cv2.LINE_AA)
        return result
    
    def _create_side_by_side(self, left_img: np.ndarray, right_img: np.ndarray,
                           left_title: str = "Before", right_title: str = "After") -> np.ndarray:
        """创建左右对比图"""
        import cv2
        
        # 复制图像以避免修改原图
        left_copy = left_img.copy()
        right_copy = right_img.copy()
        
        # 确保通道数一致（先处理通道数）
        if len(left_copy.shape) == 2:
            left_copy = cv2.cvtColor(left_copy, cv2.COLOR_GRAY2BGR)
        if len(right_copy.shape) == 2:
            right_copy = cv2.cvtColor(right_copy, cv2.COLOR_GRAY2BGR)
        
        # 确保图像尺寸一致（在通道数一致后处理）
        h1, w1 = left_copy.shape[:2]
        h2, w2 = right_copy.shape[:2]
        
        # 使用较小尺寸避免内存问题
        target_h = min(h1, h2, 1024)  # 限制最大高度
        target_w = min(w1, w2, 1024)  # 限制最大宽度
        
        # 保持宽高比调整尺寸
        scale1 = min(target_w / w1, target_h / h1)
        scale2 = min(target_w / w2, target_h / h2)
        
        new_w1, new_h1 = int(w1 * scale1), int(h1 * scale1)
        new_w2, new_h2 = int(w2 * scale2), int(h2 * scale2)
        
        # 调整到相同尺寸
        final_h = max(new_h1, new_h2)
        final_w = max(new_w1, new_w2)
        
        # 调整图像尺寸
        left_resized = cv2.resize(left_copy, (final_w, final_h))
        right_resized = cv2.resize(right_copy, (final_w, final_h))
        
        # 水平拼接
        try:
            combined = np.hstack([left_resized, right_resized])
        except ValueError as e:
            self.logger.debug(f"图像拼接失败: {e}, 左图形状: {left_resized.shape}, 右图形状: {right_resized.shape}")
            # 创建空白对比图作为后备
            combined = np.ones((final_h, final_w * 2, 3), dtype=np.uint8) * 255
            combined[:final_h, :final_w] = left_resized
            combined[:final_h, final_w:] = right_resized
        
        # 添加标题
        combined = self._add_text_overlay(combined, left_title, (10, 30))
        combined = self._add_text_overlay(combined, right_title, (final_w + 10, 30))
        
        return combined
    
    def _create_grid_visualization(self, images: List[Tuple[str, np.ndarray]], 
                                 cols: int = 2) -> np.ndarray:
        """创建网格可视化"""
        import cv2
        
        if not images:
            return np.zeros((100, 100, 3), dtype=np.uint8)
        
        num_images = len(images)
        rows = (num_images + cols - 1) // cols
        
        # 获取最大尺寸
        max_h, max_w = 0, 0
        for _, img in images:
            h, w = img.shape[:2]
            max_h, max_w = max(max_h, h), max(max_w, w)
        
        # 创建画布
        canvas_h = rows * (max_h + 40)  # 为标题预留空间
        canvas_w = cols * max_w
        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255
        
        # 放置图像
        for i, (title, img) in enumerate(images):
            row = i // cols
            col = i % cols
            
            # 确保图像格式
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            
            # 调整尺寸
            img = cv2.resize(img, (max_w, max_h))
            
            # 计算位置
            y_start = row * (max_h + 40) + 40
            y_end = y_start + max_h
            x_start = col * max_w
            x_end = x_start + max_w
            
            # 放置图像
            canvas[y_start:y_end, x_start:x_end] = img
            
            # 添加标题
            cv2.putText(canvas, title, (x_start + 10, row * (max_h + 40) + 25),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
        
        return canvas
