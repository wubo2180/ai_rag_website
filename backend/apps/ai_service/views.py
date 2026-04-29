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
from .models import KnowledgeExtractionHistory

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class KnowledgeExtractionView(View):
    """知识抽取API视图"""

    @staticmethod
    def _get_item_count(extracted_knowledge):
        if isinstance(extracted_knowledge, list):
            return len(extracted_knowledge)
        if extracted_knowledge:
            return 1
        return 0

    @staticmethod
    def _get_file_type(filename: str) -> str:
        if not filename or '.' not in filename:
            return 'FILE'
        return filename.split('.')[-1].upper()

    @staticmethod
    def _record_history(user_id, filename, file_size, status, item_count=0, elapsed_time=None, error_message=''):
        try:
            KnowledgeExtractionHistory.objects.create(
                user_id=user_id or 'anonymous',
                file_name=filename,
                file_type=KnowledgeExtractionView._get_file_type(filename),
                file_size=file_size or 0,
                status=status,
                item_count=item_count,
                elapsed_time=elapsed_time,
                error_message=error_message or ''
            )
        except Exception as history_error:
            logger.error(f"写入知识抽取历史失败: {str(history_error)}")
    
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
                data = result.get('data', {})
                extracted_knowledge = data.get('extracted_knowledge')
                elapsed_time = data.get('elapsed_time')
                item_count = self._get_item_count(extracted_knowledge)
                self._record_history(
                    user_id=user_id,
                    filename=filename,
                    file_size=uploaded_file.size,
                    status='success',
                    item_count=item_count,
                    elapsed_time=elapsed_time
                )
                return JsonResponse({
                    'status': 'success',
                    'data': data,
                    'message': '知识抽取完成'
                })
            else:
                error_message = result.get('message', '知识抽取失败')
                self._record_history(
                    user_id=user_id,
                    filename=filename,
                    file_size=uploaded_file.size,
                    status='failed',
                    error_message=error_message
                )
                return JsonResponse({
                    'status': 'error',
                    'message': error_message,
                    'details': result.get('details')
                }, status=500)
                
        except Exception as e:
            logger.error(f"知识抽取请求处理异常: {str(e)}")
            try:
                if 'uploaded_file' in locals():
                    self._record_history(
                        user_id=request.POST.get('user_id', 'anonymous'),
                        filename=uploaded_file.name,
                        file_size=uploaded_file.size,
                        status='failed',
                        error_message=str(e)
                    )
            except Exception:
                pass
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


@method_decorator(csrf_exempt, name='dispatch')
class KnowledgeExtractionHistoryView(View):
    """知识抽取历史记录API"""

    def get(self, request):
        user_id = request.GET.get('user_id', 'anonymous')
        try:
            limit = int(request.GET.get('limit', 30))
        except ValueError:
            limit = 30
        limit = max(1, min(limit, 100))

        items = list(
            KnowledgeExtractionHistory.objects.filter(user_id=user_id)
            .order_by('-created_at')
            .values(
                'id',
                'file_name',
                'file_type',
                'file_size',
                'status',
                'item_count',
                'elapsed_time',
                'error_message',
                'created_at'
            )[:limit]
        )

        for item in items:
            item['extracted_at'] = item.pop('created_at')

        return JsonResponse({
            'status': 'success',
            'data': {
                'items': items,
                'count': len(items)
            }
        })

    def delete(self, request):
        user_id = request.GET.get('user_id')
        if not user_id:
            try:
                payload = json.loads(request.body or '{}')
                user_id = payload.get('user_id')
            except json.JSONDecodeError:
                user_id = None

        if not user_id:
            return JsonResponse({
                'status': 'error',
                'message': '缺少 user_id'
            }, status=400)

        deleted_count, _ = KnowledgeExtractionHistory.objects.filter(user_id=user_id).delete()

        return JsonResponse({
            'status': 'success',
            'message': '历史记录已清空',
            'deleted_count': deleted_count
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