import re
from typing import Any


class CheckerPaperMixin:
    @classmethod
    def _empty_paper_document_payload(cls):
        fallback: dict[str, Any] = {
            'basic_info': {
                'article_id': '',
                'article_name': '',
                'article_doi': '',
                'publish_year': '',
            },
            'materials': [],
            'preparation_process': '',
            'intermediates': [],
            'properties': {'columns': [], 'rows': []},
            'notes': '',
        }
        default_payload_factory = getattr(cls, '_default_document_payload', None)
        if callable(default_payload_factory):
            candidate = default_payload_factory('paper')
            if isinstance(candidate, dict):
                return candidate
        return fallback

    @staticmethod
    def _paper_text(value):
        if value is None:
            return ''
        if isinstance(value, dict):
            for key in ('value', 'text', 'content', 'name'):
                if key in value:
                    return CheckerPaperMixin._paper_text(value.get(key))
            return ''
        if isinstance(value, list):
            for item in value:
                text = CheckerPaperMixin._paper_text(item)
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
            value = CheckerPaperMixin._paper_text(source.get(key))
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
                    'key': cls._paper_text(column.get('key')) or cls._paper_slugify(cls._paper_text(column.get('name')), index + 1),
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
            properties = item.get('properties')
            for prop in properties if isinstance(properties, list) else []:
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

    def _fill_paper_fields(self, paper_data: dict, structured: dict):
        normalized = self._normalize_paper_payload(paper_data)
        structured.clear()
        structured.update(normalized)
