#!/usr/bin/env python3
"""
清理已有JSON结果的PDF文件

功能：
- 检查 IBoxTech_single_pdf 目录中的 PDF 文件
- 如果在 multi_page_results 或 single_page_results 中有对应的 JSON 结果
- 则删除该 PDF 文件（因为已经处理过了）
"""
import os
from pathlib import Path
import shutil


class PDFCleanupService:
    """PDF清理服务"""
    
    def __init__(self, pdf_dir, json_base_dir):
        """
        初始化清理服务
        
        Args:
            pdf_dir: PDF文件目录
            json_base_dir: JSON结果基础目录
        """
        self.pdf_dir = Path(pdf_dir)
        self.json_base_dir = Path(json_base_dir)
        self.multi_page_dir = self.json_base_dir / 'multi_page_results'
        self.single_page_dir = self.json_base_dir / 'single_page_results'
        
        # 统计信息
        self.total_pdfs = 0
        self.pdfs_with_json = 0
        self.pdfs_without_json = 0
        self.deleted_count = 0
        self.kept_count = 0
        
        # 详细列表
        self.files_to_delete = []
        self.files_to_keep = []
    
    def check_json_exists(self, pdf_filename):
        """
        检查PDF是否有对应的JSON结果
        
        Args:
            pdf_filename: PDF文件名
            
        Returns:
            tuple: (是否存在, 所在目录类型)
        """
        # 移除.pdf后缀
        pdf_name_without_ext = pdf_filename.replace('.pdf', '').replace('.PDF', '')
        
        # 检查 multi_page_results
        multi_page_path = self.multi_page_dir / pdf_name_without_ext
        if multi_page_path.exists() and multi_page_path.is_dir():
            # 检查是否有 page_*_results 目录
            page_dirs = list(multi_page_path.glob('page_*_results'))
            if page_dirs:
                return True, 'multi_page', len(page_dirs)
        
        # 检查 single_page_results
        single_page_path = self.single_page_dir / pdf_name_without_ext
        if single_page_path.exists() and single_page_path.is_dir():
            # 检查是否有 steps 目录
            steps_dir = single_page_path / 'steps'
            if steps_dir.exists():
                return True, 'single_page', 1
            # 或者检查是否有 page_*_results 目录
            page_dirs = list(single_page_path.glob('page_*_results'))
            if page_dirs:
                return True, 'single_page', len(page_dirs)
        
        return False, None, 0
    
    def scan_pdfs(self, dry_run=True):
        """
        扫描PDF文件
        
        Args:
            dry_run: 是否为模拟运行（不实际删除）
            
        Returns:
            dict: 扫描结果统计
        """
        print("="*80)
        print("  PDF 文件清理工具")
        print("="*80)
        print(f"\n📂 扫描目录:")
        print(f"   PDF目录: {self.pdf_dir}")
        print(f"   JSON目录: {self.json_base_dir}")
        print(f"   - multi_page_results: {self.multi_page_dir}")
        print(f"   - single_page_results: {self.single_page_dir}")
        print(f"\n模式: {'🔍 模拟运行（不会真正删除）' if dry_run else '⚠️  实际删除模式'}")
        print("="*80)
        
        # 获取所有PDF文件
        if not self.pdf_dir.exists():
            print(f"❌ PDF目录不存在: {self.pdf_dir}")
            return None
        
        pdf_files = list(self.pdf_dir.glob('*.pdf')) + list(self.pdf_dir.glob('*.PDF'))
        self.total_pdfs = len(pdf_files)
        
        print(f"\n📊 开始扫描 {self.total_pdfs} 个PDF文件...\n")
        
        # 扫描每个PDF文件
        for idx, pdf_file in enumerate(pdf_files, 1):
            # 进度显示
            if idx % 100 == 0 or idx == self.total_pdfs:
                print(f"   进度: {idx}/{self.total_pdfs} ({idx*100//self.total_pdfs}%)")
            
            # 检查是否有JSON结果
            has_json, json_type, page_count = self.check_json_exists(pdf_file.name)
            
            if has_json:
                self.pdfs_with_json += 1
                self.files_to_delete.append({
                    'filename': pdf_file.name,
                    'path': str(pdf_file),
                    'json_type': json_type,
                    'page_count': page_count
                })
            else:
                self.pdfs_without_json += 1
                self.files_to_keep.append({
                    'filename': pdf_file.name,
                    'path': str(pdf_file)
                })
        
        print(f"\n✅ 扫描完成！\n")
        
        # 打印统计信息
        self._print_statistics()
        
        # 执行删除（如果不是dry_run）
        if not dry_run:
            self._execute_deletion()
        
        return self._get_statistics()
    
    def _print_statistics(self):
        """打印统计信息"""
        print("="*80)
        print("  扫描结果统计")
        print("="*80)
        print(f"\n📊 文件统计:")
        print(f"   总PDF文件数: {self.total_pdfs}")
        print(f"   有JSON结果: {self.pdfs_with_json} (待删除)")
        print(f"   无JSON结果: {self.pdfs_without_json} (保留)")
        print(f"\n📈 JSON类型分布:")
        
        multi_count = sum(1 for f in self.files_to_delete if f['json_type'] == 'multi_page')
        single_count = sum(1 for f in self.files_to_delete if f['json_type'] == 'single_page')
        
        print(f"   multi_page_results: {multi_count}")
        print(f"   single_page_results: {single_count}")
        print("="*80)
    
    def _execute_deletion(self):
        """执行实际删除操作"""
        print(f"\n⚠️  开始删除 {len(self.files_to_delete)} 个文件...\n")
        
        for idx, file_info in enumerate(self.files_to_delete, 1):
            try:
                file_path = Path(file_info['path'])
                if file_path.exists():
                    file_path.unlink()
                    self.deleted_count += 1
                    
                    if idx % 100 == 0 or idx == len(self.files_to_delete):
                        print(f"   已删除: {idx}/{len(self.files_to_delete)} ({idx*100//len(self.files_to_delete)}%)")
            except Exception as e:
                print(f"   ❌ 删除失败: {file_info['filename']} - {str(e)}")
        
        self.kept_count = self.total_pdfs - self.deleted_count
        
        print(f"\n✅ 删除完成！")
        print(f"   实际删除: {self.deleted_count}")
        print(f"   保留文件: {self.kept_count}")
    
    def _get_statistics(self):
        """获取统计信息"""
        return {
            'total_pdfs': self.total_pdfs,
            'pdfs_with_json': self.pdfs_with_json,
            'pdfs_without_json': self.pdfs_without_json,
            'deleted_count': self.deleted_count,
            'kept_count': self.kept_count if self.deleted_count > 0 else self.pdfs_without_json,
            'files_to_delete': self.files_to_delete,
            'files_to_keep': self.files_to_keep
        }
    
    def save_report(self, output_file='cleanup_report.txt'):
        """保存详细报告"""
        report_path = Path(output_file)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("  PDF 文件清理报告\n")
            f.write("="*80 + "\n\n")
            
            f.write(f"PDF目录: {self.pdf_dir}\n")
            f.write(f"JSON目录: {self.json_base_dir}\n\n")
            
            f.write(f"总PDF文件数: {self.total_pdfs}\n")
            f.write(f"有JSON结果: {self.pdfs_with_json}\n")
            f.write(f"无JSON结果: {self.pdfs_without_json}\n\n")
            
            # 待删除文件列表
            f.write("="*80 + "\n")
            f.write(f"待删除文件列表 ({len(self.files_to_delete)} 个)\n")
            f.write("="*80 + "\n")
            for file_info in self.files_to_delete:
                f.write(f"{file_info['filename']} ({file_info['json_type']}, {file_info['page_count']}页)\n")
            
            f.write("\n")
            
            # 保留文件列表
            f.write("="*80 + "\n")
            f.write(f"保留文件列表 ({len(self.files_to_keep)} 个)\n")
            f.write("="*80 + "\n")
            for file_info in self.files_to_keep:
                f.write(f"{file_info['filename']}\n")
        
        print(f"\n📄 详细报告已保存到: {report_path.absolute()}")


def main():
    """主函数"""
    import sys
    
    # 配置路径
    pdf_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf"
    json_base_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_json_bak"
    
    # 创建清理服务
    service = PDFCleanupService(pdf_dir, json_base_dir)
    
    # 第一步：模拟运行（查看会删除哪些文件）
    print("\n" + "="*80)
    print("  步骤 1: 模拟扫描（不会删除任何文件）")
    print("="*80 + "\n")
    
    result = service.scan_pdfs(dry_run=True)
    
    if result is None:
        print("\n❌ 扫描失败")
        sys.exit(1)
    
    # 保存报告
    report_file = "/home/h3c/workspace/IBoxTech-ocrchecker/misc/pdf_cleanup_report.txt"
    service.save_report(report_file)
    
    # 询问是否继续
    print("\n" + "="*80)
    print("  步骤 2: 确认删除")
    print("="*80)
    print(f"\n⚠️  将要删除 {result['pdfs_with_json']} 个PDF文件")
    print(f"   保留 {result['pdfs_without_json']} 个PDF文件")
    print(f"\n   详细报告: {report_file}")
    
    response = input("\n❓ 是否继续删除？(yes/no): ").strip().lower()
    
    if response in ['yes', 'y']:
        print("\n" + "="*80)
        print("  步骤 3: 执行删除")
        print("="*80 + "\n")
        
        # 重新创建服务并执行实际删除
        service2 = PDFCleanupService(pdf_dir, json_base_dir)
        result2 = service2.scan_pdfs(dry_run=False)
        
        print("\n" + "="*80)
        print("  清理完成！")
        print("="*80)
        print(f"\n✅ 已删除 {result2['deleted_count']} 个PDF文件")
        print(f"✅ 保留 {result2['kept_count']} 个PDF文件")
        print(f"\n💡 建议：")
        print(f"   1. 检查 {pdf_dir}")
        print(f"   2. 确认剩余文件数量是否正确")
        print(f"   3. 这些文件可以继续用于OCR处理")
    else:
        print("\n❌ 操作已取消，未删除任何文件")
        sys.exit(0)


if __name__ == '__main__':
    main()

