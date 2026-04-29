"""
文件模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, BigInteger, ForeignKey

# 从上级模块导入db实例
from . import db


class File(db.Model):
    """文件模型"""
    
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False, comment='原始文件名')
    stored_filename = Column(String(255), nullable=False, comment='存储文件名（UUID）')
    file_path = Column(String(500), nullable=False, comment='MinIO中的文件路径')
    file_size = Column(BigInteger, nullable=False, comment='文件大小（字节）')
    file_type = Column(String(50), nullable=False, comment='文件格式类型（pdf/jpg等）')
    # 新增：文档业务类型
    document_type_code = Column(String(50), nullable=True, comment='文档类型代码（commission/paper等）')
    mime_type = Column(String(100), nullable=False, comment='MIME类型')
    md5_hash = Column(String(32), nullable=True, comment='文件MD5哈希')
    
    # 上传信息
    uploader_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='上传用户ID')
    upload_batch_id = Column(String(36), nullable=True, comment='批量上传批次ID')
    
    # OCR处理状态
    ocr_status = Column(String(20), default='pending', comment='OCR处理状态：pending/processing/completed/failed')
    ocr_started_at = Column(DateTime, nullable=True, comment='OCR开始时间')
    ocr_completed_at = Column(DateTime, nullable=True, comment='OCR完成时间')
    ocr_error_message = Column(Text, nullable=True, comment='OCR错误信息')
    
    # 核对状态
    review_status = Column(String(20), default='unassigned', comment='核对状态：unassigned/assigned/in_progress/completed')
    review_started_at = Column(DateTime, nullable=True, comment='核对开始时间')
    review_completed_at = Column(DateTime, nullable=True, comment='核对完成时间')
    
    # 元数据
    page_count = Column(Integer, nullable=True, comment='页数')
    description = Column(Text, nullable=True, comment='文件描述')
    tags = Column(String(500), nullable=True, comment='标签（逗号分隔）')
    
    # 状态标识
    is_deleted = Column(Boolean, default=False, comment='是否已删除')
    is_processed = Column(Boolean, default=False, comment='是否已处理')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    deleted_at = Column(DateTime, nullable=True, comment='删除时间')
    
    # 关系
    uploader = db.relationship('User', backref='uploaded_files', lazy=True)
    ocr_results = db.relationship('OCRResult', backref='file', lazy=True, cascade='all, delete-orphan')
    review_records = db.relationship('ReviewRecord', backref='file', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('FileAssignment', backref='file', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, filename, stored_filename, file_path, file_size, file_type, 
                 mime_type, uploader_id, upload_batch_id=None, document_type_code=None):
        self.filename = filename
        self.stored_filename = stored_filename
        self.file_path = file_path
        self.file_size = file_size
        self.file_type = file_type
        self.mime_type = mime_type
        self.uploader_id = uploader_id
        self.upload_batch_id = upload_batch_id
        self.document_type_code = document_type_code  # 新增
    
    def get_tags_list(self):
        """获取标签列表"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def set_tags_list(self, tags_list):
        """设置标签列表"""
        if tags_list:
            self.tags = ','.join([str(tag).strip() for tag in tags_list])
        else:
            self.tags = None
    
    def get_file_extension(self):
        """获取文件扩展名"""
        return self.filename.rsplit('.', 1)[-1].lower() if '.' in self.filename else ''
    
    def get_display_size(self):
        """获取可读的文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.file_size < 1024.0:
                return f"{self.file_size:.1f} {unit}"
            self.file_size /= 1024.0
        return f"{self.file_size:.1f} TB"
    
    def soft_delete(self):
        """软删除文件"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
    
    def restore(self):
        """恢复已删除的文件"""
        self.is_deleted = False
        self.deleted_at = None
    
    def update_ocr_status(self, status, error_message=None):
        """更新OCR状态"""
        self.ocr_status = status
        if status == 'processing':
            self.ocr_started_at = datetime.utcnow()
        elif status in ['completed', 'failed']:
            self.ocr_completed_at = datetime.utcnow()
            if error_message:
                self.ocr_error_message = error_message
    
    def update_review_status(self, status):
        """更新核对状态"""
        self.review_status = status
        if status == 'in_progress':
            self.review_started_at = datetime.utcnow()
        elif status == 'completed':
            self.review_completed_at = datetime.utcnow()
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'stored_filename': self.stored_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_display': self.get_display_size(),
            'file_type': self.file_type,
            'document_type_code': self.document_type_code,  # 新增
            'mime_type': self.mime_type,
            'md5_hash': self.md5_hash,
            'uploader_id': self.uploader_id,
            'upload_batch_id': self.upload_batch_id,
            'ocr_status': self.ocr_status,
            'ocr_started_at': self.ocr_started_at.isoformat() if self.ocr_started_at else None,
            'ocr_completed_at': self.ocr_completed_at.isoformat() if self.ocr_completed_at else None,
            'ocr_error_message': self.ocr_error_message,
            'review_status': self.review_status,
            'review_started_at': self.review_started_at.isoformat() if self.review_started_at else None,
            'review_completed_at': self.review_completed_at.isoformat() if self.review_completed_at else None,
            'page_count': self.page_count,
            'description': self.description,
            'tags': self.get_tags_list(),
            'is_deleted': self.is_deleted,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None
        }
    
    def __repr__(self):
        return f'<File {self.filename}>'
