"""
智能体模块URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SmartAgentViewSet,
    AgentTaskViewSet,
    AgentExecutionViewSet,
    AgentFeedbackViewSet
)
from .formula_generation_views import (
    process_optimization_submit,
    process_optimization_stream,
    process_optimization_history,
    process_optimization_task_detail
)

# 创建路由器
router = DefaultRouter()
router.register(r'agents', SmartAgentViewSet, basename='smartagent')
router.register(r'tasks', AgentTaskViewSet, basename='agenttask')
router.register(r'executions', AgentExecutionViewSet, basename='agentexecution')
router.register(r'feedbacks', AgentFeedbackViewSet, basename='agentfeedback')

# URL模式
urlpatterns = [
    path('', include(router.urls)),
    
    # 工艺优化智能体专用接口
    path('process-optimization/submit/', process_optimization_submit, name='process-optimization-submit'),
    path('process-optimization/stream/', process_optimization_stream, name='process-optimization-stream'),
    path('process-optimization/history/', process_optimization_history, name='process-optimization-history'),
    path('process-optimization/task/<uuid:task_id>/', process_optimization_task_detail, name='process-optimization-task-detail'),
]

