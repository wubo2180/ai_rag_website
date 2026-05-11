"""
Dify API 客户端模块
负责与 Dify 智能体 API 进行交互
"""
import requests
import os
import yaml
from typing import Dict, Optional, Any


class DifyClient:
    """Dify API 客户端"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化 Dify 客户端
        
        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.base_url = self.config['dify']['base_url']
        self.api_key = self.config['dify']['api_key']
        self.default_user = self.config['dify']['default_user']
        
    def _load_config(self, config_path: str) -> Dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def upload_file(self, file_path: str, user: Optional[str] = None) -> Optional[str]:
        """
        上传文件到 Dify
        
        Args:
            file_path: 文件路径
            user: 用户标识，如果不提供则使用默认用户
            
        Returns:
            文件 ID，如果上传失败则返回 None
        """
        if user is None:
            user = self.default_user
            
        upload_url = f"{self.base_url}{self.config['dify']['upload']['endpoint']}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        try:
            print(f"上传文件中: {os.path.basename(file_path)}")
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, 'application/pdf')
                }
                data = {
                    "user": user
                }
                
                response = requests.post(upload_url, headers=headers, files=files, data=data)
                print(f"上传响应状态码: {response.status_code}")
                
                if response.status_code in [200, 201]:
                    print("文件上传成功")
                    file_id = response.json().get("id")
                    print(f"文件 ID: {file_id}")
                    return file_id
                else:
                    print(f"文件上传失败，状态码: {response.status_code}")
                    print(f"错误详情: {response.text}")
                    return None
        except Exception as e:
            print(f"上传文件时发生错误: {str(e)}")
            return None
    
    def run_workflow(
        self, 
        file_id: str, 
        user: Optional[str] = None,
        response_mode: Optional[str] = None,
        additional_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        运行 Dify 工作流
        
        Args:
            file_id: 文件 ID
            user: 用户标识，如果不提供则使用默认用户
            response_mode: 响应模式（blocking 或 streaming）
            additional_inputs: 额外的输入参数
            
        Returns:
            工作流执行结果
        """
        if user is None:
            user = self.default_user
        
        if response_mode is None:
            response_mode = self.config['dify']['workflow']['response_mode']
            
        workflow_url = f"{self.base_url}{self.config['dify']['workflow']['endpoint']}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # 构建输入参数
        inputs = {
            "file": {
                "transfer_method": self.config['dify']['workflow']['transfer_method'],
                "upload_file_id": file_id,
                "type": self.config['dify']['workflow']['file_type']
            }
        }
        
        # 添加额外的输入参数
        if additional_inputs:
            inputs.update(additional_inputs)
        
        data = {
            "inputs": inputs,
            "response_mode": response_mode,
            "user": user
        }
        
        try:
            print("运行工作流...")
            response = requests.post(workflow_url, headers=headers, json=data)
            print(f"工作流响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                print("工作流执行成功")
                return response.json()
            else:
                print(f"工作流执行失败，状态码: {response.status_code}")
                print(f"错误详情: {response.text}")
                return {
                    "status": "error", 
                    "message": f"工作流执行失败，状态码: {response.status_code}",
                    "details": response.text
                }
        except Exception as e:
            print(f"运行工作流时发生错误: {str(e)}")
            return {
                "status": "error", 
                "message": str(e)
            }
    
    def process_file(
        self, 
        file_path: str, 
        user: Optional[str] = None,
        response_mode: Optional[str] = None,
        additional_inputs: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        处理文件的完整流程：上传文件并运行工作流
        
        Args:
            file_path: 文件路径
            user: 用户标识
            response_mode: 响应模式
            additional_inputs: 额外的输入参数
            
        Returns:
            处理结果
        """
        # 上传文件
        file_id = self.upload_file(file_path, user)
        
        if not file_id:
            return {
                "status": "error",
                "message": "文件上传失败"
            }
        
        # 运行工作流
        result = self.run_workflow(file_id, user, response_mode, additional_inputs)
        return result


if __name__ == "__main__":
    # 测试代码
    client = DifyClient()
    
    # 示例：处理文件
    file_path = "/Users/wenzhicao/Documents/WorkSpace/IBoxTech/paper-reader/双组分缩合型有机硅电子灌封胶的制备及其导热阻燃性能研究_董晓娜.pdf"
    
    if os.path.exists(file_path):
        result = client.process_file(file_path)
        print("处理结果:")
        print(result)
    else:
        print(f"文件不存在: {file_path}")

