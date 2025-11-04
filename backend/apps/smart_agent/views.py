"""
智能体模块视图
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from .models import SmartAgent, AgentTask, AgentExecution, AgentFeedback, TaskStatus
from .serializers import (
    SmartAgentSerializer, SmartAgentListSerializer,
    AgentTaskSerializer, AgentTaskListSerializer,
    AgentExecutionSerializer, AgentFeedbackSerializer
)
from .engine import execute_agent_task


class SmartAgentViewSet(viewsets.ModelViewSet):
    """智能体视图集"""
    
    queryset = SmartAgent.objects.all()
    serializer_class = SmartAgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return SmartAgentListSerializer
        return SmartAgentSerializer
    
    def get_queryset(self):
        """过滤查询集"""
        queryset = SmartAgent.objects.all()
        
        # 按分类过滤
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # 只显示公开的智能体（除非是创建者）
        if self.action == 'list':
            user = self.request.user
            queryset = queryset.filter(
                Q(is_public=True) | Q(created_by=user)
            )
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(display_name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-popularity_score', '-created_at')
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """执行智能体任务"""
        agent = self.get_object()
        
        # 创建任务
        task_data = {
            'agent': agent.id,
            'title': request.data.get('title', f'执行{agent.display_name}'),
            'description': request.data.get('description', ''),
            'input_data': request.data.get('input_data', {})
        }
        
        task_serializer = AgentTaskSerializer(data=task_data, context={'request': request})
        if task_serializer.is_valid():
            task = task_serializer.save()
            
            # 更新智能体使用次数
            agent.usage_count += 1
            agent.save(update_fields=['usage_count'])
            
            # 执行任务
            try:
                result = execute_agent_task(str(task.id))
                return Response({
                    'message': '任务执行完成',
                    'task_id': task.id,
                    'task': AgentTaskSerializer(task).data,
                    'result': result
                }, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({
                    'message': '任务执行失败',
                    'task_id': task.id,
                    'error': str(e),
                    'task': AgentTaskSerializer(task).data
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(task_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取智能体统计信息"""
        agent = self.get_object()
        
        # 最近30天的任务统计
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_tasks = agent.tasks.filter(created_at__gte=thirty_days_ago)
        
        stats = {
            'total_tasks': agent.tasks.count(),
            'recent_tasks': recent_tasks.count(),
            'success_rate': agent.success_rate,
            'average_execution_time': agent.average_execution_time,
            'popularity_score': agent.popularity_score,
            'usage_count': agent.usage_count,
            'status_distribution': agent.tasks.values('status').annotate(
                count=Count('status')
            ),
            'recent_feedback_avg': agent.feedbacks.filter(
                created_at__gte=thirty_days_ago
            ).aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取智能体分类统计"""
        categories = SmartAgent.objects.values('category').annotate(
            count=Count('category'),
            avg_popularity=Avg('popularity_score')
        ).order_by('-count')
        
        return Response(categories)


class AgentTaskViewSet(viewsets.ModelViewSet):
    """智能体任务视图集"""
    
    queryset = AgentTask.objects.all()
    serializer_class = AgentTaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'list':
            return AgentTaskListSerializer
        return AgentTaskSerializer
    
    def get_queryset(self):
        """过滤查询集"""
        queryset = AgentTask.objects.all()
        
        # 只显示用户自己的任务
        user = self.request.user
        queryset = queryset.filter(created_by=user)
        
        # 按智能体过滤
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        # 按状态过滤
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """取消任务"""
        task = self.get_object()
        
        if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task.status = TaskStatus.CANCELLED
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at'])
            
            return Response({'message': '任务已取消'})
        
        return Response(
            {'error': '只能取消等待中或执行中的任务'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['get'])
    def executions(self, request, pk=None):
        """获取任务执行记录"""
        task = self.get_object()
        executions = task.executions.all()
        serializer = AgentExecutionSerializer(executions, many=True)
        return Response(serializer.data)


class AgentExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """执行记录视图集"""
    
    queryset = AgentExecution.objects.all()
    serializer_class = AgentExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """过滤查询集"""
        queryset = AgentExecution.objects.all()
        
        # 只显示用户自己的执行记录
        user = self.request.user
        queryset = queryset.filter(task__created_by=user)
        
        # 按任务过滤
        task_id = self.request.query_params.get('task_id')
        if task_id:
            queryset = queryset.filter(task_id=task_id)
        
        return queryset.order_by('step_order')


class AgentFeedbackViewSet(viewsets.ModelViewSet):
    """智能体反馈视图集"""
    
    queryset = AgentFeedback.objects.all()
    serializer_class = AgentFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """过滤查询集"""
        queryset = AgentFeedback.objects.all()
        
        # 按智能体过滤
        agent_id = self.request.query_params.get('agent_id')
        if agent_id:
            queryset = queryset.filter(agent_id=agent_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """创建反馈时更新智能体评分"""
        feedback = serializer.save()
        
        # 重新计算智能体的平均评分
        agent = feedback.agent
        avg_rating = agent.feedbacks.aggregate(avg_rating=Avg('rating'))['avg_rating']
        if avg_rating:
            agent.popularity_score = min(avg_rating * 2, 10.0)  # 转换为10分制
            agent.save(update_fields=['popularity_score'])
