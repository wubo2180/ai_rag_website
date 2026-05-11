"""
核对记录模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON

# 从上级模块导入db实例
from . import db


class ReviewRecord(db.Model):
    """核对记录模型"""
    
    __tablename__ = 'review_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False, comment='关联文件ID')
    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='核对人ID')
    ocr_result_id = Column(Integer, ForeignKey('ocr_results.id'), nullable=True, comment='关联OCR结果ID')
    
    # 核对信息
    review_type = Column(String(20), nullable=False, comment='核对类型：table/form/handwriting/all')
    action_type = Column(String(20), nullable=False, comment='操作类型：create/update/delete/correct')
    
    # 修改内容
    field_name = Column(String(100), nullable=True, comment='修改的字段名')
    old_value = Column(JSON, nullable=True, comment='修改前的值')
    new_value = Column(JSON, nullable=True, comment='修改后的值')
    
    # 位置信息
    page_number = Column(Integer, nullable=True, comment='页码')
    row_index = Column(Integer, nullable=True, comment='行索引')
    column_index = Column(Integer, nullable=True, comment='列索引')
    coordinates = Column(JSON, nullable=True, comment='坐标信息 {x, y, width, height}')
    
    # 核对详情
    review_notes = Column(Text, nullable=True, comment='核对说明')
    confidence_level = Column(String(10), nullable=True, comment='置信度：high/medium/low')
    is_confirmed = Column(db.Boolean, default=True, comment='是否确认修改')
    
    # 质量评估
    error_type = Column(String(50), nullable=True, comment='错误类型：recognition/structure/handwriting/other')
    severity = Column(String(10), nullable=True, comment='严重程度：high/medium/low')
    
    # 时间信息
    review_duration = Column(Integer, nullable=True, comment='核对耗时（秒）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='记录创建时间')
    
    def __init__(self, file_id, reviewer_id, review_type, action_type, 
                 ocr_result_id=None, field_name=None, old_value=None, new_value=None):
        self.file_id = file_id
        self.reviewer_id = reviewer_id
        self.ocr_result_id = ocr_result_id
        self.review_type = review_type
        self.action_type = action_type
        self.field_name = field_name
        self.old_value = old_value
        self.new_value = new_value
    
    def set_position(self, page_number=None, row_index=None, column_index=None, coordinates=None):
        """设置位置信息"""
        self.page_number = page_number
        self.row_index = row_index
        self.column_index = column_index
        self.coordinates = coordinates
    
    def set_quality_assessment(self, error_type=None, severity=None, confidence_level=None):
        """设置质量评估信息"""
        self.error_type = error_type
        self.severity = severity
        self.confidence_level = confidence_level
    
    def get_change_summary(self):
        """获取变更摘要"""
        if self.action_type == 'create':
            return f'添加了 {self.review_type} 数据'
        elif self.action_type == 'delete':
            return f'删除了 {self.review_type} 数据'
        elif self.action_type == 'update':
            if self.field_name:
                return f'修改了 {self.field_name} 字段'
            return f'更新了 {self.review_type} 数据'
        elif self.action_type == 'correct':
            return f'校正了 {self.review_type} 识别错误'
        return f'{self.action_type} {self.review_type}'
    
    def get_coordinates_dict(self):
        """获取坐标字典"""
        if self.coordinates:
            return self.coordinates
        return None
    
    def is_structural_change(self):
        """判断是否为结构性变更"""
        return self.action_type in ['create', 'delete'] or self.review_type == 'table'
    
    def is_content_change(self):
        """判断是否为内容变更"""
        return self.action_type in ['update', 'correct']
    
    def get_error_severity_score(self):
        """获取错误严重程度分数"""
        severity_scores = {
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return severity_scores.get(self.severity, 0)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'reviewer_id': self.reviewer_id,
            'ocr_result_id': self.ocr_result_id,
            'review_type': self.review_type,
            'action_type': self.action_type,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'page_number': self.page_number,
            'row_index': self.row_index,
            'column_index': self.column_index,
            'coordinates': self.coordinates,
            'review_notes': self.review_notes,
            'confidence_level': self.confidence_level,
            'is_confirmed': self.is_confirmed,
            'error_type': self.error_type,
            'severity': self.severity,
            'review_duration': self.review_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'change_summary': self.get_change_summary(),
            'is_structural_change': self.is_structural_change(),
            'is_content_change': self.is_content_change(),
            'error_severity_score': self.get_error_severity_score()
        }
    
    @classmethod
    def get_review_statistics(cls, file_id=None, reviewer_id=None):
        """获取核对统计信息"""
        query = cls.query
        
        if file_id:
            query = query.filter_by(file_id=file_id)
        if reviewer_id:
            query = query.filter_by(reviewer_id=reviewer_id)
        
        records = query.all()
        
        stats = {
            'total_records': len(records),
            'by_action_type': {},
            'by_review_type': {},
            'by_error_type': {},
            'by_severity': {},
            'confirmed_count': 0,
            'structural_changes': 0,
            'content_changes': 0
        }
        
        for record in records:
            # 按操作类型统计
            stats['by_action_type'][record.action_type] = \
                stats['by_action_type'].get(record.action_type, 0) + 1
            
            # 按核对类型统计
            stats['by_review_type'][record.review_type] = \
                stats['by_review_type'].get(record.review_type, 0) + 1
            
            # 按错误类型统计
            if record.error_type:
                stats['by_error_type'][record.error_type] = \
                    stats['by_error_type'].get(record.error_type, 0) + 1
            
            # 按严重程度统计
            if record.severity:
                stats['by_severity'][record.severity] = \
                    stats['by_severity'].get(record.severity, 0) + 1
            
            # 其他统计
            if record.is_confirmed:
                stats['confirmed_count'] += 1
            if record.is_structural_change():
                stats['structural_changes'] += 1
            if record.is_content_change():
                stats['content_changes'] += 1
        
        return stats
    
    def __repr__(self):
        return f'<ReviewRecord {self.action_type} {self.review_type} by user {self.reviewer_id}>'
