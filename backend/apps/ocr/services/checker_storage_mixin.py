from pathlib import Path
import os
import importlib
import logging
from datetime import datetime

from django.db import connection
from django.utils.dateparse import parse_date, parse_datetime

from ..models import CommissionBasic, File, OCRResult, SpecialTest, TestItem

logger = logging.getLogger(__name__)


class CheckerStorageMixin:
    _legacy_ids_checked = False
    @staticmethod
    def _format_date_output(value):
        if not value:
            return ''
        try:
            return value.strftime('%Y-%m-%d')
        except Exception:
            return str(value)

    @staticmethod
    def _format_datetime_output(value):
        if not value:
            return ''
        try:
            return value.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(value)

    @staticmethod
    def _commission_payload_score(payload):
        if not isinstance(payload, dict):
            return -1

        payload = CheckerStorageMixin._normalize_commission_payload(payload)
        score = 0
        basic_info = payload.get('basic_info') if isinstance(payload.get('basic_info'), dict) else {}
        score += sum(1 for value in basic_info.values() if CheckerStorageMixin._safe_text(value))

        test_items = payload.get('test_items') if isinstance(payload.get('test_items'), list) else []
        special_tests = payload.get('special_tests') if isinstance(payload.get('special_tests'), list) else []
        score += len(test_items) * 5
        score += len(special_tests) * 5
        return score

    @classmethod
    def _select_richer_commission_payload(cls, primary_payload, secondary_payload):
        primary_normalized = (
            cls._normalize_commission_payload(primary_payload)
            if isinstance(primary_payload, dict)
            else primary_payload
        )
        secondary_normalized = (
            cls._normalize_commission_payload(secondary_payload)
            if isinstance(secondary_payload, dict)
            else secondary_payload
        )
        primary_score = cls._commission_payload_score(primary_normalized)
        secondary_score = cls._commission_payload_score(secondary_normalized)

        if secondary_score >= primary_score and secondary_score >= 0:
            preferred = secondary_normalized
            fallback = primary_normalized
        elif primary_score >= 0:
            preferred = primary_normalized
            fallback = secondary_normalized
        else:
            preferred = secondary_normalized if isinstance(secondary_normalized, dict) else primary_normalized
            fallback = primary_normalized if preferred is secondary_normalized else secondary_normalized

        if not isinstance(preferred, dict):
            return preferred
        if not isinstance(fallback, dict):
            return preferred

        merged = dict(preferred)
        preferred_basic = preferred.get('basic_info') if isinstance(preferred.get('basic_info'), dict) else {}
        fallback_basic = fallback.get('basic_info') if isinstance(fallback.get('basic_info'), dict) else {}
        merged_basic = dict(preferred_basic)
        for key, value in fallback_basic.items():
            if not cls._safe_text(merged_basic.get(key)) and cls._safe_text(value):
                merged_basic[key] = value
        merged['basic_info'] = merged_basic
        merged['test_items'] = cls._merge_commission_rows(
            preferred.get('test_items'),
            fallback.get('test_items'),
        )
        merged['special_tests'] = cls._merge_commission_rows(
            preferred.get('special_tests'),
            fallback.get('special_tests'),
        )
        return merged

    @classmethod
    def _merge_commission_rows(cls, preferred_rows, fallback_rows):
        merged = []
        seen = set()

        def append_rows(rows):
            if not isinstance(rows, list):
                return
            for row in rows:
                if not isinstance(row, dict):
                    continue
                signature = cls._commission_row_signature(row)
                if signature in seen:
                    continue
                seen.add(signature)
                merged.append(dict(row))

        append_rows(preferred_rows)
        append_rows(fallback_rows)
        return merged

    @classmethod
    def _commission_row_signature(cls, row):
        if not isinstance(row, dict):
            return ''
        parts = []
        for key in sorted(row.keys()):
            if key == 'sort_order':
                continue
            value = row.get(key)
            text = cls._safe_text(value)
            if text:
                parts.append(f'{key}={text}')
        if parts:
            return '|'.join(parts)
        return f'row:{id(row)}'

    @staticmethod
    def _safe_text(value):
        if value is None:
            return ''
        if isinstance(value, (dict, list)):
            return ''
        return str(value).strip()


    @classmethod
    def _first_text(cls, *values):
        for value in values:
            text = cls._safe_text(value)
            if text:
                return text
        return ''

    @classmethod
    def _normalize_commission_payload(cls, payload):
        if not isinstance(payload, dict):
            return payload

        normalized = dict(payload)
        raw_basic = normalized.get('basic_info')
        basic_info = dict(raw_basic) if isinstance(raw_basic, dict) else {}

        def fill_basic(target, *aliases):
            if cls._safe_text(basic_info.get(target)):
                return
            value = cls._first_text(*(basic_info.get(alias) for alias in aliases))
            if value:
                basic_info[target] = value

        fill_basic('other_notes', '\u5176\u4ed6\u68c0\u67e5\u9879', '\u5176\u4ed6')
        fill_basic(
            'sample_condition_ok',
            'sample_condition',
            '\u6837\u54c1\u662f\u5426\u5b8c\u597d',
            '\u6837\u54c1\u662f\u5426\u5b8c\u597d\u5e76\u65e0\u591a\u4f59\u9644\u5e26\u7269\uff0c\u662f\u5426\u6ee1\u8db3\u6d4b\u8bd5\u6761\u4ef6\uff1f',
        )
        fill_basic(
            'business_receiver_signature',
            'business_handler_signature',
            '\u4e1a\u52a1\u53d7\u7406\u4eba\u7b7e\u5b57',
            '\u4e1a\u52a1\u53d7\u7406\u4eba\u7b7e\u5b57/\u65e5\u671f',
            '\u4e1a\u52a1\u53d7\u7406\u4eba\u7b7e\u540d/\u65e5\u671f',
            '\u4e1a\u52a1\u53d7\u8fce\u4eba\u91dc\u5b57/\u65e5\u671f',
        )
        fill_basic(
            'delivery_person_signature',
            '\u9001\u6837\u4eba\u7b7e\u540d',
            '\u9001\u6837\u4eba\u7b7e\u540d/\u65e5\u671f',
        )
        fill_basic('commission_number', 'order_number', '\u59d4\u6258\u5355\u53f7', '\u8ba2\u5355\u7f16\u53f7')
        fill_basic('commissioner', 'client_name', '\u5ba2\u6237\u540d\u79f0', '\u59d4\u6258\u4eba')
        fill_basic('commission_date', 'order_date', '\u4e0b\u5355\u65e5\u671f', '\u59d4\u6258\u65e5\u671f')
        fill_basic('need_report', 'report_submitted', '\u662f\u5426\u63d0\u4ea4\u62a5\u544a')
        fill_basic('sample_weight', 'sample_spec_weight', '\u6837\u54c1\u89c4\u683c/\u91cd\u91cf')
        fill_basic('delivery_time', 'sample_arrival_time', '\u6837\u54c1\u5230\u8fbe\u65f6\u95f4')
        fill_basic('sample_batch', 'sample_batch_number', '\u6837\u54c1\u6279\u53f7')
        fill_basic('sample_disposal', 'sample_handling', '\u6837\u54c1\u5904\u7406')
        fill_basic('required_time', 'deadline', '\u8981\u6c42\u5b8c\u6210\u65f6\u95f4')
        fill_basic('test_description', 'test_remarks', '\u6d4b\u8bd5\u5907\u6ce8', '\u6d4b\u8bd5\u8bf4\u660e')
        fill_basic('data_reviewer', 'report_reviewer', '\u62a5\u544a\u5ba1\u6838')
        fill_basic('review_date', 'report_date', '\u62a5\u544a\u65e5\u671f')

        test_item_aliases = {
            'item': 'test_item',
            '\u6d4b\u8bd5\u9879\u76ee': 'test_item',
            'test_item': 'test_item',
            '\u6d4b\u8bd5\u8bbe\u5907': 'test_equipment',
            'test_equipment': 'test_equipment',
            'standard': 'test_standard',
            '\u6d4b\u8bd5\u6807\u51c6': 'test_standard',
            'test_standard': 'test_standard',
            '\u6d4b\u8bd5\u6761\u4ef6': 'test_condition',
            'test_condition': 'test_condition',
            '\u4ea7\u54c1\u6807\u51c6': 'product_standard',
            '\u5224\u5b9a\u6807\u51c6': 'product_standard',
            'product_standard': 'product_standard',
            '\u5355\u4f4d': 'unit',
            'unit': 'unit',
            'result': 'test_result',
            '\u6d4b\u8bd5\u7ed3\u679c': 'test_result',
            'test_result': 'test_result',
            '\u6d4b\u8bd5\u5458': 'tester',
            '\u5219\u8bd5\u5458': 'tester',
            'tester': 'tester',
            '\u5907\u6ce8': 'remark',
            'remark': 'remark',
        }
        special_test_aliases = {
            '\u6d4b\u8bd5\u7c7b\u578b': 'test_type',
            'test_type': 'test_type',
            'element': 'element_name',
            '\u5143\u7d20\u540d\u79f0': 'element_name',
            'element_name': 'element_name',
            'standard_ppm': 'standard_value',
            '\u6807\u51c6\u503c': 'standard_value',
            '\u6807\u51c6': 'standard_value',
            'standard_value': 'standard_value',
            'result_ppm': 'measured_value',
            '\u5b9e\u6d4b\u503c': 'measured_value',
            '\u5b9e\u6d4b': 'measured_value',
            '\u6d4b\u8bd5\u503c': 'measured_value',
            'measured_value': 'measured_value',
            '\u5907\u6ce8': 'remark',
            'remark': 'remark',
        }

        def normalize_rows(rows, aliases):
            normalized_rows = []
            if not isinstance(rows, list):
                return normalized_rows
            for item in rows:
                if not isinstance(item, dict):
                    continue
                row = dict(item)
                for source_key, target_key in aliases.items():
                    if source_key in row and not cls._safe_text(row.get(target_key)):
                        row[target_key] = row.get(source_key)
                if aliases is special_test_aliases and not cls._safe_text(row.get('test_type')):
                    row['test_type'] = '元素分析'
                normalized_rows.append(row)
            return normalized_rows

        normalized['basic_info'] = basic_info
        normalized['test_items'] = normalize_rows(normalized.get('test_items'), test_item_aliases)
        special_tests = normalize_rows(normalized.get('special_tests'), special_test_aliases)
        special_tests.extend(normalize_rows(normalized.get('element_analysis'), special_test_aliases))
        normalized['special_tests'] = special_tests
        return normalized

    @staticmethod
    def _safe_date(value):
        text = CheckerStorageMixin._safe_text(value)
        if not text:
            return None

        parsed = parse_date(text)
        if parsed:
            return parsed

        normalized = text.replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').strip()
        parsed = parse_date(normalized)
        if parsed:
            return parsed

        if len(normalized) >= 10:
            parsed = parse_date(normalized[:10])
            if parsed:
                return parsed

        return None

    @staticmethod
    def _safe_datetime(value):
        text = CheckerStorageMixin._safe_text(value)
        if not text:
            return None

        parsed_dt = parse_datetime(text)
        if parsed_dt:
            return parsed_dt

        normalized = text.replace('年', '-').replace('月', '-').replace('日', ' ').replace('/', '-').strip()
        parsed_dt = parse_datetime(normalized)
        if parsed_dt:
            return parsed_dt

        parsed_date = CheckerStorageMixin._safe_date(text)
        if parsed_date:
            return datetime.combine(parsed_date, datetime.min.time())

        return None

    @classmethod
    def _ensure_legacy_table_ids(cls):
        if cls._legacy_ids_checked:
            return

        cls._legacy_ids_checked = True

        if connection.vendor != 'mysql':
            return

        repair_plan = [
            ('commission_basic', 'commission_number, created_at'),
            ('test_items', 'commission_number, sort_order, test_item, created_at'),
            ('special_tests', 'commission_number, sort_order, test_type, element_name, created_at'),
        ]

        try:
            with connection.cursor() as cursor:
                for index, (table_name, order_by) in enumerate(repair_plan, start=1):
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE id IS NULL')
                    row = cursor.fetchone()
                    missing_count = int((row[0] if row else 0) or 0)
                    if missing_count <= 0:
                        continue

                    variable_name = f'legacy_next_id_{index}'
                    cursor.execute(
                        f'SET @{variable_name} := (SELECT COALESCE(MAX(id), 0) FROM {table_name})'
                    )
                    cursor.execute(
                        f'''
                        UPDATE {table_name}
                        SET id = (@{variable_name} := @{variable_name} + 1)
                        WHERE id IS NULL
                        ORDER BY {order_by}
                        '''
                    )
                    logger.warning('[legacy-id-repair] repaired %s rows in %s', missing_count, table_name)
            connection.commit()
        except Exception:
            connection.rollback()
            cls._legacy_ids_checked = False
            logger.exception('[legacy-id-repair] failed')
            raise

    @staticmethod
    def _allocate_legacy_ids(model, count):
        if count <= 0:
            return []

        table_name = model._meta.db_table
        with connection.cursor() as cursor:
            cursor.execute(f'SELECT COALESCE(MAX(id), 0) FROM {table_name}')
            row = cursor.fetchone()
            start_id = int((row[0] if row else 0) or 0)
        return list(range(start_id + 1, start_id + count + 1))

    def _persist_structured_document(self, file_obj: File, structured_data):
        self._ensure_legacy_table_ids()
        document_type = str(file_obj.document_type_code or 'commission').strip().lower()
        if document_type != 'commission' or not isinstance(structured_data, dict):
            return

        structured_data = self._normalize_commission_payload(structured_data)
        basic_info_raw = structured_data.get('basic_info')
        test_items_raw = structured_data.get('test_items')
        special_tests_raw = structured_data.get('special_tests')

        basic_info = basic_info_raw if isinstance(basic_info_raw, dict) else {}
        test_items = test_items_raw if isinstance(test_items_raw, list) else []
        special_tests = special_tests_raw if isinstance(special_tests_raw, list) else []

        commission_number = self._safe_text(basic_info.get('commission_number')) or str(file_obj.pk)
        form_number = self._safe_text(basic_info.get('form_number')) or commission_number

        defaults = {
            'form_number': form_number,
            'service_type': self._safe_text(basic_info.get('service_type')),
            'need_report': self._safe_text(basic_info.get('need_report')),
            'commission_department': self._safe_text(basic_info.get('commission_department')),
            'commissioner': self._safe_text(basic_info.get('commissioner')),
            'commission_date': self._safe_date(basic_info.get('commission_date')),
            'commission_address': self._safe_text(basic_info.get('commission_address')),
            'sample_name': self._safe_text(basic_info.get('sample_name')),
            'sample_quantity': self._safe_text(basic_info.get('sample_quantity')),
            'sample_code': self._safe_text(basic_info.get('sample_code')),
            'sample_batch': self._safe_text(basic_info.get('sample_batch')),
            'product_number': self._safe_text(basic_info.get('product_number')),
            'sample_weight': self._safe_text(basic_info.get('sample_weight')),
            'delivery_time': self._safe_datetime(basic_info.get('delivery_time')),
            'required_time': self._safe_date(basic_info.get('required_time')),
            'sample_disposal': self._safe_text(basic_info.get('sample_disposal')),
            'storage_method': self._safe_text(basic_info.get('storage_method')),
            'project_number': self._safe_text(basic_info.get('project_number')),
            'material_number': self._safe_text(basic_info.get('material_number')),
            'test_nature': self._safe_text(basic_info.get('test_nature')),
            'test_description': self._safe_text(basic_info.get('test_description')),
            'special_condition_flag': self._safe_text(basic_info.get('special_condition_flag')),
            'special_condition_detail': self._safe_text(basic_info.get('special_condition_detail')),
            'product_quantity': self._safe_text(basic_info.get('product_quantity')),
            'tester': self._safe_text(basic_info.get('tester')),
            'data_reviewer': self._safe_text(basic_info.get('data_reviewer')),
            'review_date': self._safe_date(basic_info.get('review_date')),
            'form_complete': self._safe_text(basic_info.get('form_complete')),
            'sample_info_consistent': self._safe_text(basic_info.get('sample_info_consistent')),
            'sample_condition_ok': self._safe_text(basic_info.get('sample_condition_ok') or basic_info.get('sample_condition')),
            'other_notes': self._safe_text(basic_info.get('other_notes')),
            'delivery_person_signature': self._safe_text(basic_info.get('delivery_person_signature')),
            'business_receiver_signature': self._safe_text(
                basic_info.get('business_receiver_signature') or basic_info.get('business_handler_signature')
            ),
        }

        commission_queryset = CommissionBasic.objects.filter(commission_number=commission_number)
        if commission_queryset.exists():
            commission_queryset.update(**defaults)
        else:
            legacy_id = self._allocate_legacy_ids(CommissionBasic, 1)[0]
            CommissionBasic.objects.create(
                id=legacy_id,
                commission_number=commission_number,
                **defaults,
            )

        TestItem.objects.filter(commission_id=commission_number).delete()
        test_item_ids = self._allocate_legacy_ids(TestItem, len(test_items))
        test_records = []
        for index, item in enumerate(test_items):
            if not isinstance(item, dict):
                continue
            test_name = self._safe_text(item.get('test_item')) or f'测试项目{index + 1}'
            test_records.append(
                TestItem(
                    id=test_item_ids[len(test_records)],
                    commission_id=commission_number,
                    test_item=test_name,
                    test_equipment=self._safe_text(item.get('test_equipment')),
                    test_standard=self._safe_text(item.get('test_standard')),
                    test_condition=self._safe_text(item.get('test_condition')),
                    product_standard=self._safe_text(item.get('product_standard')),
                    unit=self._safe_text(item.get('unit')),
                    test_result=self._safe_text(item.get('test_result')),
                    tester=self._safe_text(item.get('tester')),
                    remark=self._safe_text(item.get('remark')),
                    sort_order=index,
                )
            )
        if test_records:
            TestItem.objects.bulk_create(test_records)

        SpecialTest.objects.filter(commission_id=commission_number).delete()
        special_test_ids = self._allocate_legacy_ids(SpecialTest, len(special_tests))
        special_records = []
        for index, item in enumerate(special_tests):
            if not isinstance(item, dict):
                continue
            test_type = self._safe_text(item.get('test_type')) or '特殊测试'
            element_name = self._safe_text(item.get('element_name')) or f'元素{index + 1}'
            special_records.append(
                SpecialTest(
                    id=special_test_ids[len(special_records)],
                    commission_id=commission_number,
                    test_type=test_type,
                    element_name=element_name,
                    standard_value=self._safe_text(item.get('standard_value')),
                    measured_value=self._safe_text(item.get('measured_value')),
                    remark=self._safe_text(item.get('remark')),
                    sort_order=index,
                )
            )
        if special_records:
            SpecialTest.objects.bulk_create(special_records)

    def _load_commission_document_from_business_tables(self, file_obj: File, persisted_payload=None, cached_payload=None):
        self._ensure_legacy_table_ids()
        default_payload = self._default_document_payload('commission', file_obj)

        commission_candidates = []
        for source in (cached_payload, persisted_payload):
            if not isinstance(source, dict):
                continue
            basic_info = source.get('basic_info') if isinstance(source.get('basic_info'), dict) else {}
            number = self._safe_text(basic_info.get('commission_number'))
            if number and number not in commission_candidates:
                commission_candidates.append(number)

        fallback_number = str(file_obj.pk)
        if fallback_number and fallback_number not in commission_candidates:
            commission_candidates.append(fallback_number)

        commission_obj = None
        for number in commission_candidates:
            commission_obj = CommissionBasic.objects.filter(commission_number=number).first()
            if commission_obj:
                break

        if not commission_obj:
            return default_payload

        basic_info = {
            'form_number': self._safe_text(commission_obj.form_number),
            'commission_number': self._safe_text(commission_obj.commission_number),
            'service_type': self._safe_text(commission_obj.service_type),
            'need_report': self._safe_text(commission_obj.need_report),
            'commission_department': self._safe_text(commission_obj.commission_department),
            'commissioner': self._safe_text(commission_obj.commissioner),
            'commission_date': self._format_date_output(commission_obj.commission_date),
            'commission_address': self._safe_text(commission_obj.commission_address),
            'sample_name': self._safe_text(commission_obj.sample_name),
            'sample_quantity': self._safe_text(commission_obj.sample_quantity),
            'sample_code': self._safe_text(commission_obj.sample_code),
            'sample_batch': self._safe_text(commission_obj.sample_batch),
            'product_number': self._safe_text(commission_obj.product_number),
            'sample_weight': self._safe_text(commission_obj.sample_weight),
            'delivery_time': self._format_datetime_output(commission_obj.delivery_time),
            'required_time': self._format_date_output(commission_obj.required_time),
            'sample_disposal': self._safe_text(commission_obj.sample_disposal),
            'storage_method': self._safe_text(commission_obj.storage_method),
            'project_number': self._safe_text(commission_obj.project_number),
            'material_number': self._safe_text(commission_obj.material_number),
            'test_nature': self._safe_text(commission_obj.test_nature),
            'test_description': self._safe_text(commission_obj.test_description),
            'special_condition_flag': self._safe_text(commission_obj.special_condition_flag),
            'special_condition_detail': self._safe_text(commission_obj.special_condition_detail),
            'product_quantity': self._safe_text(commission_obj.product_quantity),
            'tester': self._safe_text(commission_obj.tester),
            'data_reviewer': self._safe_text(commission_obj.data_reviewer),
            'review_date': self._format_date_output(commission_obj.review_date),
            'form_complete': self._safe_text(commission_obj.form_complete),
            'sample_info_consistent': self._safe_text(commission_obj.sample_info_consistent),
            'sample_condition_ok': self._safe_text(commission_obj.sample_condition_ok),
            'other_notes': self._safe_text(commission_obj.other_notes),
            'delivery_person_signature': self._safe_text(commission_obj.delivery_person_signature),
            'business_receiver_signature': self._safe_text(commission_obj.business_receiver_signature),
        }

        test_items = [
            {
                'test_item': self._safe_text(item.test_item),
                'test_equipment': self._safe_text(item.test_equipment),
                'test_standard': self._safe_text(item.test_standard),
                'test_condition': self._safe_text(item.test_condition),
                'product_standard': self._safe_text(item.product_standard),
                'unit': self._safe_text(item.unit),
                'test_result': self._safe_text(item.test_result),
                'tester': self._safe_text(item.tester),
                'remark': self._safe_text(item.remark),
                'sort_order': item.sort_order,
            }
            for item in TestItem.objects.filter(
                commission_id=commission_obj.commission_number
            ).order_by('sort_order', 'id')
        ]

        special_tests = [
            {
                'test_type': self._safe_text(item.test_type),
                'element_name': self._safe_text(item.element_name),
                'standard_value': self._safe_text(item.standard_value),
                'measured_value': self._safe_text(item.measured_value),
                'remark': self._safe_text(item.remark),
                'sort_order': item.sort_order,
            }
            for item in SpecialTest.objects.filter(
                commission_id=commission_obj.commission_number
            ).order_by('sort_order', 'id')
        ]

        return {
            'basic_info': basic_info,
            'test_items': test_items,
            'special_tests': special_tests,
        }

    def _load_latest_ocr_payload(self, file_id: int):
        try:
            result = OCRResult.objects.filter(file_id=file_id).order_by('-updated_at', '-id').first()
            if not result or not isinstance(result.raw_result, dict):
                return None

            raw_result = result.raw_result
            structured = raw_result.get('structured_data')
            if isinstance(structured, dict):
                payload = self._normalize_commission_payload(structured)
                extractor = getattr(self, '_extract_dify_output_payload', None)
                if callable(extractor):
                    workflow_payload = extractor(raw_result)
                    if isinstance(workflow_payload, dict):
                        payload = self._select_richer_commission_payload(
                            payload,
                            self._normalize_commission_payload(workflow_payload),
                        )
                return payload

            if self._is_meaningful_document_payload('paper', raw_result):
                return raw_result
            if self._is_meaningful_document_payload('commission', raw_result):
                return self._normalize_commission_payload(raw_result)
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
                # Path(__file__).resolve().parents[4] / 'backend' / '.env.dev',
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
            # workspace_root / 'backend' / '.env.dev',
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
        # 优先使用数据库中已存储的 MinIO 信息（上传时写入的 minio_bucket / minio_object_key）
        stored_bucket = getattr(file_obj, 'minio_bucket', None) or ''
        stored_object = getattr(file_obj, 'minio_object_key', None) or ''
        if stored_bucket and stored_object:
            return stored_bucket.strip(), stored_object.strip()

        object_name = (file_obj.file_path or '').strip().replace('\\', '/').lstrip('/')
        bucket_name = default_bucket

        if not object_name:
            return bucket_name, object_name

        # 本地磁盘路径（Windows/Linux）不应被当作 MinIO 对象键。
        lowered = object_name.lower()
        if (
            ':' in object_name[:3]
            or object_name.startswith('/')
            or object_name.startswith('./')
            or object_name.startswith('../')
            or lowered.startswith('file://')
        ):
            return bucket_name, ''

        # 兼容 s3://bucket/object 的显式格式。
        if lowered.startswith('s3://'):
            parts = object_name[5:].split('/', 1)
            if len(parts) == 2 and parts[0] and parts[1]:
                return parts[0], parts[1]
            return bucket_name, ''

        # 兼容 file_path 存成 bucket/object 的场景。
        if '/' in object_name:
            first, rest = object_name.split('/', 1)
            known_buckets = {default_bucket, 'ocr-files', 'commissions'}
            if first and first in known_buckets and rest:
                bucket_name = first
                object_name = rest

        return bucket_name, object_name

    @staticmethod
    def _build_minio_object_candidates(file_obj: File, resolved_object_name: str):
        candidates = []

        def push(value):
            text = (value or '').strip().replace('\\', '/').lstrip('/')
            if text and text not in candidates:
                candidates.append(text)

        # 优先使用解析出的对象键。
        push(resolved_object_name)

        # 历史记录可能把本地路径写入 file_path，这里取 basename 做兜底。
        raw_file_path = (getattr(file_obj, 'file_path', '') or '').strip().replace('\\', '/')
        basename = raw_file_path.split('/')[-1] if raw_file_path else ''
        push(basename)

        # 兼容旧实现常见键：stored_filename / filename。
        stored_filename = (getattr(file_obj, 'stored_filename', '') or '').strip()
        original_filename = (getattr(file_obj, 'filename', '') or '').strip()
        push(stored_filename)
        push(original_filename)

        # 常见目录前缀兜底。
        if stored_filename:
            push(f'checker/{stored_filename}')
            push(f'uploads/{stored_filename}')
            push(f'ocr_uploads/{stored_filename}')
        if basename:
            push(f'checker/{basename}')
            push(f'uploads/{basename}')
            push(f'ocr_uploads/{basename}')

        return candidates

    def _upload_local_file_to_minio(self, local_path: Path, object_name: str, content_type: str = 'application/octet-stream'):
        try:
            Minio = importlib.import_module('minio').Minio
        except Exception as exc:
            return {
                'success': False,
                'error': f'minio包不可用: {exc}',
            }

        cfg = self._build_minio_config()
        bucket_name = cfg['bucket_name']
        object_name = (object_name or '').strip().replace('\\', '/').lstrip('/')

        if not object_name:
            return {
                'success': False,
                'error': '对象名为空，无法上传到MinIO',
            }

        try:
            client = Minio(
                cfg['endpoint'],
                access_key=cfg['access_key'],
                secret_key=cfg['secret_key'],
                secure=cfg['secure'],
            )

            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)

            client.fput_object(
                bucket_name,
                object_name,
                str(local_path),
                content_type=content_type or 'application/octet-stream',
            )

            self._minio_probe_cache = {'ok': True, 'error': None}
            return {
                'success': True,
                'bucket': bucket_name,
                'object': object_name,
                'storage_path': f'{bucket_name}/{object_name}',
            }
        except Exception as exc:
            self._minio_probe_cache = {'ok': False, 'error': str(exc)}
            return {
                'success': False,
                'error': str(exc),
            }

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
            candidate_objects = self._build_minio_object_candidates(file_obj, object_name)
            if not candidate_objects:
                self._minio_probe_cache = {'ok': False, 'error': '无可用对象键，无法从MinIO读取'}
                return None

            bucket_candidates = [bucket_name]
            if cfg['bucket_name'] not in bucket_candidates:
                bucket_candidates.append(cfg['bucket_name'])

            last_error = None
            for candidate_bucket in bucket_candidates:
                for candidate_object in candidate_objects:
                    try:
                        response = client.get_object(candidate_bucket, candidate_object)
                        try:
                            data = response.read()
                        finally:
                            response.close()
                            response.release_conn()

                        self._minio_probe_cache = {
                            'ok': True,
                            'error': None,
                            'bucket': candidate_bucket,
                            'object': candidate_object,
                        }
                        return data
                    except Exception as exc:
                        last_error = exc
                        continue

            self._minio_probe_cache = {'ok': False, 'error': str(last_error) if last_error else '未知错误'}
            return None
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
        candidate_objects = self._build_minio_object_candidates(file_obj, object_name)

        if not candidate_objects:
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
            bucket_candidates = [bucket_name]
            if cfg['bucket_name'] not in bucket_candidates:
                bucket_candidates.append(cfg['bucket_name'])

            last_error = None
            for candidate_bucket in bucket_candidates:
                for candidate_object in candidate_objects:
                    try:
                        stat = client.stat_object(candidate_bucket, candidate_object)
                        return {
                            'available': True,
                            'endpoint': cfg['endpoint'],
                            'bucket': candidate_bucket,
                            'object': candidate_object,
                            'size': getattr(stat, 'size', None),
                        }
                    except Exception as exc:
                        last_error = exc
                        continue

            return {
                'available': False,
                'endpoint': cfg['endpoint'],
                'bucket': bucket_name,
                'object': object_name,
                'candidates': candidate_objects[:8],
                'error': str(last_error) if last_error else '未找到对象',
            }
        except Exception as exc:
            return {
                'available': False,
                'endpoint': cfg['endpoint'],
                'bucket': bucket_name,
                'object': object_name,
                'candidates': candidate_objects[:8],
                'error': str(exc),
            }
