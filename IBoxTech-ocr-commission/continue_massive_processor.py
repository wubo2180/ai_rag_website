#!/usr/bin/env python3
"""
继续大规模PDF批量处理程序 - 继续处理剩余的PDF文件
"""

import sys
import os
import json
import fitz
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.pipeline import OCRPipeline
from pdf2image import convert_from_path, pdfinfo_from_path

class ContinueMassivePDFProcessor:
    """继续大规模PDF批量处理器"""
    
    def __init__(self, input_dir: str = "data/input", existing_session_dir: str = "data/massive_output/session_20251012_210302"):
        """初始化处理器"""
        self.input_dir = Path(input_dir)
        self.session_dir = Path(existing_session_dir)
        
        if not self.session_dir.exists():
            raise ValueError(f"会话目录不存在: {self.session_dir}")
        
        # 设置日志
        self.setup_logging()
        
        # 加载现有进度
        self.load_existing_progress()
        
        # 线程锁
        self.stats_lock = threading.Lock()
        
        self.logger.info("🚀 继续大规模PDF批量处理")
        self.logger.info("=" * 80)
        self.logger.info(f"🔍 输入目录: {self.input_dir}")
        self.logger.info(f"📁 会话目录: {self.session_dir}")
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('continue_massive_processing.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_existing_progress(self):
        """加载现有进度"""
        progress_file = self.session_dir / "processing_progress.json"
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.stats = data.get("processing_statistics", {})
                self.processed_files = {item["file_name"] for item in data.get("file_results", [])}
        else:
            self.stats = {
                "total_files": 0,
                "processed_files": 0,
                "successful_files": 0,
                "failed_files": 0,
                "total_pages": 0,
                "start_time": None,
                "end_time": None
            }
            self.processed_files = set()
            
        self.logger.info(f"📊 已加载进度: {len(self.processed_files)} 个文件已处理")
        
    def get_pdf_page_count(self, pdf_path: Path) -> int:
        """获取PDF页数"""
        try:
            info = pdfinfo_from_path(pdf_path)
            return info['pages']
        except Exception as e:
            self.logger.error(f"❌ 获取PDF页数失败 {pdf_path.name}: {e}")
            return 1
            
    def is_already_processed(self, pdf_name: str) -> bool:
        """检查文件是否已经处理过"""
        return pdf_name in self.processed_files
        
    def process_single_page_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """处理单页PDF"""
        pdf_name = pdf_path.stem
        output_dir = self.session_dir / "single_page_results" / pdf_name
        
        try:
            start_time = time.time()
            self.logger.info(f"🔄 处理单页PDF: {pdf_name}")
            
            # 运行OCR管道
            pipeline = OCRPipeline(output_dir=Path(output_dir))
            result = pipeline.run_pipeline(str(pdf_path))
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            self.logger.info(f"✅ 单页PDF处理完成: {pdf_name} ({processing_time:.2f}秒)")
            
            return {
                "file_name": pdf_name,
                "file_path": str(pdf_path),
                "page_count": 1,
                "processing_type": "single_page",
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "status": "success",
                "pages_processed": [1],
                "error_message": None,
                "output_dir": str(output_dir),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ 单页PDF处理失败 {pdf_name}: {e}")
            return {
                "file_name": pdf_name,
                "file_path": str(pdf_path),
                "page_count": 1,
                "processing_type": "single_page",
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "status": "failed",
                "pages_processed": [],
                "error_message": str(e),
                "output_dir": str(output_dir),
                "end_time": datetime.fromtimestamp(time.time()).isoformat(),
                "processing_time": time.time() - start_time
            }
            
    def process_multi_page_pdf(self, pdf_path: Path, page_count: int) -> Dict[str, Any]:
        """处理多页PDF"""
        pdf_name = pdf_path.stem
        output_dir = self.session_dir / "multi_page_results" / pdf_name
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            start_time = time.time()
            self.logger.info(f"🔄 处理多页PDF: {pdf_name} ({page_count}页)")
            
            # 提取所有页面
            images = convert_from_path(pdf_path, dpi=300)
            temp_files = []
            processed_pages = []
            
            for page_num, image in enumerate(images, 1):
                try:
                    # 保存临时PNG文件
                    temp_png = output_dir / f"temp_page_{page_num:03d}.png"
                    image.save(temp_png, 'PNG')
                    temp_files.append(temp_png)
                    
                    # 处理这一页
                    page_output_dir = output_dir / f"page_{page_num:03d}_results"
                    pipeline = OCRPipeline(output_dir=Path(page_output_dir))
                    pipeline.run_pipeline(str(temp_png))
                    
                    processed_pages.append(page_num)
                    self.logger.info(f"✅ 页面 {page_num}/{page_count} 处理完成: {pdf_name}")
                    
                except Exception as e:
                    self.logger.error(f"❌ 页面 {page_num} 处理失败 {pdf_name}: {e}")
                    
            # 清理临时文件
            for temp_file in temp_files:
                try:
                    temp_file.unlink()
                except:
                    pass
                    
            end_time = time.time()
            processing_time = end_time - start_time
            
            self.logger.info(f"✅ 多页PDF处理完成: {pdf_name} ({len(processed_pages)}/{page_count}页, {processing_time:.2f}秒)")
            
            return {
                "file_name": pdf_name,
                "file_path": str(pdf_path),
                "page_count": page_count,
                "processing_type": "multi_page",
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "status": "success" if len(processed_pages) == page_count else "partial",
                "pages_processed": processed_pages,
                "error_message": None if len(processed_pages) == page_count else f"只处理了 {len(processed_pages)}/{page_count} 页",
                "output_dir": str(output_dir),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"❌ 多页PDF处理失败 {pdf_name}: {e}")
            return {
                "file_name": pdf_name,
                "file_path": str(pdf_path),
                "page_count": page_count,
                "processing_type": "multi_page",
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "status": "failed",
                "pages_processed": [],
                "error_message": str(e),
                "output_dir": str(output_dir),
                "end_time": datetime.fromtimestamp(time.time()).isoformat(),
                "processing_time": time.time() - start_time
            }
            
    def update_progress(self, result: Dict[str, Any]):
        """更新进度"""
        with self.stats_lock:
            self.stats["processed_files"] += 1
            if result["status"] == "success":
                self.stats["successful_files"] += 1
            else:
                self.stats["failed_files"] += 1
                
            self.stats["total_pages"] += len(result.get("pages_processed", []))
            
            # 保存进度
            self.save_progress(result)
            
    def save_progress(self, latest_result: Dict[str, Any]):
        """保存进度到文件"""
        progress_file = self.session_dir / "processing_progress.json"
        
        # 读取现有数据
        if progress_file.exists():
            with open(progress_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            data = {
                "session_info": {
                    "session_id": self.session_dir.name,
                    "start_time": datetime.now().isoformat(),
                    "output_directory": str(self.session_dir)
                },
                "file_results": []
            }
            
        # 更新统计信息
        data["session_info"]["last_update"] = datetime.now().isoformat()
        data["processing_statistics"] = self.stats.copy()
        data["processing_statistics"]["elapsed_time"] = time.time() - time.mktime(datetime.fromisoformat(data["session_info"]["start_time"]).timetuple()) if self.stats.get("start_time") else 0
        
        if self.stats["processed_files"] > 0:
            elapsed_minutes = data["processing_statistics"]["elapsed_time"] / 60
            data["processing_statistics"]["files_per_minute"] = self.stats["processed_files"] / elapsed_minutes if elapsed_minutes > 0 else 0
            data["processing_statistics"]["pages_per_minute"] = self.stats["total_pages"] / elapsed_minutes if elapsed_minutes > 0 else 0
        
        # 添加最新结果
        data["file_results"].append(latest_result)
        
        # 保存文件
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
    def process_remaining_files(self):
        """处理剩余文件"""
        # 扫描所有PDF文件
        pdf_files = list(self.input_dir.glob("*.pdf"))
        self.stats["total_files"] = len(pdf_files)
        self.stats["start_time"] = datetime.now().isoformat()
        
        self.logger.info(f"📊 总文件数: {len(pdf_files)}")
        self.logger.info(f"📊 已处理: {len(self.processed_files)}")
        
        # 过滤出未处理的文件
        remaining_files = [f for f in pdf_files if f.stem not in self.processed_files]
        self.logger.info(f"📊 剩余待处理: {len(remaining_files)}")
        
        if not remaining_files:
            self.logger.info("🎉 所有文件都已处理完成！")
            return
            
        # 处理剩余文件
        for i, pdf_path in enumerate(remaining_files, 1):
            try:
                self.logger.info(f"🔄 [{i}/{len(remaining_files)}] 开始处理: {pdf_path.name}")
                
                # 获取页数
                page_count = self.get_pdf_page_count(pdf_path)
                
                # 根据页数选择处理方式
                if page_count == 1:
                    result = self.process_single_page_pdf(pdf_path)
                else:
                    result = self.process_multi_page_pdf(pdf_path, page_count)
                    
                # 更新进度
                self.update_progress(result)
                
                # 显示进度
                progress_percent = (self.stats["processed_files"] / len(remaining_files)) * 100
                self.logger.info(f"📊 进度: {self.stats['processed_files']}/{len(remaining_files)} ({progress_percent:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"❌ 处理文件失败 {pdf_path.name}: {e}")
                continue
                
        # 完成处理
        self.stats["end_time"] = datetime.now().isoformat()
        self.logger.info("🎉 批量处理完成！")
        self.logger.info(f"📊 最终统计: 成功 {self.stats['successful_files']}, 失败 {self.stats['failed_files']}")

def main():
    """主函数"""
    try:
        processor = ContinueMassivePDFProcessor()
        processor.process_remaining_files()
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断处理")
    except Exception as e:
        print(f"❌ 程序错误: {e}")

if __name__ == "__main__":
    main()







