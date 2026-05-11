"""
文件管理服务
"""
import uuid
import os
from datetime import datetime
from flask import current_app
from models.file import File
from models.ocr_result import OCRResult
from models import db, get_models
from .minio_service import MinioService
from adapters.commission_adapter import CommissionAdapter
from adapters.paper_adapter import PaperAdapter
import logging

logger = logging.getLogger(__name__)

# 获取模型
models = get_models()
FileTypeConfig = models.get('FileTypeConfig')


class FileService:
    """文件管理服务类"""
    
    def __init__(self):
        self.minio_service = MinioService()
        # 适配器缓存
        self._adapters = {}
    
    def _get_adapter(self, document_type_code: str):
        """
        根据文档类型获取对应的适配器
        
        Args:
            document_type_code: 文档类型代码（commission/paper等）
            
        Returns:
            适配器实例或None
        """
        if not document_type_code:
            logger.warning("未指定文档类型代码")
            return None
        
        # 从缓存中获取
        if document_type_code in self._adapters:
            return self._adapters[document_type_code]
        
        # 尝试从file_type_configs获取适配器配置
        if FileTypeConfig:
            try:
                config = FileTypeConfig.query.filter_by(
                    type_code=document_type_code,
                    is_active=True
                ).first()
                
                if config:
                    adapter = config.get_adapter_instance()
                    self._adapters[document_type_code] = adapter
                    logger.info(f"从配置加载适配器: {document_type_code} -> {adapter.__class__.__name__}")
                    return adapter
            except Exception as e:
                logger.warning(f"从配置加载适配器失败: {str(e)}")
        
        # 回退到硬编码的适配器映射
        adapter_map = {
            'commission': CommissionAdapter,
            'paper': PaperAdapter
        }
        
        adapter_class = adapter_map.get(document_type_code)
        if adapter_class:
            adapter = adapter_class()
            self._adapters[document_type_code] = adapter
            logger.info(f"使用默认适配器: {document_type_code} -> {adapter.__class__.__name__}")
            return adapter
        
        logger.warning(f"未找到适配器: {document_type_code}")
        return None
    
    def upload_file(self, file_obj, filename, uploader_id, batch_id=None, description=None, tags=None, document_type_code=None):
        """
        上传文件
        
        Args:
            file_obj: 文件对象
            filename: 原始文件名
            uploader_id: 上传用户ID
            batch_id: 批次ID
            description: 文件描述
            tags: 标签列表
            document_type_code: 文档类型代码（commission/paper等）
            
        Returns:
            dict: 上传结果
        """
        print(f"\n[FileService.upload_file] 开始上传文件: {filename}")
        print(f"  - uploader_id: {uploader_id}")
        print(f"  - document_type_code: {document_type_code}")
        print(f"  - batch_id: {batch_id}")
        print(f"  - description: {description}")
        print(f"  - tags: {tags}")
        
        try:
            # 检查文件类型
            file_extension = os.path.splitext(filename)[1].lower()
            print(f"  - 文件扩展名: {file_extension}")
            
            if file_extension not in current_app.config['UPLOAD_EXTENSIONS']:
                print(f"  ❌ 不支持的文件类型: {file_extension}")
                print(f"  支持的类型: {current_app.config['UPLOAD_EXTENSIONS']}")
                return {
                    'success': False,
                    'message': f'不支持的文件类型: {file_extension}'
                }
            
            print(f"  ✓ 文件类型检查通过")
            
            # 上传到MinIO
            print(f"  [MinIO] 开始上传到MinIO...")
            upload_result = self.minio_service.upload_file(file_obj, filename)
            
            if not upload_result['success']:
                print(f"  ❌ MinIO上传失败: {upload_result.get('error')}")
                return {
                    'success': False,
                    'message': f'文件上传失败: {upload_result.get("error")}'
                }
            
            print(f"  ✓ MinIO上传成功")
            print(f"    - stored_filename: {upload_result['stored_filename']}")
            print(f"    - object_name: {upload_result['object_name']}")
            print(f"    - file_size: {upload_result['file_size']}")
            
            # 创建文件记录
            print(f"  [数据库] 创建文件记录...")
            file_record = File(
                filename=filename,
                stored_filename=upload_result['stored_filename'],
                file_path=upload_result['object_name'],
                file_size=upload_result['file_size'],
                file_type=file_extension,
                mime_type=upload_result['content_type'],
                uploader_id=uploader_id,
                upload_batch_id=batch_id or str(uuid.uuid4()),
                document_type_code=document_type_code  # 新增
            )
            
            file_record.md5_hash = upload_result['md5_hash']
            file_record.description = description
            
            if tags:
                file_record.set_tags_list(tags)
            
            print(f"  [数据库] 添加到session...")
            db.session.add(file_record)
            
            print(f"  [数据库] 提交事务...")
            db.session.commit()
            
            print(f"  ✓ 数据库记录创建成功，文件ID: {file_record.id}")
            
            current_app.logger.info(f'文件上传成功: {filename} (ID: {file_record.id})')
            
            result = {
                'success': True,
                'message': '文件上传成功',
                'data': file_record.to_dict()
            }
            
            print(f"[FileService.upload_file] ✅ 上传完成\n")
            return result
            
        except Exception as e:
            print(f"  ❌❌❌ 异常发生:")
            print(f"    异常类型: {type(e).__name__}")
            print(f"    异常信息: {str(e)}")
            import traceback
            print(f"    堆栈跟踪:\n{traceback.format_exc()}")
            
            db.session.rollback()
            print(f"  [数据库] 事务已回滚")
            
            current_app.logger.error(f'文件上传服务异常: {str(e)}')
            return {
                'success': False,
                'message': f'文件上传失败: {str(e)}'
            }
    
    def batch_upload_files(self, files_data, uploader_id, description=None, tags=None, document_type_code=None):
        """
        批量上传文件
        
        Args:
            files_data: 文件数据列表 [{'file_obj': file, 'filename': name}, ...]
            uploader_id: 上传用户ID
            description: 批次描述
            tags: 标签列表
            document_type_code: 文档类型代码（commission/paper等）
            
        Returns:
            dict: 批量上传结果
        """
        batch_id = str(uuid.uuid4())
        results = []
        successful_uploads = 0
        failed_uploads = 0
        
        print(f"\n[FileService.batch_upload_files] 开始批量上传")
        print(f"  - batch_id: {batch_id}")
        print(f"  - 文件数量: {len(files_data)}")
        print(f"  - document_type_code: {document_type_code}")
        
        for idx, file_data in enumerate(files_data, 1):
            file_obj = file_data['file_obj']
            filename = file_data['filename']
            
            print(f"\n  [{idx}/{len(files_data)}] 处理文件: {filename}")
            
            result = self.upload_file(
                file_obj=file_obj,
                filename=filename,
                uploader_id=uploader_id,
                batch_id=batch_id,
                description=description,
                tags=tags,
                document_type_code=document_type_code  # 新增
            )
            
            results.append({
                'filename': filename,
                'success': result['success'],
                'message': result['message'],
                'data': result.get('data')
            })
            
            if result['success']:
                successful_uploads += 1
                print(f"  ✓ 文件上传成功")
            else:
                failed_uploads += 1
                print(f"  ✗ 文件上传失败: {result['message']}")
        
        summary = {
            'batch_id': batch_id,
            'total_files': len(files_data),
            'successful_uploads': successful_uploads,
            'failed_uploads': failed_uploads,
            'results': results
        }
        
        print(f"\n[FileService.batch_upload_files] 批量上传完成")
        print(f"  总计: {summary['total_files']} | 成功: {successful_uploads} | 失败: {failed_uploads}\n")
        
        return summary
    
    def get_file_by_id(self, file_id):
        """根据ID获取文件"""
        try:
            file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
            if not file_record:
                return None
            return file_record
            
        except Exception as e:
            current_app.logger.error(f'获取文件失败: {str(e)}')
            return None
    
    def get_files_by_user(self, user_id, page=1, per_page=20, status_filter=None):
        """获取用户上传的文件列表"""
        try:
            query = File.query.filter_by(uploader_id=user_id, is_deleted=False)
            
            if status_filter:
                query = query.filter_by(ocr_status=status_filter)
            
            query = query.order_by(File.created_at.desc())
            
            pagination = query.paginate(
                page=page, 
                per_page=per_page, 
                error_out=False
            )
            
            return {
                'files': [file.to_dict() for file in pagination.items],
                'total': pagination.total,
                'pages': pagination.pages,
                'current_page': page,
                'per_page': per_page
            }
            
        except Exception as e:
            current_app.logger.error(f'获取用户文件列表失败: {str(e)}')
            return None
    
    def delete_file(self, file_id, user_id, hard_delete=False):
        """
        删除文件（软删除或硬删除）
        
        重构说明：现在会根据文件类型调用相应的适配器删除数据库中的业务数据
        """
        try:
            file_record = File.query.filter_by(id=file_id, uploader_id=user_id).first()
            
            if not file_record:
                return {
                    'success': False,
                    'message': '文件不存在或无权限删除'
                }
            
            # 根据文件类型删除业务数据
            if file_record.document_type_code:
                logger.info(f"删除文件的业务数据: file_id={file_id}, type={file_record.document_type_code}")
                adapter = self._get_adapter(file_record.document_type_code)
                if adapter:
                    try:
                        success, error = adapter.delete_from_database(file_id)
                        if not success:
                            logger.warning(f"适配器删除业务数据失败: {error}")
                        else:
                            logger.info(f"适配器删除业务数据成功")
                    except Exception as adapter_error:
                        logger.error(f"适配器删除业务数据出错: {str(adapter_error)}")
                else:
                    logger.warning(f"未找到适配器: {file_record.document_type_code}")
            
            if hard_delete:
                # 硬删除：从MinIO和数据库中完全删除
                self.minio_service.delete_file(file_record.file_path)
                db.session.delete(file_record)
                message = '文件已彻底删除'
            else:
                # 软删除：仅标记为删除
                file_record.soft_delete()
                message = '文件已删除'
            
            db.session.commit()
            
            return {
                'success': True,
                'message': message
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f'删除文件失败: {str(e)}')
            return {
                'success': False,
                'message': f'删除文件失败: {str(e)}'
            }
    
    def restore_file(self, file_id, user_id):
        """恢复已删除的文件"""
        try:
            file_record = File.query.filter_by(id=file_id, uploader_id=user_id, is_deleted=True).first()
            
            if not file_record:
                return {
                    'success': False,
                    'message': '文件不存在或未被删除'
                }
            
            file_record.restore()
            db.session.commit()
            
            return {
                'success': True,
                'message': '文件已恢复'
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'恢复文件失败: {str(e)}')
            return {
                'success': False,
                'message': f'恢复文件失败: {str(e)}'
            }
    
    def update_file_info(self, file_id, user_id, **update_data):
        """更新文件信息"""
        try:
            file_record = File.query.filter_by(id=file_id, uploader_id=user_id, is_deleted=False).first()
            
            if not file_record:
                return {
                    'success': False,
                    'message': '文件不存在'
                }
            
            # 更新允许修改的字段
            allowed_fields = ['description', 'tags']
            for field, value in update_data.items():
                if field in allowed_fields:
                    if field == 'tags':
                        file_record.set_tags_list(value)
                    else:
                        setattr(file_record, field, value)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': '文件信息已更新',
                'data': file_record.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'更新文件信息失败: {str(e)}')
            return {
                'success': False,
                'message': f'更新文件信息失败: {str(e)}'
            }
    
    def download_file(self, file_id, user_id=None):
        """下载文件"""
        try:
            file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
            
            if not file_record:
                return None
            
            # 如果指定了用户ID，检查权限（管理员可以下载任何文件）
            if user_id and file_record.uploader_id != user_id:
                # 这里可以添加更复杂的权限检查
                pass
            
            # 从MinIO下载文件
            file_data = self.minio_service.download_file(file_record.file_path)
            
            if file_data:
                return {
                    'file_data': file_data,
                    'filename': file_record.filename,
                    'content_type': file_record.mime_type
                }
            
            return None
            
        except Exception as e:
            current_app.logger.error(f'下载文件失败: {str(e)}')
            return None
    
    def get_file_preview_url(self, file_id, expires=3600):
        """获取文件预览URL"""
        try:
            file_record = File.query.filter_by(id=file_id, is_deleted=False).first()
            
            if not file_record:
                current_app.logger.warning(f'文件不存在: file_id={file_id}')
                return None
            
            current_app.logger.info(f'获取文件预览URL: {file_record.filename} (id: {file_id})')
            current_app.logger.info(f'文件路径: {file_record.file_path}')
            
            # 获取预签名URL
            url = self.minio_service.get_file_url(file_record.file_path, expires)
            
            if url:
                return {
                    'url': url,
                    'filename': file_record.filename,
                    'content_type': file_record.mime_type
                }
            else:
                # 如果MinIO预签名URL失败，尝试通过下载接口
                current_app.logger.warning('MinIO预签名URL失败，将使用下载接口作为回退')
                download_url = f"/api/files/{file_id}/download"
                return {
                    'url': download_url,
                    'filename': file_record.filename,
                    'content_type': file_record.mime_type,
                    'fallback': True
                }
            
        except Exception as e:
            current_app.logger.error(f'获取预览URL失败: {str(e)}')
            import traceback
            current_app.logger.error(f'异常详情: {traceback.format_exc()}')
            return None
    
    def start_ocr_processing(self, file_id, model_id=None):
        """开始OCR处理 - 调用外部OCR API（同步方式）
        
        @deprecated: 此方法为旧版同步OCR处理，建议迁移到 OcrTaskService.create_task()
        
        现状：
        - 此方法仍被 /files/<file_id>/process API endpoint 使用
        - 主要用于文件列表页面的批量处理
        - 同步调用，可能导致请求超时
        
        推荐方案：
        - 新功能请使用 OcrTaskService.create_task() + start_task_processing()
        - 支持异步处理、任务状态查询、进度反馈
        - 识别页面已迁移至新方案 (/files/<file_id>/ocr/recognize)
        
        迁移计划：
        1. 待系统稳定后，逐步迁移文件列表页面到异步任务
        2. 添加功能开关，支持新旧方案切换
        3. 完全迁移后废弃此方法
        
        Args:
            file_id: 文件ID
            model_id: 模型配置ID（可选），如果不提供则使用默认模型
        
        Returns:
            dict: 包含success和message的结果字典
        """
        import requests
        import json
        import traceback
        from models.model_config import ModelConfig
        
        try:
            current_app.logger.info(f'🚀 开始OCR处理，file_id: {file_id}, model_id: {model_id}')
            
            # 获取文件记录
            file_record = self.get_file_by_id(file_id)
            if not file_record:
                return {
                    'success': False,
                    'message': '文件不存在'
                }
            
            # 获取文件路径
            file_path = file_record.file_path
            current_app.logger.info(f'📄 文件存储路径: {file_path}')
            
            # 从MinIO下载文件到内存
            current_app.logger.info(f'📥 从MinIO下载文件...')
            file_data = self.minio_service.download_file(file_path)
            if not file_data:
                return {
                    'success': False,
                    'message': '无法从存储服务下载文件'
                }
            current_app.logger.info(f'✅ 文件下载成功，大小: {len(file_data)} bytes')
            
            # 获取模型配置
            model_config = None
            if model_id:
                model_config = ModelConfig.query.get(model_id)
                if not model_config or not model_config.is_active:
                    return {
                        'success': False,
                        'message': '指定的模型不存在或未启用'
                    }
            else:
                # 使用默认模型
                model_config = ModelConfig.query.filter_by(
                    is_default=True,
                    is_active=True
                ).first()
                
                if not model_config:
                    # 如果没有默认模型，使用第一个激活的模型
                    model_config = ModelConfig.query.filter_by(is_active=True).first()
                
                if not model_config:
                    return {
                        'success': False,
                        'message': '没有可用的OCR模型配置'
                    }
            
            current_app.logger.info(f'🤖 使用模型: {model_config.name} ({model_config.api_url})')
            
            # 更新文件状态为处理中，记录使用的模型
            file_record.ocr_status = 'processing'
            file_record.model_id = model_config.id
            db.session.commit()
            
            # 准备请求
            ocr_api_url = model_config.api_url
            timeout = model_config.timeout or 120
            
            files = {
                'file': (file_record.filename, file_data, 'application/pdf')
            }
            
            current_app.logger.info(f'📡 调用OCR API: {ocr_api_url}, 超时: {timeout}秒')
            
            # 发送请求到OCR服务
            response = requests.post(
                ocr_api_url,
                files=files,
                timeout=timeout
            )
            
            if response.status_code != 200:
                raise Exception(f'OCR API返回错误状态码: {response.status_code}')
            
            result = response.json()
            
            if not result.get('success'):
                raise Exception(f'OCR处理失败: {result.get("message", "未知错误")}')
            
            current_app.logger.info(f'✅ OCR API调用成功')
            
            # 注意：这是旧的OCR处理流程，建议使用 OcrTaskService.create_and_run_task()
            # TODO: 迁移到新的异步任务处理流程
            
            # 使用适配器保存OCR结果
            if file_record.document_type_code:
                adapter = self._get_adapter(file_record.document_type_code)
                if adapter:
                    try:
                        # 解析OCR结果
                        structured_data = adapter.parse_ocr_result(result)
                        # 保存到数据库
                        success, error = adapter.save_to_database(structured_data, file_id)
                        if not success:
                            current_app.logger.warning(f'适配器保存数据失败: {error}')
                    except Exception as e:
                        current_app.logger.error(f'适配器处理失败: {str(e)}')
            
            # 更新文件状态为完成
            file_record.ocr_status = 'completed'
            file_record.is_processed = True
            db.session.commit()
            
            return {
                'success': True,
                'message': 'OCR处理成功',
                'data': {
                    'file_id': file_id,
                    'model_name': model_config.name,
                    'total_pages': result.get('total_pages', 0),
                    'processing_time': result.get('processing_time', 0)
                }
            }
            
        except requests.exceptions.Timeout:
            current_app.logger.error('❌ OCR API请求超时')
            file_record.ocr_status = 'failed'
            db.session.commit()
            return {
                'success': False,
                'message': 'OCR处理超时，请稍后重试'
            }
        except Exception as e:
            current_app.logger.error(f'❌ OCR处理失败: {str(e)}')
            current_app.logger.error(f'堆栈信息: {traceback.format_exc()}')
            file_record.ocr_status = 'failed'
            db.session.commit()
            return {
                'success': False,
                'message': f'OCR处理失败: {str(e)}'
            }

    
    def get_file_ocr_results(self, file_id):
        """获取文件的OCR识别结果"""
        try:
            ocr_results = OCRResult.query.filter_by(file_id=file_id).order_by(OCRResult.page_number).all()
            
            return [result.to_dict() for result in ocr_results]
            
        except Exception as e:
            current_app.logger.error(f'获取OCR结果失败: {str(e)}')
            return []
    
    # [已废弃] _is_commission_pdf - 功能已迁移到 CommissionAdapter
    def get_document_data(self, file_id):
        """
        统一接口：获取文档业务数据
        
        Args:
            file_id: 文件ID
            
        Returns:
            dict: 文档业务数据，或None
        """
        try:
            logger.info(f"🔍 [FileService] 开始获取文档数据: file_id={file_id}")
            file_record = File.query.get(file_id)
            if not file_record:
                logger.error(f'❌ [FileService] 文件记录不存在，file_id: {file_id}')
                return None
            
            logger.info(f"📄 [FileService] 文件信息: document_type_code={file_record.document_type_code}")
            
            # 根据文件类型获取适配器
            if not file_record.document_type_code:
                logger.warning(f'⚠️ [FileService] 文件未设置document_type_code: file_id={file_id}')
                return None
            
            adapter = self._get_adapter(file_record.document_type_code)
            if not adapter:
                logger.warning(f'⚠️ [FileService] 未找到适配器: {file_record.document_type_code}')
                return None
            
            logger.info(f"🔧 [FileService] 使用适配器: {adapter.__class__.__name__}")
            
            # 调用适配器获取数据
            success, data, error = adapter.get_from_database(file_id)
            logger.info(f"🔍 [FileService] 适配器返回: success={success}, data类型={type(data)}, error={error}")
            
            if success:
                if data:
                    logger.info(f"✅ [FileService] 成功获取数据: basic_info字段数={len(data.get('basic_info', {}))}")
                else:
                    logger.warning(f"⚠️ [FileService] 成功但数据为None")
                return data
            else:
                logger.error(f'❌ [FileService] 适配器获取数据失败: {error}')
                return None
                
        except Exception as e:
            logger.error(f'❌ [FileService] 获取文档数据失败: {str(e)}')
            import traceback
            logger.error(f'错误详情: {traceback.format_exc()}')
            return None
                
    def save_document_data(self, file_id: int, data: dict) -> dict:
        """
        统一接口：首次保存文档业务数据（INSERT）
        
        Args:
            file_id: 文件ID
            data: 文档数据
            
        Returns:
            dict: {
                'success': bool,
                'message': str
            }
        """
        try:
            logger.info(f"🔍 [FileService] 开始保存文档数据: file_id={file_id}")
            file_record = File.query.get(file_id)
            if not file_record:
                return {
                    'success': False,
                    'message': f'文件记录不存在，file_id: {file_id}'
                }
            
            logger.info(f"📄 [FileService] 文件信息: document_type_code={file_record.document_type_code}")
            
            # 根据文件类型获取适配器
            if not file_record.document_type_code:
                return {
                    'success': False,
                    'message': '文件未设置document_type_code'
                }
            
            adapter = self._get_adapter(file_record.document_type_code)
            if not adapter:
                return {
                    'success': False,
                    'message': f'不支持的文档类型: {file_record.document_type_code}'
                }
            
            logger.info(f"🔧 [FileService] 使用适配器: {adapter.__class__.__name__}")
            
            # 调用适配器保存数据
            success, error = adapter.save_to_database(data, file_id)
            
            if success:
                logger.info(f"✅ [FileService] 文档数据保存成功")
                return {
                    'success': True,
                    'message': '保存成功'
                }
            else:
                logger.error(f"❌ [FileService] 文档数据保存失败: {error}")
                return {
                    'success': False,
                    'message': error or '保存失败'
                }
                
        except Exception as e:
            logger.error(f'❌ [FileService] 保存文档数据失败: {str(e)}')
            import traceback
            logger.error(f'错误详情: {traceback.format_exc()}')
            return {
                'success': False,
                'message': f'保存失败: {str(e)}'
            }
    
    def update_document_data(self, file_id, data):
        """
        统一接口：更新文档业务数据
        
        Args:
            file_id: 文件ID
            data: 更新的数据
            
        Returns:
            dict: {
                'success': bool,
                'message': str
            }
        """
        try:
            file_record = File.query.get(file_id)
            if not file_record:
                return {
                    'success': False,
                    'message': f'文件记录不存在，file_id: {file_id}'
                }
            
            # 根据文件类型获取适配器
            if not file_record.document_type_code:
                return {
                    'success': False,
                    'message': '文件未设置document_type_code'
                }
            
            adapter = self._get_adapter(file_record.document_type_code)
            if not adapter:
                return {
                    'success': False,
                    'message': f'未找到适配器: {file_record.document_type_code}'
                }
            
            # 调用适配器更新数据
            success, error = adapter.update_in_database(data, file_id)
            if success:
                return {
                    'success': True,
                    'message': '更新成功'
                }
            else:
                return {
                    'success': False,
                    'message': error or '更新失败'
                }
                
        except Exception as e:
            logger.error(f'更新文档数据失败: {str(e)}')
            import traceback
            logger.error(f'错误详情: {traceback.format_exc()}')
            return {
                'success': False,
                'message': f'更新失败: {str(e)}'
            }
    
    # ==================== 委托单特定接口（保留用于向后兼容） ====================
    
    # [已废弃] get_commission_data - 请使用 get_document_data() 统一接口
    # 功能已迁移到 CommissionAdapter.get_from_database()
    
    # [已废弃] _get_commission_number_from_file - 请使用 CommissionAdapter.get_commission_number_from_file()
    # 功能已迁移到 CommissionAdapter
    
    # [已废弃] _get_commission_number_from_file_deprecated - 功能已迁移到 CommissionAdapter
    # [已废弃] _extract_commission_number_from_filename - 功能已迁移到 CommissionAdapter
    # [已废弃] update_commission_data - 功能已迁移到 CommissionAdapter
    # [已废弃] _save_ocr_results - 功能已迁移到适配器的 save_to_database()
