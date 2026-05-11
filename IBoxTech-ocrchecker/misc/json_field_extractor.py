#!/usr/bin/env python3
"""
JSON字段提取器
从6.3_field_extraction_results.json中提取字段并映射到数据库字段
"""
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class JsonFieldExtractor:
    """JSON字段提取器"""
    
    # 测试项目表字段映射
    TEST_ITEM_MAPPING = {
        "测试项目": "test_item",
        "试验项目": "test_item",
        "项目名称": "test_item",
        "测试设备": "test_equipment",
        "试验设备": "test_equipment",
        "仪器设备": "test_equipment",
        "测试标准": "test_standard",
        "试验标准": "test_standard",
        "检测标准": "test_standard",
        "测试条件": "test_condition",
        "试验条件": "test_condition",
        "产品标准": "product_standard",
        "单位": "unit",
        "测试结果": "test_result",
        "试验结果": "test_result",
        "检测结果": "test_result",
        "测试人员": "tester",
        "测试员": "tester",
        "检测员": "tester",
        "备注": "remark",
        "说明": "remark",
    }
    
    # 特殊测试表字段映射
    SPECIAL_TEST_MAPPING = {
        "元素": "element_name",
        "元素名称": "element_name",
        "项目": "element_name",
        "标准值": "standard_value",
        "限值": "standard_value",
        "要求": "standard_value",
        "实测值": "measured_value",
        "测试值": "measured_value",
        "检测值": "measured_value",
        "备注": "remark",
        "说明": "remark",
    }
    
    # JSON字段名 → 数据库字段名映射
    FIELD_MAPPING = {
        # 基本信息
        "表格编号": "form_number",
        "委托编号": "commission_number",
        "服务类型": "service_type",
        "是否需要报告": "need_report",
        
        # 委托信息
        "委托部门": "commission_department",
        "委托人": "commissioner",
        "委托日期": "commission_date",
        "委托地址": "commission_address",
        
        # 样品信息
        "样品名称": "sample_name",
        "样品数量": "sample_quantity",
        "样品代码": "sample_code",
        "样品批次": "sample_batch",
        "样品批号": "sample_batch",  # 别名
        "送样时间": "delivery_time",
        "需求时间": "required_time",
        "余样处理": "sample_disposal",
        "样品储存方式": "storage_method",
        
        # 测试信息
        "测试性质": "test_nature",
        "测试说明": "test_description",
        "有无特殊条件": "special_condition_flag",
        "条件详情": "special_condition_detail",
        "特殊条件": "special_condition_detail",  # 别名
        "条件是": "special_condition_detail",  # 可能的OCR结果
        
        # 人员信息
        "测试员": "tester",
        "数据复核人": "data_reviewer",
        "复核日期": "review_date",
        
        # 审核检查项
        "申请单是否填写完整": "form_complete",
        "样品实物信息是否一致": "sample_info_consistent",
        "样品是否完好": "sample_condition_ok",
        "其他检查项": "other_notes",
        "其他": "other_notes",  # 别名
        
        # 签名信息
        "送样人签名": "delivery_person_signature",
        "业务受理人签字": "business_receiver_signature",
    }
    
    def __init__(self):
        pass
    
    def extract_from_json_file(self, json_path: str) -> Dict[str, Any]:
        """
        从JSON文件中提取字段
        
        Args:
            json_path: JSON文件路径
            
        Returns:
            提取结果字典
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return self.extract_from_json_data(data)
    
    def extract_from_json_data(self, json_data: Dict) -> Dict[str, Any]:
        """
        从JSON数据中提取字段
        
        Args:
            json_data: JSON数据字典
            
        Returns:
            提取结果，包含：
            - metadata: 元数据
            - fields: 提取的字段（原始）
            - mapped_fields: 映射后的字段
            - statistics: 统计信息
        """
        result = {
            'metadata': self._extract_metadata(json_data),
            'fields': self._extract_fields(json_data),
            'statistics': self._extract_statistics(json_data),
        }
        
        # 映射字段到数据库字段名
        result['mapped_fields'] = self._map_fields_to_db(result['fields'])
        
        return result
    
    def _extract_metadata(self, json_data: Dict) -> Dict[str, Any]:
        """提取元数据"""
        return {
            'extraction_timestamp': json_data.get('extraction_timestamp'),
            'source_content_blocks': json_data.get('source_content_blocks'),
            'grid_cells_count': json_data.get('grid_cells_count'),
            'matched_cells_count': json_data.get('matched_cells_count'),
            'total_fields_extracted': json_data.get('total_fields_extracted'),
        }
    
    def _extract_statistics(self, json_data: Dict) -> Dict[str, Any]:
        """提取统计信息"""
        stats = json_data.get('extraction_statistics', {})
        return {
            'single_cell_fields': stats.get('single_cell_fields', 0),
            'adjacent_cell_fields': stats.get('adjacent_cell_fields', 0),
            'handwritten_fields': stats.get('handwritten_fields', 0),
            'table_data_count': stats.get('table_data_count', 0),
        }
    
    def _extract_fields(self, json_data: Dict) -> List[Dict[str, Any]]:
        """
        提取所有字段
        
        Returns:
            字段列表，每个字段包含：
            - field_name: 字段名
            - field_value: 字段值
            - field_type: 字段类型
            - extraction_method: 提取方法
            - confidence: 置信度
            - source_block_id: 来源块ID
            - source_block_text: 来源块文本
            - bbox: 边界框
        """
        fields = []
        extracted_fields = json_data.get('extracted_fields', {})
        
        for field_name, field_data in extracted_fields.items():
            field_info = {
                'field_name': field_name,
                'field_value': field_data.get('value', ''),
                'field_type': field_data.get('type', ''),
                'extraction_method': field_data.get('extraction_method', ''),
            }
            
            # 提取source_block信息
            source_block = None
            if 'source_block' in field_data:
                source_block = field_data['source_block']
            elif 'label_block' in field_data:
                source_block = field_data['label_block']
            elif 'content_block' in field_data:
                source_block = field_data['content_block']
            elif 'choice_block' in field_data:
                source_block = field_data['choice_block']
            
            if source_block:
                field_info['confidence'] = source_block.get('confidence')
                field_info['source_block_id'] = source_block.get('id', '')
                field_info['source_block_text'] = source_block.get('text', '')
                field_info['bbox'] = source_block.get('bbox')
            
            fields.append(field_info)
        
        return fields
    
    def _map_fields_to_db(self, fields: List[Dict]) -> Dict[str, Any]:
        """
        将字段映射到数据库字段名
        
        Args:
            fields: 原始字段列表
            
        Returns:
            映射后的字段字典 {db_field_name: value}
        """
        mapped = {}
        
        for field in fields:
            field_name = field['field_name']
            field_value = field['field_value']
            
            # 查找映射
            if field_name in self.FIELD_MAPPING:
                db_field_name = self.FIELD_MAPPING[field_name]
                
                # 数据类型转换
                converted_value = self._convert_field_value(
                    db_field_name, 
                    field_value
                )
                
                mapped[db_field_name] = converted_value
        
        return mapped
    
    def _convert_field_value(self, db_field_name: str, value: str) -> Any:
        """
        转换字段值到正确的数据类型
        
        Args:
            db_field_name: 数据库字段名
            value: 原始值
            
        Returns:
            转换后的值
        """
        if not value:
            return None
        
        # 日期字段
        if db_field_name in ['commission_date', 'delivery_time', 'required_time', 'review_date']:
            return self._parse_date(value)
        
        # 布尔字段
        if db_field_name in ['need_report', 'special_condition_flag', 
                            'form_complete', 'sample_info_consistent', 
                            'sample_condition_ok']:
            return self._parse_boolean(value)
        
        # 字符串字段（清理）
        return self._clean_string(value)
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        解析日期字符串
        
        支持格式:
        - 2023-06-25
        - 2023/06/25
        - 20230625
        - 2023年6月25日
        
        Returns:
            ISO格式日期字符串 YYYY-MM-DD，或None
        """
        if not date_str:
            return None
        
        # 清理字符串
        date_str = date_str.strip()
        
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
                    
                    return date_obj.strftime('%Y-%m-%d')
                except (ValueError, AttributeError):
                    continue
        
        return None
    
    def _parse_boolean(self, value: str) -> Optional[str]:
        """
        解析布尔值
        
        Returns:
            "是" 或 "否"，或None
        """
        if not value:
            return None
        
        value = value.strip().lower()
        
        if value in ['是', 'yes', 'y', '1', 'true', '√', '✓']:
            return '是'
        elif value in ['否', 'no', 'n', '0', 'false', '×', '✗']:
            return '否'
        
        return value  # 返回原值
    
    def _clean_string(self, value: str) -> str:
        """清理字符串"""
        if not value:
            return ''
        
        # 移除多余的空白字符
        value = ' '.join(value.split())
        
        # 移除特殊字符（保留中文、英文、数字、常见标点）
        # value = re.sub(r'[^\w\s\u4e00-\u9fff.,;:!?()（），。；：！？、]', '', value)
        
        return value.strip()
    
    def extract_commission_number(self, fields: List[Dict]) -> Optional[str]:
        """
        提取委托编号
        
        Args:
            fields: 字段列表
            
        Returns:
            委托编号或None
        """
        for field in fields:
            if field['field_name'] == '委托编号':
                return field['field_value']
        return None
    
    def extract_test_items(self, json_data: Dict, commission_number: str) -> List[Dict]:
        """
        提取测试项目表数据
        
        Args:
            json_data: JSON数据
            commission_number: 委托编号
            
        Returns:
            测试项目列表
        """
        test_items = []
        extracted_fields = json_data.get('extracted_fields', {})
        
        # 策略1: 查找table_data类型的字段
        for field_name, field_data in extracted_fields.items():
            if field_data.get('type') == 'table_data':
                # 检查是否是测试项目表
                if any(keyword in field_name for keyword in ['测试项目', '试验项目', '测试表']):
                    rows = field_data.get('rows', [])
                    for idx, row in enumerate(rows, 1):
                        item = {'commission_number': commission_number, 'sort_order': idx}
                        
                        # 映射字段
                        for json_field, db_field in self.TEST_ITEM_MAPPING.items():
                            if json_field in row:
                                item[db_field] = self._clean_string(row[json_field])
                        
                        # 验证并添加
                        if item.get('test_item'):  # 至少要有测试项目
                            test_items.append(item)
        
        # 策略2: 查找带序号的字段（如"测试项目1", "测试项目2"）
        if not test_items:
            grouped = self._group_numbered_fields(extracted_fields, '测试项目')
            for idx, group in enumerate(grouped, 1):
                item = {'commission_number': commission_number, 'sort_order': idx}
                
                for field_name, value in group.items():
                    if field_name in self.TEST_ITEM_MAPPING:
                        item[self.TEST_ITEM_MAPPING[field_name]] = self._clean_string(value)
                
                if item.get('test_item'):
                    test_items.append(item)
        
        return test_items
    
    def extract_special_tests(self, json_data: Dict, commission_number: str) -> List[Dict]:
        """
        提取特殊测试表数据（RoHs/HF等）
        
        Args:
            json_data: JSON数据
            commission_number: 委托编号
            
        Returns:
            特殊测试列表
        """
        special_tests = []
        extracted_fields = json_data.get('extracted_fields', {})
        
        # 策略1: 查找table_data类型的字段
        for field_name, field_data in extracted_fields.items():
            if field_data.get('type') == 'table_data':
                # 检查是否是特殊测试表
                test_type = None
                if any(keyword in field_name for keyword in ['RoHs', 'rohs', 'ROHS']):
                    test_type = 'RoHs'
                elif any(keyword in field_name for keyword in ['HF', 'hf']):
                    test_type = 'HF'
                elif any(keyword in field_name for keyword in ['重金属', '金属元素']):
                    test_type = '其他金属'
                
                if test_type:
                    rows = field_data.get('rows', [])
                    for idx, row in enumerate(rows, 1):
                        test = {
                            'commission_number': commission_number,
                            'test_type': test_type,
                            'sort_order': idx
                        }
                        
                        # 映射字段
                        for json_field, db_field in self.SPECIAL_TEST_MAPPING.items():
                            if json_field in row:
                                test[db_field] = self._clean_string(row[json_field])
                        
                        # 验证并添加
                        if test.get('element_name'):  # 至少要有元素名称
                            special_tests.append(test)
        
        # 策略2: 查找带序号的字段
        if not special_tests:
            # 尝试查找RoHs相关字段
            for test_type_keyword in ['RoHs', 'HF', '重金属']:
                grouped = self._group_numbered_fields(extracted_fields, test_type_keyword)
                for idx, group in enumerate(grouped, 1):
                    test = {
                        'commission_number': commission_number,
                        'test_type': self._detect_test_type(test_type_keyword, group),
                        'sort_order': idx
                    }
                    
                    for field_name, value in group.items():
                        if field_name in self.SPECIAL_TEST_MAPPING:
                            test[self.SPECIAL_TEST_MAPPING[field_name]] = self._clean_string(value)
                    
                    if test.get('element_name'):
                        special_tests.append(test)
        
        return special_tests
    
    def _group_numbered_fields(self, fields: Dict, keyword: str) -> List[Dict]:
        """
        将带序号的字段分组
        
        例如: {"测试项目1": "xxx", "测试设备1": "yyy", "测试项目2": "zzz"}
        分组为: [{"测试项目": "xxx", "测试设备": "yyy"}, {"测试项目": "zzz"}]
        
        Args:
            fields: 字段字典
            keyword: 关键词（如"测试项目"）
            
        Returns:
            分组后的字段列表
        """
        import re
        groups = {}
        
        for field_name, field_data in fields.items():
            # 提取字段名和序号
            match = re.search(rf'(.+?)(\d+)$', field_name)
            if match:
                base_name = match.group(1)
                number = int(match.group(2))
                
                # 检查是否包含关键词
                if keyword in base_name or any(k in base_name for k in self.TEST_ITEM_MAPPING.keys()):
                    if number not in groups:
                        groups[number] = {}
                    
                    # 移除序号，得到纯字段名
                    clean_name = base_name.strip()
                    value = field_data.get('value', '') if isinstance(field_data, dict) else str(field_data)
                    groups[number][clean_name] = value
        
        # 按序号排序并返回
        return [groups[num] for num in sorted(groups.keys())]
    
    def _detect_test_type(self, keyword: str, group: Dict) -> str:
        """
        检测测试类型
        
        Args:
            keyword: 关键词
            group: 字段组
            
        Returns:
            测试类型
        """
        if 'RoHs' in keyword or 'rohs' in keyword.lower():
            return 'RoHs'
        elif 'HF' in keyword or 'hf' in keyword.lower():
            return 'HF'
        else:
            return '其他金属'
    
    def prepare_document_record(self, 
                               pdf_filename: str,
                               minio_object_name: str,
                               file_size: int,
                               file_md5: str,
                               page_count: int,
                               extraction_timestamp: str,
                               commission_number: Optional[str]) -> Dict:
        """
        准备commission_documents表记录
        
        Returns:
            记录字典
        """
        return {
            'pdf_filename': pdf_filename,
            'minio_object_name': minio_object_name,
            'minio_bucket': 'commissions',  # 默认桶名
            'file_size': file_size,
            'file_md5': file_md5,
            'page_count': page_count,
            'extraction_timestamp': extraction_timestamp,
            'commission_number': commission_number,
        }
    
    def prepare_field_records(self, 
                             document_id: int,
                             page_number: int,
                             fields: List[Dict]) -> List[Dict]:
        """
        准备commission_extracted_fields表记录
        
        Args:
            document_id: 文档ID
            page_number: 页码
            fields: 字段列表
            
        Returns:
            记录列表
        """
        records = []
        
        for field in fields:
            record = {
                'document_id': document_id,
                'page_number': page_number,
                'field_name': field['field_name'],
                'field_value': field['field_value'],
                'field_type': field.get('field_type'),
                'extraction_method': field.get('extraction_method'),
                'confidence': field.get('confidence'),
                'source_block_id': field.get('source_block_id'),
                'source_block_text': field.get('source_block_text'),
                'bbox_json': json.dumps(field.get('bbox')) if field.get('bbox') else None,
            }
            records.append(record)
        
        return records
    
    def prepare_statistics_record(self,
                                 document_id: int,
                                 page_number: int,
                                 metadata: Dict,
                                 statistics: Dict) -> Dict:
        """
        准备commission_statistics表记录
        
        Args:
            document_id: 文档ID
            page_number: 页码
            metadata: 元数据
            statistics: 统计信息
            
        Returns:
            记录字典
        """
        return {
            'document_id': document_id,
            'page_number': page_number,
            'source_content_blocks': metadata.get('source_content_blocks'),
            'grid_cells_count': metadata.get('grid_cells_count'),
            'matched_cells_count': metadata.get('matched_cells_count'),
            'total_fields_extracted': metadata.get('total_fields_extracted'),
            'single_cell_fields': statistics.get('single_cell_fields'),
            'adjacent_cell_fields': statistics.get('adjacent_cell_fields'),
            'handwritten_fields': statistics.get('handwritten_fields'),
            'table_data_count': statistics.get('table_data_count'),
        }


def test_extractor():
    """测试提取器"""
    # 测试文件路径
    json_file = "resource/IBoxTech_json/multi_page_results/测试中心品质部原材料委托单（OA) 2023年6月_第44页2/page_001_results/steps/step06/6.3_field_extraction_results.json"
    
    if not Path(json_file).exists():
        print(f"❌ 测试文件不存在: {json_file}")
        return
    
    print("=== JSON字段提取测试 ===\n")
    
    # 创建提取器
    extractor = JsonFieldExtractor()
    
    # 提取字段
    result = extractor.extract_from_json_file(json_file)
    
    # 打印元数据
    print("1. 元数据:")
    for key, value in result['metadata'].items():
        print(f"   {key}: {value}")
    
    # 打印统计信息
    print("\n2. 统计信息:")
    for key, value in result['statistics'].items():
        print(f"   {key}: {value}")
    
    # 打印提取的字段
    print(f"\n3. 提取的字段 ({len(result['fields'])}个):")
    for field in result['fields']:
        print(f"   - {field['field_name']}: {field['field_value']}")
        print(f"     类型: {field['field_type']}, 置信度: {field.get('confidence', 'N/A')}")
    
    # 打印映射后的字段
    print(f"\n4. 映射到数据库字段 ({len(result['mapped_fields'])}个):")
    for db_field, value in result['mapped_fields'].items():
        print(f"   - {db_field}: {value}")
    
    # 提取委托编号
    commission_number = extractor.extract_commission_number(result['fields'])
    print(f"\n5. 委托编号: {commission_number}")
    
    # 准备数据库记录示例
    print("\n6. 数据库记录示例:")
    
    # document记录
    doc_record = extractor.prepare_document_record(
        pdf_filename="测试文件.pdf",
        minio_object_name="commission_pdfs/测试文件.pdf",
        file_size=1024000,
        file_md5="abc123",
        page_count=1,
        extraction_timestamp=result['metadata']['extraction_timestamp'],
        commission_number=commission_number
    )
    print(f"   commission_documents: {json.dumps(doc_record, ensure_ascii=False, indent=2)}")
    
    # field记录
    field_records = extractor.prepare_field_records(
        document_id=1,
        page_number=1,
        fields=result['fields'][:2]  # 只显示前2个
    )
    print(f"\n   commission_extracted_fields (前2条):")
    for record in field_records:
        print(f"     {json.dumps(record, ensure_ascii=False, indent=2)}")
    
    # statistics记录
    stats_record = extractor.prepare_statistics_record(
        document_id=1,
        page_number=1,
        metadata=result['metadata'],
        statistics=result['statistics']
    )
    print(f"\n   commission_statistics:")
    print(f"     {json.dumps(stats_record, ensure_ascii=False, indent=2)}")
    
    # 测试表格提取
    print("\n7. 表格数据提取测试:")
    
    # 读取原始JSON数据
    with open(json_file, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # 提取测试项目表
    test_items = extractor.extract_test_items(json_data, commission_number or 'TEST001')
    print(f"\n   测试项目表 ({len(test_items)}条):")
    if test_items:
        for item in test_items:
            print(f"     {json.dumps(item, ensure_ascii=False, indent=2)}")
    else:
        print("     ⚠️  当前JSON中未找到测试项目表数据")
        print("     提示: 测试项目表可能在第2页或其他文件中")
    
    # 提取特殊测试表
    special_tests = extractor.extract_special_tests(json_data, commission_number or 'TEST001')
    print(f"\n   特殊测试表 ({len(special_tests)}条):")
    if special_tests:
        for test in special_tests:
            print(f"     {json.dumps(test, ensure_ascii=False, indent=2)}")
    else:
        print("     ⚠️  当前JSON中未找到特殊测试表数据")
        print("     提示: 特殊测试表（RoHs/HF）可能在单独的页面中")
    
    print("\n8. 完整数据映射流程:")
    print("   ✅ PDF文件信息 → commission_documents表")
    print("   ✅ JSON提取字段 → commission_extracted_fields表")
    print("   ✅ 统计信息 → commission_statistics表")
    print("   ✅ 基本字段 → commission_basic表 (通过字段映射)")
    print("   ✅ 测试项目 → test_items表")
    print("   ✅ 特殊测试 → special_tests表")
    
    print("\n✅ 测试完成")


if __name__ == '__main__':
    test_extractor()

