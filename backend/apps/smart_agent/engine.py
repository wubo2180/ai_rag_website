"""
智能体执行引擎
负责执行智能体任务的核心逻辑
"""
import time
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from django.utils import timezone
from django.db import transaction

from .models import SmartAgent, AgentTask, AgentExecution, TaskStatus


logger = logging.getLogger(__name__)


class AgentExecutor:
    """智能体执行器"""
    
    def __init__(self, agent: SmartAgent):
        self.agent = agent
        self.logger = logger.getChild(f'agent.{agent.name}')
    
    def execute_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行智能体任务
        
        Args:
            task: 要执行的任务
            
        Returns:
            执行结果
        """
        self.logger.info(f"开始执行任务: {task.title}")
        
        try:
            # 更新任务状态为执行中
            with transaction.atomic():
                task.status = TaskStatus.RUNNING
                task.started_at = timezone.now()
                task.progress = 0
                task.save(update_fields=['status', 'started_at', 'progress'])
            
            # 根据智能体类型执行不同的处理逻辑
            result = self._execute_by_category(task)
            
            # 更新任务状态为完成
            with transaction.atomic():
                task.status = TaskStatus.COMPLETED
                task.completed_at = timezone.now()
                task.progress = 100
                task.output_data = result
                
                # 计算执行时间
                if task.started_at:
                    task.execution_time = (task.completed_at - task.started_at).total_seconds()
                
                task.save(update_fields=[
                    'status', 'completed_at', 'progress', 
                    'output_data', 'execution_time'
                ])
            
            # 更新智能体统计信息
            self.agent.update_statistics()
            
            self.logger.info(f"任务执行完成: {task.title}")
            return result
            
        except Exception as e:
            self.logger.error(f"任务执行失败: {task.title}, 错误: {str(e)}")
            
            # 更新任务状态为失败
            with transaction.atomic():
                task.status = TaskStatus.FAILED
                task.completed_at = timezone.now()
                task.error_message = str(e)
                task.save(update_fields=[
                    'status', 'completed_at', 'error_message'
                ])
            
            raise
    
    def _execute_by_category(self, task: AgentTask) -> Dict[str, Any]:
        """根据智能体分类执行不同逻辑"""
        
        category = self.agent.category
        input_data = task.input_data
        
        if category == 'data_analysis':
            return self._execute_data_analysis(task, input_data)
        elif category == 'property_prediction':
            return self._execute_property_prediction(task, input_data)
        elif category == 'process_optimization':
            return self._execute_process_optimization(task, input_data)
        elif category == 'knowledge_extraction':
            return self._execute_knowledge_extraction(task, input_data)
        elif category == 'decision_support':
            return self._execute_decision_support(task, input_data)
        else:
            return self._execute_generic_task(task, input_data)
    
    def _execute_data_analysis(self, task: AgentTask, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行数据分析任务"""
        self._log_execution_step(task, "数据预处理", 1, "开始数据清洗和预处理")
        self._update_progress(task, 20)
        time.sleep(1)  # 模拟处理时间
        
        self._log_execution_step(task, "特征提取", 2, "提取关键特征")
        self._update_progress(task, 40)
        time.sleep(1)
        
        self._log_execution_step(task, "关联分析", 3, "分析成分-工艺-结构-性能关联关系")
        self._update_progress(task, 60)
        time.sleep(1)
        
        self._log_execution_step(task, "结果生成", 4, "生成分析结果和可视化")
        self._update_progress(task, 80)
        time.sleep(1)
        
        return {
            "analysis_type": "四级关联数据链分析",
            "composition_analysis": {
                "main_elements": ["Fe", "C", "Mn", "Si"],
                "trace_elements": ["P", "S", "Cu"],
                "phase_composition": "铁素体+珠光体"
            },
            "process_parameters": {
                "temperature": "1200°C",
                "pressure": "150MPa",
                "cooling_rate": "5°C/min",
                "duration": "120min"
            },
            "structure_features": {
                "grain_size": "15-25μm",
                "hardness": "HRC 45-50",
                "microstructure": "细化的珠光体组织"
            },
            "performance_properties": {
                "tensile_strength": "850MPa",
                "yield_strength": "650MPa",
                "elongation": "18%",
                "impact_toughness": "65J"
            },
            "correlation_matrix": [
                ["成分", "工艺", 0.85],
                ["工艺", "结构", 0.92],
                ["结构", "性能", 0.88],
                ["成分", "性能", 0.76]
            ],
            "recommendations": [
                "优化碳含量至0.45-0.50%可提高强度",
                "控制冷却速度可改善韧性",
                "添加微量Nb可细化晶粒"
            ]
        }
    
    def _execute_property_prediction(self, task: AgentTask, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行性质预测任务"""
        self._log_execution_step(task, "模型加载", 1, "加载预训练的性质预测模型")
        self._update_progress(task, 25)
        time.sleep(0.5)
        
        self._log_execution_step(task, "特征工程", 2, "处理输入特征")
        self._update_progress(task, 50)
        time.sleep(1)
        
        self._log_execution_step(task, "性质预测", 3, "运行预测算法")
        self._update_progress(task, 75)
        time.sleep(1.5)
        
        return {
            "prediction_type": "材料性质预测",
            "mechanical_properties": {
                "tensile_strength": {
                    "value": 820,
                    "unit": "MPa",
                    "confidence_interval": [780, 860],
                    "confidence_level": 0.95
                },
                "yield_strength": {
                    "value": 620,
                    "unit": "MPa",
                    "confidence_interval": [590, 650],
                    "confidence_level": 0.95
                },
                "hardness": {
                    "value": 248,
                    "unit": "HB",
                    "confidence_interval": [235, 261],
                    "confidence_level": 0.95
                }
            },
            "electrical_properties": {
                "conductivity": {
                    "value": 1.2e7,
                    "unit": "S/m",
                    "confidence_interval": [1.1e7, 1.3e7],
                    "confidence_level": 0.90
                }
            },
            "thermal_properties": {
                "thermal_conductivity": {
                    "value": 45.2,
                    "unit": "W/m·K",
                    "confidence_interval": [42.1, 48.3],
                    "confidence_level": 0.95
                }
            },
            "optimization_suggestions": [
                "增加Mn含量可提高强度约8%",
                "控制Si含量在0.3-0.5%范围内优化韧性",
                "热处理温度建议在850-900°C"
            ]
        }
    
    def _execute_process_optimization(self, task: AgentTask, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工艺优化任务"""
        self._log_execution_step(task, "工艺分析", 1, "分析当前工艺参数")
        self._update_progress(task, 30)
        time.sleep(1)
        
        self._log_execution_step(task, "优化计算", 2, "运行优化算法")
        self._update_progress(task, 70)
        time.sleep(2)
        
        return {
            "optimization_type": "生产工艺优化",
            "current_parameters": input_data.get("current_params", {}),
            "optimized_parameters": {
                "temperature": {
                    "current": 1180,
                    "optimized": 1220,
                    "unit": "°C",
                    "improvement": "+3.4%"
                },
                "pressure": {
                    "current": 140,
                    "optimized": 155,
                    "unit": "MPa",
                    "improvement": "+10.7%"
                },
                "duration": {
                    "current": 135,
                    "optimized": 118,
                    "unit": "min",
                    "improvement": "-12.6%"
                }
            },
            "expected_improvements": {
                "quality_increase": "15.2%",
                "cost_reduction": "8.7%",
                "energy_savings": "12.3%",
                "production_efficiency": "+18.5%"
            },
            "implementation_plan": [
                "第1阶段：调整温度控制系统（1-2周）",
                "第2阶段：优化压力控制（2-3周）",
                "第3阶段：缩短处理时间（1周）",
                "第4阶段：整体验证和微调（2周）"
            ],
            "risk_assessment": {
                "technical_risk": "低",
                "cost_risk": "中",
                "schedule_risk": "低",
                "quality_risk": "低"
            }
        }
    
    def _execute_knowledge_extraction(self, task: AgentTask, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行知识抽取任务"""
        self._log_execution_step(task, "文本解析", 1, "解析文献内容")
        self._update_progress(task, 25)
        time.sleep(1)
        
        self._log_execution_step(task, "实体识别", 2, "识别材料实体")
        self._update_progress(task, 50)
        time.sleep(1)
        
        self._log_execution_step(task, "关系抽取", 3, "抽取实体关系")
        self._update_progress(task, 75)
        time.sleep(1)
        
        return {
            "extraction_type": "科技文献知识抽取",
            "extracted_materials": [
                {
                    "name": "316L不锈钢",
                    "composition": "Fe-18Cr-12Ni-2.5Mo",
                    "applications": ["医疗器械", "化工设备"],
                    "confidence": 0.92
                },
                {
                    "name": "碳纤维复合材料",
                    "composition": "CFRP",
                    "applications": ["航空航天", "汽车工业"],
                    "confidence": 0.88
                }
            ],
            "process_information": [
                {
                    "process": "激光焊接",
                    "parameters": {"功率": "2.5kW", "速度": "1.2m/min"},
                    "materials": ["316L不锈钢"],
                    "confidence": 0.85
                }
            ],
            "performance_data": [
                {
                    "material": "316L不锈钢",
                    "property": "抗拉强度",
                    "value": "580MPa",
                    "test_condition": "室温",
                    "confidence": 0.90
                }
            ],
            "key_findings": [
                "激光焊接功率对焊缝质量有显著影响",
                "Mo含量提高可增强耐腐蚀性",
                "热处理温度控制在1050-1100°C最佳"
            ]
        }
    
    def _execute_decision_support(self, task: AgentTask, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行决策支持任务"""
        self._log_execution_step(task, "需求分析", 1, "分析应用需求")
        self._update_progress(task, 20)
        time.sleep(0.5)
        
        self._log_execution_step(task, "材料筛选", 2, "筛选候选材料")
        self._update_progress(task, 45)
        time.sleep(1)
        
        self._log_execution_step(task, "综合评估", 3, "多维度评估分析")
        self._update_progress(task, 70)
        time.sleep(1)
        
        self._log_execution_step(task, "方案生成", 4, "生成推荐方案")
        self._update_progress(task, 90)
        time.sleep(0.5)
        
        return {
            "decision_type": "材料选择决策支持",
            "application_requirements": input_data.get("requirements", {}),
            "recommended_materials": [
                {
                    "rank": 1,
                    "material": "Ti-6Al-4V钛合金",
                    "match_score": 0.92,
                    "advantages": ["高强度", "耐腐蚀", "生物相容性好"],
                    "disadvantages": ["成本较高", "加工难度大"],
                    "cost_index": 8.5,
                    "performance_index": 9.2,
                    "availability_index": 7.8
                },
                {
                    "rank": 2,
                    "material": "316L不锈钢",
                    "match_score": 0.87,
                    "advantages": ["成本适中", "易加工", "耐腐蚀"],
                    "disadvantages": ["强度相对较低"],
                    "cost_index": 7.2,
                    "performance_index": 8.5,
                    "availability_index": 9.0
                },
                {
                    "rank": 3,
                    "material": "Al-7075铝合金",
                    "match_score": 0.78,
                    "advantages": ["重量轻", "成本低", "易加工"],
                    "disadvantages": ["耐腐蚀性一般"],
                    "cost_index": 6.8,
                    "performance_index": 7.5,
                    "availability_index": 8.5
                }
            ],
            "comparison_matrix": {
                "criteria": ["强度", "耐腐蚀", "成本", "加工性", "可获得性"],
                "weights": [0.3, 0.25, 0.2, 0.15, 0.1],
                "scores": {
                    "Ti-6Al-4V": [9.5, 9.0, 4.0, 3.5, 7.0],
                    "316L不锈钢": [7.5, 8.5, 7.0, 8.5, 9.0],
                    "Al-7075": [8.0, 5.5, 8.5, 9.0, 8.5]
                }
            },
            "implementation_recommendations": [
                "优先考虑Ti-6Al-4V，适用于高性能应用",
                "316L不锈钢为性价比最佳选择",
                "建议进行小批量试验验证",
                "关注供应链稳定性"
            ],
            "risk_factors": [
                "钛合金价格波动风险",
                "加工设备要求较高",
                "质量控制标准严格"
            ]
        }
    
    def _execute_generic_task(self, task: AgentTask, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行通用任务"""
        self._log_execution_step(task, "任务处理", 1, "处理通用任务")
        self._update_progress(task, 50)
        time.sleep(1)
        
        return {
            "task_type": "通用任务",
            "input_received": input_data,
            "processing_time": timezone.now().isoformat(),
            "status": "completed",
            "message": f"智能体 {self.agent.display_name} 已成功处理任务"
        }
    
    def _log_execution_step(self, task: AgentTask, step_name: str, step_order: int, logs: str):
        """记录执行步骤"""
        AgentExecution.objects.create(
            task=task,
            step_name=step_name,
            step_order=step_order,
            input_data={"step": step_name},
            started_at=timezone.now(),
            status=TaskStatus.COMPLETED,
            logs=logs
        )
    
    def _update_progress(self, task: AgentTask, progress: float):
        """更新任务进度"""
        task.progress = progress
        task.save(update_fields=['progress'])


# 全局执行器实例缓存
_executors = {}


def get_agent_executor(agent: SmartAgent) -> AgentExecutor:
    """获取智能体执行器"""
    if agent.id not in _executors:
        _executors[agent.id] = AgentExecutor(agent)
    return _executors[agent.id]


def execute_agent_task(task_id: str) -> Dict[str, Any]:
    """
    执行智能体任务的入口函数
    
    Args:
        task_id: 任务ID
        
    Returns:
        执行结果
    """
    try:
        task = AgentTask.objects.get(id=task_id)
        executor = get_agent_executor(task.agent)
        return executor.execute_task(task)
    except AgentTask.DoesNotExist:
        raise ValueError(f"任务不存在: {task_id}")
    except Exception as e:
        logger.error(f"执行任务失败: {task_id}, 错误: {str(e)}")
        raise