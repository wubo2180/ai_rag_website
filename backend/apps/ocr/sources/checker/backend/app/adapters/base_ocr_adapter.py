"""
OCR适配器基类
定义所有OCR适配器必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class BaseOCRAdapter(ABC):
    """
    OCR适配器基类
    
    每个OCR模型必须实现一个适配器类，继承此基类并实现所有抽象方法
    """
    
    def __init__(self):
        """初始化适配器"""
        self.adapter_name = self.__class__.__name__
        logger.info(f"[{self.adapter_name}] 初始化适配器")
    
    @abstractmethod
    def parse_ocr_result(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析OCR服务返回的原始数据为结构化数据
        
        Args:
            raw_data: OCR服务返回的原始数据
            
        Returns:
            结构化数据，格式由具体适配器定义
            
        Example:
            {
                'basic_info': {...},
                'items': [...],
                'metadata': {...}
            }
        """
        pass
    
    @abstractmethod
    def save_to_database(self, structured_data: Dict[str, Any], file_id: int) -> Tuple[bool, Optional[str]]:
        """
        将结构化数据保存到数据库
        
        Args:
            structured_data: 解析后的结构化数据
            file_id: 关联的文件ID
            
        Returns:
            (success, error_message)
            - success: 是否保存成功
            - error_message: 如果失败，返回错误信息
        """
        pass
    
    @abstractmethod
    def get_from_database(self, file_id: int) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        从数据库获取结构化数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, structured_data, error_message)
            - success: 是否获取成功
            - structured_data: 结构化数据
            - error_message: 如果失败，返回错误信息
        """
        pass
    
    @abstractmethod
    def validate_data(self, structured_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证结构化数据的有效性
        
        Args:
            structured_data: 待验证的结构化数据
            
        Returns:
            (is_valid, errors)
            - is_valid: 数据是否有效
            - errors: 验证错误列表
        """
        pass
    
    @abstractmethod
    def delete_from_database(self, file_id: int) -> Tuple[bool, Optional[str]]:
        """
        从数据库删除数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, error_message)
            - success: 是否删除成功
            - error_message: 如果失败，返回错误信息
        """
        pass
    
    @abstractmethod
    def update_in_database(self, structured_data: Dict[str, Any], file_id: int) -> Tuple[bool, Optional[str]]:
        """
        更新数据库中的数据
        
        Args:
            structured_data: 更新后的结构化数据
            file_id: 文件ID
            
        Returns:
            (success, error_message)
            - success: 是否更新成功
            - error_message: 如果失败，返回错误信息
        """
        pass
    
    def get_adapter_info(self) -> Dict[str, Any]:
        """
        获取适配器信息
        
        Returns:
            适配器信息字典
        """
        return {
            'adapter_name': self.adapter_name,
            'adapter_class': self.__class__.__name__,
            'module': self.__class__.__module__
        }
    
    def log_info(self, message: str):
        """记录信息日志"""
        logger.info(f"[{self.adapter_name}] {message}")
    
    def log_error(self, message: str):
        """记录错误日志"""
        logger.error(f"[{self.adapter_name}] {message}")
    
    def log_warning(self, message: str):
        """记录警告日志"""
        logger.warning(f"[{self.adapter_name}] {message}")


class OCRAdapterException(Exception):
    """OCR适配器异常基类"""
    pass


class ParseError(OCRAdapterException):
    """数据解析错误"""
    pass


class SaveError(OCRAdapterException):
    """数据保存错误"""
    pass


class ValidationError(OCRAdapterException):
    """数据验证错误"""
    pass


