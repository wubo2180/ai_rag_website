#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
给PDF文件名添加B后缀
在文件名末尾（扩展名前）添加"B"标识

作者：智能OCR系统
日期：2025-10-12
"""

import os
import sys
from pathlib import Path
import argparse
from datetime import datetime


class FileSuffixAdder:
    """文件后缀添加器"""
    
    def __init__(self, target_dir, suffix="B"):
        """
        初始化
        
        Args:
            target_dir: 目标目录
            suffix: 要添加的后缀（默认为"B"）
        """
        self.target_dir = Path(target_dir)
        self.suffix = suffix
        
        if not self.target_dir.exists():
            print(f"❌ 目录不存在: {self.target_dir}")
            sys.exit(1)
        
        # 初始化日志
        self.log_file = self.target_dir.parent / f"add_suffix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'renamed': 0,
            'skipped': 0,
            'errors': 0
        }
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def add_suffix_to_filename(self, filepath):
        """
        给文件名添加后缀
        
        Args:
            filepath: 文件路径
            
        Returns:
            Path: 新的文件路径
        """
        stem = filepath.stem  # 文件名（不含扩展名）
        ext = filepath.suffix  # 扩展名
        
        # 如果已经有B后缀，跳过
        if stem.endswith(self.suffix):
            return None
        
        # 新文件名：原文件名 + B + 扩展名
        new_name = f"{stem}{self.suffix}{ext}"
        new_path = filepath.parent / new_name
        
        return new_path
    
    def run(self):
        """执行重命名"""
        self.log("="*70)
        self.log(f"🚀 PDF文件添加'{self.suffix}'后缀工具")
        self.log("="*70)
        self.log(f"📂 目标目录: {self.target_dir}")
        self.log("")
        
        # 获取所有PDF文件
        pdf_files = list(self.target_dir.glob("*.pdf"))
        pdf_files.extend(list(self.target_dir.glob("*.PDF")))
        pdf_files = sorted(pdf_files, key=lambda x: x.name)
        
        self.stats['total_files'] = len(pdf_files)
        
        if not pdf_files:
            self.log("❌ 目录中没有找到PDF文件")
            return
        
        self.log(f"📁 找到 {len(pdf_files)} 个PDF文件")
        self.log("🔄 开始重命名...")
        self.log("")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            self.log(f"[{i}/{len(pdf_files)}] 处理: {pdf_file.name}")
            
            # 生成新文件名
            new_path = self.add_suffix_to_filename(pdf_file)
            
            if new_path is None:
                self.log(f"  ⏭️  跳过（已有'{self.suffix}'后缀）")
                self.stats['skipped'] += 1
                self.log("")
                continue
            
            # 检查新文件名是否已存在
            if new_path.exists():
                self.log(f"  ⚠️  跳过（目标文件已存在）: {new_path.name}")
                self.stats['skipped'] += 1
                self.log("")
                continue
            
            # 重命名
            try:
                pdf_file.rename(new_path)
                self.log(f"  ✅ 重命名为: {new_path.name}")
                self.stats['renamed'] += 1
            except Exception as e:
                self.log(f"  ❌ 重命名失败: {str(e)}")
                self.stats['errors'] += 1
            
            self.log("")
        
        # 输出统计信息
        self.log("="*70)
        self.log("📊 处理完成统计:")
        self.log(f"  总文件数: {self.stats['total_files']}")
        self.log(f"  已重命名: {self.stats['renamed']}")
        self.log(f"  已跳过: {self.stats['skipped']}")
        self.log(f"  错误数: {self.stats['errors']}")
        self.log(f"  日志文件: {self.log_file}")
        self.log("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='PDF文件添加B后缀工具 - 在文件名末尾添加标识',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -d /path/to/other_pdf
  %(prog)s -d /path/to/other_pdf -s "B"
  
说明:
  工具会将 "文件名.pdf" 重命名为 "文件名B.pdf"
        """
    )
    
    parser.add_argument(
        '--dir', '-d',
        required=True,
        help='目标目录路径'
    )
    parser.add_argument(
        '--suffix', '-s',
        default='B',
        help='要添加的后缀 (默认: B)'
    )
    
    args = parser.parse_args()
    
    # 验证目录
    if not os.path.exists(args.dir):
        print(f"❌ 目录不存在: {args.dir}")
        sys.exit(1)
    
    if not os.path.isdir(args.dir):
        print(f"❌ 路径不是目录: {args.dir}")
        sys.exit(1)
    
    # 创建并运行
    adder = FileSuffixAdder(
        target_dir=args.dir,
        suffix=args.suffix
    )
    
    try:
        adder.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

