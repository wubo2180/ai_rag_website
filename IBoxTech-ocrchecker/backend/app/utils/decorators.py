"""
装饰器工具
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from models.user import User


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin():
            return jsonify({
                'success': False,
                'message': '需要管理员权限'
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def permission_required(permission):
    """权限检查装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.is_active:
                return jsonify({
                    'success': False,
                    'message': '用户未激活'
                }), 403
            
            # 这里可以扩展更复杂的权限检查逻辑
            if permission == 'admin' and not user.is_admin():
                return jsonify({
                    'success': False,
                    'message': '需要管理员权限'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
