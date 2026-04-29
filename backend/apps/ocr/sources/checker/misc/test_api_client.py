"""
API 客户端测试脚本
用于测试 REST API 接口
"""
import requests
import os


def test_health():
    """测试健康检查接口"""
    print("=" * 50)
    print("测试健康检查接口")
    print("=" * 50)
    
    url = "http://localhost:6002/health"
    response = requests.get(url)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_analyze_file(file_path: str):
    """测试文件分析接口"""
    print("=" * 50)
    print("测试文件分析接口")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return
    
    url = "http://localhost:6002/api/analyze"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
        data = {
            'user': 'test_user',
            'response_mode': 'blocking'
        }
        
        print(f"上传文件: {os.path.basename(file_path)}")
        response = requests.post(url, files=files, data=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()


def test_upload_and_workflow(file_path: str):
    """测试分步骤处理：先上传文件，再运行工作流"""
    print("=" * 50)
    print("测试分步骤处理")
    print("=" * 50)
    
    if not os.path.exists(file_path):
        print(f"错误: 文件不存在: {file_path}")
        return
    
    # 步骤 1: 上传文件
    print("步骤 1: 上传文件")
    upload_url = "http://localhost:6002/api/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'application/pdf')}
        data = {'user': 'test_user'}
        
        response = requests.post(upload_url, files=files, data=data)
    
    print(f"上传状态码: {response.status_code}")
    upload_result = response.json()
    print(f"上传响应: {upload_result}")
    
    if response.status_code != 200 or upload_result.get('status') != 'success':
        print("文件上传失败，无法继续")
        return
    
    file_id = upload_result.get('file_id')
    print(f"文件 ID: {file_id}")
    print()
    
    # 步骤 2: 运行工作流
    print("步骤 2: 运行工作流")
    workflow_url = "http://localhost:6002/api/workflow/run"
    
    data = {
        'file_id': file_id,
        'user': 'test_user',
        'response_mode': 'blocking'
    }
    
    response = requests.post(workflow_url, data=data)
    
    print(f"工作流状态码: {response.status_code}")
    print(f"工作流响应: {response.json()}")
    print()


if __name__ == "__main__":
    print("Dify 论文分析 API 测试脚本")
    print()
    
    # 测试 1: 健康检查
    try:
        test_health()
    except Exception as e:
        print(f"健康检查失败: {str(e)}")
        print()
    
    # 测试 2: 文件分析（一站式接口）
    test_file = "/home/h3c/workspace/IBoxTech-ocr-paper/doc/双组分缩合型有机硅电子灌封胶的制备及其导热阻燃性能研究_董晓娜.pdf"  # 请修改为实际的测试文件路径
    
    print(f"请确保测试文件存在: {test_file}")
    print("如果没有测试文件，请修改脚本中的 test_file 变量")
    print()
    
    if os.path.exists(test_file):
        try:
            test_analyze_file(test_file)
        except Exception as e:
            print(f"文件分析测试失败: {str(e)}")
            print()
        
        try:
            test_upload_and_workflow(test_file)
        except Exception as e:
            print(f"分步骤处理测试失败: {str(e)}")
            print()
    else:
        print(f"跳过文件测试（文件不存在: {test_file}）")
    
    print("测试完成!")

