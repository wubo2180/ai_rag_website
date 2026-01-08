""""""

工艺优化智能体业务逻辑服务工艺优化智能体业务逻辑服务

处理工艺优化相关的业务逻辑,调用ai_service中的Dify API处理工艺优化相关的业务逻辑，调用ai_service中的Dify API

""""""



from typing import Dict, Any, Generatorfrom typing import Dict, Any, Generator

from django.utils import timezonefrom django.utils import timezone

from apps.ai_service.process_optimization_service import ProcessOptimizationDifyServicefrom ai_rag_website.backend.apps.ai_service.formula_generation_service import process_optimization_dify_service

from .models import SmartAgent, AgentTask, AgentExecution, TaskStatusfrom .models import SmartAgent, AgentTask, AgentExecution, TaskStatus

import loggingimport logging

import jsonimport json



logger = logging.getLogger(__name__)logger = logging.getLogger(__name__)



# 创建全局服务实例

process_optimization_dify_service = ProcessOptimizationDifyService()class ProcessOptimizationService:

    """工艺优化业务服务类"""

    

class ProcessOptimizationBusinessService:    def __init__(self):

    """工艺优化业务服务类"""        """初始化服务"""

            self.dify_service = process_optimization_dify_service

    def __init__(self):    

        """初始化服务"""    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:

        self.dify_service = process_optimization_dify_service        """

            验证输入参数

    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:        

        """        Args:

        验证输入参数            inputs: 输入参数字典

                    

        Args:        Returns:

            inputs: 输入参数字典            Dict: 验证结果 {'valid': bool, 'errors': list}

                    """

        Returns:        errors = []

            Dict: 验证结果 {'valid': bool, 'errors': list}        

        """        required_fields = [

        errors = []            'product_performance',

                    'target_application_scenario',

        required_fields = [            'cost_consideration',

            'optimization_targets',            'environmental_requirements'

            'process_parameters',        ]

            'material_product_data',        

            'environmental_real_time_data',        for field in required_fields:

            'knowledge_constraints',            if not inputs.get(field):

            'historical_data',                errors.append(f"缺少必填字段: {field}")

            'cost_consideration',            elif not isinstance(inputs[field], str):

            'environmental_requirements',                errors.append(f"字段 {field} 必须是字符串类型")

            'expected_performance'            elif len(inputs[field].strip()) == 0:

        ]                errors.append(f"字段 {field} 不能为空")

                

        for field in required_fields:        return {

            if not inputs.get(field):            'valid': len(errors) == 0,

                errors.append(f"缺少必填字段: {field}")            'errors': errors

            elif not isinstance(inputs[field], str):        }

                errors.append(f"字段 {field} 必须是字符串类型")    

            elif len(inputs[field].strip()) == 0:    def create_optimization_task(

                errors.append(f"字段 {field} 不能为空")        self,

                user,

        return {        inputs: Dict[str, Any],

            'valid': len(errors) == 0,        title: str = None,

            'errors': errors        description: str = None

        }    ) -> AgentTask:

            """

    def create_optimization_task(        创建工艺优化任务

        self,        

        user,        Args:

        inputs: Dict[str, Any],            user: 用户对象

        title: str = None,            inputs: 输入参数

        description: str = None            title: 任务标题

    ) -> AgentTask:            description: 任务描述

        """            

        创建工艺优化任务        Returns:

                    AgentTask: 创建的任务对象

        Args:        """

            user: 用户对象        # 获取工艺优化智能体

            inputs: 输入参数        agent = SmartAgent.objects.filter(

            title: 任务标题            category='process_optimization'

            description: 任务描述        ).first()

                    

        Returns:        if not agent:

            AgentTask: 创建的任务对象            # 如果不存在，创建一个默认的

        """            agent = SmartAgent.objects.create(

        # 获取工艺优化智能体                name='process_optimization',

        agent = SmartAgent.objects.filter(                display_name='工艺优化',

            category='process_optimization'                description='优化工艺参数，提升生产效率',

        ).first()                category='process_optimization',

                        status='active',

        if not agent:                created_by=user

            # 如果不存在，创建一个默认的            )

            agent = SmartAgent.objects.create(        

                name='process_optimization',        # 创建任务

                display_name='工艺优化智能体',        task = AgentTask.objects.create(

                description='基于多维数据分析,提供智能化的工艺参数优化建议',            agent=agent,

                category='process_optimization',            title=title or f'工艺优化 - {inputs.get("target_application_scenario", "未命名")[:30]}',

                status='active',            description=description or '根据产品性能、应用场景、成本和环保要求生成材料配方建议',

                created_by=user            input_data=inputs,

            )            created_by=user,

                    status=TaskStatus.PENDING

        # 创建任务        )

        task = AgentTask.objects.create(        

            agent=agent,        logger.info(f"创建工艺优化任务: {task.id}, 用户: {user.username}")

            title=title or f'工艺优化 - {inputs.get("optimization_targets", "未命名")[:30]}',        

            description=description or '基于优化目标、工艺参数、材料数据等多维度信息,提供工艺优化建议',        return task

            input_data=inputs,    

            created_by=user,    def execute_optimization_streaming(

            status=TaskStatus.PENDING        self,

        )        task: AgentTask

            ) -> Generator[Dict[str, Any], None, None]:

        logger.info(f"创建工艺优化任务: {task.id}, 用户: {user.username}")        """

                执行工艺优化任务（流式响应）

        return task        

            Args:

    def execute_optimization_streaming(            task: 任务对象

        self,            

        task: AgentTask        Yields:

    ) -> Generator[Dict[str, Any], None, None]:            Dict: 流式响应数据

        """        """

        执行工艺优化任务（流式响应）        try:

                    # 更新任务状态

        Args:            task.status = TaskStatus.RUNNING

            task: 任务对象            task.started_at = timezone.now()

                        task.save(update_fields=['status', 'started_at'])

        Yields:            

            Dict: 流式响应数据            # 创建执行记录

        """            execution = AgentExecution.objects.create(

        try:                task=task,

            # 更新任务状态                status='running',

            task.status = TaskStatus.RUNNING                started_at=timezone.now()

            task.started_at = timezone.now()            )

            task.save(update_fields=['status', 'started_at'])            

                        logger.info(f"开始执行工艺优化任务: {task.id}")

            # 创建执行记录            

            execution = AgentExecution.objects.create(            # 提取输入参数

                task=task,            inputs = task.input_data

                step_name='工艺优化',            user_id = f"user-{task.created_by.id}"

                step_order=1,            

                input_data=task.input_data,            # 收集完整答案和元数据

                status='running',            full_answer = ""

                started_at=timezone.now()            conversation_id = ""

            )            message_id = ""

                        

            logger.info(f"开始执行工艺优化任务: {task.id}")            # 调用Dify服务（流式）

                        for event_data in self.dify_service.call_agent_streaming(

            # 提取输入参数                product_performance=inputs['product_performance'],

            inputs = task.input_data                target_application_scenario=inputs['target_application_scenario'],

            user_id = f"user-{task.created_by.id}"                cost_consideration=inputs['cost_consideration'],

                            environmental_requirements=inputs['environmental_requirements'],

            # 收集完整答案和元数据                user_id=user_id,

            full_answer = ""                conversation_id=task.metadata.get('conversation_id', '') if task.metadata else ''

            conversation_id = ""            ):

            message_id = ""                event_type = event_data.get('event', 'unknown')

                            

            # 调用Dify服务（流式）                # 处理不同类型的事件

            for event_data in self.dify_service.call_agent_streaming(                if event_type in ['message', 'agent_message']:

                optimization_targets=inputs['optimization_targets'],                    # 消息片段

                process_parameters=inputs['process_parameters'],                    answer = event_data.get('answer', '')

                material_product_data=inputs['material_product_data'],                    if answer:

                environmental_real_time_data=inputs['environmental_real_time_data'],                        full_answer += answer

                knowledge_constraints=inputs['knowledge_constraints'],                    

                historical_data=inputs['historical_data'],                    # 返回给前端

                cost_consideration=inputs['cost_consideration'],                    yield {

                environmental_requirements=inputs['environmental_requirements'],                        'type': 'message',

                expected_performance=inputs['expected_performance'],                        'data': event_data

                user_id=user_id,                    }

                conversation_id=''  # 每次都是新对话                

            ):                elif event_type in ['message_end', 'agent_message_end']:

                # 处理不同事件类型                    # 消息结束

                event = event_data.get('event', 'unknown')                    conversation_id = event_data.get('conversation_id', '')

                                    message_id = event_data.get('id', '')

                if event == 'message' or event == 'agent_message':                    

                    # 累积答案                    # 更新任务

                    if 'answer' in event_data:                    task.status = TaskStatus.COMPLETED

                        full_answer += event_data['answer']                    task.completed_at = timezone.now()

                                        task.result = {

                    # 向前端转发                        'answer': full_answer,

                    yield event_data                        'conversation_id': conversation_id,

                                            'message_id': message_id

                elif event == 'message_end' or event == 'agent_message_end':                    }

                    # 保存对话ID和消息ID                    task.metadata = task.metadata or {}

                    conversation_id = event_data.get('conversation_id', '')                    task.metadata['conversation_id'] = conversation_id

                    message_id = event_data.get('id', '')                    task.save(update_fields=['status', 'completed_at', 'result', 'metadata'])

                                        

                    yield event_data                    # 更新执行记录

                                        execution.status = 'completed'

                elif event == 'agent_thought':                    execution.completed_at = timezone.now()

                    # Agent思考过程                    execution.result = task.result

                    logger.debug(f"Agent思考: {event_data.get('thought', '')}")                    execution.save(update_fields=['status', 'completed_at', 'result'])

                    yield event_data                    

                                        # 更新智能体统计

                elif event == 'error':                    task.agent.usage_count += 1

                    # 错误处理                    task.agent.save(update_fields=['usage_count'])

                    error_msg = event_data.get('message', '未知错误')                    

                    logger.error(f"工艺优化执行错误: {error_msg}")                    logger.info(f"工艺优化任务完成: {task.id}")

                                        

                    # 更新执行记录                    # 返回完成事件

                    execution.status = 'failed'                    yield {

                    execution.completed_at = timezone.now()                        'type': 'complete',

                    execution.logs = f"错误: {error_msg}"                        'data': event_data

                    execution.save(update_fields=['status', 'completed_at', 'logs'])                    }

                                    

                    # 更新任务状态                elif event_type == 'agent_thought':

                    task.status = TaskStatus.FAILED                    # Agent思考过程

                    task.completed_at = timezone.now()                    yield {

                    task.save(update_fields=['status', 'completed_at'])                        'type': 'thought',

                                            'data': event_data

                    yield event_data                    }

                    return                

                else:                elif event_type == 'error':

                    # 其他事件类型                    # 错误事件

                    yield event_data                    error_msg = event_data.get('message', '未知错误')

                                

            # 执行完成，更新记录                    # 更新任务状态

            execution.status = 'completed'                    task.status = TaskStatus.FAILED

            execution.completed_at = timezone.now()                    task.completed_at = timezone.now()

            execution.output_data = {                    task.error_message = error_msg

                'answer': full_answer,                    task.save(update_fields=['status', 'completed_at', 'error_message'])

                'conversation_id': conversation_id,                    

                'message_id': message_id                    # 更新执行记录

            }                    execution.status = 'failed'

            execution.save(update_fields=['status', 'completed_at', 'output_data'])                    execution.completed_at = timezone.now()

                                execution.error_message = error_msg

            # 更新任务状态                    execution.save(update_fields=['status', 'completed_at', 'error_message'])

            task.status = TaskStatus.COMPLETED                    

            task.completed_at = timezone.now()                    logger.error(f"工艺优化任务失败: {task.id}, 错误: {error_msg}")

            task.output_data = {                    

                'answer': full_answer,                    yield {

                'conversation_id': conversation_id,                        'type': 'error',

                'message_id': message_id                        'data': event_data

            }                    }

            task.save(update_fields=['status', 'completed_at', 'output_data'])                    return

                            

            logger.info(f"工艺优化任务执行成功: {task.id}")                else:

                                # 其他事件类型

            # 发送完成事件                    yield {

            yield {                        'type': event_type,

                'event': 'done',                        'data': event_data

                'task_id': str(task.id),                    }

                'conversation_id': conversation_id        

            }        except Exception as e:

                        error_msg = f"执行工艺优化任务时出错: {str(e)}"

        except Exception as e:            logger.error(error_msg, exc_info=True)

            error_msg = str(e)            

            logger.exception(f"工艺优化任务执行异常: {task.id}")            # 更新任务状态

                        task.status = TaskStatus.FAILED

            # 更新执行记录            task.completed_at = timezone.now()

            if execution:            task.error_message = error_msg

                execution.status = 'failed'            task.save(update_fields=['status', 'completed_at', 'error_message'])

                execution.completed_at = timezone.now()            

                execution.logs = f"异常: {error_msg}"            # 更新执行记录

                execution.save(update_fields=['status', 'completed_at', 'logs'])            if 'execution' in locals():

                            execution.status = 'failed'

            # 更新任务状态                execution.completed_at = timezone.now()

            task.status = TaskStatus.FAILED                execution.error_message = error_msg

            task.completed_at = timezone.now()                execution.save(update_fields=['status', 'completed_at', 'error_message'])

            task.save(update_fields=['status', 'completed_at'])            

                        yield {

            yield {                'type': 'error',

                'event': 'error',                'data': {

                'message': f'执行失败: {error_msg}'                    'event': 'error',

            }                    'message': error_msg

                    }

    def execute_optimization_blocking(            }

        self,    

        task: AgentTask    def execute_optimization_blocking(

    ) -> Dict[str, Any]:        self,

        """        task: AgentTask

        执行工艺优化任务（阻塞式响应）    ) -> Dict[str, Any]:

                """

        Args:        执行工艺优化任务（阻塞响应）

            task: 任务对象        

                    Args:

        Returns:            task: 任务对象

            Dict: 执行结果            

        """        Returns:

        try:            Dict: 执行结果

            # 更新任务状态        """

            task.status = TaskStatus.RUNNING        try:

            task.started_at = timezone.now()            # 更新任务状态

            task.save(update_fields=['status', 'started_at'])            task.status = TaskStatus.RUNNING

                        task.started_at = timezone.now()

            # 创建执行记录            task.save(update_fields=['status', 'started_at'])

            execution = AgentExecution.objects.create(            

                task=task,            # 创建执行记录

                step_name='工艺优化',            execution = AgentExecution.objects.create(

                step_order=1,                task=task,

                input_data=task.input_data,                status='running',

                status='running',                started_at=timezone.now()

                started_at=timezone.now()            )

            )            

                        logger.info(f"开始执行工艺优化任务(阻塞模式): {task.id}")

            logger.info(f"开始执行工艺优化任务(阻塞模式): {task.id}")            

                        # 提取输入参数

            # 提取输入参数            inputs = task.input_data

            inputs = task.input_data            user_id = f"user-{task.created_by.id}"

            user_id = f"user-{task.created_by.id}"            

                        # 调用Dify服务（阻塞）

            # 调用Dify服务（阻塞式）            result = self.dify_service.call_agent_blocking(

            result = self.dify_service.call_agent_blocking(                product_performance=inputs['product_performance'],

                optimization_targets=inputs['optimization_targets'],                target_application_scenario=inputs['target_application_scenario'],

                process_parameters=inputs['process_parameters'],                cost_consideration=inputs['cost_consideration'],

                material_product_data=inputs['material_product_data'],                environmental_requirements=inputs['environmental_requirements'],

                environmental_real_time_data=inputs['environmental_real_time_data'],                user_id=user_id,

                knowledge_constraints=inputs['knowledge_constraints'],                conversation_id=task.metadata.get('conversation_id', '') if task.metadata else ''

                historical_data=inputs['historical_data'],            )

                cost_consideration=inputs['cost_consideration'],            

                environmental_requirements=inputs['environmental_requirements'],            if result['success']:

                expected_performance=inputs['expected_performance'],                # 成功

                user_id=user_id,                data = result['data']

                conversation_id=''  # 每次都是新对话                

            )                task.status = TaskStatus.COMPLETED

                            task.completed_at = timezone.now()

            # 检查是否有错误                task.result = data

            if result.get('error'):                task.save(update_fields=['status', 'completed_at', 'result'])

                error_msg = result.get('message', '未知错误')                

                logger.error(f"工艺优化执行错误: {error_msg}")                execution.status = 'completed'

                                execution.completed_at = timezone.now()

                # 更新执行记录                execution.result = data

                execution.status = 'failed'                execution.save(update_fields=['status', 'completed_at', 'result'])

                execution.completed_at = timezone.now()                

                execution.output_data = result                # 更新智能体统计

                execution.logs = f"错误: {error_msg}"                task.agent.usage_count += 1

                execution.save(update_fields=['status', 'completed_at', 'output_data', 'logs'])                task.agent.save(update_fields=['usage_count'])

                                

                # 更新任务状态                logger.info(f"工艺优化任务完成: {task.id}")

                task.status = TaskStatus.FAILED                

                task.completed_at = timezone.now()                return {

                task.save(update_fields=['status', 'completed_at'])                    'success': True,

                                    'task_id': task.id,

                return result                    'result': data

                            }

            # 执行成功            else:

            execution.status = 'completed'                # 失败

            execution.completed_at = timezone.now()                error_msg = result.get('error', '未知错误')

            execution.output_data = result                

            execution.save(update_fields=['status', 'completed_at', 'output_data'])                task.status = TaskStatus.FAILED

                            task.completed_at = timezone.now()

            # 更新任务状态                task.error_message = error_msg

            task.status = TaskStatus.COMPLETED                task.save(update_fields=['status', 'completed_at', 'error_message'])

            task.completed_at = timezone.now()                

            task.output_data = result                execution.status = 'failed'

            task.save(update_fields=['status', 'completed_at', 'output_data'])                execution.completed_at = timezone.now()

                            execution.error_message = error_msg

            logger.info(f"工艺优化任务执行成功(阻塞模式): {task.id}")                execution.save(update_fields=['status', 'completed_at', 'error_message'])

                            

            return result                logger.error(f"工艺优化任务失败: {task.id}, 错误: {error_msg}")

                            

        except Exception as e:                return {

            error_msg = str(e)                    'success': False,

            logger.exception(f"工艺优化任务执行异常: {task.id}")                    'task_id': task.id,

                                'error': error_msg

            # 更新执行记录                }

            if execution:        

                execution.status = 'failed'        except Exception as e:

                execution.completed_at = timezone.now()            error_msg = f"执行工艺优化任务时出错: {str(e)}"

                execution.logs = f"异常: {error_msg}"            logger.error(error_msg, exc_info=True)

                execution.save(update_fields=['status', 'completed_at', 'logs'])            

                        # 更新任务状态

            # 更新任务状态            task.status = TaskStatus.FAILED

            task.status = TaskStatus.FAILED            task.completed_at = timezone.now()

            task.completed_at = timezone.now()            task.error_message = error_msg

            task.save(update_fields=['status', 'completed_at'])            task.save(update_fields=['status', 'completed_at', 'error_message'])

                        

            return {            # 更新执行记录

                'error': True,            if 'execution' in locals():

                'message': f'执行失败: {error_msg}'                execution.status = 'failed'

            }                execution.completed_at = timezone.now()

                execution.error_message = error_msg

                execution.save(update_fields=['status', 'completed_at', 'error_message'])

# 创建全局服务实例            

process_optimization_business_service = ProcessOptimizationBusinessService()            return {

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
        
        return tasks


# 创建单例实例
process_optimization_service = ProcessOptimizationService()
