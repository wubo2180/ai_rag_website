"""
委托测试数据模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from . import db


class CommissionBasic(db.Model):
    """委托测试基本信息表"""
    __tablename__ = 'commission_basic'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    
    # 基本标识信息
    form_number = Column(String(50), nullable=False, comment='表格编号')  # 去掉unique约束，允许表格编号重复
    commission_number = Column(String(50), nullable=False, unique=True, comment='委托编号')  # 保持委托编号唯一
    service_type = Column(String(20), comment='服务类型')
    need_report = Column(String(10), comment='是否需要报告')
    
    # 委托信息
    commission_department = Column(String(50), comment='委托部门')
    commissioner = Column(String(30), comment='委托人')
    commission_date = Column(Date, comment='委托日期')
    commission_address = Column(String(200), comment='委托地址')
    
    # 样品信息
    sample_name = Column(String(100), comment='样品名称')
    sample_quantity = Column(String(50), comment='样品数量')
    sample_code = Column(String(50), comment='样品代码')
    sample_batch = Column(String(50), comment='样品批次')
    product_number = Column(String(100), comment='产品或原材料型号')
    sample_weight = Column(String(50), comment='样品重量')
    delivery_time = Column(DateTime, comment='送样时间')
    required_time = Column(Date, comment='需求时间')
    sample_disposal = Column(String(20), comment='余样处理')
    storage_method = Column(String(50), comment='样品储存方式')
    project_number = Column(String(100), comment='研发项目')
    material_number = Column(String(100), comment='物料代码')
    
    # 测试信息
    test_nature = Column(String(50), comment='测试性质')
    test_description = Column(Text, comment='测试说明')
    special_condition_flag = Column(String(10), comment='有无特殊条件')
    special_condition_detail = Column(String(200), comment='条件详情')
    product_quantity = Column(String(50), comment='此次投产数量')
    
    # 人员信息（手写字段）
    tester = Column(String(30), comment='测试员')
    data_reviewer = Column(String(30), comment='数据复核人')
    review_date = Column(Date, comment='复核日期')
    
    # 审核检查项（单选字段）
    form_complete = Column(String(10), comment='申请单是否填写完整')
    sample_info_consistent = Column(String(10), comment='样品信息是否一致')
    sample_condition_ok = Column(String(10), comment='样品是否完好')
    other_notes = Column(String(200), comment='其他')
    
    # 签名信息（手写字段）
    delivery_person_signature = Column(String(100), comment='送样人签名/日期')
    business_receiver_signature = Column(String(100), comment='业务受理人签字/日期')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    # 关系定义
    test_items = relationship('TestItem', backref='commission', lazy=True, cascade='all, delete-orphan')
    special_tests = relationship('SpecialTest', backref='commission', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<CommissionBasic {self.commission_number}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'form_number': self.form_number,
            'commission_number': self.commission_number,
            'service_type': self.service_type,
            'need_report': self.need_report,
            'commission_department': self.commission_department,
            'commissioner': self.commissioner,
            'commission_date': self.commission_date.isoformat() if self.commission_date else None,
            'commission_address': self.commission_address,
            'sample_name': self.sample_name,
            'sample_quantity': self.sample_quantity,
            'sample_code': self.sample_code,
            'sample_batch': self.sample_batch,
            'product_number': self.product_number,
            'sample_weight': self.sample_weight,
            'delivery_time': self.delivery_time.isoformat() if self.delivery_time else None,
            'required_time': self.required_time.isoformat() if self.required_time else None,
            'sample_disposal': self.sample_disposal,
            'storage_method': self.storage_method,
            'project_number': self.project_number,
            'material_number': self.material_number,
            'test_nature': self.test_nature,
            'test_description': self.test_description,
            'special_condition_flag': self.special_condition_flag,
            'special_condition_detail': self.special_condition_detail,
            'product_quantity': self.product_quantity,
            'tester': self.tester,
            'data_reviewer': self.data_reviewer,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'form_complete': self.form_complete,
            'sample_info_consistent': self.sample_info_consistent,
            'sample_condition_ok': self.sample_condition_ok,
            'other_notes': self.other_notes,
            'delivery_person_signature': self.delivery_person_signature,
            'business_receiver_signature': self.business_receiver_signature,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def to_dict_with_relations(self):
        """转换为包含关联数据的字典格式"""
        data = self.to_dict()
        data['test_items'] = [item.to_dict() for item in self.test_items]
        data['special_tests'] = [test.to_dict() for test in self.special_tests]
        return data


class TestItem(db.Model):
    """测试项目表"""
    __tablename__ = 'test_items'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    commission_number = Column(String(50), ForeignKey('commission_basic.commission_number'), 
                             nullable=False, comment='委托编号')
    
    # 测试项目信息
    test_item = Column(String(100), nullable=False, comment='测试项目')
    test_equipment = Column(String(100), comment='测试设备')
    test_standard = Column(String(100), comment='测试标准')
    test_condition = Column(String(100), comment='测试条件')
    product_standard = Column(String(100), comment='产品标准')
    unit = Column(String(20), comment='单位')
    test_result = Column(Text, comment='测试结果')
    tester = Column(String(30), comment='测试员')
    remark = Column(String(200), comment='备注')
    
    # 排序和系统字段
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<TestItem {self.commission_number}-{self.test_item}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'commission_number': self.commission_number,
            'test_item': self.test_item,
            'test_equipment': self.test_equipment,
            'test_standard': self.test_standard,
            'test_condition': self.test_condition,
            'product_standard': self.product_standard,
            'unit': self.unit,
            'test_result': self.test_result,
            'tester': self.tester,
            'remark': self.remark,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class SpecialTest(db.Model):
    """特殊测试表"""
    __tablename__ = 'special_tests'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    commission_number = Column(String(50), ForeignKey('commission_basic.commission_number'), 
                             nullable=False, comment='委托编号')
    
    # 特殊测试信息
    test_type = Column(String(20), nullable=False, comment='测试类型（RoHs/HF/其他金属）')
    element_name = Column(String(50), nullable=False, comment='元素名称')
    standard_value = Column(String(50), comment='标准值')
    measured_value = Column(String(50), comment='实测值')
    remark = Column(String(200), comment='备注')
    
    # 排序和系统字段
    sort_order = Column(Integer, default=0, comment='排序序号')
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    
    def __repr__(self):
        return f'<SpecialTest {self.commission_number}-{self.test_type}-{self.element_name}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'commission_number': self.commission_number,
            'test_type': self.test_type,
            'element_name': self.element_name,
            'standard_value': self.standard_value,
            'measured_value': self.measured_value,
            'remark': self.remark,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# 为了支持OCR识别结果和审核流程，可以扩展以下模型

class CommissionOcrResult(db.Model):
    """委托测试OCR识别结果表"""
    __tablename__ = 'commission_ocr_results'
    
    id = Column(Integer, primary_key=True, comment='主键ID')
    commission_number = Column(String(50), ForeignKey('commission_basic.commission_number'),
                             nullable=False, comment='委托编号')
    
    # OCR结果信息
    original_pdf_path = Column(String(500), nullable=False, comment='原始PDF文件路径')
    ocr_raw_data = Column(Text, comment='OCR原始识别数据(JSON格式)')
    field_mapping = Column(Text, comment='字段映射关系(JSON格式)')
    
    # 识别质量信息
    total_fields = Column(Integer, default=0, comment='总字段数')
    recognized_fields = Column(Integer, default=0, comment='成功识别字段数')
    avg_confidence = Column(String(10), comment='平均置信度')
    
    # 状态信息
    ocr_status = Column(String(20), default='pending', comment='OCR状态(pending/completed/failed)')
    review_status = Column(String(20), default='pending', comment='审核状态(pending/approved/rejected)')
    reviewer_id = Column(Integer, ForeignKey('users.id'), comment='审核人ID')
    reviewed_at = Column(DateTime, comment='审核时间')
    review_comments = Column(Text, comment='审核意见')
    
    # 系统字段
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f'<CommissionOcrResult {self.commission_number}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'commission_number': self.commission_number,
            'original_pdf_path': self.original_pdf_path,
            'total_fields': self.total_fields,
            'recognized_fields': self.recognized_fields,
            'avg_confidence': self.avg_confidence,
            'ocr_status': self.ocr_status,
            'review_status': self.review_status,
            'reviewer_id': self.reviewer_id,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_comments': self.review_comments,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
