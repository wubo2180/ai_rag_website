from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from django.conf import settings
import json
import requests
import re
import time
from .models import ChatSession, ChatMessage
from .serializers import ChatMessageCreateSerializer


class StreamChatAPIView(APIView):
    """流式聊天API - 整合AI_UI_928_2的流式响应功能"""
    permission_classes = []  # 允许匿名访问

    def post(self, request):
        """处理流式聊天请求"""
        serializer = ChatMessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data
        message = validated_data['message']
        session_id = validated_data.get('session_id')
        model = validated_data.get('model', 'deepseek')
        deep_thinking = request.data.get('deep_thinking', False)

        # 获取或创建会话 - 支持匿名用户
        session = None
        if session_id:
            try:
                if request.user.is_authenticated:
                    session = ChatSession.objects.get(id=session_id, user=request.user)
                else:
                    session = ChatSession.objects.get(id=session_id, user__isnull=True)
            except ChatSession.DoesNotExist:
                pass
        
        if not session:
            session_title = message[:50] + '...' if len(message) > 50 else message
            session = ChatSession.objects.create(
                user=request.user if request.user.is_authenticated else None,
                title=session_title
            )

        # 保存用户消息
        ChatMessage.objects.create(
            session=session,
            content=message,
            is_user=True
        )

        # 返回流式响应 - 添加更多反缓冲响应头
        response = StreamingHttpResponse(
            self.generate_stream_response(message, model, deep_thinking, session, request),
            content_type='text/event-stream; charset=utf-8'
        )
        
        # 关键:添加多个反缓冲响应头
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        response['X-Accel-Buffering'] = 'no'  # 禁用Nginx缓冲
        # ❌ 移除 Transfer-Encoding，它由 WSGI 服务器自动处理
        # response['Transfer-Encoding'] = 'chunked'
        response['Access-Control-Allow-Origin'] = '*'
        
        return response

    def generate_stream_response(self, message, model, deep_thinking, session=None, request=None):
        """生成流式响应"""
        try:
            # 先发送一个初始心跳,确保连接建立
            yield ": ping\n\n"
            
            # 发送 session_id 给前端
            if session:
                yield f"data: {json.dumps({'session_id': session.id})}\n\n"
            
            # API配置
            base_url = getattr(settings, 'DIFY_API_URL')
            api_url = f"{base_url.rstrip('/')}/chat-messages"
            api_key = settings.DIFY_API_KEY
            if not api_key:
                raise ValueError("DIFY_API_KEY not configured")
            
            # 模型映射
            model_mapping = {
                'deepseek': '通义千问',
                'doubao': '豆包',
                'gpt5': 'GPT-5', 
                '通义千问': '通义千问',
                'claude4': 'Claude4'
            }

            if model == 'deepseek' and deep_thinking:
                large_model = 'deepseek深度思考'
            else:
                large_model = model_mapping.get(model, '通义千问')

            # 构建请求体
            request_body = {
                "inputs": {
                    "largeModel": large_model
                },
                "query": message,
                "user": f"user_{request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
                "response_mode": "streaming"
            }
            
            if session and session.dify_conversation_id:
                request_body["conversation_id"] = session.dify_conversation_id

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream'  # 明确接受SSE
            }

            # 动态超时配置
            model_timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {})
            timeout_duration = model_timeouts.get(large_model, model_timeouts.get('default', 90))
            
            print(f"🕐 使用模型 {large_model},超时时间: {timeout_duration}秒")
            
            # 调用外部API - 禁用requests的流式缓冲
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body,
                timeout=timeout_duration,
                stream=True  # 启用流式响应
            )

            ai_content = ""
            thinking_content = ""
            dify_conversation_id = None
            dify_message_id = None
            chunk_count = 0  # 用于调试,统计接收到的块数

            if response.status_code == 200:
                # 处理流式响应 - 使用iter_lines并禁用解码延迟
                for line in response.iter_lines(decode_unicode=True, delimiter='\n'):
                    if line:
                        chunk_count += 1
                        line_str = line if isinstance(line, str) else line.decode('utf-8')
                        
                        # 发送心跳,每10个块发送一次
                        if chunk_count % 10 == 0:
                            yield ": heartbeat\n\n"
                        
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
                                        # 立即发送内容块
                                        yield f"data: {json.dumps({'content': content})}\n\n"
                                    
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
                                
                                # 深度思考内容
                                if deep_thinking and 'thinking' in data:
                                    thinking = data['thinking']
                                    thinking_content += thinking
                                    yield f"data: {json.dumps({'thinking': thinking})}\n\n"
                                    
                            except json.JSONDecodeError as e:
                                print(f"JSON解析错误: {e}, 行内容: {data_str}")
                                continue

                print(f"✅ 流式响应完成,共接收 {chunk_count} 个数据块")

                # 保存 Dify 的 conversation_id
                if session and dify_conversation_id:
                    if not session.dify_conversation_id:
                        session.dify_conversation_id = dify_conversation_id
                        session.save()

                # 保存AI响应
                if session and ai_content:
                    ai_message = ChatMessage.objects.create(
                        session=session,
                        content=ai_content,
                        is_user=False,
                        dify_message_id=dify_message_id
                    )
                    if thinking_content:
                        ai_message.metadata = {'thinking': thinking_content}
                        ai_message.save()

                # 发送完成信号
                yield f"data: {json.dumps({'done': True})}\n\n"
            
            else:
                # 错误处理
                try:
                    error_response = response.text
                    print(f"Dify API 错误响应: {response.status_code} - {error_response}")
                    
                    try:
                        error_json = response.json()
                        error_detail = error_json.get('message', str(error_json))
                    except:
                        error_detail = error_response
                        
                    error_msg = f"Dify API 错误 ({response.status_code}): {error_detail}"
                    
                except Exception as parse_error:
                    print(f"解析错误响应失败: {parse_error}")
                    error_msg = f"AI服务暂时不可用(错误代码: {response.status_code})"
                
                yield f"data: {json.dumps({'content': error_msg, 'error': True})}\n\n"
                yield f"data: {json.dumps({'done': True})}\n\n"

        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'content': '请求超时,请稍后重试。', 'error': True})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            print(f"流式响应生成错误: {e}")
            import traceback
            traceback.print_exc()
            yield f"data: {json.dumps({'content': f'服务暂时不可用: {str(e)}', 'error': True})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"


class RelatedQuestionsAPIView(APIView):
    """相关问题推荐API - 从AI_UI_928_2整合"""
    permission_classes = []  # 允许匿名访问

    def post(self, request):
        """获取相关问题推荐"""
        query = request.data.get('query', '').strip()
        
        if not query:
            return Response({
                'success': False,
                'suggestions': [],
                'error': '查询内容不能为空'
            }, status=status.HTTP_400_BAD_REQUEST)

        suggestions = self.get_related_questions(query)
        
        return Response({
            'success': True,
            'suggestions': suggestions
        })

    def get_related_questions(self, query):
        """通过百度API获取相关问题推荐"""
        if not query:
            return []
        
        try:
            url = f"https://suggestion.baidu.com/su?wd={query}&p=3&cb=window.bdsug.sug"
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            
            # 解析百度建议API返回的JSONP格式
            match = re.search(r's:(\[.*?\])', response.text)
            if match:
                suggestions = json.loads(match.group(1))
                # 过滤掉与原查询相同的建议
                filtered = [s for s in suggestions if s and s.lower().strip() != query.lower().strip()]
                return filtered[:5]  # 返回前5个建议
                
        except Exception as e:
            print(f"获取相关问题时出错: {e}")
        
        # 返回默认建议
        return [
            f"关于{query}的更多信息",
            f"{query}的应用场景",
            f"{query}的优缺点",
            f"如何学习{query}",
            f"{query}的发展趋势"
        ]


class EnhancedModelsAPIView(APIView):
    """增强版可用模型API - 整合更多AI模型"""
    permission_classes = []

    def get(self, request):
        """获取可用的AI模型列表"""
        models = [
            {
                'value': 'deepseek',
                'label': 'DeepSeek深度思考',
                'description': '支持深度思考模式的AI模型',
                'supports_thinking': True
            },
            {
                'value': 'doubao',
                'label': '豆包',
                'description': '字节跳动的大语言模型',
                'supports_thinking': False
            },
            {
                'value': 'gpt5',
                'label': 'GPT-5',
                'description': 'OpenAI最新大语言模型',
                'supports_thinking': False
            },
            {
                'value': '通义千问',
                'label': '通义千问',
                'description': '阿里云的中文优化大模型',
                'supports_thinking': False
            },
            {
                'value': 'claude4',
                'label': 'Claude 4',
                'description': 'Anthropic的安全AI模型',
                'supports_thinking': False
            }
        ]
        
        return Response({
            'success': True,
            'models': models,
            'default_model': 'deepseek'
        })


class ChatModelSwitchAPIView(APIView):
    """聊天模型切换API"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """切换用户偏好的默认模型"""
        model = request.data.get('model')
        deep_thinking = request.data.get('deep_thinking', False)
        
        # 保存用户偏好到用户资料
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            profile.preferred_ai_model = model
            profile.enable_deep_thinking = deep_thinking
            profile.save()
        
        return Response({
            'success': True,
            'message': '模型设置已保存',
            'model': model,
            'deep_thinking': deep_thinking
        })

    def get(self, request):
        """获取用户的模型偏好"""
        default_model = 'deepseek'
        default_deep_thinking = True
        
        if hasattr(request.user, 'profile'):
            profile = request.user.profile
            default_model = getattr(profile, 'preferred_ai_model', default_model)
            default_deep_thinking = getattr(profile, 'enable_deep_thinking', default_deep_thinking)
        
        return Response({
            'success': True,
            'model': default_model,
            'deep_thinking': default_deep_thinking
        })