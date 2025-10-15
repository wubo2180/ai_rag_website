from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Knowledge, Document
import json

def knowledge_index(request):
    """知识库首页"""
    knowledge_list = Knowledge.objects.filter(is_active=True)
    return render(request, 'knowledge/index.html', {'knowledge_list': knowledge_list})

@login_required
def add_knowledge(request):
    """添加知识条目"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category = request.POST.get('category', '')
        tags = request.POST.get('tags', '')
        
        knowledge = Knowledge.objects.create(
            title=title,
            content=content,
            category=category,
            tags=tags,
            created_by=request.user
        )
        
        messages.success(request, '知识条目添加成功！')
        return redirect('knowledge_index')
    
    return render(request, 'knowledge/add.html')

@login_required
def upload_document(request):
    """上传文档"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content', '')
        file = request.FILES.get('file')
        
        document = Document.objects.create(
            title=title,
            content=content,
            file_path=file,
            uploaded_by=request.user
        )
        
        messages.success(request, '文档上传成功！')
        return redirect('knowledge_index')
    
    return render(request, 'knowledge/upload.html')

def search_knowledge(request):
    """搜索知识库"""
    query = request.GET.get('q', '')
    results = []
    
    if query:
        results = Knowledge.objects.filter(
            title__icontains=query,
            is_active=True
        ) | Knowledge.objects.filter(
            content__icontains=query,
            is_active=True
        )
    
    return render(request, 'knowledge/search.html', {
        'query': query,
        'results': results
    })