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
    permission_classes = [AllowAny]  # 允许匿名用户访问
    
    def get(self, request, session_id):
        """获取指定会话的聊天历史"""
        print(f"🔍 获取会话历史请求: session_id={session_id}, user={request.user}")
        
        try:
            # 如果用户已登录，只能访问自己的会话
            if request.user.is_authenticated:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            else:
                # 匿名用户可以访问任何会话（临时允许）
                session = ChatSession.objects.get(id=session_id)
            
            print(f"✅ 找到会话: {session.title}")
            serializer = ChatHistorySerializer(session)
            return Response(serializer.data)
            
        except ChatSession.DoesNotExist:
            print(f"❌ 会话不存在: {session_id}")
            return Response(
                {'error': '会话不存在或无权限访问'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            print(f"❌ 获取会话历史异常: {str(e)}")
            return Response(
                {'error': f'获取会话历史失败: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatAPIView(APIView):
    """聊天 API"""
    permission_classes = [AllowAny]  # 允许匿名用户聊天
    
    def post(self, request):
        """发送消息并获取AI回复"""
        print(f"🔍 聊天请求数据: {request.data}")
        print(f"🔍 Content-Type: {request.content_type}")
        
        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            print(f"❌ 序列化器验证失败: {serializer.errors}")
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
            previous_messages = session.messages.order_by('timestamp')[:10]  # 最近10条消息
            for msg in previous_messages:
                role = "user" if msg.is_user else "assistant"
                chat_history.append({"role": role, "content": msg.content})
            
            # 调用Dify API获取AI响应
            try:
                # 使用 dify_conversation_id 而不是数据库ID
                user_id = str(request.user.id) if request.user.is_authenticated else "anonymous"
                ai_result = ai_service.generate_response(
                    message=message,
                    user_id=user_id,
                    session_id=session.dify_conversation_id,  # 使用Dify的conversation_id
                    model=model
                )
                
                # 获取AI响应内容
                ai_response = ai_result.get('response', '抱歉，暂时无法生成回复')
                
                # 如果是新会话，保存Dify返回的conversation_id
                if ai_result.get('success') and ai_result.get('conversation_id'):
                    if not session.dify_conversation_id:
                        session.dify_conversation_id = ai_result.get('conversation_id')
                        session.save()
                
                # 保存AI回复
                ai_message = ChatMessage.objects.create(
                    session=session,
                    content=ai_response,
                    is_user=False,
                    dify_message_id=ai_result.get('message_id')  # 保存Dify的消息ID
                )
                
                # 更新会话时间
                session.save()
                
                print(f"✅ 聊天消息处理成功")
                
                return Response({
                    'success': True,
                    'session_id': str(session.id),
                    'conversation_id': str(session.dify_conversation_id or session.id),
                    'user_message': ChatMessageSerializer(user_message).data,
                    'ai_message': ChatMessageSerializer(ai_message).data,
                    'response': ai_response,
                    'model': ai_result.get('model', model),
                    'dify_success': ai_result.get('success', False)
                })
                    
            except Exception as e:
                print(f"❌ Dify API调用失败: {str(e)}")
                
                # 如果Dify API失败，保存一个错误消息
                error_response = f'抱歉，AI服务暂时不可用。错误信息：{str(e)}'
                ai_message = ChatMessage.objects.create(
                    session=session,
                    content=error_response,
                    is_user=False
                )
                
                return Response({
                    'success': False,
                    'error': f'AI服务错误: {str(e)}',
                    'session_id': str(session.id) if 'session' in locals() else None,
                    'user_message': ChatMessageSerializer(user_message).data,
                    'ai_message': ChatMessageSerializer(ai_message).data,
                    'response': error_response
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