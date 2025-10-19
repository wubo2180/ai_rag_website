"""
材料知识图谱 URL 路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .kg_views import (
    RawMaterialViewSet, IntermediateViewSet,
    FormulaViewSet, PerformanceViewSet, KnowledgeGraphViewSet
)

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'raw-materials', RawMaterialViewSet, basename='raw-material')
router.register(r'intermediates', IntermediateViewSet, basename='intermediate')
router.register(r'formulas', FormulaViewSet, basename='formula')
router.register(r'performances', PerformanceViewSet, basename='performance')
router.register(r'graph', KnowledgeGraphViewSet, basename='knowledge-graph')

# URL模式
urlpatterns = [
    path('', include(router.urls)),
]
