#!/usr/bin/env python3
"""
PDF分解工具
将包含多个表格的PDF文件分解为单个页面的文件
作者：智能OCR系统
日期：2025-09-19
"""

import os
import sys
import fitz  # PyMuPDF
from pathlib import Path
import argparse
from datetime import datetime


class PDFSplitter:
    def __init__(self, input_dir, output_dir):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.processed_count = 0
        self.error_count = 0
        self.total_pages = 0
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日志
        self.log_file = self.output_dir / f"split_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def sanitize_filename(self, filename):
        """清理文件名，移除不安全字符"""
        # 移除或替换不安全字符
        unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in unsafe_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 200:
            filename = filename[:200]
            
        return filename
    
    def split_pdf(self, pdf_path):
        """分解单个PDF文件"""
        try:
            self.log(f"正在处理: {pdf_path.name}")
            
            # 打开PDF文档
            doc = fitz.open(str(pdf_path))
            page_count = len(doc)
            
            if page_count == 0:
                self.log(f"⚠️  警告: {pdf_path.name} 没有页面")
                return
            
            # 获取文件名（不包含扩展名）
            base_name = pdf_path.stem
            
            # 为每一页创建单独的PDF
            for page_num in range(page_count):
                try:
                    # 创建新的PDF文档
                    new_doc = fitz.open()
                    
                    # 复制页面
                    new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
                    
                    # 生成输出文件名
                    if page_count == 1:
                        # 如果只有一页，不添加页码后缀
                        output_name = f"{base_name}.pdf"
                    else:
                        # 多页时添加页码后缀
                        output_name = f"{base_name}_第{page_num + 1}页.pdf"
                    
                    # 清理文件名
                    output_name = self.sanitize_filename(output_name)
                    output_path = self.output_dir / output_name
                    
                    # 如果文件已存在，添加序号避免覆盖
                    counter = 1
                    original_output_path = output_path
                    while output_path.exists():
                        name_parts = original_output_path.stem, counter, original_output_path.suffix
                        output_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                        output_path = self.output_dir / output_name
                        counter += 1
                    
                    # 保存新PDF
                    new_doc.save(str(output_path))
                    new_doc.close()
                    
                    self.total_pages += 1
                    self.log(f"  ✅ 第{page_num + 1}页 -> {output_name}")
                    
                except Exception as e:
                    self.log(f"  ❌ 处理第{page_num + 1}页时出错: {str(e)}")
                    self.error_count += 1
            
            doc.close()
            self.processed_count += 1
            self.log(f"✅ 完成处理 {pdf_path.name} ({page_count}页)")
            
        except Exception as e:
            self.log(f"❌ 处理文件 {pdf_path.name} 时出错: {str(e)}")
            self.error_count += 1
    
    def get_pdf_files(self):
        """获取输入目录中的所有PDF文件"""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        pdf_files.extend(list(self.input_dir.glob("*.PDF")))  # 包含大写扩展名
        return sorted(pdf_files)
    
    def run(self):
        """执行PDF分解"""
        self.log("🚀 开始PDF分解任务")
        self.log(f"输入目录: {self.input_dir}")
        self.log(f"输出目录: {self.output_dir}")
        
        # 获取所有PDF文件
        pdf_files = self.get_pdf_files()
        
        if not pdf_files:
            self.log("❌ 在输入目录中没有找到PDF文件")
            return
        
        self.log(f"找到 {len(pdf_files)} 个PDF文件")
        
        # 处理每个PDF文件
        for i, pdf_file in enumerate(pdf_files, 1):
            self.log(f"\n📄 [{i}/{len(pdf_files)}] 处理文件: {pdf_file.name}")
            self.split_pdf(pdf_file)
        
        # 输出统计信息
        self.log("\n" + "="*60)
        self.log("📊 分解完成统计:")
        self.log(f"  总文件数: {len(pdf_files)}")
        self.log(f"  成功处理: {self.processed_count}")
        self.log(f"  失败文件: {self.error_count}")
        self.log(f"  总页面数: {self.total_pages}")
        self.log(f"  日志文件: {self.log_file}")
        self.log("="*60)


def main():
    parser = argparse.ArgumentParser(description='PDF分解工具 - 将多页PDF分解为单页PDF')
    parser.add_argument(
        '--input', '-i',
        default='/Users/wenzhicao/Documents/WorkSpace/IBoxTech-data/resource/IBoxTech_pdf',
        help='输入PDF文件目录路径 (默认: resource/IBoxTech_pdf)'
    )
    parser.add_argument(
        '--output', '-o',
        default='/Users/wenzhicao/Documents/WorkSpace/IBoxTech-data/resource/IBoxTech_single_pdf',
        help='输出目录路径 (默认: resource/IBoxTech_single_pdf)'
    )
    parser.add_argument(
        '--clean', '-c',
        action='store_true',
        help='清空输出目录后再开始处理'
    )
    
    args = parser.parse_args()
    
    # 验证输入目录
    if not os.path.exists(args.input):
        print(f"❌ 输入目录不存在: {args.input}")
        sys.exit(1)
    
    # 清空输出目录（如果指定）
    if args.clean and os.path.exists(args.output):
        import shutil
        print(f"🧹 清空输出目录: {args.output}")
        shutil.rmtree(args.output)
    
    # 创建并运行PDF分解器
    splitter = PDFSplitter(args.input, args.output)
    splitter.run()


if __name__ == "__main__":
    main()
