"""
应用配置文件
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基础配置类"""
    
    # 基础配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # 数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'password'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'ocr_system'
    
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_timeout': 20,
        'pool_recycle': -1,
        'pool_pre_ping': True
    }
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # MinIO配置
    MINIO_ENDPOINT = os.environ.get('MINIO_ENDPOINT') or 'localhost:9000'
    MINIO_ACCESS_KEY = os.environ.get('MINIO_ACCESS_KEY') or 'minioadmin'
    MINIO_SECRET_KEY = os.environ.get('MINIO_SECRET_KEY') or 'minioadmin'
    MINIO_BUCKET_NAME = os.environ.get('MINIO_BUCKET_NAME') or 'ocr-files'
    MINIO_SECURE = os.environ.get('MINIO_SECURE', 'False').lower() == 'true'
    
    # Redis配置（用于Celery）
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    CELERY_BROKER_URL = REDIS_URL
    CELERY_RESULT_BACKEND = REDIS_URL
    
    # 文件上传配置
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB
    UPLOAD_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff']
    
    # OCR配置
    OCR_MODEL_DIR = os.environ.get('OCR_MODEL_DIR') or './models'
    OCR_USE_GPU = os.environ.get('OCR_USE_GPU', 'False').lower() == 'true'
    OCR_LANGUAGE = os.environ.get('OCR_LANGUAGE') or 'ch'
    
    # 外部OCR服务配置
    # 委托单OCR服务
    OCR_COMMISSION_SERVICE_URL = os.environ.get('OCR_COMMISSION_SERVICE_URL') or 'http://localhost:6001'
    OCR_COMMISSION_ANALYZE_ENDPOINT = '/api/analyze'  # 委托单分析端点（统一为/api/analyze）
    OCR_COMMISSION_HEALTH_ENDPOINT = '/health'        # 委托单健康检查
    OCR_COMMISSION_TIMEOUT = int(os.environ.get('OCR_COMMISSION_TIMEOUT') or 300)  # 超时时间（秒）
    
    # 论文OCR服务
    OCR_PAPER_SERVICE_URL = os.environ.get('OCR_PAPER_SERVICE_URL') or 'http://localhost:6002'
    OCR_PAPER_ANALYZE_ENDPOINT = '/api/analyze'   # 论文分析端点
    OCR_PAPER_HEALTH_ENDPOINT = '/health'         # 论文健康检查
    OCR_PAPER_TIMEOUT = int(os.environ.get('OCR_PAPER_TIMEOUT') or 300)  # 超时时间（秒）
    
    # OCR请求参数配置
    OCR_DEFAULT_USER = os.environ.get('OCR_DEFAULT_USER') or 'system'  # 默认用户标识
    OCR_DEFAULT_RESPONSE_MODE = 'blocking'  # 默认响应模式
    
    # OCR服务重试配置
    OCR_MAX_RETRIES = int(os.environ.get('OCR_MAX_RETRIES') or 3)
    OCR_RETRY_DELAY = int(os.environ.get('OCR_RETRY_DELAY') or 5)  # 重试延迟（秒）
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL') or 'INFO'
    LOG_FILE = os.environ.get('LOG_FILE') or 'app.log'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# 配置映射
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
