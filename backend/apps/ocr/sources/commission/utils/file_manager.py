#!/usr/bin/env python3
"""
V3文件管理系统 - 统一管理中间文件和输出
"""

import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from config.settings import V3Config

class V3FileManager:
    """V3文件管理器 - 统一管理所有文件输出
    
    文件组织规则：
    📁 visualizations/ - 所有图片文件（.png, .jpg等）
    📄 steps/ - 所有数据文件（.json, .txt等）  
    🐛 debug/ - 调试专用文件
    📊 results/ - 最终结果文件
    """
    
    def __init__(self, config: V3Config, base_output_dir: Optional[Path] = None):
        self.config = config
        self.base_output_dir = base_output_dir or config.output_dir
        
        # 创建基础目录结构
        self.base_output_dir = Path(self.base_output_dir)
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.steps_dir = self.base_output_dir / "steps"
        self.visualization_dir = self.base_output_dir / "visualizations"
        self.debug_dir = self.base_output_dir / "debug"
        self.results_dir = self.base_output_dir / "results"
        
        # 根据配置决定是否创建目录
        if self.config.should_save_intermediate():
            self.steps_dir.mkdir(exist_ok=True)
        
        if self.config.visualization.enabled:
            self.visualization_dir.mkdir(exist_ok=True)
        
        if self.config.should_save_debug_data():
            self.debug_dir.mkdir(exist_ok=True)
        
        self.results_dir.mkdir(exist_ok=True)
    
    def get_step_dir(self, step_number: int) -> Path:
        """获取步骤输出目录"""
        step_dir = self.steps_dir / f"step{step_number:02d}"
        if self.config.should_save_intermediate():
            step_dir.mkdir(exist_ok=True)
        return step_dir
    
    def get_visualization_dir(self, step_number: Optional[int] = None) -> Path:
        """获取可视化输出目录"""
        if step_number:
            vis_dir = self.visualization_dir / f"step{step_number:02d}"
        else:
            vis_dir = self.visualization_dir
        
        if self.config.visualization.enabled:
            vis_dir.mkdir(exist_ok=True, parents=True)
        return vis_dir
    
    def get_debug_dir(self, step_number: Optional[int] = None) -> Path:
        """获取调试输出目录"""
        if step_number:
            debug_dir = self.debug_dir / f"step{step_number:02d}"
        else:
            debug_dir = self.debug_dir
        
        if self.config.should_save_debug_data():
            debug_dir.mkdir(exist_ok=True, parents=True)
        return debug_dir
    
    def save_image(self, image: np.ndarray, filename: str, step_number: int, 
                   category: str = "intermediate") -> Optional[Path]:
        """保存图像文件 - 所有图片统一保存到visualizations目录
        
        文件组织规则：
        📁 visualizations/ - 所有图片文件，不管category参数如何
        🐛 debug/ - 仅调试专用图片
        """
        
        # 检查是否应该保存
        if not self.config.visualization.enabled and category != "debug":
            return None
        elif category == "debug" and not self.config.should_save_debug_data():
            return None
        
        # 新文件组织规则：所有图片文件统一保存到visualizations目录
        # 只有标记为debug的图片才保存到debug目录
        if category == "debug":
            save_dir = self.get_debug_dir(step_number)
        else:
            # 所有非调试图片（包括intermediate, visualization等）都保存到visualizations目录
            save_dir = self.get_visualization_dir(step_number)
        
        # 图像尺寸控制
        if self.config.visualization.max_image_size:
            max_w, max_h = self.config.visualization.max_image_size
            h, w = image.shape[:2]
            if w > max_w or h > max_h:
                scale = min(max_w / w, max_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
                image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        
        # 保存文件
        file_path = save_dir / filename
        try:
            # 无损保存，不进行任何质量压缩
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                # JPEG使用最高质量100（无压缩）
                cv2.imwrite(str(file_path), image, [cv2.IMWRITE_JPEG_QUALITY, 100])
            elif filename.lower().endswith('.png'):
                # PNG使用最高压缩级别但保持无损
                cv2.imwrite(str(file_path), image, [cv2.IMWRITE_PNG_COMPRESSION, 1])
            else:
                # 其他格式默认无压缩保存
                cv2.imwrite(str(file_path), image)
            
            return file_path
        except Exception as e:
            print(f"保存图像失败 {file_path}: {e}")
            return None
    
    def save_json(self, data: Dict[str, Any], filename: str, step_number: int,
                  category: str = "intermediate") -> Optional[Path]:
        """保存JSON数据"""
        
        # 根据类别和配置决定是否保存
        if category == "intermediate" and not self.config.should_save_intermediate():
            return None
        elif category == "debug" and not self.config.should_save_debug_data():
            return None
        
        # 确定保存目录
        if category == "debug":
            save_dir = self.get_debug_dir(step_number)
        elif category == "result":
            save_dir = self.results_dir
        else:
            save_dir = self.get_step_dir(step_number)
        
        file_path = save_dir / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return file_path
        except Exception as e:
            print(f"保存JSON失败 {file_path}: {e}")
            return None
    
    def save_text(self, text: str, filename: str, step_number: int,
                  category: str = "intermediate") -> Optional[Path]:
        """保存文本文件"""
        
        if category == "intermediate" and not self.config.should_save_intermediate():
            return None
        elif category == "debug" and not self.config.should_save_debug_data():
            return None
        
        # 确定保存目录
        if category == "debug":
            save_dir = self.get_debug_dir(step_number)
        elif category == "result":
            save_dir = self.results_dir
        else:
            save_dir = self.get_step_dir(step_number)
        
        file_path = save_dir / filename
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            return file_path
        except Exception as e:
            print(f"保存文本失败 {file_path}: {e}")
            return None
    
    def create_comparison_image(self, image_pairs: List[Tuple[str, np.ndarray]], 
                              filename: str, step_number: int) -> Optional[Path]:
        """创建对比图像"""
        
        if not self.config.visualization.save_comparisons:
            return None
        
        try:
            # 计算网格布局
            num_images = len(image_pairs)
            cols = min(3, num_images)  # 最多3列
            rows = (num_images + cols - 1) // cols
            
            # 获取图像尺寸（假设所有图像尺寸相似）
            sample_img = image_pairs[0][1]
            if len(sample_img.shape) == 2:
                img_h, img_w = sample_img.shape
                channels = 1
            else:
                img_h, img_w, channels = sample_img.shape
            
            # 创建拼接画布
            canvas_w = cols * img_w
            canvas_h = rows * (img_h + 40)  # 为标题预留40像素
            
            if channels == 1:
                canvas = np.ones((canvas_h, canvas_w), dtype=np.uint8) * 255
            else:
                canvas = np.ones((canvas_h, canvas_w, channels), dtype=np.uint8) * 255
            
            # 拼接图像
            for i, (title, img) in enumerate(image_pairs):
                row = i // cols
                col = i % cols
                
                # 确保图像格式一致
                if channels == 1 and len(img.shape) == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                elif channels == 3 and len(img.shape) == 2:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
                
                # 调整图像尺寸以匹配预期尺寸
                if img.shape[:2] != (img_h, img_w):
                    img = cv2.resize(img, (img_w, img_h))
                
                # 计算位置
                y_start = row * (img_h + 40) + 40
                y_end = y_start + img_h
                x_start = col * img_w
                x_end = x_start + img_w
                
                # 安全复制图像
                try:
                    canvas[y_start:y_end, x_start:x_end] = img
                except ValueError as e:
                    # 如果尺寸仍然不匹配，强制调整
                    target_h = y_end - y_start
                    target_w = x_end - x_start
                    img_resized = cv2.resize(img, (target_w, target_h))
                    canvas[y_start:y_end, x_start:x_end] = img_resized
                
                # 添加标题
                if channels == 1:
                    canvas_rgb = cv2.cvtColor(canvas, cv2.COLOR_GRAY2BGR)
                else:
                    canvas_rgb = canvas
                
                cv2.putText(canvas_rgb, title, (x_start + 10, row * (img_h + 40) + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
                
                if channels == 1:
                    canvas = cv2.cvtColor(canvas_rgb, cv2.COLOR_BGR2GRAY)
                else:
                    canvas = canvas_rgb
            
            # 保存拼接图
            return self.save_image(canvas, filename, step_number, "visualization")
            
        except Exception as e:
            print(f"创建对比图失败: {e}")
            return None
    
    def cleanup_temp_files(self):
        """清理临时文件"""
        if self.config.file_output.auto_cleanup:
            try:
                # 只清理中间文件，保留结果
                if self.debug_dir.exists():
                    import shutil
                    shutil.rmtree(self.debug_dir)
                    print("🧹 调试文件已清理")
            except Exception as e:
                print(f"清理临时文件失败: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """获取文件管理摘要"""
        def count_files(directory: Path) -> int:
            if not directory.exists():
                return 0
            return len(list(directory.rglob("*"))) if directory.is_dir() else 0
        
        return {
            "base_directory": str(self.base_output_dir),
            "intermediate_files": count_files(self.steps_dir),
            "visualization_files": count_files(self.visualization_dir),
            "debug_files": count_files(self.debug_dir),
            "result_files": count_files(self.results_dir),
            "config": {
                "save_intermediate": self.config.should_save_intermediate(),
                "save_debug": self.config.should_save_debug_data(),
                "save_visualizations": self.config.visualization.enabled
            }
        }
