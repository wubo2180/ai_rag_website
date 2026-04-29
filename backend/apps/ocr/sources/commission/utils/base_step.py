#!/usr/bin/env python3
"""
V3基础步骤类 - 业务逻辑与可视化分离
"""

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from config.settings import V3Config
from .logger import V3Logger
from .file_manager import V3FileManager

class V3BaseStep(ABC):
    """V3步骤基础类 - 业务逻辑与可视化完全分离"""
    
    def __init__(self, step_number: int, step_name: str, 
                 config: V3Config, file_manager: V3FileManager, logger: V3Logger):
        self.step_number = step_number
        self.step_name = step_name
        self.config = config
        self.file_manager = file_manager
        self.logger = logger
        
        # 获取步骤专用目录
        self.step_dir = file_manager.get_step_dir(step_number)
        self.visualization_dir = file_manager.get_visualization_dir(step_number)
        self.debug_dir = file_manager.get_debug_dir(step_number)
        
        # 步骤专用配置
        self.step_config = config.get_step_config(step_number)
        
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """执行步骤主要业务逻辑 - 子类必须实现"""
        pass
    
    def run(self, input_data: Any) -> Any:
        """运行步骤（包含完整的生命周期管理）"""
        start_time = time.time()
        
        # 步骤开始
        self.logger.step_header(self.step_name, self.step_number)
        self.logger.debug(f"步骤 {self.step_number} 开始执行...")
        
        try:
            # 执行业务逻辑
            result = self.execute(input_data)
            
            # 执行后处理
            self._post_execute(result)
            
            # 步骤成功完成
            elapsed_time = time.time() - start_time
            self.logger.step_footer(self.step_number, elapsed_time)
            self.logger.performance_metric("执行时间", elapsed_time, "秒")
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.logger.error(f"步骤 {self.step_number} 执行失败: {str(e)}")
            self.logger.debug(f"失败时间: {elapsed_time:.2f}秒")
            raise
    
    def _post_execute(self, result: Any):
        """执行后处理 - 可被子类重写"""
        pass
    
    # 便捷方法 - 业务逻辑专用
    def save_result_image(self, image, filename: str) -> Optional[Path]:
        """保存结果图像（业务逻辑输出）"""
        path = self.file_manager.save_image(image, filename, self.step_number, "intermediate")
        if path:
            self.logger.file_saved(path, "处理结果")
        return path
    
    def save_result_json(self, data: Dict[str, Any], filename: str) -> Optional[Path]:
        """保存结果JSON数据"""
        path = self.file_manager.save_json(data, filename, self.step_number, "intermediate")
        if path:
            self.logger.file_saved(path, "数据结果")
        return path
    
    def save_debug_image(self, image, filename: str) -> Optional[Path]:
        """保存调试图像"""
        path = self.file_manager.save_image(image, filename, self.step_number, "debug")
        if path:
            self.logger.file_saved(path, "调试图像")
        return path
    
    def save_debug_data(self, data: Dict[str, Any], filename: str) -> Optional[Path]:
        """保存调试数据"""
        path = self.file_manager.save_json(data, filename, self.step_number, "debug")
        if path:
            self.logger.file_saved(path, "调试数据")
        return path
    
    # 配置相关便捷方法
    def should_save_intermediate(self) -> bool:
        """是否应该保存中间结果"""
        return self.config.should_save_intermediate()
    
    def should_save_debug(self) -> bool:
        """是否应该保存调试信息"""
        return self.config.should_save_debug_data()
    
    def is_debug_enabled(self) -> bool:
        """是否启用调试模式"""
        return self.config.is_debug_enabled()
    
    def is_verbose_enabled(self) -> bool:
        """是否启用详细输出"""
        return self.config.is_verbose_enabled()
    
    # 日志便捷方法
    def debug(self, message: str):
        """步骤调试信息"""
        self.logger.debug(f"[步骤{self.step_number}] {message}")
    
    def info(self, message: str):
        """步骤信息"""
        self.logger.info(f"[步骤{self.step_number}] {message}")
    
    def progress(self, message: str):
        """步骤进度信息"""
        self.logger.progress(f"[步骤{self.step_number}] {message}")
    
    def success(self, message: str):
        """步骤成功信息"""
        self.logger.success(f"[步骤{self.step_number}] {message}")
    
    def warning(self, message: str):
        """步骤警告信息"""
        self.logger.warning(f"[步骤{self.step_number}] {message}")
    
    def error(self, message: str):
        """步骤错误信息"""
        self.logger.error(f"[步骤{self.step_number}] {message}")
    
    def log_performance(self, metric_name: str, value: Any, unit: str = ""):
        """记录性能指标"""
        self.logger.performance_metric(f"[步骤{self.step_number}] {metric_name}", value, unit)
    
    def log_memory_usage(self, description: str = ""):
        """记录内存使用"""
        desc = f"步骤{self.step_number}" + (f" {description}" if description else "")
        self.logger.memory_usage(desc)
