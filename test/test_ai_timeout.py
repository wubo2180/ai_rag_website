#!/usr/bin/env python
"""
测试AI服务超时修复
"""

import os
import sys
import django

# 添加Django项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ai_service.services import AIService
from django.conf import settings

def test_timeout_configuration():
    """测试超时配置"""
    print("=== 测试AI服务超时配置 ===")
    
    # 初始化AI服务
    ai_service = AIService()
    
    print(f"AI_MODEL_TIMEOUTS配置: {getattr(settings, 'AI_MODEL_TIMEOUTS', {})}")
    
    # 测试不同模型的超时时间
    test_models = ['deepseek深度思考', 'GPT-5', 'Grok-4', '通义千问', '未知模型']
    
    for model in test_models:
        timeout = ai_service._get_model_timeout(model)
        print(f"模型 '{model}' 的超时时间: {timeout}秒")

def test_ai_service():
    """测试AI服务（不实际调用API）"""
    print("\n=== 测试AI服务初始化 ===")
    
    try:
        ai_service = AIService()
        print(f"API Key: {'已配置' if ai_service.api_key else '未配置'}")
        print(f"Base URL: {ai_service.base_url}")
        print(f"默认模型: {ai_service.default_model}")
        print("AI服务初始化成功！")
    except Exception as e:
        print(f"AI服务初始化失败: {e}")

if __name__ == "__main__":
    test_timeout_configuration()
    test_ai_service()
    print("\n测试完成！现在您可以在聊天窗口中测试deepseek深度思考、GPT-5、Grok-4等模型了。")