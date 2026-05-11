#!/usr/bin/env python3
"""
委托单数据导入工具
将PDF文件上传到MinIO，并将对应的JSON数据导入MySQL
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
import pymysql
from minio import Minio
from minio.error import S3Error
import hashlib
import argparse


class CommissionDataImporter:
    """委托单数据导入器"""
    
    def __init__(self, mysql_config, minio_config):
        self.mysql_config = mysql_config
        self.minio_config = minio_config
        self.mysql_conn = None
        self.minio_client = None
        
        # 统计信息
        self.stats = {
            'total_files': 0,
            'success_uploads': 0,
            'success_imports': 0,
            'failed_uploads': 0,
            'failed_imports': 0,
            'errors': []
        }
    
    def connect_mysql(self):
        """连接MySQL数据库"""
        try:
            self.mysql_conn = pymysql.connect(
                host=self.mysql_config['host'],
                port=self.mysql_config['port'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            print(f"✅ MySQL连接成功: {self.mysql_config['host']}:{self.mysql_config['port']}")
            return True
        except Exception as e:
            print(f"❌ MySQL连接失败: {str(e)}")
            return False
    
    def connect_minio(self):
        """连接MinIO"""
        try:
            self.minio_client = Minio(
                self.minio_config['endpoint'],
                access_key=self.minio_config['access_key'],
                secret_key=self.minio_config['secret_key'],
                secure=self.minio_config['secure']
            )
            
            # 检查并创建bucket
            bucket_name = self.minio_config['bucket_name']
            if not self.minio_client.bucket_exists(bucket_name):
                self.minio_client.make_bucket(bucket_name)
                print(f"✅ 创建MinIO存储桶: {bucket_name}")
            else:
                print(f"✅ MinIO连接成功: {self.minio_config['endpoint']}")
            
            return True
        except Exception as e:
            print(f"❌ MinIO连接失败: {str(e)}")
            return False
    
    def create_tables(self):
        """创建数据库表"""
        try:
            cursor = self.mysql_conn.cursor()
            
            # 创建委托单主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_documents (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    pdf_filename VARCHAR(255) NOT NULL COMMENT 'PDF文件名',
                    minio_object_name VARCHAR(500) NOT NULL COMMENT 'MinIO对象名',
                    minio_bucket VARCHAR(100) NOT NULL COMMENT 'MinIO存储桶',
                    file_size BIGINT COMMENT '文件大小(字节)',
                    file_md5 VARCHAR(32) COMMENT '文件MD5值',
                    page_count INT DEFAULT 1 COMMENT '页数',
                    extraction_timestamp DATETIME COMMENT '提取时间',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                    INDEX idx_pdf_filename (pdf_filename),
                    INDEX idx_created_at (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='委托单文档表';
            """)
            
            # 创建提取字段表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_extracted_fields (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_id INT NOT NULL COMMENT '文档ID',
                    page_number INT NOT NULL COMMENT '页码',
                    field_name VARCHAR(100) NOT NULL COMMENT '字段名称',
                    field_value TEXT COMMENT '字段值',
                    field_type VARCHAR(50) COMMENT '字段类型',
                    extraction_method VARCHAR(100) COMMENT '提取方法',
                    confidence FLOAT COMMENT '置信度',
                    source_block_id VARCHAR(100) COMMENT '来源块ID',
                    source_block_text TEXT COMMENT '来源块文本',
                    bbox_json TEXT COMMENT 'bbox信息(JSON)',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    FOREIGN KEY (document_id) REFERENCES commission_documents(id) ON DELETE CASCADE,
                    INDEX idx_document_id (document_id),
                    INDEX idx_field_name (field_name),
                    INDEX idx_page_number (page_number)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='委托单提取字段表';
            """)
            
            # 创建统计信息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commission_statistics (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_id INT NOT NULL COMMENT '文档ID',
                    page_number INT NOT NULL COMMENT '页码',
                    source_content_blocks INT COMMENT '内容块数',
                    grid_cells_count INT COMMENT '网格单元数',
                    matched_cells_count INT COMMENT '匹配单元数',
                    total_fields_extracted INT COMMENT '提取字段总数',
                    single_cell_fields INT COMMENT '单单元字段数',
                    adjacent_cell_fields INT COMMENT '相邻单元字段数',
                    handwritten_fields INT COMMENT '手写字段数',
                    table_data_count INT COMMENT '表格数据数',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    FOREIGN KEY (document_id) REFERENCES commission_documents(id) ON DELETE CASCADE,
                    INDEX idx_document_id (document_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='委托单统计信息表';
            """)
            
            self.mysql_conn.commit()
            print("✅ 数据库表创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建数据库表失败: {str(e)}")
            self.mysql_conn.rollback()
            return False
    
    def upload_pdf_to_minio(self, pdf_path):
        """上传PDF到MinIO"""
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            # 读取文件并计算MD5
            with open(pdf_file, 'rb') as f:
                file_content = f.read()
            
            file_md5 = hashlib.md5(file_content).hexdigest()
            file_size = len(file_content)
            
            # 生成MinIO对象名
            object_name = f"commission_pdfs/{pdf_file.name}"
            
            # 上传到MinIO
            from io import BytesIO
            self.minio_client.put_object(
                bucket_name=self.minio_config['bucket_name'],
                object_name=object_name,
                data=BytesIO(file_content),
                length=file_size,
                content_type='application/pdf'
            )
            
            print(f"  ✅ PDF上传成功: {object_name}")
            
            return {
                'success': True,
                'object_name': object_name,
                'file_size': file_size,
                'file_md5': file_md5
            }
            
        except Exception as e:
            print(f"  ❌ PDF上传失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def import_json_data(self, json_path, document_id, page_number):
        """导入JSON数据到MySQL"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cursor = self.mysql_conn.cursor()
            
            # 插入统计信息
            extraction_stats = data.get('extraction_statistics', {})
            cursor.execute("""
                INSERT INTO commission_statistics (
                    document_id, page_number, source_content_blocks, grid_cells_count,
                    matched_cells_count, total_fields_extracted, single_cell_fields,
                    adjacent_cell_fields, handwritten_fields, table_data_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                document_id, page_number,
                data.get('source_content_blocks'),
                data.get('grid_cells_count'),
                data.get('matched_cells_count'),
                data.get('total_fields_extracted'),
                extraction_stats.get('single_cell_fields'),
                extraction_stats.get('adjacent_cell_fields'),
                extraction_stats.get('handwritten_fields'),
                extraction_stats.get('table_data_count')
            ))
            
            # 插入提取的字段
            extracted_fields = data.get('extracted_fields', {})
            for field_name, field_data in extracted_fields.items():
                # 提取置信度和来源块信息
                confidence = None
                source_block_id = None
                source_block_text = None
                bbox_json = None
                
                # 根据字段类型提取信息
                field_type = field_data.get('type')
                
                if field_type == 'single_cell':
                    source_block = field_data.get('source_block', {})
                    confidence = source_block.get('confidence')
                    source_block_id = source_block.get('id')
                    source_block_text = source_block.get('text')
                    if 'bbox' in source_block:
                        bbox_json = json.dumps(source_block['bbox'])
                
                elif field_type == 'adjacent_cells':
                    content_block = field_data.get('content_block', {})
                    confidence = content_block.get('confidence')
                    source_block_id = content_block.get('id')
                    source_block_text = content_block.get('text')
                    if 'bbox' in content_block:
                        bbox_json = json.dumps(content_block['bbox'])
                
                elif field_type == 'choice_field':
                    choice_block = field_data.get('choice_block', {})
                    confidence = choice_block.get('confidence')
                    source_block_id = choice_block.get('id')
                    source_block_text = choice_block.get('text')
                    if 'bbox' in choice_block:
                        bbox_json = json.dumps(choice_block['bbox'])
                
                cursor.execute("""
                    INSERT INTO commission_extracted_fields (
                        document_id, page_number, field_name, field_value, field_type,
                        extraction_method, confidence, source_block_id, source_block_text, bbox_json
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    document_id, page_number, field_name, field_data.get('value'),
                    field_type, field_data.get('extraction_method'),
                    confidence, source_block_id, source_block_text, bbox_json
                ))
            
            self.mysql_conn.commit()
            print(f"  ✅ JSON数据导入成功 (字段数: {len(extracted_fields)})")
            
            return True
            
        except Exception as e:
            print(f"  ❌ JSON数据导入失败: {str(e)}")
            self.mysql_conn.rollback()
            return False
    
    def find_json_files(self, pdf_filename, json_base_dir):
        """查找PDF对应的JSON文件"""
        # 移除.pdf后缀
        pdf_name_without_ext = pdf_filename.replace('.pdf', '').replace('.PDF', '')
        
        # JSON目录路径
        json_dir = Path(json_base_dir) / 'multi_page_results' / pdf_name_without_ext
        
        if not json_dir.exists():
            return []
        
        # 查找所有的6.3_field_extraction_results.json文件
        json_files = []
        for page_dir in sorted(json_dir.glob('page_*_results')):
            json_file = page_dir / 'steps' / 'step06' / '6.3_field_extraction_results.json'
            if json_file.exists():
                # 提取页码
                match = re.search(r'page_(\d+)_results', page_dir.name)
                page_number = int(match.group(1)) if match else 0
                json_files.append({
                    'path': json_file,
                    'page_number': page_number
                })
        
        return json_files
    
    def process_single_pdf(self, pdf_path, json_base_dir):
        """处理单个PDF文件"""
        try:
            pdf_file = Path(pdf_path)
            print(f"\n📄 处理文件: {pdf_file.name}")
            
            # 1. 查找对应的JSON文件
            json_files = self.find_json_files(pdf_file.name, json_base_dir)
            if not json_files:
                print(f"  ⚠️  未找到对应的JSON文件")
                self.stats['errors'].append(f"{pdf_file.name}: 未找到JSON文件")
                return False
            
            print(f"  📊 找到 {len(json_files)} 个页面的JSON文件")
            
            # 2. 上传PDF到MinIO
            upload_result = self.upload_pdf_to_minio(pdf_path)
            if not upload_result['success']:
                self.stats['failed_uploads'] += 1
                self.stats['errors'].append(f"{pdf_file.name}: PDF上传失败")
                return False
            
            self.stats['success_uploads'] += 1
            
            # 3. 插入文档记录
            cursor = self.mysql_conn.cursor()
            
            # 获取提取时间（从第一个JSON文件）
            with open(json_files[0]['path'], 'r', encoding='utf-8') as f:
                first_json = json.load(f)
            extraction_timestamp = first_json.get('extraction_timestamp')
            if extraction_timestamp:
                extraction_timestamp = datetime.strptime(extraction_timestamp, '%Y-%m-%d %H:%M:%S.%f')
            
            cursor.execute("""
                INSERT INTO commission_documents (
                    pdf_filename, minio_object_name, minio_bucket, file_size,
                    file_md5, page_count, extraction_timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                pdf_file.name,
                upload_result['object_name'],
                self.minio_config['bucket_name'],
                upload_result['file_size'],
                upload_result['file_md5'],
                len(json_files),
                extraction_timestamp
            ))
            
            document_id = cursor.lastrowid
            self.mysql_conn.commit()
            
            print(f"  ✅ 文档记录创建成功 (ID: {document_id})")
            
            # 4. 导入每一页的JSON数据
            for json_file_info in json_files:
                page_num = json_file_info['page_number']
                print(f"  📄 导入第 {page_num} 页数据...")
                
                if not self.import_json_data(json_file_info['path'], document_id, page_num):
                    self.stats['failed_imports'] += 1
                    self.stats['errors'].append(f"{pdf_file.name}: 第{page_num}页JSON导入失败")
                    continue
            
            self.stats['success_imports'] += 1
            print(f"  ✅ 文件处理完成")
            
            return True
            
        except Exception as e:
            print(f"  ❌ 处理失败: {str(e)}")
            self.stats['errors'].append(f"{pdf_file.name}: {str(e)}")
            return False
    
    def process_multiple_pdfs(self, pdf_dir, json_base_dir, limit=None):
        """处理多个PDF文件"""
        pdf_files = list(Path(pdf_dir).glob("*页2.pdf"))
        
        if limit:
            pdf_files = pdf_files[:limit]
        
        self.stats['total_files'] = len(pdf_files)
        
        print(f"\n{'='*70}")
        print(f"📦 准备处理 {len(pdf_files)} 个PDF文件")
        print(f"{'='*70}")
        
        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"\n[{i}/{len(pdf_files)}]", end='')
            self.process_single_pdf(pdf_file, json_base_dir)
        
        # 打印统计信息
        print(f"\n{'='*70}")
        print(f"📊 处理完成统计")
        print(f"{'='*70}")
        print(f"  总文件数: {self.stats['total_files']}")
        print(f"  PDF上传成功: {self.stats['success_uploads']}")
        print(f"  数据导入成功: {self.stats['success_imports']}")
        print(f"  PDF上传失败: {self.stats['failed_uploads']}")
        print(f"  数据导入失败: {self.stats['failed_imports']}")
        
        if self.stats['errors']:
            print(f"\n⚠️  错误列表:")
            for error in self.stats['errors'][:10]:  # 只显示前10个错误
                print(f"  - {error}")
            if len(self.stats['errors']) > 10:
                print(f"  ... 还有 {len(self.stats['errors']) - 10} 个错误")
        
        print(f"{'='*70}\n")
    
    def close(self):
        """关闭连接"""
        if self.mysql_conn:
            self.mysql_conn.close()
            print("MySQL连接已关闭")


def main():
    parser = argparse.ArgumentParser(description='委托单数据导入工具')
    parser.add_argument('--pdf-dir', type=str,
                       default='/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_single_pdf',
                       help='PDF文件目录')
    parser.add_argument('--json-dir', type=str,
                       default='/home/h3c/workspace/IBoxTech-ocrchecker/resource/IBoxTech_json',
                       help='JSON文件基础目录')
    parser.add_argument('--limit', type=int, default=2,
                       help='处理文件数量限制（测试用）')
    parser.add_argument('--mysql-host', type=str, default='localhost', help='MySQL主机')
    parser.add_argument('--mysql-port', type=int, default=3306, help='MySQL端口')
    parser.add_argument('--mysql-user', type=str, default='root', help='MySQL用户名')
    parser.add_argument('--mysql-password', type=str, default='', help='MySQL密码')
    parser.add_argument('--mysql-database', type=str, default='ocr_system', help='MySQL数据库名')
    parser.add_argument('--minio-endpoint', type=str, default='localhost:9000', help='MinIO endpoint')
    parser.add_argument('--minio-access-key', type=str, default='minioadmin', help='MinIO access key')
    parser.add_argument('--minio-secret-key', type=str, default='minioadmin', help='MinIO secret key')
    parser.add_argument('--minio-bucket', type=str, default='ocr-files', help='MinIO bucket名称')
    parser.add_argument('--minio-secure', action='store_true', help='使用HTTPS连接MinIO')
    
    args = parser.parse_args()
    
    # MySQL配置
    mysql_config = {
        'host': args.mysql_host,
        'port': args.mysql_port,
        'user': args.mysql_user,
        'password': args.mysql_password,
        'database': args.mysql_database
    }
    
    # MinIO配置
    minio_config = {
        'endpoint': args.minio_endpoint,
        'access_key': args.minio_access_key,
        'secret_key': args.minio_secret_key,
        'bucket_name': args.minio_bucket,
        'secure': args.minio_secure
    }
    
    # 创建导入器
    importer = CommissionDataImporter(mysql_config, minio_config)
    
    # 连接数据库和MinIO
    if not importer.connect_mysql():
        sys.exit(1)
    
    if not importer.connect_minio():
        sys.exit(1)
    
    # 创建表
    if not importer.create_tables():
        sys.exit(1)
    
    # 处理文件
    try:
        importer.process_multiple_pdfs(args.pdf_dir, args.json_dir, args.limit)
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断操作")
    finally:
        importer.close()


if __name__ == "__main__":
    main()

