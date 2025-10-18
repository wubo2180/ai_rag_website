from django.urls import path
from . import views
from .dify_views import (
    DifyDatasetListAPIView,
    DifyDatasetDetailAPIView,
    DifyDatasetDocumentsAPIView
)

urlpatterns = [
    # 原有的知识库功能
    path('', views.knowledge_index, name='knowledge_index'),
    path('add/', views.add_knowledge, name='add_knowledge'),
    path('upload/', views.upload_document, name='upload_document'),
    path('search/', views.search_knowledge, name='search_knowledge'),
    
    # Dify知识库管理API
    path('api/dify/datasets/', DifyDatasetListAPIView.as_view(), name='dify_dataset_list'),
    path('api/dify/datasets/<str:dataset_id>/', DifyDatasetDetailAPIView.as_view(), name='dify_dataset_detail'),
    path('api/dify/datasets/<str:dataset_id>/documents/', DifyDatasetDocumentsAPIView.as_view(), name='dify_dataset_documents'),
]