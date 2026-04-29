#!/usr/bin/env python3
"""
大规模PDF批量处理程序 - 后台处理所有input目录中的PDF文件
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
from pdf2image import convert_from_path

class MassivePDFProcessor:
    """大规模PDF批量处理器"""
    
    def __init__(self, input_dir: str = "data/input", output_base_dir: str = "data/massive_output"):
        """初始化处理器"""
        self.input_dir = Path(input_dir)
        self.output_base_dir = Path(output_base_dir)
        self.session_dir = self.output_base_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self.setup_logging()
        
        # 统计信息
        self.stats = {
            "total_files": 0,
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "total_pages": 0,
            "start_time": None,
            "end_time": None
        }
        
        # 线程锁
        self.stats_lock = threading.Lock()
        self.progress_lock = threading.Lock()
        
    def setup_logging(self):
        """设置日志系统"""
        log_file = self.session_dir / "processing.log"
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def get_pdf_page_count(self, pdf_path: Path) -> int:
        """获取PDF页数"""
        try:
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            doc.close()
            return page_count
        except Exception as e:
            self.logger.warning(f"无法获取PDF页数 {pdf_path}: {e}")
            return 1
    
    def scan_input_files(self) -> List[Dict[str, Any]]:
        """扫描输入目录中的所有PDF文件"""
        pdf_files = []
        
        self.logger.info(f"🔍 扫描输入目录: {self.input_dir}")
        
        for pdf_path in self.input_dir.glob("*.pdf"):
            if pdf_path.is_file():
                page_count = self.get_pdf_page_count(pdf_path)
                
                pdf_files.append({
                    "path": pdf_path,
                    "name": pdf_path.stem,
                    "size": pdf_path.stat().st_size,
                    "page_count": page_count,
                    "processing_type": "multi_page" if page_count > 1 else "single_page"
                })
        
        # 按文件大小排序（小文件优先）
        pdf_files.sort(key=lambda x: x["size"])
        
        self.stats["total_files"] = len(pdf_files)
        total_pages = sum(f["page_count"] for f in pdf_files)
        self.stats["total_pages"] = total_pages
        
        self.logger.info(f"📊 扫描完成: {len(pdf_files)} 个PDF文件, 总计 {total_pages} 页")
        
        # 保存文件清单
        manifest_path = self.session_dir / "file_manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump({
                "scan_time": datetime.now().isoformat(),
                "total_files": len(pdf_files),
                "total_pages": total_pages,
                "files": [
                    {
                        "name": f["name"],
                        "path": str(f["path"]),
                        "size": f["size"],
                        "page_count": f["page_count"],
                        "processing_type": f["processing_type"]
                    }
                    for f in pdf_files
                ]
            }, f, ensure_ascii=False, indent=2)
        
        return pdf_files
    
    def process_single_pdf(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理单个PDF文件"""
        pdf_path = file_info["path"]
        pdf_name = file_info["name"]
        page_count = file_info["page_count"]
        
        start_time = time.time()
        result = {
            "file_name": pdf_name,
            "file_path": str(pdf_path),
            "page_count": page_count,
            "processing_type": file_info["processing_type"],
            "start_time": datetime.now().isoformat(),
            "status": "processing",
            "pages_processed": [],
            "error_message": None
        }
        
        try:
            if page_count == 1:
                # 单页PDF直接处理
                output_dir = self.session_dir / "single_page_results" / pdf_name
                result["output_dir"] = str(output_dir)
                
                pipeline = OCRPipeline(
                    output_dir=Path(output_dir)
                )
                
                pipeline.run_pipeline(str(pdf_path))
                
                result["pages_processed"] = [1]
                result["status"] = "success"
                
            else:
                # 多页PDF需要分解处理
                output_dir = self.session_dir / "multi_page_results" / pdf_name
                result["output_dir"] = str(output_dir)
                
                # 分解PDF为图片
                temp_dir = output_dir / "temp_pages"
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                pages = convert_from_path(str(pdf_path), dpi=150)
                
                for i, page in enumerate(pages, 1):
                    page_path = temp_dir / f"page_{i:03d}.png"
                    page.save(page_path, 'PNG')
                    
                    # 处理每一页
                    page_output_dir = output_dir / f"page_{i:03d}_results"
                    
                    pipeline = OCRPipeline(
                        output_dir=Path(page_output_dir)
                    )
                    
                    pipeline.run_pipeline(str(page_path))
                    
                    result["pages_processed"].append(i)
                
                # 清理临时文件
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
                result["status"] = "success"
        
        except Exception as e:
            result["status"] = "failed"
            result["error_message"] = str(e)
            self.logger.error(f"处理文件失败 {pdf_name}: {e}")
        
        finally:
            end_time = time.time()
            result["end_time"] = datetime.now().isoformat()
            result["processing_time"] = end_time - start_time
            
            # 更新统计信息
            with self.stats_lock:
                self.stats["processed_files"] += 1
                if result["status"] == "success":
                    self.stats["successful_files"] += 1
                else:
                    self.stats["failed_files"] += 1
                
                # 更新进度
                progress = (self.stats["processed_files"] / self.stats["total_files"]) * 100
                
                with self.progress_lock:
                    print(f"\r进度: {self.stats['processed_files']}/{self.stats['total_files']} "
                          f"({progress:.1f}%) - 成功: {self.stats['successful_files']} "
                          f"失败: {self.stats['failed_files']}", end='', flush=True)
        
        return result
    
    def save_progress(self, results: List[Dict[str, Any]]):
        """保存进度报告"""
        summary = {
            "session_info": {
                "session_id": self.session_dir.name,
                "start_time": self.stats["start_time"],
                "last_update": datetime.now().isoformat(),
                "output_directory": str(self.session_dir)
            },
            "processing_statistics": self.stats.copy(),
            "file_results": results
        }
        
        # 计算处理速度
        if self.stats["start_time"]:
            elapsed = (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).total_seconds()
            summary["processing_statistics"]["elapsed_time"] = elapsed
            if elapsed > 0:
                summary["processing_statistics"]["files_per_minute"] = (self.stats["processed_files"] / elapsed) * 60
                summary["processing_statistics"]["pages_per_minute"] = (
                    sum(len(r.get("pages_processed", [])) for r in results) / elapsed
                ) * 60
        
        # 保存进度报告
        progress_file = self.session_dir / "processing_progress.json"
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
    
    def run_batch_processing(self, max_workers: int = 4):
        """运行批量处理"""
        self.logger.info("🚀 开始大规模PDF批量处理")
        self.logger.info("=" * 80)
        
        self.stats["start_time"] = datetime.now().isoformat()
        
        # 扫描文件
        pdf_files = self.scan_input_files()
        
        if not pdf_files:
            self.logger.warning("❌ 未找到PDF文件")
            return
        
        self.logger.info(f"🔧 使用 {max_workers} 个工作线程并行处理")
        self.logger.info("=" * 80)
        
        results = []
        
        # 使用线程池并行处理
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self.process_single_pdf, file_info): file_info
                for file_info in pdf_files
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # 每处理100个文件保存一次进度
                    if len(results) % 100 == 0:
                        self.save_progress(results)
                        
                except Exception as e:
                    self.logger.error(f"处理任务异常 {file_info['name']}: {e}")
                    results.append({
                        "file_name": file_info["name"],
                        "status": "failed",
                        "error_message": str(e)
                    })
        
        print()  # 换行
        
        # 处理完成
        self.stats["end_time"] = datetime.now().isoformat()
        self.save_progress(results)
        
        # 生成最终报告
        self.generate_final_report(results)
        
        self.logger.info("=" * 80)
        self.logger.info("🎉 批量处理完成!")
        self.logger.info("=" * 80)
        self.logger.info(f"📊 处理统计:")
        self.logger.info(f"  📄 总文件数: {self.stats['total_files']}")
        self.logger.info(f"  ✅ 成功: {self.stats['successful_files']}")
        self.logger.info(f"  ❌ 失败: {self.stats['failed_files']}")
        self.logger.info(f"  📃 总页数: {self.stats['total_pages']}")
        self.logger.info(f"📁 输出目录: {self.session_dir}")
        
    def generate_final_report(self, results: List[Dict[str, Any]]):
        """生成最终报告"""
        report_path = self.session_dir / "final_report.json"
        
        # 统计信息
        successful_results = [r for r in results if r.get("status") == "success"]
        failed_results = [r for r in results if r.get("status") == "failed"]
        
        # 处理时间统计
        processing_times = [r.get("processing_time", 0) for r in successful_results if r.get("processing_time")]
        avg_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        final_report = {
            "session_summary": {
                "session_id": self.session_dir.name,
                "start_time": self.stats["start_time"],
                "end_time": self.stats["end_time"],
                "total_processing_time": (
                    datetime.fromisoformat(self.stats["end_time"]) - 
                    datetime.fromisoformat(self.stats["start_time"])
                ).total_seconds(),
                "output_directory": str(self.session_dir)
            },
            "processing_statistics": {
                "total_files": self.stats["total_files"],
                "successful_files": self.stats["successful_files"],
                "failed_files": self.stats["failed_files"],
                "success_rate": (self.stats["successful_files"] / self.stats["total_files"]) * 100,
                "total_pages": self.stats["total_pages"],
                "average_time_per_file": avg_time
            },
            "successful_files": len(successful_results),
            "failed_files": len(failed_results),
            "failure_summary": [
                {
                    "file_name": r["file_name"],
                    "error": r.get("error_message", "Unknown error")
                }
                for r in failed_results[:50]  # 只显示前50个失败案例
            ] if failed_results else [],
            "processing_results": results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(final_report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"📋 最终报告已保存: {report_path}")

def main():
    """主程序"""
    processor = MassivePDFProcessor()
    
    # 设置并行度（根据系统性能调整）
    max_workers = min(8, os.cpu_count() or 1)
    
    try:
        processor.run_batch_processing(max_workers=max_workers)
    except KeyboardInterrupt:
        processor.logger.info("\n⚠️  用户中断处理")
        processor.save_progress([])
    except Exception as e:
        processor.logger.error(f"❌ 处理过程出现异常: {e}")
        raise

if __name__ == "__main__":
    main()
