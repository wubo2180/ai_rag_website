#!/usr/bin/env python3
"""
V3 OCR Pipeline Framework
业务逻辑与可视化分离的新架构
"""

__version__ = "3.0.0"
__author__ = "IBox OCR Team"

from .core.pipeline import OCRPipeline
from .config.settings import V3Config, DebugLevel, OutputLevel
from .utils.file_manager import V3FileManager
from .utils.logger import V3Logger

__all__ = [
    'OCRPipeline',
    'V3Config',
    'DebugLevel', 
    'OutputLevel',
    'V3FileManager',
    'V3Logger'
]