import os
import requests
import json
import logging
from typing import Dict, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

class DifyAPIClient:
    """Dify API客户端"""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or getattr(settings, 'DIFY_API_KEY', os.getenv('DIFY_API_KEY'))
        self.base_url = base_url or getattr(settings, 'DIFY_BASE_URL', os.getenv('DIFY_BASE_URL', 'https://api.dify.ai/v1'))
        
        if not self.api_key or self.api_key == 'your-dify-api-key':
            logger.warning("Dify API key not configured, using fallback responses")
            self.api_key = None
    
    def _make_request(self, method: str, endpoint: str, data: dict = None, params: dict = None) -> dict:
        """发送API请求"""
        if not self.api_key:
            # 如果没有配置API Key，返回模拟响应
            return self._get_fallback_response(data.get('query', '') if data else '')
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'Django-RAG-Website/1.0'
        }
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Dify API request failed: {e}")
            return self._get_fallback_response(data.get('query', '') if data else '')
    
    def _get_fallback_response(self, query: str) -> dict:
        """API不可用时的回退响应"""
        fallback_responses = {
            '你好': '您好！我是AI助手，很高兴为您服务！',
            'hello': 'Hello! How can I help you today?',
            '天气': '抱歉，我无法获取实时天气信息，建议您查看天气应用。',
            '时间': '我无法获取当前时间，请查看您的设备时钟。',
        }
        
        query_lower = query.lower()
        for key, response in fallback_responses.items():
            if key in query_lower:
                return {
                    'answer': response,
                    'conversation_id': f'fallback_{hash(query) % 10000}',
                    'message_id': f'msg_{hash(query) % 10000}',
                    'metadata': {'source': 'fallback'}
                }
        
        return {
            'answer': f'感谢您的提问："{query}"。我正在努力理解您的需求，但目前AI服务暂时不可用。请稍后再试或联系管理员。',
            'conversation_id': f'fallback_{hash(query) % 10000}',
            'message_id': f'msg_{hash(query) % 10000}',
            'metadata': {'source': 'fallback'}
        }
    
    def chat_completion(self, 
                       query: str, 
                       user: str = "default_user",
                       conversation_id: str = None,
                       inputs: dict = None,
                       response_mode: str = "blocking") -> dict:
        """聊天完成API"""
        data = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": response_mode,
            "user": user,
        }
        
        if conversation_id:
            data["conversation_id"] = conversation_id
        
        endpoint = "chat-messages"
        return self._make_request("POST", endpoint, data)

class AIService:
    """AI服务统一接口"""
    
    def __init__(self):
        self.dify_client = DifyAPIClient()
    
    def generate_response(self, message: str, session_id: str = None, user_id: str = None) -> dict:
        """生成AI回复"""
        try:
            user = f"user_{user_id}" if user_id else "anonymous"
            
            response = self.dify_client.chat_completion(
                query=message,
                user=user,
                conversation_id=session_id
            )
            
            return {
                'success': True,
                'response': response.get('answer', '抱歉，我现在无法回答这个问题。'),
                'conversation_id': response.get('conversation_id'),
                'message_id': response.get('message_id'),
                'metadata': response.get('metadata', {})
            }
            
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': '抱歉，服务暂时不可用，请稍后再试。'
            }
    
    def search_knowledge(self, query: str, limit: int = 5) -> List[dict]:
        """搜索知识库"""
        try:
            from apps.knowledge.models import Knowledge
            
            results = Knowledge.objects.filter(
                title__icontains=query,
                is_active=True
            ) | Knowledge.objects.filter(
                content__icontains=query,
                is_active=True
            )
            
            return [
                {
                    'title': item.title,
                    'content': item.content[:200] + '...' if len(item.content) > 200 else item.content,
                    'category': item.category,
                    'score': 0.8
                }
                for item in results[:limit]
            ]
        except Exception as e:
            logger.error(f"Knowledge search failed: {e}")
            return []

# 全局AI服务实例
ai_service = AIService()