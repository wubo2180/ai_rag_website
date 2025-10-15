from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import json
import re

app = Flask(__name__)
CORS(app)

# API配置
API_URL = "http://744149f.r31.cpolar.top/v1/chat-messages"
API_KEY = "app-K9fjgkD8JbNrNfTH2ECIv4jw"

# 模型映射
MODEL_MAPPING = {
    'deepseek': 'deepseek深度思考',
    'doubao': '豆包',
    'gpt5': 'GPT-5'
}

def get_related_questions(query):
    """通过百度API获取相关问题推荐"""
    if not query:
        return []
    try:
        url = f"https://suggestion.baidu.com/su?wd={query}&p=3&cb=window.bdsug.sug"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        match = re.search(r's:(\[.*?\])', response.text)
        if match:
            suggestions = json.loads(match.group(1))
            filtered = [s for s in suggestions if s and s.lower().strip() != query.lower().strip()]
            return filtered[:3]
    except Exception as e:
        print(f"获取相关问题时出错: {e}")
    return ["你还想了解什么？", "需要更多帮助吗？", "有其他问题吗？"]

def generate_stream_response(message, model, deep_thinking=True):
    """生成流式响应 - 仅使用真实AI API"""
    try:
        if model == 'deepseek' and deep_thinking:
            large_model = 'deepseek深度思考'
        else:
            large_model = MODEL_MAPPING.get(model, 'deepseek深度思考')
        
        request_body = {
            "inputs": {
                "largeModel": large_model
            },
            "query": message,
            "user": "user_001",
            "response_mode": "streaming",
            "conversation_id": "",
            "files": []
        }
        
        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/json'
        }
        
        # 调用外部API
        response = requests.post(
            API_URL, 
            headers=headers, 
            json=request_body,
            timeout=30,
            stream=True
        )
        
        if response.status_code == 200:
            # 处理外部API的流式响应
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if 'answer' in data:
                                yield f"data: {json.dumps({'content': data['answer']})}\n\n"
                        except json.JSONDecodeError:
                            continue
            yield "data: [DONE]\n\n"
        else:
            # API调用失败，返回友好的错误信息
            if response.status_code == 502:
                error_msg = "抱歉，AI服务暂时不可用，请稍后重试。"
            elif response.status_code == 401:
                error_msg = "API密钥验证失败，请检查配置。"
            elif response.status_code == 429:
                error_msg = "请求过于频繁，请稍后重试。"
            else:
                error_msg = f"AI服务暂时不可用（错误代码: {response.status_code}），请稍后重试。"
            yield f"data: {json.dumps({'content': error_msg})}\n\n"
            yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_msg = f"API调用出错: {str(e)}"
        yield f"data: {json.dumps({'content': error_msg})}\n\n"
        yield "data: [DONE]\n\n"

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data.get('message', '')
    model = data.get('model', 'deepseek')
    deep_thinking = data.get('deep_thinking', True)
    
    return Response(
        generate_stream_response(message, model, deep_thinking),
        mimetype='text/plain',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'POST'
        }
    )

@app.route('/api/related-questions', methods=['POST'])
def related_questions():
    data = request.get_json()
    message = data.get('message', '')
    
    questions = get_related_questions(message)
    
    return jsonify({
        'related_questions': questions
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)