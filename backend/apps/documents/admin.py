from django.contrib import admin
from .models import DocumentCategory, DocumentFolder, Document, DocumentAccess


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    """文档分类管理"""
    list_display = ['name', 'color', 'document_count', 'folder_count', 'created_by', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(DocumentFolder)
class DocumentFolderAdmin(admin.ModelAdmin):
    """文档文件夹管理"""
    list_display = ['name', 'category', 'parent', 'document_count', 'created_by', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'parent', 'created_by')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """文档管理"""
    list_display = [
        'title', 'file_type', 'file_size_human', 
        'category', 'folder', 'uploaded_by', 'is_public', 'created_at'
    ]
    list_filter = ['file_type', 'category', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'original_filename', 'tags']
    readonly_fields = ['file_size', 'original_filename', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'description', 'file', 'file_type')
        }),
        ('分类信息', {
            'fields': ('category', 'folder', 'tags')
        }),
        ('文件信息', {
            'fields': ('original_filename', 'file_size')
        }),
        ('权限设置', {
            'fields': ('uploaded_by', 'is_public')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('category', 'folder', 'uploaded_by')


@admin.register(DocumentAccess)
class DocumentAccessAdmin(admin.ModelAdmin):
    """文档访问记录管理"""
    list_display = ['document', 'user', 'action', 'access_time']
    list_filter = ['action', 'access_time']
    search_fields = ['document__title', 'user__username']
    readonly_fields = ['document', 'user', 'access_time', 'action']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('document', 'user')
