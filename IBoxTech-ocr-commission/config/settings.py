#!/usr/bin/env python3
"""
V3配置设置 - 统一管理调试输出和中间文件
"""

from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional

class DebugLevel(Enum):
    """调试级别"""
    NONE = "none"           # 无调试输出
    ERROR = "error"         # 仅错误
    WARNING = "warning"     # 错误+警告
    INFO = "info"          # 错误+警告+信息
    DEBUG = "debug"        # 所有调试信息
    VERBOSE = "verbose"    # 详细调试信息

class OutputLevel(Enum):
    """输出控制级别"""
    MINIMAL = "minimal"     # 仅最终结果
    STANDARD = "standard"   # 标准输出
    DETAILED = "detailed"   # 详细输出
    COMPREHENSIVE = "comprehensive"  # 完整输出

@dataclass
class VisualizationConfig:
    """可视化配置"""
    enabled: bool = True
    save_intermediate: bool = True
    save_comparisons: bool = True
    save_debug_images: bool = False
    image_quality: int = 100  # 100%无损质量
    max_image_size: tuple = None

@dataclass
class TestTypeConfig:
    """测试类型配置"""
    # 明确定义的测试类型列表（需要时可手动添加）
    known_test_types: list = field(default_factory=lambda: [
        'RoHs', 'HF', '其他金属',
        # 可根据实际需求手动添加新的测试类型
        'REACH', 'PAH', 'VOC', 'PFOA', 'PFOS', 'BPA',
        '邻苯二甲酸酯', '阻燃剂', '甲醛', '重金属',
        'CPSIA', '铅含量', '镉含量', '汞含量'
    ])

@dataclass
class FileOutputConfig:
    """文件输出配置"""
    save_intermediate_files: bool = True
    save_debug_data: bool = False
    auto_cleanup: bool = False
    compression_enabled: bool = False
    max_file_size_mb: int = 100

@dataclass
class ProcessingConfig:
    """处理配置"""
    parallel_processing: bool = False
    max_workers: int = 4
    memory_optimization: bool = True
    early_stopping: bool = False

@dataclass
class V3Config:
    """V3框架统一配置"""
    
    # 基础配置
    debug_level: DebugLevel = DebugLevel.INFO
    output_level: OutputLevel = OutputLevel.STANDARD
    output_dir: Path = Path("data/v3_output")
    
    # 子配置
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    file_output: FileOutputConfig = field(default_factory=FileOutputConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    test_types: TestTypeConfig = field(default_factory=TestTypeConfig)
    
    # 步骤特定配置
    step_configs: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保输出目录存在
        self.output_dir = Path(self.output_dir)
        
        # 根据调试级别自动调整其他配置
        if self.debug_level == DebugLevel.NONE:
            self.visualization.save_debug_images = False
            self.file_output.save_debug_data = False
        elif self.debug_level in [DebugLevel.DEBUG, DebugLevel.VERBOSE]:
            self.visualization.save_debug_images = True
            self.file_output.save_debug_data = True
    
    def get_step_config(self, step_number: int) -> Dict[str, Any]:
        """获取步骤特定配置"""
        return self.step_configs.get(step_number, {})
    
    def set_step_config(self, step_number: int, config: Dict[str, Any]):
        """设置步骤特定配置"""
        self.step_configs[step_number] = config
    
    def is_debug_enabled(self) -> bool:
        """是否启用调试"""
        return self.debug_level not in [DebugLevel.NONE, DebugLevel.ERROR]
    
    def is_verbose_enabled(self) -> bool:
        """是否启用详细输出"""
        return self.debug_level in [DebugLevel.VERBOSE]
    
    def should_save_intermediate(self) -> bool:
        """是否保存中间文件"""
        return self.file_output.save_intermediate_files
    
    def should_save_debug_data(self) -> bool:
        """是否保存调试数据"""
        return self.file_output.save_debug_data and self.is_debug_enabled()

# 预定义配置模板
PRODUCTION_CONFIG = V3Config(
    debug_level=DebugLevel.ERROR,
    output_level=OutputLevel.MINIMAL,
    visualization=VisualizationConfig(
        save_intermediate=False,
        save_debug_images=False,
        save_comparisons=False
    ),
    file_output=FileOutputConfig(
        save_intermediate_files=False,
        save_debug_data=False,
        auto_cleanup=True
    )
)

DEVELOPMENT_CONFIG = V3Config(
    debug_level=DebugLevel.DEBUG,
    output_level=OutputLevel.DETAILED,
    visualization=VisualizationConfig(
        save_intermediate=True,
        save_debug_images=True,
        save_comparisons=True
    ),
    file_output=FileOutputConfig(
        save_intermediate_files=True,
        save_debug_data=True,
        auto_cleanup=False
    )
)

DEBUG_CONFIG = V3Config(
    debug_level=DebugLevel.VERBOSE,
    output_level=OutputLevel.COMPREHENSIVE,
    visualization=VisualizationConfig(
        save_intermediate=True,
        save_debug_images=True,
        save_comparisons=True
    ),
    file_output=FileOutputConfig(
        save_intermediate_files=True,
        save_debug_data=True,
        auto_cleanup=False
    )
)
