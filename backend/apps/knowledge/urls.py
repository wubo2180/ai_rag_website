from django.urls import path
from . import views

urlpatterns = [
    path('', views.knowledge_index, name='knowledge_index'),
    path('add/', views.add_knowledge, name='add_knowledge'),
    path('upload/', views.upload_document, name='upload_document'),
    path('search/', views.search_knowledge, name='search_knowledge'),
]