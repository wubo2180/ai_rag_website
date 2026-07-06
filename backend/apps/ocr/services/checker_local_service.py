from pathlib import Path
import hashlib
import mimetypes
import os
import re
import uuid
import json
import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.utils import timezone

from ..models import File, OCRResult, UploadBatch
from .checker_ocr_mixin import CheckerOcrMixin

logger = logging.getLogger(__name__)

_PLACEHOLDER_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n4 0 obj<</Length 72>>stream\nBT /F1 18 Tf 72 720 Td (PDF preview placeholder - source file unavailable) Tj ET\nendstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n0000000363 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n433\n%%EOF\n"

# MinIO 配置
_MINIO_ENDPOINT = getattr(settings, 'MINIO_ENDPOINT', '172.20.46.18:19000')
_MINIO_ACCESS_KEY = getattr(settings, 'MINIO_ACCESS_KEY', 'minio')
_MINIO_SECRET_KEY = getattr(settings, 'MINIO_SECRET_KEY', 'rRRyKSJFSDxfRzeE')
_MINIO_SECURE = getattr(settings, 'MINIO_SECURE', False)

# 文档类型与 MinIO 桶的映射
_DOC_TYPE_BUCKET_MAP = {
    'paper': 'ocr-papers',
    'commission': 'ocr-test-requests',
}

# 每个 batch 的最大文件数
_MAX_COUNT_PER_BATCH = 2000

# MinIO 客户端（延迟初始化）
_minio_client = None


def _get_minio_client():
    global _minio_client
    if _minio_client is None:
        try:
            from minio import Minio
            _minio_client = Minio(
                _MINIO_ENDPOINT,
                access_key=_MINIO_ACCESS_KEY,
                secret_key=_MINIO_SECRET_KEY,
                secure=_MINIO_SECURE,
            )
        except Exception as exc:
            logger.warning(f'MinIO 客户端初始化失败: {exc}')
            _minio_client = False  # 标记为不可用
    return _minio_client if _minio_client else None


def _ensure_bucket_exists(client, bucket_name: str):
    if client and not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)
        logger.info(f'创建 MinIO 桶: {bucket_name}')


def _get_or_create_upload_batch(document_type_code: str):
    """获取或创建 UploadBatch，返回 (batch, is_new)"""
    batch = UploadBatch.objects.filter(
        document_type_code=document_type_code,
        status='open',
    ).order_by('id').first()

    if batch and batch.file_count < batch.max_count:
        return batch, False

    # 创建新 batch
    last_batch = UploadBatch.objects.filter(
        document_type_code=document_type_code,
    ).order_by('-id').first()

    if last_batch:
        last_name = last_batch.batch_name
        last_num = int(last_name.split('_')[1])
        new_num = last_num + 1
    else:
        new_num = 1

    prefix = 'testRequest' if document_type_code == 'commission' else document_type_code
    batch_name = f'{prefix}_{new_num:06d}'

    batch = UploadBatch.objects.create(
        batch_name=batch_name,
        document_type_code=document_type_code,
        file_count=0,
        max_count=_MAX_COUNT_PER_BATCH,
        status='open',
    )
    logger.info(f'[新建 Batch] id={batch.id}, name={batch_name}, type={document_type_code}')
    return batch, True


def _upload_to_minio(client, bucket: str, object_key: str, file_path: str, content_type: str = 'application/pdf'):
    """上传文件到 MinIO，返回 (success, message)"""
    if not client:
        return False, 'MinIO 客户端不可用'

    try:
        _ensure_bucket_exists(client, bucket)
        file_size = os.path.getsize(file_path)
        with open(file_path, 'rb') as f:
            client.put_object(
                bucket_name=bucket,
                object_name=object_key,
                data=f,
                length=file_size,
                content_type=content_type,
            )
        return True, f'上传成功 ({file_size / 1024 / 1024:.2f} MB)'
    except Exception as e:
        return False, f'上传失败: {e}'


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

        detail_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/?', normalized)
        if request.method == 'DELETE' and detail_match:
            file_id = int(detail_match.group('file_id'))
            return self._delete_file(file_id)

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

        mark_unreviewed_match = re.fullmatch(r'(api/)?files/(?P<file_id>\d+)/mark-unreviewed', normalized)
        if mark_unreviewed_match and request.method == 'POST':
            file_id = int(mark_unreviewed_match.group('file_id'))
            return self._mark_as_unreviewed(file_id)

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

                    # 历史文件去重：忽略软删除状态，只要 sha256 相同就认为是重复文件
                    # 这样可以避免软删除后重新上传相同文件导致重复记录
                    existing = File.objects.filter(
                        sha256_hash=sha256_hex,
                    ).only('id', 'filename', 'created_at', 'is_deleted').order_by('-created_at').first()

                    if existing:
                        if disk_path.exists():
                            disk_path.unlink(missing_ok=True)
                        
                        # 如果找到的是已删除的记录，可以选择恢复它或者创建新记录
                        # 这里选择标记为重复，让用户知道文件已存在（即使是已删除的）
                        duplicates.append({
                            'filename': original_name,
                            'md5_hash': md5_hex,
                            'sha256_hash': sha256_hex,
                            'file_size': size,
                            'reason': 'duplicate_in_history',
                            'existing_file_id': existing.pk,
                            'existing_filename': existing.filename,
                            'existing_created_at': self._serialize_datetime(existing.created_at),
                            'is_deleted': existing.is_deleted,  # 标记是否已删除
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

                    # ===== MinIO 双存储 =====
                    try:
                        minio_client = _get_minio_client()
                        if minio_client:
                            bucket = _DOC_TYPE_BUCKET_MAP.get(document_type, 'ocr-test-requests')
                            upload_batch, _ = _get_or_create_upload_batch(document_type)
                            object_key = f'{upload_batch.batch_name}/{stored_filename}'

                            ok, msg = _upload_to_minio(
                                minio_client, bucket, object_key, str(disk_path), content_type,
                            )
                            if ok:
                                # 使用 current_file_id 而不是 file_obj.id（确保 ID 正确）
                                File.objects.filter(id=current_file_id).update(
                                    minio_bucket=bucket,
                                    minio_object_key=object_key,
                                    batch_id=upload_batch.id,
                                )
                                # 同步内存中的对象
                                file_obj.minio_bucket = bucket
                                file_obj.minio_object_key = object_key
                                file_obj.batch_id = upload_batch.id

                                upload_batch.file_count += 1
                                if upload_batch.file_count >= upload_batch.max_count:
                                    upload_batch.status = 'full'
                                upload_batch.save(update_fields=['file_count', 'status', 'updated_at'])

                                logger.info(
                                    f'[MinIO 上传成功] file_id={current_file_id}, bucket={bucket}, '
                                    f'key={object_key}, batch={upload_batch.batch_name} '
                                    f'({upload_batch.file_count}/{upload_batch.max_count})'
                                )
                            else:
                                logger.warning(f'[MinIO 上传失败] file_id={current_file_id}: {msg}')
                        else:
                            logger.warning('[MinIO 上传跳过] MinIO 客户端不可用')
                    except Exception as minio_exc:
                        logger.error(f'[MinIO 上传异常] file_id={current_file_id}: {minio_exc}', exc_info=True)
                    # ===== MinIO 双存储结束 =====

                    seen_hash_keys[dedupe_key] = current_file_id
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

            # 构建更清晰的消息
            dup_count = len(duplicates)
            saved_count = len(saved_files)

            if dup_count > 0 and saved_count == 0 and not errors:
                message = f'文件均已存在，未新增（{dup_count} 个重复文件已跳过）'
            elif dup_count > 0 and saved_count > 0 and not errors:
                message = f'部分文件上传成功（{saved_count} 个新文件，{dup_count} 个重复文件已跳过）'
            elif errors:
                message = f'部分文件上传成功（{saved_count} 个新文件，{len(errors)} 个失败）'
            else:
                message = f'上传成功，共入库 {saved_count} 个文件'

            return {
                'status_code': 200 if not errors else 207,
                'body': {
                    'success': not errors,
                    'message': message,
                    'data': {
                        'batch_id': batch_id,
                        'files': saved_files,
                        'total': saved_count,
                        'duplicates': duplicates,
                        'duplicate_count': dup_count,
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

    _SORT_FIELD_MAP = {
        'created_at': 'created_at',
        'filename': 'filename',
    }

    def _list_files(self, request):
        try:
            page = max(int(request.GET.get('page', 1)), 1)
            per_page = min(max(int(request.GET.get('per_page', 20)), 1), 100)
            status_filter = request.GET.get('status')
            review_status_filter = request.GET.get('review_status')
            document_type_filter = request.GET.get('document_type')
            keyword = (request.GET.get('keyword') or request.GET.get('filename') or '').strip()
            sort_by = (request.GET.get('sort_by') or 'created_at').strip().lower()
            sort_order = (request.GET.get('sort_order') or 'desc').strip().lower()

            sort_field = self._SORT_FIELD_MAP.get(sort_by, 'created_at')
            order_prefix = '' if sort_order == 'asc' else '-'
            order_field = f'{order_prefix}{sort_field}'

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
            ).order_by(order_field, '-id')

            if status_filter:
                queryset = queryset.filter(ocr_status=status_filter)
            if review_status_filter:
                queryset = queryset.filter(review_status=review_status_filter)
            if document_type_filter:
                queryset = queryset.filter(document_type_code=document_type_filter)
            if keyword:
                queryset = queryset.filter(filename__icontains=keyword)

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
                        'keyword': keyword,
                        'sort_by': sort_field,
                        'sort_order': sort_order,
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

    def _delete_file(self, file_id: int):
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

            # 保存删除前的信息
            file_path = (file_obj.file_path or '').strip()
            minio_bucket = file_obj.minio_bucket
            minio_object_key = file_obj.minio_object_key
            batch_id = file_obj.batch_id

            # 硬删除数据库记录
            file_obj.delete()
            logger.info(f'[数据库删除] file_id={file_id} 已硬删除')

            # 删除本地磁盘文件
            if file_path:
                try:
                    Path(file_path).unlink(missing_ok=True)
                    logger.info(f'[本地删除] file_id={file_id}, path={file_path}')
                except Exception as exc:
                    logger.warning(f'[本地删除失败] file_id={file_id}: {exc}')

            # 删除 MinIO 中的文件
            if minio_bucket and minio_object_key:
                try:
                    minio_client = _get_minio_client()
                    if minio_client:
                        minio_client.remove_object(minio_bucket, minio_object_key)
                        logger.info(
                            f'[MinIO 删除成功] file_id={file_id}, '
                            f'bucket={minio_bucket}, key={minio_object_key}'
                        )
                    else:
                        logger.warning(f'[MinIO 删除跳过] file_id={file_id}: MinIO 客户端不可用')
                except Exception as minio_exc:
                    logger.error(f'[MinIO 删除失败] file_id={file_id}: {minio_exc}', exc_info=True)

            # 更新 UploadBatch 的 file_count
            if batch_id:
                try:
                    batch = UploadBatch.objects.filter(id=batch_id).first()
                    if batch:
                        batch.file_count = max(0, batch.file_count - 1)
                        # 如果 file_count 变为 0，将状态改回 open
                        if batch.file_count == 0:
                            batch.status = 'open'
                        batch.save(update_fields=['file_count', 'status', 'updated_at'])
                        logger.info(
                            f'[Batch 更新] batch_id={batch_id}, '
                            f'file_count={batch.file_count}, status={batch.status}'
                        )
                except Exception as batch_exc:
                    logger.warning(f'[Batch 更新失败] batch_id={batch_id}: {batch_exc}')

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '文件删除成功',
                    'data': {
                        'id': file_id,
                    },
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'删除文件失败：{exc}',
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
            elif document_type == 'commission':
                cached_commission = cached if isinstance(cached, dict) else None
                persisted_commission = persisted if isinstance(persisted, dict) else None
                business_commission = self._load_commission_document_from_business_tables(
                    file_obj,
                    persisted_payload=persisted_commission,
                    cached_payload=cached_commission,
                )

                data = self._select_richer_commission_payload(cached_commission, persisted_commission)
                data = self._select_richer_commission_payload(data, business_commission)

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

            # 保存到内存缓存
            self._document_data_cache[file_id] = payload if isinstance(payload, dict) else {}

            # 同时保存到数据库 ocr_results 表
            if isinstance(payload, dict):
                existing = OCRResult.objects.filter(file_id=file_obj.id, page_number=1).first()
                if existing:
                    OCRResult.objects.filter(id=existing.id).update(
                        form_fields=payload,
                        raw_result={
                            'structured_data': payload,
                        },
                        updated_at=timezone.now(),
                    )
                    logger.info(f'[_put_document_data] 更新数据库成功: file_id={file_obj.id}, ocr_result_id={existing.id}')
                else:
                    OCRResult.objects.create(
                        file_id=file_obj.id,
                        page_number=1,
                        form_fields=payload,
                        raw_result={
                            'structured_data': payload,
                        },
                        ocr_engine='upstream-ocr',
                        review_status='pending',
                    )
                    logger.info(f'[_put_document_data] 创建数据库记录成功: file_id={file_obj.id}')

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '保存成功（Django本地checker）',
                    'document_type': document_type,
                },
            }
        except Exception as exc:
            logger.error(f'[_put_document_data] 保存失败: file_id={file_id}, error={exc}', exc_info=True)
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

            File.objects.filter(id=file_obj.id).update(
                review_status='completed',
                review_completed_at=timezone.now(),
                updated_at=timezone.now(),
            )

            return {
                'status_code': 200,
                'body': {'success': True, 'message': '已完成核对'},
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'完成核对失败: {exc}'},
            }

    def _mark_as_unreviewed(self, file_id: int):
        """将文件核对状态重置为待核对"""
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {
                    'status_code': 404,
                    'body': {'success': False, 'message': '文件不存在'},
                }

            File.objects.filter(id=file_obj.id).update(
                review_status='unassigned',
                review_completed_at=None,
                updated_at=timezone.now(),
            )

            logger.info(f'[_mark_as_unreviewed] 标记未核对成功: file_id={file_obj.id}')

            return {
                'status_code': 200,
                'body': {'success': True, 'message': '已标记为未核对'},
            }
        except Exception as exc:
            logger.error(f'[_mark_as_unreviewed] 标记未核对失败: file_id={file_id}, error={exc}', exc_info=True)
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'标记未核对失败: {exc}'},
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

            content_type = file_obj.mime_type or 'application/pdf'

            # 优先从 MinIO 读取
            if file_obj.minio_bucket and file_obj.minio_object_key:
                try:
                    minio_client = _get_minio_client()
                    if minio_client:
                        response = minio_client.get_object(file_obj.minio_bucket, file_obj.minio_object_key)
                        try:
                            content = response.read()
                        finally:
                            response.close()
                            response.release_conn()
                        logger.info(f'[PDF 下载] 从 MinIO 读取成功: file_id={file_id}, bucket={file_obj.minio_bucket}, key={file_obj.minio_object_key}')
                        return {
                            'status_code': 200,
                            'raw_body': content,
                            'content_type': content_type,
                        }
                except Exception as minio_exc:
                    logger.warning(f'[PDF 下载] MinIO 读取失败: file_id={file_id}, error={minio_exc}')

            # 回退到本地磁盘
            file_path = Path(file_obj.file_path or '')
            if file_path.exists() and file_path.is_file():
                content = file_path.read_bytes()
                logger.info(f'[PDF 下载] 从本地磁盘读取成功: file_id={file_id}')
                return {
                    'status_code': 200,
                    'raw_body': content,
                    'content_type': content_type,
                }

            # 都没有，返回占位 PDF
            logger.warning(f'[PDF 下载] 文件不可用: file_id={file_id}, path={file_obj.file_path}, minio={file_obj.minio_bucket}/{file_obj.minio_object_key}')
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

   

    def _save_ocr_result(self, request, file_id: int):
        """保存 OCR 识别结果到数据库"""
        try:
            file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
            if not file_obj:
                return {
                    'status_code': 404,
                    'body': {'success': False, 'message': '文件不存在'},
                }

            payload = self._parse_json_body(request)
            ocr_result = payload.get('ocr_result') or payload

            if not ocr_result:
                return {
                    'status_code': 400,
                    'body': {'success': False, 'message': 'OCR 结果为空'},
                }

            # 手动查询是否存在记录，避免 update_or_create 的 save() 主键问题
            existing = OCRResult.objects.filter(file_id=file_obj.id, page_number=1).first()

            if existing:
                # 使用 QuerySet.update() 直接执行 SQL UPDATE，绕过 save()
                OCRResult.objects.filter(id=existing.id).update(
                    form_fields=ocr_result,
                    raw_result={
                        'structured_data': ocr_result,
                    },
                    ocr_engine='upstream-ocr',
                    review_status='pending',
                    updated_at=timezone.now(),
                )
                logger.info(f'[_save_ocr_result] 更新成功: file_id={file_obj.id}, ocr_result_id={existing.id}')
            else:
                # 创建新记录
                OCRResult.objects.create(
                    file_id=file_obj.id,
                    page_number=1,
                    form_fields=ocr_result,
                    raw_result={
                        'structured_data': ocr_result,
                    },
                    ocr_engine='upstream-ocr',
                    review_status='pending',
                )
                logger.info(f'[_save_ocr_result] 创建成功: file_id={file_obj.id}')

            # 更新文件状态
            File.objects.filter(id=file_obj.id).update(
                ocr_status='completed',
                ocr_completed_at=timezone.now(),
                updated_at=timezone.now(),
            )

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '保存成功',
                },
            }
        except Exception as exc:
            logger.error(f'[_save_ocr_result] 保存失败: file_id={file_id}, error={exc}', exc_info=True)
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'保存失败: {exc}'},
            }

