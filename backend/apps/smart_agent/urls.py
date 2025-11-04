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

# 创建路由器
router = DefaultRouter()
router.register(r'agents', SmartAgentViewSet, basename='smartagent')
router.register(r'tasks', AgentTaskViewSet, basename='agenttask')
router.register(r'executions', AgentExecutionViewSet, basename='agentexecution')
router.register(r'feedbacks', AgentFeedbackViewSet, basename='agentfeedback')

# URL模式
urlpatterns = [
    path('', include(router.urls)),
]
