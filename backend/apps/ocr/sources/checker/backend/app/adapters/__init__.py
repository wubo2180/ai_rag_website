"""
OCR适配器模块
提供各种OCR模型的适配器实现
"""
from .base_ocr_adapter import (
    BaseOCRAdapter,
    OCRAdapterException,
    ParseError,
    SaveError,
    ValidationError
)

__all__ = [
    'BaseOCRAdapter',
    'OCRAdapterException',
    'ParseError',
    'SaveError',
    'ValidationError'
]


