"""
用户模型
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, DateTime, Boolean

# 从上级模块导入db实例
from . import db


class User(db.Model):
    """用户模型"""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, comment='用户名')
    email = Column(String(100), unique=True, nullable=False, comment='邮箱')
    password_hash = Column(String(255), nullable=False, comment='密码哈希')
    real_name = Column(String(50), nullable=True, comment='真实姓名')
    role = Column(String(20), nullable=False, default='user', comment='用户角色：admin/user')
    is_active = Column(Boolean, default=True, comment='是否激活')
    avatar_url = Column(String(255), nullable=True, comment='头像URL')
    last_login_at = Column(DateTime, nullable=True, comment='最后登录时间')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系 - 明确指定外键避免冲突
    # 作为分派对象的文件分配记录
    assigned_files = db.relationship('FileAssignment', 
                                   foreign_keys='FileAssignment.assigned_to',
                                   backref='assignee_user', lazy=True)
    # 作为分派人的文件分配记录  
    created_assignments = db.relationship('FileAssignment',
                                        foreign_keys='FileAssignment.assigned_by', 
                                        backref='assigner_user', lazy=True)
    # 核对记录关系
    review_records = db.relationship('ReviewRecord', backref='reviewer', lazy=True)
    
    def __init__(self, username, email, password, real_name=None, role='user', is_active=True):
        self.username = username
        self.email = email
        self.set_password(password)
        self.real_name = real_name
        self.role = role
        self.is_active = is_active
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """判断是否为管理员"""
        return self.role == 'admin'
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'role': self.role,
            'is_active': self.is_active,
            'avatar_url': self.avatar_url,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'
