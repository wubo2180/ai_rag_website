#!/usr/bin/env python3
"""
V3步骤模块 - 所有处理步骤的集合
"""

from .step1_preprocessing import PreprocessingStep
from .step2_text_recognition import TextRecognitionStep
from .step3_text_masking import TextMaskingStep
from .step4_table_line_detection import TableLineDetectionStep
from .step5_text_aggregation import TextAggregationStep
from .step6_field_extraction import FieldExtractionStep

# 可用步骤注册表
AVAILABLE_STEPS = {
    1: PreprocessingStep,
    2: TextRecognitionStep,
    3: TextMaskingStep,
    4: TableLineDetectionStep,
    5: TextAggregationStep,
    6: FieldExtractionStep,
    # 7: AttributeFormattingStep, # 待实现
    # 8: ExcelGenerationStep,  # 待实现
}

__all__ = ['AVAILABLE_STEPS', 'PreprocessingStep', 'TextRecognitionStep', 'TextMaskingStep', 'TableLineDetectionStep', 'TextAggregationStep', 'FieldExtractionStep']
