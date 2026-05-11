"""
Flask应用主入口文件
"""
import os
from flask import Flask
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config.config import config_map

# 从models模块导入统一的db实例
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
from models import db

# 初始化其他扩展
migrate = Migrate()
jwt = JWTManager()
cors = CORS()


def create_db_app(config_name=None):
    """
    创建只用于数据库操作的简化Flask应用
    """
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    config_class = config_map.get(config_name, config_map['default'])
    app.config.from_object(config_class)
    
    # 只初始化数据库相关扩展
    db.init_app(app)
    
    # 初始化所有模型
    with app.app_context():
        from models import get_models
        get_models()  # 确保所有模型都已导入
    
    return app


def create_app(config_name=None):
    """
    Flask应用工厂函数
    """
    app = Flask(__name__)
    
    # 加载配置
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    config_class = config_map.get(config_name, config_map['default'])
    app.config.from_object(config_class)
    
    # 调试JWT配置
    print(f"🔧 JWT调试信息:")
    print(f"   JWT_SECRET_KEY: {app.config.get('JWT_SECRET_KEY')}")
    print(f"   SECRET_KEY: {app.config.get('SECRET_KEY')}")
    print(f"   JWT_ACCESS_TOKEN_EXPIRES: {app.config.get('JWT_ACCESS_TOKEN_EXPIRES')}")
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 初始化所有模型
    with app.app_context():
        from models import get_models
        get_models()  # 确保所有模型都已导入
    
    # 注册蓝图
    sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))
    from api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return {'message': '资源不存在'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'message': '服务器内部错误'}, 500
    
    # JWT错误处理 - 添加调试信息
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        print(f"🚨 JWT过期: header={jwt_header}, payload={jwt_payload}")
        return {'message': 'Token已过期'}, 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        print(f"🚨 JWT无效: error={error}")
        return {'message': 'Token无效'}, 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        print(f"🚨 JWT缺失: error={error}")
        return {'message': '需要提供Token'}, 401
    
    return app


if __name__ == '__main__':
    app = create_app()
    # 关闭自动重载，避免 PaddleOCR 崩溃
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
