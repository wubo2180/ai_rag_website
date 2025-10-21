import requests

# 测试知识库列表API
def test_datasets_list():
    url = "http://172.20.46.18:8088/v1/datasets"
    headers = {"Authorization": "Bearer dataset-XGhjOXFbkSkJqagNLbs0SDEy"}
    querystring = {"page": "1", "limit": "20"}
    
    print("🔍 测试知识库列表API...")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Params: {querystring}")
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"📡 状态码: {response.status_code}")
        print(f"📄 响应内容: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功！找到 {data.get('total', 0)} 个知识库")
            return data
        else:
            print(f"❌ 失败：{response.status_code}")
            return None
            
    except Exception as e:
        print(f"💥 错误: {e}")
        return None

# 测试文档列表API
def test_documents_list():
    dataset_id = "fba4f435-1d75-48a8-84b1-4eeb550d2bea"  # 用户提供的知识库ID
    url = f"http://172.20.46.18:8088/v1/datasets/{dataset_id}/documents"
    headers = {"Authorization": "Bearer dataset-XGhjOXFbkSkJqagNLbs0SDEy"}
    querystring = {"page": "1", "limit": "20"}
    
    print(f"\n🔍 测试文档列表API (知识库: {dataset_id})...")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        print(f"📡 状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功！找到 {data.get('total', 0)} 个文档")
            print(f"📊 文档列表: {[doc['name'] for doc in data.get('data', [])]}")
            return data
        else:
            print(f"❌ 失败：{response.status_code}")
            print(f"📄 响应内容: {response.text[:500]}...")
            return None
            
    except Exception as e:
        print(f"💥 错误: {e}")
        return None

if __name__ == "__main__":
    datasets = test_datasets_list()
    documents = test_documents_list()