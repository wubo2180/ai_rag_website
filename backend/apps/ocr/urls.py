from django.urls import path, re_path

from .services.pdf_proxy_service import pdf_download, pdf_preview
from .views import ocr_health, ocr_service_entry, ocr_service_health, ocr_service_proxy, ocr_task_status


urlpatterns = [
    path('health', ocr_health, name='ocr_health'),
    path('tasks/<str:task_id>', ocr_task_status, name='ocr_task_status'),
    path('<str:service>/health', ocr_service_health, name='ocr_service_health'),
    path('<str:service>/entry', ocr_service_entry, name='ocr_service_entry'),
    # PDF 代理路由（必须在 checker 的 re_path 之前，否则会被拦截）
    path('pdf/<int:file_id>/preview', pdf_preview, name='pdf_preview'),
    path('pdf/<int:file_id>/download', pdf_download, name='pdf_download'),
    re_path(r'^(?P<service>commission|paper|checker)/(?P<path>.*)$', ocr_service_proxy, name='ocr_service_proxy'),
]
