"""
健康检查和系统状态API
"""
import psutil
import time
from datetime import datetime
from flask import jsonify
from sqlalchemy import text
from . import api_bp
from models import db
from services.minio_service import MinioService


@api_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    try:
        start_time = time.time()
        
        # 检查数据库连接
        db_status = check_database()
        
        # 检查MinIO连接
        minio_status = check_minio()
        
        # 获取系统信息
        system_info = get_system_info()
        
        response_time = round((time.time() - start_time) * 1000, 2)
        
        # 确定整体状态
        overall_status = 'healthy'
        if not db_status['connected'] or not minio_status['connected']:
            overall_status = 'degraded'
        
        return jsonify({
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'response_time_ms': response_time,
            'services': {
                'database': db_status,
                'minio': minio_status
            },
            'system': system_info
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500


def check_database():
    """检查数据库连接状态"""
    try:
        # 执行简单查询测试连接
        db.session.execute(text('SELECT 1'))
        return {
            'name': 'Database',
            'connected': True,
            'status': 'healthy'
        }
    except Exception as e:
        return {
            'name': 'Database',
            'connected': False,
            'status': 'unhealthy',
            'error': str(e)
        }


def check_minio():
    """检查MinIO连接状态"""
    try:
        minio_service = MinioService()
        # 尝试列出存储桶
        minio_service.client.list_buckets()
        return {
            'name': 'MinIO',
            'connected': True,
            'status': 'healthy'
        }
    except Exception as e:
        return {
            'name': 'MinIO',
            'connected': False,
            'status': 'unhealthy',
            'error': str(e)
        }


def get_system_info():
    """获取系统信息"""
    try:
        # 获取CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 获取内存使用情况
        memory = psutil.virtual_memory()
        
        # 获取磁盘使用情况
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_usage_percent': cpu_percent,
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percent': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': round((disk.used / disk.total) * 100, 2)
            },
            'uptime': time.time() - psutil.boot_time()
        }
    except Exception as e:
        return {
            'error': f'无法获取系统信息: {str(e)}'
        }


@api_bp.route('/version', methods=['GET'])
def get_version():
    """获取系统版本信息"""
    return jsonify({
        'name': 'OCR数据识别系统',
        'version': '1.0.0',
        'api_version': 'v1',
        'build_time': '2024-01-15T10:00:00Z',
        'description': '基于OCR技术的检测报表识别系统'
    }), 200


@api_bp.route('/stats/summary', methods=['GET'])
def get_system_summary():
    """获取系统概览统计"""
    try:
        from models.file import File
        from models.user import User
        from models.ocr_result import OCRResult
        
        # 文件统计
        total_files = File.query.filter_by(is_deleted=False).count()
        pending_files = File.query.filter_by(ocr_status='pending', is_deleted=False).count()
        processing_files = File.query.filter_by(ocr_status='processing', is_deleted=False).count()
        completed_files = File.query.filter_by(ocr_status='completed', is_deleted=False).count()
        failed_files = File.query.filter_by(ocr_status='failed', is_deleted=False).count()
        
        # 用户统计
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        
        # OCR结果统计
        total_ocr_results = OCRResult.query.count()
        reviewed_results = OCRResult.query.filter_by(is_reviewed=True).count()
        
        return jsonify({
            'success': True,
            'data': {
                'files': {
                    'total': total_files,
                    'pending': pending_files,
                    'processing': processing_files,
                    'completed': completed_files,
                    'failed': failed_files
                },
                'users': {
                    'total': total_users,
                    'active': active_users,
                    'inactive': total_users - active_users
                },
                'ocr': {
                    'total_results': total_ocr_results,
                    'reviewed': reviewed_results,
                    'pending_review': total_ocr_results - reviewed_results,
                    'review_rate': round((reviewed_results / total_ocr_results * 100), 2) if total_ocr_results > 0 else 0
                }
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取统计信息失败: {str(e)}'
        }), 500
