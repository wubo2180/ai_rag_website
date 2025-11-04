"""
AI服务视图
"""

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
from .dify_service import dify_service

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class KnowledgeExtractionView(View):
    """知识抽取API视图"""
    
    def post(self, request):
        """
        处理知识抽取请求
        """
        try:
            # 检查是否有文件上传
            if 'file' not in request.FILES:
                return JsonResponse({
                    'status': 'error',
                    'message': '请上传文件'
                }, status=400)
            
            uploaded_file = request.FILES['file']
            
            # 检查文件大小（限制为10MB）
            max_size = 10 * 1024 * 1024  # 10MB
            if uploaded_file.size > max_size:
                return JsonResponse({
                    'status': 'error',
                    'message': '文件大小不能超过10MB'
                }, status=400)
            
            # 获取用户标识（如果有的话）
            user_id = request.POST.get('user_id', 'anonymous')
            
            # 读取文件数据
            file_data = uploaded_file.read()
            filename = uploaded_file.name
            
            logger.info(f"开始处理知识抽取请求，文件: {filename}, 大小: {uploaded_file.size} bytes")
            
            # 调用Dify服务处理文件
            result = dify_service.process_file_with_workflow(
                file_data=file_data,
                filename=filename,
                user=user_id
            )
            
            if result.get('status') == 'success':
                return JsonResponse({
                    'status': 'success',
                    'data': result.get('data', {}),
                    'message': '知识抽取完成'
                })
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': result.get('message', '知识抽取失败'),
                    'details': result.get('details')
                }, status=500)
                
        except Exception as e:
            logger.error(f"知识抽取请求处理异常: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'服务器内部错误: {str(e)}'
            }, status=500)
    
    def get(self, request):
        """
        获取知识抽取服务信息
        """
        return JsonResponse({
            'status': 'success',
            'service': 'knowledge_extraction',
            'description': '知识抽取服务，支持从文档中提取结构化知识',
            'supported_formats': ['pdf', 'txt', 'docx', 'md'],
            'max_file_size': '10MB'
        })


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    健康检查端点
    """
    try:
        return JsonResponse({
            'status': 'healthy',
            'service': 'ai_service',
            'timestamp': request.META.get('HTTP_DATE'),
            'dify_configured': bool(dify_service.api_url and dify_service.api_key)
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)


@csrf_exempt 
@require_http_methods(["POST"])
def test_dify_connection(request):
    """
    测试Dify连接
    """
    try:
        # 创建一个简单的测试文件
        test_content = "这是一个测试文档，用于验证Dify API连接。"
        test_filename = "test_connection.txt"
        
        # 测试文件上传
        file_id = dify_service.upload_file_from_memory(
            file_data=test_content.encode('utf-8'),
            filename=test_filename,
            user="test_user"
        )
        
        if file_id:
            return JsonResponse({
                'status': 'success',
                'message': 'Dify连接正常',
                'file_id': file_id
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Dify连接失败'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'连接测试失败: {str(e)}'
        }, status=500)