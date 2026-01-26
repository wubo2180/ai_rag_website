"""
AI服务模块 - 与Dify API交互
"""
import requests
import logging
import json
from django.conf import settings

logger = logging.getLogger(__name__)


class AIService:
    """AI服务类，用于与Dify API交互"""
    
    def __init__(self):
        self.api_key = settings.DIFY_API_KEY
        self.base_url = settings.DIFY_API_URL
        self.default_model = getattr(settings, 'DIFY_DEFAULT_MODEL', '通义千问')
    
    def _get_model_timeout(self, model):
        """根据模型获取对应的超时时间"""
        timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {})
        return timeouts.get(model, timeouts.get('default', 90))
    
    def generate_response(self, message, user_id="default_user", session_id=None, model=None):
        """
        生成AI响应（非流式，返回完整结果）
        """
        if not model:
            model = self.default_model
        
        try:
            response = self._call_dify_api_streaming(message, user_id, session_id, model)
            return {
                'success': True,
                'response': response.get('answer', ''),
                'conversation_id': response.get('conversation_id'),
                'message_id': response.get('message_id'),
                'model': model
            }
        except Exception as e:
            logger.error(f"AI服务错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f'抱歉，AI服务暂时不可用。错误信息：{str(e)}'
            }
    
    def generate_response_stream(self, message, user_id="default_user", session_id=None, model=None):
        """
        生成AI响应（流式，逐块返回）
        
        Yields:
            dict: 每个数据块，包含 content, done, conversation_id 等
        """
        if not model:
            model = self.default_model
        
        timeout = self._get_model_timeout(model)
        url = f"{self.base_url}/chat-messages"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': message,
            'response_mode': 'streaming',
            'user': user_id
        }
        
        if model:
            payload['inputs'] = {'largeModel': model}
        
        if session_id and session_id.strip():
            payload['conversation_id'] = session_id
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=timeout,
                stream=True  # 启用流式响应
            )
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Dify API错误响应: {error_detail}")
                yield {
                    'content': f'AI服务错误: {error_detail}',
                    'done': True,
                    'error': True
                }
                return
            
            conversation_id = None
            message_id = None
            
            # 解析 SSE 流
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        try:
                            data = json.loads(line_text[6:])
                            event = data.get('event', '')
                            
                            if event == 'message':
                                # 消息片段
                                yield {
                                    'content': data.get('answer', ''),
                                    'done': False,
                                    'conversation_id': data.get('conversation_id'),
                                    'message_id': data.get('message_id')
                                }
                                conversation_id = data.get('conversation_id')
                                message_id = data.get('message_id')
                                
                            elif event == 'message_end':
                                # 消息结束
                                yield {
                                    'content': '',
                                    'done': True,
                                    'conversation_id': data.get('conversation_id'),
                                    'message_id': data.get('message_id'),
                                    'metadata': data.get('metadata', {})
                                }
                                return
                                
                            elif event == 'error':
                                # 错误事件
                                yield {
                                    'content': data.get('message', '未知错误'),
                                    'done': True,
                                    'error': True
                                }
                                return
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析SSE数据失败: {line_text}, 错误: {e}")
                            continue
            
            # 如果没有收到 message_end 事件，发送完成信号
            yield {
                'content': '',
                'done': True,
                'conversation_id': conversation_id,
                'message_id': message_id
            }
            
        except requests.exceptions.Timeout:
            logger.error("Dify API 请求超时")
            yield {
                'content': 'AI 服务响应超时，请稍后再试',
                'done': True,
                'error': True
            }
        except Exception as e:
            logger.error(f"Dify API 请求异常: {str(e)}")
            yield {
                'content': f'请求异常: {str(e)}',
                'done': True,
                'error': True
            }
    
    def _call_dify_api_streaming(self, message, user_id, session_id, model):
        """
        调用Dify API（流式模式），收集完整响应后返回
        """
        timeout = self._get_model_timeout(model)
        url = f"{self.base_url}/chat-messages"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': message,
            'response_mode': 'streaming',
            'user': user_id
        }
        
        if model:
            payload['inputs'] = {'largeModel': model}
        
        if session_id and session_id.strip():
            payload['conversation_id'] = session_id
            logger.info(f"使用已有会话ID: {session_id}")
        else:
            logger.info("创建新会话")
        
        logger.info(f"调用Dify API: {url}")
        logger.info(f"使用模型: {model}")
        logger.info(f"超时时间: {timeout}秒")
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=headers, 
                timeout=timeout,
                stream=True
            )
            
            logger.info(f"Dify API响应状态: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Dify API错误响应: {error_detail}")
                raise Exception(f"Dify API 错误 ({response.status_code}): {error_detail}")
            
            # 收集流式响应
            full_answer = ""
            conversation_id = None
            message_id = None
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        try:
                            data = json.loads(line_text[6:])
                            event = data.get('event', '')
                            
                            if event == 'message':
                                full_answer += data.get('answer', '')
                                conversation_id = data.get('conversation_id')
                                message_id = data.get('message_id')
                                
                            elif event == 'message_end':
                                conversation_id = data.get('conversation_id')
                                message_id = data.get('message_id')
                                break
                                
                            elif event == 'error':
                                raise Exception(data.get('message', '未知错误'))
                                
                        except json.JSONDecodeError as e:
                            logger.warning(f"解析SSE数据失败: {line_text}")
                            continue
            
            logger.info(f"收集到完整响应，长度: {len(full_answer)}")
            
            return {
                'answer': full_answer,
                'conversation_id': conversation_id,
                'message_id': message_id
            }
            
        except requests.exceptions.Timeout:
            logger.error("Dify API 请求超时")
            raise Exception("AI 服务响应超时，请稍后再试")
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到 Dify API")
            raise Exception("无法连接到 AI 服务，请检查网络连接")
    
    def get_available_models(self):
        """获取可用的模型列表"""
        return getattr(settings, 'AVAILABLE_AI_MODELS', [
            'deepseek深度思考',
            '通义千问',
            '腾讯混元',
            '豆包',
            'Kimi',
            'GPT-5',
            'Claude4',
            'Gemini2.5',
            'Grok-4',
            'Llama4'
        ])


# 创建全局AI服务实例
ai_service = AIService()