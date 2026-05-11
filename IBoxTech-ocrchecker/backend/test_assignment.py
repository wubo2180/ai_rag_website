#!/usr/bin/env python3
"""测试文件分配功能"""
import sys
sys.path.insert(0, '/home/h3c/workspace/IBoxTech-ocrchecker/backend')

# 直接导入app
from app import app
from app.models import db
from app.models.file import File
from app.models.file_assignment import FileAssignment
from app.models.user import User

with app.app_context():
    print("=== 检查数据 ===\n")
    
    # 检查用户
    users = User.query.all()
    print(f"用户总数: {len(users)}")
    for u in users:
        print(f"  - ID: {u.id}, 用户名: {u.username}, 角色: {u.role}")
    
    # 检查文件
    files = File.query.filter_by(is_deleted=False).limit(5).all()
    print(f"\n文件总数（前5个）: {len(files)}")
    for f in files:
        print(f"  - ID: {f.id}, 文件名: {f.filename}, 上传者ID: {f.uploader_id}")
    
    # 检查分配记录
    assignments = FileAssignment.query.all()
    print(f"\n分配记录总数: {len(assignments)}")
    for a in assignments:
        file = File.query.get(a.file_id)
        assignee = User.query.get(a.assigned_to)
        assigner = User.query.get(a.assigned_by)
        print(f"  - 分配ID: {a.id}")
        print(f"    文件: {file.filename if file else '未找到'}")
        print(f"    分配给: {assignee.username if assignee else '未找到'} (ID: {a.assigned_to})")
        print(f"    分配人: {assigner.username if assigner else '未找到'} (ID: {a.assigned_by})")
        print(f"    状态: {a.status}")
    
    # 测试创建一个分配记录
    if len(users) >= 2 and len(files) > 0:
        print("\n=== 测试创建分配记录 ===")
        admin = next((u for u in users if u.is_admin()), None)
        regular_user = next((u for u in users if not u.is_admin()), None)
        
        if admin and regular_user:
            test_file = files[0]
            print(f"尝试将文件 '{test_file.filename}' 分配给用户 '{regular_user.username}'")
            
            # 检查是否已经存在
            existing = FileAssignment.query.filter_by(
                file_id=test_file.id,
                assigned_to=regular_user.id
            ).first()
            
            if existing:
                print(f"  已存在分配记录: ID={existing.id}, 状态={existing.status}")
            else:
                try:
                    assignment = FileAssignment(
                        file_id=test_file.id,
                        assigned_by=admin.id,
                        assigned_to=regular_user.id,
                        assignment_type='review',
                        priority='normal',
                        assignment_notes='测试分配'
                    )
                    db.session.add(assignment)
                    db.session.commit()
                    print(f"  ✅ 成功创建分配记录: ID={assignment.id}")
                except Exception as e:
                    db.session.rollback()
                    print(f"  ❌ 创建失败: {e}")
        else:
            print("  无法找到管理员或普通用户")
    
    print("\n=== 测试文件查询逻辑 ===")
    if len(users) > 0:
        test_user = users[-1]  # 取最后一个用户
        print(f"测试用户: {test_user.username} (ID: {test_user.id})")
        
        # 查询分配给该用户的文件
        assigned_file_ids = db.session.query(FileAssignment.file_id).filter(
            FileAssignment.assigned_to == test_user.id,
            FileAssignment.status.in_(['assigned', 'in_progress'])
        ).distinct().all()
        
        file_ids = [f[0] for f in assigned_file_ids]
        print(f"分配给该用户的文件ID: {file_ids}")
        
        # 查询该用户上传的文件
        uploaded_files = File.query.filter_by(
            uploader_id=test_user.id,
            is_deleted=False
        ).limit(5).all()
        
        print(f"该用户上传的文件: {[f.filename for f in uploaded_files]}")

