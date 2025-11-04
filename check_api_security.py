#!/usr/bin/env python
"""
验证 API Key 安全性检查
检查代码中是否还有硬编码的 API key
"""

import os
import sys
import re
from pathlib import Path

def check_hardcoded_keys():
    """检查硬编码的 API key"""
    print("🔍 检查硬编码 API Key...")
    print("=" * 60)
    
    backend_path = Path(__file__).parent / 'backend'
    
    # API key 模式
    patterns = [
        r'app-[a-zA-Z0-9]{20,}',  # Dify API key
        r'dataset-[a-zA-Z0-9]{20,}',  # Dify dataset key
        r'sk-[a-zA-Z0-9]{40,}',  # OpenAI API key
    ]
    
    # 需要忽略的文件（测试文件中的示例）
    ignore_files = {
        '.env', '.env.example', 
        '__pycache__', '.git', 'node_modules',
        'test_env_loading.py', 'check_api_security.py'
    }
    
    findings = []
    
    for py_file in backend_path.rglob('*.py'):
        if any(ignore in str(py_file) for ignore in ignore_files):
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
                for line_num, line in enumerate(content.splitlines(), 1):
                    for pattern in patterns:
                        matches = re.findall(pattern, line)
                        if matches:
                            # 检查是否是注释行
                            stripped_line = line.strip()
                            if not stripped_line.startswith('#'):
                                findings.append({
                                    'file': py_file.relative_to(Path(__file__).parent),
                                    'line': line_num,
                                    'content': line.strip(),
                                    'keys': matches
                                })
        except Exception as e:
            print(f"⚠️  无法读取文件 {py_file}: {e}")
    
    if findings:
        print("❌ 发现硬编码的 API Key:")
        for finding in findings:
            print(f"\n📁 文件: {finding['file']}")
            print(f"📍 行号: {finding['line']}")
            print(f"📄 内容: {finding['content']}")
            print(f"🔑 发现的 Key: {finding['keys']}")
    else:
        print("✅ 未发现硬编码的 API Key!")
    
    return len(findings) == 0

def check_env_config():
    """检查环境变量配置"""
    print("\n🔍 检查环境变量配置...")
    print("=" * 60)
    
    # 加载环境变量
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / 'backend' / '.env'
    load_dotenv(env_path)
    
    required_keys = [
        'DIFY_API_KEY',
        'DIFY_DATASET_API_KEY',
        'SECRET_KEY'
    ]
    
    optional_keys = [
        'DIFY_BASE_URL',
        'DIFY_DATASET_BASE_URL',
        'OPENAI_API_KEY'
    ]
    
    print("必需的环境变量:")
    all_required_present = True
    for key in required_keys:
        value = os.getenv(key)
        if value:
            masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"❌ {key}: 未设置")
            all_required_present = False
    
    print("\n可选的环境变量:")
    for key in optional_keys:
        value = os.getenv(key)
        if value:
            if 'KEY' in key:
                masked_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                masked_value = value
            print(f"✅ {key}: {masked_value}")
        else:
            print(f"⚪ {key}: 未设置 (可选)")
    
    return all_required_present

def check_settings_security():
    """检查 Django settings 安全性"""
    print("\n🔍 检查 Django settings 安全性...")
    print("=" * 60)
    
    try:
        # 添加 Django 路径
        backend_path = Path(__file__).parent / 'backend'
        sys.path.insert(0, str(backend_path))
        
        # 设置 Django 环境
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
        
        import django
        django.setup()
        
        from django.conf import settings
        
        # 检查关键设置
        checks = [
            ('DEBUG模式', not settings.DEBUG if hasattr(settings, 'DEBUG') else True),
            ('SECRET_KEY安全', len(settings.SECRET_KEY) > 20 if hasattr(settings, 'SECRET_KEY') else False),
            ('DIFY_API_KEY配置', hasattr(settings, 'DIFY_API_KEY') and bool(settings.DIFY_API_KEY)),
            ('DIFY_DATASET_API_KEY配置', hasattr(settings, 'DIFY_DATASET_API_KEY') and bool(settings.DIFY_DATASET_API_KEY)),
        ]
        
        all_secure = True
        for check_name, is_secure in checks:
            if is_secure:
                print(f"✅ {check_name}: 安全")
            else:
                print(f"⚠️  {check_name}: 需要注意")
                if check_name == 'DEBUG模式' and settings.DEBUG:
                    print("   📝 生产环境请设置 DEBUG=False")
                all_secure = False
        
        return all_secure
        
    except Exception as e:
        print(f"❌ Django settings 检查失败: {e}")
        return False

def main():
    """主函数"""
    print("🔐 API Key 安全性检查工具")
    print("=" * 60)
    
    # 检查硬编码
    no_hardcoded = check_hardcoded_keys()
    
    # 检查环境变量
    env_configured = check_env_config()
    
    # 检查 Django settings
    settings_secure = check_settings_security()
    
    print("\n" + "=" * 60)
    print("📊 检查结果摘要:")
    print(f"{'✅' if no_hardcoded else '❌'} 无硬编码 API Key")
    print(f"{'✅' if env_configured else '❌'} 环境变量配置完整")
    print(f"{'✅' if settings_secure else '⚠️'} Django 设置安全")
    
    if all([no_hardcoded, env_configured, settings_secure]):
        print("\n🎉 所有安全检查通过！")
        return True
    else:
        print("\n⚠️  请修复上述问题以确保 API Key 安全。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)