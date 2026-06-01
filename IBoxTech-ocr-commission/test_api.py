#!/usr/bin/env python3
"""
测试OCR Commission API接口
"""

import requests
import json
from pathlib import Path

# API地址
BASE_URL = "http://localhost:6001"

def test_health():
    """测试健康检查接口"""
    print("=" * 60)
    print("测试 /health 接口")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()
    
    # 验证返回格式
    data = response.json()
    assert "status" in data, "缺少 status 字段"
    assert "timestamp" in data, "缺少 timestamp 字段"
    print("✅ /health 接口测试通过")
    print()


def test_analyze(pdf_file_path: str):
    """测试分析接口"""
    print("=" * 60)
    print("测试 /api/analyze 接口")
    print("=" * 60)
    
    if not Path(pdf_file_path).exists():
        print(f"❌ 文件不存在: {pdf_file_path}")
        return
    
    # 准备文件和参数
    files = {
        'file': ('test.pdf', open(pdf_file_path, 'rb'), 'application/pdf')
    }
    
    data = {
        'user': 'test_user',
        'token': 'test_token_123',
        'response_mode': 'blocking',
        'extra': json.dumps({"custom_param": "value"})
    }
    
    print(f"上传文件: {pdf_file_path}")
    print(f"参数:")
    for key, value in data.items():
        print(f"  - {key}: {value}")
    print()
    
    response = requests.post(f"{BASE_URL}/api/analyze", files=files, data=data)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"响应内容:")
        print(json.dumps({
            "success": result.get("success"),
            "message": result.get("message"),
            "processing_time": result.get("processing_time"),
            "data": {
                "total_pages": result.get("data", {}).get("total_pages"),
                "ocr_raw_data_count": result.get("data", {}).get("ocr_raw_data", []),
                "field_extraction_results_count": result.get("data", {}).get("field_extraction_results", []),
                "has_combined_results": result.get("data", {}).get("combined_results")
            }
        }, indent=2, ensure_ascii=False))
        print()
        
        # 验证返回格式
        assert "success" in result, "缺少 success 字段"
        assert "message" in result, "缺少 message 字段"
        assert "data" in result, "缺少 data 字段"
        assert "processing_time" in result, "缺少 processing_time 字段"
        
        # 验证data字段结构
        data_obj = result.get("data", {})
        assert "total_pages" in data_obj, "data中缺少 total_pages 字段"
        assert "ocr_raw_data" in data_obj, "data中缺少 ocr_raw_data 字段"
        assert "field_extraction_results" in data_obj, "data中缺少 field_extraction_results 字段"
        assert "combined_results" in data_obj, "data中缺少 combined_results 字段"
        
        print("✅ /api/analyze 接口测试通过")
    else:
        print(f"❌ 请求失败: {response.text}")
    print()


def test_root():
    """测试根接口"""
    print("=" * 60)
    print("测试 / 接口")
    print("=" * 60)
    
    response = requests.get(f"{BASE_URL}/")
    print(f"状态码: {response.status_code}")
    print(f"响应内容:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    print()


if __name__ == "__main__":
    print("🚀 开始测试 IBoxTech OCR Commission API")
    print()
    
    # 测试根接口
    test_root()
    
    # 测试健康检查
    test_health()
    
    # 测试分析接口（需要提供PDF文件路径）
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        test_analyze(pdf_path)
    else:
        print("⚠️  未提供PDF文件路径，跳过 /api/analyze 接口测试")
        print("   使用方法: python test_api.py <pdf_file_path>")
        print()
    
    print("✅ 测试完成！")



