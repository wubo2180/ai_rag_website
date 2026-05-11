"""
文件类型配置管理API
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import api_bp
from models import db, get_models
from utils.decorators import admin_required
import logging

# 获取模型
models = get_models()
FileTypeConfig = models['FileTypeConfig']
ModelConfig = models['ModelConfig']
User = models['User']

logger = logging.getLogger(__name__)


@api_bp.route('/file-type-configs', methods=['GET'])
@jwt_required()
def get_file_type_configs():
    """获取文件类型配置列表"""
    try:
        logger.info("📥 收到获取文件类型配置列表请求")
        
        # 获取查询参数
        is_active = request.args.get('is_active')
        
        # 构建查询
        query = FileTypeConfig.query
        
        if is_active is not None:
            query = query.filter(FileTypeConfig.is_active == (is_active == 'true'))
        
        # 查询所有配置
        configs = query.order_by(
            FileTypeConfig.sort_order.asc(),
            FileTypeConfig.created_at.desc()
        ).all()
        
        logger.info(f"✅ 查询到 {len(configs)} 个文件类型配置")
        
        result = {
            'success': True,
            'data': [config.to_dict() for config in configs]
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f'获取文件类型配置失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取文件类型配置失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/<int:config_id>', methods=['GET'])
@jwt_required()
def get_file_type_config(config_id):
    """获取单个文件类型配置"""
    try:
        config = FileTypeConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '文件类型配置不存在'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'获取文件类型配置失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取文件类型配置失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/by-code/<type_code>', methods=['GET'])
@jwt_required()
def get_file_type_config_by_code(type_code):
    """根据类型代码获取配置"""
    try:
        config = FileTypeConfig.query.filter_by(type_code=type_code).first()
        if not config:
            return jsonify({
                'success': False,
                'message': f'文件类型配置不存在: {type_code}'
            }), 404
        
        return jsonify({
            'success': True,
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'获取文件类型配置失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取文件类型配置失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs', methods=['POST'])
@jwt_required()
@admin_required
def create_file_type_config():
    """创建文件类型配置"""
    try:
        data = request.get_json()
        logger.info(f"📝 创建文件类型配置: {data.get('type_code')}")
        
        # 验证必填字段
        required_fields = ['type_code', 'type_name', 'storage_tables', 'adapter_class']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'缺少必填字段: {field}'
                }), 400
        
        # 检查类型代码是否已存在
        existing = FileTypeConfig.query.filter_by(type_code=data['type_code']).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'类型代码已存在: {data["type_code"]}'
            }), 400
        
        # 验证关联的模型配置是否存在
        if data.get('model_config_id'):
            model = ModelConfig.query.get(data['model_config_id'])
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型配置不存在: {data["model_config_id"]}'
                }), 400
        
        # 验证存储表配置格式（新格式：字符串数组）
        storage_tables = data.get('storage_tables', [])
        if not isinstance(storage_tables, list) or len(storage_tables) == 0:
            return jsonify({
                'success': False,
                'message': '存储表配置必须是非空数组'
            }), 400
        
        # 新格式：验证是否为字符串数组
        for table in storage_tables:
            if not isinstance(table, str):
                return jsonify({
                    'success': False,
                    'message': '存储表配置格式错误，必须是字符串数组，如：["table1", "table2"]'
                }), 400
        
        # 创建配置
        config = FileTypeConfig(
            type_code=data['type_code'],
            type_name=data['type_name'],
            type_description=data.get('type_description'),
            model_config_id=data.get('model_config_id'),
            ocr_config=data.get('ocr_config'),
            storage_tables=storage_tables,
            adapter_class=data['adapter_class'],
            adapter_module=data.get('adapter_module', 'adapters'),
            form_config=data.get('form_config'),
            form_component=data.get('form_component'),
            validation_rules=data.get('validation_rules'),
            is_active=data.get('is_active', True),
            sort_order=data.get('sort_order', 0)
        )
        
        db.session.add(config)
        db.session.commit()
        
        logger.info(f"✅ 文件类型配置创建成功: {config.type_code} (ID: {config.id})")
        
        return jsonify({
            'success': True,
            'message': '创建成功',
            'data': config.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建文件类型配置失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/<int:config_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_file_type_config(config_id):
    """更新文件类型配置"""
    try:
        config = FileTypeConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '文件类型配置不存在'
            }), 404
        
        data = request.get_json()
        logger.info(f"📝 更新文件类型配置: {config.type_code} (ID: {config_id})")
        
        # 验证关联的模型配置是否存在
        if data.get('model_config_id'):
            model = ModelConfig.query.get(data['model_config_id'])
            if not model:
                return jsonify({
                    'success': False,
                    'message': f'模型配置不存在: {data["model_config_id"]}'
                }), 400
        
        # 验证存储表配置格式（新格式：字符串数组）
        if 'storage_tables' in data:
            storage_tables = data['storage_tables']
            if not isinstance(storage_tables, list) or len(storage_tables) == 0:
                return jsonify({
                    'success': False,
                    'message': '存储表配置必须是非空数组'
                }), 400
            
            # 新格式：验证是否为字符串数组
            for table in storage_tables:
                if not isinstance(table, str):
                    return jsonify({
                        'success': False,
                        'message': '存储表配置格式错误，必须是字符串数组，如：["table1", "table2"]'
                    }), 400
        
        # 更新字段
        if 'type_name' in data:
            config.type_name = data['type_name']
        if 'type_description' in data:
            config.type_description = data['type_description']
        if 'model_config_id' in data:
            config.model_config_id = data['model_config_id']
        if 'ocr_config' in data:
            config.ocr_config = data['ocr_config']
        if 'storage_tables' in data:
            config.storage_tables = data['storage_tables']
        if 'adapter_class' in data:
            config.adapter_class = data['adapter_class']
        if 'adapter_module' in data:
            config.adapter_module = data['adapter_module']
        if 'form_config' in data:
            config.form_config = data['form_config']
        if 'form_component' in data:
            config.form_component = data['form_component']
        if 'validation_rules' in data:
            config.validation_rules = data['validation_rules']
        if 'is_active' in data:
            config.is_active = data['is_active']
        if 'sort_order' in data:
            config.sort_order = data['sort_order']
        
        db.session.commit()
        
        logger.info(f"✅ 文件类型配置更新成功: {config.type_code}")
        
        return jsonify({
            'success': True,
            'message': '更新成功',
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新文件类型配置失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/<int:config_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_file_type_config(config_id):
    """删除文件类型配置"""
    try:
        config = FileTypeConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '文件类型配置不存在'
            }), 404
        
        type_code = config.type_code
        
        db.session.delete(config)
        db.session.commit()
        
        logger.info(f"✅ 文件类型配置删除成功: {type_code} (ID: {config_id})")
        
        return jsonify({
            'success': True,
            'message': '删除成功'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除文件类型配置失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/<int:config_id>/toggle-active', methods=['PATCH'])
@jwt_required()
@admin_required
def toggle_file_type_config_active(config_id):
    """切换文件类型配置的启用状态"""
    try:
        config = FileTypeConfig.query.get(config_id)
        if not config:
            return jsonify({
                'success': False,
                'message': '文件类型配置不存在'
            }), 404
        
        data = request.get_json()
        is_active = data.get('is_active')
        
        if is_active is None:
            return jsonify({
                'success': False,
                'message': '缺少is_active参数'
            }), 400
        
        config.is_active = is_active
        db.session.commit()
        
        logger.info(f"✅ 文件类型配置状态切换成功: {config.type_code} -> {'启用' if is_active else '禁用'}")
        
        return jsonify({
            'success': True,
            'message': '状态切换成功',
            'data': config.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'切换状态失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'切换状态失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/adapters', methods=['GET'])
@jwt_required()
def get_adapters():
    """获取所有可用的适配器列表"""
    try:
        # 这里可以动态扫描适配器目录，或者返回预定义列表
        adapters = [
            {
                'name': 'CommissionAdapter',
                'description': '委托单适配器',
                'module': 'adapters'
            },
            {
                'name': 'PaperAdapter',
                'description': '论文适配器',
                'module': 'adapters'
            }
        ]
        
        return jsonify({
            'success': True,
            'data': adapters
        }), 200
        
    except Exception as e:
        logger.error(f'获取适配器列表失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取适配器列表失败: {str(e)}'
        }), 500


@api_bp.route('/file-type-configs/database-tables', methods=['GET'])
@jwt_required()
def get_database_tables():
    """获取数据库表列表"""
    try:
        from sqlalchemy import inspect
        
        # 获取数据库引擎的 inspector
        inspector = inspect(db.engine)
        
        # 获取所有表名
        all_tables = inspector.get_table_names()
        
        # 过滤系统表，只返回业务表
        # 排除 alembic、用户表等系统表
        excluded_tables = {'alembic_version', 'users', 'roles', 'user_roles'}
        
        business_tables = [
            {
                'name': table,
                'label': table.replace('_', ' ').title()  # 格式化显示名称
            }
            for table in sorted(all_tables)
            if table not in excluded_tables
        ]
        
        return jsonify({
            'success': True,
            'data': business_tables
        }), 200
        
    except Exception as e:
        logger.error(f'获取数据库表列表失败: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取数据库表列表失败: {str(e)}'
        }), 500


