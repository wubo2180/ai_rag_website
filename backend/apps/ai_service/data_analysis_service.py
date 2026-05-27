"""
数据分析智能体的Dify API调用服务
专门处理与Dify平台的材料数据分析相关API交互
支持柱状图、饼状图、热力图、表格等可视化数据返回
"""

import requests
import json
import math
import re
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
        self.api_key = os.environ.get('DIFY_AGENT_DataAnalysis_API_KEY')

        logger.info(f"初始化数据分析Dify服务: {self.api_base}")

    @staticmethod
    def _compact_text(value: str, max_len: int = 200) -> str:
        """将输入压缩到 Dify 输入控件可接受长度（默认 200）以内。"""
        text = (value or "").strip()
        if len(text) <= max_len:
            return text
        if max_len <= 3:
            return text[:max_len]
        return text[: max_len - 3] + "..."

    @staticmethod
    def _is_input_length_error(status_code: int, response_text: str) -> bool:
        """识别 Dify 输入长度限制报错。"""
        if status_code != 400:
            return False
        text = (response_text or "").lower()
        return (
            "invalid_param" in text
            and "must be less than" in text
            and "in input form" in text
        )

    @staticmethod
    def _build_query(
        data_content: str,
        analysis_type: str,
        data_description: str,
        analysis_goal: str,
    ) -> str:
        """构建 query，携带完整数据（避免输入控件长度限制影响）。"""
        return (
            "请基于以下完整输入变量完成材料数据分析，并严格按要求输出 JSON。\n"
            f"分析目标: {analysis_goal or ''}\n"
            f"分析类型: {analysis_type or ''}\n"
            f"数据背景: {data_description or ''}\n"
            "材料数据:\n"
            f"{data_content or ''}"
        )

    @staticmethod
    def _build_inputs(
        data_content: str,
        analysis_type: str,
        data_description: str,
        analysis_goal: str,
        compact: bool = False,
    ) -> Dict[str, Any]:
        """构建发送给 Dify 的 inputs，兼容新旧变量命名。"""
        context_parts = []
        if analysis_type:
            context_parts.append(f"分析类型: {analysis_type}")
        if data_description:
            context_parts.append(f"数据背景: {data_description}")
        data_context = "；".join(context_parts)

        material_data = data_content
        data_content_value = data_content
        analysis_goal_value = analysis_goal
        data_context_value = data_context
        analysis_type_value = analysis_type
        data_description_value = data_description

        if compact:
            material_data = DataAnalysisDifyService._compact_text(material_data)
            data_content_value = DataAnalysisDifyService._compact_text(data_content_value)
            analysis_goal_value = DataAnalysisDifyService._compact_text(analysis_goal_value)
            data_context_value = DataAnalysisDifyService._compact_text(data_context_value)
            analysis_type_value = DataAnalysisDifyService._compact_text(analysis_type_value)
            data_description_value = DataAnalysisDifyService._compact_text(data_description_value)

        return {
            # 新变量（Dify 页面推荐）
            "material_data": material_data,
            "analysis_goal": analysis_goal_value,
            "data_context": data_context_value,
            # 旧变量（向后兼容）
            "data_content": data_content_value,
            "analysis_type": analysis_type_value,
            "data_description": data_description_value,
        }

    def call_agent_streaming(
        self,
        data_content: str,
        analysis_type: str,
        data_description: str,
        analysis_goal: str,
        user_id: Optional[str] = None,
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

        query = self._build_query(
            data_content=data_content,
            analysis_type=analysis_type,
            data_description=data_description,
            analysis_goal=analysis_goal,
        )

        payload = {
            "inputs": self._build_inputs(
                data_content=data_content,
                analysis_type=analysis_type,
                data_description=data_description,
                analysis_goal=analysis_goal,
                compact=False,
            ),
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

            # 兼容 Dify 输入控件长度限制，自动重试一次（压缩 inputs，完整数据保留在 query）。
            if self._is_input_length_error(response.status_code, response.text):
                logger.warning("检测到 Dify 输入长度限制，切换 compact inputs 重试")
                payload["inputs"] = self._build_inputs(
                    data_content=data_content,
                    analysis_type=analysis_type,
                    data_description=data_description,
                    analysis_goal=analysis_goal,
                    compact=True,
                )
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
        user_id: Optional[str] = None,
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

        query = self._build_query(
            data_content=data_content,
            analysis_type=analysis_type,
            data_description=data_description,
            analysis_goal=analysis_goal,
        )

        # 兼容 Agent Chat App（不支持 blocking mode）：
        # 统一采用 streaming 并在后端聚合为一次性返回。
        payload = {
            "inputs": self._build_inputs(
                data_content=data_content,
                analysis_type=analysis_type,
                data_description=data_description,
                analysis_goal=analysis_goal,
                compact=False,
            ),
            "query": query,
            "response_mode": "streaming",
            "conversation_id": conversation_id,
            "user": user_id or f"user-{id(self)}"
        }

        try:
            logger.info(f"发送数据分析请求到Dify (流式聚合模式): {url}")

            response = requests.post(
                url,
                headers=headers,
                json=payload,
                stream=True,
                timeout=180
            )

            # 兼容 Dify 输入控件长度限制，自动重试一次（压缩 inputs，完整数据保留在 query）。
            if self._is_input_length_error(response.status_code, response.text):
                logger.warning("检测到 Dify 输入长度限制，切换 compact inputs 重试")
                payload["inputs"] = self._build_inputs(
                    data_content=data_content,
                    analysis_type=analysis_type,
                    data_description=data_description,
                    analysis_goal=analysis_goal,
                    compact=True,
                )
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
                return {
                    'success': False,
                    'error': error_msg,
                    'status_code': response.status_code
                }

            full_answer = ""
            final_event: Dict[str, Any] = {}

            for line in response.iter_lines():
                if not line:
                    continue

                line_text = line.decode('utf-8')
                if not line_text.startswith('data: '):
                    continue

                data_str = line_text[6:]
                try:
                    event = json.loads(data_str)
                except json.JSONDecodeError:
                    logger.warning(f"阻塞聚合模式解析事件失败: {line_text}")
                    continue

                event_type = event.get('event', '')
                if event_type in ('message', 'agent_message'):
                    full_answer += event.get('answer', '') or ''

                if event_type in ('message_end', 'agent_message_end'):
                    final_event = event
                    break

                if event_type == 'error':
                    error_msg = event.get('message', '未知错误')
                    return {
                        'success': False,
                        'error': f"Dify流式响应错误: {error_msg}"
                    }

            result = {
                'answer': full_answer,
                'conversation_id': final_event.get('conversation_id', ''),
                'id': final_event.get('id', ''),
                'metadata': final_event.get('metadata', {}),
            }

            logger.info("成功聚合Dify数据分析响应")
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
            'summary': '',  # 文字结论
            'insights': [],
            'rankings': [],
            'anomalies': [],
            # 新版结构扩展字段
            'statistics': None,
            'key_findings': [],
            'trends': [],
            'recommendations': [],
            'visualization_suggestions': [],
        }

        if not answer:
            return visualization

        def _to_float_list(raw: str) -> list:
            values = []
            for token in re.split(r'[，,\s]+', (raw or '').strip()):
                token = token.strip()
                if not token:
                    continue
                try:
                    values.append(float(token))
                except ValueError:
                    continue
            return values

        def _compute_stats(values: list) -> Dict[str, Any]:
            if not values:
                return {'min': None, 'max': None, 'mean': None, 'std': None}
            n = len(values)
            mean = sum(values) / n
            variance = sum((v - mean) ** 2 for v in values) / n
            std = math.sqrt(variance)
            return {
                'min': round(min(values), 4),
                'max': round(max(values), 4),
                'mean': round(mean, 4),
                'std': round(std, 4),
            }

        def _infer_visualization_from_text(raw_text: str) -> None:
            text = (raw_text or '').strip()
            if not text:
                return

            # 提取“材料”列表（支持：材料/材料名/材料名称）
            materials = []
            material_match = re.search(r'(?:^|\n)\s*[-*•]?\s*材料(?:名称|名)?\s*[:：]\s*(.+)', text)
            if material_match:
                materials_raw = material_match.group(1).strip()
                materials_raw = materials_raw.split('\n')[0].strip()
                materials = [
                    item.strip()
                    for item in re.split(r'[、，,]', materials_raw)
                    if item.strip()
                ]

            # 提取“指标: [1,2,3]”模式
            metric_series: Dict[str, list] = {}
            array_pattern = re.compile(
                r'(?:^|\n)\s*[-*•]?\s*([\u4e00-\u9fa5A-Za-z0-9_\-]{1,30})\s*[:：]\s*\[([^\]]+)\]'
            )
            for m in array_pattern.finditer(text):
                metric = (m.group(1) or '').strip()
                values = _to_float_list(m.group(2))
                if values:
                    metric_series[metric] = values

            if not metric_series:
                return

            # 统一长度，避免图表因维度不一致报错
            min_len = min(len(v) for v in metric_series.values())
            if min_len <= 0:
                return

            for key in list(metric_series.keys()):
                metric_series[key] = metric_series[key][:min_len]

            if not materials or len(materials) < min_len:
                materials = [f'样本{i + 1}' for i in range(min_len)]
            else:
                materials = materials[:min_len]

            # 自动生成 statistics
            numeric_stats = {
                metric: _compute_stats(values)
                for metric, values in metric_series.items()
            }
            visualization['statistics'] = {
                'sample_count': min_len,
                'columns': ['材料', *list(metric_series.keys())],
                'numeric_stats': numeric_stats,
            }

            # 自动生成洞察
            if not visualization['insights']:
                insights = []
                for metric, values in metric_series.items():
                    max_idx = max(range(len(values)), key=lambda i: values[i])
                    min_idx = min(range(len(values)), key=lambda i: values[i])
                    insights.append(f"{metric}最高为{materials[max_idx]}（{values[max_idx]}）")
                    insights.append(f"{metric}最低为{materials[min_idx]}（{values[min_idx]}）")
                    if len(insights) >= 4:
                        break
                visualization['insights'] = insights

            # 自动生成表格
            if not visualization['tables']:
                metric_names = list(metric_series.keys())
                rows = []
                for i, name in enumerate(materials):
                    row = [name]
                    for metric in metric_names:
                        row.append(metric_series[metric][i])
                    rows.append(row)

                visualization['tables'] = [
                    {
                        'title': '材料指标明细',
                        'columns': ['材料', *metric_names],
                        'rows': rows,
                    }
                ]

            # 自动生成图表
            if not visualization['charts']:
                metric_names = list(metric_series.keys())
                first_metric = metric_names[0]

                # 1) 柱状图（首要指标）
                visualization['charts'].append({
                    'title': f'{first_metric}对比',
                    'type': 'bar',
                    'data': {
                        'labels': materials,
                        'datasets': [
                            {
                                'label': first_metric,
                                'data': metric_series[first_metric],
                            }
                        ],
                    },
                })

                # 2) 折线图（全部指标）
                visualization['charts'].append({
                    'title': '关键指标趋势',
                    'type': 'line',
                    'data': {
                        'labels': materials,
                        'datasets': [
                            {
                                'label': metric,
                                'data': metric_series[metric],
                            }
                            for metric in metric_names
                        ],
                    },
                })

                # 3) 饼图（优先成本，否则首要指标）
                pie_metric = None
                for candidate in ('成本', 'cost', 'Cost'):
                    if candidate in metric_series:
                        pie_metric = candidate
                        break
                pie_metric = pie_metric or first_metric

                visualization['charts'].append({
                    'title': f'{pie_metric}占比',
                    'type': 'pie',
                    'data': {
                        'labels': materials,
                        'datasets': [
                            {
                                'data': metric_series[pie_metric],
                            }
                        ],
                    },
                })

                # 4) 热力图（材料×指标）
                values_matrix = []
                for i in range(min_len):
                    values_matrix.append([
                        metric_series[metric][i]
                        for metric in metric_names
                    ])

                visualization['charts'].append({
                    'title': '材料-指标热力图',
                    'type': 'heatmap',
                    'data': {
                        'xLabels': metric_names,
                        'yLabels': materials,
                        'values': values_matrix,
                    },
                })

            # 如果 summary 仍为空，给一个简短总结
            if not visualization['summary']:
                first_metric = list(metric_series.keys())[0]
                first_values = metric_series[first_metric]
                max_idx = max(range(len(first_values)), key=lambda i: first_values[i])
                visualization['summary'] = f"已从文本中提取{len(metric_series)}个数值指标并生成图表，{first_metric}最高为{materials[max_idx]}。"

        def _build_charts_from_statistics() -> None:
            """当返回结构化结果但无 charts 时，基于 statistics 自动补图。"""
            stats = visualization.get('statistics') or {}
            numeric_stats = stats.get('numeric_stats') if isinstance(stats, dict) else None
            if not isinstance(numeric_stats, dict) or not numeric_stats:
                return

            metrics = list(numeric_stats.keys())

            def _num(value):
                try:
                    if value is None:
                        return 0.0
                    return float(value)
                except Exception:
                    return 0.0

            means = [_num(numeric_stats[m].get('mean')) for m in metrics]
            mins = [_num(numeric_stats[m].get('min')) for m in metrics]
            maxs = [_num(numeric_stats[m].get('max')) for m in metrics]
            stds = [_num(numeric_stats[m].get('std')) for m in metrics]

            # 1) 各指标均值柱状图
            visualization['charts'].append({
                'title': '各指标均值对比',
                'type': 'bar',
                'data': {
                    'labels': metrics,
                    'datasets': [
                        {'label': '均值', 'data': means}
                    ]
                }
            })

            # 2) min/mean/max 趋势折线
            visualization['charts'].append({
                'title': '指标统计分布（min/mean/max）',
                'type': 'line',
                'data': {
                    'labels': metrics,
                    'datasets': [
                        {'label': 'min', 'data': mins},
                        {'label': 'mean', 'data': means},
                        {'label': 'max', 'data': maxs},
                    ]
                }
            })

            # 3) 均值占比饼图（非负化）
            pie_values = [max(0.0, v) for v in means]
            if any(v > 0 for v in pie_values):
                visualization['charts'].append({
                    'title': '各指标均值占比',
                    'type': 'pie',
                    'data': {
                        'labels': metrics,
                        'datasets': [
                            {'data': pie_values}
                        ]
                    }
                })

            # 4) 热力图（指标 × 统计项）
            visualization['charts'].append({
                'title': '指标统计热力图',
                'type': 'heatmap',
                'data': {
                    'xLabels': ['min', 'mean', 'max', 'std'],
                    'yLabels': metrics,
                    'values': [
                        [mins[i], means[i], maxs[i], stds[i]]
                        for i in range(len(metrics))
                    ]
                }
            })

        def _merge_parsed(parsed: Dict[str, Any]) -> None:
            if not isinstance(parsed, dict):
                return

            # 旧版字段
            if isinstance(parsed.get('charts'), list):
                visualization['charts'].extend(parsed.get('charts', []))
            if isinstance(parsed.get('tables'), list):
                visualization['tables'].extend(parsed.get('tables', []))
            if isinstance(parsed.get('summary'), str):
                visualization['summary'] = parsed.get('summary', '')
            if isinstance(parsed.get('insights'), list):
                visualization['insights'] = parsed.get('insights', [])
            if isinstance(parsed.get('rankings'), list):
                visualization['rankings'] = parsed.get('rankings', [])
            if isinstance(parsed.get('anomalies'), list):
                visualization['anomalies'] = parsed.get('anomalies', [])

            # 新版字段
            if parsed.get('statistics') is not None:
                visualization['statistics'] = parsed.get('statistics')
            if isinstance(parsed.get('key_findings'), list):
                visualization['key_findings'] = parsed.get('key_findings', [])
                # 前端已有 insights 区块，自动复用
                if not visualization['insights']:
                    visualization['insights'] = parsed.get('key_findings', [])
            if isinstance(parsed.get('trends'), list):
                visualization['trends'] = parsed.get('trends', [])
            if isinstance(parsed.get('recommendations'), list):
                visualization['recommendations'] = parsed.get('recommendations', [])
            if isinstance(parsed.get('visualization_suggestions'), list):
                visualization['visualization_suggestions'] = parsed.get('visualization_suggestions', [])

        # 尝试提取 ```json ... ``` 或 ``` ... ``` 代码块
        json_blocks = re.findall(r'```(?:json)?\s*([\s\S]*?)\s*```', answer)
        for block in json_blocks:
            try:
                parsed = json.loads(block)
                _merge_parsed(parsed)
            except json.JSONDecodeError:
                pass

        # 如果没有提取到JSON块，尝试整体解析
        if not visualization['charts'] and not visualization['tables']:
            try:
                parsed = json.loads(answer)
                _merge_parsed(parsed)
            except json.JSONDecodeError:
                pass

        # 最后兜底：如果仍无图表，先尝试从纯文本提取，再尝试从结构化 statistics 补图
        if not visualization['charts']:
            _infer_visualization_from_text(answer)
        if not visualization['charts']:
            _build_charts_from_statistics()

        # 如果仍然没有可视化数据，将回答作为summary
        if not visualization['summary']:
            visualization['summary'] = answer

        return visualization


# 创建单例实例
data_analysis_dify_service = DataAnalysisDifyService()
