from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.chat_index, name='chat_index'),
    path('api/', views.chat_api, name='chat_api'),
    path('api/models/', views.get_available_models, name='get_models'),
    path('api/test/', views.test_ai_connection, name='test_ai'),
    path('history/<int:session_id>/', views.chat_history, name='chat_history'),
    path('rename/<int:session_id>/', views.rename_session, name='rename_session'),
    path('delete/<int:session_id>/', views.delete_session, name='delete_session'),
    path('markdown-test/', TemplateView.as_view(template_name='markdown_test.html'), name='markdown_test'),
]