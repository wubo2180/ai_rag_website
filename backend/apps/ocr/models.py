"""
OCR 统一数据模型（Django ORM）
来源：IBoxTech-ocrchecker/backend/app/models
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from django.db import models
from django.utils import timezone
from werkzeug.security import check_password_hash, generate_password_hash


class User(models.Model):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    password_hash = models.CharField(max_length=255)
    real_name = models.CharField(max_length=50, blank=True, null=True)
    role = models.CharField(max_length=20, default='user')
    is_active = models.BooleanField(default=True)
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    last_login_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'

    @property
    def password(self) -> None:
        raise AttributeError('Password is write-only.')

    @password.setter
    def password(self, raw_password: str) -> None:
        self.set_password(raw_password)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def is_admin(self) -> bool:
        return self.role == 'admin'

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'role': self.role,
            'is_active': self.is_active,
            'avatar_url': self.avatar_url,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_sensitive:
            data['password_hash'] = self.password_hash
        return data

class UploadBatch(models.Model):
    batch_name = models.CharField(max_length=50, unique=True)
    document_type_code = models.CharField(max_length=20)

    file_count = models.IntegerField(default=0)
    max_count = models.IntegerField(default=2000)

    status = models.CharField(max_length=20, default="open")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    remark = models.TextField(null=True, blank=True)
class File(models.Model):
    filename = models.CharField(max_length=255)
    stored_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    file_type = models.CharField(max_length=50)
    document_type_code = models.CharField(max_length=50, blank=True, null=True)
    mime_type = models.CharField(max_length=100)
    md5_hash = models.CharField(max_length=32, blank=True, null=True)
    sha256_hash = models.CharField(max_length=64, blank=True, null=True, db_index=True)

    uploader = models.ForeignKey(User, on_delete=models.PROTECT, related_name='uploaded_files', db_column='uploader_id')
    upload_batch_id = models.CharField(max_length=36, blank=True, null=True)

    # MinIO 存储信息
    minio_bucket = models.CharField(max_length=100, blank=True, null=True)
    minio_object_key = models.CharField(max_length=500, blank=True, null=True)
    batch_id = models.IntegerField(blank=True, null=True)

    ocr_status = models.CharField(max_length=20, default='pending')
    ocr_started_at = models.DateTimeField(blank=True, null=True)
    ocr_completed_at = models.DateTimeField(blank=True, null=True)
    ocr_error_message = models.TextField(blank=True, null=True)

    review_status = models.CharField(max_length=20, default='unassigned')
    review_started_at = models.DateTimeField(blank=True, null=True)
    review_completed_at = models.DateTimeField(blank=True, null=True)

    page_count = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'files'

    def get_tags_list(self) -> List[str]:
        return [tag.strip() for tag in self.tags.split(',')] if self.tags else []

    def get_display_size(self) -> str:
        size = float(self.file_size or 0)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f'{size:.1f} {unit}'
            size /= 1024.0
        return f'{size:.1f} TB'

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'filename': self.filename,
            'stored_filename': self.stored_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_size_display': self.get_display_size(),
            'file_type': self.file_type,
            'document_type_code': self.document_type_code,
            'mime_type': self.mime_type,
            'md5_hash': self.md5_hash,
            'sha256_hash': self.sha256_hash,
            'uploader_id': self.uploader_id,
            'upload_batch_id': self.upload_batch_id,
            'minio_bucket': self.minio_bucket,
            'minio_object_key': self.minio_object_key,
            'batch_id': self.batch_id,
            'ocr_status': self.ocr_status,
            'ocr_started_at': self.ocr_started_at.isoformat() if self.ocr_started_at else None,
            'ocr_completed_at': self.ocr_completed_at.isoformat() if self.ocr_completed_at else None,
            'ocr_error_message': self.ocr_error_message,
            'review_status': self.review_status,
            'review_started_at': self.review_started_at.isoformat() if self.review_started_at else None,
            'review_completed_at': self.review_completed_at.isoformat() if self.review_completed_at else None,
            'page_count': self.page_count,
            'description': self.description,
            'tags': self.get_tags_list(),
            'is_deleted': self.is_deleted,
            'is_processed': self.is_processed,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'deleted_at': self.deleted_at.isoformat() if self.deleted_at else None,
        }


class OCRResult(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='ocr_results', db_column='file_id')
    page_number = models.IntegerField()
    raw_text = models.TextField(blank=True, null=True)
    raw_result = models.JSONField(blank=True, null=True)
    table_data = models.JSONField(blank=True, null=True)
    form_fields = models.JSONField(blank=True, null=True)
    text_regions = models.JSONField(blank=True, null=True)
    table_regions = models.JSONField(blank=True, null=True)
    handwriting_regions = models.JSONField(blank=True, null=True)
    confidence_score = models.FloatField(blank=True, null=True)
    quality_score = models.FloatField(blank=True, null=True)
    processing_time = models.FloatField(blank=True, null=True)
    ocr_engine = models.CharField(max_length=50, default='PaddleOCR')
    ocr_version = models.CharField(max_length=20, blank=True, null=True)
    is_reviewed = models.BooleanField(default=False)
    review_status = models.CharField(max_length=20, default='pending')
    corrected_table_data = models.JSONField(blank=True, null=True)
    corrected_form_fields = models.JSONField(blank=True, null=True)
    correction_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'ocr_results'

    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        data = {
            'id': self.id,
            'file_id': self.file_id,
            'page_number': self.page_number,
            'table_data': self.table_data,
            'form_fields': self.form_fields,
            'text_regions': self.text_regions,
            'table_regions': self.table_regions,
            'handwriting_regions': self.handwriting_regions,
            'confidence_score': self.confidence_score,
            'quality_score': self.quality_score,
            'processing_time': self.processing_time,
            'ocr_engine': self.ocr_engine,
            'ocr_version': self.ocr_version,
            'is_reviewed': self.is_reviewed,
            'review_status': self.review_status,
            'corrected_table_data': self.corrected_table_data,
            'corrected_form_fields': self.corrected_form_fields,
            'correction_notes': self.correction_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
        }
        if include_raw:
            data['raw_text'] = self.raw_text
            data['raw_result'] = self.raw_result
        return data


class ReviewRecord(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='review_records', db_column='file_id')
    reviewer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='review_records', db_column='reviewer_id')
    ocr_result = models.ForeignKey(OCRResult, on_delete=models.SET_NULL, blank=True, null=True, related_name='review_records', db_column='ocr_result_id')
    review_type = models.CharField(max_length=20)
    action_type = models.CharField(max_length=20)
    field_name = models.CharField(max_length=100, blank=True, null=True)
    old_value = models.JSONField(blank=True, null=True)
    new_value = models.JSONField(blank=True, null=True)
    page_number = models.IntegerField(blank=True, null=True)
    row_index = models.IntegerField(blank=True, null=True)
    column_index = models.IntegerField(blank=True, null=True)
    coordinates = models.JSONField(blank=True, null=True)
    review_notes = models.TextField(blank=True, null=True)
    confidence_level = models.CharField(max_length=10, blank=True, null=True)
    is_confirmed = models.BooleanField(default=True)
    error_type = models.CharField(max_length=50, blank=True, null=True)
    severity = models.CharField(max_length=10, blank=True, null=True)
    review_duration = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'review_records'


class FileAssignment(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='assignments', db_column='file_id')
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_assignments', db_column='assigned_by')
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assigned_files', db_column='assigned_to')
    assignment_type = models.CharField(max_length=20, default='review')
    priority = models.CharField(max_length=10, default='medium')
    status = models.CharField(max_length=20, default='assigned')
    assigned_at = models.DateTimeField(default=timezone.now)
    due_date = models.DateTimeField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    estimated_duration = models.IntegerField(blank=True, null=True)
    actual_duration = models.IntegerField(blank=True, null=True)
    assignment_notes = models.TextField(blank=True, null=True)
    completion_notes = models.TextField(blank=True, null=True)
    feedback = models.TextField(blank=True, null=True)
    quality_score = models.IntegerField(blank=True, null=True)
    is_approved = models.BooleanField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='approved_assignments', db_column='approved_by')
    approved_at = models.DateTimeField(blank=True, null=True)
    reassignment_count = models.IntegerField(default=0)
    previous_assignee = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='previous_assignments', db_column='previous_assignee')

    class Meta:
        db_table = 'file_assignments'


class ModelConfig(models.Model):
    name = models.CharField(max_length=100)
    api_url = models.CharField(max_length=500)
    file_type = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    config_params = models.JSONField(blank=True, null=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    timeout = models.IntegerField(default=120)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, db_column='created_by')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'model_configs'


class FileTypeConfig(models.Model):
    type_code = models.CharField(max_length=50, unique=True)
    type_name = models.CharField(max_length=100)
    type_description = models.TextField(blank=True, null=True)
    model_config = models.ForeignKey(ModelConfig, on_delete=models.SET_NULL, blank=True, null=True, related_name='file_types', db_column='model_config_id')
    ocr_config = models.JSONField(blank=True, null=True)
    storage_tables = models.JSONField(default=list)
    adapter_class = models.CharField(max_length=100)
    adapter_module = models.CharField(max_length=200, default='adapters')
    form_config = models.JSONField(blank=True, null=True)
    form_component = models.CharField(max_length=200, blank=True, null=True)
    validation_rules = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'file_type_configs'


class CommissionBasic(models.Model):
    form_number = models.CharField(max_length=50)
    commission_number = models.CharField(max_length=50, unique=True)
    service_type = models.CharField(max_length=20, blank=True, null=True)
    need_report = models.CharField(max_length=10, blank=True, null=True)
    commission_department = models.CharField(max_length=50, blank=True, null=True)
    commissioner = models.CharField(max_length=30, blank=True, null=True)
    commission_date = models.DateField(blank=True, null=True)
    commission_address = models.CharField(max_length=200, blank=True, null=True)
    sample_name = models.CharField(max_length=100, blank=True, null=True)
    sample_quantity = models.CharField(max_length=50, blank=True, null=True)
    sample_code = models.CharField(max_length=50, blank=True, null=True)
    sample_batch = models.CharField(max_length=50, blank=True, null=True)
    product_number = models.CharField(max_length=100, blank=True, null=True)
    sample_weight = models.CharField(max_length=50, blank=True, null=True)
    delivery_time = models.DateTimeField(blank=True, null=True)
    required_time = models.DateField(blank=True, null=True)
    sample_disposal = models.CharField(max_length=20, blank=True, null=True)
    storage_method = models.CharField(max_length=50, blank=True, null=True)
    project_number = models.CharField(max_length=100, blank=True, null=True)
    material_number = models.CharField(max_length=100, blank=True, null=True)
    test_nature = models.CharField(max_length=50, blank=True, null=True)
    test_description = models.TextField(blank=True, null=True)
    special_condition_flag = models.CharField(max_length=10, blank=True, null=True)
    special_condition_detail = models.CharField(max_length=200, blank=True, null=True)
    product_quantity = models.CharField(max_length=50, blank=True, null=True)
    tester = models.CharField(max_length=30, blank=True, null=True)
    data_reviewer = models.CharField(max_length=30, blank=True, null=True)
    review_date = models.DateField(blank=True, null=True)
    form_complete = models.CharField(max_length=10, blank=True, null=True)
    sample_info_consistent = models.CharField(max_length=10, blank=True, null=True)
    sample_condition_ok = models.CharField(max_length=10, blank=True, null=True)
    other_notes = models.CharField(max_length=200, blank=True, null=True)
    delivery_person_signature = models.CharField(max_length=100, blank=True, null=True)
    business_receiver_signature = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'commission_basic'


class TestItem(models.Model):
    commission = models.ForeignKey(CommissionBasic, to_field='commission_number', db_column='commission_number', on_delete=models.CASCADE, related_name='test_items')
    test_item = models.CharField(max_length=100)
    test_equipment = models.CharField(max_length=100, blank=True, null=True)
    test_standard = models.CharField(max_length=100, blank=True, null=True)
    test_condition = models.CharField(max_length=100, blank=True, null=True)
    product_standard = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=20, blank=True, null=True)
    test_result = models.TextField(blank=True, null=True)
    tester = models.CharField(max_length=30, blank=True, null=True)
    remark = models.CharField(max_length=200, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'test_items'


class SpecialTest(models.Model):
    commission = models.ForeignKey(CommissionBasic, to_field='commission_number', db_column='commission_number', on_delete=models.CASCADE, related_name='special_tests')
    test_type = models.CharField(max_length=20)
    element_name = models.CharField(max_length=50)
    standard_value = models.CharField(max_length=50, blank=True, null=True)
    measured_value = models.CharField(max_length=50, blank=True, null=True)
    remark = models.CharField(max_length=200, blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'special_tests'


class CommissionOcrResult(models.Model):
    commission = models.ForeignKey(CommissionBasic, to_field='commission_number', db_column='commission_number', on_delete=models.CASCADE, related_name='ocr_results')
    original_pdf_path = models.CharField(max_length=500)
    ocr_raw_data = models.TextField(blank=True, null=True)
    field_mapping = models.TextField(blank=True, null=True)
    total_fields = models.IntegerField(default=0)
    recognized_fields = models.IntegerField(default=0)
    avg_confidence = models.CharField(max_length=10, blank=True, null=True)
    ocr_status = models.CharField(max_length=20, default='pending')
    review_status = models.CharField(max_length=20, default='pending')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True, related_name='commission_reviewed_results', db_column='reviewer_id')
    reviewed_at = models.DateTimeField(blank=True, null=True)
    review_comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'commission_ocr_results'


class CommissionDocument(models.Model):
    pdf_filename = models.CharField(max_length=255)
    minio_object_name = models.CharField(max_length=500)
    minio_bucket = models.CharField(max_length=100)
    file_size = models.BigIntegerField(blank=True, null=True)
    file_md5 = models.CharField(max_length=32, blank=True, null=True)
    page_count = models.IntegerField(default=1)
    extraction_timestamp = models.DateTimeField(blank=True, null=True)
    commission_number = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'commission_documents'
        indexes = [
            models.Index(fields=['pdf_filename'], name='idx_pdf_filename'),
            models.Index(fields=['commission_number'], name='idx_commission_number'),
            models.Index(fields=['created_at'], name='idx_created_at'),
        ]


class CommissionExtractedField(models.Model):
    document = models.ForeignKey(CommissionDocument, on_delete=models.CASCADE, related_name='extracted_fields', db_column='document_id')
    page_number = models.IntegerField()
    field_name = models.CharField(max_length=100)
    field_value = models.TextField(blank=True, null=True)
    field_type = models.CharField(max_length=50, blank=True, null=True)
    extraction_method = models.CharField(max_length=100, blank=True, null=True)
    confidence = models.FloatField(blank=True, null=True)
    source_block_id = models.CharField(max_length=100, blank=True, null=True)
    source_block_text = models.TextField(blank=True, null=True)
    bbox_json = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'commission_extracted_fields'
        indexes = [
            models.Index(fields=['document'], name='idx_document_id'),
            models.Index(fields=['field_name'], name='idx_field_name'),
            models.Index(fields=['page_number'], name='idx_page_number'),
        ]


class CommissionStatistics(models.Model):
    document = models.ForeignKey(CommissionDocument, on_delete=models.CASCADE, related_name='statistics', db_column='document_id')
    page_number = models.IntegerField()
    source_content_blocks = models.IntegerField(blank=True, null=True)
    grid_cells_count = models.IntegerField(blank=True, null=True)
    matched_cells_count = models.IntegerField(blank=True, null=True)
    total_fields_extracted = models.IntegerField(blank=True, null=True)
    single_cell_fields = models.IntegerField(blank=True, null=True)
    adjacent_cell_fields = models.IntegerField(blank=True, null=True)
    handwritten_fields = models.IntegerField(blank=True, null=True)
    table_data_count = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'commission_statistics'
        indexes = [models.Index(fields=['document'], name='idx_document_id_stats')]

