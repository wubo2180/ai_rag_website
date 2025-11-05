import requests
import json
import os

def upload_file(file_path, user):
    upload_url = "http://172.20.46.18:8088/v1/files/upload"
    headers = {
        "Authorization": "Bearer app-Xomtem4zJ9dkx23GcUbsUpNd",
    }

    try:
        print("上传文件中...")
        with open(file_path, 'rb') as file:
            # 尝试不同的文件上传格式
            files = {
                'file': (os.path.basename(file_path), file, 'text/plain')
            }
            data = {
                "user": user
            }

            response = requests.post(upload_url, headers=headers, files=files, data=data)
            print(f"上传响应状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            
            if response.status_code == 201:  # 201 表示创建成功
                print("文件上传成功")
                return response.json().get("id")  # 获取上传的文件 ID
            elif response.status_code == 200:  # 有时也可能返回200
                print("文件上传成功")
                return response.json().get("id")
            else:
                print(f"文件上传失败，状态码: {response.status_code}")
                print(f"错误详情: {response.text}")
                return None
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return None

def run_workflow(file_id, user, response_mode="blocking"):
    workflow_url = "http://172.20.46.18:8088/v1/workflows/run"
    headers = {
        "Authorization": "Bearer app-Xomtem4zJ9dkx23GcUbsUpNd",
        "Content-Type": "application/json"
    }

    # 尝试简化的输入参数格式
    data = {
        "inputs": {
            "file": {
                "transfer_method": "local_file",
                "upload_file_id": file_id,
                "type": "document"
            }
        },
        "response_mode": response_mode,
        "user": user
    }

    try:
        print("运行工作流...")
        response = requests.post(workflow_url, headers=headers, json=data)
        print(f"工作流响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            print("工作流执行成功")
            return response.json()
        else:
            print(f"工作流执行失败，状态码: {response.status_code}")
            print(f"错误详情: {response.text}")
            return {"status": "error", "message": f"Failed to execute workflow, status code: {response.status_code}"}
    except Exception as e:
        print(f"发生错误: {str(e)}")
        return {"status": "error", "message": str(e)}

# 使用示例
file_path = "E:\\document\\Desktop\\安伯斯\\安伯斯\\高导热加成型有机硅灌封胶的制备研究_李艳飞.pdf"
user = "difyuser"

# 上传文件
file_id = upload_file(file_path, user)
if file_id:
    # 文件上传成功，继续运行工作流
    result = run_workflow(file_id, user)
    print(result)
else:
    print("文件上传失败，无法执行工作流")
