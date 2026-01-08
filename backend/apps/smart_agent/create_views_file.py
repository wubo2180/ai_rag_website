# 临时脚本用于创建process_optimization_views.py

content = '''"""
工艺优化智能体视图
处理工艺优化相关的HTTP请求
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import StreamingHttpResponse
import json
import logging

from .process_optimization_business import process_optimization_business_service
from .models import AgentTask
from .serializers import AgentTaskSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def process_optimization_submit(request):
    """提交工艺优化任务（阻塞模式）"""
    try:
        inputs = {
            'optimization_targets': request.data.get('optimization_targets', ''),
            'process_parameters': request.data.get('process_parameters', ''),
            'material_product_data': request.data.get('material_product_data', ''),
            'environmental_real_time_data': request.data.get('environmental_real_time_data', ''),
            'knowledge_constraints': request.data.get('knowledge_constraints', ''),
            'historical_data': request.data.get('historical_data', ''),
            'cost_consideration': request.data.get('cost_consideration', ''),
            'environmental_requirements': request.data.get('environmental_requirements', ''),
            'expected_performance': request.data.get('expected_performance', '')
        }
        
        validation = process_optimization_business_service.validate_inputs(inputs)
        if not validation['valid']:
            return Response({
                'success': False,
                'errors': validation['errors']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user if request.user.is_authenticated else None
        if not user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, _ = User.objects.get_or_create(username='anonymous')
        
        task = process_optimization_business_service.create_optimization_task(
            user=user,
            inputs=inputs,
            title=request.data.get('title'),
            description=request.data.get('description')
        )
        
        result = process_optimization_business_service.execute_optimization_blocking(task)
        
        if not result.get('error'):
            return Response({
                'success': True,
                'message': '优化完成',
                'task_id': str(task.id),
                'task': AgentTaskSerializer(task).data,
                'result': result
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': '优化失败',
                'task_id': str(task.id),
                'error': result.get('message', '未知错误')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"提交工艺优化任务失败: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def process_optimization_stream(request):
    """提交工艺优化任务（流式响应）"""
    try:
        inputs = {
            'optimization_targets': request.data.get('optimization_targets', ''),
            'process_parameters': request.data.get('process_parameters', ''),
            'material_product_data': request.data.get('material_product_data', ''),
            'environmental_real_time_data': request.data.get('environmental_real_time_data', ''),
            'knowledge_constraints': request.data.get('knowledge_constraints', ''),
            'historical_data': request.data.get('historical_data', ''),
            'cost_consideration': request.data.get('cost_consideration', ''),
            'environmental_requirements': request.data.get('environmental_requirements', ''),
            'expected_performance': request.data.get('expected_performance', '')
        }
        
        validation = process_optimization_business_service.validate_inputs(inputs)
        if not validation['valid']:
            def error_stream():
                yield f"data: {json.dumps({'event': 'error', 'errors': validation['errors']}, ensure_ascii=False)}\\n\\n"
            return StreamingHttpResponse(error_stream(), content_type='text/event-stream', status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user if request.user.is_authenticated else None
        if not user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, _ = User.objects.get_or_create(username='anonymous')
        
        task = process_optimization_business_service.create_optimization_task(
            user=user,
            inputs=inputs,
            title=request.data.get('title'),
            description=request.data.get('description')
        )
        
        def event_stream():
            try:
                yield f"data: {json.dumps({'event': 'task_created', 'task_id': str(task.id)}, ensure_ascii=False)}\\n\\n"
                for event_data in process_optimization_business_service.execute_optimization_streaming(task):
                    if isinstance(event_data, dict):
                        yield f"data: {json.dumps(event_data, ensure_ascii=False)}\\n\\n"
                yield f"data: {json.dumps({'event': 'done', 'task_id': str(task.id)}, ensure_ascii=False)}\\n\\n"
            except Exception as e:
                logger.error(f"流式执行失败: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\\n\\n"
        
        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
    
    except Exception as e:
        logger.error(f"创建流式任务失败: {str(e)}", exc_info=True)
        def error_stream():
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\\n\\n"
        return StreamingHttpResponse(error_stream(), content_type='text/event-stream', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def process_optimization_task_detail(request, task_id):
    """获取任务详情"""
    try:
        task = AgentTask.objects.get(id=task_id)
        return Response({'success': True, 'task': AgentTaskSerializer(task).data}, status=status.HTTP_200_OK)
    except AgentTask.DoesNotExist:
        return Response({'success': False, 'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def process_optimization_task_list(request):
    """获取任务列表"""
    try:
        if request.user.is_authenticated:
            tasks = AgentTask.objects.filter(agent__category='process_optimization', created_by=request.user).order_by('-created_at')
        else:
            tasks = AgentTask.objects.none()
        return Response({'success': True, 'tasks': AgentTaskSerializer(tasks, many=True).data, 'count': tasks.count()}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"获取任务列表失败: {str(e)}", exc_info=True)
        return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
'''

# 写入文件
with open('process_optimization_views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("文件创建成功!")
