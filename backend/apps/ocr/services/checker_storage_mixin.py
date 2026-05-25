from pathlib import Path
import os
import importlib

from django.db import connection

from ..models import File, OCRResult


class CheckerStorageMixin:
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
        file_values = CheckerStorageMixin._read_env_values(
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

    @staticmethod
    def _build_minio_config():
        target_keys = {
            'MINIO_ENDPOINT',
            'MINIO_ACCESS_KEY',
            'MINIO_SECRET_KEY',
            'MINIO_BUCKET_NAME',
            'MINIO_SECURE',
        }
        file_values = CheckerStorageMixin._read_env_values(
            CheckerStorageMixin._candidate_env_files(),
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
        return CheckerStorageMixin._read_env_values(
            CheckerStorageMixin._candidate_env_files(),
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
