"""
工艺优化智能体视图
处理工艺优化相关的HTTP请求
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .formula_generation_business import process_optimization_service
from .models import AgentTask
from .serializers import AgentTaskSerializer

logger = logging.getLogger(__name__)


def _resolve_agent_category_from_path(path: str) -> str:
    """根据请求路径推断智能体分类。"""
    path_val = (path or '').lower()
    if '/formula-generation/' in path_val:
        return 'formula_generation'
    return 'process_optimization'


@api_view(['POST'])
@permission_classes([AllowAny])  # 可以根据需要改为 IsAuthenticated
def process_optimization_submit(request):
    """
    提交工艺优化任务（阻塞模式）
    
    POST /api/smart-agent/process-optimization/submit/
    
    Request Body:
    {
        "product_performance_requirements": "产品性能要求",
        "target_application_scenario": "目标应用场景",
        "cost_consideration": "成本预算范围",
        "environmental_requirements": "环保要求",
        "optimization_targets": "优化目标",
        "process_parameters": "可调工艺参数及范围",
        "material_product_data": "材料与产品规格",
        "knowledge_constraints": "知识与约束",
        "historical_data": "历史数据（可选）",
        "environmental_real_time_data": "环境与实时数据（可选）",
        "expected_performance": "预期性能（可选）",
        "cost_consideration": "单公斤成本控制在 200 元以内",
        "environmental_requirements": "符合 RoHS/REACH，无卤、低VOC 排放",
        "title": "可选的任务标题",
        "description": "可选的任务描述"
    }
    """
    try:
        # 获取输入参数
        inputs = {
            'product_performance_requirements': request.data.get('product_performance_requirements', ''),
            'optimization_targets': request.data.get('optimization_targets', ''),
            'process_parameters': request.data.get('process_parameters', ''),
            'material_product_data': request.data.get('material_product_data', ''),
            'knowledge_constraints': request.data.get('knowledge_constraints', ''),
            'historical_data': request.data.get('historical_data', ''),
            'environmental_real_time_data': request.data.get('environmental_real_time_data', ''),
            'expected_performance': request.data.get('expected_performance', ''),
            'cost_consideration': request.data.get('cost_consideration', ''),
            'environmental_requirements': request.data.get('environmental_requirements', ''),
            # 兼容旧版字段
            'product_performance': request.data.get('product_performance', ''),
            'target_application_scenario': request.data.get('target_application_scenario', '')
        }
        
        # 验证输入
        validation = process_optimization_service.validate_inputs(inputs)
        if not validation['valid']:
            return Response({
                'success': False,
                'errors': validation['errors']
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取用户（如果未认证，使用匿名用户）
        user = request.user if request.user.is_authenticated else None
        if not user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, _ = User.objects.get_or_create(username='anonymous')
        
        # 创建任务
        agent_category = _resolve_agent_category_from_path(request.path)
        task = process_optimization_service.create_optimization_task(
            user=user,
            inputs=inputs,
            agent_category=agent_category,
            title=request.data.get('title'),
            description=request.data.get('description')
        )
        
        # 执行任务（阻塞模式）
        result = process_optimization_service.execute_optimization_blocking(task)
        
        if result['success']:
            return Response({
                'success': True,
                'message': '优化完成',
                'task_id': str(task.id),
                'task': AgentTaskSerializer(task).data,
                'result': result['result']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': '优化失败',
                'task_id': str(task.id),
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    except Exception as e:
        logger.error(f"提交工艺优化任务失败: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def process_optimization_stream(request):
    """
    提交工艺优化任务（流式响应）
    
    POST /api/smart-agent/process-optimization/stream/
    
    Request Body: 同 submit 接口
    
    Response: Server-Sent Events (SSE) 格式
    """
    try:
        # 获取输入参数
        inputs = {
            'product_performance_requirements': request.data.get('product_performance_requirements', ''),
            'optimization_targets': request.data.get('optimization_targets', ''),
            'process_parameters': request.data.get('process_parameters', ''),
            'material_product_data': request.data.get('material_product_data', ''),
            'knowledge_constraints': request.data.get('knowledge_constraints', ''),
            'historical_data': request.data.get('historical_data', ''),
            'environmental_real_time_data': request.data.get('environmental_real_time_data', ''),
            'expected_performance': request.data.get('expected_performance', ''),
            'cost_consideration': request.data.get('cost_consideration', ''),
            'environmental_requirements': request.data.get('environmental_requirements', ''),
            # 兼容旧版字段
            'product_performance': request.data.get('product_performance', ''),
            'target_application_scenario': request.data.get('target_application_scenario', '')
        }
        
        # 验证输入
        validation = process_optimization_service.validate_inputs(inputs)
        if not validation['valid']:
            # 流式响应也返回错误
            def error_generator():
                yield f"data: {json.dumps({'event': 'error', 'errors': validation['errors']}, ensure_ascii=False)}\n\n".encode('utf-8')
            
            return StreamingHttpResponse(
                error_generator(),
                content_type='text/event-stream'
            )
        
        # 获取用户
        user = request.user if request.user.is_authenticated else None
        if not user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, _ = User.objects.get_or_create(username='anonymous')
        
        # 创建任务
        agent_category = _resolve_agent_category_from_path(request.path)
        task = process_optimization_service.create_optimization_task(
            user=user,
            inputs=inputs,
            agent_category=agent_category,
            title=request.data.get('title'),
            description=request.data.get('description')
        )
        
        # 流式响应生成器
        def event_stream():
            """生成SSE格式的流式响应"""
            try:
                # 发送任务创建事件
                yield f"data: {json.dumps({'event': 'task_created', 'task_id': str(task.id)}, ensure_ascii=False)}\n\n".encode('utf-8')
                
                # 执行任务并流式返回结果
                for event in process_optimization_service.execute_optimization_streaming(task):
                    event_type = event.get('type', 'unknown')
                    event_data = event.get('data', {})
                    
                    # 转换为SSE格式
                    sse_data = {
                        'event': event_type,
                        **event_data
                    }
                    
                    yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n".encode('utf-8')
                
                # 发送完成标记
                yield f"data: {json.dumps({'event': 'done'}, ensure_ascii=False)}\n\n".encode('utf-8')
            
            except Exception as e:
                logger.error(f"流式执行出错: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n".encode('utf-8')
        
        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        
        return response
    
    except Exception as e:
        logger.error(f"提交流式工艺优化任务失败: {str(e)}", exc_info=True)
        
        def error_generator():
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n".encode('utf-8')
        
        return StreamingHttpResponse(
            error_generator(),
            content_type='text/event-stream'
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def process_optimization_history(request):
    """
    获取用户的工艺优化历史记录
    
    GET /api/smart-agent/process-optimization/history/
    
    Query Parameters:
    - limit: 返回数量限制（默认20）
    """
    try:
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 100)  # 最多100条
        
        tasks = process_optimization_service.get_task_history(
            user=request.user,
            limit=limit
        )
        
        return Response({
            'success': True,
            'count': len(tasks),
            'tasks': AgentTaskSerializer(tasks, many=True).data
        }, status=status.HTTP_200_OK)
    
    except Exception as e:
        logger.error(f"获取历史记录失败: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def process_optimization_task_detail(request, task_id):
    """
    获取任务详情
    
    GET /api/smart-agent/process-optimization/task/{task_id}/
    """
    try:
        task = AgentTask.objects.get(id=task_id, created_by=request.user)
        
        return Response({
            'success': True,
            'task': AgentTaskSerializer(task).data
        }, status=status.HTTP_200_OK)
    
    except AgentTask.DoesNotExist:
        return Response({
            'success': False,
            'error': '任务不存在或无权访问'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"获取任务详情失败: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
