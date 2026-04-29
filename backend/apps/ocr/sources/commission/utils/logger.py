#!/usr/bin/env python3
"""
V3日志系统 - 支持分级调试输出
"""

import sys
import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Any
from config.settings import V3Config, DebugLevel, OutputLevel

class LogLevel(Enum):
    """日志级别"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"
    PROGRESS = "PROGRESS"

class V3Logger:
    """V3统一日志管理器"""
    
    def __init__(self, config: V3Config, log_file: Optional[Path] = None):
        self.config = config
        self.log_file = log_file
        self.start_time = time.time()
        
        # 颜色配置
        self.colors = {
            LogLevel.DEBUG: '\033[90m',     # 灰色
            LogLevel.INFO: '\033[94m',      # 蓝色
            LogLevel.WARNING: '\033[93m',   # 黄色  
            LogLevel.ERROR: '\033[91m',     # 红色
            LogLevel.SUCCESS: '\033[92m',   # 绿色
            LogLevel.PROGRESS: '\033[96m',  # 青色
        }
        self.reset_color = '\033[0m'
        
        # 如果指定了日志文件，创建目录
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _should_log(self, level: LogLevel) -> bool:
        """判断是否应该输出此级别的日志"""
        debug_level = self.config.debug_level
        
        if debug_level == DebugLevel.NONE:
            return level == LogLevel.ERROR
        elif debug_level == DebugLevel.ERROR:
            return level == LogLevel.ERROR
        elif debug_level == DebugLevel.WARNING:
            return level in [LogLevel.ERROR, LogLevel.WARNING]
        elif debug_level == DebugLevel.INFO:
            return level in [LogLevel.ERROR, LogLevel.WARNING, LogLevel.INFO, LogLevel.SUCCESS, LogLevel.PROGRESS]
        elif debug_level == DebugLevel.DEBUG:
            return True
        elif debug_level == DebugLevel.VERBOSE:
            return True
        
        return False
    
    def _format_message(self, level: LogLevel, message: str, prefix: str = "") -> str:
        """格式化日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        if self.config.output_level == OutputLevel.MINIMAL:
            return f"{prefix}{message}"
        elif self.config.output_level == OutputLevel.STANDARD:
            return f"{prefix}[{level.value}] {message}"
        else:  # DETAILED or COMPREHENSIVE
            return f"{prefix}[{timestamp}] [{level.value}] {message}"
    
    def _log(self, level: LogLevel, message: str, prefix: str = "", color: bool = True):
        """内部日志输出方法"""
        if not self._should_log(level):
            return
        
        formatted_msg = self._format_message(level, message, prefix)
        
        # 控制台输出
        if color and level in self.colors:
            console_msg = f"{self.colors[level]}{formatted_msg}{self.reset_color}"
        else:
            console_msg = formatted_msg
        
        print(console_msg)
        
        # 文件输出
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(f"{formatted_msg}\n")
            except Exception as e:
                print(f"日志文件写入失败: {e}")
    
    # 基础日志方法
    def debug(self, message: str):
        """调试信息"""
        self._log(LogLevel.DEBUG, message, "🔍 ")
    
    def info(self, message: str):
        """一般信息"""
        self._log(LogLevel.INFO, message, "ℹ️  ")
    
    def warning(self, message: str):
        """警告信息"""
        self._log(LogLevel.WARNING, message, "⚠️  ")
    
    def error(self, message: str):
        """错误信息"""
        self._log(LogLevel.ERROR, message, "❌ ")
    
    def success(self, message: str):
        """成功信息"""
        self._log(LogLevel.SUCCESS, message, "✅ ")
    
    def progress(self, message: str):
        """进度信息"""
        self._log(LogLevel.PROGRESS, message, "⏳ ")
    
    # 结构化输出方法
    def step_header(self, step_name: str, step_number: int):
        """步骤开始标记"""
        if self.config.output_level != OutputLevel.MINIMAL:
            separator = "=" * 60
            self._log(LogLevel.INFO, f"\n{separator}")
            self._log(LogLevel.INFO, f"步骤 {step_number}: {step_name}")
            self._log(LogLevel.INFO, f"{separator}")
    
    def step_footer(self, step_number: int, elapsed_time: Optional[float] = None):
        """步骤结束标记"""
        if self.config.output_level == OutputLevel.COMPREHENSIVE:
            if elapsed_time:
                self._log(LogLevel.SUCCESS, f"步骤 {step_number} 完成 (耗时: {elapsed_time:.2f}秒)")
            else:
                self._log(LogLevel.SUCCESS, f"步骤 {step_number} 完成")
    
    def result_summary(self, message: str):
        """结果摘要"""
        self._log(LogLevel.SUCCESS, f"📊 {message}")
    
    def file_saved(self, file_path: Path, description: str = ""):
        """文件保存通知"""
        if self.config.is_verbose_enabled():
            desc = f" ({description})" if description else ""
            self._log(LogLevel.INFO, f"💾 文件保存: {file_path}{desc}")
    
    def performance_metric(self, metric_name: str, value: Any, unit: str = ""):
        """性能指标"""
        if self.config.debug_level in [DebugLevel.DEBUG, DebugLevel.VERBOSE]:
            unit_str = f" {unit}" if unit else ""
            self._log(LogLevel.DEBUG, f"📈 {metric_name}: {value}{unit_str}")
    
    def memory_usage(self, description: str = ""):
        """内存使用情况"""
        if self.config.debug_level == DebugLevel.VERBOSE:
            try:
                import psutil
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                desc = f" ({description})" if description else ""
                self._log(LogLevel.DEBUG, f"💾 内存使用: {memory_mb:.1f}MB{desc}")
            except ImportError:
                pass
    
    def execution_time(self, description: str = ""):
        """执行时间"""
        elapsed = time.time() - self.start_time
        desc = f" ({description})" if description else ""
        self._log(LogLevel.INFO, f"⏱️  总执行时间: {elapsed:.2f}秒{desc}")
    
    # 兼容旧接口
    @property
    def debug_enabled(self) -> bool:
        """兼容旧代码的调试开关"""
        return self.config.is_debug_enabled()
