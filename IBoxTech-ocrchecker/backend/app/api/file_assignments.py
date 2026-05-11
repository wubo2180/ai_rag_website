"""
文件分配相关API
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from . import api_bp
from models import db
from models.file import File
from models.file_assignment import FileAssignment
from models.user import User
from datetime import datetime


@api_bp.route('/files/batch-assign', methods=['POST'])
@jwt_required()
def batch_assign_files():
    """批量分配文件给核对人员"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        print(f"\n{'='*60}")
        print(f"[批量分配] 收到请求")
        print(f"  当前用户ID: {current_user_id}")
        print(f"  请求数据: {data}")
        print(f"{'='*60}\n")
        
        # 验证必填字段
        file_ids = data.get('file_ids', [])
        assignee_id = data.get('assignee_id')
        
        print(f"[批量分配] 文件ID列表: {file_ids}")
        print(f"[批量分配] 审核人ID: {assignee_id}")
        
        if not file_ids:
            print(f"[批量分配] 错误: 没有选择文件")
            return jsonify({
                'success': False,
                'message': '请选择要分配的文件'
            }), 400
        
        if not assignee_id:
            print(f"[批量分配] 错误: 没有选择审核人")
            return jsonify({
                'success': False,
                'message': '请选择核对人员'
            }), 400
        
        # 检查核对人员是否存在
        assignee = User.query.get(assignee_id)
        if not assignee:
            print(f"[批量分配] 错误: 审核人不存在 (ID: {assignee_id})")
            return jsonify({
                'success': False,
                'message': '核对人员不存在'
            }), 404
        
        print(f"[批量分配] 审核人: {assignee.username}")
        
        # 获取其他参数
        priority = data.get('priority', 'normal')
        notes = data.get('notes', '')
        
        print(f"[批量分配] 优先级: {priority}")
        print(f"[批量分配] 备注: {notes}")
        
        # 批量创建分配记录
        successful_assignments = []
        failed_assignments = []
        
        for file_id in file_ids:
            try:
                print(f"\n[批量分配] 处理文件ID: {file_id}")
                
                # 检查文件是否存在
                file = File.query.get(file_id)
                if not file:
                    print(f"  ❌ 文件不存在")
                    failed_assignments.append({
                        'file_id': file_id,
                        'reason': '文件不存在'
                    })
                    continue
                
                print(f"  文件名: {file.filename}")
                
                # 检查是否已经分配给该用户
                existing_assignment = FileAssignment.query.filter_by(
                    file_id=file_id,
                    assigned_to=assignee_id
                ).filter(
                    FileAssignment.status.in_(['assigned', 'in_progress', 'pending'])
                ).first()
                
                if existing_assignment:
                    print(f"  ⚠️  已分配给该用户")
                    failed_assignments.append({
                        'file_id': file_id,
                        'filename': file.filename,
                        'reason': '已分配给该用户'
                    })
                    continue
                
                # 创建分配记录
                print(f"  创建分配记录...")
                assignment = FileAssignment(
                    file_id=file_id,
                    assigned_by=current_user_id,
                    assigned_to=assignee_id,
                    assignment_type='review',
                    priority=priority,
                    assignment_notes=notes
                )
                
                db.session.add(assignment)
                print(f"  已添加到session")
                
                # 更新文件的核对状态
                if file.review_status == 'unassigned':
                    file.review_status = 'assigned'
                    print(f"  更新文件状态: unassigned -> assigned")
                
                successful_assignments.append({
                    'file_id': file_id,
                    'filename': file.filename
                })
                print(f"  ✅ 成功")
                
            except Exception as e:
                print(f"  ❌ 异常: {str(e)}")
                import traceback
                traceback.print_exc()
                failed_assignments.append({
                    'file_id': file_id,
                    'reason': str(e)
                })
        
        # 提交数据库更改
        print(f"\n[批量分配] 提交到数据库...")
        db.session.commit()
        print(f"[批量分配] ✅ 数据库提交成功")
        
        print(f"[批量分配] 成功: {len(successful_assignments)}, 失败: {len(failed_assignments)}")
        
        return jsonify({
            'success': True,
            'message': f'成功分配 {len(successful_assignments)} 个文件',
            'data': {
                'successful_count': len(successful_assignments),
                'failed_count': len(failed_assignments),
                'successful_assignments': successful_assignments,
                'failed_assignments': failed_assignments,
                'assignee': {
                    'id': assignee.id,
                    'username': assignee.username,
                    'real_name': assignee.real_name,
                    'email': assignee.email
                }
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"\n[批量分配] ❌ 总体失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'批量分配失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/assign', methods=['POST'])
@jwt_required()
def assign_file(file_id):
    """分配单个文件给核对人员"""
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        assignee_id = data.get('assignee_id')
        if not assignee_id:
            return jsonify({
                'success': False,
                'message': '请选择核对人员'
            }), 400
        
        # 检查文件是否存在
        file = File.query.get(file_id)
        if not file:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 检查核对人员是否存在
        assignee = User.query.get(assignee_id)
        if not assignee:
            return jsonify({
                'success': False,
                'message': '核对人员不存在'
            }), 404
        
        # 检查是否已经分配给该用户
        existing_assignment = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=assignee_id,
            status='pending'
        ).first()
        
        if existing_assignment:
            return jsonify({
                'success': False,
                'message': '该文件已分配给该用户'
            }), 400
        
        # 创建分配记录
        assignment = FileAssignment(
            file_id=file_id,
            assigned_to=assignee_id,
            assigned_by=current_user_id,
            priority=data.get('priority', 'normal'),
            notes=data.get('notes', '')
        )
        
        db.session.add(assignment)
        
        # 更新文件的核对状态
        if file.review_status == 'unassigned':
            file.review_status = 'assigned'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '文件分配成功',
            'data': {
                'assignment_id': assignment.id,
                'file': file.to_dict(),
                'assignee': assignee.to_dict()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'文件分配失败: {str(e)}'
        }), 500

