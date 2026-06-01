#!/usr/bin/env python3
"""
测试V3分层倾斜校正功能
"""

import sys
from pathlib import Path
import json

# 添加项目根路径到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import V3Config, DebugLevel, OutputLevel
from utils.logger import V3Logger
from utils.file_manager import V3FileManager
from visualization.step_visualizers import PreprocessingVisualizer
from steps.step1_preprocessing import PreprocessingStep

def test_layered_deskewing():
    """测试分层倾斜校正功能"""
    
    print("🧪 V3分层倾斜校正功能测试")
    print("=" * 50)
    
    # 输入文件
    pdf_path = "/home/h3c/workspace/IBoxTech-ocr/data/input/测试中心 品质部原材料委托单2023年4月（OA+纸质）_第2页.pdf"
    
    if not Path(pdf_path).exists():
        print(f"❌ 测试文件不存在: {pdf_path}")
        return
    
    # 创建测试输出目录
    test_output_dir = Path("layered_deskewing_test")
    test_output_dir.mkdir(exist_ok=True)
    
    # 测试3种不同的分层校正方法
    methods_to_test = [
        ('stepwise', '分步校正（推荐）'),
        ('weighted', '加权平均校正'),  
        ('best_angle', '最佳单一角度')
    ]
    
    results = {}
    
    for method, method_desc in methods_to_test:
        print(f"\n🔍 测试方法: {method_desc}")
        print("-" * 30)
        
        # 配置
        config = V3Config(
            debug_level=DebugLevel.DEBUG,
            output_level=OutputLevel.COMPREHENSIVE,
            output_dir=test_output_dir / f"method_{method}"
        )
        
        # 设置分层校正参数
        config.step_configs[1] = {
            'processing_params': {
                'use_layered_deskewing': True,
                'layered_method': method,
                'structure_weight': 0.6,
                'document_weight': 0.2,
                'content_weight': 0.2,
                'projection_angle_range': 3.0,
                'projection_angle_step': 0.2,
                'deskew_min_angle': 0.05  # 降低最小角度阈值以便测试
            }
        }
        
        # 初始化组件
        logger = V3Logger(config, log_file=config.output_dir / "test.log")
        file_manager = V3FileManager(config)
        
        # 创建处理步骤
        preprocessing_step = PreprocessingStep(config, file_manager, logger)
        
        try:
            # 执行处理
            result_path = preprocessing_step.run(pdf_path)
            
            # 读取调试数据
            debug_file = config.output_dir / "steps" / "step01" / "preprocessing_stats.json"
            if debug_file.exists():
                with open(debug_file, 'r', encoding='utf-8') as f:
                    debug_data = json.load(f)
                
                deskew_info = debug_data.get('processing_stats', {}).get('deskew_info', {})
                
                results[method] = {
                    'method_desc': method_desc,
                    'result_path': result_path,
                    'detected_angles': deskew_info.get('detected_angles', {}),
                    'final_angle': deskew_info.get('final_angle', 0.0),
                    'angle_selection_reason': deskew_info.get('angle_selection_reason', ''),
                    'correction_applied': deskew_info.get('correction_applied', False),
                    'output_dir': str(config.output_dir)
                }
                
                print(f"✅ {method_desc} 测试完成")
                print(f"   检测的角度: {deskew_info.get('detected_angles', {})}")
                print(f"   最终角度: {deskew_info.get('final_angle', 0.0):.3f}°")
                print(f"   选择策略: {deskew_info.get('angle_selection_reason', '')}")
                print(f"   输出目录: {config.output_dir}")
                
            else:
                print(f"⚠️ 无法读取调试数据: {debug_file}")
                results[method] = {
                    'method_desc': method_desc,
                    'result_path': result_path,
                    'output_dir': str(config.output_dir),
                    'debug_data_available': False
                }
                
        except Exception as e:
            print(f"❌ {method_desc} 测试失败: {e}")
            results[method] = {
                'method_desc': method_desc,
                'error': str(e)
            }
    
    # 保存测试结果汇总
    print(f"\n📊 测试结果汇总")
    print("=" * 50)
    
    summary_file = test_output_dir / "layered_deskewing_test_results.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 显示结果对比
    print("方法对比:")
    for method, result in results.items():
        if 'error' in result:
            print(f"❌ {result['method_desc']}: 失败 - {result['error']}")
        else:
            detected = result.get('detected_angles', {})
            final = result.get('final_angle', 0.0)
            print(f"✅ {result['method_desc']}:")
            print(f"   结构层: {detected.get('structure', 0.0):.3f}° | "
                  f"文档层: {detected.get('document', 0.0):.3f}° | "
                  f"内容层: {detected.get('content', 0.0):.3f}°")
            print(f"   最终角度: {final:.3f}° | 策略: {result.get('angle_selection_reason', '')}")
    
    print(f"\n📁 详细结果保存在: {summary_file}")
    
    # 建议最佳方法
    if 'stepwise' in results and 'error' not in results['stepwise']:
        print(f"\n💡 推荐使用分步校正方法，结果保存在:")
        print(f"   {results['stepwise']['output_dir']}")

def test_traditional_vs_layered():
    """对比传统方法与分层校正方法"""
    
    print(f"\n🔬 传统方法 vs 分层校正对比测试")
    print("=" * 50)
    
    pdf_path = "/home/h3c/workspace/IBoxTech-ocr/data/input/测试中心 品质部原材料委托单2023年4月（OA+纸质）_第2页.pdf"
    comparison_output_dir = Path("traditional_vs_layered_test")
    comparison_output_dir.mkdir(exist_ok=True)
    
    methods_to_compare = [
        {'use_layered_deskewing': False, 'name': 'traditional', 'desc': '传统霍夫变换'},
        {'use_layered_deskewing': True, 'layered_method': 'stepwise', 'name': 'stepwise', 'desc': '分层分步校正'}
    ]
    
    comparison_results = {}
    
    for method_config in methods_to_compare:
        method_name = method_config['name']
        method_desc = method_config['desc']
        
        print(f"\n🧪 测试: {method_desc}")
        
        # 创建配置
        config = V3Config(
            debug_level=DebugLevel.DEBUG,
            output_dir=comparison_output_dir / f"method_{method_name}"
        )
        
        # 更新处理参数
        processing_params = {
            'deskew_min_angle': 0.05  # 降低阈值便于对比
        }
        processing_params.update(method_config)
        config.step_configs[1] = {'processing_params': processing_params}
        
        # 初始化并运行
        logger = V3Logger(config, log_file=config.output_dir / "test.log")
        file_manager = V3FileManager(config)
        preprocessing_step = PreprocessingStep(config, file_manager, logger)
        
        try:
            result_path = preprocessing_step.run(pdf_path)
            print(f"✅ {method_desc} 完成: {result_path}")
            
            comparison_results[method_name] = {
                'desc': method_desc,
                'result_path': result_path,
                'output_dir': str(config.output_dir)
            }
            
        except Exception as e:
            print(f"❌ {method_desc} 失败: {e}")
            comparison_results[method_name] = {
                'desc': method_desc,
                'error': str(e)
            }
    
    # 保存对比结果
    comparison_file = comparison_output_dir / "traditional_vs_layered_results.json"
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 对比结果保存在: {comparison_file}")
    
    return comparison_results

if __name__ == "__main__":
    try:
        # 测试分层校正功能
        test_layered_deskewing()
        
        # 对比传统方法与分层方法
        test_traditional_vs_layered()
        
        print(f"\n🎉 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
