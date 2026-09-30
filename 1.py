import requests
import json

url = "http://172.20.46.18/v1/chat-messages"

headers = {
    "Authorization": "Bearer aapp-FVJbFiVXBkpS8gr3TYyMKSMo", # 替换为你的 API Key
    "Content-Type": "application/json"
}

payload = {
    # 在 inputs 中传入 webSearch 和 Aggregation
    "inputs": {
        "webSearch": "yes",      # 控制联网搜索：yes 或 no
        "Aggregation": "yes"     # 控制聚合模式：yes 或 no
    },
    "query": "What are the specs of the iPhone 13 Pro Max?",
    "response_mode": "streaming",
    "conversation_id": "",
    "user": "abc-123",
    "files": [
        {
            "type": "image",
            "transfer_method": "remote_url",
            "url": "https://cloud.dify.ai/logo/logo-site.png"
        }
    ]
}

try:
    print("正在请求 Dify 应用...")
    response = requests.post(url, headers=headers, json=payload, stream=True)
    response.raise_for_status()

    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith("data: "):
                json_str = decoded_line[6:]
                if json_str == "[DONE]":
                    break
                try:
                    data = json.loads(json_str)
                    # 打印 LLM 回复
                    if "answer" in data:
                        print(data["answer"], end="", flush=True)
                    # 打印工作流节点输出（如果是 Workflow 类型应用）
                    elif "data" in data and "outputs" in data["data"]:
                        print(data["data"]["outputs"], end="", flush=True)
                except json.JSONDecodeError:
                    pass

    print("\n--- 请求结束 ---")

except requests.exceptions.RequestException as e:
    print(f"\n请求出错: {e}")