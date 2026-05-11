"""
模型配置数据模型
"""
from models import db
from datetime import datetime


class ModelConfig(db.Model):
    """OCR模型配置"""
    __tablename__ = 'model_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, comment='模型名称')
    api_url = db.Column(db.String(500), nullable=False, comment='API地址')
    file_type = db.Column(db.String(50), comment='文件类型（如：pdf, image, word等）')
    description = db.Column(db.Text, comment='模型描述')
    config_params = db.Column(db.JSON, comment='额外配置参数')
    is_default = db.Column(db.Boolean, default=False, comment='是否为默认模型')
    is_active = db.Column(db.Boolean, default=True, comment='是否启用')
    timeout = db.Column(db.Integer, default=120, comment='超时时间（秒）')
    created_by = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'api_url': self.api_url,
            'file_type': self.file_type,
            'description': self.description,
            'config_params': self.config_params,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'timeout': self.timeout,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

