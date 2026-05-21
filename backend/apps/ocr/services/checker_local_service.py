from pathlib import Path
import hashlib
import mimetypes
import os
import re
import threading
import uuid
import json
import importlib

from django.conf import settings
from django.core.paginator import Paginator
from django.db import close_old_connections, connection
from django.utils import timezone
import requests

from ..models import File, OCRResult
from .config import get_paper_dify_config, get_service_base_urls, get_timeout


_PLACEHOLDER_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n4 0 obj<</Length 72>>stream\nBT /F1 18 Tf 72 720 Td (PDF preview placeholder - source file unavailable) Tj ET\nendstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n0000000363 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n433\n%%EOF\n"


class CheckerLocalService:
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
    def _empty_paper_document_payload():
        return CheckerLocalService._default_document_payload('paper')

    @staticmethod
    def _paper_text(value):
        if value is None:
            return ''
        if isinstance(value, dict):
            for key in ('value', 'text', 'content', 'name'):
                if key in value:
                    return CheckerLocalService._paper_text(value.get(key))
            return ''
        if isinstance(value, list):
            for item in value:
                text = CheckerLocalService._paper_text(item)
                if text:
                    return text
            return ''
        return str(value).strip()

    @staticmethod
    def _paper_first_value(source, keys):
        if not isinstance(source, dict):
            return ''
        for key in keys:
            if key not in source:
                continue
            value = CheckerLocalService._paper_text(source.get(key))
            if value:
                return value
        return ''

    @staticmethod
    def _paper_ensure_list(value):
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            for key in ('rows', 'data', 'items'):
                nested = value.get(key)
                if isinstance(nested, list):
                    return nested
        return []

    @staticmethod
    def _paper_slugify(value: str, fallback_index: int):
        text = re.sub(r'[^0-9a-zA-Z\u4e00-\u9fa5]+', '_', str(value or '').strip().lower())
        text = re.sub(r'_+', '_', text).strip('_')
        return text or f'metric_{fallback_index}'

    @classmethod
    def _normalize_paper_material_row(cls, row):
        return {
            'material_id': cls._paper_first_value(row, ['material_id', '原料编号', '材料编号', 'Material ID']),
            'material_name': cls._paper_first_value(row, ['material_name', '原料名称', '材料名称', 'Material Name']),
            'material_characteristic': cls._paper_first_value(
                row,
                ['material_characteristic', '原料特性', '材料特性', 'Material Characteristic', 'characteristic'],
            ),
            'cas_number': cls._paper_first_value(row, ['cas_number', 'CAS', 'cas', 'CAS号', 'CAS Number']),
        }

    @classmethod
    def _normalize_paper_intermediate_row(cls, row):
        return {
            'intermediate_id': cls._paper_first_value(row, ['intermediate_id', '中间体编号', 'Intermediate ID']),
            'formula': cls._paper_first_value(
                row,
                ['formula', '配方', '中间体组成', 'intermediate_composition', '中间体名称', 'intermediate_name'],
            ),
        }

    @classmethod
    def _normalize_paper_properties(cls, value):
        normalized = {'columns': [], 'rows': []}
        product_keys = ['product_name', 'product', '产物（中间体配比）', '产物(中间体配比)', '产物']

        if isinstance(value, dict) and isinstance(value.get('columns'), list) and isinstance(value.get('rows'), list):
            normalized['columns'] = [
                {
                    'key': cls._paper_text(column.get('key')) or cls._paper_slugify(column.get('name'), index + 1),
                    'name': cls._paper_text(column.get('name')) or f'metric_{index + 1}',
                }
                for index, column in enumerate(value.get('columns') or [])
                if isinstance(column, dict)
            ]
            for row in value.get('rows') or []:
                if not isinstance(row, dict):
                    continue
                row_values = {}
                for column in normalized['columns']:
                    row_values[column['key']] = cls._paper_text(
                        (row.get('values') or {}).get(column['key']) if isinstance(row.get('values'), dict) else row.get(column['key'])
                    )
                normalized['rows'].append(
                    {
                        'product_name': cls._paper_first_value(row, product_keys),
                        'values': row_values,
                    }
                )
            return normalized

        rows = [item for item in cls._paper_ensure_list(value) if isinstance(item, dict)]
        if not rows:
            return normalized

        column_map = {}
        for row in rows:
            for key in row.keys():
                if key in set(product_keys + ['values']):
                    continue
                label = cls._paper_text(key)
                if label and label not in column_map:
                    column_map[label] = {
                        'key': cls._paper_slugify(label, len(column_map) + 1),
                        'name': label,
                    }

        normalized['columns'] = list(column_map.values())
        for row in rows:
            row_values = {}
            for column in normalized['columns']:
                row_values[column['key']] = cls._paper_text(row.get(column['name']))
            normalized['rows'].append(
                {
                    'product_name': cls._paper_first_value(row, product_keys),
                    'values': row_values,
                }
            )
        return normalized

    @classmethod
    def _build_paper_properties_from_hierarchy(cls, hierarchy):
        columns = []
        column_map = {}
        rows = []

        for index, item in enumerate(hierarchy):
            if not isinstance(item, dict):
                continue
            row = {
                'product_name': cls._paper_first_value(
                    item,
                    ['product_name', 'intermediate_name', 'intermediate_id', 'material_name', '产物（中间体配比）', '产物'],
                ) or f'row_{index + 1}',
                'values': {},
            }
            properties = item.get('properties') if isinstance(item.get('properties'), list) else []
            for prop in properties:
                if not isinstance(prop, dict):
                    continue
                label = cls._paper_first_value(prop, ['property_name', '性能名称', 'property_id', '性能编号'])
                if not label:
                    continue
                if label not in column_map:
                    column_map[label] = {
                        'key': cls._paper_slugify(label, len(column_map) + 1),
                        'name': label,
                    }
                    columns.append(column_map[label])
                row['values'][column_map[label]['key']] = cls._paper_first_value(prop, ['property_value', '性能值', 'value'])
            rows.append(row)

        return {'columns': columns, 'rows': rows}

    @classmethod
    def _normalize_paper_payload(cls, payload):
        normalized = cls._empty_paper_document_payload()
        if not isinstance(payload, dict):
            return normalized

        if (
            isinstance(payload.get('basic_info'), dict)
            or isinstance(payload.get('properties'), dict)
            or isinstance(payload.get('materials'), list)
            or isinstance(payload.get('intermediates'), list)
            or 'preparation_process' in payload
            or '原材料' in payload
        ):
            basic = payload.get('basic_info') if isinstance(payload.get('basic_info'), dict) else payload
            normalized['basic_info'] = {
                'article_id': cls._paper_first_value(basic, ['article_id', '文献编号', '文献编号（Article ID）']),
                'article_name': cls._paper_first_value(basic, ['article_name', '文献名称', '文献名称（Article Name）']),
                'article_doi': cls._paper_first_value(basic, ['article_doi', 'doi', 'DOI', '文献DOI号']),
                'publish_year': cls._paper_first_value(basic, ['publish_year', 'year', '文献出版年份', '出版年份']),
            }
            normalized['materials'] = [
                cls._normalize_paper_material_row(item)
                for item in cls._paper_ensure_list(payload.get('materials') or payload.get('原材料'))
                if isinstance(item, dict)
            ]
            normalized['preparation_process'] = cls._paper_first_value(
                payload,
                ['preparation_process', '制备工艺', 'process_description'],
            )
            normalized['intermediates'] = [
                cls._normalize_paper_intermediate_row(item)
                for item in cls._paper_ensure_list(payload.get('intermediates') or payload.get('中间体'))
                if isinstance(item, dict)
            ]
            normalized['properties'] = cls._normalize_paper_properties(payload.get('properties') or payload.get('性能'))
            normalized['notes'] = cls._paper_first_value(payload, ['notes', '备注', 'remark', '说明'])
            return normalized

        hierarchy = payload.get('hierarchical_data')
        if not isinstance(hierarchy, list):
            hierarchy = payload.get('material_intermediates')
        if not isinstance(hierarchy, list):
            hierarchy = payload.get('四级数据连接')
        if not isinstance(hierarchy, list):
            hierarchy = payload.get('四级数据连接（4-level Data Linkage）')
        if not isinstance(hierarchy, list):
            hierarchy = []

        normalized_hierarchy = [
            cls._normalize_paper_hierarchy_item(item)
            for item in hierarchy
            if isinstance(item, dict)
        ]

        normalized['basic_info'] = {
            'article_id': cls._paper_first_value(payload, ['article_id', '文献编号', '文献编号（Article ID）']),
            'article_name': cls._paper_first_value(payload, ['article_name', '文献名称', '文献名称（Article Name）']),
            'article_doi': cls._paper_first_value(payload, ['article_doi', 'doi', 'DOI', '文献DOI号']),
            'publish_year': cls._paper_first_value(payload, ['publish_year', 'year', '文献出版年份', '出版年份']),
        }

        material_seen = set()
        materials = []
        intermediate_seen = set()
        intermediates = []
        for item in normalized_hierarchy:
            material_row = cls._normalize_paper_material_row(item)
            material_key = tuple(material_row.values())
            if any(material_row.values()) and material_key not in material_seen:
                material_seen.add(material_key)
                materials.append(material_row)

            intermediate_row = cls._normalize_paper_intermediate_row(item)
            intermediate_key = tuple(intermediate_row.values())
            if any(intermediate_row.values()) and intermediate_key not in intermediate_seen:
                intermediate_seen.add(intermediate_key)
                intermediates.append(intermediate_row)

        normalized['materials'] = materials
        normalized['intermediates'] = intermediates
        normalized['properties'] = cls._build_paper_properties_from_hierarchy(normalized_hierarchy)
        normalized['notes'] = cls._paper_first_value(payload, ['notes', '备注', 'performance_trend', '性能趋势'])
        return normalized

    @classmethod
    def _paper_payload_score(cls, payload):
        if not isinstance(payload, dict):
            return -1
        normalized = cls._normalize_paper_payload(payload)
        basic_info = normalized.get('basic_info') or {}
        materials = normalized.get('materials') or []
        intermediates = normalized.get('intermediates') or []
        properties = normalized.get('properties') or {}
        columns = properties.get('columns') or []
        rows = properties.get('rows') or []

        score_value = 0
        if cls._paper_text(basic_info.get('article_id')):
            score_value += 12
        if cls._paper_text(basic_info.get('article_name')):
            score_value += 8
        if cls._paper_text(basic_info.get('article_doi')):
            score_value += 12
        if cls._paper_text(basic_info.get('publish_year')):
            score_value += 6
        if cls._paper_text(normalized.get('preparation_process')):
            score_value += 10
        if cls._paper_text(normalized.get('notes')):
            score_value += 6

        score_value += len(materials) * 8
        score_value += len(intermediates) * 6
        score_value += len(columns) * 4
        score_value += len(rows) * 4
        score_value += sum(len(row.get('values') or {}) for row in rows)
        return score_value

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
        return int(row[0] or 1)

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
                    size = 0
                    with disk_path.open('wb') as dest:
                        for chunk in uploaded.chunks():
                            md5.update(chunk)
                            size += len(chunk)
                            dest.write(chunk)

                    file_obj = File.objects.create(
                        id=current_file_id,
                        filename=original_name,
                        stored_filename=stored_filename,
                        file_path=str(disk_path),
                        file_size=size,
                        file_type=suffix or Path(original_name).suffix.lower() or '',
                        document_type_code=document_type,
                        mime_type=content_type,
                        md5_hash=md5.hexdigest(),
                        uploader_id=self._default_uploader_id(),
                        upload_batch_id=batch_id,
                        ocr_status='pending',
                        review_status='unassigned',
                        description=description,
                        tags=tags,
                    )
                    file_obj.id = current_file_id
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
                    },
                }

            return {
                'status_code': 200 if not errors else 207,
                'body': {
                    'success': not errors,
                    'message': '上传成功' if not errors else '部分文件上传成功',
                    'data': {
                        'batch_id': batch_id,
                        'files': saved_files,
                        'total': len(saved_files),
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

    def _load_latest_ocr_payload(self, file_id: int):
        try:
            result = OCRResult.objects.filter(file_id=file_id).order_by('-updated_at', '-id').first()
            if not result or not isinstance(result.raw_result, dict):
                return None

            raw_result = result.raw_result
            structured = raw_result.get('structured_data')
            if isinstance(structured, dict):
                return structured

            if self._is_meaningful_document_payload('paper', raw_result):
                return raw_result
            if self._is_meaningful_document_payload('commission', raw_result):
                return raw_result
            return None
        except Exception:
            return None
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

    @classmethod
    def _select_richer_paper_payload(cls, cached_payload, legacy_payload):
        cached_score = cls._paper_payload_score(cached_payload)
        legacy_score = cls._paper_payload_score(legacy_payload)

        if legacy_score >= cached_score and legacy_score >= 0:
            return legacy_payload
        if cached_score >= 0:
            return cached_payload
        return legacy_payload if isinstance(legacy_payload, dict) else cached_payload

    def _load_paper_document_from_legacy_tables(self, file_id: int):
        file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
        default_payload = self._default_document_payload('paper', file_obj)

        try:
            with connection.cursor() as cursor:
                payload = self._query_paper_payload(cursor, file_id)
                if payload:
                    return payload
        except Exception:
            pass

        external_payload = self._load_paper_document_from_external_mysql(file_id)
        if external_payload:
            return external_payload

        return default_payload

    def _query_paper_payload(self, cursor, file_id: int):
        cursor.execute(
            """
            SELECT article_id, article_name, performance_trend
            FROM paper_articles
            WHERE file_id = %s
            ORDER BY id DESC
            LIMIT 1
            """,
            [file_id],
        )
        article_row = cursor.fetchone()

        if not article_row:
            return None

        article_id, article_name, performance_trend = article_row

        cursor.execute(
            """
            SELECT id, material_id, material_name, cas_number,
                   intermediate_id, intermediate_name, intermediate_composition
            FROM paper_material_intermediates
            WHERE article_id = %s
            ORDER BY sort_order ASC, id ASC
            """,
            [article_id],
        )
        materials_rows = cursor.fetchall()

        hierarchical_data = []
        for (
            material_pk,
            material_id,
            material_name,
            cas_number,
            intermediate_id,
            intermediate_name,
            intermediate_composition,
        ) in materials_rows:
            cursor.execute(
                """
                SELECT property_id, property_name, property_value
                FROM paper_properties
                WHERE material_intermediate_id = %s
                ORDER BY sort_order ASC, id ASC
                """,
                [material_pk],
            )
            properties_rows = cursor.fetchall()

            hierarchical_data.append(
                {
                    'material_id': material_id or '',
                    'material_name': material_name or '',
                    'cas_number': cas_number or '',
                    'intermediate_id': intermediate_id or '',
                    'intermediate_name': intermediate_name or '',
                    'intermediate_composition': intermediate_composition or '',
                    'properties': [
                        {
                            'property_id': pid or '',
                            'property_name': pname or '',
                            'property_value': pvalue or '',
                        }
                        for (pid, pname, pvalue) in properties_rows
                    ],
                }
            )

        return {
            'article_id': article_id or '',
            'article_name': article_name or '',
            'performance_trend': performance_trend or '',
            'hierarchical_data': hierarchical_data,
        }

    def _load_paper_document_from_external_mysql(self, file_id: int):
        cfg = self._build_legacy_mysql_config()
        if not cfg:
            return None

        connector = None
        connect_kwargs = None
        try:
            mysql_client = importlib.import_module('MySQLdb')
            connector = mysql_client
            connect_kwargs = {
                'host': cfg['host'],
                'port': int(cfg['port']),
                'user': cfg['user'],
                'passwd': cfg['password'],
                'db': cfg['database'],
                'charset': 'utf8mb4',
            }
        except Exception:
            try:
                pymysql_client = importlib.import_module('pymysql')
                connector = pymysql_client
                connect_kwargs = {
                    'host': cfg['host'],
                    'port': int(cfg['port']),
                    'user': cfg['user'],
                    'password': cfg['password'],
                    'database': cfg['database'],
                    'charset': 'utf8mb4',
                }
            except Exception:
                return None

        if not connector or not connect_kwargs:
            return None

        try:
            conn = connector.connect(**connect_kwargs)
            try:
                with conn.cursor() as cursor:
                    return self._query_paper_payload(cursor, file_id)
            finally:
                conn.close()
        except Exception:
            return None

    @staticmethod
    def _build_legacy_mysql_config():
        target_keys = {
            'LEGACY_OCR_MYSQL_HOST',
            'LEGACY_OCR_MYSQL_PORT',
            'LEGACY_OCR_MYSQL_USER',
            'LEGACY_OCR_MYSQL_PASSWORD',
            'LEGACY_OCR_MYSQL_DB',
            'MYSQL_HOST_OCR',
            'MYSQL_PORT_OCR',
            'MYSQL_USER_OCR',
            'MYSQL_PASSWORD_OCR',
            'MYSQL_DB_OCR',
            'MYSQL_HOST',
            'MYSQL_PORT',
            'MYSQL_USER',
            'MYSQL_PASSWORD',
            'MYSQL_DB',
            'MYSQL_DATABASE',
        }
        file_values = CheckerLocalService._read_env_values(
            [
                Path(__file__).resolve().parents[4] / 'backend' / '.env.dev',
                Path(__file__).resolve().parents[4] / 'backend' / '.env',
            ],
            target_keys,
        )

        def pick_env_first(*names):
            for name in names:
                raw = os.environ.get(name)
                if raw is None or str(raw).strip() == '':
                    raw = file_values.get(name)
                if raw is not None and str(raw).strip() != '':
                    return str(raw).strip().strip('"').strip("'")
            return ''

        def pick_file_first(*names):
            for name in names:
                raw = file_values.get(name)
                if raw is None or str(raw).strip() == '':
                    raw = os.environ.get(name)
                if raw is not None and str(raw).strip() != '':
                    return str(raw).strip().strip('"').strip("'")
            return ''

        host = pick_env_first('LEGACY_OCR_MYSQL_HOST') or pick_file_first('MYSQL_HOST_OCR', 'MYSQL_HOST')
        port = pick_env_first('LEGACY_OCR_MYSQL_PORT') or pick_file_first('MYSQL_PORT_OCR', 'MYSQL_PORT') or '3306'
        user = pick_env_first('LEGACY_OCR_MYSQL_USER') or pick_file_first('MYSQL_USER_OCR', 'MYSQL_USER')
        password = pick_env_first('LEGACY_OCR_MYSQL_PASSWORD') or pick_file_first('MYSQL_PASSWORD_OCR', 'MYSQL_PASSWORD')
        database = pick_env_first('LEGACY_OCR_MYSQL_DB') or pick_file_first('MYSQL_DB_OCR', 'MYSQL_DB', 'MYSQL_DATABASE')

        if not all([host, user, password, database]):
            return None

        return {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database': database,
        }

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

    @staticmethod
    def _build_minio_config():
        target_keys = {
            'MINIO_ENDPOINT',
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'MINIO_BUCKET_NAME',
            'MINIO_SECURE',
        }
        file_values = CheckerLocalService._read_env_values(
            CheckerLocalService._candidate_env_files(),
            target_keys,
        )

        def pick(name: str, default: str):
            raw = os.environ.get(name)
            if raw is None or str(raw).strip() == '':
                raw = file_values.get(name)
            if raw is None or str(raw).strip() == '':
                raw = default
            return str(raw).strip().strip('"').strip("'")

        endpoint = pick('MINIO_ENDPOINT', 'localhost:9000')
        access_key = pick('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = pick('MINIO_SECRET_KEY', 'minioadmin')
        bucket_name = pick('MINIO_BUCKET_NAME', 'ocr-files')
        secure = pick('MINIO_SECURE', 'false').lower() == 'true'
        return {
            'endpoint': endpoint,
            'access_key': access_key,
            'secret_key': secret_key,
            'bucket_name': bucket_name,
            'secure': secure,
        }

    @staticmethod
    def _read_minio_env_file_values():
        return CheckerLocalService._read_env_values(
            CheckerLocalService._candidate_env_files(),
            {
                'MINIO_ENDPOINT',
                'MINIO_ACCESS_KEY',
                'MINIO_SECRET_KEY',
                'MINIO_BUCKET_NAME',
                'MINIO_SECURE',
            },
        )

    @staticmethod
    def _candidate_env_files():
        workspace_root = Path(__file__).resolve().parents[4]
        return [
            workspace_root / 'backend' / '.env.dev',
            workspace_root / 'backend' / '.env',
        ]

    @staticmethod
    def _read_env_values(candidate_env_files, target_keys):
        values = {}

        for env_path in candidate_env_files:
            if not env_path.exists():
                continue

            try:
                for line in env_path.read_text(encoding='utf-8').splitlines():
                    text = line.strip()
                    if not text or text.startswith('#') or '=' not in text:
                        continue
                    key, raw_value = text.split('=', 1)
                    key = key.strip()
                    if key not in target_keys:
                        continue
                    value = raw_value.strip().strip('"').strip("'")
                    if value and key not in values:
                        values[key] = value
            except Exception:
                continue

        return values

    @staticmethod
    def _resolve_bucket_and_object(file_obj: File, default_bucket: str):
        object_name = (file_obj.file_path or '').lstrip('/')
        bucket_name = default_bucket

        # 兼容 file_path 存成 bucket/object 的场景。
        if object_name and '/' in object_name:
            first, rest = object_name.split('/', 1)
            if first and first in {'ocr-files', 'commissions', 'checker', 'files'}:
                if first != 'files':
                    bucket_name = first
                    object_name = rest

        return bucket_name, object_name

    def _try_download_from_minio(self, file_obj: File):
        try:
            import importlib
            Minio = importlib.import_module('minio').Minio  # 延迟导入，避免缺包时影响其它功能
        except Exception as exc:
            self._minio_probe_cache = {'ok': False, 'error': f'minio包不可用: {exc}'}
            return None

        cfg = self._build_minio_config()

        try:
            client = Minio(
                cfg['endpoint'],
                access_key=cfg['access_key'],
                secret_key=cfg['secret_key'],
                secure=cfg['secure'],
            )

            bucket_name, object_name = self._resolve_bucket_and_object(file_obj, cfg['bucket_name'])
            if not object_name:
                self._minio_probe_cache = {'ok': False, 'error': 'file_path为空，无法从MinIO读取'}
                return None

            response = client.get_object(bucket_name, object_name)
            try:
                data = response.read()
            finally:
                response.close()
                response.release_conn()

            self._minio_probe_cache = {'ok': True, 'error': None}
            return data
        except Exception as exc:
            self._minio_probe_cache = {'ok': False, 'error': str(exc)}
            return None

    def _probe_minio_object(self, file_obj: File):
        try:
            import importlib
            Minio = importlib.import_module('minio').Minio
        except Exception as exc:
            return {
                'available': False,
                'error': f'minio包不可用: {exc}',
            }

        cfg = self._build_minio_config()
        bucket_name, object_name = self._resolve_bucket_and_object(file_obj, cfg['bucket_name'])

        if not object_name:
            return {
                'available': False,
                'bucket': bucket_name,
                'object': object_name,
                'error': '对象名为空',
            }

        try:
            client = Minio(
                cfg['endpoint'],
                access_key=cfg['access_key'],
                secret_key=cfg['secret_key'],
                secure=cfg['secure'],
            )
            stat = client.stat_object(bucket_name, object_name)
            return {
                'available': True,
                'endpoint': cfg['endpoint'],
                'bucket': bucket_name,
                'object': object_name,
                'size': getattr(stat, 'size', None),
            }
        except Exception as exc:
            return {
                'available': False,
                'endpoint': cfg['endpoint'],
                'bucket': bucket_name,
                'object': object_name,
                'error': str(exc),
            }

    def _start_recognize(self, file_id: int):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {'status_code': 404, 'body': {'success': False, 'message': '文件不存在'}}

            task_id = f'local-{uuid.uuid4().hex[:12]}'
            document_type = self._normalize_document_type(file_obj)
            self._tasks[task_id] = {
                'status': 'processing',
                'result': {
                    'structured_data': self._default_document_payload(document_type, file_obj),
                    'document_type': document_type,
                },
            }

            file_obj.ocr_status = 'processing'
            file_obj.ocr_started_at = timezone.now()
            file_obj.save(update_fields=['ocr_status', 'ocr_started_at', 'updated_at'])

            thread = threading.Thread(
                target=self._run_recognize_task,
                args=(task_id, file_id),
                daemon=True,
            )
            thread.start()

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': 'OCR识别任务已提交',
                    'data': {'task_id': task_id},
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'启动识别失败: {exc}'},
            }

    def _run_recognize_task(self, task_id: str, file_id: int):
        close_old_connections()
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                raise ValueError('文件不存在')

            document_type = self._normalize_document_type(file_obj)
            fallback_note = None
            try:
                raw_result = self._call_upstream_ocr(file_obj, document_type)
                structured_data = self._parse_upstream_ocr_result(raw_result, document_type, file_obj)
            except Exception as upstream_exc:
                # paper 场景优先做本地降级，避免上游临时不可用时整单失败。
                if document_type == 'paper':
                    structured_data = self._build_paper_fallback_payload(file_id, file_obj)
                    if self._is_meaningful_document_payload(document_type, structured_data):
                        raw_result = {
                            'status': 'fallback',
                            'message': str(upstream_exc),
                            'source': 'local-cache-or-legacy',
                        }
                        fallback_note = f'论文OCR上游不可达，已使用本地数据降级填充：{upstream_exc}'
                    else:
                        raise upstream_exc
                else:
                    raise upstream_exc

            if not self._is_meaningful_document_payload(document_type, structured_data):
                raise ValueError('OCR服务未返回可用结构化字段')

            self._document_data_cache[file_id] = structured_data
            self._store_ocr_payload(file_obj, structured_data, raw_result)

            file_obj.ocr_status = 'completed'
            file_obj.ocr_completed_at = timezone.now()
            file_obj.ocr_error_message = None
            file_obj.save(update_fields=['ocr_status', 'ocr_completed_at', 'ocr_error_message', 'updated_at'])

            self._tasks[task_id] = {
                'status': 'completed',
                'result': {
                    'structured_data': structured_data,
                    'document_type': document_type,
                    'warning': fallback_note,
                },
            }
        except Exception as exc:
            try:
                File.objects.filter(id=file_id).update(
                    ocr_status='failed',
                    ocr_error_message=str(exc),
                    updated_at=timezone.now(),
                )
            except Exception:
                pass

            self._tasks[task_id] = {
                'status': 'failed',
                'error_message': str(exc),
                'result': {},
            }
        finally:
            close_old_connections()

    def _build_paper_fallback_payload(self, file_id: int, file_obj: File):
        cached = self._document_data_cache.get(file_id)
        persisted = self._load_latest_ocr_payload(file_id)
        legacy = self._load_paper_document_from_legacy_tables(file_id)

        data = self._select_richer_paper_payload(
            cached if isinstance(cached, dict) else None,
            persisted if isinstance(persisted, dict) else None,
        )
        data = self._select_richer_paper_payload(data, legacy if isinstance(legacy, dict) else None)
        data = self._normalize_paper_payload(data)

        if not self._is_meaningful_document_payload('paper', data):
            data = self._default_document_payload('paper', file_obj)
        return data

    def _read_file_bytes(self, file_obj: File):
        file_path = Path(file_obj.file_path or '')
        if file_path.exists() and file_path.is_file():
            return file_path.read_bytes()

        minio_bytes = self._try_download_from_minio(file_obj)
        if minio_bytes is not None:
            return minio_bytes

        raise FileNotFoundError('源文件不可读，无法提交OCR识别')
    @staticmethod
    def _paper_ocr_additional_inputs(file_obj: File):
        file_name = (getattr(file_obj, 'filename', '') or '').strip()
        return {
            'template_type': 'paper_material_v2',
            'filename_hint': file_name,
            'output_requirements': (
                '请严格输出 paper_material_v2 JSON。必须包含 basic_info、materials、preparation_process、'
                'intermediates、properties、notes 六部分；缺失字段返回空字符串、空数组或空对象。'
            ),
            'output_schema': {
                'template_type': 'paper_material_v2',
                'basic_info': {
                    'article_id': '',
                    'article_name': '',
                    'article_doi': '',
                    'publish_year': '',
                },
                'materials': [
                    {
                        'material_id': '',
                        'material_name': '',
                        'material_characteristic': '',
                        'cas_number': '',
                    }
                ],
                'preparation_process': '',
                'intermediates': [
                    {
                        'intermediate_id': '',
                        'formula': '',
                    }
                ],
                'properties': {
                    'columns': [{'key': 'metric_1', 'name': ''}],
                    'rows': [{'product_name': '', 'values': {'metric_1': ''}}],
                },
                'notes': '',
            },
        }

    @staticmethod
    def _parse_extra_dict(extra):
        if not extra:
            return {}
        if isinstance(extra, dict):
            return extra
        if not isinstance(extra, str):
            return {}
        try:
            parsed = json.loads(extra)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    @classmethod
    def _deep_merge_dict(cls, base, override):
        if not isinstance(base, dict):
            base = {}
        if not isinstance(override, dict):
            return dict(base)

        merged = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(merged.get(key), dict):
                merged[key] = cls._deep_merge_dict(merged.get(key), value)
            else:
                merged[key] = value
        return merged

    @classmethod
    def _build_paper_additional_inputs(cls, file_obj: File):
        defaults = cls._paper_ocr_additional_inputs(file_obj)
        # 兼容“extra JSON”能力：可通过环境变量覆盖默认模板。
        # 示例：OCR_PAPER_EXTRA='{"output_requirements":"..."}'
        env_extra = cls._parse_extra_dict(os.environ.get('OCR_PAPER_EXTRA'))
        return cls._deep_merge_dict(defaults, env_extra)

    @staticmethod
    def _paper_allowed_extensions():
        raw = (os.environ.get('OCR_PAPER_ALLOWED_EXTENSIONS') or 'pdf').strip()
        values = [item.strip().lower().lstrip('.') for item in raw.split(',') if item.strip()]
        return set(values or ['pdf'])

    @staticmethod
    def _paper_max_file_size_mb():
        raw = (os.environ.get('OCR_PAPER_MAX_MB') or '').strip()
        try:
            value = float(raw) if raw else 50.0
        except Exception:
            value = 50.0
        return max(value, 1.0)

    def _validate_upstream_input_file(self, file_obj: File, content: bytes, document_type: str):
        if document_type != 'paper':
            return

        filename = (file_obj.filename or file_obj.stored_filename or '').strip()
        extension = Path(filename).suffix.lower().lstrip('.')
        allowed_extensions = self._paper_allowed_extensions()
        if extension not in allowed_extensions:
            allowed_text = ', '.join(sorted(allowed_extensions))
            raise ValueError(f'不支持的论文文件类型: {extension or "未知"}，允许类型: {allowed_text}')

        max_mb = self._paper_max_file_size_mb()
        size_mb = len(content or b'') / (1024 * 1024)
        if size_mb > max_mb:
            raise ValueError(f'论文文件大小超过限制：最大允许 {max_mb:.0f}MB，当前 {size_mb:.2f}MB')

    @staticmethod
    def _normalize_dify_error_message(message):
        text = str(message or '').strip()
        if not text:
            return '论文分析失败'
        lowered = text.lower()
        if 'insufficient balance' in lowered or 'status code 402' in lowered:
            return '论文OCR上游模型余额不足，请充值或更换可用模型配置'
        return text

    @classmethod
    def _extract_dify_error(cls, result):
        if not isinstance(result, dict):
            return None

        if str(result.get('status', '')).lower() in {'error', 'failed'}:
            return cls._normalize_dify_error_message(
                result.get('message') or result.get('error') or '论文分析失败'
            )

        nested = result.get('data')
        if isinstance(nested, dict) and str(nested.get('status', '')).lower() in {'failed', 'error', 'stopped'}:
            return cls._normalize_dify_error_message(
                nested.get('error') or nested.get('message') or '论文分析失败'
            )

        return None

    @staticmethod
    def _join_url(base_url: str, endpoint: str):
        return f"{(base_url or '').rstrip('/')}/{(endpoint or '').lstrip('/')}"

    def _call_paper_dify(self, file_obj: File, content: bytes, mime_type: str, additional_inputs: dict):
        cfg = get_paper_dify_config()
        base_url = cfg.get('base_url') or ''
        api_key = cfg.get('api_key') or ''
        if not base_url:
            raise ValueError('未配置 OCR_PAPER_DIFY_BASE_URL（或 DIFY_API_URL），无法直连 Dify 论文识别')
        if not api_key:
            raise ValueError('未配置 OCR_PAPER_DIFY_API_KEY（或 DIFY_API_KEY），无法直连 Dify 论文识别')

        filename = file_obj.filename or file_obj.stored_filename or f'file-{file_obj.pk}.pdf'
        user = cfg.get('default_user') or 'ai-rag-django'
        timeout = max(float(cfg.get('timeout', get_timeout())), 30.0)

        upload_url = self._join_url(base_url, cfg.get('upload_endpoint', '/files/upload'))
        upload_headers = {'Authorization': f'Bearer {api_key}'}

        try:
            upload_resp = requests.post(
                upload_url,
                headers=upload_headers,
                files={'file': (filename, content, mime_type or 'application/pdf')},
                data={'user': user},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise ValueError(f'Dify文件上传失败，无法连接 {upload_url}: {exc}') from exc

        try:
            upload_payload = upload_resp.json()
        except ValueError as exc:
            raise ValueError(f'Dify文件上传返回非JSON: HTTP {upload_resp.status_code}') from exc

        if not (200 <= upload_resp.status_code < 300):
            message = (
                upload_payload.get('message')
                or upload_payload.get('error')
                or f'Dify文件上传失败: HTTP {upload_resp.status_code}'
            )
            raise ValueError(message)

        upload_file_id = (
            upload_payload.get('id')
            or (upload_payload.get('data') or {}).get('id')
            or (upload_payload.get('data') or {}).get('file_id')
        )
        if not upload_file_id:
            raise ValueError('Dify文件上传成功但未返回文件ID')

        workflow_url = self._join_url(base_url, cfg.get('workflow_endpoint', '/workflows/run'))
        workflow_headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }
        workflow_body = {
            'inputs': {
                'file': {
                    'transfer_method': cfg.get('transfer_method', 'local_file'),
                    'upload_file_id': upload_file_id,
                    'type': cfg.get('file_type', 'document'),
                },
                **(additional_inputs or {}),
            },
            'response_mode': cfg.get('response_mode', 'blocking'),
            'user': user,
        }

        try:
            workflow_resp = requests.post(
                workflow_url,
                headers=workflow_headers,
                json=workflow_body,
                timeout=max(timeout, get_timeout()),
            )
        except requests.RequestException as exc:
            raise ValueError(f'Dify工作流调用失败，无法连接 {workflow_url}: {exc}') from exc

        try:
            workflow_payload = workflow_resp.json()
        except ValueError as exc:
            raise ValueError(f'Dify工作流返回非JSON: HTTP {workflow_resp.status_code}') from exc

        workflow_error = self._extract_dify_error(workflow_payload)
        if workflow_error:
            raise ValueError(workflow_error)

        if not (200 <= workflow_resp.status_code < 300):
            message = (
                workflow_payload.get('message')
                or workflow_payload.get('error')
                or f'Dify工作流调用失败: HTTP {workflow_resp.status_code}'
            )
            raise ValueError(message)

        return workflow_payload

    def _call_upstream_ocr(self, file_obj: File, document_type: str):
        service = 'paper' if document_type == 'paper' else 'commission'
        base_url = get_service_base_urls().get(service)
        if document_type != 'paper' and not base_url:
            raise ValueError(f'未配置{service} OCR服务地址')

        content = self._read_file_bytes(file_obj)
        self._validate_upstream_input_file(file_obj, content, document_type)
        filename = file_obj.filename or file_obj.stored_filename or f'file-{file_obj.pk}.pdf'
        mime_type = file_obj.mime_type or 'application/pdf'

        if document_type == 'paper':
            paper_inputs = self._build_paper_additional_inputs(file_obj)
            if get_paper_dify_config().get('enabled', True):
                return self._call_paper_dify(file_obj, content, mime_type, paper_inputs)

        url = f'{base_url}/api/analyze'
        request_data = {'user': 'ai-rag-django', 'response_mode': 'blocking'}
        if document_type == 'paper':
            request_data['extra'] = json.dumps(
                paper_inputs,
                ensure_ascii=False,
            )

        try:
            response = requests.post(
                url,
                files={'file': (filename, content, mime_type)},
                data=request_data,
                timeout=max(get_timeout(), 300),
            )
        except requests.RequestException as exc:
            raise ValueError(
                f'无法连接{service} OCR服务（{base_url}），请确认对应服务已启动，或在 backend 配置 OCR_{service.upper()}_BASE_URL。原始错误: {exc}'
            ) from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise ValueError(f'OCR服务返回非JSON响应: HTTP {response.status_code}') from exc

        upstream_error = self._extract_dify_error(payload)
        if upstream_error:
            raise ValueError(upstream_error)

        if not (200 <= response.status_code < 300):
            raise ValueError(payload.get('message') or f'OCR服务调用失败: HTTP {response.status_code}')
        if payload.get('success') is False:
            raise ValueError(payload.get('message') or 'OCR服务处理失败')

        return payload

    def _parse_upstream_ocr_result(self, raw_result, document_type: str, file_obj: File):
        if document_type == 'paper':
            return self._parse_paper_ocr_result(raw_result, file_obj)
        return self._parse_commission_ocr_result(raw_result)

    def _store_ocr_payload(self, file_obj: File, structured_data: dict, raw_result=None):
        try:
            OCRResult.objects.update_or_create(
                file_id=file_obj.pk,
                page_number=1,
                defaults={
                    'raw_text': '',
                    'raw_result': {
                        'structured_data': structured_data,
                        'upstream_raw_result': raw_result or {},
                    },
                    'form_fields': structured_data,
                    'ocr_engine': 'upstream-ocr',
                    'review_status': 'pending',
                },
            )
        except Exception:
            pass

    @staticmethod
    def _extract_scalar_value(value):
        if isinstance(value, dict):
            if 'value' in value:
                return CheckerLocalService._extract_scalar_value(value.get('value'))
            if 'text' in value:
                return CheckerLocalService._extract_scalar_value(value.get('text'))
            if 'content' in value:
                return CheckerLocalService._extract_scalar_value(value.get('content'))
            return ''
        if isinstance(value, list):
            for item in value:
                scalar = CheckerLocalService._extract_scalar_value(item)
                if scalar:
                    return scalar
            return ''
        if value is None:
            return ''
        return str(value).strip()

    @staticmethod
    def _looks_like_table_field(field_name: str, field_data):
        field_type = field_data.get('type', '') if isinstance(field_data, dict) else ''
        return (
            field_type == 'multi_row_table'
            or (isinstance(field_data, dict) and any(key in field_data for key in ('data', 'rows', 'tests')))
            or ('表' in field_name and field_name not in {'表格编号'})
        )

    def _parse_commission_ocr_result(self, raw_result):
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
            '样品实物信息是否一致': 'sample_info_consistent',
        }

        structured = {'basic_info': {}, 'test_items': [], 'special_tests': []}
        data = raw_result.get('data', raw_result) if isinstance(raw_result, dict) else {}

        if isinstance(data.get('basic_info'), dict):
            structured['basic_info'].update(data.get('basic_info') or {})
        if isinstance(data.get('test_items'), list):
            structured['test_items'] = data.get('test_items') or []
        if isinstance(data.get('special_tests'), list):
            structured['special_tests'] = data.get('special_tests') or []

        field_results = data.get('field_extraction_results') if isinstance(data, dict) else None
        if isinstance(field_results, list):
            collected_fields = {}
            for page_data in field_results:
                extracted_fields = page_data.get('extracted_fields') if isinstance(page_data, dict) else None
                if not isinstance(extracted_fields, dict):
                    continue

                for field_name, field_data in extracted_fields.items():
                    if self._looks_like_table_field(field_name, field_data):
                        self._parse_commission_table(field_name, field_data, structured)
                        continue

                    mapped_name = field_name_mapping.get(field_name, field_name)
                    value = self._extract_scalar_value(field_data)
                    if value and mapped_name not in collected_fields:
                        collected_fields[mapped_name] = value

            structured['basic_info'].update(collected_fields)

        combined = data.get('combined_results') if isinstance(data, dict) else None
        if isinstance(combined, dict) and not structured['basic_info']:
            combined_field_data = combined.get('combined_field_data')
            if isinstance(combined_field_data, dict):
                extracted = combined_field_data.get('all_extracted_fields')
                if isinstance(extracted, dict):
                    for key, value in extracted.items():
                        mapped_name = field_name_mapping.get(key, key)
                        scalar = self._extract_scalar_value(value)
                        if scalar:
                            structured['basic_info'][mapped_name] = scalar

        return structured

    @staticmethod
    def _parse_commission_table(field_name: str, field_data, structured: dict):
        if not isinstance(field_data, dict):
            return

        test_item_mapping = {
            '测试项目': 'test_item',
            '测试设备': 'test_equipment',
            '测试标准': 'test_standard',
            '测试条件': 'test_condition',
            '产品标准': 'product_standard',
            '单位': 'unit',
            '测试结果': 'test_result',
            '测试员': 'tester',
            '备注': 'remark',
        }
        special_test_mapping = {
            '测试类型': 'test_type',
            '元素名称': 'element_name',
            '标准值': 'standard_value',
            '标准': 'standard_value',
            '实测值': 'measured_value',
            '实测': 'measured_value',
            '备注': 'remark',
        }

        if isinstance(field_data.get('tests'), list):
            for group in field_data.get('tests') or []:
                test_name = group.get('test_name', '') if isinstance(group, dict) else ''
                rows = group.get('data', []) if isinstance(group, dict) else []
                for row_index, row in enumerate(rows if isinstance(rows, list) else []):
                    if not isinstance(row, dict):
                        continue
                    mapped = {'test_type': test_name, 'sort_order': row_index}
                    for key, value in row.items():
                        mapped[special_test_mapping.get(key, key)] = value
                    structured['special_tests'].append(mapped)
            return

        rows = field_data.get('data') or field_data.get('rows') or []
        if not isinstance(rows, list):
            return

        is_special = any(token in field_name.lower() for token in ('特殊', 'rohs', 'special')) or '测试结果表' in field_name
        mapping = special_test_mapping if is_special else test_item_mapping
        target = 'special_tests' if is_special else 'test_items'
        for row_index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            mapped = {'sort_order': row_index}
            for key, value in row.items():
                mapped[mapping.get(key, key)] = value
            structured[target].append(mapped)

    @staticmethod
    def _jsonish(value):
        if not isinstance(value, str):
            return value
        text = value.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?', '', text).strip()
            text = re.sub(r'```$', '', text).strip()
        if not text or text[0] not in '[{':
            return value
        try:
            return json.loads(text)
        except Exception:
            return value

    def _parse_paper_ocr_result(self, raw_result, file_obj: File):
        best_payload = self._empty_paper_document_payload()
        best_score = self._paper_payload_score(best_payload)
        queue = [raw_result]
        visited = set()

        while queue:
            current = self._jsonish(queue.pop(0))

            if isinstance(current, (dict, list)):
                marker = id(current)
                if marker in visited:
                    continue
                visited.add(marker)

            if isinstance(current, list):
                queue.extend(current)
                continue
            if not isinstance(current, dict):
                continue

            candidates = [current]
            for key in ('文献', 'paper', 'data', 'outputs', 'result', 'payload', 'content'):
                nested = current.get(key)
                if isinstance(nested, dict):
                    candidates.append(nested)
                elif isinstance(nested, list):
                    queue.extend(nested)
                elif isinstance(nested, str):
                    queue.append(nested)

            for candidate in candidates:
                normalized = self._normalize_paper_payload(candidate)
                score = self._paper_payload_score(normalized)
                if score > best_score:
                    best_payload = normalized
                    best_score = score

            for value in current.values():
                if isinstance(value, (dict, list, str)):
                    queue.append(value)
        return self._normalize_paper_payload(best_payload)

    def _fill_paper_fields(self, paper_data: dict, structured: dict):
        normalized = self._normalize_paper_payload(paper_data)
        structured.clear()
        structured.update(normalized)

    @classmethod
    def _normalize_paper_hierarchy_item(cls, item: dict):
        materials = item.get('原材料（Materials）') or item.get('原材料') or item.get('materials') or item
        intermediates = item.get('中间体（Intermediates）') or item.get('中间体') or item.get('intermediates') or item
        if isinstance(materials, list):
            materials = materials[0] if materials else {}
        if isinstance(intermediates, list):
            intermediates = intermediates[0] if intermediates else {}
        if not isinstance(materials, dict):
            materials = {}
        if not isinstance(intermediates, dict):
            intermediates = {}

        properties = item.get('性能（Properties）') or item.get('性能') or item.get('properties') or []
        normalized_properties = []
        if isinstance(properties, list):
            for prop in properties:
                if not isinstance(prop, dict):
                    continue
                normalized_properties.append(
                    {
                        'property_id': cls._paper_first_value(prop, ['property_id', '性能编号', '性能编号（Property ID）']),
                        'property_name': cls._paper_first_value(prop, ['property_name', '性能名称', '性能名称（Property Name）']),
                        'property_value': cls._paper_first_value(prop, ['property_value', '性能值', '性能值（Property Value）', 'value']),
                    }
                )

        return {
            'material_id': cls._paper_first_value(materials, ['material_id', '材料编号', '原料编号', 'Material ID'])
            or cls._paper_first_value(item, ['material_id', '材料编号', '原料编号']),
            'material_name': cls._paper_first_value(materials, ['material_name', '原料名称', '材料名称', 'Material Name'])
            or cls._paper_first_value(item, ['material_name', '原料名称', '材料名称']),
            'material_characteristic': cls._paper_first_value(
                materials,
                ['material_characteristic', '原料特性', '材料特性', 'Material Characteristic', 'characteristic'],
            )
            or cls._paper_first_value(item, ['material_characteristic', '原料特性', '材料特性']),
            'cas_number': cls._paper_first_value(materials, ['cas_number', 'CAS', 'CAS号', 'CAS Number'])
            or cls._paper_first_value(item, ['cas_number', 'CAS', 'CAS号']),
            'intermediate_id': cls._paper_first_value(intermediates, ['intermediate_id', '中间体编号', 'Intermediate ID'])
            or cls._paper_first_value(item, ['intermediate_id', '中间体编号']),
            'intermediate_name': cls._paper_first_value(intermediates, ['intermediate_name', '中间体名称', 'Intermediate Name'])
            or cls._paper_first_value(item, ['intermediate_name', '中间体名称']),
            'intermediate_composition': cls._paper_first_value(
                item,
                ['intermediate_composition', '中间体组成', '中间体组成（Intermediate Compositions）'],
            ),
            'properties': normalized_properties,
        }

    def _get_task_status(self, task_id: str):
        task = self._tasks.get(task_id)
        if not task:
            return {
                'status_code': 404,
                'body': {'success': False, 'status': 'not_found', 'message': '任务不存在'},
            }

        return {
            'status_code': 200,
            'body': {
                'success': True,
                'status': task.get('status', 'completed'),
                'result': task.get('result', {}),
                'error_message': task.get('error_message'),
            },
        }

    def _save_ocr_result(self, request, file_id: int):
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {'status_code': 404, 'body': {'success': False, 'message': '文件不存在'}}

            payload = self._parse_json_body(request)
            ocr_result = payload.get('ocr_result', payload)
            if not isinstance(ocr_result, dict):
                ocr_result = {}
            document_type = self._normalize_document_type(file_obj)
            if document_type == 'paper':
                ocr_result = self._normalize_paper_payload(ocr_result)

            self._document_data_cache[file_id] = ocr_result
            self._store_ocr_payload(file_obj, ocr_result, {'source': 'manual-save'})

            file_obj.ocr_status = 'completed'
            file_obj.save(update_fields=['ocr_status', 'updated_at'])

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': 'OCR结果保存成功（Django本地checker）',
                    'document_type': document_type,
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'OCR结果保存失败: {exc}'},
            }
