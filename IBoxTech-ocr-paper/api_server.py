"""
REST API service for the paper OCR workflow.
"""
import json
import os
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import uvicorn
import yaml
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dify_client import DifyClient


BASE_DIR = Path(__file__).resolve().parent


def load_config(config_path: str = "config.yaml"):
    path = Path(config_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    with open(path, "r", encoding="utf-8") as file:
        loaded_config = yaml.safe_load(file)

    dify_config = loaded_config.setdefault("dify", {})
    dify_config["base_url"] = os.environ.get("DIFY_BASE_URL", dify_config.get("base_url"))
    dify_config["api_key"] = os.environ.get("DIFY_API_KEY", dify_config.get("api_key"))
    dify_config["default_user"] = os.environ.get("DIFY_DEFAULT_USER", dify_config.get("default_user"))
    return loaded_config


config = load_config()


def extract_dify_error(result: Any) -> Optional[str]:
    def normalize(message: str) -> str:
        text = str(message or "").strip()
        if not text:
            return "论文分析失败"
        lowered = text.lower()
        if "insufficient balance" in lowered or "status code 402" in lowered:
            return "论文OCR上游模型余额不足，请充值或更换可用模型配置"
        return text

    if not isinstance(result, dict):
        return None

    if str(result.get("status", "")).lower() in {"error", "failed"}:
        return normalize(result.get("message") or result.get("error") or "论文分析失败")

    nested = result.get("data")
    if isinstance(nested, dict) and str(nested.get("status", "")).lower() in {"failed", "error", "stopped"}:
        return normalize(nested.get("error") or nested.get("message") or "论文分析失败")

    return None


def build_default_additional_inputs(filename: str) -> Dict[str, Any]:
    return {
        "template_type": "paper_material_v2",
        "filename_hint": filename,
        "output_requirements": (
            "请输出固定 JSON 结构 paper_material_v2。必须包含 basic_info、materials、"
            "preparation_process、intermediates、properties、notes 六部分。缺失字段请返回空字符串、"
            "空数组或空对象，不要省略字段，也不要输出模板外说明文字。"
        ),
        "output_schema": {
            "template_type": "paper_material_v2",
            "basic_info": {
                "article_id": "",
                "article_name": "",
                "article_doi": "",
                "publish_year": "",
            },
            "materials": [
                {
                    "material_id": "",
                    "material_name": "",
                    "material_characteristic": "",
                    "cas_number": "",
                }
            ],
            "preparation_process": "",
            "intermediates": [
                {
                    "intermediate_id": "",
                    "formula": "",
                }
            ],
            "properties": {
                "columns": [
                    {
                        "key": "metric_1",
                        "name": "",
                    }
                ],
                "rows": [
                    {
                        "product_name": "",
                        "values": {
                            "metric_1": "",
                        },
                    }
                ],
            },
            "notes": "",
        },
    }


def parse_extra(extra: Optional[str]) -> Dict[str, Any]:
    if not extra:
        return {}
    try:
        payload = json.loads(extra)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    service: Optional[str] = None
    version: Optional[str] = None
    dify_base_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    processing_time: float


app = FastAPI(
    title="Dify 论文分析 API",
    description="提供论文文件上传和智能分析的 REST API 接口",
    version="1.0.0",
)

if config["api"]["enable_cors"]:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config["api"]["allowed_origins"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

temp_dir = Path(config["api"]["temp_upload_dir"])
temp_dir.mkdir(parents=True, exist_ok=True)

dify_client = DifyClient()


@app.get("/")
async def root():
    return {
        "message": "Dify 论文分析 API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health - GET - 服务健康检查",
            "analyze": "/api/analyze - POST - 上传 PDF 文件进行分析",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        service="IBoxTech OCR Paper API",
        version="1.0.0",
        dify_base_url=config["dify"]["base_url"],
    )


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze_file(
    file: UploadFile = File(..., description="要分析的 PDF 文件"),
    user: Optional[str] = Form(None, description="用户标识"),
    token: Optional[str] = Form(None, description="用户认证 token"),
    response_mode: Optional[str] = Form(None, description="响应模式: blocking 或 streaming"),
    extra: Optional[str] = Form(None, description="自定义参数（JSON 字符串格式）"),
):
    start_time = time.time()

    print("收到分析请求:")
    print(f"  - 文件名: {file.filename}")
    print(f"  - 用户: {user or 'N/A'}")
    print(f"  - Token: {'***' if token else 'N/A'}")
    print(f"  - 响应模式: {response_mode or 'blocking (default)'}")
    print(f"  - 额外参数: {extra or 'N/A'}")

    file_extension = os.path.splitext(file.filename)[1].lower().replace(".", "")
    allowed_extensions = config["dify"]["upload"]["allowed_extensions"]

    if file_extension not in allowed_extensions:
        return AnalyzeResponse(
            success=False,
            message=f"不支持的文件类型。允许的类型: {', '.join(allowed_extensions)}",
            data=None,
            processing_time=time.time() - start_time,
        )

    temp_file_path = temp_dir / file.filename

    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size_mb = os.path.getsize(temp_file_path) / (1024 * 1024)
        max_size = config["dify"]["upload"]["max_file_size"]
        if file_size_mb > max_size:
            os.remove(temp_file_path)
            return AnalyzeResponse(
                success=False,
                message=f"文件大小超过限制。最大允许 {max_size}MB，当前文件 {file_size_mb:.2f}MB",
                data=None,
                processing_time=time.time() - start_time,
            )

        additional_inputs = build_default_additional_inputs(file.filename or "")
        additional_inputs.update(parse_extra(extra))

        dify_result = dify_client.process_file(
            file_path=str(temp_file_path),
            user=user,
            response_mode=response_mode,
            additional_inputs=additional_inputs,
        )

        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        processing_time = time.time() - start_time
        if isinstance(dify_result, dict):
            dify_status = dify_result.get("status", "unknown")
            dify_error = extract_dify_error(dify_result)

            if dify_status == "error" or dify_error:
                return AnalyzeResponse(
                    success=False,
                    message=dify_error or dify_result.get("message", "论文分析失败"),
                    data=dify_result,
                    processing_time=processing_time,
                )

            return AnalyzeResponse(
                success=True,
                message="论文分析成功",
                data=dify_result,
                processing_time=processing_time,
            )

        return AnalyzeResponse(
            success=True,
            message="论文分析完成",
            data=dify_result if isinstance(dify_result, dict) else {"result": dify_result},
            processing_time=processing_time,
        )
    except Exception as error:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return AnalyzeResponse(
            success=False,
            message=f"处理文件时发生错误: {error}",
            data=None,
            processing_time=time.time() - start_time,
        )


if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host=config["api"]["host"],
        port=config["api"]["port"],
        reload=config["api"]["debug"],
    )
