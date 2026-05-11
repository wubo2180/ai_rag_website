"""
用户管理相关API
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import desc, asc
from . import api_bp
from models.user import User
from models import db
from utils.decorators import admin_required


@api_bp.route('/users', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """获取用户列表（仅管理员）"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '')
        role_filter = request.args.get('role', '')
        status_filter = request.args.get('status', '')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # 构建查询
        query = User.query
        
        # 搜索条件
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                (User.username.like(search_pattern)) |
                (User.email.like(search_pattern)) |
                (User.real_name.like(search_pattern))
            )
        
        # 角色筛选
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        # 状态筛选
        if status_filter == 'active':
            query = query.filter(User.is_active == True)
        elif status_filter == 'inactive':
            query = query.filter(User.is_active == False)
        
        # 排序
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == 'desc':
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        return jsonify({
            'success': True,
            'message': '获取用户列表成功',
            'data': {
                'users': [user.to_dict() for user in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户列表失败: {str(e)}'
        }), 500


@api_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    """创建新用户（仅管理员）"""
    try:
        data = request.get_json()
        
        # 验证必填字段
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field}字段不能为空'
                }), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=data['username']).first():
            return jsonify({
                'success': False,
                'message': '用户名已存在'
            }), 400
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=data['email']).first():
            return jsonify({
                'success': False,
                'message': '邮箱已被使用'
            }), 400
        
        # 创建新用户
        user = User(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            real_name=data.get('real_name'),
            role=data.get('role', 'user')
        )
        
        user.is_active = data.get('is_active', True)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户创建成功',
            'data': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建用户失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """更新用户信息（仅管理员）"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        
        # 检查邮箱是否被其他用户使用
        if data.get('email') and data['email'] != user.email:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': '邮箱已被其他用户使用'
                }), 400
        
        # 更新用户信息
        if 'email' in data:
            user.email = data['email']
        if 'real_name' in data:
            user.real_name = data['real_name']
        if 'role' in data:
            user.role = data['role']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户更新成功',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新用户失败: {str(e)}'
        }), 500


@api_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """删除用户（仅管理员）"""
    try:
        current_user_id = get_jwt_identity()
        
        # 不能删除自己
        if user_id == current_user_id:
            return jsonify({
                'success': False,
                'message': '不能删除自己的账户'
            }), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        # 检查用户是否有相关数据
        # 这里可以添加更复杂的检查逻辑
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除用户失败: {str(e)}'
        }), 500


@api_bp.route('/users/stats', methods=['GET'])
@jwt_required()
@admin_required
def get_user_stats():
    """获取用户统计信息（仅管理员）"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        admin_users = User.query.filter_by(role='admin').count()
        
        return jsonify({
            'success': True,
            'message': '获取统计信息成功',
            'data': {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'admin_users': admin_users,
                'regular_users': total_users - admin_users
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500
