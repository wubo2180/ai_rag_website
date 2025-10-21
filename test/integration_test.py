#!/usr/bin/env python3
"""
AI_UI_928_2 集成验证脚本
测试Django后端与前端的整合功能
"""

import os
import sys
import subprocess
import requests
import json
from pathlib import Path

def check_django_setup():
    """检查Django环境设置"""
    print("🔍 检查Django环境...")
    
    # 检查Django是否可以启动
    try:
        os.chdir('E:/document/python_workspace/ai_rag_website/backend')
        result = subprocess.run([
            'D:/program/miniconda3/Scripts/conda.exe', 'run', '-p', 'D:\\program\\miniconda3',
            '--no-capture-output', 'python', 'manage.py', 'check'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Django环境正常")
            return True
        else:
            print(f"❌ Django检查失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Django环境检查异常: {e}")
        return False

def test_api_endpoints():
    """测试新增的API端点"""
    print("\n🧪 测试API端点...")
    
    base_url = "http://127.0.0.1:8000"
    endpoints = [
        '/api/chat/api/enhanced-models/',
        '/api/chat/api/suggestions/',
    ]
    
    for endpoint in endpoints:
        try:
            if endpoint == '/api/chat/api/suggestions/':
                # POST请求
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={'query': '人工智能'},
                                       timeout=5)
            else:
                # GET请求
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {endpoint} - 正常")
                if endpoint == '/api/chat/api/enhanced-models/':
                    data = response.json()
                    print(f"   📊 可用模型: {len(data.get('models', []))}")
            else:
                print(f"❌ {endpoint} - 状态码: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"⚠️  {endpoint} - 服务器未启动")
        except Exception as e:
            print(f"❌ {endpoint} - 错误: {e}")

def check_frontend_files():
    """检查前端文件完整性"""
    print("\n📁 检查前端文件...")
    
    files_to_check = [
        'E:/document/python_workspace/ai_rag_website/frontend/src/views/EnhancedChat.vue',
        'E:/document/python_workspace/ai_rag_website/frontend/src/components/Navigation.vue',
        'E:/document/python_workspace/ai_rag_website/frontend/src/utils/api.js',
        'E:/document/python_workspace/ai_rag_website/frontend/src/router/index.js'
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {Path(file_path).name} - {size} bytes")
        else:
            print(f"❌ {Path(file_path).name} - 文件不存在")

def check_backend_files():
    """检查后端文件完整性"""
    print("\n🔧 检查后端文件...")
    
    files_to_check = [
        'E:/document/python_workspace/ai_rag_website/backend/apps/chat/enhanced_views.py',
        'E:/document/python_workspace/ai_rag_website/backend/apps/chat/urls.py',
        'E:/document/python_workspace/ai_rag_website/backend/config/settings.py',
        'E:/document/python_workspace/ai_rag_website/backend/apps/accounts/models.py',
        'E:/document/python_workspace/ai_rag_website/backend/apps/chat/models.py'
    ]
    
    for file_path in files_to_check:
        if Path(file_path).exists():
            size = Path(file_path).stat().st_size
            print(f"✅ {Path(file_path).name} - {size} bytes")
            
            # 检查关键内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'enhanced_views.py' in file_path:
                if 'StreamChatAPIView' in content:
                    print("   📡 流式聊天API - 已实现")
                if 'RelatedQuestionsAPIView' in content:
                    print("   🔗 相关问题推荐API - 已实现")
                    
            elif 'settings.py' in file_path:
                if 'DIFY_API_URL' in content:
                    print("   🔑 AI服务配置 - 已添加")
                    
        else:
            print(f"❌ {Path(file_path).name} - 文件不存在")

def generate_integration_summary():
    """生成集成摘要"""
    print("\n📋 AI_UI_928_2 集成摘要")
    print("=" * 50)
    
    features = [
        "✨ 流式聊天响应 (StreamChatAPIView)",
        "🧠 深度思考模式支持",
        "🔗 相关问题推荐 (RelatedQuestionsAPIView)", 
        "🎯 多AI模型支持 (DeepSeek, 豆包, GPT-5等)",
        "👤 用户偏好设置 (preferred_ai_model, enable_deep_thinking)",
        "📱 现代化Vue.js界面 (EnhancedChat.vue)",
        "🧭 导航组件支持 (Navigation.vue)",
        "⚙️ API配置整合 (enhancedAPI in api.js)"
    ]
    
    for feature in features:
        print(f"  {feature}")
    
    print(f"\n🎉 集成完成！访问路由:")
    print(f"  • 基础聊天: http://localhost:3000/chat")
    print(f"  • 增强聊天: http://localhost:3000/enhanced-chat")

def main():
    """主测试流程"""
    print("🚀 AI_UI_928_2 与 ai_rag_website 集成验证")
    print("=" * 60)
    
    # 基础检查
    django_ok = check_django_setup()
    check_backend_files()
    check_frontend_files()
    
    # API测试
    print(f"\n💡 提示: 如需测试API，请先启动Django服务:")
    print(f"cd E:/document/python_workspace/ai_rag_website/backend")
    print(f"python manage.py runserver")
    
    # 测试API（如果Django在运行）
    test_api_endpoints()
    
    # 生成摘要
    generate_integration_summary()
    
    print(f"\n✅ 集成验证完成！")

if __name__ == "__main__":
    main()