import requests
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('../.env')

# 从环境变量读取配置
dataset_api_key = os.getenv('DIFY_DATASET_API_KEY')
base_url = os.getenv('DIFY_DATASET_BASE_URL', 'http://172.20.46.18:8088/v1')

if not dataset_api_key:
    raise ValueError("DIFY_DATASET_API_KEY not found in environment variables")

# 测试 1: 获取特定数据集信息
def test_get_dataset():
    url = f"{base_url}/datasets/fba4f435-1d75-48a8-84b1-4eeb550d2bea"
    headers = {"Authorization": f"Bearer {dataset_api_key}"}
    response = requests.get(url, headers=headers)
    print("Dataset info:", response.json())

# 测试 2: 获取数据集列表
def test_get_datasets():
    url = f"{base_url}/datasets"
    querystring = {"page":"1","limit":"20"}
    headers = {"Authorization": f"Bearer {dataset_api_key}"}
    response = requests.get(url, headers=headers, params=querystring)
    print("Datasets list:", response.json())

# 测试 3: 获取数据集文档
url = f"{base_url}/datasets/fba4f435-1d75-48a8-84b1-4eeb550d2bea/documents"

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('../.env')

querystring = {"page":"1","limit":"20"}

# 从环境变量读取 API key
dataset_api_key = os.getenv('DIFY_DATASET_API_KEY')
if not dataset_api_key:
    raise ValueError("DIFY_DATASET_API_KEY not found in environment variables")

headers = {"Authorization": f"Bearer {dataset_api_key}"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())