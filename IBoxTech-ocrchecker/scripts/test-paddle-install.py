#!/usr/bin/env python3
"""
PaddlePaddle 3.2.0 + PaddleOCR 2.7.3 安装验证脚本
"""
import sys
import importlib

def test_import(module_name, display_name=None):
    """测试模块导入"""
    if display_name is None:
        display_name = module_name
    
    try:
        module = importlib.import_module(module_name)
        version = getattr(module, '__version__', 'unknown')
        print(f"✅ {display_name}: {version}")
        return True, module
    except ImportError as e:
        print(f"❌ {display_name}: 导入失败 - {str(e)}")
        return False, None
    except Exception as e:
        print(f"⚠️ {display_name}: 检查失败 - {str(e)}")
        return False, None

def main():
    """主测试函数"""
    print("🔍 PaddlePaddle 3.2.0 兼容性测试")
    print("=" * 40)
    
    # 测试核心依赖
    tests = [
        ('paddle', 'PaddlePaddle'),
        ('paddleocr', 'PaddleOCR'),
        ('cv2', 'OpenCV'),
        ('PIL', 'Pillow'),
        ('numpy', 'NumPy'),
    ]
    
    success_count = 0
    total_tests = len(tests)
    
    for module_name, display_name in tests:
        success, module = test_import(module_name, display_name)
        if success:
            success_count += 1
    
    print("\n" + "=" * 40)
    print(f"📊 测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("\n🎉 所有依赖安装成功！")
        
        # 进行功能测试
        print("\n🧪 进行OCR功能测试...")
        try:
            import paddleocr
            ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
            print("✅ PaddleOCR 初始化成功")
            print("✅ 系统已就绪，可以开始使用OCR功能")
            return 0
        except Exception as e:
            print(f"⚠️ OCR初始化失败: {str(e)}")
            print("📝 建议检查CUDA配置或重新安装PaddlePaddle")
            return 1
    else:
        print(f"\n❌ {total_tests - success_count} 个依赖安装失败")
        print("\n📋 建议执行以下命令修复:")
        print("pip install -r backend/requirements.txt --force-reinstall")
        return 1

if __name__ == '__main__':
    sys.exit(main())
