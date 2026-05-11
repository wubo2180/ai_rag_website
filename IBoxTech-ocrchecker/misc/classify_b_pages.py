#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF B页识别与移动工具（简化版）
只做一件事：识别不包含"委托部门"、"委托人"、"委托日期"的B页，并移动到other_pdf

作者：智能OCR系统
日期：2025-10-11
"""

import os
import sys
import io
from pathlib import Path
import argparse
from datetime import datetime
import shutil
import re

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import cv2

try:
    from paddleocr import PaddleOCR
except ImportError:
    print("❌ 错误：未安装PaddleOCR")
    print("请运行: pip install paddleocr")
    sys.exit(1)


class BPageClassifier:
    """B页识别器"""
    
    def __init__(self, input_dir, other_dir=None):
        """
        初始化识别器
        
        Args:
            input_dir: 输入PDF文件目录
            other_dir: B页输出目录（默认为input_dir/other_pdf）
        """
        self.input_dir = Path(input_dir)
        self.other_dir = Path(other_dir) if other_dir else self.input_dir / "other_pdf"
        
        # 关键词列表
        self.keywords = ["委托部门", "委托人", "委托日期"]
        
        # 创建输出目录
        self.other_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化日志
        self.log_file = self.input_dir / f"classify_b_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        # 初始化OCR引擎
        self.log("🚀 正在初始化PaddleOCR引擎...")
        try:
            self.ocr_engine = PaddleOCR(lang='ch')
            self.log("✅ PaddleOCR引擎初始化成功")
            self.log("⚠️  注意：OCR模型已加载，处理过程中不会重复加载")
        except Exception as e:
            self.log(f"❌ PaddleOCR初始化失败：{str(e)}")
            sys.exit(1)
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'a_pages': 0,
            'b_pages': 0,
            'moved_to_other': 0,
            'errors': 0
        }
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_message + '\n')
    
    def check_pdf_is_a_page(self, pdf_path):
        """
        检查PDF是否为A页（包含关键词）
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            tuple: (is_a_page, found_keywords) - 是否为A页和找到的关键词列表
        """
        try:
            doc = fitz.open(str(pdf_path))
            
            # 只检查第一页
            if len(doc) > 0:
                page = doc[0]
                
                # 将PDF页面转换为图片
                mat = fitz.Matrix(2.0, 2.0)  # 放大2倍提高识别精度
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                
                # 转换为PIL图像
                image = Image.open(io.BytesIO(img_data))
                
                # 转换为OpenCV格式
                img_array = np.array(image)
                if len(img_array.shape) == 3:
                    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
                
                # 执行OCR识别（使用predict方法）
                ocr_result = self.ocr_engine.predict(img_array)
                
                # 提取所有识别的文本
                all_text = ""
                if ocr_result and len(ocr_result) > 0:
                    result_obj = ocr_result[0]
                    
                    # 从OCRResult对象中获取识别的文本
                    if isinstance(result_obj, dict) and 'rec_texts' in result_obj:
                        rec_texts = result_obj['rec_texts']
                        # 将所有文本拼接起来
                        all_text = ''.join(rec_texts)
                
                doc.close()
                
                # 检查是否包含关键词
                found_keywords = []
                for keyword in self.keywords:
                    if keyword in all_text:
                        found_keywords.append(keyword)
                
                return len(found_keywords) > 0, found_keywords
            
            doc.close()
            return False, []
            
        except Exception as e:
            self.log(f"  ⚠️  检查PDF时出错: {str(e)}")
            return None, []
    
    def get_sorted_pdf_files(self):
        """获取排序后的PDF文件列表"""
        pdf_files = list(self.input_dir.glob("*.pdf"))
        pdf_files.extend(list(self.input_dir.glob("*.PDF")))
        
        # 过滤掉已经处理过的文件（文件名包含"2.pdf"的）
        filtered_files = []
        skipped = 0
        for pdf_file in pdf_files:
            # 跳过已经合并过的文件（如：第1页2.pdf）
            if re.search(r'页2\.pdf$', pdf_file.name, re.IGNORECASE):
                skipped += 1
                continue
            filtered_files.append(pdf_file)
        
        if skipped > 0:
            self.log(f"⏭️  跳过 {skipped} 个已处理文件（文件名包含'页2.pdf'）")
        
        # 按文件名排序
        return sorted(filtered_files, key=lambda x: x.name)
    
    def move_to_other(self, pdf_path):
        """移动PDF文件到other_pdf目录"""
        try:
            dest_path = self.other_dir / pdf_path.name
            
            # 如果目标文件已存在，添加时间戳
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                name_without_ext = dest_path.stem
                ext = dest_path.suffix
                dest_path = self.other_dir / f"{name_without_ext}_{timestamp}{ext}"
            
            shutil.move(str(pdf_path), str(dest_path))
            self.stats['moved_to_other'] += 1
            return True
        except Exception as e:
            self.log(f"  ❌ 移动文件失败: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def run(self):
        """执行B页识别和移动"""
        import time
        
        self.log("="*70)
        self.log("🚀 PDF B页识别与移动工具")
        self.log("="*70)
        self.log(f"📂 输入目录: {self.input_dir}")
        self.log(f"📂 B页目录: {self.other_dir}")
        self.log(f"🔑 关键词: {', '.join(self.keywords)}")
        self.log("")
        
        # 获取文件列表
        pdf_files = self.get_sorted_pdf_files()
        self.stats['total_files'] = len(pdf_files)
        
        if not pdf_files:
            self.log("❌ 在输入目录中没有找到PDF文件")
            return
        
        self.log(f"📁 找到 {len(pdf_files)} 个待处理PDF文件")
        self.log("🔍 开始识别...")
        self.log("")
        
        start_time = time.time()
        
        for i, pdf_file in enumerate(pdf_files, 1):
            file_start_time = time.time()
            
            # 显示当前文件
            self.log(f"[{i}/{len(pdf_files)}] 检查: {pdf_file.name}")
            
            # 检查是否为A页
            is_a_page, keywords = self.check_pdf_is_a_page(pdf_file)
            
            file_time = time.time() - file_start_time
            
            if is_a_page is None:
                # 识别出错
                self.stats['errors'] += 1
                self.log(f"  ❌ 识别失败 (耗时: {file_time:.2f}秒)")
            elif is_a_page:
                # A页，保留
                self.stats['a_pages'] += 1
                self.log(f"  ✅ A页 - 找到关键词: {', '.join(keywords)} (耗时: {file_time:.2f}秒)")
                self.log(f"  📍 保留在原位置")
            else:
                # B页，移动到other_pdf
                self.stats['b_pages'] += 1
                self.log(f"  📄 B页 - 无关键词 (耗时: {file_time:.2f}秒)")
                if self.move_to_other(pdf_file):
                    self.log(f"  ➡️  已移动到: {self.other_dir.name}/{pdf_file.name}")
            
            # 显示进度和预估时间
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(pdf_files) - i) * avg_time
            progress_pct = (i / len(pdf_files)) * 100
            
            # 格式化时间显示
            remaining_hours = int(remaining // 3600)
            remaining_mins = int((remaining % 3600) // 60)
            remaining_secs = int(remaining % 60)
            
            if remaining_hours > 0:
                time_str = f"{remaining_hours}小时{remaining_mins}分钟"
            elif remaining_mins > 0:
                time_str = f"{remaining_mins}分钟{remaining_secs}秒"
            else:
                time_str = f"{remaining_secs}秒"
            
            self.log(f"  📊 进度: {i}/{len(pdf_files)} ({progress_pct:.1f}%) | 已用时: {int(elapsed)}秒 | 预计剩余: {time_str}")
            self.log("")
        
        total_time = time.time() - start_time
        
        # 输出统计信息
        self.log("="*70)
        self.log("📊 处理完成统计:")
        self.log(f"  总文件数: {self.stats['total_files']}")
        self.log(f"  A页（包含关键词）: {self.stats['a_pages']}")
        self.log(f"  B页（无关键词）: {self.stats['b_pages']}")
        self.log(f"  移动到other_pdf: {self.stats['moved_to_other']}")
        self.log(f"  错误数: {self.stats['errors']}")
        self.log(f"  总耗时: {int(total_time)}秒 ({total_time/60:.1f}分钟)")
        self.log(f"  日志文件: {self.log_file}")
        self.log("="*70)


def main():
    parser = argparse.ArgumentParser(
        description='PDF B页识别与移动工具 - 识别不包含关键词的B页并移动到other_pdf',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='输入PDF文件目录路径'
    )
    parser.add_argument(
        '--other', '-o',
        default=None,
        help='B页输出目录 (默认: 输入目录/other_pdf)'
    )
    
    args = parser.parse_args()
    
    # 验证输入目录
    if not os.path.exists(args.input):
        print(f"❌ 输入目录不存在: {args.input}")
        sys.exit(1)
    
    if not os.path.isdir(args.input):
        print(f"❌ 输入路径不是目录: {args.input}")
        sys.exit(1)
    
    # 创建并运行分类器
    classifier = BPageClassifier(
        input_dir=args.input,
        other_dir=args.other
    )
    
    try:
        classifier.run()
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

