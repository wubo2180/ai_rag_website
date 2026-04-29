"""
论文材料和中间体数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import db


class PaperMaterialIntermediate(db.Model):
    """论文材料和中间体表（合并表）"""
    __tablename__ = 'paper_material_intermediates'
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    
    # 关联文献
    article_id = Column(String(50), 
                       ForeignKey('paper_articles.article_id', ondelete='CASCADE'), 
                       nullable=False, comment='关联的文献编号')
    
    # 实体类型
    entity_type = Column(String(20), default='material', nullable=False,
                        comment='实体类型：material(原材料)/intermediate(中间体)')
    
    # 材料信息
    material_id = Column(String(50), unique=True, nullable=False, 
                        comment='材料编号，如：A1M1')
    material_name = Column(Text, nullable=True, 
                          comment='原材料名称及规格')
    cas_number = Column(String(50), nullable=True, 
                       comment='CAS号')
    
    # 中间体信息
    intermediate_id = Column(String(50), nullable=True, 
                            comment='中间体编号，如：A1I1')
    intermediate_name = Column(Text, nullable=True, 
                              comment='中间体名称')
    intermediate_composition = Column(Text, nullable=True, 
                                     comment='中间体组成/配方')
    
    # 层级关系
    parent_id = Column(Integer, 
                      ForeignKey('paper_material_intermediates.id', ondelete='SET NULL'),
                      nullable=True, comment='父级ID（用于关联材料和中间体的关系）')
    sort_order = Column(Integer, default=0, comment='排序序号')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                       comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, 
                       onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    # article 关系在 PaperArticle 中定义（backref）
    parent = relationship('PaperMaterialIntermediate', 
                         remote_side=[id], 
                         backref='children',
                         lazy=True)
    properties = relationship('PaperProperty', 
                             backref='material_intermediate', 
                             lazy='dynamic',
                             cascade='all, delete-orphan',
                             foreign_keys='PaperProperty.material_intermediate_id')
    
    def __repr__(self):
        return f'<PaperMaterialIntermediate {self.material_id}: {self.material_name[:20] if self.material_name else "N/A"}>'
    
    def to_dict(self, include_properties=False):
        """转换为字典"""
        result = {
            'id': self.id,
            'article_id': self.article_id,
            'entity_type': self.entity_type,
            'material_id': self.material_id,
            'material_name': self.material_name,
            'cas_number': self.cas_number,
            'intermediate_id': self.intermediate_id,
            'intermediate_name': self.intermediate_name,
            'intermediate_composition': self.intermediate_composition,
            'parent_id': self.parent_id,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        
        # 包含性能数据
        if include_properties:
            result['properties'] = [
                prop.to_dict() 
                for prop in self.properties.order_by('sort_order').all()
            ]
        
        return result



