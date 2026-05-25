from pathlib import Path
import hashlib
import mimetypes
import os
import re
import uuid
import json

from django.conf import settings
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from ..models import File, OCRResult
from .checker_ocr_mixin import CheckerOcrMixin


_PLACEHOLDER_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n4 0 obj<</Length 72>>stream\nBT /F1 18 Tf 72 720 Td (PDF preview placeholder - source file unavailable) Tj ET\nendstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n0000000363 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n433\n%%EOF\n"


class CheckerLocalService(CheckerOcrMixin):
    """checker 的 Django 本地适配器（纯 Django 轻量模式，不依赖 Flask 运行时）。"""

    def __init__(self):
        self._load_error = None
        self._tasks = {}
        self._document_data_cache = {}
        self._minio_probe_cache = {'ok': None, 'error': None}

    @property
    def service_name(self):
        return 'checker'

    def health(self):
        return {
            'status': 'ok',
            'service': self.service_name,
            'mode': 'local-in-django-lite',
            'message': 'checker 已切换为 Django 轻量模式（不依赖 sources 目录）',
        }

    def proxy(self, request, path: str):
        normalized = (path or '').lstrip('/').lower()

        if normalized in ('', '/') and request.method == 'GET':
            health = self.health()
            return {
                'status_code': 200,
                'body': {
                    'message': 'Checker OCR API (Django Local)',
                    'service': self.service_name,
                    'version': '1.0.0',
                    'mode': health.get('mode', 'local-in-django-lite'),
                    'health': health,
                    'endpoints': {
                        'health': '/api/ocr/checker/health - GET - 服务健康检查',
                        'proxy': '/api/ocr/checker/<path> - 统一代理入口（按策略回退）',
                    },
                },
            }

        if normalized == 'health' and request.method == 'GET':
            return {
                'status_code': 200,
                'body': self.health(),
            }

        if request.method == 'GET' and normalized in ('api/files', 'files'):
            return self._list_files(request)

        if request.method == 'POST' and normalized in ('api/files/batch-upload', 'files/batch-upload'):
            return self._batch_upload(request)

        if request.method == 'GET' and normalized in ('api/files/count', 'files/count'):
            return self._count_files(request)

        detail_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)', normalized)
        if request.method == 'GET' and detail_match:
            file_id = int(detail_match.group('file_id'))
            return self._get_file_detail(file_id)

        doc_data_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/document-data', normalized)
        if doc_data_match and request.method in ('GET', 'PUT'):
            file_id = int(doc_data_match.group('file_id'))
            if request.method == 'GET':
                return self._get_document_data(file_id, request=request)
            return self._put_document_data(request, file_id)

        complete_review_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/complete-review', normalized)
        if complete_review_match and request.method == 'POST':
            file_id = int(complete_review_match.group('file_id'))
            return self._complete_review(file_id)

        preview_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/preview', normalized)
        if preview_match and request.method == 'GET':
            file_id = int(preview_match.group('file_id'))
            return self._get_preview_url(file_id)

        download_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/download', normalized)
        if download_match and request.method == 'GET':
            file_id = int(download_match.group('file_id'))
            return self._download_file(file_id)

        recognize_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/ocr/recognize', normalized)
        if recognize_match and request.method == 'POST':
            file_id = int(recognize_match.group('file_id'))
            return self._start_recognize(file_id)

        task_match = re.fullmatch(r'(api/)?files/ocr/task/(?P<task_id>[a-z0-9\-]+)', normalized)
        if task_match and request.method == 'GET':
            return self._get_task_status(task_match.group('task_id'))

        save_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/ocr/save', normalized)
        if save_match and request.method == 'POST':
            file_id = int(save_match.group('file_id'))
            return self._save_ocr_result(request, file_id)

        return None

    @staticmethod
    def _parse_json_body(request):
        try:
            if not request.body:
                return {}
            return json.loads(request.body.decode('utf-8'))
        except Exception:
            return {}

    @staticmethod
    def _default_document_payload(document_type: str, file_obj=None):
        file_name = (getattr(file_obj, 'filename', '') or '').strip()
        file_id = getattr(file_obj, 'pk', None)

        if document_type == 'paper':
            return {
                'template_type': 'paper_material_v2',
                'basic_info': {
                    'article_id': '',
                    'article_name': '',
                    'article_doi': '',
                    'publish_year': '',
                },
                'materials': [],
                'preparation_process': '',
                'intermediates': [],
                'properties': {
                    'columns': [],
                    'rows': [],
                },
                'notes': '',
            }
        return {
            'basic_info': {
                'form_number': str(file_id or ''),
                'commission_number': str(file_id or ''),
                'sample_name': file_name,
            },
            'test_items': [],
            'special_tests': [],
        }

    @staticmethod
    def _normalize_document_type(file_obj: File):
        return (file_obj.document_type_code or 'commission').strip().lower()

    @staticmethod
    def _serialize_file(file_obj: File):
        return file_obj.to_dict()

    @staticmethod
    def _serialize_datetime(value):
        if not value:
            return None
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        return str(value)

    @classmethod
    def _serialize_file_summary(cls, file_obj: File):
        tags = []
        if file_obj.tags:
            tags = [tag.strip() for tag in str(file_obj.tags).split(',') if tag.strip()]

        return {
            'id': file_obj.id,
            'filename': file_obj.filename,
            'stored_filename': file_obj.stored_filename,
            'file_path': file_obj.file_path,
            'file_size': file_obj.file_size,
            'file_size_display': file_obj.get_display_size(),
            'file_type': file_obj.file_type,
            'document_type_code': file_obj.document_type_code,
            'mime_type': file_obj.mime_type,
            'md5_hash': file_obj.md5_hash,
            'sha256_hash': file_obj.sha256_hash,
            'uploader_id': file_obj.uploader_id,
            'upload_batch_id': file_obj.upload_batch_id,
            'ocr_status': file_obj.ocr_status,
            'ocr_started_at': None,
            'ocr_completed_at': cls._serialize_datetime(file_obj.ocr_completed_at),
            'ocr_error_message': file_obj.ocr_error_message,
            'review_status': file_obj.review_status,
            'review_started_at': None,
            'review_completed_at': None,
            'page_count': file_obj.page_count,
            'description': file_obj.description,
            'tags': tags,
            'is_deleted': file_obj.is_deleted,
            'is_processed': file_obj.is_processed,
            'created_at': cls._serialize_datetime(file_obj.created_at),
            'updated_at': cls._serialize_datetime(file_obj.updated_at),
            'deleted_at': None,
        }

    @staticmethod
    def _normalize_upload_name(name: str):
        filename = Path(name or '').name.strip()
        return filename or 'uploaded-file.pdf'

    @staticmethod
    def _resolve_upload_suffix(filename: str, content_type: str):
        suffix = Path(filename).suffix.lower()
        if suffix:
            return suffix

        guessed = mimetypes.guess_extension(content_type or '')
        return guessed or ''

    @staticmethod
    def _default_uploader_id():
        return 1

    @staticmethod
    def _next_file_id():
        with connection.cursor() as cursor:
            cursor.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM files')
            row = cursor.fetchone()
        return int((row[0] if row else 1) or 1)

    def _batch_upload(self, request):
        try:
            uploads = request.FILES.getlist('files')
            if not uploads:
                single_file = request.FILES.get('file')
                uploads = [single_file] if single_file else []

            if not uploads:
                return {
                    'status_code': 400,
                    'body': {
                        'success': False,
                        'message': '请至少选择一个文件',
                    },
                }

            document_type = (
                request.POST.get('document_type_code')
                or request.POST.get('document_type')
                or request.POST.get('file_type')
                or 'commission'
            ).strip()
            description = (request.POST.get('description') or '').strip() or None
            tags = (request.POST.get('tags') or '').strip() or None
            batch_id = str(uuid.uuid4())

            upload_dir = Path(settings.MEDIA_ROOT) / 'ocr_uploads' / timezone.localtime().strftime('%Y%m%d')
            upload_dir.mkdir(parents=True, exist_ok=True)

            saved_files = []
            errors = []
            duplicates = []
            seen_hash_keys = {}
            next_file_id = self._next_file_id()

            for uploaded in uploads:
                try:
                    current_file_id = next_file_id
                    original_name = self._normalize_upload_name(getattr(uploaded, 'name', ''))
                    content_type = getattr(uploaded, 'content_type', '') or mimetypes.guess_type(original_name)[0] or 'application/octet-stream'
                    suffix = self._resolve_upload_suffix(original_name, content_type)
                    stored_filename = f'{uuid.uuid4().hex}{suffix}'
                    disk_path = upload_dir / stored_filename

                    md5 = hashlib.md5()
                    sha256 = hashlib.sha256()
                    size = 0
                    with disk_path.open('wb') as dest:
                        for chunk in uploaded.chunks():
                            md5.update(chunk)
                            sha256.update(chunk)
                            size += len(chunk)
                            dest.write(chunk)

                    md5_hex = md5.hexdigest()
                    sha256_hex = sha256.hexdigest()
                    dedupe_key = (sha256_hex, size)

                    # 同一批次内去重：同样内容只保留第一份。
                    if dedupe_key in seen_hash_keys:
                        if disk_path.exists():
                            disk_path.unlink(missing_ok=True)
                        duplicates.append({
                            'filename': original_name,
                            'md5_hash': md5_hex,
                            'sha256_hash': sha256_hex,
                            'file_size': size,
                            'reason': 'duplicate_in_batch',
                            'existing_file_id': seen_hash_keys[dedupe_key],
                        })
                        continue

                    # 历史文件去重：优先 sha256 + size；兼容历史仅 md5 的记录。
                    existing = File.objects.filter(
                        is_deleted=False,
                        file_size=size,
                    ).filter(
                        Q(sha256_hash=sha256_hex)
                        | Q(sha256_hash__isnull=True, md5_hash=md5_hex)
                    ).only('id', 'filename', 'created_at').order_by('-created_at').first()

                    if existing:
                        if disk_path.exists():
                            disk_path.unlink(missing_ok=True)
                        duplicates.append({
                            'filename': original_name,
                            'md5_hash': md5_hex,
                            'sha256_hash': sha256_hex,
                            'file_size': size,
                            'reason': 'duplicate_in_history',
                            'existing_file_id': existing.pk,
                            'existing_filename': existing.filename,
                            'existing_created_at': self._serialize_datetime(existing.created_at),
                        })
                        seen_hash_keys[dedupe_key] = existing.pk
                        continue

                    file_obj = File.objects.create(
                        id=current_file_id,
                        filename=original_name,
                        stored_filename=stored_filename,
                        file_path=str(disk_path),
                        file_size=size,
                        file_type=suffix or Path(original_name).suffix.lower() or '',
                        document_type_code=document_type,
                        mime_type=content_type,
                        md5_hash=md5_hex,
                        sha256_hash=sha256_hex,
                        uploader_id=self._default_uploader_id(),
                        upload_batch_id=batch_id,
                        ocr_status='pending',
                        review_status='unassigned',
                        description=description,
                        tags=tags,
                    )

                    seen_hash_keys[dedupe_key] = current_file_id
                    next_file_id += 1
                    saved_files.append(self._serialize_file(file_obj))
                except Exception as exc:
                    errors.append({
                        'filename': getattr(uploaded, 'name', ''),
                        'message': str(exc),
                    })

            if errors and not saved_files:
                return {
                    'status_code': 500,
                    'body': {
                        'success': False,
                        'message': '上传失败',
                        'errors': errors,
                        'duplicates': duplicates,
                    },
                }

            if duplicates and saved_files and not errors:
                message = '部分文件上传成功，重复文件已跳过'
            elif duplicates and not saved_files and not errors:
                message = '文件均已存在，未新增'
            elif errors:
                message = '部分文件上传成功'
            else:
                message = '上传成功'

            return {
                'status_code': 200 if not errors else 207,
                'body': {
                    'success': not errors,
                    'message': message,
                    'data': {
                        'batch_id': batch_id,
                        'files': saved_files,
                        'total': len(saved_files),
                        'duplicates': duplicates,
                        'duplicate_count': len(duplicates),
                        'errors': errors,
                    },
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'上传失败: {exc}',
                    'service': self.service_name,
                },
            }

    def _list_files(self, request):
        try:
            page = max(int(request.GET.get('page', 1)), 1)
            per_page = min(max(int(request.GET.get('per_page', 20)), 1), 100)
            status_filter = request.GET.get('status')
            review_status_filter = request.GET.get('review_status')
            document_type_filter = request.GET.get('document_type')

            queryset = File.objects.filter(is_deleted=False).only(
                'id',
                'filename',
                'stored_filename',
                'file_path',
                'file_size',
                'file_type',
                'document_type_code',
                'mime_type',
                'md5_hash',
                'sha256_hash',
                'uploader_id',
                'upload_batch_id',
                'ocr_status',
                'ocr_completed_at',
                'ocr_error_message',
                'review_status',
                'page_count',
                'description',
                'tags',
                'is_deleted',
                'is_processed',
                'created_at',
                'updated_at',
            ).order_by('-created_at')

            if status_filter:
                queryset = queryset.filter(ocr_status=status_filter)
            if review_status_filter:
                queryset = queryset.filter(review_status=review_status_filter)
            if document_type_filter:
                queryset = queryset.filter(document_type_code=document_type_filter)

            paginator = Paginator(queryset, per_page)
            page_obj = paginator.get_page(page)
            files_data = []
            serialize_error_count = 0
            for item in page_obj.object_list:
                try:
                    files_data.append(self._serialize_file_summary(item))
                except Exception:
                    serialize_error_count += 1
                    files_data.append(
                        {
                            'id': item.pk,
                            'filename': item.filename,
                            'document_type_code': item.document_type_code,
                            'ocr_status': item.ocr_status,
                            'review_status': item.review_status,
                            'created_at': str(item.created_at) if item.created_at else None,
                            'updated_at': str(item.updated_at) if item.updated_at else None,
                        }
                    )

            message = '获取文件列表成功（Django本地checker）'
            if serialize_error_count:
                message = f'获取文件列表成功（部分记录降级返回，异常{serialize_error_count}条）'

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': message,
                    'data': {
                        'files': files_data,
                        'total': paginator.count,
                        'pages': paginator.num_pages if paginator.count else 0,
                        'current_page': page,
                        'per_page': per_page,
                    },
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'读取文件列表失败: {exc}',
                    'service': self.service_name,
                },
            }

    def _get_file_detail(self, file_id: int):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {
                    'status_code': 404,
                    'body': {
                        'success': False,
                        'message': '文件不存在',
                    },
                }

            payload = self._serialize_file(file_obj)
            payload['ocr_results'] = [
                item.to_dict(include_raw=True)
                for item in OCRResult.objects.filter(file_id=file_obj.pk).order_by('page_number', 'id')
            ]

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '获取文件详情成功（Django本地checker）',
                    'data': payload,
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'获取文件详情失败: {exc}',
                    'service': self.service_name,
                },
            }

    def _count_files(self, request):
        try:
            status_filter = request.GET.get('status')
            review_status_filter = request.GET.get('review_status')
            document_type_filter = request.GET.get('document_type')

            queryset = File.objects.filter(is_deleted=False)

            if status_filter:
                queryset = queryset.filter(ocr_status=status_filter)
            if review_status_filter:
                queryset = queryset.filter(review_status=review_status_filter)
            if document_type_filter:
                queryset = queryset.filter(document_type_code=document_type_filter)

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '获取文件统计成功（Django本地checker）',
                    'data': {
                        'total': queryset.count(),
                    },
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'读取文件统计失败: {exc}',
                    'service': self.service_name,
                },
            }

    def _get_document_data(self, file_id: int, request=None):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {
                    'status_code': 404,
                    'body': {'success': False, 'message': '文件不存在'},
                }
            document_type = self._normalize_document_type(file_obj)
            cached = self._document_data_cache.get(file_id)
            persisted = self._load_latest_ocr_payload(file_id)
            if document_type == 'paper':
                cached_paper = cached if isinstance(cached, dict) else None
                persisted_paper = persisted if isinstance(persisted, dict) else None
                legacy_paper = self._load_paper_document_from_legacy_tables(file_id)
                data = self._select_richer_paper_payload(cached_paper, persisted_paper)
                data = self._select_richer_paper_payload(data, legacy_paper)
                data = self._normalize_paper_payload(data)
                if self._is_meaningful_document_payload(document_type, data):
                    self._document_data_cache[file_id] = data
                else:
                    data = self._default_document_payload(document_type, file_obj)
            elif isinstance(cached, dict) and self._is_meaningful_document_payload(document_type, cached):
                data = cached
            elif isinstance(persisted, dict) and self._is_meaningful_document_payload(document_type, persisted):
                data = persisted
                self._document_data_cache[file_id] = data
            else:
                data = self._default_document_payload(document_type, file_obj)

            if not data:
                data = self._default_document_payload(document_type, file_obj)

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'document_type': document_type,
                    'data': data,
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'读取文档数据失败: {exc}'},
            }

    @staticmethod
    def _is_meaningful_document_payload(document_type: str, payload):
        if not isinstance(payload, dict):
            return False

        if document_type == 'paper':
            normalized = CheckerLocalService._normalize_paper_payload(payload)
            basic_info = normalized.get('basic_info') or {}
            if CheckerLocalService._paper_text(basic_info.get('article_id')):
                return True
            if CheckerLocalService._paper_text(basic_info.get('article_doi')):
                return True
            if CheckerLocalService._paper_text(basic_info.get('publish_year')):
                return True
            if normalized.get('materials'):
                return True
            if CheckerLocalService._paper_text(normalized.get('preparation_process')):
                return True
            if normalized.get('intermediates'):
                return True
            properties = normalized.get('properties') or {}
            if properties.get('columns') or properties.get('rows'):
                return True
            if CheckerLocalService._paper_text(normalized.get('notes')):
                return True
            return False

        basic_info = payload.get('basic_info')
        if isinstance(basic_info, dict) and len(basic_info) > 0:
            return True
        test_items = payload.get('test_items')
        if isinstance(test_items, list) and len(test_items) > 0:
            return True
        special_tests = payload.get('special_tests')
        if isinstance(special_tests, list) and len(special_tests) > 0:
            return True
        return False

    def _put_document_data(self, request, file_id: int):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {
                    'status_code': 404,
                    'body': {'success': False, 'message': '文件不存在'},
                }

            payload = self._parse_json_body(request)
            document_type = self._normalize_document_type(file_obj)
            if document_type == 'paper':
                payload = self._normalize_paper_payload(payload)
            self._document_data_cache[file_id] = payload if isinstance(payload, dict) else {}

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '保存成功（Django本地checker）',
                    'document_type': document_type,
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'保存文档数据失败: {exc}'},
            }

    def _complete_review(self, file_id: int):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {
                    'status_code': 404,
                    'body': {'success': False, 'message': '文件不存在'},
                }

            file_obj.review_status = 'completed'
            file_obj.review_completed_at = timezone.now()
            file_obj.save(update_fields=['review_status', 'review_completed_at', 'updated_at'])

            return {
                'status_code': 200,
                'body': {'success': True, 'message': '已完成核对'},
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'完成核对失败: {exc}'},
            }

    def _get_preview_url(self, file_id: int):
        file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
        if not file_obj:
            return {'status_code': 404, 'body': {'success': False, 'message': '文件不存在'}}

        diagnostics = self._build_preview_diagnostics(file_obj)

        # 为避免 iframe 预览时鉴权问题，统一让前端走 blob 下载预览回退。
        return {
            'status_code': 200,
            'body': {
                'success': True,
                'message': '本地checker使用blob方式预览',
                'data': {
                    'fallback': True,
                    'diagnostics': diagnostics,
                },
            },
        }

    def _build_preview_diagnostics(self, file_obj: File):
        file_path_value = (file_obj.file_path or '').strip()
        file_path = Path(file_path_value)
        local_exists = file_path.exists() and file_path.is_file()

        diagnostics = {
            'mode': 'local-file' if local_exists else 'object-storage-or-missing',
            'file_id': file_obj.pk,
            'filename': file_obj.filename,
            'file_path': file_path_value,
            'local_exists': local_exists,
        }

        if not local_exists:
            probe = self._probe_minio_object(file_obj)
            diagnostics['minio'] = probe

        return diagnostics

    def _download_file(self, file_id: int):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {'status_code': 404, 'body': {'success': False, 'message': '文件不存在'}}

            file_path = Path(file_obj.file_path or '')
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                content_type = file_obj.mime_type or 'application/octet-stream'
                return {
                    'status_code': 200,
                    'raw_body': content,
                    'content_type': content_type,
                }

            # 本地文件不存在时，尝试从 MinIO 拉取真实内容。
            minio_bytes = self._try_download_from_minio(file_obj)
            if minio_bytes is not None:
                return {
                    'status_code': 200,
                    'raw_body': minio_bytes,
                    'content_type': file_obj.mime_type or 'application/pdf',
                }

            # MinIO对象键场景下如果仍不可读，返回占位PDF避免前端404报错与白屏。
            return {
                'status_code': 200,
                'raw_body': _PLACEHOLDER_PDF_BYTES,
                'content_type': 'application/pdf',
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'下载失败: {exc}'},
            }

