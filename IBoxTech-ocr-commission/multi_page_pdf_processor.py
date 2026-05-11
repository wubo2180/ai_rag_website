#!/usr/bin/env python3
"""
多页PDF处理器 - 自动处理单个PDF文件的所有页面
"""

import sys
import time
from pathlib import Path
import json
from datetime import datetime
import pdf2image

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入模块
from config.settings import DEVELOPMENT_CONFIG
from core.pipeline import OCRPipeline
import tempfile
import shutil

class MultiPagePDFProcessor:
    """多页PDF处理器"""
    
    def __init__(self, config=None):
        """初始化处理器"""
        self.config = config or DEVELOPMENT_CONFIG
        self.processed_pages = []
        self.failed_pages = []
        self.total_start_time = None
        
    def extract_pdf_pages(self, pdf_path: Path, output_dir: Path) -> list:
        """
        提取PDF的所有页面为单独的图像文件
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
            
        Returns:
            提取的页面文件路径列表
        """
        print(f"📄 分析PDF文件: {pdf_path}")
        
        try:
            # 转换PDF为图像列表
            images = pdf2image.convert_from_path(str(pdf_path), dpi=300)
            
            if not images:
                print("❌ PDF转换失败 - 无图像输出")
                return []
            
            print(f"📚 发现 {len(images)} 页")
            
            # 创建临时目录存储各页面
            pages_dir = output_dir / "extracted_pages"
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            page_files = []
            
            for i, image in enumerate(images, 1):
                # 保存每一页为PNG文件
                page_filename = f"page_{i:03d}.png"
                page_path = pages_dir / page_filename
                
                image.save(page_path, 'PNG')
                page_files.append(page_path)
                
                print(f"  📃 页面 {i}: {page_path.name}")
            
            return page_files
            
        except Exception as e:
            print(f"❌ PDF页面提取失败: {e}")
            return []
    
    def process_single_page(self, page_file: Path, page_number: int, output_dir: Path) -> dict:
        """
        处理单个页面
        
        Args:
            page_file: 页面文件路径
            page_number: 页面编号
            output_dir: 输出目录
            
        Returns:
            处理结果字典
        """
        start_time = time.time()
        
        try:
            # 为每个页面创建独立的输出目录
            page_output_dir = output_dir / f"page_{page_number:03d}_results"
            
            # 更新配置的输出目录
            page_config = self.config
            page_config.output_dir = page_output_dir
            
            # 初始化流水线
            pipeline = OCRPipeline(config=page_config)
            
            print(f"  🚀 开始处理第 {page_number} 页")
            
            # 运行完整流水线（注意：这里我们直接传入PNG文件，Step1会处理）
            results = pipeline.run_pipeline(str(page_file))
            
            processing_time = time.time() - start_time
            
            # 收集结果统计
            result_summary = {
                'page_number': page_number,
                'file': str(page_file),
                'status': 'success',
                'processing_time': processing_time,
                'output_dir': str(page_output_dir),
                'steps_completed': list(results.get('step_results', {}).keys()),
                'total_execution_time': results.get('total_execution_time', 0)
            }
            
            # 尝试获取识别的文本数量（如果Step2完成了）
            if 'execution_stats' in results:
                result_summary['execution_stats'] = results['execution_stats']
            
            print(f"  ✅ 第 {page_number} 页处理完成 ({processing_time:.1f}s)")
            
            return result_summary
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            print(f"  ❌ 第 {page_number} 页处理失败: {error_msg}")
            
            return {
                'page_number': page_number,
                'file': str(page_file),
                'status': 'failed',
                'processing_time': processing_time,
                'error': error_msg
            }
    
    def process_multi_page_pdf(self, pdf_path: str, output_dir: str = None):
        """
        处理多页PDF文件
        
        Args:
            pdf_path: PDF文件路径
            output_dir: 输出目录
        """
        self.total_start_time = time.time()
        
        print("🚀 多页PDF处理器")
        print("=" * 60)
        
        # 设置路径
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            print(f"❌ PDF文件不存在: {pdf_file}")
            return
        
        if output_dir is None:
            output_path = Path("data/multi_page_output") / f"{pdf_file.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            output_path = Path(output_dir)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 输入文件: {pdf_file}")
        print(f"📁 输出目录: {output_path}")
        
        # 第1步：提取PDF页面
        print(f"\n🔍 第1步：提取PDF页面")
        print("-" * 40)
        
        page_files = self.extract_pdf_pages(pdf_file, output_path)
        
        if not page_files:
            print("❌ 未能提取PDF页面")
            return
        
        # 第2步：逐页处理
        print(f"\n🔄 第2步：逐页OCR处理")
        print("-" * 40)
        
        page_results = []
        successful_pages = 0
        failed_pages = 0
        
        for i, page_file in enumerate(page_files, 1):
            print(f"\n📄 处理页面 {i}/{len(page_files)}")
            
            try:
                result = self.process_single_page(page_file, i, output_path)
                page_results.append(result)
                
                if result['status'] == 'success':
                    successful_pages += 1
                    self.processed_pages.append(result)
                else:
                    failed_pages += 1
                    self.failed_pages.append(result)
                    
            except Exception as e:
                error_result = {
                    'page_number': i,
                    'file': str(page_file),
                    'status': 'failed',
                    'error': str(e),
                    'processing_time': 0
                }
                page_results.append(error_result)
                failed_pages += 1
                self.failed_pages.append(error_result)
                print(f"  ❌ 页面处理失败: {e}")
        
        # 第3步：生成汇总报告
        total_time = time.time() - self.total_start_time
        
        print(f"\n📊 第3步：生成汇总报告")
        print("-" * 40)
        
        # 创建汇总报告
        summary = {
            'pdf_processing_summary': {
                'input_file': str(pdf_file),
                'start_time': datetime.fromtimestamp(self.total_start_time).isoformat(),
                'end_time': datetime.now().isoformat(),
                'total_processing_time': total_time,
                'total_pages': len(page_files),
                'successful_pages': successful_pages,
                'failed_pages': failed_pages,
                'success_rate': successful_pages / len(page_files) * 100 if page_files else 0,
                'average_time_per_page': total_time / len(page_files) if page_files else 0
            },
            'page_results': page_results
        }
        
        # 保存汇总报告
        report_file = output_path / "multi_page_processing_summary.json"
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️  保存汇总报告失败: {e}")
        
        # 清理临时页面文件
        pages_dir = output_path / "extracted_pages"
        if pages_dir.exists():
            try:
                shutil.rmtree(pages_dir)
                print("🧹 清理临时页面文件")
            except Exception as e:
                print(f"⚠️  清理临时文件失败: {e}")
        
        # 打印最终统计
        print("\n" + "=" * 60)
        print("🎉 多页PDF处理完成!")
        print("=" * 60)
        print(f"📊 处理统计:")
        print(f"  📄 总页数: {len(page_files)}")
        print(f"  ✅ 成功页面: {successful_pages}")
        print(f"  ❌ 失败页面: {failed_pages}")
        print(f"  📈 成功率: {successful_pages/len(page_files)*100:.1f}%" if page_files else "0%")
        print(f"  ⏱️  总耗时: {total_time:.1f}秒")
        print(f"  📄 平均每页: {total_time/len(page_files):.1f}秒" if page_files else "")
        print(f"📋 处理报告: {report_file}")
        print(f"📁 输出目录: {output_path}")
        print("=" * 60)


def main():
    """主函数"""
    print("V3 多页PDF处理工具")
    print("=" * 50)
    
    try:
        # 获取输入参数
        pdf_file = input("请输入PDF文件路径: ").strip()
        if not pdf_file:
            print("❌ 请提供PDF文件路径")
            return
        
        # 验证文件存在
        if not Path(pdf_file).exists():
            print(f"❌ 文件不存在: {pdf_file}")
            return
        
        # 询问是否开始处理
        confirm = input(f"\n确认处理PDF文件: {pdf_file}? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("👋 取消处理")
            return
            
    except KeyboardInterrupt:
        print("\n👋 退出")
        return
    
    # 开始处理
    try:
        processor = MultiPagePDFProcessor(DEVELOPMENT_CONFIG)
        processor.process_multi_page_pdf(pdf_file)
    except KeyboardInterrupt:
        print("\n\n⚠️  处理中断")
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
