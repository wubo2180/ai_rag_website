"""
文件管理相关API
"""
from flask import request, jsonify, send_file, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from io import BytesIO
from datetime import datetime
import uuid
from . import api_bp
from models import db
from models.user import User
from services.file_service import FileService
from utils.decorators import admin_required


@api_bp.route('/files/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """单个文件上传"""
    try:
        current_user_id = get_jwt_identity()
        
        # 检查是否有文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        # 获取额外参数
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else None
        document_type_code = request.form.get('document_type_code')  # 新增：文档类型代码
        
        # 处理文件名
        original_filename = file.filename
        filename = secure_filename(file.filename)
        
        # 检查secure_filename是否移除了扩展名
        if not filename or '.' not in filename:
            print(f"[单文件上传] ⚠️  警告: secure_filename处理后文件名无效")
            print(f"  原始文件名: {original_filename}")
            print(f"  处理后: {filename}")
            # 如果secure_filename把文件名处理坏了，使用原始文件名
            filename = original_filename
        
        # 使用文件服务上传
        file_service = FileService()
        result = file_service.upload_file(
            file_obj=file,
            filename=filename,
            uploader_id=current_user_id,
            description=description,
            tags=tags,
            document_type_code=document_type_code  # 新增
        )
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'文件上传失败: {str(e)}'
        }), 500


@api_bp.route('/files/batch-upload', methods=['POST'])
@jwt_required()
def batch_upload_files():
    """批量文件上传"""
    try:
        current_user_id = get_jwt_identity()
        
        print(f"\n{'='*80}")
        print(f"[批量上传] 开始处理批量上传请求")
        print(f"[批量上传] 当前用户ID: {current_user_id}")
        print(f"{'='*80}\n")
        
        # 检查是否有文件
        if 'files' not in request.files:
            print(f"[批量上传] ❌ 错误: request.files中没有'files'字段")
            print(f"[批量上传] request.files的keys: {list(request.files.keys())}")
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        files = request.files.getlist('files')
        print(f"[批量上传] 接收到 {len(files)} 个文件")
        
        if not files or all(f.filename == '' for f in files):
            print(f"[批量上传] ❌ 错误: 文件列表为空或所有文件名为空")
            return jsonify({
                'success': False,
                'message': '没有选择文件'
            }), 400
        
        # 获取额外参数
        description = request.form.get('description')
        tags = request.form.get('tags', '').split(',') if request.form.get('tags') else None
        document_type_code = request.form.get('document_type_code')  # 新增：文档类型代码
        
        print(f"[批量上传] 请求参数:")
        print(f"  - description: {description}")
        print(f"  - tags: {tags}")
        print(f"  - document_type_code: {document_type_code}")
        print(f"  - request.form所有字段: {dict(request.form)}")
        
        # 准备文件数据
        files_data = []
        for file in files:
            if file.filename:
                original_filename = file.filename
                filename = secure_filename(file.filename)
                
                # 检查secure_filename是否移除了扩展名
                if not filename or '.' not in filename:
                    print(f"[批量上传] ⚠️  警告: secure_filename处理后文件名无效")
                    print(f"    原始文件名: {original_filename}")
                    print(f"    处理后: {filename}")
                    # 如果secure_filename把文件名处理坏了，使用原始文件名
                    filename = original_filename
                
                files_data.append({
                    'file_obj': file,
                    'filename': filename
                })
                print(f"[批量上传] 处理文件: {filename} (原始名: {original_filename})")
        
        if not files_data:
            print(f"[批量上传] ❌ 错误: 没有有效的文件")
            return jsonify({
                'success': False,
                'message': '没有有效的文件'
            }), 400
        
        print(f"[批量上传] 准备上传 {len(files_data)} 个有效文件")
        
        # 使用文件服务批量上传
        file_service = FileService()
        print(f"[批量上传] 调用 FileService.batch_upload_files...")
        
        result = file_service.batch_upload_files(
            files_data=files_data,
            uploader_id=current_user_id,
            description=description,
            tags=tags,
            document_type_code=document_type_code  # 新增
        )
        
        print(f"[批量上传] FileService返回结果:")
        print(f"  - successful_uploads: {result['successful_uploads']}")
        print(f"  - failed_uploads: {result['failed_uploads']}")
        print(f"  - total_files: {result['total_files']}")
        
        response_data = {
            'success': True,
            'message': f'批量上传完成，成功: {result["successful_uploads"]}, 失败: {result["failed_uploads"]}',
            'data': result
        }
        
        print(f"[批量上传] ✅ 返回响应: {response_data['message']}")
        print(f"{'='*80}\n")
        
        return jsonify(response_data), 201
        
    except Exception as e:
        print(f"\n[批量上传] ❌❌❌ 异常发生:")
        print(f"  异常类型: {type(e).__name__}")
        print(f"  异常信息: {str(e)}")
        import traceback
        print(f"  堆栈跟踪:\n{traceback.format_exc()}")
        print(f"{'='*80}\n")
        
        return jsonify({
            'success': False,
            'message': f'批量上传失败: {str(e)}'
        }), 500


@api_bp.route('/files', methods=['GET'])
@jwt_required()
def get_files():
    """获取文件列表"""
    try:
        from flask import request as flask_request
        from models.file import File
        from models.file_assignment import FileAssignment
        from sqlalchemy import or_
        
        print(f"🔍 获取文件列表API调用:")
        print(f"   Authorization header: {flask_request.headers.get('Authorization')}")
        
        current_user_id = get_jwt_identity()
        print(f"   当前用户ID: {current_user_id}")
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status_filter = request.args.get('status')
        review_status_filter = request.args.get('review_status')  # 核对状态筛选
        document_type_filter = request.args.get('document_type')  # 文件类型筛选
        view_mode = request.args.get('view_mode', 'my_files')  # my_files | assigned | all
        
        print(f"   查询参数:")
        print(f"   - page: {page}")
        print(f"   - per_page: {per_page}")
        print(f"   - status: {status_filter}")
        print(f"   - review_status: {review_status_filter}")
        print(f"   - document_type: {document_type_filter}")
        print(f"   - view_mode: {view_mode}")
        
        # 检查是否为管理员
        user = User.query.get(current_user_id)
        
        # 构建查询
        if user and user.is_admin() and (request.args.get('all_files') == 'true' or view_mode == 'all'):
            # 管理员可以查看所有文件
            query = File.query.filter_by(is_deleted=False)
        elif view_mode == 'assigned':
            # 查看分配给我的文件
            # 先获取分配给当前用户的文件ID
            assigned_file_ids = db.session.query(FileAssignment.file_id).filter(
                FileAssignment.assigned_to == current_user_id
            ).distinct().all()
            
            file_ids = [f[0] for f in assigned_file_ids]
            query = File.query.filter(
                File.id.in_(file_ids),
                File.is_deleted == False
            )
        elif view_mode == 'my_files':
            # 只查看我上传的文件
            query = File.query.filter(
                File.uploader_id == current_user_id,
                File.is_deleted == False
            )
        else:
            # 默认：查看自己上传的文件或分配给自己的文件（兼容旧逻辑）
            # 获取分配给我的文件ID
            assigned_file_ids = db.session.query(FileAssignment.file_id).filter(
                FileAssignment.assigned_to == current_user_id
            ).distinct().all()
            
            file_ids = [f[0] for f in assigned_file_ids]
            
            # 我上传的文件或分配给我的文件
            query = File.query.filter(
                or_(
                    File.uploader_id == current_user_id,
                    File.id.in_(file_ids) if file_ids else False
                ),
                File.is_deleted == False
            )
        
        # 状态筛选
        if status_filter:
            query = query.filter_by(ocr_status=status_filter)
        
        # 核对状态筛选
        if review_status_filter:
            query = query.filter_by(review_status=review_status_filter)
        
        # 文件类型筛选
        if document_type_filter:
            query = query.filter_by(document_type_code=document_type_filter)
        
        # 排序
        query = query.order_by(File.created_at.desc())
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # 转换为字典并添加审核人员信息
        files_data = []
        for file in pagination.items:
            file_dict = file.to_dict()
            
            # 获取当前分配信息（包括已完成的分配）
            assignment = FileAssignment.query.filter_by(
                file_id=file.id
            ).order_by(FileAssignment.assigned_at.desc()).first()
            
            if assignment:
                assignee = User.query.get(assignment.assigned_to)
                assigner = User.query.get(assignment.assigned_by)
                
                file_dict['assignment'] = {
                    'id': assignment.id,
                    'assigned_to': assignment.assigned_to,
                    'assigned_by': assignment.assigned_by,
                    'assignee_name': assignee.real_name or assignee.username if assignee else None,
                    'assignee_email': assignee.email if assignee else None,
                    'assigner_name': assigner.real_name or assigner.username if assigner else None,
                    'priority': assignment.priority,
                    'status': assignment.status,
                    'assigned_at': assignment.assigned_at.isoformat() if assignment.assigned_at else None
                }
            else:
                file_dict['assignment'] = None
            
            files_data.append(file_dict)
        
        result = {
            'files': files_data,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
        
        return jsonify({
            'success': True,
            'message': '获取文件列表成功',
            'data': result
        }), 200
            
    except Exception as e:
        print(f"❌ 获取文件列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'获取文件列表失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file_detail(file_id):
    """获取文件详情"""
    try:
        print(f"\n{'='*60}")
        print(f"🔍 [get_file_detail] 开始获取文件详情")
        print(f"📝 文件ID: {file_id}")
        
        from models.file import File
        from models.file_assignment import FileAssignment
        
        current_user_id = get_jwt_identity()
        print(f"👤 当前用户ID: {current_user_id}")
        
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        print(f"📄 文件记录查询结果: {file_record is not None}")
        
        if not file_record:
            print(f"❌ 文件不存在")
            print(f"{'='*60}\n")
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        print(f"✅ 文件记录: {file_record.to_dict()}")
        
        # 权限检查：管理员、上传者或被分配的用户可以访问
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        print(f"🔐 权限检查:")
        print(f"  - 是否管理员: {is_admin}")
        print(f"  - 是否上传者: {is_uploader}")
        
        # 检查是否被分配给当前用户
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        print(f"  - 是否被分配: {is_assigned}")
        
        if not (is_admin or is_uploader or is_assigned):
            print(f"❌ 无权限访问此文件")
            print(f"{'='*60}\n")
            return jsonify({
                'success': False,
                'message': '无权限访问此文件'
            }), 403
        
        # 获取OCR结果
        ocr_results = file_service.get_file_ocr_results(file_id)
        print(f"📋 OCR结果数量: {len(ocr_results) if ocr_results else 0}")
        
        file_data = file_record.to_dict()
        file_data['ocr_results'] = ocr_results
        
        print(f"✅ 成功返回文件详情")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'message': '获取文件详情成功',
            'data': file_data
        }), 200
        
    except Exception as e:
        print(f"❌ [get_file_detail] 异常: {str(e)}")
        print(f"❌ 异常类型: {type(e).__name__}")
        import traceback
        print(f"❌ 堆栈跟踪:\n{traceback.format_exc()}")
        print(f"{'='*60}\n")
        return jsonify({
            'success': False,
            'message': f'获取文件详情失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>', methods=['PUT'])
@jwt_required()
def update_file(file_id):
    """更新文件信息"""
    try:
        from models.file_assignment import FileAssignment
        
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        # 权限检查：管理员、上传者或被分配的用户可以更新文件信息
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        # 检查是否被分配给当前用户
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        if not (is_admin or is_uploader or is_assigned):
            return jsonify({
                'success': False,
                'message': '无权限修改此文件'
            }), 403
        
        # 更新文件信息
        result = file_service.update_file_info(
            file_id=file_id,
            user_id=current_user_id,
            description=data.get('description'),
            tags=data.get('tags')
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'更新文件信息失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    """删除文件"""
    try:
        current_user_id = get_jwt_identity()
        hard_delete = request.args.get('hard', 'false').lower() == 'true'
        
        # 权限检查
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        user = User.query.get(current_user_id)
        if not (user.is_admin() or file_record.uploader_id == current_user_id):
            return jsonify({
                'success': False,
                'message': '无权限删除此文件'
            }), 403
        
        # 删除文件
        result = file_service.delete_file(
            file_id=file_id,
            user_id=current_user_id,
            hard_delete=hard_delete
        )
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'删除文件失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/restore', methods=['POST'])
@jwt_required()
def restore_file(file_id):
    """恢复已删除的文件"""
    try:
        current_user_id = get_jwt_identity()
        
        file_service = FileService()
        result = file_service.restore_file(file_id, current_user_id)
        
        if result['success']:
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'恢复文件失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/download', methods=['GET'])
@jwt_required(optional=True)
def download_file(file_id):
    """下载文件"""
    try:
        from models.file_assignment import FileAssignment
        
        # 尝试从JWT获取用户ID
        current_user_id = get_jwt_identity()
        
        # 如果JWT中没有用户ID，尝试从URL参数中获取token
        if not current_user_id:
            token = request.args.get('token')
            if token:
                try:
                    from flask_jwt_extended import decode_token
                    decoded = decode_token(token)
                    current_user_id = decoded['sub']
                    print(f"✅ 从URL参数获取到用户ID: {current_user_id}")
                except Exception as e:
                    print(f"❌ 解析URL token失败: {e}")
                    return jsonify({
                        'success': False,
                        'message': '无效的访问令牌'
                    }), 401
        
        if not current_user_id:
            return jsonify({
                'success': False,
                'message': '需要登录才能下载文件'
            }), 401
        
        # 权限检查：管理员、上传者或被分配的用户可以下载
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        # 检查是否被分配给当前用户
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        if not (is_admin or is_uploader or is_assigned):
            return jsonify({
                'success': False,
                'message': '无权限下载此文件'
            }), 403
        
        # 下载文件
        download_result = file_service.download_file(file_id, current_user_id)
        
        if not download_result:
            return jsonify({
                'success': False,
                'message': '文件下载失败'
            }), 500
        
        # 检查是否为预览模式
        preview_mode = request.args.get('preview', 'false').lower() == 'true'
        
        # 返回文件流
        return send_file(
            BytesIO(download_result['file_data']),
            mimetype=download_result['content_type'],
            as_attachment=not preview_mode,  # 预览模式时不设置为附件
            download_name=download_result['filename'] if not preview_mode else None
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'下载文件失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/preview', methods=['GET'])
@jwt_required()
def get_file_preview_url(file_id):
    """获取文件预览URL"""
    try:
        from models.file_assignment import FileAssignment
        
        current_user_id = get_jwt_identity()
        expires = request.args.get('expires', 3600, type=int)
        
        # 权限检查：管理员、上传者或被分配的用户可以预览
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        # 检查是否被分配给当前用户
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        if not (is_admin or is_uploader or is_assigned):
            return jsonify({
                'success': False,
                'message': '无权限预览此文件'
            }), 403
        
        # 获取预览URL
        preview_result = file_service.get_file_preview_url(file_id, expires)
        
        if preview_result:
            return jsonify({
                'success': True,
                'message': '获取预览URL成功',
                'data': preview_result
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '获取预览URL失败'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取预览URL失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/process', methods=['POST'])
@jwt_required()
def start_file_processing(file_id):
    """开始文件OCR处理（旧版同步方式）
    
    @deprecated: 此API使用同步OCR处理，建议迁移到 /files/<file_id>/ocr/recognize
    
    现状：
    - 主要用于文件列表页面的"开始处理"功能
    - 同步调用 FileService.start_ocr_processing()
    - 可能因OCR处理时间长而超时
    
    推荐替代方案：
    - 使用 /files/<file_id>/ocr/recognize 创建异步任务
    - 使用 /files/ocr/task/<task_id> 轮询任务状态
    - 识别页面已迁移至新方案
    
    迁移计划：
    - 待系统稳定后，文件列表页面迁移到异步任务
    - 完全迁移后可以废弃此endpoint
    """
    try:
        from models.file_assignment import FileAssignment
        
        current_app.logger.info(f'🚀 [API] 开始处理文件OCR请求，file_id: {file_id}')
        current_user_id = get_jwt_identity()
        current_app.logger.info(f'👤 [API] 当前用户ID: {current_user_id}')
        
        # 获取请求数据（可能包含model_id）
        data = request.get_json() if request.is_json else {}
        model_id = data.get('model_id')
        
        if model_id:
            current_app.logger.info(f'🤖 [API] 指定使用模型ID: {model_id}')
        
        # 权限检查：管理员、上传者或被分配的用户可以处理文件
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            current_app.logger.error(f'❌ [API] 文件不存在，file_id: {file_id}')
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        current_app.logger.info(f'📂 [API] 文件记录找到: {file_record.filename}, 状态: {file_record.ocr_status}')
        
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        # 检查是否被分配给当前用户
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        if not (is_admin or is_uploader or is_assigned):
            current_app.logger.error(f'🚫 [API] 权限不足，文件上传者: {file_record.uploader_id}, 当前用户: {current_user_id}')
            return jsonify({
                'success': False,
                'message': '无权限处理此文件'
            }), 403
        
        # 开始OCR处理（传递model_id）
        current_app.logger.info(f'🔄 [API] 调用OCR处理服务...')
        result = file_service.start_ocr_processing(file_id, model_id=model_id)
        
        current_app.logger.info(f'📊 [API] OCR处理结果: success={result.get("success")}, message={result.get("message")}')
        
        if result['success']:
            current_app.logger.info(f'✅ [API] OCR处理成功，返回200')
            return jsonify(result), 200
        else:
            current_app.logger.error(f'❌ [API] OCR处理失败，返回400: {result}')
            return jsonify(result), 400
            
    except Exception as e:
        current_app.logger.error(f'💥 [API] 处理异常: {str(e)}')
        import traceback
        current_app.logger.error(f'💥 [API] 异常堆栈: {traceback.format_exc()}')
        return jsonify({
            'success': False,
            'message': f'启动文件处理失败: {str(e)}'
        }), 500


# ==================== 统一文档数据接口 ====================

@api_bp.route('/files/<int:file_id>/document-data', methods=['GET'])
@jwt_required()
def get_document_data(file_id):
    """
    统一接口：获取文件的文档数据（自动识别类型）
    
    根据 file.document_type_code 自动路由：
    - 'paper' → PaperAdapter.get_from_database()
    - 'commission' → CommissionAdapter.get_from_database()
    
    返回格式：
    {
        "success": true,
        "data": {
            // 论文格式
            "article_id": "...",
            "article_name": "...",
            "hierarchical_data": [...]
            
            // 或委托单格式
            "basic_info": {...},
            "test_items": [...],
            "special_tests": [...]
        },
        "document_type": "paper" | "commission"
    }
    """
    try:
        from models.file_assignment import FileAssignment
        
        current_user_id = get_jwt_identity()
        
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 权限检查：管理员、上传者或被分配的用户可以查看
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        # 检查是否被分配给当前用户
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        if not (is_admin or is_uploader or is_assigned):
            return jsonify({
                'success': False,
                'message': '无权限查看此文件的文档数据'
            }), 403
        
        # 获取文档类型
        document_type = file_record.document_type_code
        if not document_type:
            return jsonify({
                'success': False,
                'message': '文件未设置文档类型'
            }), 400
        
        current_app.logger.info(f"🔍 [统一API] 获取文档数据: file_id={file_id}, document_type={document_type}")
        
        # 使用统一接口获取数据
        document_data = file_service.get_document_data(file_id)
        
        # 注意：Adapter 会返回空结构而不是 None，所以这里 document_data 应该总是有值
        if document_data is None:
            current_app.logger.warning(f"⚠️ [统一API] 文档数据为 None（异常情况）")
            return jsonify({
                'success': False,
                'message': '获取文档数据失败'
            }), 500
        
        current_app.logger.info(f"✅ [统一API] 成功获取文档数据")
        
        return jsonify({
            'success': True,
            'message': '获取文档数据成功',
            'data': document_data,
            'document_type': document_type
        })
        
    except Exception as e:
        current_app.logger.error(f"❌ [统一API] 获取文档数据失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取文档数据失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/document-data', methods=['PUT'])
@jwt_required()
def update_document_data_unified(file_id):
    """
    统一接口：保存或更新文件的文档数据（自动识别类型）
    
    根据 file.document_type_code 自动路由：
    - 'paper' → PaperAdapter (通过 update_in_database)
    - 'commission' → CommissionAdapter.update_in_database()
    
    请求体：
    {
        // 论文格式
        "article_id": "...",
        "article_name": "...",
        "hierarchical_data": [...]
        
        // 或委托单格式
        "basic_info": {...},
        "test_items": [...],
        "special_tests": [...]
    }
    
    返回格式：
    {
        "success": true,
        "message": "保存成功",
        "document_type": "paper" | "commission"
    }
    """
    try:
        from models.file_assignment import FileAssignment
        
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少请求数据'
            }), 400
        
        file_service = FileService()
        file_record = file_service.get_file_by_id(file_id)
        
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 权限检查：管理员、上传者或被分配的用户可以更新
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        is_assigned = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first() is not None
        
        if not (is_admin or is_uploader or is_assigned):
            return jsonify({
                'success': False,
                'message': '无权限操作此文件的文档数据'
            }), 403
        
        # 获取文档类型
        document_type = file_record.document_type_code
        if not document_type:
            return jsonify({
                'success': False,
                'message': '文件未设置文档类型'
            }), 400
        
        current_app.logger.info(f"📝 [统一API] 更新文档数据: file_id={file_id}, document_type={document_type}")
        
        # 使用统一接口更新数据
        update_result = file_service.update_document_data(file_id, data)
        
        if update_result['success']:
            current_app.logger.info(f"✅ [统一API] 文档数据更新成功")
            return jsonify({
                'success': True,
                'message': update_result['message'],
                'document_type': document_type
            })
        else:
            current_app.logger.error(f"❌ [统一API] 文档数据更新失败: {update_result['message']}")
            return jsonify({
                'success': False,
                'message': update_result['message']
            }), 500
        
    except Exception as e:
        current_app.logger.error(f"❌ [统一API] 更新文档数据失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'更新文档数据失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/complete-review', methods=['POST'])
@jwt_required()
def complete_file_review(file_id):
    """完成文件核对"""
    try:
        from models.file import File
        from models.file_assignment import FileAssignment
        from models import db
        
        current_user_id = get_jwt_identity()
        print(f"🔍 [完成核对] 用户ID: {current_user_id}, 文件ID: {file_id}")
        
        # 获取文件记录
        file_record = File.query.get(file_id)
        if not file_record:
            print(f"❌ [完成核对] 文件不存在: {file_id}")
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        print(f"📄 [完成核对] 文件信息 - 上传者ID: {file_record.uploader_id}")
        
        # 权限检查：管理员、上传者或被分配的用户可以完成核对
        user = User.query.get(current_user_id)
        is_admin = user.is_admin()
        is_uploader = file_record.uploader_id == current_user_id
        
        print(f"👤 [完成核对] 用户角色: {user.role}, 是否管理员: {is_admin}, 是否上传者: {is_uploader}")
        
        # 检查是否被分配给当前用户
        assignment = FileAssignment.query.filter_by(
            file_id=file_id,
            assigned_to=current_user_id
        ).first()
        
        is_assigned = assignment is not None
        print(f"📋 [完成核对] 是否被分配: {is_assigned}, 分配记录: {assignment}")
        
        if not (is_admin or is_uploader or is_assigned):
            print(f"🚫 [完成核对] 权限不足 - 管理员:{is_admin}, 上传者:{is_uploader}, 被分配:{is_assigned}")
            return jsonify({
                'success': False,
                'message': '无权限完成此文件的核对'
            }), 403
        
        print(f"✅ [完成核对] 权限检查通过，开始更新状态")
        
        # 更新文件的核对状态
        file_record.update_review_status('completed')
        
        # 如果是通过分配来的，更新分配记录状态
        if assignment:
            assignment.status = 'completed'
            assignment.completed_at = datetime.utcnow()
        
        db.session.commit()
        print(f"✅ [完成核对] 核对完成，文件ID: {file_id}")
        
        return jsonify({
            'success': True,
            'message': '核对已完成',
            'data': {
                'file_id': file_id,
                'review_status': 'completed',
                'review_completed_at': file_record.review_completed_at.isoformat() if file_record.review_completed_at else None
            }
        })
        
    except Exception as e:
        print(f"❌ [完成核对] 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'完成核对失败: {str(e)}'
        }), 500


# ==================== OCR识别相关API ====================
# ✅ 推荐使用：异步任务方式
# 以下API使用 OcrTaskService 提供异步OCR处理能力

@api_bp.route('/files/<int:file_id>/ocr/recognize', methods=['POST'])
@jwt_required()
def recognize_file_ocr(file_id):
    """
    对文件进行OCR识别（异步任务 - 推荐方式）
    
    ✅ 新版异步API
    - 立即返回任务ID，不阻塞请求
    - 支持任务进度查询和状态轮询
    - 处理超时不会影响用户体验
    
    当前使用场景：
    - FileRecognize 识别页面 ✅
    
    工作流程：
    1. 创建异步任务，返回 task_id
    2. 后台线程处理OCR识别
    3. 前端轮询 /files/ocr/task/<task_id> 获取状态
    4. 任务完成后返回OCR结果
    
    对比旧版API：
    - 旧版：POST /files/<file_id>/process（同步，可能超时）
    - 新版：POST /files/<file_id>/ocr/recognize（异步，推荐）
    """
    from services.ocr_task_service import OcrTaskService
    
    try:
        current_user_id = get_jwt_identity()
        file_service = FileService()
        
        # 获取文件信息
        file_record = file_service.get_file_by_id(file_id)
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 检查权限（文件所有者或管理员）
        user = User.query.get(current_user_id)
        if file_record.uploader_id != current_user_id and not user.is_admin():
            return jsonify({
                'success': False,
                'message': '无权限操作此文件'
            }), 403
        
        current_app.logger.info(f'🔍 创建OCR识别任务: 文件ID={file_id}, 用户ID={current_user_id}')
        
        # 创建异步任务
        task = OcrTaskService.create_task(file_id, current_user_id)
        
        # 启动后台处理
        OcrTaskService.start_task_processing(task.task_id, file_service)
        
        # 立即返回任务ID
        return jsonify({
            'success': True,
            'message': 'OCR识别任务已创建',
            'data': {
                'task_id': task.task_id,
                'file_id': file_id,
                'status': task.status
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'创建OCR任务失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'创建OCR任务失败: {str(e)}'
        }), 500


@api_bp.route('/files/ocr/task/<task_id>', methods=['GET'])
@jwt_required()
def get_ocr_task_status(task_id):
    """
    获取OCR任务状态
    
    用于前端轮询任务进度
    """
    from services.ocr_task_service import OcrTaskService
    
    try:
        current_user_id = get_jwt_identity()
        
        # 获取任务
        task = OcrTaskService.get_task(task_id)
        if not task:
            return jsonify({
                'success': False,
                'message': '任务不存在'
            }), 404
        
        # 检查权限（任务所有者或管理员）
        user = User.query.get(current_user_id)
        if task.user_id != current_user_id and not user.is_admin():
            return jsonify({
                'success': False,
                'message': '无权限查看此任务'
            }), 403
        
        # 返回任务状态
        task_data = task.to_dict()
        ocr_result = task.result if task.status == 'completed' else None
        
        # 添加详细日志
        current_app.logger.info(f'📤 [API] 返回任务状态: task_id={task_id}, status={task.status}')
        current_app.logger.info(f'📊 [API] task.result 类型: {type(task.result)}')
        current_app.logger.info(f'📊 [API] task.result 值: {task.result}')
        
        if ocr_result:
            current_app.logger.info(f'📦 [API] OCR结果类型: {type(ocr_result)}')
            current_app.logger.info(f'📦 [API] OCR结果键: {list(ocr_result.keys()) if isinstance(ocr_result, dict) else "非字典"}')
            
            if isinstance(ocr_result, dict):
                if 'structured_data' in ocr_result:
                    structured = ocr_result['structured_data']
                    current_app.logger.info(f'✅ [API] 找到 structured_data')
                    current_app.logger.info(f'📋 [API] structured_data 类型: {type(structured)}')
                    current_app.logger.info(f'📋 [API] structured_data 键: {list(structured.keys()) if isinstance(structured, dict) else "非字典"}')
                    
                    # 根据文档类型输出不同的信息
                    if 'article_id' in structured:
                        # 论文数据
                        current_app.logger.info(f'📄 [API] 论文数据 - 文献ID: {structured.get("article_id")}, '
                                              f'文献名称: {structured.get("article_name")}, '
                                              f'材料/中间体数: {len(structured.get("hierarchical_data", []))}')
                    elif 'basic_info' in structured:
                        # 委托单数据
                        basic_info = structured.get('basic_info', {})
                        test_items = structured.get('test_items', [])
                        special_tests = structured.get('special_tests', [])
                        
                        current_app.logger.info(f'📋 [API] 委托单数据 - 基本信息字段数: {len(basic_info)}, '
                                              f'检测项: {len(test_items)}, '
                                              f'特殊试验: {len(special_tests)}')
                        
                        # 打印完整的字段列表
                        current_app.logger.info("=" * 80)
                        current_app.logger.info("🌐 [OCR Task API] 返回给前端的 basic_info 字段:")
                        for idx, (key, value) in enumerate(basic_info.items(), 1):
                            # 截断长值以便于阅读
                            display_value = str(value)[:50] + '...' if len(str(value)) > 50 else str(value)
                            current_app.logger.info(f"  {idx}. {key} = {display_value}")
                        current_app.logger.info("=" * 80)
                else:
                    current_app.logger.warning(f'⚠️ [API] OCR结果中没有 structured_data')
                    current_app.logger.warning(f'⚠️ [API] OCR结果内容: {ocr_result}')
        else:
            current_app.logger.warning(f'⚠️ [API] ocr_result 为空（任务状态: {task.status}）')
        
        return jsonify({
            'success': True,
            'data': {
                'task': task_data,
                'ocr_result': ocr_result
            }
        })
        
    except Exception as e:
        current_app.logger.error(f'获取任务状态失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取任务状态失败: {str(e)}'
        }), 500


@api_bp.route('/files/<int:file_id>/ocr/save', methods=['POST'])
@jwt_required()
def save_ocr_result(file_id):
    """
    统一接口：保存OCR识别结果到数据库（自动识别类型）
    
    根据 file.document_type_code 自动路由：
    - 'paper' → PaperAdapter.save_to_database()
    - 'commission' → CommissionAdapter.save_to_database()
    
    用于识别界面，用户核对修改后首次保存
    
    请求体：
    {
        "ocr_result": {
            // 论文格式
            "article_id": "...",
            "article_name": "...",
            "hierarchical_data": [...]
            
            // 或委托单格式
            "extracted_fields": {...},
            "test_items": [...],
            "special_tests": [...]
        }
    }
    
    注意：
    - 此接口用于首次保存OCR结果（INSERT）
    - 如需更新，请使用 PUT /files/{id}/document-data
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '缺少数据'
            }), 400
        
        file_service = FileService()
        
        # 获取文件信息
        file_record = file_service.get_file_by_id(file_id)
        if not file_record:
            return jsonify({
                'success': False,
                'message': '文件不存在'
            }), 404
        
        # 检查权限（文件所有者或管理员）
        user = User.query.get(current_user_id)
        if file_record.uploader_id != current_user_id and not user.is_admin():
            return jsonify({
                'success': False,
                'message': '无权限操作此文件'
            }), 403
        
        # 提取数据
        ocr_result = data.get('ocr_result')
        if not ocr_result:
            return jsonify({
                'success': False,
                'message': '缺少OCR识别结果'
            }), 400
        
        # 获取文档类型
        document_type = file_record.document_type_code
        if not document_type:
            return jsonify({
                'success': False,
                'message': '文件未设置文档类型'
            }), 400
        
        current_app.logger.info(f'💾 [OCR保存] 开始保存: 文件ID={file_id}, 用户ID={current_user_id}, 文档类型={document_type}')
        
        # 使用统一接口保存到数据库
        # Adapter 会自己处理 OCR 结果的格式转换和验证
        try:
            save_result = file_service.save_document_data(file_id, ocr_result)
            
            if save_result['success']:
                current_app.logger.info(f'✅ OCR识别结果保存成功: 文件ID={file_id}')
                
                # 更新文件状态
                file_record.ocr_status = 'completed'
                file_record.ocr_completed_at = datetime.utcnow()
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'OCR识别结果保存成功',
                    'document_type': document_type
                })
            else:
                return jsonify({
                    'success': False,
                    'message': save_result['message']
                }), 500
                
        except ValueError as ve:
            # 捕获委托编号已存在等验证错误
            current_app.logger.warning(f'⚠️  保存失败: {str(ve)}')
            return jsonify({
                'success': False,
                'message': str(ve)
            }), 400
        except Exception as e:
            current_app.logger.error(f'❌ 保存OCR识别结果失败: {str(e)}')
            import traceback
            current_app.logger.error(f'错误详情: {traceback.format_exc()}')
            return jsonify({
                'success': False,
                'message': f'保存失败: {str(e)}'
            }), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'保存OCR识别结果失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500
