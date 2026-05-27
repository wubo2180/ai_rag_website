"""
工艺优化智能体业务逻辑服务
处理工艺优化相关的业务逻辑，调用ai_service中的Dify API
"""

from typing import Dict, Any, Generator, Optional
from django.utils import timezone
from apps.ai_service.formula_generation_service import process_optimization_dify_service
from .models import SmartAgent, AgentTask, AgentExecution, TaskStatus
import logging
import json

logger = logging.getLogger(__name__)


class ProcessOptimizationService:
    """工艺优化业务服务类"""
    
    def __init__(self):
        """初始化服务"""
        self.dify_service = process_optimization_dify_service
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证输入参数
        
        Args:
            inputs: 输入参数字典
            
        Returns:
            Dict: 验证结果 {'valid': bool, 'errors': list}
        """
        errors = []
        
        required_formula_fields = [
            'product_performance_requirements',
            'target_application_scenario',
            'cost_consideration',
            'environmental_requirements'
        ]
        required_new_fields = [
            'optimization_targets',
            'process_parameters',
            'material_product_data',
            'knowledge_constraints',
            'cost_consideration',
            'environmental_requirements'
        ]
        required_legacy_fields = [
            'product_performance',
            'target_application_scenario',
            'cost_consideration',
            'environmental_requirements'
        ]

        has_formula_payload = bool(inputs.get('product_performance_requirements'))
        has_new_payload = any(bool(inputs.get(field)) for field in required_new_fields)
        if has_formula_payload:
            required_fields = required_formula_fields
        elif has_new_payload:
            required_fields = required_new_fields
        else:
            required_fields = required_legacy_fields
        
        for field in required_fields:
            if not inputs.get(field):
                errors.append(f"缺少必填字段: {field}")
            elif not isinstance(inputs[field], str):
                errors.append(f"字段 {field} 必须是字符串类型")
            elif len(inputs[field].strip()) == 0:
                errors.append(f"字段 {field} 不能为空")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def create_optimization_task(
        self,
        user,
        inputs: Dict[str, Any],
        agent_category: str = 'process_optimization',
        title: Optional[str] = None,
        description: Optional[str] = None
    ) -> AgentTask:
        """
        创建工艺优化任务
        
        Args:
            user: 用户对象
            inputs: 输入参数
            title: 任务标题
            description: 任务描述
            
        Returns:
            AgentTask: 创建的任务对象
        """
        # 获取工艺优化智能体
        agent = SmartAgent.objects.filter(
            category=agent_category
        ).first()
        
        if not agent:
            # 如果不存在，创建一个默认的
            agent = SmartAgent.objects.create(
                name=agent_category,
                display_name='配方生成' if agent_category == 'formula_generation' else '工艺优化',
                description='根据需求生成材料配方建议' if agent_category == 'formula_generation' else '优化工艺参数，提升生产效率',
                category=agent_category,
                status='active',
                created_by=user
            )
        
        # 创建任务
        task = AgentTask.objects.create(
            agent=agent,
            title=title or f'工艺优化 - {(inputs.get("product_performance_requirements") or inputs.get("optimization_targets") or inputs.get("product_performance") or "未命名")[:30]}',
            description=description or '根据优化目标、工艺参数与约束条件生成可执行工艺优化建议',
            input_data=inputs,
            created_by=user,
            status=TaskStatus.PENDING
        )
        
        logger.info(f"创建工艺优化任务: {task.id}, 用户: {user.username}")
        
        return task
    
    def execute_optimization_streaming(
        self,
        task: AgentTask
    ) -> Generator[Dict[str, Any], None, None]:
        """
        执行工艺优化任务（流式响应）
        
        Args:
            task: 任务对象
            
        Yields:
            Dict: 流式响应数据
        """
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = timezone.now()
            task.save(update_fields=['status', 'started_at'])
            
            # 创建执行记录
            execution = AgentExecution.objects.create(
                task=task,
                step_name='工艺优化',
                step_order=1,
                input_data=task.input_data,
                status='running',
                started_at=timezone.now()
            )
            
            logger.info(f"开始执行工艺优化任务: {task.id}")
            
            # 提取输入参数
            inputs = task.input_data
            user_id = f"user-{getattr(task.created_by, 'pk', 'anonymous')}"
            
            # 收集完整答案和元数据
            full_answer = ""
            conversation_id = ""
            message_id = ""
            
            # 调用Dify服务（流式）
            for event_data in self.dify_service.call_agent_streaming(
                inputs=inputs,
                user_id=user_id,
                conversation_id=''  # 每次都是新对话
            ):
                event_type = event_data.get('event', 'unknown')
                
                # 处理不同类型的事件
                if event_type in ['message', 'agent_message']:
                    # 消息片段
                    answer = event_data.get('answer', '')
                    if answer:
                        full_answer += answer
                    
                    # 返回给前端
                    yield {
                        'type': 'message',
                        'data': event_data
                    }
                
                elif event_type in ['message_end', 'agent_message_end']:
                    # 消息结束
                    conversation_id = event_data.get('conversation_id', '')
                    message_id = event_data.get('id', '')
                    
                    # 更新任务
                    task.status = TaskStatus.COMPLETED
                    task.completed_at = timezone.now()
                    task.output_data = {
                        'answer': full_answer,
                        'conversation_id': conversation_id,
                        'message_id': message_id
                    }
                    task.save(update_fields=['status', 'completed_at', 'output_data'])
                    
                    # 更新执行记录
                    execution.status = 'completed'
                    execution.completed_at = timezone.now()
                    execution.output_data = task.output_data
                    execution.save(update_fields=['status', 'completed_at', 'output_data'])
                    
                    # 更新智能体统计
                    task.agent.usage_count += 1
                    task.agent.save(update_fields=['usage_count'])
                    
                    logger.info(f"工艺优化任务完成: {task.id}")
                    
                    # 返回完成事件
                    yield {
                        'type': 'complete',
                        'data': event_data
                    }
                
                elif event_type == 'agent_thought':
                    # Agent思考过程
                    yield {
                        'type': 'thought',
                        'data': event_data
                    }
                
                elif event_type == 'error':
                    # 错误事件
                    error_msg = event_data.get('message', '未知错误')
                    
                    # 更新任务状态
                    task.status = TaskStatus.FAILED
                    task.completed_at = timezone.now()
                    task.save(update_fields=['status', 'completed_at'])
                    
                    # 更新执行记录
                    execution.status = 'failed'
                    execution.completed_at = timezone.now()
                    execution.logs = f"错误: {error_msg}"
                    execution.save(update_fields=['status', 'completed_at', 'logs'])
                    
                    logger.error(f"工艺优化任务失败: {task.id}, 错误: {error_msg}")
                    
                    yield {
                        'type': 'error',
                        'data': event_data
                    }
                    return
                
                else:
                    # 其他事件类型
                    yield {
                        'type': event_type,
                        'data': event_data
                    }
        
        except Exception as e:
            error_msg = f"执行工艺优化任务时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 更新任务状态
            task.status = TaskStatus.FAILED
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at'])
            
            # 更新执行记录
            if 'execution' in locals():
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"异常: {error_msg}"
                execution.save(update_fields=['status', 'completed_at', 'logs'])
            
            yield {
                'type': 'error',
                'data': {
                    'event': 'error',
                    'message': error_msg
                }
            }
    
    def execute_optimization_blocking(
        self,
        task: AgentTask
    ) -> Dict[str, Any]:
        """
        执行工艺优化任务（阻塞响应）
        
        Args:
            task: 任务对象
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 更新任务状态
            task.status = TaskStatus.RUNNING
            task.started_at = timezone.now()
            task.save(update_fields=['status', 'started_at'])
            
            # 创建执行记录
            execution = AgentExecution.objects.create(
                task=task,
                step_name='工艺优化',
                step_order=1,
                input_data=task.input_data,
                status='running',
                started_at=timezone.now()
            )
            
            logger.info(f"开始执行工艺优化任务(阻塞模式): {task.id}")
            
            # 提取输入参数
            inputs = task.input_data
            user_id = f"user-{getattr(task.created_by, 'pk', 'anonymous')}"
            
            # 调用Dify服务（阻塞）
            result = self.dify_service.call_agent_blocking(
                inputs=inputs,
                user_id=user_id,
                conversation_id=''  # 每次都是新对话
            )
            
            if result['success']:
                # 成功
                data = result['data']
                
                task.status = TaskStatus.COMPLETED
                task.completed_at = timezone.now()
                task.output_data = data
                task.save(update_fields=['status', 'completed_at', 'output_data'])
                
                execution.status = 'completed'
                execution.completed_at = timezone.now()
                execution.output_data = data
                execution.save(update_fields=['status', 'completed_at', 'output_data'])
                
                # 更新智能体统计
                task.agent.usage_count += 1
                task.agent.save(update_fields=['usage_count'])
                
                logger.info(f"工艺优化任务完成: {task.id}")
                
                return {
                    'success': True,
                    'task_id': task.id,
                    'result': data
                }
            else:
                # 失败
                error_msg = result.get('error', '未知错误')
                
                task.status = TaskStatus.FAILED
                task.completed_at = timezone.now()
                task.save(update_fields=['status', 'completed_at'])
                
                execution.status = 'failed'
                execution.completed_at = timezone.now()
                execution.logs = f"错误: {error_msg}"
                execution.save(update_fields=['status', 'completed_at', 'logs'])
                
                logger.error(f"工艺优化任务失败: {task.id}, 错误: {error_msg}")
                
                return {
                    'success': False,
                    'task_id': task.id,
                    'error': error_msg
                }
        
        except Exception as e:
            error_msg = f"执行工艺优化任务时出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            # 更新任务状态
            task.status = TaskStatus.FAILED
            task.completed_at = timezone.now()
            task.save(update_fields=['status', 'completed_at'])
            
            # 更新执行记录
            if 'execution' in locals():
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
        获取用户的工艺优化任务历史
        
        Args:
            user: 用户对象
            limit: 返回数量限制
            
        Returns:
            list: 任务列表
        """
        agent = SmartAgent.objects.filter(category='process_optimization').first()
        
        if not agent:
            return []
        
        tasks = AgentTask.objects.filter(
            agent=agent,
            created_by=user
        ).order_by('-created_at')[:limit]

        return list(tasks)


# 创建单例实例
process_optimization_service = ProcessOptimizationService()
