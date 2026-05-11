"""
论文OCR适配器
处理论文文档的OCR识别结果、数据持久化和业务逻辑
"""
from typing import Dict, Any, Optional, Tuple, List
from models import db, get_models
from .base_ocr_adapter import BaseOCRAdapter, ParseError, SaveError, ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from utils.id_generator import IDGenerator, get_existing_article_ids_from_db

# 获取模型
models = get_models()
PaperArticle = models['PaperArticle']
PaperMaterialIntermediate = models['PaperMaterialIntermediate']
PaperProperty = models['PaperProperty']
File = models['File']


class PaperAdapter(BaseOCRAdapter):
    """
    论文OCR适配器
    
    负责：
    1. 解析论文OCR识别结果 (parse_ocr_result)
    2. 验证论文数据 (validate_data)
    3. 保存论文数据到数据库 (save_to_database)
    4. 从数据库获取论文数据 (get_from_database)
    5. 更新论文数据 (update_in_database)
    6. 删除论文数据 (delete_from_database)
    """
    
    def parse_ocr_result(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析论文OCR结果（新格式）
        
        Args:
            raw_data: OCR服务返回的原始数据
            格式: {
                "success": true,
                "message": "...",
                "data": {
                    "task_id": "...",
                    "workflow_run_id": "...",
                    "data": {              ← 注意：第二层data
                        "id": "...",
                        "workflow_id": "...",
                        "status": "succeeded",
                        "outputs": {
                            "text": "..."  ← JSON字符串或字典
                        }
                    }
                },
                "processing_time": 25.7
            }
            
            text 字段内容（可能包含markdown标记）:
            ```json
            {
                "文献": {
                    "文献编号（Article ID）": "A1",
                    "文献名称（Article Name）": "...",
                    "四级数据连接（4-level Data Linkage）": [...]
                }
            }
            ```
            
        Returns:
            {
                'article_id': 'A1',
                'article_name': '...',
                'performance_trend': '...',
                'hierarchical_data': [...]  # 四级数据连接
            }
        """
        self.log_info("开始解析论文OCR结果（新格式）")
        
        try:
            # 打印原始数据结构用于调试
            import json
            self.log_info("=" * 80)
            self.log_info("📋 原始OCR返回数据（完整）:")
            self.log_info("=" * 80)
            try:
                formatted_data = json.dumps(raw_data, ensure_ascii=False, indent=2)
                # 分段打印，避免日志过长
                # if len(formatted_data) > 2000:
                #     self.log_info(formatted_data[:1000])
                #     self.log_info("... (中间部分省略) ...")
                #     self.log_info(formatted_data[-1000:])
                # else:
                #     self.log_info(formatted_data)
                self.log_info(formatted_data)
            except Exception as e:
                self.log_warning(f"无法格式化原始数据: {str(e)}")
                self.log_info(str(raw_data)[:1000])
            self.log_info("=" * 80)
            
            structured_data = {
                'article_id': '',
                'article_name': '',
                'performance_trend': '',
                'hierarchical_data': []
            }
            
            # 从新格式中提取data字段（注意：有两层data）
            if 'data' in raw_data:
                first_data = raw_data['data']
                self.log_info(f"发现第一层data字段，类型: {type(first_data)}")
                self.log_info(f"第一层data的键: {list(first_data.keys()) if isinstance(first_data, dict) else '不是字典'}")
                
                # 检查是否有第二层data（新格式：data -> data -> outputs）
                if isinstance(first_data, dict) and 'data' in first_data:
                    data_content = first_data['data']
                    self.log_info(f"✅ 发现第二层data字段，类型: {type(data_content)}")
                    self.log_info(f"第二层data的键: {list(data_content.keys()) if isinstance(data_content, dict) else '不是字典'}")
                else:
                    # 如果没有第二层，就使用第一层（向后兼容）
                    data_content = first_data
                    self.log_info(f"⚠️ 未发现第二层data，使用第一层data")
                
                # 从outputs中提取论文数据
                if isinstance(data_content, dict) and 'outputs' in data_content:
                    outputs = data_content['outputs']
                    self.log_info(f"发现outputs，键: {list(outputs.keys()) if isinstance(outputs, dict) else 'outputs不是字典'}")
                    
                    # 提取文本输出并尝试解析JSON
                    if isinstance(outputs, dict) and 'text' in outputs:
                        text_output = outputs['text']
                        self.log_info(f"发现文本输出，类型: {type(text_output)}, 长度: {len(str(text_output))}")
                        
                        # 尝试解析JSON格式的文本输出
                        try:
                            # 如果text_output已经是字典，直接使用
                            if isinstance(text_output, dict):
                                parsed_output = text_output
                                self.log_info("text输出已经是字典格式")
                            elif isinstance(text_output, str):
                                # 清理可能的markdown代码块标记
                                cleaned_text = self._clean_markdown_code_block(text_output)
                                if cleaned_text != text_output:
                                    self.log_info("✂️ 检测到并清理了markdown代码块标记")
                                    self.log_info(f"清理前长度: {len(text_output)}, 清理后长度: {len(cleaned_text)}")
                                
                                parsed_output = json.loads(cleaned_text)
                                self.log_info("✅ 成功解析JSON字符串")
                            else:
                                parsed_output = None
                                self.log_warning(f"text输出类型未知: {type(text_output)}")
                            
                            if isinstance(parsed_output, dict):
                                self.log_info(f"解析后的字典键: {list(parsed_output.keys())}")
                                self._extract_from_dict(parsed_output, structured_data)
                                self.log_info(f"从text字段提取 - 文献ID: {structured_data['article_id']}, 文献名称: {structured_data['article_name'][:30] if structured_data['article_name'] else '空'}")
                        except json.JSONDecodeError as je:
                            self.log_warning(f"文本输出不是JSON格式: {str(je)}")
                            self.log_warning(f"JSON错误位置: 行{je.lineno}, 列{je.colno}")
                            self.log_warning(f"文本前200字符: {str(text_output)[:200]}")
                        except Exception as e:
                            self.log_error(f"解析text字段时出错: {str(e)}")
                            import traceback
                            self.log_error(traceback.format_exc())
                    
                    # 只有在text解析失败时，才直接从outputs提取字段
                    if not structured_data['article_id'] and isinstance(outputs, dict):
                        self.log_info("text字段未提取到数据，尝试从outputs直接提取")
                        self._extract_from_dict(outputs, structured_data)
                        self.log_info(f"从outputs直接提取 - 文献ID: {structured_data['article_id']}")
                
                # 如果outputs中没有数据，尝试从data顶级提取
                if not structured_data['article_id'] and isinstance(data_content, dict):
                    self.log_info("尝试从data顶级提取数据")
                    self._extract_from_dict(data_content, structured_data)
                    self.log_info(f"从data提取 - 文献ID: {structured_data['article_id']}")
            
            # 如果还是没有数据，尝试从顶级提取
            if not structured_data['article_id']:
                self.log_info("尝试从顶级提取数据")
                self._extract_from_dict(raw_data, structured_data)
                self.log_info(f"从顶级提取 - 文献ID: {structured_data['article_id']}")
            
            # ⭐ 生成本地编号（在返回给前端之前）
            self.log_info("=" * 80)
            self.log_info("🔄 开始替换为本地生成的编号")
            self.log_info("=" * 80)
            
            # 1. 生成唯一的文献编号
            existing_ids = get_existing_article_ids_from_db()
            old_article_id = structured_data['article_id']
            new_article_id = IDGenerator.generate_unique_article_id(existing_ids)
            structured_data['article_id'] = new_article_id
            self.log_info(f"📄 文献编号: {old_article_id} → {new_article_id}")
            
            # 2. 初始化计数器
            material_counter = 0
            intermediate_counter = 0
            property_counter = 0
            
            # 3. 替换材料/中间体/性能编号
            for idx, item in enumerate(structured_data.get('hierarchical_data', [])):
                self.log_info(f"\n🔄 处理第 {idx + 1} 个材料/中间体组")
                
                # 检查并生成材料编号
                old_material_id = item.get('材料编号') or item.get('material_id', '')
                if old_material_id or item.get('原材料名称') or item.get('material_name'):
                    material_counter += 1
                    new_material_id = IDGenerator.generate_material_id(new_article_id, material_counter)
                    if '材料编号' in item:
                        item['材料编号'] = new_material_id
                    if 'material_id' in item:
                        item['material_id'] = new_material_id
                    self.log_info(f"  📦 材料编号: {old_material_id} → {new_material_id}")
                
                # 检查并生成中间体编号
                old_intermediate_id = item.get('中间体编号') or item.get('intermediate_id', '')
                if old_intermediate_id or item.get('中间体名称') or item.get('intermediate_name'):
                    intermediate_counter += 1
                    new_intermediate_id = IDGenerator.generate_intermediate_id(new_article_id, intermediate_counter)
                    if '中间体编号' in item:
                        item['中间体编号'] = new_intermediate_id
                    if 'intermediate_id' in item:
                        item['intermediate_id'] = new_intermediate_id
                    self.log_info(f"  🧪 中间体编号: {old_intermediate_id} → {new_intermediate_id}")
                
                # 替换性能编号
                for prop_key in ['性能', 'properties', 'Properties']:
                    if prop_key in item and isinstance(item[prop_key], list):
                        for prop in item[prop_key]:
                            old_property_id = prop.get('性能编号') or prop.get('property_id', '')
                            property_counter += 1
                            new_property_id = IDGenerator.generate_property_id(new_article_id, property_counter)
                            if '性能编号' in prop:
                                prop['性能编号'] = new_property_id
                            if 'property_id' in prop:
                                prop['property_id'] = new_property_id
                            self.log_info(f"    ⚡ 性能编号: {old_property_id} → {new_property_id}")
            
            self.log_info("=" * 80)
            self.log_info(f"✅ 编号替换完成")
            self.log_info(f"  文献编号: {new_article_id}")
            self.log_info(f"  材料数: {material_counter}")
            self.log_info(f"  中间体数: {intermediate_counter}")
            self.log_info(f"  性能数: {property_counter}")
            self.log_info("=" * 80)
            
            self.log_info(f"✅ 解析完成 - 文献ID: {structured_data['article_id']}, "
                         f"文献名称: {structured_data['article_name'][:30] if structured_data['article_name'] else '空'}, "
                         f"材料/中间体数: {len(structured_data['hierarchical_data'])}")
            
            return structured_data
            
        except Exception as e:
            error_msg = f"解析论文OCR结果失败: {str(e)}"
            self.log_error(error_msg)
            import traceback
            self.log_error(traceback.format_exc())
            raise ParseError(error_msg) from e
    
    def _clean_markdown_code_block(self, text: str) -> str:
        """
        清理markdown代码块标记
        
        例如:
        ```json
        {"文献": {"文献编号（Article ID）": "A2", ...}}
        ```
        
        转换为:
        {"文献": {"文献编号（Article ID）": "A2", ...}}
        """
        import re
        
        text = text.strip()
        
        # 去除开头的 ```json 或 ``` 标记（可能带换行）
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        
        # 去除结尾的 ``` 标记（可能带换行）
        text = re.sub(r'\n?```\s*$', '', text)
        
        return text.strip()
    
    def _extract_from_dict(self, data_dict: Dict, structured_data: Dict):
        """从字典中提取论文数据（支持多种格式）"""
        self.log_info(f"🔍 _extract_from_dict 输入字典的键: {list(data_dict.keys()) if isinstance(data_dict, dict) else '不是字典'}")
        
        # 检查是否有顶层的"文献"包装对象（新格式）
        if '文献' in data_dict and isinstance(data_dict['文献'], dict):
            self.log_info("📦 发现'文献'包装对象，提取内部数据")
            paper_data = data_dict['文献']
        else:
            paper_data = data_dict
        
        # 提取文献编号（支持多种字段名）
        article_id_keys = ['文献编号（Article ID）', '文献编号', 'article_id']
        for key in article_id_keys:
            if key in paper_data:
                old_value = structured_data['article_id']
                structured_data['article_id'] = paper_data[key] or ''
                self.log_info(f"📌 提取文献编号 (键:'{key}'): '{old_value}' -> '{structured_data['article_id']}'")
                break
        
        # 提取文献名称（支持多种字段名）
        article_name_keys = ['文献名称（Article Name）', '文献名称', 'article_name']
        for key in article_name_keys:
            if key in paper_data:
                old_value = structured_data['article_name']
                structured_data['article_name'] = paper_data[key] or ''
                self.log_info(f"📌 提取文献名称 (键:'{key}'): '{old_value[:20] if old_value else ''}...' -> '{structured_data['article_name'][:20] if structured_data['article_name'] else ''}...'")
                break
        
        # 提取性能趋势（支持多种字段名）
        trend_keys = ['性能趋势', 'performance_trend']
        for key in trend_keys:
            if key in paper_data:
                structured_data['performance_trend'] = paper_data[key] or ''
                self.log_info(f"📌 提取性能趋势 (键:'{key}'): {len(structured_data['performance_trend'])} 字符")
                break
        
        # 提取四级数据连接（支持多种字段名）
        hierarchical_keys = ['四级数据连接（4-level Data Linkage）', '四级数据连接', 'hierarchical_data']
        hierarchical_key = None
        for key in hierarchical_keys:
            if key in paper_data:
                hierarchical_key = key
                self.log_info(f"📌 找到层次数据键: '{key}'")
                break
        
        if hierarchical_key:
            hierarchical_list = paper_data[hierarchical_key]
            if isinstance(hierarchical_list, list):
                # 转换新格式的嵌套结构为扁平化结构
                normalized_data = self._normalize_hierarchical_data(hierarchical_list)
                structured_data['hierarchical_data'] = normalized_data
                self.log_info(f"✅ 提取到 {len(normalized_data)} 个材料/中间体数据")
            else:
                self.log_warning(f"⚠️ {hierarchical_key} 不是列表类型: {type(hierarchical_list)}")
        else:
            self.log_info(f"ℹ️ 未找到层次数据键，当前字典键: {list(paper_data.keys())[:10]}")
    
    def _normalize_hierarchical_data(self, hierarchical_list: List[Dict]) -> List[Dict]:
        """
        将嵌套的材料/中间体数据结构转换为扁平化结构
        
        新格式:
        [{
            "原材料（Materials）": {...},
            "中间体（Intermediates）": {...},
            "中间体组成（Intermediate Compositions）": "...",
            "性能（Properties）": [...]
        }]
        
        转换为:
        [{
            "材料编号": "...",
            "原材料名称": "...",
            "CAS号": "...",
            "中间体编号": "...",
            "中间体名称": "...",
            "中间体组成": "...",
            "性能": [...]
        }]
        """
        normalized = []
        
        for idx, item in enumerate(hierarchical_list):
            self.log_info(f"🔄 处理第 {idx + 1} 个材料/中间体数据")
            
            normalized_item = {}
            
            # 检查是否是新格式（嵌套结构）
            if '原材料（Materials）' in item or '中间体（Intermediates）' in item:
                self.log_info("  📦 检测到新格式（嵌套结构）")
                
                # 提取材料信息
                materials = item.get('原材料（Materials）', {})
                if isinstance(materials, dict):
                    normalized_item['材料编号'] = materials.get('材料编号（Material ID）', '')
                    normalized_item['原材料名称'] = materials.get('原材料名称（Material Name）', '')
                    normalized_item['CAS号'] = materials.get('CAS号（CAS Number）', '')
                    self.log_info(f"    ✓ 材料编号: {normalized_item['材料编号']}")
                elif isinstance(materials, list) and len(materials) > 0:
                    # 材料是数组，取第一个
                    first_material = materials[0]
                    normalized_item['材料编号'] = first_material.get('材料编号（Material ID）', '')
                    normalized_item['原材料名称'] = first_material.get('原材料名称（Material Name）', '')
                    normalized_item['CAS号'] = first_material.get('CAS号（CAS Number）', '')
                    self.log_info(f"    ✓ 材料编号（从数组）: {normalized_item['材料编号']}")
                
                # 提取中间体信息
                intermediates = item.get('中间体（Intermediates）', {})
                if isinstance(intermediates, dict):
                    normalized_item['中间体编号'] = intermediates.get('中间体编号（Intermediate ID）', '')
                    normalized_item['中间体名称'] = intermediates.get('中间体名称（Intermediate Name）', '')
                    self.log_info(f"    ✓ 中间体编号: {normalized_item['中间体编号']}")
                elif isinstance(intermediates, list) and len(intermediates) > 0:
                    # 中间体是数组，取第一个
                    first_intermediate = intermediates[0]
                    normalized_item['中间体编号'] = first_intermediate.get('中间体编号（Intermediate ID）', '')
                    normalized_item['中间体名称'] = first_intermediate.get('中间体名称（Intermediate Name）', '')
                    self.log_info(f"    ✓ 中间体编号（从数组）: {normalized_item['中间体编号']}")
                
                # 提取中间体组成
                normalized_item['中间体组成'] = item.get('中间体组成（Intermediate Compositions）', '')
                
                # 提取性能数据
                properties = item.get('性能（Properties）', [])
                if isinstance(properties, list):
                    # 将性能数据也转换为统一格式
                    normalized_properties = []
                    for prop in properties:
                        normalized_prop = {
                            '性能编号': prop.get('性能编号（Property ID）', ''),
                            '性能名称': prop.get('性能名称（Property Name）', ''),
                            '性能值': prop.get('性能值（Property Value）', '')
                        }
                        normalized_properties.append(normalized_prop)
                    normalized_item['性能'] = normalized_properties
                    self.log_info(f"    ✓ 性能数据: {len(normalized_properties)} 条")
            else:
                # 旧格式（扁平结构），直接使用
                self.log_info("  📋 检测到旧格式（扁平结构）")
                normalized_item = item
            
            normalized.append(normalized_item)
        
        return normalized
    
    def save_to_database(self, structured_data: Dict[str, Any], file_id: int) -> Tuple[bool, Optional[str]]:
        """
        保存论文数据到数据库
        
        注意：编号已经在 parse_ocr_result() 中生成，这里直接使用
        
        Args:
            structured_data: 结构化数据（已包含本地生成的编号）
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        self.log_info(f"保存论文数据到数据库，文件ID: {file_id}")
        
        try:
            # 验证数据
            is_valid, errors = self.validate_data(structured_data)
            if not is_valid:
                error_msg = f"数据验证失败: {', '.join(errors)}"
                self.log_error(error_msg)
                return False, error_msg
            
            # 检查是否已存在
            existing = PaperArticle.query.filter_by(file_id=file_id).first()
            if existing:
                self.log_info(f"文件ID {file_id} 的论文数据已存在，删除旧数据")
                db.session.delete(existing)
                db.session.flush()
            
            # 使用已生成的文献编号
            article_id_str = structured_data['article_id']
            self.log_info(f"使用已生成的文献编号: {article_id_str}")
            
            # 创建论文记录
            article = PaperArticle(
                file_id=file_id,
                article_id=article_id_str,
                article_name=structured_data['article_name'],
                performance_trend=structured_data.get('performance_trend', '')
            )
            db.session.add(article)
            db.session.flush()  # 获取article.id（数据库自增ID）
            
            self.log_info(f"论文记录已创建 - 数据库ID: {article.id}, 文献编号: {article_id_str}")
            
            # 保存材料/中间体和性能数据
            for material_data in structured_data.get('hierarchical_data', []):
                # 使用已生成的材料编号和中间体编号
                material_id = material_data.get('材料编号') or material_data.get('material_id', '')
                intermediate_id = material_data.get('中间体编号') or material_data.get('intermediate_id', '')
                
                # 创建材料/中间体记录
                material = PaperMaterialIntermediate(
                    article_id=article_id_str,
                    material_id=material_id,
                    material_name=material_data.get('原材料名称') or material_data.get('material_name', ''),
                    cas_number=material_data.get('CAS号') or material_data.get('cas_number', ''),
                    intermediate_id=intermediate_id,
                    intermediate_name=material_data.get('中间体名称') or material_data.get('intermediate_name', ''),
                    intermediate_composition=material_data.get('中间体组成') or material_data.get('intermediate_composition', ''),
                    sort_order=material_data.get('sort_order', 0)
                )
                db.session.add(material)
                db.session.flush()  # 获取material.id
                
                # 保存性能数据
                properties_key = None
                for key in ['性能', 'properties', 'Properties']:
                    if key in material_data:
                        properties_key = key
                        break
                
                if properties_key:
                    for prop_data in material_data[properties_key]:
                        # 使用已生成的性能编号
                        property_id = prop_data.get('性能编号') or prop_data.get('property_id', '')
                        
                        property_record = PaperProperty(
                            article_id=article_id_str,
                            material_intermediate_id=material.id,
                            property_id=property_id,
                            property_name=prop_data.get('性能名称') or prop_data.get('property_name', ''),
                            property_value=prop_data.get('性能值') or prop_data.get('property_value', ''),
                            property_unit=prop_data.get('单位') or prop_data.get('property_unit', ''),
                            sort_order=prop_data.get('sort_order', 0)
                        )
                        db.session.add(property_record)
            
            # 更新文件的 OCR 状态
            file_record = File.query.get(file_id)
            if file_record:
                file_record.update_ocr_status('completed')
                self.log_info(f"已更新文件 {file_id} 的 OCR 状态为 completed")
            else:
                self.log_warning(f"未找到文件 {file_id}，无法更新 OCR 状态")
            
            # 提交事务
            db.session.commit()
            
            self.log_info(f"✅ 论文数据保存成功，文献编号: {article_id_str}")
            return True, None
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"保存论文数据失败: {str(e)}"
            self.log_error(error_msg)
            import traceback
            self.log_error(traceback.format_exc())
            return False, error_msg
    
    def get_from_database(self, file_id: int) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """
        从数据库获取论文数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, structured_data, error_message)
        """
        self.log_info(f"从数据库获取论文数据，文件ID: {file_id}")
        
        try:
            article = PaperArticle.query.filter_by(file_id=file_id).first()
            
            if not article:
                self.log_info("未找到论文数据，返回空结构")
                # 返回空的论文数据结构
                empty_data = {
                    'article_id': '',
                    'article_name': '',
                    'performance_trend': '',
                    'material_intermediates': []
                }
                return True, empty_data, None
            
            # 获取材料/中间体数据（包含性能）
            material_intermediates_list = []
            for mi in article.material_intermediates.order_by('sort_order').all():
                mi_data = {
                    'material_id': mi.material_id,
                    'material_name': mi.material_name or '',
                    'cas_number': mi.cas_number or '',
                    'intermediate_id': mi.intermediate_id or '',
                    'intermediate_name': mi.intermediate_name or '',
                    'intermediate_composition': mi.intermediate_composition or '',
                    'properties': [
                        {
                            'property_id': prop.property_id,
                            'property_name': prop.property_name,
                            'property_value': prop.property_value or ''
                        }
                        for prop in mi.properties.order_by('sort_order').all()
                    ]
                }
                material_intermediates_list.append(mi_data)
            
            # 转换为前端期望的格式（英文键名）
            structured_data = {
                'article_id': article.article_id,
                'article_name': article.article_name,
                'performance_trend': article.performance_trend or '',
                'material_intermediates': material_intermediates_list
            }
            
            self.log_info(f"成功获取论文数据，文献ID: {article.article_id}, 材料/中间体数: {len(material_intermediates_list)}")
            return True, structured_data, None
            
        except Exception as e:
            error_msg = f"获取论文数据失败: {str(e)}"
            self.log_error(error_msg)
            import traceback
            self.log_error(f"错误详情: {traceback.format_exc()}")
            return False, None, error_msg
    
    def validate_data(self, structured_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证论文数据
        
        Args:
            structured_data: 待验证的数据
            
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # 验证必填字段
        if not structured_data.get('article_id'):
            errors.append("缺少文献编号")
        
        if not structured_data.get('article_name'):
            errors.append("缺少文献名称")
        
        # 验证层次数据格式
        hierarchical_data = structured_data.get('hierarchical_data', [])
        if not isinstance(hierarchical_data, list):
            errors.append("四级数据连接格式错误，必须是列表")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            self.log_info("数据验证通过")
        else:
            self.log_warning(f"数据验证失败: {errors}")
        
        return is_valid, errors
    
    def delete_from_database(self, file_id: int) -> Tuple[bool, Optional[str]]:
        """
        删除论文数据（基础方法：通过file_id删除）
        
        Args:
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        self.log_info(f"删除论文数据，文件ID: {file_id}")
        
        # 调用更完善的删除方法
        return self.delete_paper_by_file_id(file_id)
    
    def update_in_database(self, structured_data: Dict[str, Any], file_id: int) -> Tuple[bool, Optional[str]]:
        """
        更新论文数据（基础方法：通过file_id更新）
        
        Args:
            structured_data: 更新后的数据
            file_id: 文件ID
            
        Returns:
            (success, error_message)
        """
        self.log_info(f"更新论文数据，文件ID: {file_id}")
        
        try:
            # 查找现有文章
            article = PaperArticle.query.filter_by(file_id=file_id).first()
            
            if not article:
                return False, f"未找到文件ID {file_id} 对应的论文数据"
            
            # 使用article_id调用更新方法
            return self.update_paper_by_article_id(
                article.article_id,
                structured_data
            )
        
        except Exception as e:
            error_msg = f"更新论文数据失败: {str(e)}"
            self.log_error(error_msg)
            return False, error_msg
    
    # ==================== 业务逻辑方法（从 PaperService 迁移） ====================
    
    def get_paper_by_article_id(self, article_id: str, include_details: bool = True) -> Optional[Dict[str, Any]]:
        """
        根据文献编号获取论文数据
        
        Args:
            article_id: 文献编号
            include_details: 是否包含详细数据
        
        Returns:
            论文数据字典 或 None
        """
        try:
            article = PaperArticle.query.filter_by(article_id=article_id).first()
            
            if not article:
                self.log_info(f"文献编号 {article_id} 不存在")
                return None
            
            return article.to_dict(include_details=include_details)
        
        except Exception as e:
            self.log_error(f"获取论文数据失败: {str(e)}")
            return None
    
    def get_paper_hierarchical_data(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        获取论文的层次化数据（JSON格式）
        
        Args:
            article_id: 文献编号
        
        Returns:
            层次化的JSON数据 或 None
        """
        try:
            article = PaperArticle.query.filter_by(article_id=article_id).first()
            
            if not article:
                self.log_info(f"文献编号 {article_id} 不存在")
                return None
            
            return article.to_hierarchical_dict()
        
        except Exception as e:
            self.log_error(f"获取论文层次化数据失败: {str(e)}")
            return None
    
    def get_paper_hierarchical_data_by_file_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        """
        根据文件ID获取论文的层次化数据（JSON格式）
        
        Args:
            file_id: 文件ID
        
        Returns:
            层次化的JSON数据 或 None
        """
        try:
            article = PaperArticle.query.filter_by(file_id=file_id).first()
            
            if not article:
                self.log_info(f"文件ID {file_id} 没有关联的论文数据")
                return None
            
            return article.to_hierarchical_dict()
        
        except Exception as e:
            self.log_error(f"获取论文层次化数据失败: {str(e)}")
            return None
    
    def update_paper_by_article_id(
        self,
        article_id: str,
        paper_data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        根据文献编号更新论文数据
        
        Args:
            article_id: 文献编号
            paper_data: 更新的数据，格式：
                {
                    'article_name': str (可选),
                    'performance_trend': str (可选),
                    'status': str (可选),
                    'hierarchical_data': list (可选)
                }
            user_id: 操作用户ID（可选）
        
        Returns:
            (success, error_message)
        """
        try:
            self.log_info(f"更新论文数据，文献编号: {article_id}")
            
            article = PaperArticle.query.filter_by(article_id=article_id).first()
            
            if not article:
                return False, f'文献编号 {article_id} 不存在'
            
            # 更新基本信息
            if 'article_name' in paper_data:
                article.article_name = paper_data['article_name']
            if 'performance_trend' in paper_data:
                article.performance_trend = paper_data['performance_trend']
            if 'status' in paper_data:
                article.status = paper_data['status']
            
            # 如果有层次化数据更新，先删除旧数据
            if 'hierarchical_data' in paper_data:
                # 删除旧的材料/中间体（级联删除性能数据）
                PaperMaterialIntermediate.query.filter_by(
                    article_id=article_id
                ).delete()
                
                # 重新插入数据
                hierarchical_data = paper_data['hierarchical_data']
                for idx, item in enumerate(hierarchical_data):
                    mi = PaperMaterialIntermediate(
                        article_id=article.article_id,
                        entity_type='material',
                        material_id=item.get('material_id'),
                        material_name=item.get('material_name'),
                        cas_number=item.get('cas_number'),
                        intermediate_id=item.get('intermediate_id'),
                        intermediate_name=item.get('intermediate_name'),
                        intermediate_composition=item.get('intermediate_composition'),
                        sort_order=idx + 1
                    )
                    db.session.add(mi)
                    db.session.flush()
                    
                    # 插入性能数据
                    properties = item.get('properties', [])
                    for p_idx, prop in enumerate(properties):
                        property_record = PaperProperty(
                            material_intermediate_id=mi.id,
                            article_id=article.article_id,
                            property_id=prop.get('property_id'),
                            property_name=prop.get('property_name'),
                            property_value=prop.get('property_value', ''),
                            sort_order=p_idx + 1
                        )
                        db.session.add(property_record)
            
            db.session.commit()
            
            self.log_info(f"论文数据更新成功: {article_id}")
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            error_msg = f'更新论文数据失败：{str(e)}'
            self.log_error(error_msg)
            return False, error_msg
    
    def delete_paper_by_article_id(self, article_id: str) -> Tuple[bool, Optional[str]]:
        """
        根据文献编号删除论文数据（级联删除材料和性能数据）
        
        级联删除顺序：
        1. PaperProperty (性能数据) [手动删除]
        2. PaperMaterialIntermediate (材料/中间体) [手动删除]
        3. PaperArticle (文献记录)
        
        Args:
            article_id: 文献编号
        
        Returns:
            (success, error_message)
        """
        try:
            self.log_info(f"开始删除论文数据: {article_id}")
            
            # 1. 查找文献记录
            article = PaperArticle.query.filter_by(article_id=article_id).first()
            
            if not article:
                self.log_warning(f"文献不存在: {article_id}")
                return False, f'文献编号 {article_id} 不存在'
            
            # 2. 统计关联数据（用于日志）
            material_count = PaperMaterialIntermediate.query.filter_by(article_id=article_id).count()
            property_count = PaperProperty.query.filter_by(article_id=article_id).count()
            
            self.log_info(f"文献 {article_id} 关联数据统计:")
            self.log_info(f"  - 材料/中间体: {material_count} 条")
            self.log_info(f"  - 性能数据: {property_count} 条")
            
            # 3. 手动删除性能数据（确保删除，即使数据库级联失败）
            if property_count > 0:
                self.log_info(f"手动删除 {property_count} 条性能数据...")
                PaperProperty.query.filter_by(article_id=article_id).delete()
                db.session.flush()  # 立即执行
                self.log_info(f"✅ 性能数据删除完成")
            
            # 4. 手动删除材料/中间体数据
            if material_count > 0:
                self.log_info(f"手动删除 {material_count} 条材料/中间体数据...")
                PaperMaterialIntermediate.query.filter_by(article_id=article_id).delete()
                db.session.flush()  # 立即执行
                self.log_info(f"✅ 材料/中间体数据删除完成")
            
            # 5. 删除文献记录
            self.log_info(f"删除文献记录...")
            db.session.delete(article)
            
            # 6. 提交事务
            db.session.commit()
            
            self.log_info(f"✅ 论文数据删除成功: {article_id}")
            self.log_info(f"  - 共删除 {material_count} 条材料/中间体数据")
            self.log_info(f"  - 共删除 {property_count} 条性能数据")
            
            return True, None
        
        except IntegrityError as ie:
            db.session.rollback()
            error_msg = f'删除失败，存在外键约束: {str(ie)}'
            self.log_error(error_msg)
            return False, error_msg
        
        except Exception as e:
            db.session.rollback()
            error_msg = f'删除失败：{str(e)}'
            self.log_error(error_msg)
            import traceback
            self.log_error(traceback.format_exc())
            return False, error_msg
    
    def delete_paper_by_file_id(self, file_id: int) -> Tuple[bool, Optional[str]]:
        """
        根据文件ID删除论文数据（级联删除材料和性能数据）
        
        Args:
            file_id: 文件ID
        
        Returns:
            (success, error_message)
        """
        try:
            self.log_info(f"根据文件ID删除论文数据: {file_id}")
            
            # 查找文献记录
            article = PaperArticle.query.filter_by(file_id=file_id).first()
            
            if not article:
                self.log_info(f"文件ID {file_id} 没有关联的论文数据")
                return True, None  # 没有数据也算成功
            
            # 使用article_id调用删除方法
            return self.delete_paper_by_article_id(article.article_id)
        
        except Exception as e:
            error_msg = f'删除论文数据失败: {str(e)}'
            self.log_error(error_msg)
            return False, error_msg
    
    def get_paper_by_file_id(self, file_id: int, include_details: bool = True) -> Optional[Dict[str, Any]]:
        """
        根据文件ID获取论文数据
        
        Args:
            file_id: 文件ID
            include_details: 是否包含详细数据
        
        Returns:
            论文数据字典 或 None
        """
        try:
            article = PaperArticle.query.filter_by(file_id=file_id).first()
            
            if not article:
                self.log_info(f"文件ID {file_id} 没有关联的论文数据")
                return None
            
            return article.to_dict(include_details=include_details)
        
        except Exception as e:
            self.log_error(f"获取论文数据失败: {str(e)}")
            return None
    
    def update_review_status(
        self,
        article_id: str,
        review_status: str,
        reviewer_id: int,
        review_comments: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        更新论文审核状态
        
        Args:
            article_id: 文献编号
            review_status: 审核状态（pending/approved/rejected）
            reviewer_id: 审核人ID
            review_comments: 审核意见（可选）
        
        Returns:
            (success, error_message)
        """
        try:
            from datetime import datetime
            
            article = PaperArticle.query.filter_by(article_id=article_id).first()
            
            if not article:
                return False, f'文献编号 {article_id} 不存在'
            
            article.review_status = review_status
            article.reviewer_id = reviewer_id
            article.reviewed_at = datetime.utcnow()
            
            if review_comments:
                article.review_comments = review_comments
            
            db.session.commit()
            
            self.log_info(f"审核状态已更新: {article_id} -> {review_status}")
            
            return True, None
        
        except Exception as e:
            db.session.rollback()
            error_msg = f'更新审核状态失败：{str(e)}'
            self.log_error(error_msg)
            return False, error_msg


