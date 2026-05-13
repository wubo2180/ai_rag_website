from pathlib import Path
import os
import re
import uuid
import json
import importlib

from django.core.paginator import Paginator
from django.db import connection
from django.utils import timezone

from ..models import File, OCRResult


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
            article_id = ''
            if file_id is not None:
                article_id = f"A-{int(file_id):05d}"[-7:]

            return {
                'article_id': article_id,
                'article_name': file_name,
                'performance_trend': '待补充',
                'hierarchical_data': [],
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

    def _list_files(self, request):
        try:
            page = max(int(request.GET.get('page', 1)), 1)
            per_page = min(max(int(request.GET.get('per_page', 20)), 1), 100)
            status_filter = request.GET.get('status')
            review_status_filter = request.GET.get('review_status')
            document_type_filter = request.GET.get('document_type')

            queryset = File.objects.filter(is_deleted=False).order_by('-created_at')

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
                    files_data.append(self._serialize_file(item))
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
            force_refresh = str(getattr(request, 'GET', {}).get('refresh', '')).strip().lower() in {'1', 'true', 'yes'}
            cached = None if force_refresh else self._document_data_cache.get(file_id)
            if document_type == 'paper':
                cached_paper = cached if isinstance(cached, dict) else None
                legacy_paper = self._load_paper_document_from_legacy_tables(file_id)
                data = self._select_richer_paper_payload(cached_paper, legacy_paper)
                if isinstance(data, dict):
                    self._document_data_cache[file_id] = data
            elif isinstance(cached, dict) and self._is_meaningful_document_payload(document_type, cached):
                data = cached
            else:
                data = self._default_document_payload(document_type, file_obj)

            if not data:
                data = self._default_document_payload(document_type, file_obj)

            if document_type == 'paper' and not data.get('article_name'):
                data['article_name'] = file_obj.filename or ''

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
            if str(payload.get('article_id') or '').strip():
                return True
            if str(payload.get('article_name') or '').strip():
                return True
            if str(payload.get('performance_trend') or '').strip():
                return True
            hierarchical_data = payload.get('hierarchical_data')
            if isinstance(hierarchical_data, list) and len(hierarchical_data) > 0:
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

    @staticmethod
    def _select_richer_paper_payload(cached_payload, legacy_payload):
        def score(payload):
            if not isinstance(payload, dict):
                return -1

            hierarchy = payload.get('hierarchical_data')
            hierarchy_count = len(hierarchy) if isinstance(hierarchy, list) else 0
            property_count = 0
            if isinstance(hierarchy, list):
                for row in hierarchy:
                    props = row.get('properties') if isinstance(row, dict) else None
                    if isinstance(props, list):
                        property_count += len(props)

            score_value = 0
            if str(payload.get('article_id') or '').strip():
                score_value += 10
            if str(payload.get('article_name') or '').strip():
                score_value += 10
            if str(payload.get('performance_trend') or '').strip():
                score_value += 5

            score_value += hierarchy_count * 20
            score_value += property_count
            return score_value

        cached_score = score(cached_payload)
        legacy_score = score(legacy_payload)

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
            self._document_data_cache[file_id] = payload if isinstance(payload, dict) else {}

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '保存成功（Django本地checker）',
                    'document_type': self._normalize_document_type(file_obj),
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
            if file_id not in self._document_data_cache:
                self._document_data_cache[file_id] = self._default_document_payload(document_type, file_obj)

            file_obj.ocr_status = 'completed'
            file_obj.ocr_completed_at = timezone.now()
            file_obj.save(update_fields=['ocr_status', 'ocr_completed_at', 'updated_at'])

            self._tasks[task_id] = {
                'status': 'completed',
                'result': {
                    'structured_data': self._document_data_cache[file_id],
                    'document_type': document_type,
                },
            }

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '本地识别任务已完成',
                    'data': {'task_id': task_id},
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'启动识别失败: {exc}'},
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

            self._document_data_cache[file_id] = ocr_result

            file_obj.ocr_status = 'completed'
            file_obj.save(update_fields=['ocr_status', 'updated_at'])

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': 'OCR结果保存成功（Django本地checker）',
                    'document_type': self._normalize_document_type(file_obj),
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {'success': False, 'message': f'OCR结果保存失败: {exc}'},
            }
