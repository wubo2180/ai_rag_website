from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.models import User
from django.conf import settings
import json
import requests
import logging

# REST Framework imports (from api_views.py)
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

logger = logging.getLogger(__name__)

from .models import ChatSession, ChatMessage
from apps.ai_service.services import ai_service

# Serializers (from api_views.py)
from .serializers import (
    ChatSessionSerializer,
    ChatMessageSerializer, 
    ChatMessageCreateSerializer,
    ChatSessionCreateSerializer,
    ChatSessionUpdateSerializer,
    ChatHistorySerializer
)

def chat_index(request):
    """聊天主页 - 直接返回Vue.js应用"""
    # 直接返回Vue.js的index.html文件
    from django.http import FileResponse
    import os
    from django.conf import settings
    
    # 构建Vue.js构建文件的路径
    vue_index_path = os.path.join(settings.BASE_DIR.parent, 'frontend', 'dist', 'index.html')
    
    if os.path.exists(vue_index_path):
        return FileResponse(open(vue_index_path, 'rb'), content_type='text/html')
    else:
        from django.http import HttpResponse
        return HttpResponse("Vue.js应用未构建，请运行 'npm run build'", status=404)

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """聊天API接口"""
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        model = data.get('model')  # 获取用户选择的模型
        
        if not message:
            return JsonResponse({'error': '消息不能为空'}, status=400)
        
        # 获取或创建会话
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
                if request.user.is_authenticated and session.user != request.user:
                    return JsonResponse({'error': '无权访问此会话'}, status=403)
            except ChatSession.DoesNotExist:
                return JsonResponse({'error': '会话不存在'}, status=404)
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
        
        # 调用Dify API获取AI响应
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
        
        return JsonResponse({
            'success': ai_result.get('success', True),
            'response': ai_response,
            'session_id': session.id,
            'message_id': ai_message.id,
            'model': ai_result.get('model', model),
            'error': ai_result.get('error') if not ai_result.get('success') else None
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'服务器错误: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def get_available_models(request):
    """获取可用的AI模型列表"""
    try:
        models = ai_service.get_available_models()
        return JsonResponse({
            'success': True,
            'models': models
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def test_ai_connection(request):
    """测试AI服务连接"""
    try:
        result = ai_service.generate_response(
            message="你好",
            user_id="test_user"
        )
        return JsonResponse({
            'success': result.get('success', False),
            'message': 'AI服务连接正常' if result.get('success') else 'AI服务连接失败',
            'response': result.get('response', ''),
            'error': result.get('error')
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
def chat_history(request, session_id):
    """获取聊天历史"""
    try:
        # 如果用户已登录，检查会话所有权
        if request.user.is_authenticated:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            # 未登录用户只能访问无主的会话
            session = get_object_or_404(ChatSession, id=session_id, user=None)
        
        messages = session.messages.all().order_by('timestamp')
        
        messages_data = []
        for msg in messages:
            messages_data.append({
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.timestamp.isoformat()
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'session_title': session.title
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def rename_session(request, session_id):
    """重命名聊天会话"""
    try:
        data = json.loads(request.body)
        new_title = data.get('title', '').strip()
        
        if not new_title:
            return JsonResponse({'error': '标题不能为空'}, status=400)
        
        # 如果用户已登录，检查会话所有权
        if request.user.is_authenticated:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
        else:
            # 未登录用户只能修改无主的会话
            session = get_object_or_404(ChatSession, id=session_id, user=None)
        
        session.title = new_title
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': '重命名成功',
            'title': session.title
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': '无效的JSON数据'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def delete_session(request, session_id):
    """删除聊天会话"""
    if request.method == 'DELETE':
        try:
            session = get_object_or_404(ChatSession, id=session_id, user=request.user)
            session.delete()
            return JsonResponse({'success': True, 'message': '会话已删除'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '不支持的请求方法'}, status=405)


# ==================== REST API Views (merged from api_views.py) ====================

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


# ==================== 微信小程序 SSE API ====================

class WeChatMiniProgramSSEAPIView(APIView):
    """
    微信小程序专用SSE流式聊天API
    
    SSE格式要求：
    - Content-Type: text/event-stream
    - Cache-Control: no-cache
    - 每个数据块以 data: 开头
    - 每个数据块以 \\n\\n 结束
    - 结束标记为 data: [DONE]\\n\\n
    
    请求格式：
    POST /api/chat/wechat/stream/
    {
        "message": "用户消息",
        "session_id": "会话ID（可选）",
        "model": "模型名称（可选）",
        "user_id": "微信用户标识（可选）"
    }
    
    响应格式（SSE流）：
    data: {"session_id": "123", "conversation_id": "abc"}
    data: {"content": "你好"}
    data: {"content": "世界"}
    data: {"done": true, "message_id": "xxx"}
    data: [DONE]
    """
    permission_classes = [AllowAny]  # 允许匿名访问，但会尝试解析Token获取用户
    
    def post(self, request):
        """处理微信小程序的SSE流式聊天请求"""
        logger.info(f"📱 微信小程序SSE请求: {request.data}")
        logger.info(f"📱 用户认证状态: {request.user}, is_authenticated={request.user.is_authenticated}")
        
        # 获取请求参数
        message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')
        model = request.data.get('model')
        wechat_user_id = request.data.get('user_id', 'wechat_anonymous')
        
        # 验证消息
        if not message:
            return self._create_error_sse_response({'error': '消息不能为空'})
        
        try:
            # 获取或创建会话 - 传入request以获取用户信息
            session = self._get_or_create_session(session_id, message, request)
            
            # 保存用户消息
            user_message = ChatMessage.objects.create(
                session=session,
                content=message,
                is_user=True
            )
            
            # 返回SSE流式响应
            response = StreamingHttpResponse(
                self._generate_sse_stream(
                    message=message,
                    model=model,
                    session=session,
                    wechat_user_id=wechat_user_id
                ),
                content_type='text/event-stream'
            )
            
            # 设置SSE必需的响应头
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'  # 禁用nginx缓冲
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            
            return response
            
        except Exception as e:
            logger.error(f"❌ 微信小程序SSE请求失败: {str(e)}")
            return self._create_error_sse_response({'error': f'服务器错误: {str(e)}'})
    
    def _get_or_create_session(self, session_id, message, request):
        """
        获取或创建会话
        
        逻辑：
        1. 如果提供了session_id，尝试获取该会话
           - 如果用户已登录，验证会话属于该用户
           - 如果用户未登录，只能访问无主会话
        2. 如果没有提供session_id或会话不存在，创建新会话
           - 新会话会关联到当前登录用户（如果有）
        
        这样确保：
        - 微信小程序用户登录后，对话会关联到他们的账户
        - 网页端和微信小程序共享同一份对话历史
        """
        user = request.user if request.user.is_authenticated else None
        
        if session_id:
            try:
                session = ChatSession.objects.get(id=session_id)
                
                # 权限验证
                if user:
                    # 已登录用户只能访问自己的会话
                    if session.user and session.user != user:
                        logger.warning(f"⚠️ 用户 {user.id} 尝试访问其他用户的会话 {session_id}")
                        # 不抛错，而是创建新会话
                        pass
                    else:
                        # 如果会话没有用户，绑定到当前用户
                        if not session.user:
                            session.user = user
                            session.save()
                            logger.info(f"📱 会话 {session_id} 已绑定到用户 {user.id}")
                        return session
                else:
                    # 未登录用户只能访问无主会话
                    if session.user is None:
                        return session
                    else:
                        logger.warning(f"⚠️ 匿名用户尝试访问用户会话 {session_id}")
                        
            except ChatSession.DoesNotExist:
                logger.info(f"📱 会话 {session_id} 不存在，将创建新会话")
        
        # 创建新会话
        session_title = message[:50] + '...' if len(message) > 50 else message
        session = ChatSession.objects.create(
            user=user,  # 关联到当前登录用户
            title=session_title
        )
        logger.info(f"📱 创建新会话 {session.id}, 用户: {user.id if user else 'anonymous'}")
        return session
    
    def _generate_sse_stream(self, message, model, session, wechat_user_id):
        """
        生成符合微信小程序要求的SSE流
        
        格式要求：
        - 每行以 data: 开头
        - 每个数据块以 \\n\\n 结束
        - 最后发送 data: [DONE]\\n\\n
        """
        try:
            # 1. 首先发送session_id信息
            session_info = {
                'session_id': str(session.id),
                'conversation_id': session.dify_conversation_id or str(session.id)
            }
            yield f"data: {json.dumps(session_info, ensure_ascii=False)}\n\n"
            
            # 2. 调用Dify API获取流式响应
            api_url = f"{settings.DIFY_API_URL.rstrip('/')}/chat-messages"
            api_key = settings.DIFY_API_KEY
            
            if not api_key:
                yield f"data: {json.dumps({'error': 'API密钥未配置'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # Dify支持的模型列表
            valid_models = [
                'deepseek深度思考', '通义千问', '腾讯混元', '豆包', 
                'Kimi', 'GPT-5', 'Claude4', 'Gemini2.5', 'Grok-4', 'Llama4'
            ]
            
            # 模型映射 - 将前端传的模型名映射到Dify支持的模型名
            model_mapping = {
                'deepseek': '通义千问',
                'qianwen': '通义千问',
                'tongyi': '通义千问',
                'hunyuan': '腾讯混元',
                'doubao': '豆包',
                'kimi': 'Kimi',
                'gpt': 'GPT-5',
                'gpt-5': 'GPT-5',
                'claude': 'Claude4',
                'claude4': 'Claude4',
                'gemini': 'Gemini2.5',
                'grok': 'Grok-4',
                'llama': 'Llama4',
            }
            
            # 获取有效的模型名
            default_model = getattr(settings, 'DIFY_DEFAULT_MODEL', '通义千问')
            if not model:
                large_model = default_model
            elif model in valid_models:
                large_model = model
            elif model.lower() in model_mapping:
                large_model = model_mapping[model.lower()]
            else:
                # 如果模型名无效，使用默认模型
                logger.warning(f"⚠️ 无效的模型名: {model}，使用默认模型: {default_model}")
                large_model = default_model
            
            # 构建请求体
            request_body = {
                "inputs": {"largeModel": large_model},
                "query": message,
                "user": wechat_user_id,
                "response_mode": "streaming"
            }
            
            # 如果有Dify会话ID，则使用
            if session.dify_conversation_id:
                request_body["conversation_id"] = session.dify_conversation_id
            
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            # 获取超时配置
            model_timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {})
            timeout_duration = model_timeouts.get(large_model, model_timeouts.get('default', 90))
            
            logger.info(f"📱 微信小程序调用Dify API, 模型: {large_model}, 超时: {timeout_duration}秒")
            
            # 调用Dify API
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body,
                timeout=timeout_duration,
                stream=True
            )
            
            if response.status_code != 200:
                error_msg = f"AI服务错误: {response.status_code}"
                logger.error(f"❌ Dify API错误: {response.text}")
                yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
                return
            
            # 3. 处理Dify的SSE响应并转发给微信小程序
            ai_content = ""
            dify_conversation_id = None
            dify_message_id = None
            
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        
                        try:
                            data = json.loads(data_str)
                            event = data.get('event', '')
                            
                            # 处理消息事件
                            if event == 'message' or 'answer' in data:
                                content = data.get('answer', '')
                                if content:
                                    ai_content += content
                                    # 发送内容块 - 符合微信小程序SSE格式
                                    yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                                
                                # 保存conversation_id
                                if data.get('conversation_id'):
                                    dify_conversation_id = data.get('conversation_id')
                                if data.get('message_id'):
                                    dify_message_id = data.get('message_id')
                            
                            # 处理消息结束事件
                            elif event == 'message_end':
                                if data.get('conversation_id'):
                                    dify_conversation_id = data.get('conversation_id')
                                if data.get('message_id'):
                                    dify_message_id = data.get('message_id')
                            
                            # 处理错误事件
                            elif event == 'error':
                                error_msg = data.get('message', '未知错误')
                                yield f"data: {json.dumps({'error': error_msg}, ensure_ascii=False)}\n\n"
                                
                        except json.JSONDecodeError:
                            continue
            
            # 4. 保存Dify的conversation_id到会话
            if dify_conversation_id and not session.dify_conversation_id:
                session.dify_conversation_id = dify_conversation_id
                session.save()
            
            # 5. 保存AI响应到数据库
            ai_message = None
            if ai_content:
                ai_message = ChatMessage.objects.create(
                    session=session,
                    content=ai_content,
                    is_user=False,
                    dify_message_id=dify_message_id
                )
            
            # 6. 发送完成信号
            done_data = {
                'done': True,
                'session_id': str(session.id),
                'conversation_id': dify_conversation_id or str(session.id)
            }
            if ai_message:
                done_data['message_id'] = str(ai_message.id)
            
            yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"
            
            # 7. 发送SSE结束标记
            yield "data: [DONE]\n\n"
            
            logger.info(f"✅ 微信小程序SSE响应完成, 内容长度: {len(ai_content)}")
            
        except requests.exceptions.Timeout:
            logger.error("❌ Dify API请求超时")
            yield f"data: {json.dumps({'error': 'AI服务响应超时，请稍后再试'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
        except requests.exceptions.ConnectionError:
            logger.error("❌ 无法连接到Dify API")
            yield f"data: {json.dumps({'error': '无法连接到AI服务，请检查网络'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"❌ SSE流生成异常: {str(e)}")
            yield f"data: {json.dumps({'error': f'服务异常: {str(e)}'}, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
    
    def _create_error_sse_response(self, error_data):
        """创建错误SSE响应"""
        def error_generator():
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        
        response = StreamingHttpResponse(
            error_generator(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        response['Access-Control-Allow-Origin'] = '*'
        return response
    
    def options(self, request):
        """处理CORS预检请求"""
        response = Response(status=status.HTTP_200_OK)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response