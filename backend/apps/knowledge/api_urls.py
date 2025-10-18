from django.urls import path
from .dify_views import (
    DifyDatasetListAPIView,
    DifyDatasetDetailAPIView,
    DifyDatasetDocumentsAPIView
)

app_name = 'knowledge_api'

# 知识库相关的API路由
urlpatterns = [
    # Dify知识库管理API
    path('dify/datasets/', DifyDatasetListAPIView.as_view(), name='dify_dataset_list'),
    path('dify/datasets/<str:dataset_id>/', DifyDatasetDetailAPIView.as_view(), name='dify_dataset_detail'),
    path('dify/datasets/<str:dataset_id>/documents/', DifyDatasetDocumentsAPIView.as_view(), name='dify_dataset_documents'),
]