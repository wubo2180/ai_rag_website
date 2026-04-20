"""
数据分析智能体的Dify API调用服务
专门处理与Dify平台的材料数据分析相关API交互
支持柱状图、饼状图、热力图、表格等可视化数据返回
"""

import requests
import json
from typing import Dict, Any, Generator, Optional
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


class DataAnalysisDifyService:
    """数据分析Dify API服务类"""

    def __init__(self):
        """初始化服务"""
        self.api_base = os.environ.get('DIFY_API_URL')
        self.api_key = os.environ.get('DIFY_AGENT_DATA_ANALYSIS_API_KEY')

        logger.info(f"初始化数据分析Dify服务: {self.api_base}")

    def call_agent_streaming(
        self,
        data_content: str,
        analysis_type: str,
        data_description: str,
        analysis_goal: str,
        user_id: str = None,
        conversation_id: str = ""
    ) -> Generator[Dict[str, Any], None, None]:
        """
        调用Dify数据分析智能体（流式响应）

        Args:
            data_content: 材料数据内容（文本/JSON/CSV格式）
            analysis_type: 分析类型（trend/pattern/comparison/distribution）
            data_description: 数据背景描述
            analysis_goal: 分析目标
            user_id: 用户ID
            conversation_id: 会话ID

        Yields:
            Dict: 流式响应数据
        """
        url = f"{self.api_base}/chat-messages"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        query = (
            f"请对以下材料数据进行{analysis_goal}分析，"
            f"要求以JSON格式输出可视化数据（包含柱状图、饼状图、热力图、表格），"
            f"并给出文字分析结论和发现的隐藏模式与趋势。"
        )

        payload = {
            "inputs": {
                "data_content": data_content,
                "analysis_type": analysis_type,
                "data_description": data_description,
                "analysis_goal": analysis_goal
            },
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user_id or f"user-{id(self)}"
        }

        try:
            logger.info(f"发送数据分析请求到Dify: {url}")
            logger.debug(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=180
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

            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8')
                    if line_text.startswith('data: '):
                        try:
                            data_str = line_text[6:]
                            data = json.loads(data_str)
                            yield data
                            logger.debug(f"收到事件: {data.get('event', 'unknown')}")
                        except json.JSONDecodeError as e:
                            logger.error(f"解析JSON失败: {e}, 原文: {line_text}")
                            yield {
                                'event': 'error',
                                'message': f'解析响应失败: {str(e)}'
                            }

        except requests.exceptions.RequestException as e:
            error_msg = f"请求Dify API失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {'event': 'error', 'message': error_msg}
        except Exception as e:
            error_msg = f"处理Dify响应时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            yield {'event': 'error', 'message': error_msg}

    def call_agent_blocking(
        self,
        data_content: str,
        analysis_type: str,
        data_description: str,
        analysis_goal: str,
        user_id: str = None,
        conversation_id: str = ""
    ) -> Dict[str, Any]:
        """
        调用Dify数据分析智能体（阻塞响应）

        Args:
            data_content: 材料数据内容
            analysis_type: 分析类型
            data_description: 数据背景描述
            analysis_goal: 分析目标
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

        query = (
            f"请对以下材料数据进行{analysis_goal}分析，"
            f"要求以JSON格式输出可视化数据（包含柱状图、饼状图、热力图、表格），"
            f"并给出文字分析结论和发现的隐藏模式与趋势。"
        )

        payload = {
            "inputs": {
                "data_content": data_content,
                "analysis_type": analysis_type,
                "data_description": data_description,
                "analysis_goal": analysis_goal
            },
            "query": query,
            "response_mode": "blocking",
            "conversation_id": conversation_id,
            "user": user_id or f"user-{id(self)}"
        }

        try:
            logger.info(f"发送数据分析请求到Dify (阻塞模式): {url}")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=180
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
            logger.info("成功接收Dify数据分析响应")

            return {
                'success': True,
                'data': result
            }

        except requests.exceptions.RequestException as e:
            error_msg = f"请求Dify API失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f"处理Dify响应时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {'success': False, 'error': error_msg}

    def parse_visualization_data(self, answer: str) -> Dict[str, Any]:
        """
        从AI回答中解析可视化数据

        尝试从回答文本中提取JSON格式的可视化配置块，
        支持 ```json ... ``` 代码块或直接JSON对象。

        Args:
            answer: AI回答的完整文本

        Returns:
            Dict: 解析后的可视化数据，包含 charts 列表和 tables 列表
        """
        visualization = {
            'charts': [],   # [{type, title, data, options}]
            'tables': [],   # [{title, columns, rows}]
            'summary': ''   # 文字结论
        }

        if not answer:
            return visualization

        # 尝试提取 ```json ... ``` 代码块
        import re
        json_blocks = re.findall(r'```json\s*([\s\S]*?)\s*```', answer)
        for block in json_blocks:
            try:
                parsed = json.loads(block)
                if isinstance(parsed, dict):
                    # 合并 charts/tables
                    if 'charts' in parsed:
                        visualization['charts'].extend(parsed['charts'])
                    if 'tables' in parsed:
                        visualization['tables'].extend(parsed['tables'])
                    if 'summary' in parsed:
                        visualization['summary'] = parsed['summary']
            except json.JSONDecodeError:
                pass

        # 如果没有提取到JSON块，尝试整体解析
        if not visualization['charts'] and not visualization['tables']:
            try:
                parsed = json.loads(answer)
                if isinstance(parsed, dict):
                    visualization['charts'] = parsed.get('charts', [])
                    visualization['tables'] = parsed.get('tables', [])
                    visualization['summary'] = parsed.get('summary', '')
            except json.JSONDecodeError:
                pass

        # 如果仍然没有可视化数据，将回答作为summary
        if not visualization['summary']:
            visualization['summary'] = answer

        return visualization


# 创建单例实例
data_analysis_dify_service = DataAnalysisDifyService()
