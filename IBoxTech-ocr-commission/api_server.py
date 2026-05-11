#!/usr/bin/env python3
"""
OCR分析API服务器
支持PDF文件上传和OCR分析，返回原始OCR数据和字段提取结果
"""

import asyncio
import json
import os
import tempfile
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import pdf2image
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# 添加项目根目录到Python路径
import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import DEVELOPMENT_CONFIG
from core.pipeline import OCRPipeline


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: str
    service: Optional[str] = None
    version: Optional[str] = None


class OCRResponse(BaseModel):
    """OCR分析响应模型"""
    success: bool
    message: str
    data: Dict[str, Any]
    processing_time: float


class OCRAPIServer:
    """OCR API服务器"""
    
    def __init__(self):
        """初始化API服务器"""
        self.app = FastAPI(
            title="IBoxTech OCR分析API",
            description="PDF文档OCR分析和字段提取API",
            version="1.0.0"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        self._register_routes()
        
    def _register_routes(self):
        """注册API路由"""
        
        @self.app.get("/")
        async def root():
            """API根路径"""
            return {
                "service": "IBoxTech OCR分析API",
                "version": "1.0.0",
                "status": "运行中",
                "endpoints": {
                    "analyze": "/api/analyze - POST - 上传PDF文件进行OCR分析",
                    "health": "/health - GET - 服务健康检查"
                }
            }
        
        @self.app.get("/health", response_model=HealthResponse)
        async def health_check():
            """健康检查"""
            return HealthResponse(
                status="healthy",
                timestamp=datetime.now().isoformat(),
                service="IBoxTech OCR Commission API",
                version="1.0.0"
            )
        
        @self.app.post("/api/analyze", response_model=OCRResponse)
        async def analyze_pdf(
            file: UploadFile = File(...),
            user: Optional[str] = Form(None),
            token: Optional[str] = Form(None),
            response_mode: Optional[str] = Form(None),
            extra: Optional[str] = Form(None)
        ):
            """
            分析PDF文件
            
            Args:
                file: 上传的PDF文件
                user: 用户标识（可选）
                token: 用户token（可选）
                response_mode: 响应模式 - blocking 或 streaming（可选）
                extra: 自定义参数，格式由服务自己定义（可选）
                
            Returns:
                统一格式的OCR分析结果
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
            if not file.filename.lower().endswith('.pdf'):
                return OCRResponse(
                    success=False,
                    message="只支持PDF文件",
                    data={},
                    processing_time=time.time() - start_time
                )
            
            # 创建临时工作目录
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                try:
                    # 保存上传的文件
                    pdf_path = temp_path / file.filename
                    with open(pdf_path, "wb") as buffer:
                        content = await file.read()
                        buffer.write(content)
                    
                    # 执行OCR分析
                    result = await self._analyze_pdf_file(pdf_path, temp_path)
                    
                    # 计算处理时间
                    processing_time = time.time() - start_time
                    
                    # 构建统一返回格式
                    return OCRResponse(
                        success=result["success"],
                        message=result["message"],
                        data={
                            "total_pages": result["total_pages"],
                            "ocr_raw_data": result["ocr_raw_data"],
                            "field_extraction_results": result["field_extraction_results"],
                            "combined_results": result["combined_results"]
                        },
                        processing_time=processing_time
                    )
                    
                except Exception as e:
                    error_msg = f"处理PDF文件时发生错误: {str(e)}"
                    print(f"❌ {error_msg}")
                    print(traceback.format_exc())
                    
                    return OCRResponse(
                        success=False,
                        message=error_msg,
                        data={
                            "total_pages": 0,
                            "ocr_raw_data": [],
                            "field_extraction_results": [],
                            "combined_results": None
                        },
                        processing_time=time.time() - start_time
                    )
    
    async def _analyze_pdf_file(self, pdf_path: Path, temp_dir: Path) -> Dict[str, Any]:
        """
        分析PDF文件的核心逻辑
        
        Args:
            pdf_path: PDF文件路径
            temp_dir: 临时工作目录
            
        Returns:
            分析结果字典
        """
        print(f"📄 开始分析PDF文件: {pdf_path.name}")
        
        # 提取PDF页面
        page_files = self._extract_pdf_pages(pdf_path, temp_dir)
        
        if not page_files:
            return {
                "success": False,
                "message": "PDF页面提取失败",
                "total_pages": 0,
                "ocr_raw_data": [],
                "field_extraction_results": []
            }
        
        print(f"📚 发现 {len(page_files)} 页，开始逐页分析...")
        
        # 处理每一页
        all_ocr_data = []
        all_field_results = []
        
        for i, page_file in enumerate(page_files, 1):
            print(f"🔍 处理第 {i}/{len(page_files)} 页...")
            
            try:
                # 为每页创建输出目录
                page_output_dir = temp_dir / f"page_{i:03d}_analysis"
                page_output_dir.mkdir(parents=True, exist_ok=True)
                
                # 使用OCR管道处理单页
                ocr_data, field_data = await self._process_single_page(
                    page_file, page_output_dir
                )
                
                # 添加页面信息
                ocr_data["page_number"] = i
                field_data["page_number"] = i
                
                all_ocr_data.append(ocr_data)
                all_field_results.append(field_data)
                
                print(f"✅ 第 {i} 页处理完成")
                
            except Exception as e:
                print(f"❌ 第 {i} 页处理失败: {str(e)}")
                # 添加空的结果以保持页面顺序
                all_ocr_data.append({
                    "page_number": i,
                    "error": str(e),
                    "dt_polys": [],
                    "rec_res": []
                })
                all_field_results.append({
                    "page_number": i,
                    "error": str(e),
                    "extracted_fields": {}
                })
        
        # 合并多页结果
        combined_results = self._combine_multi_page_results(all_ocr_data, all_field_results)
        
        return {
            "success": True,
            "message": f"成功处理 {len(page_files)} 页PDF文档",
            "total_pages": len(page_files),
            "ocr_raw_data": all_ocr_data,
            "field_extraction_results": all_field_results,
            "combined_results": combined_results
        }
    
    def _extract_pdf_pages(self, pdf_path: Path, output_dir: Path) -> List[Path]:
        """
        提取PDF的所有页面为单独的图像文件
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            
        Returns:
            提取的页面文件路径列表
        """
        try:
            # 转换PDF为图像列表
            images = pdf2image.convert_from_path(str(pdf_path), dpi=300)
            
            if not images:
                print("❌ PDF转换失败 - 无图像输出")
                return []
            
            # 创建页面目录
            pages_dir = output_dir / "extracted_pages"
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            page_files = []
            
            for i, image in enumerate(images, 1):
                # 保存每一页为PNG文件
                page_filename = f"page_{i:03d}.png"
                page_path = pages_dir / page_filename
                
                image.save(page_path, 'PNG')
                page_files.append(page_path)
            
            return page_files
            
        except Exception as e:
            print(f"❌ PDF页面提取失败: {e}")
            return []
    
    async def _process_single_page(self, page_file: Path, output_dir: Path) -> tuple:
        """
        处理单个页面
        
        Args:
            page_file: 页面文件路径
            output_dir: 输出目录
            
        Returns:
            (ocr_raw_data, field_extraction_results) 元组
        """
        # 初始化OCR管道（参考massive_pdf_processor的调用方式）
        print(f"🔍 [API调试] 输出目录: {output_dir}")
        print(f"🔍 [API调试] 输入文件: {page_file}")
        
        pipeline = OCRPipeline(
            output_dir=Path(output_dir)
        )
        
        # 运行完整管道
        print(f"🔄 [API调试] 开始OCR处理...")
        try:
            result = pipeline.run_pipeline(str(page_file))
            print(f"✅ [API调试] OCR处理完成")
        except Exception as e:
            print(f"❌ [API调试] OCR处理失败: {e}")
            raise e
        
        # 检查输出目录结构
        print(f"📁 [API调试] 检查输出目录结构:")
        if output_dir.exists():
            for item in sorted(output_dir.rglob('*')):
                if item.is_file():
                    print(f"   {item.relative_to(output_dir)} ({item.stat().st_size} bytes)")
        
        # 读取结果文件
        ocr_file = output_dir / "steps" / "step02" / "2.1_ocr_raw_data.json"
        field_file = output_dir / "steps" / "step06" / "6.3_field_extraction_results.json"
        
        print(f"🔍 [API调试] OCR文件路径: {ocr_file}")
        print(f"🔍 [API调试] 字段文件路径: {field_file}")
        
        ocr_data = {}
        field_data = {}
        
        # 读取OCR原始数据
        if ocr_file.exists():
            print(f"✅ [API调试] 找到OCR文件")
            with open(ocr_file, 'r', encoding='utf-8') as f:
                ocr_data = json.load(f)
            print(f"📊 [API调试] OCR数据: dt_polys={len(ocr_data.get('dt_polys', []))}, rec_res={len(ocr_data.get('rec_res', []))}")
        else:
            print(f"❌ [API调试] OCR数据文件不存在: {ocr_file}")
        
        # 读取字段提取结果
        if field_file.exists():
            print(f"✅ [API调试] 找到字段文件")
            with open(field_file, 'r', encoding='utf-8') as f:
                field_data = json.load(f)
            print(f"📋 [API调试] 字段数据: extracted_fields={len(field_data.get('extracted_fields', {}))}")
        else:
            print(f"❌ [API调试] 字段提取文件不存在: {field_file}")
        
        return ocr_data, field_data
    
    def _combine_multi_page_results(self, ocr_data_list: List[Dict], field_data_list: List[Dict]) -> Dict[str, Any]:
        """
        合并多页结果
        
        Args:
            ocr_data_list: 各页OCR数据列表
            field_data_list: 各页字段提取结果列表
            
        Returns:
            合并后的结果字典
        """
        combined = {
            "combined_timestamp": datetime.now().isoformat(),
            "total_pages": len(ocr_data_list),
            "combined_ocr_data": {
                "total_text_boxes": 0,
                "all_recognized_text": [],
                "confidence_summary": {
                    "min_confidence": 1.0,
                    "max_confidence": 0.0,
                    "avg_confidence": 0.0
                }
            },
            "combined_field_data": {
                "total_fields_extracted": 0,
                "all_extracted_fields": {},
                "field_sources": {}  # 记录每个字段来自哪一页
            }
        }
        
        # 合并OCR数据
        all_confidences = []
        for page_num, ocr_data in enumerate(ocr_data_list, 1):
            if "error" in ocr_data:
                continue
                
            # 合并文本框数量
            if "dt_polys" in ocr_data:
                combined["combined_ocr_data"]["total_text_boxes"] += len(ocr_data["dt_polys"])
            
            # 合并识别文本
            if "rec_res" in ocr_data:
                for text_info in ocr_data["rec_res"]:
                    if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                        text, confidence = text_info[0], text_info[1]
                        combined["combined_ocr_data"]["all_recognized_text"].append({
                            "text": text,
                            "confidence": confidence,
                            "page": page_num
                        })
                        all_confidences.append(confidence)
        
        # 计算置信度统计
        if all_confidences:
            combined["combined_ocr_data"]["confidence_summary"]["min_confidence"] = min(all_confidences)
            combined["combined_ocr_data"]["confidence_summary"]["max_confidence"] = max(all_confidences)
            combined["combined_ocr_data"]["confidence_summary"]["avg_confidence"] = sum(all_confidences) / len(all_confidences)
        
        # 合并字段提取数据
        for page_num, field_data in enumerate(field_data_list, 1):
            if "error" in field_data:
                continue
                
            if "extracted_fields" in field_data:
                for field_name, field_info in field_data["extracted_fields"].items():
                    # 如果字段已存在，创建列表保存多页数据
                    if field_name in combined["combined_field_data"]["all_extracted_fields"]:
                        existing = combined["combined_field_data"]["all_extracted_fields"][field_name]
                        if not isinstance(existing, list):
                            existing = [existing]
                        existing.append({**field_info, "source_page": page_num})
                        combined["combined_field_data"]["all_extracted_fields"][field_name] = existing
                    else:
                        combined["combined_field_data"]["all_extracted_fields"][field_name] = {
                            **field_info, 
                            "source_page": page_num
                        }
                    
                    # 记录字段来源页面
                    if field_name not in combined["combined_field_data"]["field_sources"]:
                        combined["combined_field_data"]["field_sources"][field_name] = []
                    combined["combined_field_data"]["field_sources"][field_name].append(page_num)
        
        # 统计总字段数
        combined["combined_field_data"]["total_fields_extracted"] = len(
            combined["combined_field_data"]["all_extracted_fields"]
        )
        
        return combined


def create_app():
    """创建API应用实例"""
    api_server = OCRAPIServer()
    return api_server.app


if __name__ == "__main__":
    print("🚀 启动 IBoxTech OCR分析API服务器...")
    print("📖 API文档地址: http://localhost:6001/docs")
    print("🔍 交互式文档: http://localhost:6001/redoc")
    
    app = create_app()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=6001,
        reload=False,  # 在生产环境中关闭reload
        log_level="info"
    )



