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
        self.api_key = os.environ.get('DIFY_AGENT_ProcessOptimization_API_KEY')
        
        if not self.api_base:
            raise ValueError("未配置 DIFY_API_URL 环境变量")
        if not self.api_key:
            raise ValueError("未配置 DIFY_AGENT_ProcessOptimization_API_KEY 环境变量")
            
        logger.info(f"初始化工艺优化Dify服务: {self.api_base}")
    
    def call_agent_streaming(
        self,
        optimization_targets: str,
        process_parameters: str,
        material_product_data: str,
        environmental_real_time_data: str,
        knowledge_constraints: str,
        historical_data: str,
        cost_consideration: str,
        environmental_requirements: str,
        expected_performance: str,
        user_id: str = None,
        conversation_id: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        调用Dify工艺优化智能体（流式响应）
        
        Args:
            optimization_targets: 优化目标
            process_parameters: 工艺参数
            material_product_data: 材料与产品数据
            environmental_real_time_data: 环境与实时数据
            knowledge_constraints: 知识与约束
            historical_data: 历史数据
            cost_consideration: 所需成本
            environmental_requirements: 环保要求
            expected_performance: 期待性能提升
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
                "optimization_targets": optimization_targets,
                "process_parameters": process_parameters,
                "material_product_data": material_product_data,
                "environmental_real_time_data": environmental_real_time_data,
                "knowledge_constraints": knowledge_constraints,
                "historical_data": historical_data,
                "cost_consideration": cost_consideration,
                "environmental_requirements": environmental_requirements,
                "expected_performance": expected_performance
            },
            "query": "请根据上述要求，分析并提供工艺优化建议",
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
                            
                            logger.debug(f"收到Dify响应: {data.get('event', 'unknown')}")
                            yield data
                            
                        except json.JSONDecodeError as e:
                            logger.warning(f"JSON解析失败: {e}, 原始数据: {data_str}")
                            continue
                            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求Dify API失败: {str(e)}"
            logger.error(error_msg)
            yield {
                'event': 'error',
                'message': error_msg
            }
    
    def call_agent_blocking(
        self,
        optimization_targets: str,
        process_parameters: str,
        material_product_data: str,
        environmental_real_time_data: str,
        knowledge_constraints: str,
        historical_data: str,
        cost_consideration: str,
        environmental_requirements: str,
        expected_performance: str,
        user_id: str = None,
        conversation_id: str = ""
    ) -> Dict[str, Any]:
        """
        调用Dify工艺优化智能体（阻塞式响应）
        
        Args:
            optimization_targets: 优化目标
            process_parameters: 工艺参数
            material_product_data: 材料与产品数据
            environmental_real_time_data: 环境与实时数据
            knowledge_constraints: 知识与约束
            historical_data: 历史数据
            cost_consideration: 所需成本
            environmental_requirements: 环保要求
            expected_performance: 期待性能提升
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
                "optimization_targets": optimization_targets,
                "process_parameters": process_parameters,
                "material_product_data": material_product_data,
                "environmental_real_time_data": environmental_real_time_data,
                "knowledge_constraints": knowledge_constraints,
                "historical_data": historical_data,
                "cost_consideration": cost_consideration,
                "environmental_requirements": environmental_requirements,
                "expected_performance": expected_performance
            },
            "query": "请根据上述要求，分析并提供工艺优化建议",
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user_id or f"user-{id(self)}"
        }
        
        try:
            logger.info(f"发送工艺优化请求到Dify (阻塞模式): {url}")
            logger.debug(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
            
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
                    'error': True,
                    'message': error_msg,
                    'status_code': response.status_code
                }
            
            result = response.json()
            logger.info("工艺优化请求成功完成")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = f"请求Dify API失败: {str(e)}"
            logger.error(error_msg)
            return {
                'error': True,
                'message': error_msg
            }
