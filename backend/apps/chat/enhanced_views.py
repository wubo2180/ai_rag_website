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

        # 获取或创建会话
        session = None
        if session_id and request.user.is_authenticated:
            try:
                session = ChatSession.objects.get(id=session_id, user=request.user)
            except ChatSession.DoesNotExist:
                pass
        
        if not session and request.user.is_authenticated:
            # 创建新会话
            session_title = message[:50] + '...' if len(message) > 50 else message
            session = ChatSession.objects.create(
                user=request.user,
                title=session_title
            )

        # 保存用户消息
        if session:
            ChatMessage.objects.create(
                session=session,
                content=message,
                is_user=True
            )

        # 返回流式响应
        response = StreamingHttpResponse(
            self.generate_stream_response(message, model, deep_thinking, session, request),
            content_type='text/plain'
        )
        response['Cache-Control'] = 'no-cache'
        response['Connection'] = 'keep-alive'
        response['Access-Control-Allow-Origin'] = '*'
        return response

    def generate_stream_response(self, message, model, deep_thinking, session=None, request=None):
        """生成流式响应"""
        try:
            # API配置 - 从AI_UI_928_2整合
            api_url = getattr(settings, 'DIFY_API_URL', 'http://744149f.r31.cpolar.top/v1/chat-messages')
            api_key = getattr(settings, 'DIFY_API_KEY', 'app-K9fjgkD8JbNrNfTH2ECIv4jw')
            
            # 模型映射 - 修复：使用经过验证的模型名
            model_mapping = {
                'deepseek': '通义千问',  # 修改：默认使用通义千问
                'doubao': '豆包',
                'gpt5': 'GPT-5', 
                '通义千问': '通义千问',
                'claude4': 'Claude4'
            }

            # 选择模型 - 修复：只有特定组合支持深度思考
            if model == 'deepseek' and deep_thinking:
                large_model = 'deepseek深度思考'  # 保留深度思考模式
            else:
                large_model = model_mapping.get(model, '通义千问')  # 默认通义千问

            # 构建请求体 - 使用经过验证的格式
            request_body = {
                "inputs": {
                    "largeModel": large_model
                },
                "query": message,
                "user": f"user_{request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else 'anonymous'}",
                "response_mode": "streaming"
            }
            
            # 只在有会话ID时才添加conversation_id
            if session and session.id:
                request_body["conversation_id"] = str(session.id)

            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }

            # 动态超时配置 - 根据模型调整超时时间
            model_timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {})
            timeout_duration = model_timeouts.get(large_model, model_timeouts.get('default', 90))
            
            print(f"🕐 使用模型 {large_model}，超时时间: {timeout_duration}秒")
            
            # 调用外部API
            response = requests.post(
                api_url,
                headers=headers,
                json=request_body,
                timeout=timeout_duration,  # 使用动态超时
                stream=True
            )

            ai_content = ""
            thinking_content = ""

            if response.status_code == 200:
                # 处理流式响应
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                data = json.loads(data_str)
                                if 'answer' in data:
                                    content = data['answer']
                                    ai_content += content
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                                
                                # 如果有深度思考内容
                                if deep_thinking and 'thinking' in data:
                                    thinking = data['thinking']
                                    thinking_content += thinking
                                    yield f"data: {json.dumps({'thinking': thinking})}\n\n"
                                    
                            except json.JSONDecodeError:
                                continue

                # 保存AI响应
                if session and ai_content:
                    ai_message = ChatMessage.objects.create(
                        session=session,
                        content=ai_content,
                        is_user=False
                    )
                    # 如果有深度思考内容，也保存
                    if thinking_content:
                        ai_message.metadata = {'thinking': thinking_content}
                        ai_message.save()

                yield "data: [DONE]\n\n"
            
            else:
                # 详细错误处理 - 添加更多调试信息
                try:
                    error_response = response.text
                    print(f"Dify API 错误响应: {response.status_code} - {error_response}")
                    
                    # 尝试解析错误JSON
                    try:
                        error_json = response.json()
                        if 'message' in error_json:
                            error_detail = error_json['message']
                        else:
                            error_detail = str(error_json)
                    except:
                        error_detail = error_response
                        
                    error_msg = f"Dify API 错误 ({response.status_code}): {error_detail}"
                    
                except Exception as parse_error:
                    print(f"解析错误响应失败: {parse_error}")
                    error_msg = f"AI服务暂时不可用（错误代码: {response.status_code}）"
                
                yield f"data: {json.dumps({'content': error_msg})}\n\n"
                yield "data: [DONE]\n\n"

        except requests.exceptions.Timeout:
            yield f"data: {json.dumps({'content': '请求超时，请稍后重试。'})}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"流式响应生成错误: {e}")
            yield f"data: {json.dumps({'content': '服务暂时不可用，请稍后重试。'})}\n\n"
            yield "data: [DONE]\n\n"


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