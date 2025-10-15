from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.contrib.auth.models import User
import os

from .models import Document, DocumentCategory, DocumentAccess
from .serializers import (
    DocumentUploadSerializer,
    DocumentListSerializer,
    DocumentDetailSerializer,
    DocumentUpdateSerializer,
    DocumentCategorySerializer,
    DocumentAccessSerializer
)


class DocumentCategoryListCreateAPIView(generics.ListCreateAPIView):
    """文档分类列表和创建API"""
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户的分类"""
        return DocumentCategory.objects.filter(created_by=self.request.user)


class DocumentCategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """文档分类详情API"""
    serializer_class = DocumentCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return DocumentCategory.objects.filter(created_by=self.request.user)


class DocumentUploadAPIView(APIView):
    """文档上传API"""
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = DocumentUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            document = serializer.save()
            return Response({
                'success': True,
                'message': '文档上传成功',
                'document': DocumentDetailSerializer(document).data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class DocumentListAPIView(generics.ListAPIView):
    """文档列表API"""
    serializer_class = DocumentListSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'tags', 'original_filename']
    ordering_fields = ['created_at', 'title', 'file_size']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取文档查询集"""
        queryset = Document.objects.select_related('category', 'uploaded_by')
        
        # 根据用户权限过滤
        user = self.request.user
        if user.is_staff:
            # 管理员可以看到所有文档
            pass
        else:
            # 普通用户只能看到自己的文档和公开文档
            queryset = queryset.filter(
                Q(uploaded_by=user) | Q(is_public=True)
            )
        
        # 按分类过滤
        category_id = self.request.query_params.get('category')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # 按文件类型过滤
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type=file_type)
        
        # 按上传者过滤
        uploaded_by = self.request.query_params.get('uploaded_by')
        if uploaded_by:
            queryset = queryset.filter(uploaded_by__username=uploaded_by)
        
        return queryset


class DocumentDetailAPIView(generics.RetrieveAPIView):
    """文档详情API"""
    serializer_class = DocumentDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Document.objects.all()
        else:
            return Document.objects.filter(
                Q(uploaded_by=user) | Q(is_public=True)
            )
    
    def retrieve(self, request, *args, **kwargs):
        """获取文档详情并记录访问"""
        instance = self.get_object()
        
        # 记录访问日志
        DocumentAccess.objects.create(
            document=instance,
            user=request.user,
            action='view'
        )
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class DocumentUpdateAPIView(generics.UpdateAPIView):
    """文档更新API"""
    serializer_class = DocumentUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 只能更新自己的文档或管理员权限
        user = self.request.user
        if user.is_staff:
            return Document.objects.all()
        else:
            return Document.objects.filter(uploaded_by=user)


class DocumentDeleteAPIView(generics.DestroyAPIView):
    """文档删除API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Document.objects.all()
        else:
            return Document.objects.filter(uploaded_by=user)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 删除文件
        if instance.file:
            try:
                if os.path.isfile(instance.file.path):
                    os.remove(instance.file.path)
            except Exception:
                pass
        
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': '文档删除成功'
        }, status=status.HTTP_200_OK)


class DocumentDownloadAPIView(APIView):
    """文档下载API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        """下载文档"""
        user = request.user
        
        try:
            if user.is_staff:
                document = Document.objects.get(pk=pk)
            else:
                document = Document.objects.get(
                    Q(pk=pk) & (Q(uploaded_by=user) | Q(is_public=True))
                )
        except Document.DoesNotExist:
            return Response({
                'error': '文档不存在或无权限访问'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 记录下载日志
        DocumentAccess.objects.create(
            document=document,
            user=request.user,
            action='download'
        )
        
        try:
            # 构建文件响应
            response = HttpResponse(
                document.file.read(),
                content_type='application/octet-stream'
            )
            response['Content-Disposition'] = f'attachment; filename="{document.original_filename}"'
            response['Content-Length'] = document.file_size
            
            return response
        except Exception as e:
            return Response({
                'error': f'文件下载失败: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentStatsAPIView(APIView):
    """文档统计API"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """获取文档统计信息"""
        user = request.user
        
        if user.is_staff:
            # 管理员统计
            total_documents = Document.objects.count()
            total_categories = DocumentCategory.objects.count()
            total_size = sum(doc.file_size for doc in Document.objects.all())
        else:
            # 用户统计
            user_documents = Document.objects.filter(uploaded_by=user)
            total_documents = user_documents.count()
            total_categories = DocumentCategory.objects.filter(created_by=user).count()
            total_size = sum(doc.file_size for doc in user_documents)
        
        # 按文件类型统计
        file_type_stats = {}
        documents = Document.objects.filter(uploaded_by=user) if not user.is_staff else Document.objects.all()
        
        for doc in documents:
            if doc.file_type in file_type_stats:
                file_type_stats[doc.file_type]['count'] += 1
                file_type_stats[doc.file_type]['size'] += doc.file_size
            else:
                file_type_stats[doc.file_type] = {
                    'count': 1,
                    'size': doc.file_size,
                    'name': dict(Document.FILE_TYPES)[doc.file_type]
                }
        
        return Response({
            'total_documents': total_documents,
            'total_categories': total_categories,
            'total_size': total_size,
            'total_size_human': self._format_bytes(total_size),
            'file_type_stats': file_type_stats,
        })
    
    def _format_bytes(self, bytes_size):
        """格式化字节大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} TB"
