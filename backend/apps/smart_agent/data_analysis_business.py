"""
数据分析智能体业务逻辑服务
处理材料数据分析相关的业务逻辑，调用ai_service中的Dify API
支持发现隐藏模式和趋势，输出柱状图、饼状图、热力图、表格等可视化数据
"""

from typing import Dict, Any, Generator
from django.utils import timezone
from apps.ai_service.data_analysis_service import data_analysis_dify_service
from .models import SmartAgent, AgentTask, AgentExecution, TaskStatus
import logging
import json

logger = logging.getLogger(__name__)

# 支持的分析类型
ANALYSIS_TYPES = {
    'trend': '趋势分析',
    'pattern': '模式识别',
    'comparison': '对比分析',
    'distribution': '分布分析',
    'correlation': '相关性分析',
    'comprehensive': '综合分析'
}


class DataAnalysisService:
    """数据分析智能体业务服务类"""

    def __init__(self):
        """初始化服务"""
        self.dify_service = data_analysis_dify_service

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证输入参数

        Args:
            inputs: 输入参数字典

        Returns:
            Dict: 验证结果 {'valid': bool, 'errors': list}
        """
        errors = []

        # 必填字段
        if not inputs.get('data_content'):
            errors.append("缺少必填字段: data_content（材料数据内容）")
        elif not isinstance(inputs['data_content'], str):
            errors.append("字段 data_content 必须是字符串类型")
        elif len(inputs['data_content'].strip()) == 0:
            errors.append("字段 data_content 不能为空")

        if not inputs.get('analysis_goal'):
            errors.append("缺少必填字段: analysis_goal（分析目标）")
        elif len(inputs['analysis_goal'].strip()) == 0:
            errors.append("字段 analysis_goal 不能为空")

        # 可选字段校验
        analysis_type = inputs.get('analysis_type', 'comprehensive')
        if analysis_type not in ANALYSIS_TYPES:
            errors.append(
                f"analysis_type 无效，可选值: {', '.join(ANALYSIS_TYPES.keys())}"
            )

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def create_analysis_task(
        self,
        user,
        inputs: Dict[str, Any],
        title: str = None,
        description: str = None
    ) -> AgentTask:
        """
        创建数据分析任务

        Args:
            user: 用户对象
            inputs: 输入参数
            title: 任务标题
            description: 任务描述

        Returns:
            AgentTask: 创建的任务对象
        """
        agent = SmartAgent.objects.filter(category='data_analysis').first()

        if not agent:
            agent = SmartAgent.objects.create(
                name='data_analysis',
                display_name='数据分析智能体',
                description='分析材料数据，发现隐藏模式和趋势，生成柱状图、饼状图、热力图、表格等可视化结果',
                category='data_analysis',
                status='active',
                created_by=user,
                ai_model='dify',
                prompt_template='',
                icon='chart-bar',
                color_theme='green'
            )

        analysis_type_label = ANALYSIS_TYPES.get(
            inputs.get('analysis_type', 'comprehensive'), '综合分析'
        )

        task = AgentTask.objects.create(
            agent=agent,
            title=title or f'数据分析 - {analysis_type_label} - {inputs.get("analysis_goal", "")[:30]}',
            description=description or '基于材料数据进行智能分析，发现隐藏模式、趋势及关联关系，输出可视化图表与表格',
            input_data=inputs,
            created_by=user,
            status=TaskStatus.PENDING
        )

        logger.info(f"创建数据分析任务: {task.id}, 用户: {user.username}")
        return task

    def execute_analysis_streaming(
        self,
        task: AgentTask
    ) -> Generator[Dict[str, Any], None, None]:
        """
        执行数据分析任务（流式响应）

        Args:
            task: 任务对象

        Yields:
            Dict: 流式响应数据，type 可为 message / thought / complete / visualization / error
        """
        execution = None
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = timezone.now()
            task.save(update_fields=['status', 'started_at'])

            execution = AgentExecution.objects.create(
                task=task,
                step_name='材料数据分析',
                step_order=1,
                input_data=task.input_data,
                status='running',
                started_at=timezone.now()
            )

            logger.info(f"开始执行数据分析任务: {task.id}")

            inputs = task.input_data
            user_id = f"user-{task.created_by.id}"
            full_answer = ""
            conversation_id = ""
            message_id = ""

            for event_data in self.dify_service.call_agent_streaming(
                data_content=inputs.get('data_content', ''),
                analysis_type=inputs.get('analysis_type', 'comprehensive'),
                data_description=inputs.get('data_description', ''),
                analysis_goal=inputs.get('analysis_goal', ''),
                user_id=user_id,
                conversation_id=''
            ):
                event_type = event_data.get('event', 'unknown')

                if event_type in ['message', 'agent_message']:
                    answer = event_data.get('answer', '')
                    if answer:
                        full_answer += answer
                    yield {'type': 'message', 'data': event_data}

                elif event_type in ['message_end', 'agent_message_end']:
                    conversation_id = event_data.get('conversation_id', '')
                    message_id = event_data.get('id', '')

                    # 解析可视化数据
                    visualization = self.dify_service.parse_visualization_data(full_answer)

                    output_data = {
                        'answer': full_answer,
                        'conversation_id': conversation_id,
                        'message_id': message_id,
                        'visualization': visualization
                    }

                    task.status = TaskStatus.COMPLETED
                    task.completed_at = timezone.now()
                    task.output_data = output_data
                    task.save(update_fields=['status', 'completed_at', 'output_data'])

                    execution.status = 'completed'
                    execution.completed_at = timezone.now()
                    execution.output_data = output_data
                    execution.save(update_fields=['status', 'completed_at', 'output_data'])

                    task.agent.usage_count += 1
                    task.agent.save(update_fields=['usage_count'])

                    logger.info(f"数据分析任务完成: {task.id}")

                    # 先推送可视化数据事件
                    yield {
                        'type': 'visualization',
                        'data': {
                            'event': 'visualization',
                            'visualization': visualization
                        }
                    }
                    yield {'type': 'complete', 'data': event_data}

                elif event_type == 'agent_thought':
                    yield {'type': 'thought', 'data': event_data}

                elif event_type == 'error':
                    error_msg = event_data.get('message', '未知错误')
                    task.status = TaskStatus.FAILED
                    task.completed_at = timezone.now()
                    task.save(update_fields=['status', 'completed_at'])

                    if execution:
                        execution.status = 'failed'
                        execution.completed_at = timezone.now()
                        execution.logs = f"错误: {error_msg}"
                        execution.save(update_fields=['status', 'completed_at', 'logs'])

                    logger.error(f"数据分析任务失败: {task.id}, 错误: {error_msg}")
                    yield {'type': 'error', 'data': event_data}
                    return

                else:
                    yield {'type': event_type, 'data': event_data}

        except Exception as e:
            error_msg = f"执行数据分析任务时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)

            task.status = TaskStatus.FAILED
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at'])

            if execution:
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"异常: {error_msg}"
                execution.save(update_fields=['status', 'completed_at', 'logs'])

            yield {
                'type': 'error',
                'data': {'event': 'error', 'message': error_msg}
            }

    def execute_analysis_blocking(
        self,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        执行数据分析任务（阻塞响应）

        Args:
            task: 任务对象

        Returns:
            Dict: 执行结果，包含 answer 文字分析和 visualization 可视化数据
        """
        execution = None
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = timezone.now()
            task.save(update_fields=['status', 'started_at'])

            execution = AgentExecution.objects.create(
                task=task,
                step_name='材料数据分析',
                step_order=1,
                input_data=task.input_data,
                status='running',
                started_at=timezone.now()
            )

            logger.info(f"开始执行数据分析任务(阻塞模式): {task.id}")

            inputs = task.input_data
            user_id = f"user-{task.created_by.id}"

            result = self.dify_service.call_agent_blocking(
                data_content=inputs.get('data_content', ''),
                analysis_type=inputs.get('analysis_type', 'comprehensive'),
                data_description=inputs.get('data_description', ''),
                analysis_goal=inputs.get('analysis_goal', ''),
                user_id=user_id,
                conversation_id=''
            )

            if result['success']:
                data = result['data']
                answer = data.get('answer', '')

                # 解析可视化数据
                visualization = self.dify_service.parse_visualization_data(answer)
                data['visualization'] = visualization

                task.status = TaskStatus.COMPLETED
                task.completed_at = timezone.now()
                task.output_data = data
                task.save(update_fields=['status', 'completed_at', 'output_data'])

                execution.status = 'completed'
                execution.completed_at = timezone.now()
                execution.output_data = data
                execution.save(update_fields=['status', 'completed_at', 'output_data'])

                task.agent.usage_count += 1
                task.agent.save(update_fields=['usage_count'])

                logger.info(f"数据分析任务完成: {task.id}")

                return {
                    'success': True,
                    'task_id': task.id,
                    'result': data
                }
            else:
                error_msg = result.get('error', '未知错误')

                task.status = TaskStatus.FAILED
                task.completed_at = timezone.now()
                task.save(update_fields=['status', 'completed_at'])

                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"错误: {error_msg}"
                execution.save(update_fields=['status', 'completed_at', 'logs'])

                logger.error(f"数据分析任务失败: {task.id}, 错误: {error_msg}")

                return {
                    'success': False,
                    'task_id': task.id,
                    'error': error_msg
                }

        except Exception as e:
            error_msg = f"执行数据分析任务时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)

            task.status = TaskStatus.FAILED
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at'])

            if execution:
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"异常: {error_msg}"
                execution.save(update_fields=['status', 'completed_at', 'logs'])

            return {
                'success': False,
                'task_id': task.id,
                'error': error_msg
            }

    def get_task_history(self, user, limit: int = 20) -> list:
        """
        获取用户的数据分析任务历史

        Args:
            user: 用户对象
            limit: 返回数量限制

        Returns:
            list: 任务列表
        """
        agent = SmartAgent.objects.filter(category='data_analysis').first()
        if not agent:
            return []

        tasks = AgentTask.objects.filter(
            agent=agent,
            created_by=user
        ).order_by('-created_at')[:limit]

        return tasks

    def get_supported_analysis_types(self) -> Dict[str, str]:
        """
        返回支持的分析类型

        Returns:
            Dict: {分析类型key: 分析类型中文名}
        """
        return ANALYSIS_TYPES


# 创建单例实例
data_analysis_service = DataAnalysisService()
