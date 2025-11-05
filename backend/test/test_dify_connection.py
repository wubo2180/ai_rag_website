"""
测试Dify API连接的脚本
"""

import os
import sys
import django

# 设置Django环境
sys.path.append('/e/document/python_workspace/ai_rag_website/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.ai_service.dify_service import dify_service

def test_dify_connection():
    """测试Dify连接"""
    print("🔗 测试Dify API连接...")
    
    # 创建测试文件
    test_content = "这是一个测试文档，用于验证Dify API连接和工作流处理功能。\n\n材料科学测试数据：\n- 材料类型：复合材料\n- 密度：2.5 g/cm³\n- 强度：350 MPa"
    
    try:
        # 测试文件上传
        print("📁 测试文件上传...")
        file_id = dify_service.upload_file_from_memory(
            file_data=test_content.encode('utf-8'),
            filename="test_material_data.txt",
            user="test_user"
        )
        
        if file_id:
            print(f"✅ 文件上传成功，ID: {file_id}")
            
            # 测试工作流执行
            print("⚙️ 测试工作流执行...")
            result = dify_service.run_workflow(file_id, "test_user")
            
            if result.get('status') == 'success':
                print("✅ 工作流执行成功!")
                print("📊 结果预览:")
                data = result.get('data', {})
                if 'data' in data and 'outputs' in data['data']:
                    outputs = data['data']['outputs']
                    if 'text' in outputs:
                        print(f"输出内容: {outputs['text'][:200]}...")
                else:
                    print("结果格式:", result)
            else:
                print(f"❌ 工作流执行失败: {result.get('message')}")
                
        else:
            print("❌ 文件上传失败")
            
    except Exception as e:
        print(f"❌ 连接测试异常: {str(e)}")

if __name__ == "__main__":
    test_dify_connection()