#!/usr/bin/env python3
"""
合并other_pdf中的A文件和其后续的所有连续B文件
"""
import re
import sys
from pathlib import Path
from datetime import datetime
import fitz  # PyMuPDF
import argparse

class ABFileMerger:
    """A文件和后续B文件合并器"""
    
    def __init__(self, other_dir, output_dir=None):
        self.other_dir = Path(other_dir)
        self.output_dir = Path(output_dir) if output_dir else self.other_dir.parent
        
        if not self.other_dir.exists():
            print(f"❌ 目录不存在: {self.other_dir}")
            sys.exit(1)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.output_dir / f"merge_ab_files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        self.stats = {
            'total_a_files': 0,
            'merged_files': 0,
            'a_only_files': 0,  # 只有A没有后续B的
            'errors': 0,
            'total_pages_merged': 0
        }
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message, flush=True)
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def extract_page_info(self, filename):
        """从文件名中提取基础名和页码"""
        # 匹配 "XXX_第N页A.pdf" 或 "XXX_第N页B.pdf"
        match = re.search(r'^(.+)_第(\d+)页([AB])\.pdf$', filename, re.IGNORECASE)
        if match:
            base_name = match.group(1)  # 例如：测试中心品质部原材料委单2025年3月份
            page_num = int(match.group(2))
            suffix = match.group(3).upper()
            return base_name, page_num, suffix
        return None, None, None
    
    def get_all_files_index(self):
        """建立文件索引：{(base_name, page_num): {'A': path, 'B': path}}"""
        from collections import defaultdict
        file_index = defaultdict(dict)
        
        pdf_files = list(self.other_dir.glob("*.pdf"))
        pdf_files.extend(list(self.other_dir.glob("*.PDF")))
        
        for pdf_file in pdf_files:
            base_name, page_num, suffix = self.extract_page_info(pdf_file.name)
            if base_name and page_num and suffix:
                key = (base_name, page_num)
                file_index[key][suffix] = pdf_file
        
        return file_index
    
    def find_consecutive_b_pages(self, file_index, base_name, start_page):
        """查找从start_page开始的所有连续B页"""
        consecutive_b_pages = []
        current_page = start_page + 1
        
        while True:
            key = (base_name, current_page)
            if key in file_index and 'B' in file_index[key]:
                consecutive_b_pages.append(file_index[key]['B'])
                current_page += 1
            else:
                break
        
        return consecutive_b_pages
    
    def merge_pdfs(self, pdf_paths, output_path):
        """合并多个PDF文件"""
        try:
            merged_doc = fitz.open()
            
            for pdf_path in pdf_paths:
                with fitz.open(pdf_path) as doc:
                    merged_doc.insert_pdf(doc)
            
            merged_doc.save(str(output_path))
            merged_doc.close()
            return True, len(pdf_paths)
        except Exception as e:
            return False, str(e)
    
    def run(self):
        """执行合并任务"""
        self.log("=" * 70)
        self.log("🚀 A文件与后续B文件合并工具")
        self.log("=" * 70)
        self.log(f"📂 输入目录: {self.other_dir}")
        self.log(f"📂 输出目录: {self.output_dir}")
        self.log("")
        
        # 建立文件索引
        self.log("🔍 正在建立文件索引...")
        file_index = self.get_all_files_index()
        
        # 找出所有A文件
        a_files = []
        for key, files in file_index.items():
            if 'A' in files:
                base_name, page_num = key
                a_files.append((base_name, page_num, files['A']))
        
        a_files.sort(key=lambda x: (x[0], x[1]))  # 按基础名和页码排序
        self.stats['total_a_files'] = len(a_files)
        
        self.log(f"✅ 找到 {len(a_files)} 个A文件")
        self.log("")
        self.log("🔄 开始合并处理...")
        self.log("")
        
        import time
        start_time = time.time()
        
        for i, (base_name, page_num, a_file_path) in enumerate(a_files, 1):
            file_start_time = time.time()
            self.log(f"[{i}/{len(a_files)}] 处理: {a_file_path.name}")
            
            # 查找后续的所有连续B页
            consecutive_b_pages = self.find_consecutive_b_pages(file_index, base_name, page_num)
            
            if consecutive_b_pages:
                self.log(f"  📄 找到 {len(consecutive_b_pages)} 个连续B页")
                for b_page in consecutive_b_pages:
                    self.log(f"     - {b_page.name}")
                
                # 合并A页和所有B页
                files_to_merge = [a_file_path] + consecutive_b_pages
                
                # 生成输出文件名：去掉A后缀，加上"2"
                # 例如：测试中心品质部原材料委单2025年3月份_第79页A.pdf 
                # -> 测试中心品质部原材料委单2025年3月份_第79页2.pdf
                output_filename = f"{base_name}_第{page_num}页2.pdf"
                output_path = self.output_dir / output_filename
                
                self.log(f"  🔧 合并 {len(files_to_merge)} 个文件到: {output_filename}")
                
                success, result = self.merge_pdfs(files_to_merge, output_path)
                
                if success:
                    self.stats['merged_files'] += 1
                    self.stats['total_pages_merged'] += result
                    file_time = time.time() - file_start_time
                    self.log(f"  ✅ 合并成功！包含 {result} 个文件 (耗时: {file_time:.2f}秒)")
                else:
                    self.stats['errors'] += 1
                    self.log(f"  ❌ 合并失败: {result}")
            else:
                # 只有A页，没有后续B页
                self.stats['a_only_files'] += 1
                self.log(f"  ℹ️  没有找到后续B页，跳过")
            
            # 进度统计
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(a_files) - i) * avg_time
            hours, remainder = divmod(remaining, 3600)
            minutes, seconds = divmod(remainder, 60)
            self.log(f"  📊 进度: {i}/{len(a_files)} ({i/len(a_files)*100:.1f}%) | "
                    f"已用时: {int(elapsed)}秒 | 预计剩余: {int(hours)}小时{int(minutes)}分钟")
            self.log("")
        
        total_time = time.time() - start_time
        
        self.log("=" * 70)
        self.log("📊 处理完成统计:")
        self.log(f"  总A文件数: {self.stats['total_a_files']}")
        self.log(f"  成功合并: {self.stats['merged_files']}")
        self.log(f"  只有A页: {self.stats['a_only_files']}")
        self.log(f"  错误数: {self.stats['errors']}")
        self.log(f"  合并的总页数: {self.stats['total_pages_merged']}")
        self.log(f"  总耗时: {int(total_time)}秒 ({total_time/60:.1f}分钟)")
        self.log(f"  日志文件: {self.log_file}")
        self.log("=" * 70)

def main():
    parser = argparse.ArgumentParser(description='合并A文件和其后续的所有连续B文件')
    parser.add_argument('--other', '-o', type=str, 
                       default='/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf/other_pdf',
                       help='other_pdf目录路径')
    parser.add_argument('--output', type=str,
                       default='/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf',
                       help='合并后PDF的输出目录路径')
    args = parser.parse_args()
    
    merger = ABFileMerger(args.other, args.output)
    
    try:
        merger.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
        sys.exit(1)

if __name__ == "__main__":
    main()

