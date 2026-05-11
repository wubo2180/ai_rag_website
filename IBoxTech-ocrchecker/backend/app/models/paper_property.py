"""
论文性能数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import db


class PaperProperty(db.Model):
    """论文性能数据表"""
    __tablename__ = 'paper_properties'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联材料/中间体
    material_intermediate_id = Column(
        Integer, 
        ForeignKey('paper_material_intermediates.id', ondelete='CASCADE'), 
        nullable=False, 
        comment='关联的材料/中间体ID'
    )
    
    # 冗余字段（优化查询）
    article_id = Column(
        String(50), 
        ForeignKey('paper_articles.article_id', ondelete='CASCADE'), 
        nullable=False, 
        comment='关联的文献编号（冗余字段，便于查询）'
    )
    
    # 性能信息
    property_id = Column(String(50), unique=True, nullable=False, 
                        comment='性能编号，如：A1P1')
    property_name = Column(String(200), nullable=False, 
                          comment='性能名称，如：粘度/黏度 MPa·S')
    property_value = Column(String(500), nullable=True, 
                           comment='性能值')
    property_unit = Column(String(50), nullable=True, 
                          comment='单位（可选，从property_name中提取）')
    
    # 排序
    sort_order = Column(Integer, default=0, comment='排序序号')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                       comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    # material_intermediate 关系在 PaperMaterialIntermediate 中定义（backref）
    # article 关系在 PaperArticle 中定义（backref）
    
    def __repr__(self):
        return f'<PaperProperty {self.property_id}: {self.property_name}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'material_intermediate_id': self.material_intermediate_id,
            'article_id': self.article_id,
            'property_id': self.property_id,
            'property_name': self.property_name,
            'property_value': self.property_value,
            'property_unit': self.property_unit,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }



