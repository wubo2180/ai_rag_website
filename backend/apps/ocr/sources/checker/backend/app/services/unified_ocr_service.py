"""
统一OCR识别服务
根据文档类型自动路由到相应的OCR服务
"""
import time
import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from flask import current_app

logger = logging.getLogger(__name__)


class UnifiedOCRService:
    """统一OCR识别服务"""
    
    # 文档类型到服务的映射
    DOCUMENT_TYPE_MAPPING = {
        'commission': 'commission_ocr',  # 委托单 -> 委托单OCR服务
        'paper': 'paper_ocr',            # 论文 -> 论文OCR服务
    }
    
    def __init__(self):
        """初始化服务"""
        self.config = None
        
    def _get_config(self):
        """获取配置"""
        if self.config is None:
            self.config = current_app.config
        return self.config
        
    def recognize_file(self, file_path: str, document_type_code: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        识别文件
        
        Args:
            file_path: 文件路径
            document_type_code: 文档类型代码（'commission' 或 'paper'）
            
        Returns:
            (success, result_data, error_message)
        """
        logger.info(f"[UnifiedOCR] 开始识别文件: {file_path}, 文档类型: {document_type_code}")
        
        # 验证文件是否存在
        if not Path(file_path).exists():
            error_msg = f"文件不存在: {file_path}"
            logger.error(f"[UnifiedOCR] {error_msg}")
            return False, None, error_msg
        
        # 根据文档类型选择服务
        service_type = self.DOCUMENT_TYPE_MAPPING.get(document_type_code)
        if not service_type:
            error_msg = f"不支持的文档类型: {document_type_code}"
            logger.error(f"[UnifiedOCR] {error_msg}")
            return False, None, error_msg
        
        # 路由到相应的识别服务
        if service_type == 'commission_ocr':
            return self._recognize_commission(file_path)
        elif service_type == 'paper_ocr':
            return self._recognize_paper(file_path)
        else:
            error_msg = f"未实现的服务类型: {service_type}"
            logger.error(f"[UnifiedOCR] {error_msg}")
            return False, None, error_msg
    
    def _recognize_commission(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        调用委托单OCR服务
        
        Args:
            file_path: 文件路径
            
        Returns:
            (success, result_data, error_message)
        """
        config = self._get_config()
        service_url = config.get('OCR_COMMISSION_SERVICE_URL')
        endpoint = config.get('OCR_COMMISSION_ANALYZE_ENDPOINT')
        timeout = config.get('OCR_COMMISSION_TIMEOUT', 300)
        max_retries = config.get('OCR_MAX_RETRIES', 3)
        retry_delay = config.get('OCR_RETRY_DELAY', 5)
        
        # 获取请求参数配置
        default_user = config.get('OCR_DEFAULT_USER', 'system')
        response_mode = config.get('OCR_DEFAULT_RESPONSE_MODE', 'blocking')
        
        full_url = f"{service_url}{endpoint}"
        
        logger.info(f"[CommissionOCR] 调用委托单OCR服务: {full_url}")
        logger.info(f"[CommissionOCR] 文件: {file_path}")
        
        # 重试逻辑
        for attempt in range(max_retries):
            try:
                # 准备文件和表单数据
                file_name = Path(file_path).name
                with open(file_path, 'rb') as f:
                    files = {'file': (file_name, f, 'application/pdf')}
                    data = {
                        'user': default_user,
                        'response_mode': response_mode
                    }
                    
                    # 发送请求
                    logger.info(f"[CommissionOCR] 尝试 {attempt + 1}/{max_retries}...")
                    logger.info(f"[CommissionOCR] 请求参数: user={default_user}, response_mode={response_mode}")
                    start_time = time.time()
                    
                    response = requests.post(
                        full_url,
                        files=files,
                        data=data,
                        timeout=timeout
                    )
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"[CommissionOCR] 请求完成，耗时: {elapsed_time:.2f}秒")
                    
                    # 检查响应状态
                    if response.status_code == 200:
                        result_data = response.json()
                        
                        # 统一格式验证
                        if 'success' in result_data:
                            if result_data['success']:
                                logger.info(f"[CommissionOCR] ✅ 识别成功")
                                logger.info(f"[CommissionOCR] 服务器处理时间: {result_data.get('processing_time', 'N/A')}秒")
                                return True, result_data, None
                            else:
                                error_msg = result_data.get('message', '识别失败')
                                logger.error(f"[CommissionOCR] ❌ 识别失败: {error_msg}")
                                return False, None, error_msg
                        else:
                            error_msg = "响应格式错误：缺少success字段"
                            logger.error(f"[CommissionOCR] ❌ {error_msg}")
                            return False, None, error_msg
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                        logger.error(f"[CommissionOCR] ❌ 请求失败: {error_msg}")
                        
                        # 如果是服务器错误，重试
                        if response.status_code >= 500 and attempt < max_retries - 1:
                            logger.info(f"[CommissionOCR] 等待 {retry_delay} 秒后重试...")
                            time.sleep(retry_delay)
                            continue
                        
                        return False, None, error_msg
                        
            except requests.exceptions.Timeout:
                error_msg = f"请求超时（{timeout}秒）"
                logger.error(f"[CommissionOCR] ❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    logger.info(f"[CommissionOCR] 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                
                return False, None, error_msg
                
            except requests.exceptions.ConnectionError as e:
                error_msg = f"连接失败: {str(e)}"
                logger.error(f"[CommissionOCR] ❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    logger.info(f"[CommissionOCR] 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                
                return False, None, error_msg
                
            except Exception as e:
                error_msg = f"未知错误: {str(e)}"
                logger.error(f"[CommissionOCR] ❌ {error_msg}", exc_info=True)
                return False, None, error_msg
        
        # 所有重试都失败
        error_msg = f"所有尝试都失败（共 {max_retries} 次）"
        logger.error(f"[CommissionOCR] ❌ {error_msg}")
        return False, None, error_msg
    
    def _recognize_paper(self, file_path: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        调用论文OCR服务
        
        Args:
            file_path: 文件路径
            
        Returns:
            (success, result_data, error_message)
        """
        config = self._get_config()
        service_url = config.get('OCR_PAPER_SERVICE_URL')
        endpoint = config.get('OCR_PAPER_ANALYZE_ENDPOINT')
        timeout = config.get('OCR_PAPER_TIMEOUT', 300)
        max_retries = config.get('OCR_MAX_RETRIES', 3)
        retry_delay = config.get('OCR_RETRY_DELAY', 5)
        
        # 获取请求参数配置
        default_user = config.get('OCR_DEFAULT_USER', 'system')
        response_mode = config.get('OCR_DEFAULT_RESPONSE_MODE', 'blocking')
        
        full_url = f"{service_url}{endpoint}"
        
        logger.info(f"[PaperOCR] 调用论文OCR服务: {full_url}")
        logger.info(f"[PaperOCR] 文件: {file_path}")
        
        # 重试逻辑
        for attempt in range(max_retries):
            try:
                # 准备文件和表单数据
                file_name = Path(file_path).name
                with open(file_path, 'rb') as f:
                    files = {'file': (file_name, f, 'application/pdf')}
                    data = {
                        'user': default_user,
                        'response_mode': response_mode
                    }
                    
                    # 发送请求
                    logger.info(f"[PaperOCR] 尝试 {attempt + 1}/{max_retries}...")
                    logger.info(f"[PaperOCR] 请求参数: user={default_user}, response_mode={response_mode}")
                    start_time = time.time()
                    
                    response = requests.post(
                        full_url,
                        files=files,
                        data=data,
                        timeout=timeout
                    )
                    
                    elapsed_time = time.time() - start_time
                    logger.info(f"[PaperOCR] 请求完成，耗时: {elapsed_time:.2f}秒")
                    
                    # 检查响应状态
                    if response.status_code == 200:
                        result_data = response.json()
                        
                        # 统一格式验证：所有OCR服务现在都返回相同格式
                        if 'success' in result_data:
                            if result_data['success']:
                                logger.info(f"[PaperOCR] ✅ 识别成功")
                                logger.info(f"[PaperOCR] 服务器处理时间: {result_data.get('processing_time', 'N/A')}秒")
                                return True, result_data, None
                            else:
                                error_msg = result_data.get('message', '识别失败')
                                logger.error(f"[PaperOCR] ❌ 识别失败: {error_msg}")
                                return False, None, error_msg
                        else:
                            error_msg = "响应格式错误：缺少success字段"
                            logger.error(f"[PaperOCR] ❌ {error_msg}")
                            return False, None, error_msg
                    else:
                        error_msg = f"HTTP {response.status_code}: {response.text[:500]}"
                        logger.error(f"[PaperOCR] ❌ 请求失败: {error_msg}")
                        
                        # 如果是服务器错误，重试
                        if response.status_code >= 500 and attempt < max_retries - 1:
                            logger.info(f"[PaperOCR] 等待 {retry_delay} 秒后重试...")
                            time.sleep(retry_delay)
                            continue
                        
                        return False, None, error_msg
                        
            except requests.exceptions.Timeout:
                error_msg = f"请求超时（{timeout}秒）"
                logger.error(f"[PaperOCR] ❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    logger.info(f"[PaperOCR] 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                
                return False, None, error_msg
                
            except requests.exceptions.ConnectionError as e:
                error_msg = f"连接失败: {str(e)}"
                logger.error(f"[PaperOCR] ❌ {error_msg}")
                
                if attempt < max_retries - 1:
                    logger.info(f"[PaperOCR] 等待 {retry_delay} 秒后重试...")
                    time.sleep(retry_delay)
                    continue
                
                return False, None, error_msg
                
            except Exception as e:
                error_msg = f"未知错误: {str(e)}"
                logger.error(f"[PaperOCR] ❌ {error_msg}", exc_info=True)
                return False, None, error_msg
        
        # 所有重试都失败
        error_msg = f"所有尝试都失败（共 {max_retries} 次）"
        logger.error(f"[PaperOCR] ❌ {error_msg}")
        return False, None, error_msg
    
    def check_service_health(self, document_type_code: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        检查OCR服务健康状态
        
        Args:
            document_type_code: 文档类型代码
            
        Returns:
            (healthy, status_data, error_message)
        """
        config = self._get_config()
        service_type = self.DOCUMENT_TYPE_MAPPING.get(document_type_code)
        
        if not service_type:
            return False, None, f"不支持的文档类型: {document_type_code}"
        
        try:
            if service_type == 'commission_ocr':
                service_url = config.get('OCR_COMMISSION_SERVICE_URL')
                health_endpoint = config.get('OCR_COMMISSION_HEALTH_ENDPOINT')
            elif service_type == 'paper_ocr':
                service_url = config.get('OCR_PAPER_SERVICE_URL')
                health_endpoint = config.get('OCR_PAPER_HEALTH_ENDPOINT')
            else:
                return False, None, f"未知服务类型: {service_type}"
            
            full_url = f"{service_url}{health_endpoint}"
            logger.info(f"[HealthCheck] 检查服务健康状态: {full_url}")
            
            response = requests.get(full_url, timeout=10)
            
            if response.status_code == 200:
                status_data = response.json()
                logger.info(f"[HealthCheck] ✅ 服务健康")
                return True, status_data, None
            else:
                error_msg = f"HTTP {response.status_code}"
                logger.error(f"[HealthCheck] ❌ 服务不健康: {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"健康检查失败: {str(e)}"
            logger.error(f"[HealthCheck] ❌ {error_msg}")
            return False, None, error_msg


# 创建全局单例
unified_ocr_service = UnifiedOCRService()


