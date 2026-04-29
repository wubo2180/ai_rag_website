#!/usr/bin/env python3
"""
检查哪些JSON文件对应的PDF没有入库到数据库

功能：
- 从JSON目录中获取所有已处理的PDF名称
- 从数据库中查询已入库的文件
- 对比找出差异
"""
import os
import sys
from pathlib import Path
import pymysql
from collections import defaultdict
import shutil


class DatabaseChecker:
    """数据库检查器"""
    
    def __init__(self):
        """初始化数据库连接"""
        # 数据库配置
        self.db_config = {
            'host': '172.20.46.24',
            'port': 3306,
            'user': 'root',
            'password': 'bigdata206.',
            'database': 'ocr_system',
            'charset': 'utf8mb4',
            'connect_timeout': 10
        }
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = pymysql.connect(**self.db_config)
            self.cursor = self.conn.cursor(pymysql.cursors.DictCursor)
            print("✅ 数据库连接成功")
            return True
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return False
    
    def get_database_files(self):
        """从数据库获取所有已入库的文件"""
        try:
            # 查询 commission_basic 表（业务表）
            self.cursor.execute("""
                SELECT 
                    id,
                    commission_number,
                    form_number,
                    created_at
                FROM commission_basic
                ORDER BY id
            """)
            commission_records = self.cursor.fetchall()
            
            # 查询 files 表
            self.cursor.execute("""
                SELECT 
                    id,
                    filename,
                    file_type,
                    created_at
                FROM files
                WHERE file_type = '委托单'
                ORDER BY id
            """)
            file_records = self.cursor.fetchall()
            
            return {
                'commission_basic': commission_records,
                'files': file_records
            }
            
        except Exception as e:
            print(f"❌ 查询数据库失败: {str(e)}")
            return None
    
    def close(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


class JSONChecker:
    """JSON文件检查器"""
    
    def __init__(self, json_base_dir):
        """初始化"""
        self.json_base_dir = Path(json_base_dir)
        self.multi_page_dir = self.json_base_dir / 'multi_page_results'
        self.single_page_dir = self.json_base_dir / 'single_page_results'
    
    def get_json_files(self):
        """获取所有JSON对应的PDF名称"""
        json_files = {
            'multi_page': [],
            'single_page': []
        }
        
        # 检查 multi_page_results
        if self.multi_page_dir.exists():
            for item in self.multi_page_dir.iterdir():
                if item.is_dir():
                    # 目录名就是PDF文件名（去除.pdf后缀）
                    pdf_name = item.name + '.pdf'
                    json_files['multi_page'].append({
                        'pdf_name': pdf_name,
                        'base_name': item.name,
                        'path': str(item)
                    })
        
        # 检查 single_page_results
        if self.single_page_dir.exists():
            for item in self.single_page_dir.iterdir():
                if item.is_dir():
                    pdf_name = item.name + '.pdf'
                    json_files['single_page'].append({
                        'pdf_name': pdf_name,
                        'base_name': item.name,
                        'path': str(item)
                    })
        
        return json_files


def main():
    """主函数"""
    print("="*80)
    print("  JSON文件与数据库差异检查工具")
    print("="*80)
    print()
    
    # 配置路径
    json_base_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_json"
    pdf_backup_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf_bak"
    
    # 1. 获取JSON文件列表
    print("📂 步骤 1: 扫描JSON文件...")
    print("-"*80)
    
    json_checker = JSONChecker(json_base_dir)
    json_files = json_checker.get_json_files()
    
    multi_count = len(json_files['multi_page'])
    single_count = len(json_files['single_page'])
    total_json = multi_count + single_count
    
    print(f"   multi_page_results: {multi_count} 个")
    print(f"   single_page_results: {single_count} 个")
    print(f"   总计: {total_json} 个")
    print()
    
    # 创建PDF名称集合（用于快速查找）
    all_json_pdf_names = set()
    json_pdf_info = {}
    
    for item in json_files['multi_page']:
        all_json_pdf_names.add(item['pdf_name'])
        json_pdf_info[item['pdf_name']] = {
            'type': 'multi_page',
            'base_name': item['base_name']
        }
    
    for item in json_files['single_page']:
        all_json_pdf_names.add(item['pdf_name'])
        json_pdf_info[item['pdf_name']] = {
            'type': 'single_page',
            'base_name': item['base_name']
        }
    
    # 2. 查询数据库
    print("📊 步骤 2: 查询数据库...")
    print("-"*80)
    
    db_checker = DatabaseChecker()
    if not db_checker.connect():
        print("❌ 无法连接数据库，退出")
        sys.exit(1)
    
    db_data = db_checker.get_database_files()
    if db_data is None:
        print("❌ 查询数据库失败，退出")
        db_checker.close()
        sys.exit(1)
    
    commission_count = len(db_data['commission_basic'])
    files_count = len(db_data['files'])
    
    print(f"   commission_basic 表: {commission_count} 条记录")
    print(f"   files 表: {files_count} 条记录（委托单类型）")
    print()
    
    # 创建数据库文件名集合
    db_filenames = set()
    for file_record in db_data['files']:
        db_filenames.add(file_record['filename'])
    
    db_checker.close()
    
    # 3. 对比差异
    print("🔍 步骤 3: 对比差异...")
    print("-"*80)
    
    # 找出有JSON但没有入库的文件
    missing_in_db = all_json_pdf_names - db_filenames
    
    # 找出入库了但没有JSON的文件（理论上不应该有）
    extra_in_db = db_filenames - all_json_pdf_names
    
    print(f"   有JSON但未入库: {len(missing_in_db)} 个")
    print(f"   已入库但无JSON: {len(extra_in_db)} 个")
    print()
    
    # 4. 详细分析
    print("="*80)
    print("  详细分析结果")
    print("="*80)
    print()
    
    # 统计未入库文件的类型分布
    missing_by_type = {
        'multi_page': [],
        'single_page': []
    }
    
    for pdf_name in missing_in_db:
        if pdf_name in json_pdf_info:
            json_type = json_pdf_info[pdf_name]['type']
            missing_by_type[json_type].append({
                'pdf_name': pdf_name,
                'base_name': json_pdf_info[pdf_name]['base_name']
            })
    
    print(f"📊 未入库文件类型分布:")
    print(f"   multi_page: {len(missing_by_type['multi_page'])} 个")
    print(f"   single_page: {len(missing_by_type['single_page'])} 个")
    print()
    
    # 5. 检查PDF文件是否存在于备份目录
    print("📂 步骤 4: 检查PDF文件是否存在于备份目录...")
    print("-"*80)
    
    pdf_backup_path = Path(pdf_backup_dir)
    files_with_pdf = []
    files_without_pdf = []
    
    if pdf_backup_path.exists():
        print(f"   备份目录: {pdf_backup_dir}")
        print(f"   检查 {len(missing_in_db)} 个文件...")
        print()
        
        for pdf_name in missing_in_db:
            pdf_file = pdf_backup_path / pdf_name
            if pdf_file.exists():
                files_with_pdf.append({
                    'pdf_name': pdf_name,
                    'json_type': json_pdf_info.get(pdf_name, {}).get('type', 'unknown'),
                    'pdf_path': str(pdf_file)
                })
            else:
                files_without_pdf.append({
                    'pdf_name': pdf_name,
                    'json_type': json_pdf_info.get(pdf_name, {}).get('type', 'unknown')
                })
        
        print(f"   ✅ 有对应PDF文件: {len(files_with_pdf)} 个")
        print(f"   ❌ 无对应PDF文件: {len(files_without_pdf)} 个")
        print()
    else:
        print(f"   ⚠️  备份目录不存在: {pdf_backup_dir}")
        print()
    
    # 6. 保存报告
    report_file = "/home/h3c/workspace/IBoxTech-ocrchecker/misc/missing_files_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("  JSON文件与数据库差异报告\n")
        f.write("="*80 + "\n\n")
        
        f.write(f"统计信息:\n")
        f.write(f"  - JSON文件总数: {total_json}\n")
        f.write(f"    - multi_page: {multi_count}\n")
        f.write(f"    - single_page: {single_count}\n")
        f.write(f"  - 数据库记录数:\n")
        f.write(f"    - commission_basic: {commission_count}\n")
        f.write(f"    - files: {files_count}\n")
        f.write(f"  - 有JSON但未入库: {len(missing_in_db)}\n")
        f.write(f"  - 已入库但无JSON: {len(extra_in_db)}\n")
        f.write(f"  - PDF文件存在性:\n")
        f.write(f"    - 有对应PDF: {len(files_with_pdf)}\n")
        f.write(f"    - 无对应PDF: {len(files_without_pdf)}\n\n")
        
        f.write("="*80 + "\n")
        f.write(f"有JSON但未入库且有PDF文件的列表 ({len(files_with_pdf)} 个)\n")
        f.write("="*80 + "\n")
        f.write("这些文件可以重新导入到数据库\n\n")
        
        # 有PDF的文件
        for item in sorted(files_with_pdf, key=lambda x: x['pdf_name']):
            f.write(f"{item['pdf_name']} ({item['json_type']})\n")
        f.write("\n")
        
        f.write("="*80 + "\n")
        f.write(f"有JSON但未入库且无PDF文件的列表 ({len(files_without_pdf)} 个)\n")
        f.write("="*80 + "\n")
        f.write("这些文件的PDF已丢失，无法重新导入\n\n")
        
        # 无PDF的文件
        for item in sorted(files_without_pdf, key=lambda x: x['pdf_name']):
            f.write(f"{item['pdf_name']} ({item['json_type']})\n")
        f.write("\n")
        
        # 已入库但无JSON
        if extra_in_db:
            f.write("="*80 + "\n")
            f.write(f"已入库但无JSON的文件列表 ({len(extra_in_db)} 个)\n")
            f.write("="*80 + "\n\n")
            for filename in sorted(extra_in_db):
                f.write(f"{filename}\n")
    
    print(f"📄 详细报告已保存到: {report_file}")
    print()
    
    # 7. 显示前20个未入库的文件
    if files_with_pdf:
        print("📋 有PDF可重新导入的文件示例（前20个）:")
        print("-"*80)
        for idx, item in enumerate(sorted(files_with_pdf, key=lambda x: x['pdf_name'])[:20], 1):
            print(f"   {idx}. {item['pdf_name']} ({item['json_type']})")
        
        if len(files_with_pdf) > 20:
            print(f"   ... 还有 {len(files_with_pdf) - 20} 个文件")
        print()
    
    # 8. 总结
    print("="*80)
    print("  总结")
    print("="*80)
    print(f"\n✅ JSON文件总数: {total_json}")
    print(f"✅ 数据库files表: {files_count} 条")
    print(f"✅ commission_basic表: {commission_count} 条")
    print(f"\n⚠️  差异分析:")
    print(f"   - 有JSON但未入库: {len(missing_in_db)} 个")
    print(f"   - 其中有PDF可导入: {len(files_with_pdf)} 个")
    print(f"   - 其中PDF已丢失: {len(files_without_pdf)} 个")
    
    if len(files_with_pdf) > 0:
        print(f"\n💡 建议:")
        print(f"   1. 有 {len(files_with_pdf)} 个文件可以重新导入")
        print(f"   2. PDF文件位于: {pdf_backup_dir}")
        print(f"   3. JSON文件位于: {json_base_dir}")
        print(f"   4. 可以使用批量导入工具重新导入这些文件")
        print(f"   5. 详细列表见: {report_file}")
    
    if len(files_without_pdf) > 0:
        print(f"\n⚠️  注意:")
        print(f"   有 {len(files_without_pdf)} 个文件的PDF已丢失")
        print(f"   这些文件只有JSON数据，无法完整导入")
    
    print()
    
    # 9. 询问是否拷贝PDF文件
    if len(files_with_pdf) > 0:
        print("="*80)
        print("  步骤 5: 拷贝PDF文件到导入目录")
        print("="*80)
        print()
        
        target_pdf_dir = "/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf"
        target_path = Path(target_pdf_dir)
        
        print(f"📂 目标目录: {target_pdf_dir}")
        print(f"📋 将拷贝 {len(files_with_pdf)} 个PDF文件")
        print()
        
        response = input("❓ 是否开始拷贝？(yes/no): ").strip().lower()
        
        if response in ['yes', 'y']:
            # 确保目标目录存在
            target_path.mkdir(parents=True, exist_ok=True)
            
            print()
            print("🔄 开始拷贝文件...")
            print("-"*80)
            
            copied_count = 0
            skipped_count = 0
            failed_count = 0
            
            for idx, item in enumerate(files_with_pdf, 1):
                source_file = Path(item['pdf_path'])
                target_file = target_path / item['pdf_name']
                
                try:
                    # 检查目标文件是否已存在
                    if target_file.exists():
                        skipped_count += 1
                        if idx % 100 == 0 or idx == len(files_with_pdf):
                            print(f"   进度: {idx}/{len(files_with_pdf)} - 跳过已存在的文件: {item['pdf_name']}")
                    else:
                        # 拷贝文件
                        shutil.copy2(source_file, target_file)
                        copied_count += 1
                        
                        if idx % 100 == 0 or idx == len(files_with_pdf):
                            print(f"   进度: {idx}/{len(files_with_pdf)} ({idx*100//len(files_with_pdf)}%)")
                
                except Exception as e:
                    failed_count += 1
                    print(f"   ❌ 拷贝失败: {item['pdf_name']} - {str(e)}")
            
            print()
            print("="*80)
            print("  拷贝完成")
            print("="*80)
            print(f"\n✅ 成功拷贝: {copied_count} 个文件")
            print(f"⏭️  跳过已存在: {skipped_count} 个文件")
            if failed_count > 0:
                print(f"❌ 拷贝失败: {failed_count} 个文件")
            print(f"\n📂 文件位置: {target_pdf_dir}")
            print(f"💡 现在可以使用导入工具批量导入这些文件了")
            print()
        else:
            print("\n❌ 已取消拷贝操作")
            print()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

