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
        self.base_url = settings.DIFY_BASE_URL
        self.default_model = getattr(settings, 'DIFY_DEFAULT_MODEL', '通义千问')
    
    def _get_model_timeout(self, model):
        """根据模型获取对应的超时时间"""
        timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {})
        return timeouts.get(model, timeouts.get('default', 90))
    
    def generate_response(self, message, user_id="default_user", session_id=None, model=None):
        """
        生成AI响应
        
        Args:
            message: 用户消息
            user_id: 用户ID
            session_id: Dify的会话ID（UUID格式，可选）
            model: 使用的模型名称（可选，默认使用配置中的模型）
        
        Returns:
            dict: API响应结果，包含：
                - success: 是否成功
                - response: AI回复内容
                - conversation_id: Dify的会话ID（UUID）
                - message_id: Dify的消息ID
                - model: 使用的模型名称
        """
        if not model:
            model = self.default_model
        
        try:
            response = self._call_dify_api(message, user_id, session_id, model)
            return {
                'success': True,
                'response': response.get('answer', ''),
                'conversation_id': response.get('conversation_id'),  # Dify的UUID
                'message_id': response.get('message_id'),  # Dify的消息ID
                'model': model
            }
        except Exception as e:
            logger.error(f"AI服务错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'response': f'抱歉，AI服务暂时不可用。错误信息：{str(e)}'
            }
    
    def _call_dify_api(self, message, user_id, session_id, model):
        """
        调用Dify API
        
        Args:
            message: 用户消息
            user_id: 用户ID
            session_id: Dify的会话ID（UUID格式，可选）
            model: 模型名称
        
        Returns:
            dict: API响应
        """
        # 获取模型对应的超时时间
        timeout = self._get_model_timeout(model)
        
        url = f"{self.base_url}/chat-messages"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        # 基础 payload - 不包含 inputs
        # Dify API 的基本参数
        payload = {
            'query': message,
            'response_mode': 'blocking',
            'user': user_id
        }
        
        # 尝试添加 inputs 参数（如果 Dify 工作流需要）
        # 注意：这取决于你的 Dify 工作流配置
        # 如果工作流不需要 inputs 参数，请注释掉下面这段
        if model:
            payload['inputs'] = {'largeModel': model}
        
        # 只有在session_id存在且不为空时才添加到请求中
        # session_id必须是Dify返回的UUID格式
        if session_id and session_id.strip():
            payload['conversation_id'] = session_id
            logger.info(f"使用已有会话ID: {session_id}")
        else:
            logger.info("创建新会话")
        
        logger.info(f"调用Dify API: {url}")
        logger.info(f"使用模型: {model}")
        logger.info(f"超时时间: {timeout}秒")
        logger.info(f"请求 payload: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout)
            
            # 记录响应状态
            logger.info(f"Dify API响应状态: {response.status_code}")
            
            if response.status_code != 200:
                error_detail = response.text
                logger.error(f"Dify API错误响应: {error_detail}")
                
                # 尝试解析JSON错误信息
                try:
                    error_json = response.json()
                    error_message = error_json.get('message', error_detail)
                    logger.error(f"Dify API错误详情: {error_message}")
                except:
                    error_message = error_detail
                
                raise Exception(f"Dify API 错误 ({response.status_code}): {error_message}")
            
            result = response.json()
            logger.debug(f"API响应: {result}")
            
            return result
            
        except requests.exceptions.Timeout:
            logger.error("Dify API 请求超时")
            raise Exception("AI 服务响应超时，请稍后再试")
        except requests.exceptions.ConnectionError:
            logger.error("无法连接到 Dify API")
            raise Exception("无法连接到 AI 服务，请检查网络连接")
        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API 请求异常: {str(e)}")
            raise
    
    def get_available_models(self):
        """
        获取可用的模型列表
        
        Returns:
            list: 可用模型列表
        """
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
