"""
REST API 服务器
提供文件上传和分析的 REST API 接口
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import yaml
import os
import shutil
import time
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from dify_client import DifyClient


# 加载配置
def load_config(config_path: str = "config.yaml"):
    """加载配置文件"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


config = load_config()


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    service: Optional[str] = None
    version: Optional[str] = None
    dify_base_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    """分析接口响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: float


# 创建 FastAPI 应用
app = FastAPI(
    title="Dify 论文分析 API",
    description="提供论文文件上传和智能分析的 REST API 接口",
    version="1.0.0"
)

# 配置 CORS
if config['api']['enable_cors']:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config['api']['allowed_origins'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 创建临时文件存储目录
temp_dir = Path(config['api']['temp_upload_dir'])
temp_dir.mkdir(exist_ok=True)

# 初始化 Dify 客户端
dify_client = DifyClient()


@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "Dify 论文分析 API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health - GET - 服务健康检查",
            "analyze": "/api/analyze - POST - 上传PDF文件进行分析"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查接口"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="IBoxTech OCR Paper API",
        version="1.0.0",
        dify_base_url=config['dify']['base_url']
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(..., description="要分析的 PDF 文件"),
    user: Optional[str] = Form(None, description="用户标识"),
    token: Optional[str] = Form(None, description="用户认证 token"),
    response_mode: Optional[str] = Form(None, description="响应模式: blocking 或 streaming"),
    extra: Optional[str] = Form(None, description="自定义参数（JSON字符串格式）")
):
    """
    上传并分析文件的统一接口
    
    Args:
        file: 上传的PDF文件
        user: 用户标识（可选）
        token: 用户认证token（可选）
        response_mode: 响应模式 - blocking 或 streaming（可选）
        extra: 自定义参数，JSON字符串格式（可选）
        
    Returns:
        统一格式的分析结果:
        {
            "success": bool,
            "message": str,
            "data": dify_result,
            "processing_time": float
        }
    """
    start_time = time.time()
    
    # 打印请求参数（用于调试）
    print(f"📥 收到分析请求:")
    print(f"   - 文件名: {file.filename}")
    print(f"   - 用户: {user or 'N/A'}")
    print(f"   - Token: {'***' if token else 'N/A'}")
    print(f"   - 响应模式: {response_mode or 'blocking (default)'}")
    print(f"   - 额外参数: {extra or 'N/A'}")
    
    # 验证文件类型
    file_extension = os.path.splitext(file.filename)[1].lower().replace('.', '')
    allowed_extensions = config['dify']['upload']['allowed_extensions']
    
    if file_extension not in allowed_extensions:
        return AnalyzeResponse(
            success=False,
            message=f"不支持的文件类型。允许的类型: {', '.join(allowed_extensions)}",
            data=None,
            processing_time=time.time() - start_time
        )
    
    # 保存上传的文件到临时目录
    temp_file_path = temp_dir / file.filename
    
    try:
        # 保存文件
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 检查文件大小
        file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
        max_size = config['dify']['upload']['max_file_size']
        
        if file_size_mb > max_size:
            os.remove(temp_file_path)
            return AnalyzeResponse(
                success=False,
                message=f"文件大小超过限制。最大允许: {max_size}MB，当前文件: {file_size_mb:.2f}MB",
                data=None,
                processing_time=time.time() - start_time
            )
        
        # 使用 Dify 客户端处理文件
        dify_result = dify_client.process_file(
            file_path=str(temp_file_path),
            user=user,
            response_mode=response_mode
        )
        
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 检查Dify结果状态
        if isinstance(dify_result, dict):
            # 判断Dify是否成功
            dify_status = dify_result.get('status', 'unknown')
            
            if dify_status == 'error':
                # Dify处理失败
                return AnalyzeResponse(
                    success=False,
                    message=dify_result.get('message', '论文分析失败'),
                    data=dify_result,
                    processing_time=processing_time
                )
            else:
                # Dify处理成功
                return AnalyzeResponse(
                    success=True,
                    message="论文分析成功",
                    data=dify_result,
                    processing_time=processing_time
                )
        else:
            # 未知格式
            return AnalyzeResponse(
                success=True,
                message="论文分析完成",
                data=dify_result if isinstance(dify_result, dict) else {"result": dify_result},
                processing_time=processing_time
            )
        
    except Exception as e:
        # 清理临时文件
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # 返回统一错误格式
        return AnalyzeResponse(
            success=False,
            message=f"处理文件时发生错误: {str(e)}",
            data=None,
            processing_time=time.time() - start_time
        )


if __name__ == "__main__":
    # 启动服务器
    # 使用导入字符串以支持 reload 模式
    uvicorn.run(
        "api_server:app",
        host=config['api']['host'],
        port=config['api']['port'],
        reload=config['api']['debug']
    )

