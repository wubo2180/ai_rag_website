from django.urls import path, re_path

from .views import ocr_health, ocr_service_entry, ocr_service_health, ocr_service_proxy, ocr_task_status


urlpatterns = [
    path('health', ocr_health, name='ocr_health'),
    path('tasks/<str:task_id>', ocr_task_status, name='ocr_task_status'),
    path('<str:service>/health', ocr_service_health, name='ocr_service_health'),
    path('<str:service>/entry', ocr_service_entry, name='ocr_service_entry'),
    re_path(r'^(?P<service>commission|paper|checker)/(?P<path>.*)$', ocr_service_proxy, name='ocr_service_proxy'),
]
