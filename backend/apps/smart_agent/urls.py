# smart_agent/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('agent-info/', views.AgentInfoView.as_view(), name='agent_info'),
]
