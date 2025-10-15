from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.conf import settings
import json

from .models import ChatSession, ChatMessage
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer, 
    ChatMessageCreateSerializer,
    ChatSessionCreateSerializer,
    ChatSessionUpdateSerializer,
    ChatHistorySerializer
)
from apps.ai_service.services import ai_service


class ChatSessionPagination(PageNumberPagination):
    """聊天会话分页"""
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class ChatSessionListAPIView(generics.ListCreateAPIView):
    """聊天会话列表 API"""
    serializer_class = ChatSessionSerializer
    pagination_class = ChatSessionPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """获取当前用户的会话列表"""
        return ChatSession.objects.filter(user=self.request.user).order_by('-updated_at')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ChatSessionCreateSerializer
        return ChatSessionSerializer
    
    def perform_create(self, serializer):
        """创建会话时自动设置用户"""
        serializer.save(user=self.request.user)


class ChatSessionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """聊天会话详情 API"""
    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return ChatSession.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ChatSessionUpdateSerializer
        return ChatSessionSerializer


class ChatHistoryAPIView(APIView):
    """获取聊天历史 API"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, session_id):
        """获取指定会话的聊天历史"""
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            serializer = ChatHistorySerializer(session)
            return Response(serializer.data)
        except ChatSession.DoesNotExist:
            return Response(
                {'error': '会话不存在或无权限访问'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class ChatAPIView(APIView):
    """聊天 API"""
    permission_classes = [AllowAny]  # 允许匿名用户聊天
    
    def post(self, request):
        """发送消息并获取AI回复"""
        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message = serializer.validated_data['message']
        session_id = serializer.validated_data.get('session_id')
        model = serializer.validated_data.get('model')
        
        try:
            # 获取或创建会话
            if session_id:
                try:
                    session = ChatSession.objects.get(id=session_id)
                    # 验证权限（如果是登录用户）
                    if request.user.is_authenticated and session.user != request.user:
                        return Response(
                            {'error': '无权访问此会话'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                except ChatSession.DoesNotExist:
                    return Response(
                        {'error': '会话不存在'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # 创建新会话
                session_title = message[:50] + '...' if len(message) > 50 else message
                session = ChatSession.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    title=session_title
                )
            
            # 保存用户消息
            user_message = ChatMessage.objects.create(
                session=session,
                content=message,
                is_user=True
            )
            
            # 获取聊天历史用于上下文
            chat_history = []
            previous_messages = session.messages.order_by('created_at')[:10]  # 最近10条消息
            for msg in previous_messages:
                role = "user" if msg.is_user else "assistant"
                chat_history.append({"role": role, "content": msg.content})
            
            # 调用AI服务
            try:
                ai_response = ai_service.chat_with_ai(
                    message=message,
                    conversation_id=str(session.conversation_id),
                    model=model,
                    chat_history=chat_history
                )
                
                if ai_response.get('success'):
                    # 保存AI回复
                    ai_message = ChatMessage.objects.create(
                        session=session,
                        content=ai_response['response'],
                        is_user=False,
                        model_used=ai_response.get('model', model or settings.DIFY_DEFAULT_MODEL)
                    )
                    
                    # 更新会话时间
                    session.save()
                    
                    return Response({
                        'success': True,
                        'session_id': str(session.id),
                        'conversation_id': str(session.conversation_id),
                        'user_message': ChatMessageSerializer(user_message).data,
                        'ai_message': ChatMessageSerializer(ai_message).data,
                        'response': ai_response['response']
                    })
                else:
                    return Response({
                        'success': False,
                        'error': ai_response.get('error', 'AI服务暂时不可用'),
                        'session_id': str(session.id)
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                return Response({
                    'success': False,
                    'error': f'AI服务错误: {str(e)}',
                    'session_id': str(session.id)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'服务器错误: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AvailableModelsAPIView(APIView):
    """获取可用的AI模型列表"""
    permission_classes = [AllowAny]
    
    def get(self, request):
        """返回可用的AI模型列表"""
        models = settings.AVAILABLE_AI_MODELS
        default_model = settings.DIFY_DEFAULT_MODEL
        
        return Response({
            'models': models,
            'default_model': default_model
        })


class ChatSessionRenameAPIView(APIView):
    """重命名聊天会话"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, session_id):
        """重命名会话"""
        try:
            session = ChatSession.objects.get(id=session_id, user=request.user)
            new_title = request.data.get('title', '').strip()
            
            if not new_title:
                return Response(
                    {'error': '会话标题不能为空'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if len(new_title) > 100:
                return Response(
                    {'error': '会话标题不能超过100个字符'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            session.title = new_title
            session.save()
            
            return Response({
                'success': True,
                'title': session.title,
                'message': '重命名成功'
            })
            
        except ChatSession.DoesNotExist:
            return Response(
                {'error': '会话不存在或无权限访问'}, 
                status=status.HTTP_404_NOT_FOUND
            )