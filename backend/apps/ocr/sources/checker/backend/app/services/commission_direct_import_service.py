"""
委托单直接导入服务 - 直接导入到业务表
基于用户提供的完整JSON到数据库字段映射关系
"""
import os
import json
import re
import hashlib
import uuid
from pathlib import Path
from datetime import datetime
from flask import current_app

from models import db
from models.commission import CommissionBasic, TestItem, SpecialTest, CommissionOcrResult
from models.file import File
from services.minio_service import MinioService


class CommissionDirectImportService:
    """委托单直接导入服务"""
    
    # JSON字段名 → 数据库字段名映射（commission_basic表）
    FIELD_MAPPING = {
        # 基本信息 - single_cell
        "表格编号": "form_number",
        "委托编号": "commission_number",
        "服务类型": "service_type",
        "是否需要报告": "need_report",
        
        # 委托信息 - adjacent_cells
        "委托部门": "commission_department",
        "委托人": "commissioner",
        "委托日期": "commission_date",
        "委托地址": "commission_address",
        
        # 样品信息 - adjacent_cells
        "样品名称": "sample_name",
        "样品数量": "sample_quantity",
        "样品代码": "sample_code",
        "样品批次": "sample_batch",
        "产品或原材料型号": "product_number",
        "样品重量": "sample_weight",
        "送样时间": "delivery_time",
        "需求时间": "required_time",
        "余样处理": "sample_disposal",
        "样品储存方式": "storage_method",
        "研发项目": "project_number",
        "物料代码": "material_number",
        
        # 测试信息 - adjacent_cells
        "测试性质": "test_nature",
        "测试说明": "test_description",
        "有无特殊条件": "special_condition_flag",
        "条件是": "special_condition_detail",  # 特殊条件详情
        "此次投产数量": "product_quantity",
        
        # 人员信息 - handwritten
        "测试员": "tester",
        "数据复核人": "data_reviewer",
        "复核日期": "review_date",
        
        # 审核检查项 - choice_field
        "申请单是否填写完整": "form_complete",
        "样品实物信息是否一致": "sample_info_consistent",
        "样品是否完好": "sample_condition_ok",
        "其他检查项": "other_notes",
        
        # 签名信息 - handwritten
        "送样人签名": "delivery_person_signature",
        "业务受理人签字": "business_receiver_signature",
    }
    
    # 测试项目表字段映射
    TEST_ITEM_FIELDS = [
        "测试项目",
        "测试设备", 
        "测试标准",
        "测试条件",
        "产品标准",
        "单位",
        "测试结果",
        "测试员",
        "备注"
    ]
    
    TEST_ITEM_DB_MAPPING = {
        "测试项目": "test_item",
        "测试设备": "test_equipment",
        "测试标准": "test_standard",
        "测试条件": "test_condition",
        "产品标准": "product_standard",
        "单位": "unit",
        "测试结果": "test_result",
        "测试员": "tester",
        "备注": "remark"
    }
    
    # 测试结果表（special_tests）字段映射
    SPECIAL_TEST_DB_MAPPING = {
        "元素名称": "element_name",
        "标准": "standard_value",
        "标准值": "standard_value",
        "实测": "measured_value",
        "实测值": "measured_value",
        "备注": "remark"
    }
    
    def __init__(self):
        self.minio_service = MinioService()
    
    def _calculate_md5(self, file_path):
        """计算文件MD5"""
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    def _create_file_record(self, pdf_path, uploader_id=1):
        """
        创建文件记录并上传到MinIO
        
        Args:
            pdf_path: PDF文件路径
            uploader_id: 上传者ID（默认为1，即admin）
            
        Returns:
            File: 创建的文件记录
        """
        pdf_file = Path(pdf_path)
        file_size = pdf_file.stat().st_size
        
        # 上传文件到MinIO
        with open(pdf_path, 'rb') as f:
            upload_result = self.minio_service.upload_file(
                file_obj=f,
                filename=pdf_file.name,
                content_type='application/pdf',
                folder='commissions'  # 使用专门的文件夹存储委托单
            )
        
        if not upload_result:
            raise Exception(f"上传PDF到MinIO失败: {pdf_path}")
        
        # 创建File对象，只传递__init__接受的参数
        file_record = File(
            filename=pdf_file.name,
            stored_filename=upload_result['stored_filename'],
            file_path=upload_result['object_name'],  # 使用MinIO路径
            file_size=file_size,
            file_type='委托单',
            mime_type='application/pdf',
            uploader_id=uploader_id
        )
        
        # 设置其他属性
        file_record.md5_hash = upload_result.get('md5_hash', self._calculate_md5(pdf_path))
        file_record.ocr_status = 'completed'  # 因为我们已经有JSON结果了
        file_record.ocr_completed_at = datetime.utcnow()
        file_record.review_status = 'unassigned'
        file_record.page_count = 1  # 单页PDF
        
        return file_record
    
    def _create_ocr_result_record(self, commission_number, pdf_path, json_data, field_mapping):
        """
        创建OCR结果记录
        
        Args:
            commission_number: 委托编号
            pdf_path: PDF文件路径
            json_data: OCR原始JSON数据
            field_mapping: 字段映射关系
            
        Returns:
            CommissionOcrResult: 创建的OCR结果记录
        """
        extracted_fields = json_data.get('extracted_fields', {})
        total_fields = len(extracted_fields)
        
        # 计算识别的字段数（有些值是字符串，有些是字典）
        recognized_fields = 0
        for f in extracted_fields.values():
            if isinstance(f, dict):
                if f.get('value'):
                    recognized_fields += 1
            elif isinstance(f, str) and f:
                recognized_fields += 1
        
        # 计算平均置信度
        confidences = []
        for field_data in extracted_fields.values():
            if isinstance(field_data, dict) and 'confidence' in field_data:
                try:
                    conf = float(field_data['confidence'])
                    confidences.append(conf)
                except:
                    pass
        
        avg_confidence = f"{sum(confidences) / len(confidences):.2f}" if confidences else "0.00"
        
        ocr_result = CommissionOcrResult(
            commission_number=commission_number,
            original_pdf_path=str(pdf_path),
            ocr_raw_data=json.dumps(json_data, ensure_ascii=False),
            field_mapping=json.dumps(field_mapping, ensure_ascii=False),
            total_fields=total_fields,
            recognized_fields=recognized_fields,
            avg_confidence=avg_confidence,
            ocr_status='completed',
            review_status='pending'
        )
        
        return ocr_result
    
    def import_single_pdf(self, pdf_path, json_base_dir, uploader_id=1):
        """
        导入单个PDF及其JSON数据到业务表
        
        Args:
            pdf_path: PDF文件路径
            json_base_dir: JSON基础目录
            
        Returns:
            dict: 导入结果
        """
        try:
            pdf_file = Path(pdf_path)
            
            if not pdf_file.exists():
                return {
                    'success': False,
                    'message': f'PDF文件不存在: {pdf_path}'
                }
            
            # 查找对应的JSON文件
            json_files = self._find_json_files(pdf_file.name, json_base_dir)
            
            if not json_files:
                return {
                    'success': False,
                    'message': f'未找到对应的JSON文件'
                }
            
            # 提取所有页面的数据
            all_fields = {}
            test_items_data = []
            special_tests_data = []
            
            for json_file_info in json_files:
                json_path = json_file_info['path']
                with open(json_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                extracted_fields = json_data.get('extracted_fields', {})
                
                # 提取基本字段
                for field_name, field_data in extracted_fields.items():
                    value = field_data.get('value', '')
                    # 如果字段已存在，只在当前为空时才更新
                    if field_name not in all_fields or not all_fields[field_name]:
                        all_fields[field_name] = value
                
                # 提取测试项目表
                if '测试项目表' in extracted_fields:
                    test_table = extracted_fields['测试项目表']
                    test_items_data.extend(self._extract_test_items(test_table))
                
                # 提取测试结果表（special_tests）
                if '测试结果表' in extracted_fields:
                    result_table = extracted_fields['测试结果表']
                    special_tests_data.extend(self._extract_special_tests(result_table))
            
            # 映射到数据库字段
            mapped_data = self._map_fields_to_db(all_fields)
            
            if not mapped_data.get('commission_number'):
                return {
                    'success': False,
                    'message': '未找到委托编号'
                }
            
            commission_number = mapped_data['commission_number']
            
            # 检查是否已存在
            existing = CommissionBasic.query.filter_by(
                commission_number=commission_number
            ).first()
            
            if existing:
                return {
                    'success': False,
                    'message': f'委托编号 {commission_number} 已存在',
                    'commission_number': commission_number
                }
            
            # 插入commission_basic
            commission = CommissionBasic(**mapped_data)
            db.session.add(commission)
            db.session.flush()
            
            commission_id = commission.id
            
            # 插入test_items
            test_items_count = 0
            for test_item_data in test_items_data:
                test_item = TestItem(
                    commission_number=commission_number,
                    **test_item_data
                )
                db.session.add(test_item)
                test_items_count += 1
            
            # 插入special_tests
            special_tests_count = 0
            for special_test_data in special_tests_data:
                special_test = SpecialTest(
                    commission_number=commission_number,
                    **special_test_data
                )
                db.session.add(special_test)
                special_tests_count += 1
            
            # 创建文件记录
            file_record = self._create_file_record(pdf_path, uploader_id)
            db.session.add(file_record)
            db.session.flush()
            
            # 创建OCR结果记录
            # 合并所有JSON数据用于OCR记录
            combined_json = {
                'extracted_fields': all_fields,
                'test_items': test_items_data,
                'special_tests': special_tests_data
            }
            ocr_result = self._create_ocr_result_record(
                commission_number=commission_number,
                pdf_path=pdf_path,
                json_data=combined_json,
                field_mapping=self.FIELD_MAPPING
            )
            db.session.add(ocr_result)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': '导入成功',
                'commission_number': commission_number,
                'commission_id': commission_id,
                'file_id': file_record.id,
                'ocr_result_id': ocr_result.id,
                'pdf_filename': pdf_file.name,
                'extracted_fields': len(all_fields),
                'test_items_count': test_items_count,
                'special_tests_count': special_tests_count
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'导入失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'message': f'导入失败: {str(e)}'
            }
    
    def import_multiple_pdfs(self, pdf_dir, json_base_dir, limit=None, uploader_id=1):
        """
        批量导入多个PDF
        
        Args:
            pdf_dir: PDF目录
            json_base_dir: JSON基础目录
            limit: 限制处理数量
            uploader_id: 上传者ID
            
        Returns:
            dict: 批量导入结果
        """
        pdf_dir = Path(pdf_dir)
        
        if not pdf_dir.exists():
            return {
                'success': False,
                'message': f'PDF目录不存在: {pdf_dir}'
            }
        
        # 获取所有PDF文件
        pdf_files = sorted(pdf_dir.glob('*.pdf'))
        
        if limit:
            pdf_files = pdf_files[:limit]
        
        results = {
            'total': len(pdf_files),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'details': []
        }
        
        for pdf_file in pdf_files:
            result = self.import_single_pdf(str(pdf_file), json_base_dir, uploader_id=uploader_id)
            
            detail = {
                'filename': pdf_file.name,
                'success': result['success'],
                'message': result.get('message', ''),
                'commission_number': result.get('commission_number')
            }
            
            if result['success']:
                detail['test_items_count'] = result.get('test_items_count', 0)
                detail['special_tests_count'] = result.get('special_tests_count', 0)
                results['success'] += 1
            elif 'already exists' in result.get('message', '') or '已存在' in result.get('message', ''):
                results['skipped'] += 1
            else:
                results['failed'] += 1
            
            results['details'].append(detail)
        
        return results
    
    def _find_json_files(self, pdf_filename, json_base_dir):
        """查找PDF对应的JSON文件"""
        # 移除.pdf后缀
        pdf_name_without_ext = pdf_filename.replace('.pdf', '').replace('.PDF', '')
        
        # 尝试两种目录结构：multi_page_results 和 single_page_results
        json_dirs = [
            Path(json_base_dir) / 'multi_page_results' / pdf_name_without_ext,
            Path(json_base_dir) / 'single_page_results' / pdf_name_without_ext
        ]
        
        json_files = []
        
        for json_dir in json_dirs:
            if not json_dir.exists():
                continue
            
            # 查找所有的6.3_field_extraction_results.json文件
            for page_dir in sorted(json_dir.glob('page_*_results')):
                json_file = page_dir / 'steps' / 'step06' / '6.3_field_extraction_results.json'
                if json_file.exists():
                    # 提取页码
                    match = re.search(r'page_(\d+)_results', page_dir.name)
                    page_number = int(match.group(1)) if match else 0
                    json_files.append({
                        'path': str(json_file),
                        'page_number': page_number
                    })
            
            # 如果在这个目录找到了，就不再查找其他目录
            if json_files:
                break
            
            # 如果是单页结果，直接查找steps目录
            json_file = json_dir / 'steps' / 'step06' / '6.3_field_extraction_results.json'
            if json_file.exists():
                json_files.append({
                    'path': str(json_file),
                    'page_number': 1
                })
                break
        
        return json_files
    
    def _extract_test_items(self, test_table_data):
        """
        从测试项目表中提取数据
        
        Args:
            test_table_data: 测试项目表的JSON数据
            
        Returns:
            list: 测试项目列表
        """
        test_items = []
        
        if not isinstance(test_table_data, dict):
            return test_items
        
        table_type = test_table_data.get('table_type', '')
        data_list = test_table_data.get('data', [])
        
        if not isinstance(data_list, list):
            return test_items
        
        for row_data in data_list:
            if not isinstance(row_data, dict):
                continue
            
            # 映射字段
            test_item = {}
            for json_field, db_field in self.TEST_ITEM_DB_MAPPING.items():
                value = row_data.get(json_field, '')
                if value:
                    test_item[db_field] = self._clean_string(value)
            
            # 至少要有测试项目字段才添加
            if test_item.get('test_item'):
                test_items.append(test_item)
        
        return test_items
    
    def _extract_special_tests(self, result_table_data):
        """
        从测试结果表中提取special_tests数据
        
        结构：
        {
          "tests": [
            {
              "test_name": "RoHs",
              "data": [
                {"元素名称": "铅（Pb）", "标准": "<1000", "实测": "ND", "备注": ""}
              ]
            }
          ]
        }
        
        Args:
            result_table_data: 测试结果表的JSON数据
            
        Returns:
            list: 特殊测试列表
        """
        special_tests = []
        
        if not isinstance(result_table_data, dict):
            return special_tests
        
        tests_list = result_table_data.get('tests', [])
        
        if not isinstance(tests_list, list):
            return special_tests
        
        for test_group in tests_list:
            if not isinstance(test_group, dict):
                continue
            
            test_type = test_group.get('test_name', '')
            data_list = test_group.get('data', [])
            
            if not isinstance(data_list, list):
                continue
            
            for row_data in data_list:
                if not isinstance(row_data, dict):
                    continue
                
                # 映射字段
                special_test = {
                    'test_type': test_type
                }
                
                for json_field, db_field in self.SPECIAL_TEST_DB_MAPPING.items():
                    value = row_data.get(json_field, '')
                    if value and db_field not in special_test:
                        special_test[db_field] = self._clean_string(value)
                
                # 至少要有元素名称才添加
                if special_test.get('element_name'):
                    special_tests.append(special_test)
        
        return special_tests
    
    def _map_fields_to_db(self, fields):
        """将JSON字段映射到数据库字段"""
        mapped = {}
        
        for json_field, value in fields.items():
            if json_field in self.FIELD_MAPPING:
                db_field = self.FIELD_MAPPING[json_field]
                converted_value = self._convert_field_value(db_field, value)
                mapped[db_field] = converted_value
        
        return mapped
    
    def _convert_field_value(self, db_field_name, value):
        """转换字段值到正确的数据类型"""
        if not value:
            return None
        
        # 日期字段
        if db_field_name in ['commission_date', 'required_time', 'review_date']:
            return self._parse_date(value)
        
        # 日期时间字段
        if db_field_name in ['delivery_time']:
            return self._parse_datetime(value)
        
        # 布尔字段
        if db_field_name in ['need_report', 'special_condition_flag', 
                            'form_complete', 'sample_info_consistent', 
                            'sample_condition_ok']:
            return self._parse_boolean(value)
        
        # 字符串字段（清理）
        return self._clean_string(value)
    
    def _parse_date(self, date_str):
        """解析日期字符串"""
        if not date_str:
            return None
        
        date_str = str(date_str).strip()
        
        # 尝试各种格式
        patterns = [
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d'),
            (r'(\d{4})/(\d{1,2})/(\d{1,2})', '%Y/%m/%d'),
            (r'(\d{4})(\d{2})(\d{2})', '%Y%m%d'),
            (r'(\d{4})年(\d{1,2})月(\d{1,2})日?', None),
        ]
        
        for pattern, fmt in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if fmt:
                        date_obj = datetime.strptime(match.group(0), fmt)
                    else:
                        # 中文格式
                        year, month, day = match.groups()
                        date_obj = datetime(int(year), int(month), int(day))
                    
                    return date_obj.date()
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _parse_datetime(self, datetime_str):
        """解析日期时间字符串"""
        if not datetime_str:
            return None
        
        datetime_str = str(datetime_str).strip()
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d %H:%M',
            '%Y/%m/%d',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(datetime_str, fmt)
            except ValueError:
                continue
        
        # 尝试先解析日期部分
        date_part = self._parse_date(datetime_str)
        if date_part:
            return datetime.combine(date_part, datetime.min.time())
        
        return None
    
    def _parse_boolean(self, value):
        """解析布尔值"""
        if not value:
            return None
        
        value_str = str(value).strip().lower()
        
        if value_str in ['是', 'yes', 'y', '1', 'true', '√', '✓']:
            return '是'
        elif value_str in ['否', 'no', 'n', '0', 'false', '×', '✗']:
            return '否'
        
        return value
    
    def _clean_string(self, value):
        """清理字符串"""
        if not value:
            return ''
        
        # 移除多余的空白字符
        value = ' '.join(str(value).split())
        
        return value.strip()
