"""
数据分析智能体视图
处理材料数据分析相关的HTTP请求
支持流式/阻塞响应，返回柱状图、饼状图、热力图、表格等可视化数据
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

from .data_analysis_business import data_analysis_service
from .models import AgentTask
from .serializers import AgentTaskSerializer

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def data_analysis_submit(request):
    """
    提交数据分析任务（阻塞模式）

    POST /api/smart-agent/data-analysis/submit/

    Request Body:
    {
        "data_content": "材料名称,导电率,热稳定性,成本\\n石墨烯,高,高,贵\\n碳纳米管,高,中,中...",
        "analysis_type": "comprehensive",   // trend/pattern/comparison/distribution/correlation/comprehensive
        "data_description": "这是一批锂电池正极材料的性能测试数据",
        "analysis_goal": "分析各材料的性能分布，找出高性价比材料",
        "title": "可选任务标题",
        "description": "可选任务描述"
    }

    Response:
    {
        "success": true,
        "task_id": "uuid",
        "result": {
            "answer": "文字分析结论...",
            "visualization": {
                "charts": [
                    {
                        "type": "bar",
                        "title": "各材料导电率对比",
                        "data": { "labels": [...], "datasets": [...] }
                    },
                    {
                        "type": "pie",
                        "title": "成本分布",
                        "data": { "labels": [...], "datasets": [...] }
                    },
                    {
                        "type": "heatmap",
                        "title": "性能相关性热力图",
                        "data": { "xLabels": [...], "yLabels": [...], "values": [[...]] }
                    }
                ],
                "tables": [
                    {
                        "title": "材料性能汇总",
                        "columns": ["材料名称", "导电率", "热稳定性", "成本"],
                        "rows": [[...], [...]]
                    }
                ],
                "summary": "综合结论..."
            }
        }
    }
    """
    try:
        inputs = {
            'data_content': request.data.get('data_content', ''),
            'analysis_type': request.data.get('analysis_type', 'comprehensive'),
            'data_description': request.data.get('data_description', ''),
            'analysis_goal': request.data.get('analysis_goal', '')
        }

        validation = data_analysis_service.validate_inputs(inputs)
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

        task = data_analysis_service.create_analysis_task(
            user=user,
            inputs=inputs,
            title=request.data.get('title'),
            description=request.data.get('description')
        )

        result = data_analysis_service.execute_analysis_blocking(task)

        if result['success']:
            return Response({
                'success': True,
                'message': '分析完成',
                'task_id': str(task.id),
                'task': AgentTaskSerializer(task).data,
                'result': result['result']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': '分析失败',
                'task_id': str(task.id),
                'error': result['error']
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    except Exception as e:
        logger.error(f"提交数据分析任务失败: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def data_analysis_stream(request):
    """
    提交数据分析任务（流式响应 SSE）

    POST /api/smart-agent/data-analysis/stream/

    Request Body: 同 submit 接口

    Response: Server-Sent Events 格式，事件类型：
        - task_created: 任务创建成功
        - message: AI 回答片段
        - thought: Agent 思考过程
        - visualization: 解析后的可视化数据（包含 charts/tables/summary）
        - complete: 完成
        - error: 错误
        - done: 流结束标记
    """
    try:
        inputs = {
            'data_content': request.data.get('data_content', ''),
            'analysis_type': request.data.get('analysis_type', 'comprehensive'),
            'data_description': request.data.get('data_description', ''),
            'analysis_goal': request.data.get('analysis_goal', '')
        }

        validation = data_analysis_service.validate_inputs(inputs)
        if not validation['valid']:
            def error_generator():
                yield f"data: {json.dumps({'event': 'error', 'errors': validation['errors']}, ensure_ascii=False)}\n\n"
            return StreamingHttpResponse(
                error_generator(),
                content_type='text/event-stream'
            )

        user = request.user if request.user.is_authenticated else None
        if not user:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user, _ = User.objects.get_or_create(username='anonymous')

        task = data_analysis_service.create_analysis_task(
            user=user,
            inputs=inputs,
            title=request.data.get('title'),
            description=request.data.get('description')
        )

        def event_stream():
            """生成 SSE 格式的流式响应"""
            try:
                yield f"data: {json.dumps({'event': 'task_created', 'task_id': str(task.id)}, ensure_ascii=False)}\n\n"

                for event in data_analysis_service.execute_analysis_streaming(task):
                    event_type = event.get('type', 'unknown')
                    event_data = event.get('data', {})

                    sse_data = {
                        'event': event_type,
                        **event_data
                    }
                    yield f"data: {json.dumps(sse_data, ensure_ascii=False)}\n\n"

                yield f"data: {json.dumps({'event': 'done'}, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.error(f"流式执行出错: {str(e)}", exc_info=True)
                yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    except Exception as e:
        logger.error(f"提交流式数据分析任务失败: {str(e)}", exc_info=True)

        def error_generator():
            yield f"data: {json.dumps({'event': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

        return StreamingHttpResponse(
            error_generator(),
            content_type='text/event-stream'
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_analysis_history(request):
    """
    获取用户的数据分析历史记录

    GET /api/smart-agent/data-analysis/history/

    Query Parameters:
    - limit: 返回数量限制（默认20，最多100）
    """
    try:
        limit = int(request.query_params.get('limit', 20))
        limit = min(limit, 100)

        tasks = data_analysis_service.get_task_history(
            user=request.user,
            limit=limit
        )

        return Response({
            'success': True,
            'count': len(tasks),
            'tasks': AgentTaskSerializer(tasks, many=True).data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"获取数据分析历史记录失败: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_analysis_task_detail(request, task_id):
    """
    获取数据分析任务详情

    GET /api/smart-agent/data-analysis/task/{task_id}/

    返回任务信息，包括 output_data.visualization 中的可视化数据
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
        logger.error(f"获取数据分析任务详情失败: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def data_analysis_types(request):
    """
    获取支持的分析类型列表

    GET /api/smart-agent/data-analysis/types/

    Response:
    {
        "success": true,
        "analysis_types": {
            "trend": "趋势分析",
            "pattern": "模式识别",
            "comparison": "对比分析",
            "distribution": "分布分析",
            "correlation": "相关性分析",
            "comprehensive": "综合分析"
        }
    }
    """
    return Response({
        'success': True,
        'analysis_types': data_analysis_service.get_supported_analysis_types()
    }, status=status.HTTP_200_OK)
