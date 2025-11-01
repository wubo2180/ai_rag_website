from django.urls import path
from . import views


urlpatterns = [
    # 原有的知识库功能
    path('', views.knowledge_index, name='knowledge_index'),
    path('add/', views.add_knowledge, name='add_knowledge'),
    path('upload/', views.upload_document, name='upload_document'),
    path('search/', views.search_knowledge, name='search_knowledge'),
    
    # Dify知识库管理API
    path('dify/datasets/',views.DifyDatasetListAPIView.as_view(), name='dify_dataset_list'),
    path('dify/datasets/<str:dataset_id>/', views.DifyDatasetDetailAPIView.as_view(), name='dify_dataset_detail'),
    path('dify/datasets/<str:dataset_id>/documents/', views.DifyDatasetDocumentsAPIView.as_view(), name='dify_dataset_documents'),
]