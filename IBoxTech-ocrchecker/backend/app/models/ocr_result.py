"""
OCR识别结果模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float

# 从上级模块导入db实例
from . import db


class OCRResult(db.Model):
    """OCR识别结果模型"""
    
    __tablename__ = 'ocr_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False, comment='关联文件ID')
    page_number = Column(Integer, nullable=False, comment='页码（从1开始）')
    
    # 原始OCR结果
    raw_text = Column(Text, nullable=True, comment='原始识别文本')
    raw_result = Column(JSON, nullable=True, comment='原始OCR结果JSON')
    
    # 结构化数据
    table_data = Column(JSON, nullable=True, comment='表格数据JSON')
    form_fields = Column(JSON, nullable=True, comment='表单字段数据')
    
    # 识别区域信息
    text_regions = Column(JSON, nullable=True, comment='文本区域坐标')
    table_regions = Column(JSON, nullable=True, comment='表格区域坐标')
    handwriting_regions = Column(JSON, nullable=True, comment='手写区域坐标')
    
    # 质量评估
    confidence_score = Column(Float, nullable=True, comment='识别置信度')
    quality_score = Column(Float, nullable=True, comment='图像质量评分')
    
    # 处理信息
    processing_time = Column(Float, nullable=True, comment='处理耗时（秒）')
    ocr_engine = Column(String(50), default='PaddleOCR', comment='使用的OCR引擎')
    ocr_version = Column(String(20), nullable=True, comment='OCR引擎版本')
    
    # 修正状态
    is_reviewed = Column(db.Boolean, default=False, comment='是否已人工核对')
    review_status = Column(String(20), default='pending', comment='核对状态：pending/in_progress/completed')
    
    # 修正后的数据
    corrected_table_data = Column(JSON, nullable=True, comment='修正后的表格数据')
    corrected_form_fields = Column(JSON, nullable=True, comment='修正后的表单数据')
    correction_notes = Column(Text, nullable=True, comment='修正说明')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    reviewed_at = Column(DateTime, nullable=True, comment='核对完成时间')
    
    def __init__(self, file_id, page_number, raw_text=None, raw_result=None):
        self.file_id = file_id
        self.page_number = page_number
        self.raw_text = raw_text
        self.raw_result = raw_result
    
    def set_table_data(self, table_data):
        """设置表格数据"""
        self.table_data = table_data
    
    def set_form_fields(self, form_fields):
        """设置表单字段"""
        self.form_fields = form_fields
    
    def get_corrected_data(self):
        """获取修正后的数据，如果没有则返回原始数据"""
        return {
            'table_data': self.corrected_table_data or self.table_data,
            'form_fields': self.corrected_form_fields or self.form_fields
        }
    
    def apply_corrections(self, table_data=None, form_fields=None, notes=None):
        """应用人工修正"""
        if table_data is not None:
            self.corrected_table_data = table_data
        if form_fields is not None:
            self.corrected_form_fields = form_fields
        if notes:
            self.correction_notes = notes
        
        self.is_reviewed = True
        self.review_status = 'completed'
        self.reviewed_at = datetime.utcnow()
    
    def calculate_accuracy(self):
        """计算数据准确性（需要有人工校正数据作为参考）"""
        if not self.is_reviewed or not self.corrected_table_data:
            return None
        
        # 简单的准确性计算逻辑
        original_cells = len(str(self.table_data or ''))
        corrected_cells = len(str(self.corrected_table_data or ''))
        
        if original_cells == 0:
            return 0.0
        
        # 这里可以实现更复杂的准确性计算算法
        return min(corrected_cells / original_cells, 1.0)
    
    def get_text_regions_count(self):
        """获取文本区域数量"""
        if self.text_regions and isinstance(self.text_regions, list):
            return len(self.text_regions)
        return 0
    
    def get_table_regions_count(self):
        """获取表格区域数量"""
        if self.table_regions and isinstance(self.table_regions, list):
            return len(self.table_regions)
        return 0
    
    def get_handwriting_regions_count(self):
        """获取手写区域数量"""
        if self.handwriting_regions and isinstance(self.handwriting_regions, list):
            return len(self.handwriting_regions)
        return 0
    
    def to_dict(self, include_raw=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'file_id': self.file_id,
            'page_number': self.page_number,
            'table_data': self.table_data,
            'form_fields': self.form_fields,
            'text_regions': self.text_regions,
            'table_regions': self.table_regions,
            'handwriting_regions': self.handwriting_regions,
            'confidence_score': self.confidence_score,
            'quality_score': self.quality_score,
            'processing_time': self.processing_time,
            'ocr_engine': self.ocr_engine,
            'ocr_version': self.ocr_version,
            'is_reviewed': self.is_reviewed,
            'review_status': self.review_status,
            'corrected_table_data': self.corrected_table_data,
            'corrected_form_fields': self.corrected_form_fields,
            'correction_notes': self.correction_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'text_regions_count': self.get_text_regions_count(),
            'table_regions_count': self.get_table_regions_count(),
            'handwriting_regions_count': self.get_handwriting_regions_count()
        }
        
        if include_raw:
            data.update({
                'raw_text': self.raw_text,
                'raw_result': self.raw_result
            })
        
        return data
    
    def __repr__(self):
        return f'<OCRResult file_id={self.file_id} page={self.page_number}>'
