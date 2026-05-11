"""
OCR任务模型
用于异步OCR处理的任务队列
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from . import db


class OcrTask(db.Model):
    """OCR任务模型"""
    
    __tablename__ = 'ocr_tasks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False, comment='关联文件ID')
    task_id = Column(String(50), unique=True, nullable=False, comment='任务ID（UUID）')
    
    # 任务状态：pending/processing/completed/failed
    status = Column(String(20), default='pending', nullable=False, comment='任务状态')
    
    # 进度信息
    progress = Column(Integer, default=0, comment='进度百分比（0-100）')
    current_step = Column(String(100), nullable=True, comment='当前处理步骤')
    
    # 结果数据
    result = Column(JSON, nullable=True, comment='识别结果（JSON格式）')
    error_message = Column(Text, nullable=True, comment='错误信息')
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    started_at = Column(DateTime, nullable=True, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    
    # 请求用户
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, comment='请求用户ID')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'file_id': self.file_id,
            'task_id': self.task_id,
            'status': self.status,
            'progress': self.progress,
            'current_step': self.current_step,
            'result': self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }



