"""
文件分派模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean

# 从上级模块导入db实例
from . import db


class FileAssignment(db.Model):
    """文件分派模型"""
    
    __tablename__ = 'file_assignments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(Integer, ForeignKey('files.id'), nullable=False, comment='关联文件ID')
    assigned_by = Column(Integer, ForeignKey('users.id'), nullable=False, comment='分派人ID（管理员）')
    assigned_to = Column(Integer, ForeignKey('users.id'), nullable=False, comment='被分派人ID（普通用户）')
    
    # 分派信息
    assignment_type = Column(String(20), default='review', comment='分派类型：review/verify/correct')
    priority = Column(String(10), default='medium', comment='优先级：high/medium/low')
    
    # 状态管理
    status = Column(String(20), default='assigned', comment='状态：assigned/in_progress/completed/cancelled')
    
    # 时间管理
    assigned_at = Column(DateTime, default=datetime.utcnow, comment='分派时间')
    due_date = Column(DateTime, nullable=True, comment='截止时间')
    started_at = Column(DateTime, nullable=True, comment='开始时间')
    completed_at = Column(DateTime, nullable=True, comment='完成时间')
    cancelled_at = Column(DateTime, nullable=True, comment='取消时间')
    
    # 工作信息
    estimated_duration = Column(Integer, nullable=True, comment='预估耗时（分钟）')
    actual_duration = Column(Integer, nullable=True, comment='实际耗时（分钟）')
    
    # 说明和反馈
    assignment_notes = Column(Text, nullable=True, comment='分派说明')
    completion_notes = Column(Text, nullable=True, comment='完成说明')
    feedback = Column(Text, nullable=True, comment='反馈意见')
    
    # 质量控制
    quality_score = Column(Integer, nullable=True, comment='质量评分（1-5）')
    is_approved = Column(Boolean, nullable=True, comment='是否批准')
    approved_by = Column(Integer, ForeignKey('users.id'), nullable=True, comment='批准人ID')
    approved_at = Column(DateTime, nullable=True, comment='批准时间')
    
    # 重新分派记录
    reassignment_count = Column(Integer, default=0, comment='重新分派次数')
    previous_assignee = Column(Integer, ForeignKey('users.id'), nullable=True, comment='前一个分派人ID')
    
    # 关系 - 不使用backref避免冲突，User模型中已定义相关关系
    assigner = db.relationship('User', foreign_keys=[assigned_by], 
                              overlaps="assigner_user,created_assignments")
    assignee = db.relationship('User', foreign_keys=[assigned_to],
                              overlaps="assigned_files,assignee_user")
    approver = db.relationship('User', foreign_keys=[approved_by])
    prev_assignee = db.relationship('User', foreign_keys=[previous_assignee])
    
    def __init__(self, file_id, assigned_by, assigned_to, assignment_type='review', 
                 priority='medium', assignment_notes=None, due_date=None):
        self.file_id = file_id
        self.assigned_by = assigned_by
        self.assigned_to = assigned_to
        self.assignment_type = assignment_type
        self.priority = priority
        self.assignment_notes = assignment_notes
        self.due_date = due_date
    
    def start_work(self):
        """开始工作"""
        if self.status == 'assigned':
            self.status = 'in_progress'
            self.started_at = datetime.utcnow()
    
    def complete_work(self, completion_notes=None, actual_duration=None):
        """完成工作"""
        self.status = 'completed'
        self.completed_at = datetime.utcnow()
        if completion_notes:
            self.completion_notes = completion_notes
        if actual_duration:
            self.actual_duration = actual_duration
        elif self.started_at:
            # 自动计算耗时
            duration = datetime.utcnow() - self.started_at
            self.actual_duration = int(duration.total_seconds() / 60)  # 转换为分钟
    
    def cancel_assignment(self, reason=None):
        """取消分派"""
        self.status = 'cancelled'
        self.cancelled_at = datetime.utcnow()
        if reason:
            self.completion_notes = f'取消原因: {reason}'
    
    def reassign(self, new_assignee_id, assigner_id, reason=None):
        """重新分派"""
        self.previous_assignee = self.assigned_to
        self.assigned_to = new_assignee_id
        self.assigned_by = assigner_id
        self.reassignment_count += 1
        self.status = 'assigned'
        self.started_at = None
        self.assigned_at = datetime.utcnow()
        
        if reason:
            note = f'重新分派原因: {reason}'
            if self.assignment_notes:
                self.assignment_notes += f'\n{note}'
            else:
                self.assignment_notes = note
    
    def set_quality_score(self, score, feedback=None):
        """设置质量评分"""
        if 1 <= score <= 5:
            self.quality_score = score
            if feedback:
                self.feedback = feedback
    
    def approve(self, approver_id, feedback=None):
        """批准完成"""
        self.is_approved = True
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        if feedback:
            self.feedback = feedback
    
    def reject(self, approver_id, feedback=None):
        """拒绝完成"""
        self.is_approved = False
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        self.status = 'assigned'  # 重新分派状态
        if feedback:
            self.feedback = feedback
    
    def is_overdue(self):
        """检查是否过期"""
        if self.due_date and self.status not in ['completed', 'cancelled']:
            return datetime.utcnow() > self.due_date
        return False
    
    def get_duration_display(self):
        """获取耗时显示"""
        if self.actual_duration:
            hours = self.actual_duration // 60
            minutes = self.actual_duration % 60
            if hours > 0:
                return f'{hours}小时{minutes}分钟'
            return f'{minutes}分钟'
        return None
    
    def get_priority_display(self):
        """获取优先级显示"""
        priority_map = {
            'high': '高',
            'medium': '中',
            'low': '低'
        }
        return priority_map.get(self.priority, self.priority)
    
    def get_status_display(self):
        """获取状态显示"""
        status_map = {
            'assigned': '已分派',
            'in_progress': '进行中',
            'completed': '已完成',
            'cancelled': '已取消'
        }
        return status_map.get(self.status, self.status)
    
    def get_progress_percentage(self):
        """获取进度百分比"""
        if self.status == 'completed':
            return 100
        elif self.status == 'in_progress':
            # 基于时间的简单进度计算
            if self.started_at and self.due_date:
                total_duration = self.due_date - self.assigned_at
                elapsed_duration = datetime.utcnow() - self.started_at
                progress = min((elapsed_duration / total_duration) * 100, 95)
                return round(progress)
            return 50
        elif self.status == 'assigned':
            return 0
        return 0
    
    def to_dict(self, include_relations=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'file_id': self.file_id,
            'assigned_by': self.assigned_by,
            'assigned_to': self.assigned_to,
            'assignment_type': self.assignment_type,
            'priority': self.priority,
            'priority_display': self.get_priority_display(),
            'status': self.status,
            'status_display': self.get_status_display(),
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cancelled_at': self.cancelled_at.isoformat() if self.cancelled_at else None,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'duration_display': self.get_duration_display(),
            'assignment_notes': self.assignment_notes,
            'completion_notes': self.completion_notes,
            'feedback': self.feedback,
            'quality_score': self.quality_score,
            'is_approved': self.is_approved,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'reassignment_count': self.reassignment_count,
            'previous_assignee': self.previous_assignee,
            'is_overdue': self.is_overdue(),
            'progress_percentage': self.get_progress_percentage()
        }
        
        if include_relations:
            # 可以添加关联的用户和文件信息
            pass
        
        return data
    
    @classmethod
    def get_assignment_statistics(cls, user_id=None, file_id=None):
        """获取分派统计信息"""
        query = cls.query
        
        if user_id:
            query = query.filter_by(assigned_to=user_id)
        if file_id:
            query = query.filter_by(file_id=file_id)
        
        assignments = query.all()
        
        stats = {
            'total': len(assignments),
            'by_status': {},
            'by_priority': {},
            'overdue_count': 0,
            'avg_duration': 0,
            'completed_count': 0,
            'avg_quality_score': 0
        }
        
        total_duration = 0
        total_quality_scores = []
        
        for assignment in assignments:
            # 按状态统计
            stats['by_status'][assignment.status] = \
                stats['by_status'].get(assignment.status, 0) + 1
            
            # 按优先级统计
            stats['by_priority'][assignment.priority] = \
                stats['by_priority'].get(assignment.priority, 0) + 1
            
            # 过期统计
            if assignment.is_overdue():
                stats['overdue_count'] += 1
            
            # 耗时统计
            if assignment.actual_duration:
                total_duration += assignment.actual_duration
            
            # 完成统计
            if assignment.status == 'completed':
                stats['completed_count'] += 1
                if assignment.quality_score:
                    total_quality_scores.append(assignment.quality_score)
        
        # 计算平均值
        if stats['completed_count'] > 0:
            stats['avg_duration'] = round(total_duration / stats['completed_count'])
        
        if total_quality_scores:
            stats['avg_quality_score'] = round(sum(total_quality_scores) / len(total_quality_scores), 2)
        
        return stats
    
    def __repr__(self):
        return f'<FileAssignment file_id={self.file_id} assignee={self.assigned_to}>'
