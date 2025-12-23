"""
工艺优化智能体的Dify API调用服务
专门处理与Dify平台的工艺优化相关API交互
"""

import requests
import json
from typing import Dict, Any, Generator, Optional
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


class ProcessOptimizationDifyService:
    """工艺优化Dify API服务类"""
    
    def __init__(self):
        """初始化服务"""
        # 从环境变量或settings获取配置
        self.api_base = os.environ.get('DIFY_API_URL')
        self.api_key = os.environ.get('DIFY_AGENT_RECIPE_GENERATION_API_KEY')
        
        logger.info(f"初始化工艺优化Dify服务: {self.api_base}")
    
    def call_agent_streaming(
        self,
        product_performance: str,
        target_application_scenario: str,
        cost_consideration: str,
        environmental_requirements: str,
        user_id: str = None,
        conversation_id: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        调用Dify工艺优化智能体（流式响应）
        
        Args:
            product_performance: 产品性能要求
            target_application_scenario: 目标应用场景
            cost_consideration: 成本考量
            environmental_requirements: 环保要求
            user_id: 用户ID
            conversation_id: 会话ID（用于多轮对话）
            
        Yields:
            Dict: 流式响应数据
        """
        url = f"{self.api_base}/chat-messages"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "inputs": {
                "product_performance": product_performance,
                "target_application_scenario": target_application_scenario,
                "cost_consideration": cost_consideration,
                "environmental_requirements": environmental_requirements
            },
            "query": "请根据上述要求，生成材料配方建议",
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user_id or f"user-{id(self)}"
        }
        
        try:
            logger.info(f"发送工艺优化请求到Dify: {url}")
            logger.debug(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = f"Dify API错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                yield {
                    'event': 'error',
                    'message': error_msg,
                    'status_code': response.status_code
                }
                return
            
            # 处理流式响应
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    
                    # SSE格式: data: {...}
                    if line_text.startswith('data: '):
                        try:
                            data_str = line_text[6:]  # 去掉 "data: " 前缀
                            data = json.loads(data_str)
                            
                            # 返回解析后的数据
                            yield data
                            
                            logger.debug(f"收到事件: {data.get('event', 'unknown')}")
                            
                        except json.JSONDecodeError as e:
                            logger.error(f"解析JSON失败: {e}, 原文: {data_str}")
                            yield {
                                'event': 'error',
                                'message': f'解析响应失败: {str(e)}'
                            }
        
        except requests.exceptions.RequestException as e:
            error_msg = f"请求Dify API失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                'event': 'error',
                'message': error_msg
            }
        except Exception as e:
            error_msg = f"处理Dify响应时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {
                'event': 'error',
                'message': error_msg
            }
    
    def call_agent_blocking(
        self,
        product_performance: str,
        target_application_scenario: str,
        cost_consideration: str,
        environmental_requirements: str,
        user_id: str = None,
        conversation_id: str = ""
    ) -> Dict[str, Any]:
        """
        调用Dify工艺优化智能体（阻塞响应）
        
        Args:
            product_performance: 产品性能要求
            target_application_scenario: 目标应用场景
            cost_consideration: 成本考量
            environmental_requirements: 环保要求
            user_id: 用户ID
            conversation_id: 会话ID
            
        Returns:
            Dict: 完整响应数据
        """
        url = f"{self.api_base}/chat-messages"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "inputs": {
                "product_performance": product_performance,
                "target_application_scenario": target_application_scenario,
                "cost_consideration": cost_consideration,
                "environmental_requirements": environmental_requirements
            },
            "query": "请根据上述要求，生成材料配方建议",
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user_id or f"user-{id(self)}"
        }
        
        try:
            logger.info(f"发送工艺优化请求到Dify (阻塞模式): {url}")
            
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                error_msg = f"Dify API错误: {response.status_code} - {response.text}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }
            
            result = response.json()
            logger.info("成功接收Dify响应")
            
            return {
                'success': True,
                'data': result
            }
        
        except requests.exceptions.RequestException as e:
            error_msg = f"请求Dify API失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
        except Exception as e:
            error_msg = f"处理Dify响应时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg
            }
    
    def get_conversation_history(
        self,
        conversation_id: str,
        user_id: str = None
    ) -> Dict[str, Any]:
        """
        获取会话历史
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            
        Returns:
            Dict: 会话历史数据
        """
        url = f"{self.api_base}/messages"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'conversation_id': conversation_id,
            'user': user_id or f"user-{id(self)}"
        }
        
        try:
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"获取会话历史失败: {response.status_code}"
                }
            
            return {
                'success': True,
                'data': response.json()
            }
        
        except Exception as e:
            logger.error(f"获取会话历史失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


# 创建单例实例
process_optimization_dify_service = ProcessOptimizationDifyService()
