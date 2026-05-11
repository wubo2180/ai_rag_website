#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移动B页的前序A页到other_pdf目录，并添加A后缀

作者：智能OCR系统
日期：2025-10-12
"""

import os
import sys
import shutil
import re
from pathlib import Path
from datetime import datetime


class PrecedingAPageMover:
    """前序A页移动器"""
    
    def __init__(self, input_dir, other_dir, search_dir=None):
        """
        初始化
        
        Args:
            input_dir: 主PDF文件目录
            other_dir: B页所在目录（也是A页要移动到的目录）
            search_dir: 搜索前序A页的目录（如果不提供，则使用input_dir）
        """
        self.input_dir = Path(input_dir)
        self.other_dir = Path(other_dir)
        self.search_dir = Path(search_dir) if search_dir else self.input_dir
        
        if not self.input_dir.exists():
            print(f"❌ 输入目录不存在: {self.input_dir}")
            sys.exit(1)
        
        if not self.other_dir.exists():
            print(f"❌ B页目录不存在: {self.other_dir}")
            sys.exit(1)
        
        # 初始化日志
        self.log_file = self.input_dir / f"move_preceding_a_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 统计信息
        self.stats = {
            'total_b_pages': 0,
            'found_preceding': 0,
            'moved_preceding': 0,
            'preceding_already_in_other': 0,
            'not_found_preceding': 0,
            'errors': 0
        }
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def extract_page_info_from_b_page(self, filename):
        """
        从B页文件名中提取基本信息和页码
        
        Args:
            filename: B页文件名（例如：测试中心品质部原材料（OA）2024年7月份_第10页B.pdf）
            
        Returns:
            tuple: (基础名称, B页页码) 或 (None, None)
        """
        # 匹配格式：xxx_第X页B.pdf
        match = re.search(r'(_第(\d+)页)B\.pdf$', filename, re.IGNORECASE)
        if match:
            # 提取基础名称（不包含"_第X页B"部分）
            base_name = filename[:match.start(1)]
            page_num = int(match.group(2))
            return base_name, page_num
        return None, None
    
    def run(self):
        """执行移动操作"""
        self.log("="*70)
        self.log("🚀 移动B页的前序A页工具（添加A后缀）")
        self.log("="*70)
        self.log(f"📂 主目录 (前序A页所在): {self.input_dir}")
        self.log(f"📂 目标目录 (移动到): {self.other_dir}")
        self.log("")
        
        # 获取other_dir中的所有B页文件
        b_page_files = list(self.other_dir.glob("*B.pdf"))
        b_page_files.extend(list(self.other_dir.glob("*B.PDF")))
        b_page_files = sorted(b_page_files, key=lambda x: x.name)
        
        self.stats['total_b_pages'] = len(b_page_files)
        
        if not b_page_files:
            self.log("❌ 在other_pdf目录中没有找到B页文件")
            return
        
        self.log(f"📁 找到 {len(b_page_files)} 个B页文件，开始查找并移动前序A页...")
        self.log("")
        
        for i, b_page_path in enumerate(b_page_files, 1):
            self.log(f"[{i}/{len(b_page_files)}] 处理B页: {b_page_path.name}")
            
            # 从B页文件名中提取信息
            base_name, b_page_num = self.extract_page_info_from_b_page(b_page_path.name)
            
            if base_name and b_page_num and b_page_num > 1:
                preceding_page_num = b_page_num - 1
                
                # 前序A页的原文件名（不带A后缀）
                preceding_filename_original = f"{base_name}_第{preceding_page_num}页.pdf"
                preceding_path_original = self.search_dir / preceding_filename_original
                
                # 前序A页的目标文件名（带A后缀）
                preceding_filename_with_a = f"{base_name}_第{preceding_page_num}页A.pdf"
                preceding_path_target = self.other_dir / preceding_filename_with_a
                
                # 检查前序A页是否已经在other_pdf中（可能已经带A后缀）
                if preceding_path_target.exists():
                    self.stats['preceding_already_in_other'] += 1
                    self.log(f"  ✓ 前序A页已在other_pdf中: {preceding_filename_with_a}")
                elif preceding_path_original.exists():
                    # 找到了前序A页，移动并重命名
                    self.stats['found_preceding'] += 1
                    try:
                        shutil.move(str(preceding_path_original), str(preceding_path_target))
                        self.stats['moved_preceding'] += 1
                        self.log(f"  ✅ 找到前序A页: {preceding_filename_original}")
                        self.log(f"  ➡️  已移动并重命名为: {self.other_dir.name}/{preceding_filename_with_a}")
                    except Exception as e:
                        self.stats['errors'] += 1
                        self.log(f"  ❌ 移动前序A页失败: {str(e)}")
                else:
                    self.stats['not_found_preceding'] += 1
                    self.log(f"  ⚠️  未找到前序A页: {preceding_filename_original}")
            else:
                self.stats['not_found_preceding'] += 1
                self.log(f"  ⚠️  无法解析B页文件名或为第1页: {b_page_path.name}")
            
            self.log("")
        
        # 输出统计信息
        self.log("="*70)
        self.log("📊 处理完成统计:")
        self.log(f"  B页总数: {self.stats['total_b_pages']}")
        self.log(f"  找到的前序A页: {self.stats['found_preceding']}")
        self.log(f"  移动的前序A页: {self.stats['moved_preceding']}")
        self.log(f"  前序A页已在other_pdf: {self.stats['preceding_already_in_other']}")
        self.log(f"  未找到前序A页: {self.stats['not_found_preceding']}")
        self.log(f"  错误数: {self.stats['errors']}")
        self.log(f"  日志文件: {self.log_file}")
        self.log("="*70)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='移动B页的前序A页到other_pdf目录，并添加A后缀',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s
  %(prog)s -i /path/to/main_dir -o /path/to/other_pdf
  
说明:
  工具会查找B页文件（例如：xxx_第10页B.pdf），
  找到其前序A页（例如：xxx_第9页.pdf），
  移动到other_pdf并重命名为（例如：xxx_第9页A.pdf）
        """
    )
    
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf',
        help='主PDF文件目录路径 (用于查找前序A页)'
    )
    parser.add_argument(
        '--other', '-o',
        type=str,
        default='/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf/other_pdf',
        help='B页和前序A页的目标目录路径'
    )
    parser.add_argument(
        '--search', '-s',
        type=str,
        default=None,
        help='搜索前序A页的目录路径（如果不提供，则使用主目录）'
    )
    
    args = parser.parse_args()
    
    # 创建并运行
    mover = PrecedingAPageMover(args.input, args.other, args.search)
    
    try:
        mover.run()
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

