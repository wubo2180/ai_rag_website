"""
外部OCR API回调接口
接收外部OCR服务的识别结果
"""
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from . import api_bp
from models import db, get_models
from utils.decorators import admin_required
from services.commission_direct_import_service import CommissionDirectImportService

# 获取模型
models = get_models()
File = models['File']
CommissionBasic = models['CommissionBasic']
TestItem = models['TestItem']
SpecialTest = models['SpecialTest']
CommissionOcrResult = models['CommissionOcrResult']


@api_bp.route('/ocr/callback', methods=['POST'])
@jwt_required()
@admin_required
def receive_ocr_callback():
    """
    接收外部OCR API的识别结果回调
    
    请求体:
    {
        "file_id": 文件ID,
        "ocr_result": {
            "commission_number": "委托编号",
            "structured_data": {
                "basic_info": { ... },
                "test_items": [ ... ],
                "special_tests": [ ... ]
            },
            "confidence": 0.95,
            "ocr_engine": "external_api_v1"
        }
    }
    """
    try:
        data = request.get_json()
        
        # 验证必填参数
        if not data or 'file_id' not in data or 'ocr_result' not in data:
            return jsonify({
                'success': False,
                'message': '缺少必填参数：file_id 或 ocr_result'
            }), 400
        
        file_id = data['file_id']
        ocr_result = data['ocr_result']
        
        # 验证文件是否存在
        file_record = File.query.get(file_id)
        if not file_record:
            return jsonify({
                'success': False,
                'message': f'文件不存在：file_id={file_id}'
            }), 404
        
        # 提取结构化数据
        commission_number = ocr_result.get('commission_number')
        structured_data = ocr_result.get('structured_data', {})
        
        if not commission_number:
            return jsonify({
                'success': False,
                'message': '缺少委托编号'
            }), 400
        
        # 检查委托编号是否已存在
        existing = CommissionBasic.query.filter_by(commission_number=commission_number).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'委托编号已存在：{commission_number}'
            }), 409
        
        # 获取当前用户ID
        current_user_id = get_jwt_identity()
        
        # 保存委托基本信息
        basic_info = structured_data.get('basic_info', {})
        if basic_info:
            basic_info['commission_number'] = commission_number
            commission_basic = CommissionBasic(**basic_info)
            db.session.add(commission_basic)
        
        # 保存测试项目
        test_items = structured_data.get('test_items', [])
        for i, item in enumerate(test_items):
            item['commission_number'] = commission_number
            item['sort_order'] = i
            test_item = TestItem(**item)
            db.session.add(test_item)
        
        # 保存特殊测试
        special_tests = structured_data.get('special_tests', [])
        for i, test in enumerate(special_tests):
            test['commission_number'] = commission_number
            test['sort_order'] = i
            special_test = SpecialTest(**test)
            db.session.add(special_test)
        
        # 保存OCR结果记录
        ocr_result_record = CommissionOcrResult(
            commission_number=commission_number,
            original_pdf_path=file_record.file_path,
            ocr_raw_data=str(ocr_result),
            total_fields=len(basic_info) + len(test_items) + len(special_tests),
            recognized_fields=len(basic_info) + len(test_items) + len(special_tests),
            avg_confidence=str(ocr_result.get('confidence', 0.0)),
            ocr_status='completed',
            review_status='pending'
        )
        db.session.add(ocr_result_record)
        
        # 更新文件状态
        file_record.ocr_status = 'completed'
        file_record.is_processed = True
        
        # 提交事务
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'OCR结果接收成功',
            'data': {
                'file_id': file_id,
                'commission_number': commission_number,
                'test_items_count': len(test_items),
                'special_tests_count': len(special_tests)
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'处理OCR回调失败: {str(e)}'
        }), 500


@api_bp.route('/ocr/status', methods=['GET'])
@jwt_required()
def get_ocr_service_status():
    """
    获取OCR服务状态
    """
    return jsonify({
        'success': True,
        'data': {
            'internal_ocr_enabled': False,
            'external_ocr_required': True,
            'message': '内置OCR已禁用，请使用外部OCR API',
            'callback_endpoint': '/api/ocr/callback',
            'import_service_available': True
        }
    })


@api_bp.route('/ocr/test-callback', methods=['POST'])
@jwt_required()
@admin_required
def test_ocr_callback():
    """
    测试OCR回调接口
    使用模拟数据测试回调流程
    """
    try:
        # 模拟OCR结果数据
        test_data = {
            "file_id": request.json.get('file_id', 1),
            "ocr_result": {
                "commission_number": f"TEST{__import__('time').time_ns()}"[-12:],
                "structured_data": {
                    "basic_info": {
                        "commission_department": "测试部门",
                        "commissioner": "测试人员",
                        "commission_date": "2024-10-16",
                        "sample_name": "测试样品"
                    },
                    "test_items": [
                        {
                            "test_item": "测试项目1",
                            "test_standard": "GB/T 1234"
                        }
                    ],
                    "special_tests": []
                },
                "confidence": 0.95,
                "ocr_engine": "test_engine"
            }
        }
        
        # 调用回调处理
        return receive_ocr_callback()
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'测试失败: {str(e)}'
        }), 500

