"""
论文文献数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import db


class PaperArticle(db.Model):
    """论文文献表"""
    __tablename__ = 'paper_articles'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联文件
    file_id = Column(Integer, ForeignKey('files.id', ondelete='CASCADE'), 
                     nullable=False, comment='关联的文件ID')
    
    # 文献基本信息
    article_id = Column(String(50), unique=True, nullable=False, 
                       comment='文献编号，如：A1')
    article_name = Column(Text, nullable=False, 
                         comment='文献名称/标题')
    performance_trend = Column(Text, nullable=True, 
                              comment='性能趋势描述')
    
    # 审核状态
    status = Column(String(20), default='pending', 
                   comment='数据状态：pending/completed/failed')
    review_status = Column(String(20), default='pending', 
                          comment='审核状态：pending/approved/rejected')
    reviewer_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), 
                        nullable=True, comment='审核人ID')
    reviewed_at = Column(DateTime, nullable=True, comment='审核时间')
    review_comments = Column(Text, nullable=True, comment='审核意见')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                       comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    file = relationship('File', backref='paper_articles', lazy=True)
    reviewer = relationship('User', backref='reviewed_papers', lazy=True)
    material_intermediates = relationship('PaperMaterialIntermediate', 
                                         backref='article', 
                                         lazy='dynamic',
                                         cascade='all, delete-orphan',
                                         foreign_keys='PaperMaterialIntermediate.article_id')
    properties = relationship('PaperProperty', 
                             backref='article', 
                             lazy='dynamic',
                             cascade='all, delete-orphan',
                             foreign_keys='PaperProperty.article_id')
    
    def __repr__(self):
        return f'<PaperArticle {self.article_id}: {self.article_name[:30]}...>'
    
    def to_dict(self, include_details=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'file_id': self.file_id,
            'article_id': self.article_id,
            'article_name': self.article_name,
            'performance_trend': self.performance_trend,
            'status': self.status,
            'review_status': self.review_status,
            'reviewer_id': self.reviewer_id,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_comments': self.review_comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 包含详细的材料和性能数据
        if include_details:
            result['material_intermediates'] = [
                mi.to_dict(include_properties=True) 
                for mi in self.material_intermediates.order_by('sort_order').all()
            ]
        
        return result
    
    def to_hierarchical_dict(self):
        """
        转换为层次化字典（符合前端JSON格式）
        """
        material_intermediates_list = []
        
        for mi in self.material_intermediates.order_by('sort_order').all():
            mi_data = {
                '材料编号（Material ID）': mi.material_id,
                '原材料名称（Material Name）': mi.material_name or '',
                'CAS号（CAS Number）': mi.cas_number or '',
                '中间体编号（Intermediate ID）': mi.intermediate_id or '',
                '中间体名称（Intermediate Name）': mi.intermediate_name or '',
                '中间体组成（Intermediate Compositions）': mi.intermediate_composition or '',
                '性能（Properties）': [
                    {
                        '性能编号（Property ID）': prop.property_id,
                        '性能名称（Property Name）': prop.property_name,
                        '性能值（Property Value）': prop.property_value or ''
                    }
                    for prop in mi.properties.order_by('sort_order').all()
                ]
            }
            material_intermediates_list.append(mi_data)
        
        return {
            '文献编号（Article ID）': self.article_id,
            '文献名称（Article Name）': self.article_name,
            '四级数据连接（4-level Data Linkage）': material_intermediates_list,
            '性能趋势': self.performance_trend or ''
        }



