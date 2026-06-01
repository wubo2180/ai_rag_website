#!/usr/bin/env python3
"""
快速测试API服务器功能
"""

import requests
import json
import time
from pathlib import Path

def test_api_health():
    """测试API健康状态"""
    print("🔍 测试API服务器连接...")
    try:
        response = requests.get("http://localhost:6001/health", timeout=10)
        if response.status_code == 200:
            print("✅ API服务器运行正常")
            result = response.json()
            print(f"   响应: {json.dumps(result, ensure_ascii=False)}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务器")
        return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_api_root():
    """测试API根路径"""
    print("\n🔍 测试API根路径...")
    try:
        response = requests.get("http://localhost:6001/", timeout=10)
        if response.status_code == 200:
            print("✅ 根路径访问正常")
            result = response.json()
            print(f"   响应: {json.dumps(result, ensure_ascii=False)}")
            # print(f"   服务: {result.get('service', 'N/A')}")
            # print(f"   版本: {result.get('version', 'N/A')}")
            # print(f"   状态: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ 根路径访问失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 测试出错: {e}")
        return False

def test_pdf_analyze_with_sample():
    """使用示例PDF文件测试分析功能"""
    print("\n🔍 查找可用的PDF文件...")
    
    # 查找可用的PDF文件
    pdf_dirs = [
        Path("/home/h3c/workspace/IBoxTech-ocr/data/input"),
        Path(".")
    ]
    
    sample_pdf = None
    for pdf_dir in pdf_dirs:
        if pdf_dir.exists():
            pdf_files = list(pdf_dir.glob("*.pdf"))
            if pdf_files:
                sample_pdf = pdf_files[0]
                break
    
    if not sample_pdf:
        print("⚠️  未找到可用的PDF文件")
        print("   如需测试PDF分析功能，请将PDF文件放在data/input/目录下")
        return False
    
    print(f"📄 使用示例文件: {sample_pdf.name}")
    print("⏳ 正在测试PDF分析功能（这可能需要一些时间）...")
    
    try:
        with open(sample_pdf, 'rb') as f:
            files = {'file': (sample_pdf.name, f, 'application/pdf')}
            
            start_time = time.time()
            response = requests.post(
                "http://localhost:6001/analyze",
                files=files,
                timeout=120  # 2分钟超时
            )
            end_time = time.time()
        
        if response.status_code == 200:
            print("✅ PDF分析功能正常")
            result = response.json()
            
            print(f"   📊 处理结果:")
            print(f"      成功: {result.get('success', False)}")
            print(f"      消息: {result.get('message', 'N/A')}")
            print(f"      总页数: {result.get('total_pages', 0)}")
            print(f"      处理时间: {result.get('processing_time', 0):.2f}秒")
            print(f"      请求时间: {end_time - start_time:.2f}秒")

            print(f"   响应: {json.dumps(result, ensure_ascii=False)}")
            
            # 详细显示OCR数据
            if result.get('ocr_raw_data'):
                ocr_pages = len(result['ocr_raw_data'])
                print(f"      OCR数据页数: {ocr_pages}")
                
                for i, page_data in enumerate(result['ocr_raw_data'], 1):
                    print(f"         第{i}页:")
                    if 'error' in page_data:
                        print(f"           ❌ 错误: {page_data['error']}")
                    else:
                        dt_polys = len(page_data.get('dt_polys', []))
                        rec_res = len(page_data.get('rec_res', []))
                        print(f"           📍 文本框: {dt_polys}个")
                        print(f"           📝 识别文本: {rec_res}个")
                        
                        # 显示前几个识别的文本
                        if page_data.get('rec_res'):
                            print(f"           📄 示例文本:")
                            for j, text_info in enumerate(page_data['rec_res'][:3]):
                                if isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                    text, confidence = text_info[0], text_info[1]
                                    print(f"             {j+1}. '{text}' (置信度: {confidence:.3f})")
            
            # 详细显示字段提取结果
            if result.get('field_extraction_results'):
                field_pages = len(result['field_extraction_results'])
                print(f"      字段提取页数: {field_pages}")
                
                for i, page_data in enumerate(result['field_extraction_results'], 1):
                    print(f"         第{i}页:")
                    if 'error' in page_data:
                        print(f"           ❌ 错误: {page_data['error']}")
                    else:
                        fields = page_data.get('extracted_fields', {})
                        print(f"           📋 提取字段: {len(fields)}个")
                        
                        # 显示前几个提取的字段
                        if fields:
                            print(f"           🏷️  示例字段:")
                            for j, (field_name, field_info) in enumerate(list(fields.items())[:3]):
                                if isinstance(field_info, dict) and 'value' in field_info:
                                    print(f"             {j+1}. {field_name}: '{field_info['value']}'")
            
            # 显示合并结果统计
            if result.get('combined_results'):
                combined = result['combined_results']
                print(f"      🔗 合并统计:")
                print(f"         总文本框: {combined['combined_ocr_data']['total_text_boxes']}")
                print(f"         合并字段: {combined['combined_field_data']['total_fields_extracted']}")
                conf_summary = combined['combined_ocr_data']['confidence_summary']
                if conf_summary['avg_confidence'] > 0:
                    print(f"         平均置信度: {conf_summary['avg_confidence']:.3f}")
            
            # 保存测试结果
            with open("api_test_result.json", "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("   💾 完整结果已保存到: api_test_result.json")
            
            # 如果有错误，显示完整的返回数据用于调试
            has_errors = any('error' in page for page in result.get('ocr_raw_data', []))
            has_errors = has_errors or any('error' in page for page in result.get('field_extraction_results', []))
            
            if has_errors:
                print("\n   🔍 检测到错误，显示完整返回数据:")
                print("   " + "="*50)
                print(json.dumps(result, ensure_ascii=False, indent=6))
                print("   " + "="*50)
            
            return True
        else:
            print(f"❌ PDF分析失败: {response.status_code}")
            print(f"   错误信息: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⚠️  请求超时 - PDF处理可能需要更长时间")
        return False
    except Exception as e:
        print(f"❌ PDF分析出错: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 快速测试API服务器")
    print("=" * 40)
    
    # 测试1: 健康检查
    health_ok = test_api_health()
    
    # 测试2: 根路径
    if health_ok:
        root_ok = test_api_root()
    else:
        print("❌ 跳过后续测试，因为无法连接到服务器")
        return
    
    # 测试3: PDF分析（可选）
    if root_ok:
        print("\n" + "=" * 40)
        print("是否测试PDF分析功能？")
        print("⚠️  注意：PDF分析可能需要较长时间")
        
        try:
            # 自动进行轻量测试
            print("🔄 进行轻量级PDF分析测试...")
            pdf_ok = test_pdf_analyze_with_sample()
        except KeyboardInterrupt:
            print("\n⚠️  用户中断测试")
            pdf_ok = False
    
    print("\n" + "=" * 40)
    print("📊 测试总结:")
    print(f"   健康检查: {'✅' if health_ok else '❌'}")
    if health_ok:
        print(f"   根路径访问: {'✅' if root_ok else '❌'}")
        if root_ok:
            try:
                print(f"   PDF分析: {'✅' if pdf_ok else '⚠️'}")
            except:
                print(f"   PDF分析: ⚠️ 未完成")
    
    if health_ok and root_ok:
        print("\n🎉 API服务器基本功能正常！")
        print("📖 访问 http://localhost:6001/docs 查看完整API文档")
    else:
        print("\n❌ API服务器存在问题，请检查服务器状态")

if __name__ == "__main__":
    main()
