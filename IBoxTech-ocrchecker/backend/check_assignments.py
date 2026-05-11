#!/usr/bin/env python3
"""检查文件分配记录"""
import sys
sys.path.insert(0, '/home/h3c/workspace/IBoxTech-ocrchecker/backend')

from app.models import db
from app.models.file_assignment import FileAssignment
from app.models.file import File
from app.models.user import User
from app.app import create_app

app = create_app()

with app.app_context():
    print("=== 文件分配记录 ===")
    assignments = FileAssignment.query.all()
    print(f'总分配记录数: {len(assignments)}\n')
    
    for a in assignments[:10]:
        assignee = User.query.get(a.assigned_to)
        assigner = User.query.get(a.assigned_by)
        file = File.query.get(a.file_id)
        
        print(f'分配ID: {a.id}')
        print(f'  文件: {file.filename if file else "未找到"}')
        print(f'  分配给: {assignee.username if assignee else "未找到"} (ID: {a.assigned_to})')
        print(f'  分配人: {assigner.username if assigner else "未找到"} (ID: {a.assigned_by})')
        print(f'  状态: {a.status}')
        print(f'  优先级: {a.priority}')
        print('-' * 60)
    
    print("\n=== 用户列表 ===")
    users = User.query.all()
    for u in users:
        print(f'用户ID: {u.id}, 用户名: {u.username}, 角色: {u.role}')

