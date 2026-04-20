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
    process_optimization_submit as formula_generation_submit,
    process_optimization_stream as formula_generation_stream,
    process_optimization_history as formula_generation_history,
    process_optimization_task_detail as formula_generation_task_detail
)
from .data_analysis_views import (
    data_analysis_submit,
    data_analysis_stream,
    data_analysis_history,
    data_analysis_task_detail,
    data_analysis_types
)
# from .process_optimization_views import (
#     process_optimization_submit,
#     process_optimization_stream,
#     process_optimization_task_detail,
#     process_optimization_task_list
# )

# 创建路由器
router = DefaultRouter()
router.register(r'agents', SmartAgentViewSet, basename='smartagent')
router.register(r'tasks', AgentTaskViewSet, basename='agenttask')
router.register(r'executions', AgentExecutionViewSet, basename='agentexecution')
router.register(r'feedbacks', AgentFeedbackViewSet, basename='agentfeedback')

# URL模式
urlpatterns = [
    path('', include(router.urls)),
    
    # 配方生成智能体专用接口
    path('formula-generation/submit/', formula_generation_submit, name='formula-generation-submit'),
    path('formula-generation/stream/', formula_generation_stream, name='formula-generation-stream'),
    path('formula-generation/history/', formula_generation_history, name='formula-generation-history'),
    path('formula-generation/task/<uuid:task_id>/', formula_generation_task_detail, name='formula-generation-task-detail'),

    # 数据分析智能体专用接口
    path('data-analysis/submit/', data_analysis_submit, name='data-analysis-submit'),
    path('data-analysis/stream/', data_analysis_stream, name='data-analysis-stream'),
    path('data-analysis/history/', data_analysis_history, name='data-analysis-history'),
    path('data-analysis/task/<uuid:task_id>/', data_analysis_task_detail, name='data-analysis-task-detail'),
    path('data-analysis/types/', data_analysis_types, name='data-analysis-types'),
    
    # # 工艺优化智能体专用接口
    # path('process-optimization/submit/', process_optimization_submit, name='process-optimization-submit'),
    # path('process-optimization/stream/', process_optimization_stream, name='process-optimization-stream'),
    # path('process-optimization/tasks/', process_optimization_task_list, name='process-optimization-task-list'),
    # path('process-optimization/task/<uuid:task_id>/', process_optimization_task_detail, name='process-optimization-task-detail'),
]

