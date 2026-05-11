"""
委托单OCR适配器
处理委托单文档的OCR识别结果、数据持久化和业务逻辑
"""
from typing import Dict, Any, Optional, Tuple, List
from models import db, get_models
from .base_ocr_adapter import BaseOCRAdapter, ParseError, SaveError, ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import pymysql
import re
import logging
from datetime import datetime
from flask import current_app

logger = logging.getLogger(__name__)

# 获取模型
models = get_models()
CommissionBasic = models['CommissionBasic']
TestItem = models['TestItem']
SpecialTest = models['SpecialTest']
CommissionOcrResult = models.get('CommissionOcrResult')
File = models['File']


class CommissionAdapter(BaseOCRAdapter):
    """
    委托单OCR适配器
    
    负责：
    1. 解析委托单OCR识别结果 (parse_ocr_result)
    2. 验证委托单数据 (validate_data)
    3. 保存委托单数据到数据库 (save_to_database)
    4. 从数据库获取委托单数据 (get_from_database)
    5. 更新委托单数据 (update_in_database)
    6. 删除委托单数据 (delete_from_database)
    7. 从文件中提取委托编号等辅助方法
    """
    
    def parse_ocr_result(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析委托单OCR结果（新格式）
        
        Args:
            raw_data: OCR服务返回的原始数据
            格式: {
                "success": true,
                "message": "...",
                "data": {
                    "total_pages": 2,
                    "ocr_raw_data": [...],
                    "field_extraction_results": [...],
                    "combined_results": {...}
                },
                "processing_time": 15.3
            }
            
        Returns:
            {
                'basic_info': {...},      # 基本信息字典
                'test_items': [...],      # 测试项目列表
                'special_tests': [...]    # 特殊测试列表
            }
        """
        self.log_info("开始解析委托单OCR结果（新格式）")
        
        # 中文字段名到英文字段名的映射
        field_name_mapping = {
            '表格编号': 'form_number',
            '委托编号': 'commission_number',
            '服务类型': 'service_type',
            '是否需要报告': 'need_report',
            '研发项目': 'project_number',
            '物料代码': 'material_number',
            '产品或原材料型号': 'product_number',
            '样品重量': 'sample_weight',
            '委托部门': 'commission_department',
            '委托人': 'commissioner',
            '委托日期': 'commission_date',
            '委托地址': 'commission_address',
            '样品名称': 'sample_name',
            '样品数量': 'sample_quantity',
            '样品代码': 'sample_code',
            '样品批次': 'sample_batch',
            '送样时间': 'delivery_time',
            '需求时间': 'required_time',
            '余样处理': 'sample_disposal',
            '样品储存方式': 'storage_method',
            '测试性质': 'test_nature',
            '测试说明': 'test_description',
            '有无特殊条件': 'special_condition_flag',
            '条件是': 'special_condition_detail',
            '测试员': 'tester',
            '数据复核人': 'data_reviewer',
            '复核日期': 'review_date',
            '送样人签名': 'delivery_person_signature',
            '样品是否完好': 'sample_condition',
            '业务受理人签字': 'business_handler_signature',
            '申请单是否填写完整': 'form_complete',
            '样品实物信息是否一致': 'sample_info_consistent'
        }
        
        try:
            structured_data = {
                'basic_info': {},
                'test_items': [],
                'special_tests': []
            }
            
            # 从新格式中提取data字段
            if 'data' not in raw_data:
                self.log_warning("响应中缺少data字段")
                return structured_data
            
            data_content = raw_data['data']
            self.log_info(f"发现data字段，键: {list(data_content.keys())}")
            
            # 从field_extraction_results提取（委托单OCR的标准格式）
            if 'field_extraction_results' in data_content:
                field_results = data_content['field_extraction_results']
                
                if isinstance(field_results, list) and len(field_results) > 0:
                    # 临时存储：字段名 -> 页面号 -> 字段值
                    all_fields_by_page = {}
                    
                    # 第一遍：收集所有页面的所有字段
                    for page_idx, page_data in enumerate(field_results):
                        page_number = page_idx + 1
                        self.log_info(f"处理第 {page_number} 页的字段")
                        
                        if isinstance(page_data, dict) and 'extracted_fields' in page_data:
                            extracted_fields = page_data['extracted_fields']
                            field_names = list(extracted_fields.keys())
                            self.log_info(f"  第 {page_number} 页包含 {len(field_names)} 个字段")
                            self.log_info(f"  字段列表: {field_names}")
                            
                            # 特别检查表格编号
                            if '表格编号' in field_names:
                                self.log_info(f"  ✅ 发现'表格编号'字段，值: {extracted_fields['表格编号']}")
                            else:
                                self.log_warning(f"  ⚠️ 第{page_number}页未找到'表格编号'字段")
                            
                            # 收集每个字段
                        for field_name, field_data in extracted_fields.items():
                                if field_name not in all_fields_by_page:
                                    all_fields_by_page[field_name] = {}
                                all_fields_by_page[field_name][page_number] = field_data
                    
                    # 第二遍：合并字段（优先非空值，都非空时取第一页）
                    for field_name, pages_data in all_fields_by_page.items():
                        # 映射中文字段名到英文
                        en_field_name = field_name_mapping.get(field_name, field_name)
                        
                        # 按页码排序，优先处理第一页
                        sorted_pages = sorted(pages_data.keys())
                        
                        final_value = None
                        field_data_to_use = None
                        
                        # 遍历所有页面，找到第一个非空值
                        for page_num in sorted_pages:
                            field_data = pages_data[page_num]
                            
                            # 处理数组类型（跨页重复的字段）
                            if isinstance(field_data, list):
                                for item in field_data:
                                    if isinstance(item, dict) and 'value' in item:
                                        value = item['value']
                                        if value and not final_value:
                                            final_value = value
                                            self.log_info(f"  [{field_name}] 从第{page_num}页数组中获取: {value}")
                                            break
                                if final_value:
                                    break
                                continue
                            
                            # 处理字典类型
                            if isinstance(field_data, dict):
                                field_type = field_data.get('type', '')
                                
                                # 处理表格类型字段（只处理一次，不合并）
                                # 注意：排除"表格编号"这种包含"表"但不是表格的字段
                                is_table_field = (
                                    field_type == 'multi_row_table' or 
                                    ('表' in field_name and field_name not in ['表格编号'])
                                )
                                
                                if is_table_field:
                                    if page_num == sorted_pages[0]:  # 只在第一次遇到时处理
                                        self._parse_table_field(field_name, field_data, structured_data)
                                        self.log_info(f"  [{field_name}] 从第{page_num}页提取表格数据")
                                    break
                                
                                # 处理普通字段
                                elif 'value' in field_data:
                                    value = field_data['value']
                                    if value and not final_value:
                                        final_value = value
                                        self.log_info(f"  [{field_name}] 从第{page_num}页获取: {value}")
                                        break
                            
                            # 处理简单类型
                            elif isinstance(field_data, (str, int, float)):
                                if field_data and not final_value:
                                    final_value = field_data
                                    self.log_info(f"  [{field_name}] 从第{page_num}页获取简单值: {final_value}")
                                    break
                        
                        # 保存最终值
                        if final_value:
                            structured_data['basic_info'][en_field_name] = str(final_value)
            
            # 如果没有找到数据，尝试从combined_results提取
            if not structured_data['basic_info'] and 'combined_results' in data_content:
                combined = data_content['combined_results']
                if 'combined_field_data' in combined:
                    extracted = combined['combined_field_data'].get('all_extracted_fields', {})
                    structured_data['basic_info'] = extracted
            
            self.log_info(f"解析完成 - 基本信息: {len(structured_data['basic_info'])} 个字段, "
                         f"测试项: {len(structured_data['test_items'])} 个, "
                         f"特殊测试: {len(structured_data['special_tests'])} 个")
            
            # 打印完整的basic_info字段列表
            self.log_info("=" * 80)
            self.log_info("📋 最终解析的 basic_info 字段列表:")
            for idx, (key, value) in enumerate(structured_data['basic_info'].items(), 1):
                self.log_info(f"  {idx}. {key} = {value}")
            self.log_info("=" * 80)
            
            return structured_data
            
        except Exception as e:
            error_msg = f"解析委托单OCR结果失败: {str(e)}"
            self.log_error(error_msg)
            raise ParseError(error_msg) from e
    
    def _parse_table_field(self, field_name: str, field_data: Dict, structured_data: Dict):
        """解析表格字段，支持两种结构：
        1. 标准表格: {'data': [...]}
        2. 多测试表格: {'tests': [{'test_name': '...', 'data': [...]}, ...]}
        """
        # 字段映射
        test_item_mapping = {
            '测试项目': 'test_item',
            '测试设备': 'test_equipment',
            '测试标准': 'test_standard',
            '测试条件': 'test_condition',
            '产品标准': 'product_standard',
            '单位': 'unit',
            '测试结果': 'test_result',
            '测试员': 'tester',
            '备注': 'remark'
        }
        
        special_test_mapping = {
            '测试类型': 'test_type',
            '元素名称': 'element_name',
            '标准值': 'standard_value',
            '标准': 'standard_value',  # 添加映射
            '实测值': 'measured_value',
            '实测': 'measured_value',  # 添加映射
            '备注': 'remark'
        }
        
        # 检查是否是多测试表格（包含tests数组）
        if 'tests' in field_data:
            self.log_info(f"解析多测试表格: {field_name}, 包含 {len(field_data['tests'])} 个测试组")
            
            for test_group in field_data['tests']:
                test_name = test_group.get('test_name', 'unknown')
                test_rows = test_group.get('data', [])
                
                self.log_info(f"  处理测试组: {test_name}, 包含 {len(test_rows)} 行数据")
                
                for row_idx, row in enumerate(test_rows):
                    if not isinstance(row, dict):
                        continue
                    
                    mapped_row = {
                        'test_type': test_name,  # 添加测试类型标识
                        'sort_order': row_idx
                    }
                    
                    # 映射字段
                    for cn_key, value in row.items():
                        en_key = special_test_mapping.get(cn_key, cn_key)
                        mapped_row[en_key] = value
                    
                    structured_data['special_tests'].append(mapped_row)
                    
            return  # 处理完多测试表格后直接返回
        
        # 处理标准表格（单一data数组）
        if 'data' not in field_data:
            return
        
        table_rows = field_data['data']
        self.log_info(f"解析表格字段: {field_name}, 包含 {len(table_rows)} 行")
        
        # 转换表格行
        for row_idx, row in enumerate(table_rows):
            if not isinstance(row, dict):
                continue
            
            # 判断是测试项目还是特殊测试
            if '测试项目' in field_name or 'test_item' in field_name.lower():
                mapped_row = {}
                for cn_key, value in row.items():
                    en_key = test_item_mapping.get(cn_key, cn_key)
                    mapped_row[en_key] = value
                
                if 'sort_order' not in mapped_row:
                    mapped_row['sort_order'] = row_idx
                
                structured_data['test_items'].append(mapped_row)
                
            elif '特殊测试' in field_name or '测试结果表' in field_name or 'special' in field_name.lower() or 'rohs' in field_name.lower():
                mapped_row = {}
                for cn_key, value in row.items():
                    en_key = special_test_mapping.get(cn_key, cn_key)
                    mapped_row[en_key] = value
                
                if 'sort_order' not in mapped_row:
                    mapped_row['sort_order'] = row_idx
                
                structured_data['special_tests'].append(mapped_row)
    
    def save_to_database(self, structured_data: Dict[str, Any], file_id: int) -> Tuple[bool, Optional[str]]:
        """
        保存委托单数据到数据库
        
        Args:
            structured_data: OCR结果数据，支持两种格式：
                1. OCR格式: {'extracted_fields': {...}, 'test_items': [...], 'special_tests': [...]}
                2. 标准格式: {'basic_info': {...}, 'test_items': [...], 'special_tests': [...]}
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        self.log_info(f"保存委托单数据到数据库，文件ID: {file_id}")
        
        try:
            # 处理数据格式转换
            # 兼容两种格式：extracted_fields（OCR结果）和 basic_info（前端表单）
            if 'extracted_fields' in structured_data:
                # OCR格式，转换为标准格式
                self.log_info("检测到OCR格式数据，转换为标准格式")
                normalized_data = {
                    'basic_info': structured_data.get('extracted_fields', {}),
                    'test_items': structured_data.get('test_items', []),
                    'special_tests': structured_data.get('special_tests', [])
                }
            elif 'basic_info' in structured_data:
                # 已经是标准格式
                self.log_info("数据已是标准格式")
                normalized_data = structured_data
            else:
                # 兼容旧格式：直接把整个 structured_data 当作 basic_info
                self.log_info("检测到旧格式数据，尝试转换")
                normalized_data = {
                    'basic_info': structured_data,
                    'test_items': [],
                    'special_tests': []
                }
            
            # 打印接收到的数据（用于调试）
            basic_info = normalized_data.get('basic_info', {})
            test_items = normalized_data.get('test_items', [])
            special_tests = normalized_data.get('special_tests', [])
            
            self.log_info("=" * 80)
            self.log_info(f"📥 [CommissionAdapter] 接收到的数据:")
            self.log_info(f"  basic_info: {len(basic_info)} 个字段")
            self.log_info(f"  test_items: {len(test_items)} 项")
            self.log_info(f"  special_tests: {len(special_tests)} 项")
            if basic_info:
                self.log_info(f"  basic_info 字段列表: {list(basic_info.keys())}")
            self.log_info("=" * 80)
            
            # 验证数据
            is_valid, errors = self.validate_data(normalized_data)
            if not is_valid:
                error_msg = f"数据验证失败: {', '.join(errors)}"
                self.log_error(error_msg)
                return False, error_msg
            
            # 生成委托编号（如果没有）
            commission_number = basic_info.get('commission_number')
            if not commission_number:
                import time
                commission_number = f"COM{int(time.time() * 1000) % 100000000:08d}"
                basic_info['commission_number'] = commission_number
            
            # 检查委托编号是否已存在
            existing = CommissionBasic.query.filter_by(commission_number=commission_number).first()
            if existing:
                # 如果已存在，删除旧数据
                self.log_info(f"委托编号 {commission_number} 已存在，删除旧数据")
                db.session.delete(existing)
            
            # 保存基本信息
            basic_info_copy = basic_info.copy()
            
            # 转换日期字段格式
            date_fields = ['commission_date', 'delivery_time', 'required_time', 'review_date']
            for field in date_fields:
                if field in basic_info_copy:
                    basic_info_copy[field] = self._convert_date_format(basic_info_copy[field])
            
            commission_basic = CommissionBasic(**basic_info_copy)
            db.session.add(commission_basic)
            
            # 保存测试项目
            for i, item_data in enumerate(test_items):
                item_data['commission_number'] = commission_number
                if 'sort_order' not in item_data:
                    item_data['sort_order'] = i
                test_item = TestItem(**item_data)
                db.session.add(test_item)
            
            # 保存特殊测试
            for i, test_data in enumerate(special_tests):
                test_data['commission_number'] = commission_number
                if 'sort_order' not in test_data:
                    test_data['sort_order'] = i
                special_test = SpecialTest(**test_data)
                db.session.add(special_test)
            
            # 提交事务
            db.session.commit()
            
            self.log_info(f"委托单数据保存成功，委托编号: {commission_number}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"保存委托单数据失败: {str(e)}"
            self.log_error(error_msg)
            return False, error_msg
    
    def get_from_database(self, file_id: int) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        从数据库获取委托单数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, structured_data, error_message)
        """
        self.log_info(f"从数据库获取委托单数据，文件ID: {file_id}")
        
        try:
            # 使用业务逻辑方法获取数据
            data = self.get_commission_data_by_file_id(file_id)
            
            if data is None:
                # 未找到数据，返回空结构
                self.log_info("未找到委托单数据，返回空结构")
            return True, {
                'basic_info': {},
                'test_items': [],
                'special_tests': []
            }, None
            
            # 打印返回的数据结构
            self.log_info("=" * 80)
            self.log_info(f"📦 [get_from_database] 从数据库获取到的数据:")
            self.log_info(f"  basic_info 字段数: {len(data.get('basic_info', {}))}")
            self.log_info(f"  test_items 数量: {len(data.get('test_items', []))}")
            self.log_info(f"  special_tests 数量: {len(data.get('special_tests', []))}")
            self.log_info("  basic_info 字段列表:")
            for idx, key in enumerate(data.get('basic_info', {}).keys(), 1):
                self.log_info(f"    {idx}. {key}")
            self.log_info("=" * 80)
            
            return True, data, None
            
        except Exception as e:
            error_msg = f"获取委托单数据失败: {str(e)}"
            self.log_error(error_msg)
            return False, None, error_msg
    
    def validate_data(self, structured_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证委托单数据
        
        Args:
            structured_data: 待验证的数据
            
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # 验证基本信息
        if not structured_data.get('basic_info'):
            errors.append("缺少基本信息")
        
        # 验证测试项目格式
        test_items = structured_data.get('test_items', [])
        if not isinstance(test_items, list):
            errors.append("测试项目格式错误，必须是列表")
        
        # 验证特殊测试格式
        special_tests = structured_data.get('special_tests', [])
        if not isinstance(special_tests, list):
            errors.append("特殊测试格式错误，必须是列表")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.log_info("数据验证通过")
        else:
            self.log_warning(f"数据验证失败: {errors}")
        
        return is_valid, errors
    
    def delete_from_database(self, file_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除委托单数据（基础方法：通过file_id删除）
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        self.log_info(f"删除委托单数据，文件ID: {file_id}")
        
        # 调用更完善的删除方法
        return self.delete_commission_by_file_id(file_id)
    
    def update_in_database(self, structured_data: Dict[str, Any], file_id: int) -> Tuple[bool, Optional[str]]:
        """
        更新委托单数据（基础方法：通过file_id更新）
        
        Args:
            structured_data: 更新后的数据
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        self.log_info(f"更新委托单数据，文件ID: {file_id}")
        
        # 从structured_data中提取commission_number
        commission_number = structured_data.get('basic_info', {}).get('commission_number')
        
        if not commission_number:
            return False, "缺少委托编号"
        
        # 使用commission_number调用更新方法，并传递file_id
        return self.update_commission_by_number(commission_number, structured_data, file_id)
    
    # ==================== 业务逻辑方法（从 FileService 迁移） ====================
    
    def _get_db_connection(self):
        """获取数据库连接"""
        try:
            return pymysql.connect(
                host=current_app.config.get('MYSQL_HOST', '172.20.46.24'),
                port=current_app.config.get('MYSQL_PORT', 3306),
                user=current_app.config.get('MYSQL_USER', 'root'),
                password=current_app.config.get('MYSQL_PASSWORD', 'bigdata206.'),
                database=current_app.config.get('MYSQL_DB', 'ocr_system'),
                charset='utf8mb4',
                autocommit=False
            )
        except Exception as e:
            self.log_error(f"数据库连接失败: {str(e)}")
            raise
    
    def _convert_date_format(self, value):
        """转换日期格式为MySQL兼容格式"""
        if not value or value is None:
            return None
        
        if isinstance(value, str):
            try:
                # 处理常见的OCR错误：日期和时间之间缺少空格
                # 例如：'2025-06-1318:48' -> '2025-06-13 18:48'
                match = re.match(r'(\d{4})-(\d{2})-(\d{2})(\d{2}):(\d{2})', value)
                if match:
                    year, month, day, hour, minute = match.groups()
                    value = f'{year}-{month}-{day} {hour}:{minute}'
                    self.log_info(f'修正日期格式: {match.group(0)} -> {value}')
                
                # 使用dateutil解析
                from dateutil import parser
                dt = parser.parse(value)
                
                # 返回MySQL格式
                if ':' in str(value):  # 包含时间
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                else:  # 只有日期
                    return dt.strftime('%Y-%m-%d')
            except Exception as e:
                self.log_warning(f'日期格式转换失败: {value}, 错误: {e}')
                return None
        return value
    
    def _truncate_field(self, value, max_length: int, field_name: str = ''):
        """截断字段到指定长度"""
        if value and len(str(value)) > max_length:
            self.log_warning(f'{field_name}过长（{len(str(value))}字符），截断到{max_length}字符')
            return str(value)[:max_length]
        return value
    
    def extract_commission_number_from_filename(self, filename: str) -> Optional[str]:
        """
        从文件名中提取委托编号
        
        Args:
            filename: 文件名
            
        Returns:
            委托编号或None
        """
        try:
            # 常见的委托编号格式模式
            patterns = [
                r'IBTC\d{8}\d{3}',  # IBTC20230421001
                r'IBTC\d{10,}',     # IBTC开头的长数字
                r'[A-Z]{2,4}\d{8,}', # 字母+数字组合
                r'\d{4}OA_?\d+',    # 20234OA_1 格式
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filename)
                if match:
                    commission_number = match.group(0)
                    self.log_info(f'从文件名提取到委托编号: {commission_number}')
                    return commission_number
            
            self.log_info(f'未能从文件名提取委托编号: {filename}')
            return None
            
        except Exception as e:
            self.log_error(f'从文件名提取委托编号失败: {str(e)}')
            return None
    
    def get_commission_number_from_file(self, file_id: int) -> Optional[str]:
        """
        从文件记录中获取委托编号
        
        Args:
            file_id: 文件ID
            
        Returns:
            委托编号或None
        """
        try:
            # 获取文件记录
            file_record = File.query.get(file_id)
            if not file_record:
                self.log_error(f'文件记录不存在，file_id: {file_id}')
                return None
            
            self.log_info(f'文件记录找到: filename={file_record.filename}')
            
            connection = self._get_db_connection()
            cursor = connection.cursor()
            
            try:
                # 方案1: 通过文件路径精确匹配
                if hasattr(file_record, 'file_path') and file_record.file_path:
                    stored_path = file_record.file_path
                    self.log_info(f'使用文件路径查询: {stored_path}')
                    
                    if CommissionOcrResult:
                        cursor.execute(
                            'SELECT commission_number FROM commission_ocr_results WHERE original_pdf_path = %s',
                            (stored_path,)
                        )
                        result = cursor.fetchone()
                        
                        if result:
                            commission_number = result[0]
                            self.log_info(f'通过文件路径获取到委托编号: {commission_number}')
                            cursor.close()
                            connection.close()
                            return commission_number
                
                # 方案2: 通过filename进行LIKE查询
                if hasattr(file_record, 'filename') and file_record.filename:
                    self.log_info(f'尝试通过filename查询: {file_record.filename}')
                    
                    if CommissionOcrResult:
                        cursor.execute(
                            'SELECT commission_number FROM commission_ocr_results WHERE original_pdf_path LIKE %s ORDER BY id DESC LIMIT 1',
                            (f'%{file_record.filename}',)
                        )
                        result = cursor.fetchone()
                        
                        if result:
                            commission_number = result[0]
                            self.log_info(f'通过filename LIKE查询获取到委托编号: {commission_number}')
                            cursor.close()
                            connection.close()
                            return commission_number
                
                cursor.close()
                connection.close()
                
            except Exception as db_error:
                self.log_error(f'数据库查询失败: {db_error}')
                if cursor:
                    cursor.close()
                if connection:
                    connection.close()
            
            # 尝试从文件名中提取委托编号
            filename = getattr(file_record, 'original_filename', None) or file_record.filename
            commission_number = self.extract_commission_number_from_filename(filename)
            
            if commission_number:
                self.log_info(f'从文件名中提取到委托编号: {commission_number}')
                return commission_number
            
            self.log_warning(f'无法从文件中提取委托编号')
            return None
            
        except Exception as e:
            self.log_error(f'获取委托编号失败: {str(e)}')
            import traceback
            self.log_error(f'错误详情: {traceback.format_exc()}')
            return None
    
    def get_commission_data_by_file_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        根据文件ID获取委托数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            委托数据字典或None
        """
        try:
            self.log_info(f'开始获取委托数据，file_id: {file_id}')
            
            # 获取委托编号
            commission_number = self.get_commission_number_from_file(file_id)
            
            if not commission_number:
                self.log_warning('未找到委托编号，可能是非委托文件')
                return None
            
            # 根据委托编号获取数据
            return self.get_commission_data_by_number(commission_number)
            
        except Exception as e:
            self.log_error(f'获取委托数据失败: {str(e)}')
            return None
    
    def get_commission_data_by_number(self, commission_number: str) -> Optional[Dict[str, Any]]:
        """
        根据委托编号获取委托数据
        
        Args:
            commission_number: 委托编号
            
        Returns:
            委托数据字典或None
        """
        try:
            self.log_info(f'开始查询委托数据，委托编号: {commission_number}')
            
            connection = self._get_db_connection()
            cursor = connection.cursor()
            
            # 查询基本信息
            cursor.execute('SELECT * FROM commission_basic WHERE commission_number = %s', (commission_number,))
            basic_info_result = cursor.fetchone()
            self.log_info(f'基本信息查询结果: {basic_info_result is not None}')
            
            # 查询测试项目
            cursor.execute('SELECT * FROM test_items WHERE commission_number = %s ORDER BY sort_order', (commission_number,))
            test_items_results = cursor.fetchall()
            self.log_info(f'测试项目数量: {len(test_items_results)}')
            
            # 查询特殊测试
            cursor.execute('SELECT * FROM special_tests WHERE commission_number = %s ORDER BY sort_order', (commission_number,))
            special_tests_results = cursor.fetchall()
            self.log_info(f'特殊测试数量: {len(special_tests_results)}')
            
            # 查询OCR结果
            if CommissionOcrResult:
                cursor.execute('SELECT * FROM commission_ocr_results WHERE commission_number = %s', (commission_number,))
                ocr_result_data = cursor.fetchone()
                self.log_info(f'OCR结果查询: {ocr_result_data is not None}')
            
            # 转换为字典格式
            basic_info = None
            if basic_info_result:
                cursor.execute("SHOW COLUMNS FROM commission_basic")
                all_columns = [col[0] for col in cursor.fetchall()]
                basic_info = dict(zip(all_columns, basic_info_result))
                
                # 格式化日期和时间字段
                for key, value in basic_info.items():
                    if isinstance(value, datetime):
                        basic_info[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif hasattr(value, 'strftime'):  # date类型
                        basic_info[key] = value.strftime('%Y-%m-%d')
            
            # 转换测试项目
            test_items = []
            if test_items_results:
                cursor.execute("SHOW COLUMNS FROM test_items")
                test_columns = [col[0] for col in cursor.fetchall()]
                for row in test_items_results:
                    item = dict(zip(test_columns, row))
                    # 格式化日期字段
                    for key, value in item.items():
                        if isinstance(value, datetime):
                            item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif hasattr(value, 'strftime'):
                            item[key] = value.strftime('%Y-%m-%d')
                    test_items.append(item)
            
            # 转换特殊测试
            special_tests = []
            if special_tests_results:
                cursor.execute("SHOW COLUMNS FROM special_tests")
                special_columns = [col[0] for col in cursor.fetchall()]
                for row in special_tests_results:
                    item = dict(zip(special_columns, row))
                    for key, value in item.items():
                        if isinstance(value, datetime):
                            item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                        elif hasattr(value, 'strftime'):
                            item[key] = value.strftime('%Y-%m-%d')
                    special_tests.append(item)
            
            cursor.close()
            connection.close()
            
            if not basic_info:
                self.log_warning(f'未找到委托数据: {commission_number}')
                return None
            
            result = {
                'basic_info': basic_info,
                'test_items': test_items,
                'special_tests': special_tests
            }
            
            self.log_info(f'成功获取委托数据: {commission_number}')
            return result
            
        except Exception as e:
            self.log_error(f'获取委托数据失败: {str(e)}')
            import traceback
            self.log_error(f'错误详情: {traceback.format_exc()}')
            return None
    
    def update_commission_by_number(
        self,
        commission_number: str,
        data: Dict[str, Any],
        file_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        根据委托编号更新委托数据
        
        Args:
            commission_number: 委托编号
            data: 更新的数据，格式：
                {
                    'basic_info': {...},
                    'test_items': [...],
                    'special_tests': [...]
                }
            file_id: 文件ID（可选，如果提供则建立file_id到commission_number的映射）
                
        Returns:
            (success, error_message)
        """
        try:
            self.log_info(f'开始更新委托数据: {commission_number}')
            
            connection = self._get_db_connection()
            cursor = connection.cursor()
            
            try:
                # 日期字段列表
                date_fields = ['commission_date', 'delivery_time', 'required_time', 'review_date']
                
                # 系统字段列表
                system_fields = ['id', 'created_at', 'updated_at', 'commission_number']
                
                # 更新基本信息
                if 'basic_info' in data:
                    basic_info_dict = data['basic_info'].copy()
                    
                    # 移除系统字段
                    for field in system_fields:
                        basic_info_dict.pop(field, None)
                    
                    # 转换日期字段
                    for field in date_fields:
                        if field in basic_info_dict:
                            basic_info_dict[field] = self._convert_date_format(basic_info_dict[field])
                    
                    # 检查记录是否存在
                    cursor.execute('SELECT id FROM commission_basic WHERE commission_number = %s', (commission_number,))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # 更新现有记录
                        basic_info_dict['updated_at'] = datetime.now()
                        update_fields = []
                        update_values = []
                        for key, value in basic_info_dict.items():
                            update_fields.append(f"{key} = %s")
                            update_values.append(value)
                        
                        if update_fields:
                            update_values.append(commission_number)
                            sql = f"UPDATE commission_basic SET {', '.join(update_fields)} WHERE commission_number = %s"
                            cursor.execute(sql, update_values)
                            self.log_info('基本信息更新成功')
                    else:
                        # 插入新记录
                        basic_info_dict['created_at'] = datetime.now()
                        basic_info_dict['updated_at'] = datetime.now()
                        fields = ['commission_number'] + [k for k in basic_info_dict.keys() if k != 'id']
                        values = [commission_number] + [basic_info_dict[k] for k in fields[1:]]
                        placeholders = ', '.join(['%s'] * len(fields))
                        sql = f"INSERT INTO commission_basic ({', '.join(fields)}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                        self.log_info('基本信息插入成功')
                
                # 更新测试项目
                if 'test_items' in data:
                    # 删除现有项目
                    cursor.execute('DELETE FROM test_items WHERE commission_number = %s', (commission_number,))
                    
                    # 添加新项目
                    for i, item_data in enumerate(data['test_items']):
                        fields = ['commission_number', 'sort_order', 'created_at'] + [
                            k for k in item_data.keys() 
                            if k not in ['id', 'created_at', 'updated_at', 'commission_number', 'sort_order']
                        ]
                        values = [commission_number, i, datetime.now()] + [item_data.get(k) for k in fields[3:]]
                        placeholders = ', '.join(['%s'] * len(fields))
                        # 使用反引号包裹字段名，避免中文或保留字导致的SQL错误
                        escaped_fields = ', '.join([f'`{field}`' for field in fields])
                        sql = f"INSERT INTO test_items ({escaped_fields}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                    
                    self.log_info(f'测试项目更新成功，共 {len(data["test_items"])} 条')
                
                # 更新特殊测试
                if 'special_tests' in data:
                    # 删除现有项目
                    cursor.execute('DELETE FROM special_tests WHERE commission_number = %s', (commission_number,))
                    
                    # 添加新项目
                    for i, item_data in enumerate(data['special_tests']):
                        fields = ['commission_number', 'sort_order', 'created_at'] + [
                            k for k in item_data.keys() 
                            if k not in ['id', 'created_at', 'updated_at', 'commission_number', 'sort_order']
                        ]
                        values = [commission_number, i, datetime.now()] + [item_data.get(k) for k in fields[3:]]
                        placeholders = ', '.join(['%s'] * len(fields))
                        # 使用反引号包裹字段名，避免中文或保留字导致的SQL错误
                        escaped_fields = ', '.join([f'`{field}`' for field in fields])
                        sql = f"INSERT INTO special_tests ({escaped_fields}) VALUES ({placeholders})"
                        cursor.execute(sql, values)
                    
                    self.log_info(f'特殊测试更新成功，共 {len(data["special_tests"])} 条')
                
                # 如果提供了file_id，建立file_id到commission_number的映射
                if file_id and CommissionOcrResult:
                    try:
                        # 获取文件信息
                        cursor.execute('SELECT file_path, filename FROM files WHERE id = %s', (file_id,))
                        file_info = cursor.fetchone()
                        
                        if file_info:
                            file_path = file_info[0]
                            filename = file_info[1]
                            
                            self.log_info(f'准备创建映射: file_id={file_id}, path={file_path}, commission_number={commission_number}')
                            
                            # 检查是否已存在映射
                            cursor.execute(
                                'SELECT id FROM commission_ocr_results WHERE commission_number = %s',
                                (commission_number,)
                            )
                            existing_mapping = cursor.fetchone()
                            
                            if existing_mapping:
                                # 更新现有映射
                                cursor.execute(
                                    'UPDATE commission_ocr_results SET original_pdf_path = %s, updated_at = %s WHERE commission_number = %s',
                                    (file_path, datetime.now(), commission_number)
                                )
                                rows_affected = cursor.rowcount
                                self.log_info(f'✅ 更新file_id映射成功: {file_id} -> {commission_number} (影响行数: {rows_affected})')
                            else:
                                # 创建新映射（不包含file_id字段，因为表中可能没有）
                                cursor.execute(
                                    '''INSERT INTO commission_ocr_results 
                                       (commission_number, original_pdf_path, created_at, updated_at) 
                                       VALUES (%s, %s, %s, %s)''',
                                    (commission_number, file_path, datetime.now(), datetime.now())
                                )
                                rows_affected = cursor.rowcount
                                self.log_info(f'✅ 创建file_id映射成功: {file_id} -> {commission_number} (影响行数: {rows_affected})')
                    except Exception as mapping_error:
                        # 映射失败不影响主流程，但记录详细错误
                        import traceback
                        self.log_warning(f'⚠️ 创建file_id映射失败（不影响保存）: {mapping_error}')
                        self.log_warning(f'错误详情: {traceback.format_exc()}')
                
                connection.commit()
                cursor.close()
                connection.close()
                
                self.log_info(f'委托数据更新成功: {commission_number}')
                return True, None
                
            except Exception as e:
                connection.rollback()
                cursor.close()
                connection.close()
                raise e
                
        except Exception as e:
            error_msg = f'更新委托数据失败: {str(e)}'
            self.log_error(error_msg)
            import traceback
            self.log_error(f'错误详情: {traceback.format_exc()}')
            return False, error_msg
    
    def delete_commission_by_number(self, commission_number: str) -> Tuple[bool, Optional[str]]:
        """
        根据委托编号删除委托数据（级联删除测试项目和特殊测试）
        
        Args:
            commission_number: 委托编号
            
        Returns:
            (success, error_message)
        """
        try:
            self.log_info(f'开始删除委托数据: {commission_number}')
            
            connection = self._get_db_connection()
            cursor = connection.cursor()
            
            try:
                # 删除测试项目
                cursor.execute('DELETE FROM test_items WHERE commission_number = %s', (commission_number,))
                test_items_deleted = cursor.rowcount
                
                # 删除特殊测试
                cursor.execute('DELETE FROM special_tests WHERE commission_number = %s', (commission_number,))
                special_tests_deleted = cursor.rowcount
                
                # 删除OCR结果
                if CommissionOcrResult:
                    cursor.execute('DELETE FROM commission_ocr_results WHERE commission_number = %s', (commission_number,))
                    ocr_deleted = cursor.rowcount
                else:
                    ocr_deleted = 0
                
                # 删除基本信息
                cursor.execute('DELETE FROM commission_basic WHERE commission_number = %s', (commission_number,))
                basic_deleted = cursor.rowcount
                
                connection.commit()
                cursor.close()
                connection.close()
                
                self.log_info(f'委托数据删除成功: {commission_number}')
                self.log_info(f'  - 基本信息: {basic_deleted} 条')
                self.log_info(f'  - 测试项目: {test_items_deleted} 条')
                self.log_info(f'  - 特殊测试: {special_tests_deleted} 条')
                self.log_info(f'  - OCR结果: {ocr_deleted} 条')
                
                return True, None
                
            except Exception as e:
                connection.rollback()
                cursor.close()
                connection.close()
                raise e
                
        except Exception as e:
            error_msg = f'删除委托数据失败: {str(e)}'
            self.log_error(error_msg)
            return False, error_msg
    
    def delete_commission_by_file_id(self, file_id: int) -> Tuple[bool, Optional[str]]:
        """
        根据文件ID删除委托数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        try:
            self.log_info(f'根据文件ID删除委托数据: {file_id}')
            
            # 获取委托编号
            commission_number = self.get_commission_number_from_file(file_id)
            
            if not commission_number:
                self.log_info(f'文件ID {file_id} 没有关联的委托数据')
                return True, None  # 没有数据也算成功
            
            # 使用commission_number调用删除方法
            return self.delete_commission_by_number(commission_number)
            
        except Exception as e:
            error_msg = f'删除委托数据失败: {str(e)}'
            self.log_error(error_msg)
            return False, error_msg


