"""
身份认证相关API
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity, get_jwt
from datetime import datetime
from . import api_bp
from models.user import User
from models import db


@api_bp.route('/auth/register', methods=['POST'])
def register():
    """用户注册"""
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
            role='user'  # 默认为普通用户
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'注册失败: {str(e)}'
        }), 500


@api_bp.route('/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': '用户名和密码不能为空'
            }), 400
        
        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == data['username']) | (User.email == data['username'])
        ).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': '用户名或密码错误'
            }), 401
        
        if not user.is_active:
            return jsonify({
                'success': False,
                'message': '账户已被禁用'
            }), 401
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        
        # 创建JWT令牌 - subject必须是字符串
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登录失败: {str(e)}'
        }), 500


@api_bp.route('/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_active:
            return jsonify({
                'success': False,
                'message': '用户不存在或已被禁用'
            }), 401
        
        access_token = create_access_token(identity=str(current_user_id))
        
        return jsonify({
            'success': True,
            'message': '令牌刷新成功',
            'data': {
                'access_token': access_token
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'令牌刷新失败: {str(e)}'
        }), 500


@api_bp.route('/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        # 在实际应用中，这里可以将token添加到黑名单
        jti = get_jwt()['jti']
        
        return jsonify({
            'success': True,
            'message': '登出成功'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'登出失败: {str(e)}'
        }), 500


@api_bp.route('/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前用户信息"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'message': '获取用户信息成功',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取用户信息失败: {str(e)}'
        }), 500


@api_bp.route('/auth/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({
                'success': False,
                'message': '用户不存在'
            }), 404
        
        data = request.get_json()
        
        if not data.get('old_password') or not data.get('new_password'):
            return jsonify({
                'success': False,
                'message': '旧密码和新密码不能为空'
            }), 400
        
        # 验证旧密码
        if not user.check_password(data['old_password']):
            return jsonify({
                'success': False,
                'message': '旧密码错误'
            }), 400
        
        # 设置新密码
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'密码修改失败: {str(e)}'
        }), 500
