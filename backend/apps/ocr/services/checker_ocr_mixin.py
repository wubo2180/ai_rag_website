from pathlib import Path
import os
import re
import threading
import uuid
import json

from django.db import close_old_connections
from django.utils import timezone
import requests

from ..models import File, OCRResult
from .config import get_paper_dify_config, get_service_base_urls, get_timeout
from .checker_paper_mixin import CheckerPaperMixin
from .checker_storage_mixin import CheckerStorageMixin


class CheckerOcrMixin(CheckerStorageMixin, CheckerPaperMixin):
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
            content_type = upload_resp.headers.get('Content-Type', '')
            body_preview = (upload_resp.text or '')[:200].replace('\n', ' ').strip()
            raise ValueError(
                f'Dify文件上传返回非JSON: HTTP {upload_resp.status_code}, url={upload_url}, '
                f'content_type={content_type}, body={body_preview}'
            ) from exc

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
                return CheckerOcrMixin._extract_scalar_value(value.get('value'))
            if 'text' in value:
                return CheckerOcrMixin._extract_scalar_value(value.get('text'))
            if 'content' in value:
                return CheckerOcrMixin._extract_scalar_value(value.get('content'))
            return ''
        if isinstance(value, list):
            for item in value:
                scalar = CheckerOcrMixin._extract_scalar_value(item)
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
