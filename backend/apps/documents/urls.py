from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # 文档分类相关
    path('categories/', views.DocumentCategoryListCreateAPIView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.DocumentCategoryDetailAPIView.as_view(), name='category-detail'),
    
    # 文档相关
    path('upload/', views.DocumentUploadAPIView.as_view(), name='document-upload'),
    path('list/', views.DocumentListAPIView.as_view(), name='document-list'),
    path('<int:pk>/', views.DocumentDetailAPIView.as_view(), name='document-detail'),
    path('<int:pk>/update/', views.DocumentUpdateAPIView.as_view(), name='document-update'),
    path('<int:pk>/delete/', views.DocumentDeleteAPIView.as_view(), name='document-delete'),
    path('<int:pk>/download/', views.DocumentDownloadAPIView.as_view(), name='document-download'),
    
    # 统计信息
    path('stats/', views.DocumentStatsAPIView.as_view(), name='document-stats'),
]