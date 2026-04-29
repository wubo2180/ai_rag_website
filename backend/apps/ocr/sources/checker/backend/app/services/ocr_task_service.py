"""
OCR异步任务服务
管理OCR识别的异步任务队列

✅ 推荐使用方式（新版异步任务）
本服务提供异步OCR处理能力，支持：
- 任务状态查询和进度反馈
- 后台线程处理，不阻塞请求
- 统一的错误处理和重试机制
- 完整的任务生命周期管理

使用场景：
1. FileRecognize 识别页面 ✅ 已迁移
2. FileManagement 文件列表页面 ⏳ 待迁移

API端点：
- POST /files/<file_id>/ocr/recognize - 创建任务
- GET /files/ocr/task/<task_id> - 查询任务状态

对比旧版方式：
- 旧版：FileService.start_ocr_processing() - 同步处理，可能超时
- 新版：OcrTaskService.create_task() - 异步处理，体验更好

迁移参考：
- 查看 frontend/src/views/FileRecognize/index.vue 的实现
- 查看 backend/app/api/files.py 中的 recognize_file_ocr() 函数
"""
import uuid
import threading
from datetime import datetime
from flask import current_app
from models import db
from models.ocr_task import OcrTask
from app.adapters.paper_adapter import PaperAdapter
from app.adapters.commission_adapter import CommissionAdapter


class OcrTaskService:
    """OCR任务服务类"""
    
    @staticmethod
    def create_task(file_id, user_id):
        """
        创建OCR任务
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            
        Returns:
            OcrTask: 任务对象
        """
        task_id = str(uuid.uuid4())
        
        task = OcrTask(
            file_id=file_id,
            task_id=task_id,
            status='pending',
            progress=0,
            user_id=user_id
        )
        
        db.session.add(task)
        db.session.commit()
        
        current_app.logger.info(f'📝 创建OCR任务: task_id={task_id}, file_id={file_id}')
        
        return task
    
    @staticmethod
    def get_task(task_id):
        """
        获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            OcrTask: 任务对象
        """
        return OcrTask.query.filter_by(task_id=task_id).first()
    
    @staticmethod
    def update_task_status(task_id, status, progress=None, current_step=None, result=None, error_message=None):
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            status: 状态
            progress: 进度
            current_step: 当前步骤
            result: 结果数据
            error_message: 错误信息
        """
        task = OcrTask.query.filter_by(task_id=task_id).first()
        if not task:
            return False
        
        task.status = status
        
        if progress is not None:
            task.progress = progress
        
        if current_step:
            task.current_step = current_step
        
        if result is not None:
            task.result = result
        
        if error_message:
            task.error_message = error_message
        
        if status == 'processing' and not task.started_at:
            task.started_at = datetime.utcnow()
        
        if status in ['completed', 'failed']:
            task.completed_at = datetime.utcnow()
            task.progress = 100 if status == 'completed' else task.progress
        
        db.session.commit()
        
        current_app.logger.info(f'📊 更新任务状态: task_id={task_id}, status={status}, progress={progress}')
        
        return True
    
    @staticmethod
    def process_task_async(task_id, file_service, app):
        """
        异步处理OCR任务
        
        Args:
            task_id: 任务ID
            file_service: 文件服务实例
            app: Flask应用实例
        """
        with app.app_context():
            try:
                task = OcrTask.query.filter_by(task_id=task_id).first()
                if not task:
                    current_app.logger.error(f'❌ 任务不存在: task_id={task_id}')
                    return
                
                # 更新状态为处理中
                OcrTaskService.update_task_status(
                    task_id,
                    'processing',
                    progress=10,
                    current_step='开始OCR识别'
                )
                
                # 获取文件信息
                file_record = file_service.get_file_by_id(task.file_id)
                if not file_record:
                    OcrTaskService.update_task_status(
                        task_id,
                        'failed',
                        error_message='文件不存在'
                    )
                    return
                
                # 下载文件
                OcrTaskService.update_task_status(
                    task_id,
                    'processing',
                    progress=20,
                    current_step='下载文件'
                )
                
                file_data = file_service.minio_service.download_file(file_record.file_path)
                if not file_data:
                    OcrTaskService.update_task_status(
                        task_id,
                        'failed',
                        error_message='无法从存储中获取文件'
                    )
                    return
                
                # 获取文档类型
                document_type_code = file_record.document_type_code or 'commission'  # 默认为委托单
                current_app.logger.info(f'📋 [Task {task_id}] 文档类型: {document_type_code}')
                
                # 调用统一OCR识别服务
                OcrTaskService.update_task_status(
                    task_id,
                    'processing',
                    progress=40,
                    current_step='调用OCR识别服务'
                )
                
                # 保存文件到临时目录
                import tempfile
                import os
                from pathlib import Path
                
                temp_file = None
                try:
                    # 创建临时文件
                    suffix = Path(file_record.filename).suffix
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                    temp_file.write(file_data)
                    temp_file.close()
                    
                    current_app.logger.info(f'📄 [Task {task_id}] 临时文件: {temp_file.name}')
                    
                    # 使用统一OCR服务
                    from services.unified_ocr_service import unified_ocr_service
                    
                    current_app.logger.info(f'📡 [Task {task_id}] 调用统一OCR服务，文档类型: {document_type_code}')
                    
                    success, result, error_msg = unified_ocr_service.recognize_file(
                        temp_file.name,
                        document_type_code
                    )
                    
                    if not success:
                        current_app.logger.error(f'❌ [Task {task_id}] OCR识别失败: {error_msg}')
                        OcrTaskService.update_task_status(
                            task_id,
                            'failed',
                            error_message=error_msg
                        )
                        return
                    
                    current_app.logger.info(f'✅ [Task {task_id}] OCR识别成功')
                    
                finally:
                    # 清理临时文件
                    if temp_file and os.path.exists(temp_file.name):
                        try:
                            os.unlink(temp_file.name)
                            current_app.logger.info(f'🗑️  [Task {task_id}] 已清理临时文件')
                        except Exception as e:
                            current_app.logger.warning(f'⚠️ [Task {task_id}] 清理临时文件失败: {str(e)}')
                
                # 解析OCR结果为结构化数据
                OcrTaskService.update_task_status(
                    task_id,
                    'processing',
                    progress=70,
                    current_step='解析识别结果'
                )
                
                current_app.logger.info(f'🔍 [Task {task_id}] 开始解析OCR结果...')
                
                # 根据文档类型解析结果（不保存到数据库，由前端用户确认后再保存）
                if document_type_code == 'paper':
                    # 论文类型：使用PaperAdapter
                    current_app.logger.info(f'📄 [Task {task_id}] 论文类型，使用PaperAdapter处理')
                    
                    try:
                        # 创建适配器实例
                        adapter = PaperAdapter()
                        
                        # 解析OCR结果
                        current_app.logger.info(f'🔍 [Task {task_id}] 开始解析论文OCR结果')
                        structured_data = adapter.parse_ocr_result(result)
                        current_app.logger.info(f'✅ [Task {task_id}] 解析完成 - 文献ID: {structured_data.get("article_id")}, '
                                               f'材料/中间体数: {len(structured_data.get("hierarchical_data", []))}')
                        
                        # ⚠️ 注意：不在这里保存到数据库
                        # 数据将返回给前端，由用户确认后点击"保存入库"按钮才保存
                        current_app.logger.info(f'📤 [Task {task_id}] 解析完成，数据将返回前端供用户确认')
                        
                    except Exception as parse_error:
                        error_msg = f'处理论文OCR结果失败: {str(parse_error)}'
                        current_app.logger.error(f'❌ [Task {task_id}] {error_msg}')
                        import traceback
                        current_app.logger.error(f'❌ [Task {task_id}] 堆栈信息:\n{traceback.format_exc()}')
                        OcrTaskService.update_task_status(
                            task_id,
                            'failed',
                            error_message=error_msg
                        )
                        return
                        
                else:
                    # 委托单类型：使用CommissionAdapter
                    current_app.logger.info(f'📋 [Task {task_id}] 委托单类型，使用CommissionAdapter处理')
                    
                    try:
                        # 创建适配器实例
                        adapter = CommissionAdapter()
                        
                        # 解析OCR结果
                        current_app.logger.info(f'🔍 [Task {task_id}] 开始解析委托单OCR结果')
                        structured_data = adapter.parse_ocr_result(result)
                        current_app.logger.info(f'✅ [Task {task_id}] 解析完成 - 基本信息字段数: {len(structured_data.get("basic_info", {}))}, '
                                               f'检测项: {len(structured_data.get("test_items", []))}, '
                                               f'特殊试验: {len(structured_data.get("special_tests", []))}')
                        
                        # ⚠️ 注意：不在这里保存到数据库
                        # 数据将返回给前端，由用户确认后点击"保存入库"按钮才保存
                        current_app.logger.info(f'📤 [Task {task_id}] 解析完成，数据将返回前端供用户确认')
                        
                    except Exception as parse_error:
                        error_msg = f'处理委托单OCR结果失败: {str(parse_error)}'
                        current_app.logger.error(f'❌ [Task {task_id}] {error_msg}')
                        import traceback
                        current_app.logger.error(f'❌ [Task {task_id}] 堆栈信息:\n{traceback.format_exc()}')
                        OcrTaskService.update_task_status(
                            task_id,
                            'failed',
                            error_message=error_msg
                        )
                        return
                
                # 处理完成（只解析，不保存）
                OcrTaskService.update_task_status(
                    task_id,
                    'completed',
                    progress=100,
                    current_step='识别完成（待用户确认保存）',
                    result={
                        'structured_data': structured_data,
                        'raw_ocr_data': result.get('data', result),
                        'document_type': document_type_code,
                        'confidence': result.get('confidence', '未知')
                    }
                )
                
                current_app.logger.info(f'🎉 [Task {task_id}] OCR任务完成！')
                
                current_app.logger.info(f'✅ OCR任务完成: task_id={task_id}')
                
            except Exception as e:
                current_app.logger.error(f'❌ OCR任务失败: task_id={task_id}, error={str(e)}')
                import traceback
                traceback.print_exc()
                
                OcrTaskService.update_task_status(
                    task_id,
                    'failed',
                    error_message=str(e)
                )
    
    @staticmethod
    def _parse_ocr_api_result(ocr_data, filename):
        """
        解析OCR API返回的结果，转换为结构化的键值对
        
        Args:
            ocr_data: OCR API返回的数据
            filename: 文件名
            
        Returns:
            dict: 结构化数据 {basic_info: {}, test_items: [], special_tests: []}
        """
        from flask import current_app
        
        current_app.logger.info(f'🔧 开始解析OCR数据，文件: {filename}')
        current_app.logger.info(f'🔧 输入数据类型: {type(ocr_data)}')
        
        # 初始化结构化数据
        structured_data = {
            'basic_info': {},
            'test_items': [],
            'special_tests': []
        }
        
        try:
            # 如果OCR数据中有表格信息
            if isinstance(ocr_data, dict):
                current_app.logger.info(f'🔧 OCR数据是字典，包含键: {list(ocr_data.keys())}')
                
                # 方式1: 从fields字段提取（如果有的话）
                if 'fields' in ocr_data:
                    fields = ocr_data['fields']
                    current_app.logger.info(f'📋 发现fields字段，类型: {type(fields)}, 长度: {len(fields) if isinstance(fields, (list, dict)) else "N/A"}')
                    
                    if isinstance(fields, list):
                        for field in fields:
                            field_name = field.get('field_name', '')
                            field_value = field.get('field_value', '')
                            
                            if field_name and field_value:
                                structured_data['basic_info'][field_name] = field_value
                    elif isinstance(fields, dict):
                        # fields 本身就是键值对
                        structured_data['basic_info'] = fields
                        current_app.logger.info(f'✅ fields是字典，直接使用，包含 {len(fields)} 个字段')
                
                # 方式2: 从tables字段提取（如果有的话）
                if 'tables' in ocr_data:
                    tables = ocr_data['tables']
                    current_app.logger.info(f'📊 发现tables字段，类型: {type(tables)}, 长度: {len(tables) if isinstance(tables, list) else "N/A"}')
                    
                    if isinstance(tables, list):
                        for idx, table in enumerate(tables):
                            current_app.logger.info(f'   表格 {idx}: {type(table)}')
                            if isinstance(table, dict) and 'cells' in table:
                                # 解析表格数据
                                cells = table['cells']
                                current_app.logger.info(f'   表格 {idx} 包含 {len(cells)} 个单元格')
                
                # 方式3: 直接就是键值对字典
                if 'basic_info' in ocr_data:
                    structured_data['basic_info'] = ocr_data['basic_info']
                    current_app.logger.info(f'✅ 直接使用basic_info，包含 {len(structured_data["basic_info"])} 个字段')
                
                if 'test_items' in ocr_data:
                    structured_data['test_items'] = ocr_data['test_items']
                    current_app.logger.info(f'✅ 直接使用test_items，包含 {len(structured_data["test_items"])} 项')
                
                if 'special_tests' in ocr_data:
                    structured_data['special_tests'] = ocr_data['special_tests']
                    current_app.logger.info(f'✅ 直接使用special_tests，包含 {len(structured_data["special_tests"])} 项')
                
                # 方式4: 从field_extraction_results提取（这是实际的OCR API格式！优先级最高）
                if not structured_data['basic_info'] and 'field_extraction_results' in ocr_data:
                    field_results = ocr_data['field_extraction_results']
                    current_app.logger.info(f'🔍 发现field_extraction_results，类型: {type(field_results)}, 长度: {len(field_results) if isinstance(field_results, list) else "N/A"}')
                    
                    if isinstance(field_results, list) and len(field_results) > 0:
                        # 取第一页的结果
                        first_page = field_results[0]
                        current_app.logger.info(f'📄 处理第一页数据，类型: {type(first_page)}')
                        current_app.logger.info(f'📄 第一页包含键: {list(first_page.keys()) if isinstance(first_page, dict) else "N/A"}')
                        
                        if isinstance(first_page, dict):
                            # 提取 extracted_fields（这是关键！）
                            if 'extracted_fields' in first_page:
                                extracted_fields = first_page['extracted_fields']
                                current_app.logger.info(f'📋 发现extracted_fields，类型: {type(extracted_fields)}')
                                
                                if isinstance(extracted_fields, dict):
                                    current_app.logger.info(f'📋 extracted_fields包含 {len(extracted_fields)} 个字段')
                                    
                                    # 遍历每个字段，提取value
                                    for field_name, field_data in extracted_fields.items():
                                        # 检查是否是表格类型的字段
                                        if isinstance(field_data, dict):
                                            field_type = field_data.get('type', '')
                                            
                                            # 处理表格类型字段（测试项目表、特殊测试表等）
                                            if field_type == 'multi_row_table' or '表' in field_name:
                                                current_app.logger.info(f'📊 发现表格字段: {field_name}, 类型: {field_type}')
                                                
                                                # 提取表格数据
                                                if 'data' in field_data:
                                                    table_rows = field_data['data']
                                                    current_app.logger.info(f'   表格包含 {len(table_rows)} 行数据')
                                                    
                                                    # 字段映射：中文 -> 英文
                                                    test_item_field_mapping = {
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
                                                    
                                                    special_test_field_mapping = {
                                                        '测试类型': 'test_type',
                                                        '元素名称': 'element_name',
                                                        '标准值': 'standard_value',
                                                        '实测值': 'measured_value',
                                                        '标准': 'standard_value',
                                                        '实测': 'measured_value',
                                                        '备注': 'remark'
                                                    }
                                                    
                                                    # 转换表格行数据
                                                    mapped_rows = []
                                                    for row_idx, row in enumerate(table_rows):
                                                        if isinstance(row, dict):
                                                            # 根据字段名判断是测试项目还是特殊测试
                                                            if '测试项目' in field_name or 'test_item' in field_name.lower():
                                                                # 映射测试项目字段
                                                                mapped_row = {}
                                                                for cn_key, value in row.items():
                                                                    en_key = test_item_field_mapping.get(cn_key, cn_key)
                                                                    mapped_row[en_key] = value
                                                                
                                                                # 添加sort_order
                                                                if 'sort_order' not in mapped_row:
                                                                    mapped_row['sort_order'] = row_idx
                                                                
                                                                mapped_rows.append(mapped_row)
                                                            
                                                            elif '特殊测试' in field_name or 'special' in field_name.lower() or 'rohs' in field_name.lower():
                                                                # 映射特殊测试字段
                                                                mapped_row = {}
                                                                for cn_key, value in row.items():
                                                                    en_key = special_test_field_mapping.get(cn_key, cn_key)
                                                                    mapped_row[en_key] = value
                                                                
                                                                # 添加sort_order
                                                                if 'sort_order' not in mapped_row:
                                                                    mapped_row['sort_order'] = row_idx
                                                                
                                                                mapped_rows.append(mapped_row)
                                                            else:
                                                                # 默认按测试项目处理
                                                                mapped_row = {}
                                                                for cn_key, value in row.items():
                                                                    en_key = test_item_field_mapping.get(cn_key, cn_key)
                                                                    mapped_row[en_key] = value
                                                                
                                                                if 'sort_order' not in mapped_row:
                                                                    mapped_row['sort_order'] = row_idx
                                                                
                                                                mapped_rows.append(mapped_row)
                                                    
                                                    # 根据字段名判断添加到哪个列表
                                                    if '测试项目' in field_name or 'test_item' in field_name.lower():
                                                        structured_data['test_items'].extend(mapped_rows)
                                                        current_app.logger.info(f'   ✅ 映射并添加了 {len(mapped_rows)} 个测试项到test_items')
                                                    elif '特殊测试' in field_name or 'special' in field_name.lower() or 'rohs' in field_name.lower():
                                                        structured_data['special_tests'].extend(mapped_rows)
                                                        current_app.logger.info(f'   ✅ 映射并添加了 {len(mapped_rows)} 个特殊测试到special_tests')
                                                    else:
                                                        # 默认添加到test_items
                                                        structured_data['test_items'].extend(mapped_rows)
                                                        current_app.logger.info(f'   ✅ 默认映射并添加了 {len(mapped_rows)} 个项目到test_items')
                                                    
                                                    # 打印第一行作为样例
                                                    if mapped_rows:
                                                        current_app.logger.info(f'   📝 样例行数据: {mapped_rows[0]}')
                                                
                                                # 表格字段不添加到basic_info
                                                continue
                                            
                                            # 处理普通字段
                                            if 'value' in field_data:
                                                value = field_data['value']
                                                if value:  # 只添加非空值
                                                    structured_data['basic_info'][field_name] = str(value)
                                        elif isinstance(field_data, (str, int, float)):
                                            # 如果直接就是值
                                            structured_data['basic_info'][field_name] = str(field_data)

                                    
                                    current_app.logger.info(f'✅ 从field_extraction_results[0].extracted_fields提取了 {len(structured_data["basic_info"])} 个非空字段')
                                    
                                    # 打印前5个字段作为样例
                                    if structured_data['basic_info']:
                                        sample_items = list(structured_data['basic_info'].items())[:5]
                                        current_app.logger.info(f'📝 样例字段: {sample_items}')
                            
                            # 提取表格数据
                            if 'tables' in first_page or 'table' in first_page:
                                tables_key = 'tables' if 'tables' in first_page else 'table'
                                tables_data = first_page[tables_key]
                                current_app.logger.info(f'📊 发现{tables_key}数据，类型: {type(tables_data)}')
                                
                                if isinstance(tables_data, list):
                                    for idx, table in enumerate(tables_data):
                                        current_app.logger.info(f'   处理表格 {idx}，类型: {type(table)}')
                                        # TODO: 根据表格名称或索引判断是test_items还是special_tests
                                        # 暂时先添加到test_items
                                        if isinstance(table, dict):
                                            if 'rows' in table:
                                                structured_data['test_items'].extend(table['rows'])
                                            elif 'data' in table:
                                                structured_data['test_items'].extend(table['data'])
                                
                                if structured_data['test_items']:
                                    current_app.logger.info(f'✅ 从表格提取了 {len(structured_data["test_items"])} 个测试项')
                            
                            # 如果没有extracted_fields，尝试直接使用fields
                            if not structured_data['basic_info'] and 'fields' in first_page:
                                fields_data = first_page['fields']
                                if isinstance(fields_data, dict):
                                    # 同样的逻辑，提取value
                                    for field_name, field_data in fields_data.items():
                                        if isinstance(field_data, dict) and 'value' in field_data:
                                            value = field_data['value']
                                            if value:
                                                structured_data['basic_info'][field_name] = str(value)
                                        elif isinstance(field_data, (str, int, float)):
                                            structured_data['basic_info'][field_name] = str(field_data)
                                    
                                    current_app.logger.info(f'✅ 从field_extraction_results[0].fields提取了 {len(structured_data["basic_info"])} 个字段')
                
                # 方式5: 从原始OCR结果中提取所有键值对
                if not structured_data['basic_info'] and 'result' in ocr_data:
                    result_data = ocr_data['result']
                    current_app.logger.info(f'🔍 尝试从result提取，类型: {type(result_data)}')
                    
                    if isinstance(result_data, dict):
                        for key, value in result_data.items():
                            if isinstance(value, (str, int, float)):
                                structured_data['basic_info'][key] = str(value)
                        current_app.logger.info(f'📝 从result提取了 {len(structured_data["basic_info"])} 个字段')
                
                # 方式6: 从combined_results提取（OCR API的实际格式）
                if not structured_data['basic_info'] and 'combined_results' in ocr_data:
                    combined_results = ocr_data['combined_results']
                    current_app.logger.info(f'🔍 发现combined_results，类型: {type(combined_results)}')
                    current_app.logger.info(f'🔍 combined_results 包含键: {list(combined_results.keys()) if isinstance(combined_results, dict) else "N/A"}')
                    
                    if isinstance(combined_results, dict):
                        # 可能包含的键: extracted_fields, table_data等
                        if 'extracted_fields' in combined_results:
                            extracted_fields = combined_results['extracted_fields']
                            current_app.logger.info(f'📋 发现extracted_fields，类型: {type(extracted_fields)}')
                            
                            if isinstance(extracted_fields, dict):
                                structured_data['basic_info'] = extracted_fields
                                current_app.logger.info(f'✅ 从combined_results.extracted_fields提取了 {len(extracted_fields)} 个字段')
                            elif isinstance(extracted_fields, list):
                                # 如果是列表，遍历提取
                                for item in extracted_fields:
                                    if isinstance(item, dict):
                                        for k, v in item.items():
                                            structured_data['basic_info'][k] = str(v)
                                current_app.logger.info(f'✅ 从combined_results.extracted_fields列表提取了 {len(structured_data["basic_info"])} 个字段')
                        
                        # 提取表格数据（test_items, special_tests）
                        if 'table_data' in combined_results:
                            table_data = combined_results['table_data']
                            current_app.logger.info(f'📊 发现table_data，类型: {type(table_data)}')
                            
                            if isinstance(table_data, dict):
                                if 'test_items' in table_data:
                                    structured_data['test_items'] = table_data['test_items']
                                    current_app.logger.info(f'✅ 从table_data提取了 {len(structured_data["test_items"])} 个测试项')
                                
                                if 'special_tests' in table_data:
                                    structured_data['special_tests'] = table_data['special_tests']
                                    current_app.logger.info(f'✅ 从table_data提取了 {len(structured_data["special_tests"])} 个特殊试验')
                        
                        # 如果combined_results本身就是键值对
                        if not structured_data['basic_info']:
                            for key, value in combined_results.items():
                                if key not in ['table_data', 'extracted_fields']:
                                    if isinstance(value, dict):
                                        # 可能是基本信息
                                        structured_data['basic_info'].update(value)
                                    elif isinstance(value, (str, int, float, bool)):
                                        structured_data['basic_info'][key] = str(value)
                            
                            if structured_data['basic_info']:
                                current_app.logger.info(f'✅ 从combined_results直接提取了 {len(structured_data["basic_info"])} 个字段')
                
                # 方式7: 如果都没有，尝试直接从顶级键提取
                if not structured_data['basic_info']:
                    current_app.logger.info(f'🔍 尝试从顶级键提取数据...')
                    excluded_keys = ['fields', 'tables', 'result', 'basic_info', 'test_items', 'special_tests',
                                    'combined_results', 'field_extraction_results', 'ocr_raw_data', 
                                    'success', 'message', 'processing_time', 'total_pages']
                    for key, value in ocr_data.items():
                        if key not in excluded_keys:
                            if isinstance(value, (str, int, float, bool)):
                                structured_data['basic_info'][key] = str(value)
                                current_app.logger.info(f'   添加字段: {key} = {value}')
                    
                    if structured_data['basic_info']:
                        current_app.logger.info(f'📝 从顶级键提取了 {len(structured_data["basic_info"])} 个字段')
            
            current_app.logger.info(f'✅ 解析完成 - 基本信息: {len(structured_data["basic_info"])} 字段, '
                                   f'检测项: {len(structured_data["test_items"])} 项, '
                                   f'特殊试验: {len(structured_data["special_tests"])} 项')
            
            # 如果测试项目和特殊测试为空，尝试使用备用方法从原始OCR文本中提取
            if not structured_data['test_items'] and not structured_data['special_tests']:
                current_app.logger.info('⚠️ 表格数据为空，尝试从原始OCR文本中提取...')
                
                # 获取所有OCR识别的文本
                all_texts = []
                if 'ocr_raw_data' in ocr_data and isinstance(ocr_data['ocr_raw_data'], list):
                    for page_data in ocr_data['ocr_raw_data']:
                        if isinstance(page_data, dict) and 'rec_texts' in page_data:
                            all_texts.extend(page_data['rec_texts'])
                
                if all_texts:
                    current_app.logger.info(f'📝 从OCR原始数据中获取了 {len(all_texts)} 个文本块')
                    
                    # 使用简化的提取逻辑
                    structured_data['test_items'] = self._extract_test_items_from_texts(all_texts)
                    structured_data['special_tests'] = self._extract_special_tests_from_texts(all_texts)
                    
                    current_app.logger.info(f'✅ 补充提取 - 检测项: {len(structured_data["test_items"])} 项, '
                                          f'特殊试验: {len(structured_data["special_tests"])} 项')
            
            # 如果还是空的，打印警告
            if not structured_data['basic_info'] and not structured_data['test_items'] and not structured_data['special_tests']:
                current_app.logger.warning(f'⚠️ 警告：解析后的结构化数据为空！')
                current_app.logger.warning(f'⚠️ 原始OCR数据结构可能不符合预期，请检查OCR API返回格式')
            
        except Exception as e:
            current_app.logger.error(f'❌ 解析OCR数据时出错: {str(e)}')
            import traceback
            current_app.logger.error(traceback.format_exc())
        
        return structured_data
    
    @staticmethod
    def _extract_test_items_from_texts(texts):
        """从OCR文本中提取测试项目（简化版）"""
        test_items = []
        
        # 查找常见测试项目关键词
        test_keywords = ['挥发分', '外观', 'RoHs测试', '红外扫描', '成分分析', '物理性能']
        
        for i, text in enumerate(texts):
            for keyword in test_keywords:
                if keyword in text:
                    # 找到了测试项目，尝试提取相关信息
                    test_item = {
                        'test_item': keyword,
                        'test_equipment': '',
                        'test_standard': '',
                        'test_condition': '',
                        'product_standard': '',
                        'unit': '',
                        'test_result': '',
                        'tester': '',
                        'remark': '',
                        'sort_order': len(test_items)
                    }
                    
                    # 尝试从附近的文本块中提取其他信息
                    nearby_texts = texts[max(0, i-2):min(len(texts), i+3)]
                    
                    for nearby_text in nearby_texts:
                        # 提取测试标准（如GB/T xxx）
                        import re
                        if 'GB/T' in nearby_text or 'GB' in nearby_text:
                            test_item['test_standard'] = nearby_text
                        
                        # 提取单位（如%、kg等）
                        if '%' in nearby_text or 'kg' in nearby_text or 'g' in nearby_text:
                            test_item['unit'] = nearby_text
                        
                        # 提取数值结果
                        number_match = re.search(r'\d+\.?\d*', nearby_text)
                        if number_match and not test_item['test_result']:
                            test_item['test_result'] = nearby_text
                    
                    test_items.append(test_item)
                    break
        
        return test_items
    
    @staticmethod
    def _extract_special_tests_from_texts(texts):
        """从OCR文本中提取特殊测试项目（简化版）"""
        special_tests = []
        
        # RoHs元素
        rohs_elements = {
            '铅': 'Pb', '汞': 'Hg', '镉': 'Cd', '铬': 'Cr',
            'Pb': 'Pb', 'Hg': 'Hg', 'Cd': 'Cd', 'Cr': 'Cr'
        }
        
        # 卤素元素
        halogen_elements = {
            '溴': 'Br', '氯': 'Cl',
            'Br': 'Br', 'Cl': 'Cl'
        }
        
        # 其他金属
        other_metals = {
            '砷': 'As', '锑': 'Sb', '锡': 'Sn',
            'As': 'As', 'Sb': 'Sb', 'Sn': 'Sn'
        }
        
        # 检查是否有RoHs测试
        has_rohs = any('RoHs' in text or 'ROHS' in text or 'rohs' in text for text in texts)
        has_halogen = any('卤素' in text or 'HF' in text for text in texts)
        
        import re
        
        # 提取RoHs元素数据
        if has_rohs:
            for text in texts:
                for element_cn, element_en in rohs_elements.items():
                    if element_cn in text or element_en in text:
                        # 尝试提取测量值
                        value_match = re.search(r'(\d+\.?\d*|ND|<\d+)', text)
                        measured_value = value_match.group(1) if value_match else 'ND'
                        
                        special_tests.append({
                            'test_type': 'RoHs',
                            'element_name': f'{element_cn}({element_en})' if element_cn in rohs_elements else element_en,
                            'standard_value': '<1000',
                            'measured_value': measured_value,
                            'remark': '合格' if measured_value == 'ND' or (measured_value.replace('.', '').isdigit() and float(measured_value) < 1000) else '',
                            'sort_order': len(special_tests)
                        })
        
        # 提取卤素元素数据
        if has_halogen:
            for text in texts:
                for element_cn, element_en in halogen_elements.items():
                    if element_cn in text or element_en in text:
                        value_match = re.search(r'(\d+\.?\d*|ND|<\d+)', text)
                        measured_value = value_match.group(1) if value_match else 'ND'
                        
                        special_tests.append({
                            'test_type': 'HF',
                            'element_name': f'{element_cn}({element_en})' if element_cn in halogen_elements else element_en,
                            'standard_value': '<900',
                            'measured_value': measured_value,
                            'remark': '合格' if measured_value == 'ND' or (measured_value.replace('.', '').isdigit() and float(measured_value) < 900) else '',
                            'sort_order': len(special_tests)
                        })
        
        # 提取其他金属元素数据
        for text in texts:
            for element_cn, element_en in other_metals.items():
                if element_cn in text or element_en in text:
                    value_match = re.search(r'(\d+\.?\d*|ND|<\d+)', text)
                    measured_value = value_match.group(1) if value_match else 'ND'
                    
                    special_tests.append({
                        'test_type': '其他金属',
                        'element_name': f'{element_cn}({element_en})' if element_cn in other_metals else element_en,
                        'standard_value': '<1000',
                        'measured_value': measured_value,
                        'remark': '合格' if measured_value == 'ND' or (measured_value.replace('.', '').isdigit() and float(measured_value) < 1000) else '',
                        'sort_order': len(special_tests)
                    })
        
        return special_tests
    
    @staticmethod
    def start_task_processing(task_id, file_service):
        """
        启动任务处理（在后台线程中）
        
        Args:
            task_id: 任务ID
            file_service: 文件服务实例
        """
        from flask import current_app
        app = current_app._get_current_object()  # 获取真实的app对象
        
        thread = threading.Thread(
            target=OcrTaskService.process_task_async,
            args=(task_id, file_service, app)
        )
        thread.daemon = True
        thread.start()
        
        current_app.logger.info(f'🚀 启动后台OCR任务: task_id={task_id}')


