"""
Dify API 服务
用于处理与Dify平台的交互，包括文件上传和工作流执行
"""

import os
import requests
import json
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class DifyAPIService:
    """Dify API服务类"""
    
    def __init__(self):
        self.api_url = settings.DIFY_API_URL
        # 直接从环境变量获取，避免Django settings缓存问题
        import os
        self.api_key = os.environ.get('DIFY_API_KEY_data4line', settings.DIFY_API_KEY)
        self.session = requests.Session()
        
        # 设置请求头
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
        })
    
    def upload_file(self, file_path: str, user: str = "default_user") -> Optional[str]:
        """
        上传文件到Dify平台
        
        Args:
            file_path: 文件路径
            user: 用户标识
            
        Returns:
            str: 文件ID，如果上传失败返回None
        """
        upload_url = f"{self.api_url}/files/upload"
        
        try:
            logger.info(f"开始上传文件: {file_path}")
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, 'application/octet-stream')
                }
                data = {
                    "user": user
                }
                
                # 上传文件时需要移除Content-Type头
                headers = {'Authorization': f'Bearer {self.api_key}'}
                
                response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=60)
                
                logger.info(f"上传响应状态码: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    file_id = result.get('id')
                    logger.info(f"文件上传成功，文件ID: {file_id}")
                    return file_id
                else:
                    logger.error(f"文件上传失败，状态码: {response.status_code}, 错误: {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"文件上传异常: {str(e)}")
            return None
    
    def upload_file_from_memory(self, file_data: bytes, filename: str, user: str = "default_user") -> Optional[str]:
        """
        从内存上传文件到Dify平台
        
        Args:
            file_data: 文件二进制数据
            filename: 文件名
            user: 用户标识
            
        Returns:
            str: 文件ID，如果上传失败返回None
        """
        upload_url = f"{self.api_url}/files/upload"
        
        try:
            logger.info(f"开始上传文件: {filename}")
            
            files = {
                'file': (filename, file_data, 'application/octet-stream')
            }
            data = {
                "user": user
            }
            
            # 上传文件时需要移除Content-Type头
            headers = {'Authorization': f'Bearer {self.api_key}'}
            
            response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=60)
            
            logger.info(f"上传响应状态码: {response.status_code}")
            
            if response.status_code in [200, 201]:
                result = response.json()
                file_id = result.get('id')
                logger.info(f"文件上传成功，文件ID: {file_id}")
                return file_id
            else:
                logger.error(f"文件上传失败，状态码: {response.status_code}, 错误: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"文件上传异常: {str(e)}")
            return None
    
    def run_workflow(self, file_id: str, user: str = "default_user", 
                    response_mode: str = "streaming") -> Dict[str, Any]:
        """
        运行Dify工作流
        
        Args:
            file_id: 已上传的文件ID
            user: 用户标识
            response_mode: 响应模式，blocking或streaming
            
        Returns:
            dict: 工作流执行结果
        """
        workflow_url = f"{self.api_url}/workflows/run"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "inputs": {
                "file": {
                    "transfer_method": "local_file",
                    "upload_file_id": file_id,
                    "type": "document"
                }
            },
            "response_mode": response_mode,
            "user": user
        }
        
        try:
            logger.info(f"开始运行工作流，文件ID: {file_id}")
            
            response = requests.post(workflow_url, headers=headers, json=data, timeout=120)
            
            logger.info(f"工作流响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.info("工作流执行成功")
                return {
                    "status": "success",
                    "data": result
                }
            else:
                logger.error(f"工作流执行失败，状态码: {response.status_code}, 错误: {response.text}")
                return {
                    "status": "error",
                    "message": f"工作流执行失败，状态码: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            logger.error(f"工作流执行异常: {str(e)}")
            return {
                "status": "error", 
                "message": f"工作流执行异常: {str(e)}"
            }
    
    def process_file_with_workflow(self, file_data: bytes, filename: str, 
                                 user: str = "default_user") -> Dict[str, Any]:
        """
        完整的文件处理流程：上传文件 -> 运行工作流
        
        Args:
            file_data: 文件二进制数据
            filename: 文件名
            user: 用户标识
            
        Returns:
            dict: 处理结果
        """
        try:
            # 1. 上传文件
            logger.info(f"开始处理文件: {filename}")
            file_id = self.upload_file_from_memory(file_data, filename, user)
            
            if not file_id:
                return {
                    "status": "error",
                    "message": "文件上传失败"
                }
            
            # 2. 运行工作流
            workflow_result = self.run_workflow(file_id, user)
            
            if workflow_result.get("status") == "success":
                # 解析工作流结果
                workflow_data = workflow_result.get("data", {})
                outputs = workflow_data.get("data", {}).get("outputs", {})
                
                # 尝试解析JSON格式的输出
                result_text = outputs.get("text", "")
                try:
                    if result_text:
                        parsed_result = json.loads(result_text)
                        return {
                            "status": "success",
                            "data": {
                                "extracted_knowledge": parsed_result,
                                "file_id": file_id,
                                "task_id": workflow_data.get("task_id"),
                                "workflow_run_id": workflow_data.get("workflow_run_id"),
                                "elapsed_time": workflow_data.get("data", {}).get("elapsed_time")
                            }
                        }
                    else:
                        return {
                            "status": "success",
                            "data": {
                                "extracted_knowledge": [],
                                "message": "工作流执行成功，但未返回结果",
                                "file_id": file_id,
                                "raw_output": outputs
                            }
                        }
                except json.JSONDecodeError:
                    # 如果不是JSON格式，直接返回文本
                    return {
                        "status": "success",
                        "data": {
                            "extracted_knowledge": result_text,
                            "file_id": file_id,
                            "task_id": workflow_data.get("task_id"),
                            "workflow_run_id": workflow_data.get("workflow_run_id")
                        }
                    }
            else:
                return workflow_result
                
        except Exception as e:
            logger.error(f"文件处理流程异常: {str(e)}")
            return {
                "status": "error",
                "message": f"文件处理流程异常: {str(e)}"
            }


# 创建全局实例
dify_service = DifyAPIService()