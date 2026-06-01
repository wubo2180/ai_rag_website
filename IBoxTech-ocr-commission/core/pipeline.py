#!/usr/bin/env python3
"""
V3核心流水线 - 统一管理所有步骤的执行
"""

import time
from typing import Dict, Any, List, Optional
from pathlib import Path

from config.settings import V3Config, DEVELOPMENT_CONFIG
from utils.logger import V3Logger
from utils.file_manager import V3FileManager
from steps import AVAILABLE_STEPS

class OCRPipeline:
    """V3 OCR处理流水线 - 统一调度所有步骤"""
    
    def __init__(self, config: Optional[V3Config] = None, 
                 output_dir: Optional[Path] = None):
        """初始化流水线
        
        Args:
            config: V3配置对象，默认使用开发配置
            output_dir: 输出目录，会覆盖配置中的设置
        """
        self.config = config or DEVELOPMENT_CONFIG
        
        # 如果指定了输出目录，更新配置
        if output_dir:
            self.config.output_dir = Path(output_dir)
        
        # 初始化核心组件
        self.file_manager = V3FileManager(self.config)
        
        # 创建日志文件
        log_file = self.file_manager.base_output_dir / "pipeline.log"
        self.logger = V3Logger(self.config, log_file)
        
        # 初始化步骤
        self.steps = {}
        self._initialize_steps()
        
        # 执行统计
        self.execution_stats = {}
        
    def _initialize_steps(self):
        """初始化所有步骤"""
        for step_num, step_class in AVAILABLE_STEPS.items():
            try:
                step_instance = step_class(
                    self.config, 
                    self.file_manager, 
                    self.logger
                )
                self.steps[step_num] = step_instance
                self.logger.debug(f"步骤 {step_num} 初始化成功: {step_class.__name__}")
            except Exception as e:
                self.logger.error(f"步骤 {step_num} 初始化失败: {e}")
                raise
    
    def run_single_step(self, step_number: int, input_data: Any) -> Any:
        """运行单个步骤
        
        Args:
            step_number: 步骤编号
            input_data: 输入数据
            
        Returns:
            步骤输出数据
        """
        if step_number not in self.steps:
            raise ValueError(f"步骤 {step_number} 不存在")
        
        step = self.steps[step_number]
        
        self.logger.info(f"开始执行步骤 {step_number}: {step.step_name}")
        start_time = time.time()
        
        try:
            result = step.run(input_data)
            
            # 记录执行统计
            elapsed_time = time.time() - start_time
            self.execution_stats[step_number] = {
                'step_name': step.step_name,
                'execution_time': elapsed_time,
                'status': 'success'
            }
            
            self.logger.success(f"步骤 {step_number} 执行成功，耗时 {elapsed_time:.2f}秒")
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            self.execution_stats[step_number] = {
                'step_name': step.step_name,
                'execution_time': elapsed_time,
                'status': 'failed',
                'error': str(e)
            }
            
            self.logger.error(f"步骤 {step_number} 执行失败: {e}")
            raise
    
    def run_pipeline(self, input_file: str, 
                    start_step: int = 1, 
                    end_step: Optional[int] = None) -> Dict[str, Any]:
        """运行完整流水线
        
        Args:
            input_file: 输入文件路径
            start_step: 开始步骤编号
            end_step: 结束步骤编号，None表示运行到最后
            
        Returns:
            包含所有步骤结果的字典
        """
        pipeline_start_time = time.time()
        
        self.logger.info("=" * 60)
        self.logger.info(f"V3 OCR Pipeline 开始执行")
        self.logger.info(f"输入文件: {input_file}")
        self.logger.info(f"输出目录: {self.file_manager.base_output_dir}")
        self.logger.info(f"执行步骤: {start_step} - {end_step or '最后'}")
        self.logger.info("=" * 60)
        
        # 确定执行的步骤范围
        available_steps = sorted(self.steps.keys())
        if end_step is None:
            end_step = max(available_steps)
        
        execution_steps = [s for s in available_steps if start_step <= s <= end_step]
        
        if not execution_steps:
            raise ValueError(f"没有找到有效的执行步骤 (范围: {start_step}-{end_step})")
        
        # 初始化结果字典
        results = {
            'input_file': input_file,
            'config': self.config,
            'step_results': {}
        }
        
        # 执行步骤
        current_data = input_file
        
        for step_num in execution_steps:
            try:
                self.logger.info(f"\n{'='*20} 步骤 {step_num} {'='*20}")
                
                result = self.run_single_step(step_num, current_data)
                results['step_results'][step_num] = result
                current_data = result  # 将结果传递给下一步
                
                # 记录内存使用情况
                self.logger.memory_usage(f"步骤 {step_num} 完成后")
                
            except Exception as e:
                self.logger.error(f"流水线在步骤 {step_num} 中断: {e}")
                results['error_step'] = step_num
                results['error_message'] = str(e)
                break
        
        # 执行完成统计
        total_time = time.time() - pipeline_start_time
        results['execution_stats'] = self.execution_stats
        results['total_execution_time'] = total_time
        
        # 生成执行报告
        self._generate_execution_report(results)
        
        # 清理临时文件
        if self.config.file_output.auto_cleanup:
            self.file_manager.cleanup_temp_files()
        
        self.logger.info("=" * 60)
        self.logger.success(f"V3 OCR Pipeline 执行完成，总耗时 {total_time:.2f}秒")
        self.logger.info("=" * 60)
        
        return results
    
    def _generate_execution_report(self, results: Dict[str, Any]):
        """生成执行报告"""
        try:
            report_data = {
                'pipeline_version': '3.0.0',
                'execution_time': results.get('total_execution_time', 0),
                'input_file': results.get('input_file', ''),
                'output_directory': str(self.file_manager.base_output_dir),
                'steps_executed': list(results.get('step_results', {}).keys()),
                'execution_stats': results.get('execution_stats', {}),
                'file_summary': self.file_manager.get_summary(),
                'config_summary': {
                    'debug_level': self.config.debug_level.value,
                    'output_level': self.config.output_level.value,
                    'save_intermediate': self.config.should_save_intermediate(),
                    'save_debug': self.config.should_save_debug_data(),
                    'visualization_enabled': self.config.visualization.enabled
                }
            }
            
            # 保存报告
            report_path = self.file_manager.save_json(
                report_data, 
                "pipeline_execution_report.json", 
                0,  # 步骤0表示全局
                "result"
            )
            
            if report_path:
                self.logger.file_saved(report_path, "流水线执行报告")
        
        except Exception as e:
            self.logger.warning(f"生成执行报告失败: {e}")
    
    def get_step_info(self, step_number: int) -> Dict[str, Any]:
        """获取步骤信息"""
        if step_number not in self.steps:
            return {}
        
        step = self.steps[step_number]
        return {
            'step_number': step_number,
            'step_name': step.step_name,
            'step_class': step.__class__.__name__,
            'config': step.step_config
        }
    
    def list_available_steps(self) -> List[Dict[str, Any]]:
        """列出所有可用步骤"""
        return [self.get_step_info(step_num) for step_num in sorted(self.steps.keys())]
    
    def update_step_config(self, step_number: int, config: Dict[str, Any]):
        """更新步骤配置"""
        self.config.set_step_config(step_number, config)
        if step_number in self.steps:
            self.steps[step_number].step_config = config
            
    def set_debug_level(self, debug_level):
        """设置调试级别"""
        self.config.debug_level = debug_level
        self.logger.config = self.config
