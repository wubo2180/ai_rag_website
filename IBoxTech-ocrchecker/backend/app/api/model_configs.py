"""
模型配置管理API
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import api_bp
from models import db, get_models
from utils.decorators import admin_required

# 获取模型
models = get_models()
ModelConfig = models['ModelConfig']
User = models['User']


@api_bp.route('/model-configs', methods=['GET'])
@jwt_required()
def get_model_configs():
    """获取模型配置列表"""
    try:
        print("=" * 50)
        print("📥 收到获取模型配置列表请求")
        
        # 获取查询参数
        file_type = request.args.get('file_type')
        is_active = request.args.get('is_active')
        
        print(f"🔍 查询参数: file_type={file_type}, is_active={is_active}")
        
        # 构建查询
        query = ModelConfig.query
        
        if file_type:
            query = query.filter(
                (ModelConfig.file_type == file_type) | 
                (ModelConfig.file_type == None)
            )
        
        if is_active is not None:
            query = query.filter(ModelConfig.is_active == (is_active == 'true'))
        
        # 查询所有配置
        configs = query.order_by(
            ModelConfig.is_default.desc(),
            ModelConfig.created_at.desc()
        ).all()
        
        print(f"✅ 查询到 {len(configs)} 个模型配置")
        for config in configs:
            print(f"  - {config.name} (id={config.id}, type={config.file_type}, default={config.is_default})")
        
        result = {
            'success': True,
            'data': [config.to_dict() for config in configs]
        }
        
        print(f"📤 返回数据: success=True, 模型数量={len(result['data'])}")
        print("=" * 50)
        
        return jsonify(result), 200
        
    except Exception as e:
        current_app.logger.error(f'获取模型配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取模型配置失败: {str(e)}'
        }), 500


@api_bp.route('/model-configs/<int:config_id>', methods=['GET'])
@jwt_required()
def get_model_config(config_id):
    """获取单个模型配置"""
    try:
        config = ModelConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '模型配置不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'获取模型配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取模型配置失败: {str(e)}'
        }), 500


@api_bp.route('/model-configs', methods=['POST'])
@jwt_required()
@admin_required
def create_model_config():
    """创建模型配置"""
    try:
        data = request.get_json()
        current_user_id = get_jwt_identity()
        
        # 验证必填字段
        if not data.get('name') or not data.get('api_url'):
            return jsonify({
                'success': False,
                'message': '模型名称和API地址为必填项'
            }), 400
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if data.get('is_default'):
            ModelConfig.query.filter_by(is_default=True).update({'is_default': False})
        
        # 创建新配置
        config = ModelConfig(
            name=data['name'],
            api_url=data['api_url'],
            file_type=data.get('file_type'),
            description=data.get('description'),
            config_params=data.get('config_params'),
            is_default=data.get('is_default', False),
            is_active=data.get('is_active', True),
            timeout=data.get('timeout', 120),
            created_by=current_user_id
        )
        
        db.session.add(config)
        db.session.commit()
        
        current_app.logger.info(f'创建模型配置成功: {config.name}')
        
        return jsonify({
            'success': True,
            'message': '模型配置创建成功',
            'data': config.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建模型配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'创建模型配置失败: {str(e)}'
        }), 500


@api_bp.route('/model-configs/<int:config_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_model_config(config_id):
    """更新模型配置"""
    try:
        config = ModelConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '模型配置不存在'
            }), 404
        
        data = request.get_json()
        
        # 如果设置为默认模型，取消其他模型的默认状态
        if data.get('is_default') and not config.is_default:
            ModelConfig.query.filter_by(is_default=True).update({'is_default': False})
        
        # 更新字段
        if 'name' in data:
            config.name = data['name']
        if 'api_url' in data:
            config.api_url = data['api_url']
        if 'file_type' in data:
            config.file_type = data['file_type']
        if 'description' in data:
            config.description = data['description']
        if 'config_params' in data:
            config.config_params = data['config_params']
        if 'is_default' in data:
            config.is_default = data['is_default']
        if 'is_active' in data:
            config.is_active = data['is_active']
        if 'timeout' in data:
            config.timeout = data['timeout']
        
        db.session.commit()
        
        current_app.logger.info(f'更新模型配置成功: {config.name}')
        
        return jsonify({
            'success': True,
            'message': '模型配置更新成功',
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新模型配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新模型配置失败: {str(e)}'
        }), 500


@api_bp.route('/model-configs/<int:config_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_model_config(config_id):
    """删除模型配置"""
    try:
        config = ModelConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '模型配置不存在'
            }), 404
        
        # 检查是否为默认模型
        if config.is_default:
            return jsonify({
                'success': False,
                'message': '无法删除默认模型，请先设置其他模型为默认'
            }), 400
        
        config_name = config.name
        db.session.delete(config)
        db.session.commit()
        
        current_app.logger.info(f'删除模型配置成功: {config_name}')
        
        return jsonify({
            'success': True,
            'message': '模型配置删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除模型配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除模型配置失败: {str(e)}'
        }), 500


@api_bp.route('/model-configs/get-for-file', methods=['GET'])
@jwt_required()
def get_model_for_file():
    """根据文件业务类型获取合适的模型配置列表"""
    try:
        file_type = request.args.get('file_type', '')
        
        print(f"🔍 获取模型配置 - 文件类型: {file_type}")
        
        # 查询匹配的模型
        query = ModelConfig.query.filter_by(is_active=True)
        
        if file_type:
            # 获取该业务类型的模型或通用模型（file_type为NULL）
            configs = query.filter(
                (ModelConfig.file_type == file_type) | 
                (ModelConfig.file_type == None)
            ).order_by(
                ModelConfig.is_default.desc(),
                ModelConfig.file_type.desc(),  # 优先匹配特定类型
                ModelConfig.created_at.desc()
            ).all()
        else:
            # 未知类型，只返回通用模型
            configs = query.filter(
                ModelConfig.file_type == None
            ).order_by(
                ModelConfig.is_default.desc(),
                ModelConfig.created_at.desc()
            ).all()
        
        print(f"✅ 找到 {len(configs)} 个可用模型")
        for config in configs:
            print(f"  - {config.name} (id={config.id}, type={config.file_type})")
        
        if not configs:
            return jsonify({
                'success': False,
                'message': '没有可用的模型配置'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'file_type': file_type or 'unknown',
                'models': [config.to_dict() for config in configs],
                'default_model': configs[0].to_dict() if configs else None
            }
        }), 200
        
    except Exception as e:
        current_app.logger.error(f'获取文件模型配置失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取文件模型配置失败: {str(e)}'
        }), 500

