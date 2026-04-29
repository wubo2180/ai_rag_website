"""
委托单文档和提取字段模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, BigInteger, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime

from . import db


class CommissionDocument(db.Model):
    """委托单文档表 - 存储PDF和MinIO信息"""
    __tablename__ = 'commission_documents'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    
    # PDF文件信息
    pdf_filename = Column(String(255), nullable=False, comment='PDF文件名')
    minio_object_name = Column(String(500), nullable=False, comment='MinIO对象名')
    minio_bucket = Column(String(100), nullable=False, comment='MinIO存储桶')
    file_size = Column(BigInteger, comment='文件大小(字节)')
    file_md5 = Column(String(32), comment='文件MD5值')
    page_count = Column(Integer, default=1, comment='页数')
    
    # JSON提取信息
    extraction_timestamp = Column(DateTime, comment='提取时间')
    
    # 关联的委托编号（如果能从JSON中提取）
    commission_number = Column(String(50), comment='委托编号')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系
    extracted_fields = relationship('CommissionExtractedField', back_populates='document', 
                                   cascade='all, delete-orphan', lazy='dynamic')
    statistics = relationship('CommissionStatistics', back_populates='document',
                            cascade='all, delete-orphan', lazy='dynamic')
    
    # 索引
    __table_args__ = (
        Index('idx_pdf_filename', 'pdf_filename'),
        Index('idx_commission_number', 'commission_number'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<CommissionDocument {self.pdf_filename}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'pdf_filename': self.pdf_filename,
            'minio_object_name': self.minio_object_name,
            'minio_bucket': self.minio_bucket,
            'file_size': self.file_size,
            'file_md5': self.file_md5,
            'page_count': self.page_count,
            'extraction_timestamp': self.extraction_timestamp.isoformat() if self.extraction_timestamp else None,
            'commission_number': self.commission_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class CommissionExtractedField(db.Model):
    """委托单提取字段表 - 存储JSON中提取的字段"""
    __tablename__ = 'commission_extracted_fields'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    document_id = Column(Integer, ForeignKey('commission_documents.id', ondelete='CASCADE'),
                        nullable=False, comment='文档ID')
    page_number = Column(Integer, nullable=False, comment='页码')
    
    # 字段信息
    field_name = Column(String(100), nullable=False, comment='字段名称')
    field_value = Column(Text, comment='字段值')
    field_type = Column(String(50), comment='字段类型')
    extraction_method = Column(String(100), comment='提取方法')
    
    # 置信度和来源
    confidence = Column(Float, comment='置信度')
    source_block_id = Column(String(100), comment='来源块ID')
    source_block_text = Column(Text, comment='来源块文本')
    bbox_json = Column(Text, comment='bbox信息(JSON)')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    document = relationship('CommissionDocument', back_populates='extracted_fields')
    
    # 索引
    __table_args__ = (
        Index('idx_document_id', 'document_id'),
        Index('idx_field_name', 'field_name'),
        Index('idx_page_number', 'page_number'),
    )
    
    def __repr__(self):
        return f'<CommissionExtractedField {self.field_name}={self.field_value}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'page_number': self.page_number,
            'field_name': self.field_name,
            'field_value': self.field_value,
            'field_type': self.field_type,
            'extraction_method': self.extraction_method,
            'confidence': self.confidence,
            'source_block_id': self.source_block_id,
            'source_block_text': self.source_block_text,
            'bbox_json': self.bbox_json,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class CommissionStatistics(db.Model):
    """委托单统计信息表 - 存储JSON中的统计数据"""
    __tablename__ = 'commission_statistics'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    document_id = Column(Integer, ForeignKey('commission_documents.id', ondelete='CASCADE'),
                        nullable=False, comment='文档ID')
    page_number = Column(Integer, nullable=False, comment='页码')
    
    # 统计数据
    source_content_blocks = Column(Integer, comment='内容块数')
    grid_cells_count = Column(Integer, comment='网格单元数')
    matched_cells_count = Column(Integer, comment='匹配单元数')
    total_fields_extracted = Column(Integer, comment='提取字段总数')
    
    # 字段类型统计
    single_cell_fields = Column(Integer, comment='单单元字段数')
    adjacent_cell_fields = Column(Integer, comment='相邻单元字段数')
    handwritten_fields = Column(Integer, comment='手写字段数')
    table_data_count = Column(Integer, comment='表格数据数')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    # 关系
    document = relationship('CommissionDocument', back_populates='statistics')
    
    # 索引
    __table_args__ = (
        Index('idx_document_id_stats', 'document_id'),
    )
    
    def __repr__(self):
        return f'<CommissionStatistics doc_id={self.document_id} page={self.page_number}>'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'page_number': self.page_number,
            'source_content_blocks': self.source_content_blocks,
            'grid_cells_count': self.grid_cells_count,
            'matched_cells_count': self.matched_cells_count,
            'total_fields_extracted': self.total_fields_extracted,
            'single_cell_fields': self.single_cell_fields,
            'adjacent_cell_fields': self.adjacent_cell_fields,
            'handwritten_fields': self.handwritten_fields,
            'table_data_count': self.table_data_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

