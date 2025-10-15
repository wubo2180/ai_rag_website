from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests
import json
import time
import re

app = Flask(__name__)
CORS(app)

# API配置
API_URL = "http://11652fb8.r15.vip.cpolar.cn/v1/chat-messages"
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
    """生成流式响应"""
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
        
        # 尝试调用外部API
        try:
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=request_body,
                timeout=5,
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
                return
        except Exception as e:
            print(f"外部API调用失败: {e}")
        
        # 如果外部API失败，使用本地模拟流式响应
        local_response = get_local_response(message, model, deep_thinking)
        
        # 模拟流式输出，逐字符发送
        for i in range(0, len(local_response), 3):  # 每次发送3个字符
            chunk = local_response[i:i+3]
            yield f"data: {json.dumps({'content': chunk})}\n\n"
            time.sleep(0.05)  # 模拟网络延迟
        
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        error_msg = f"生成响应时发生错误: {str(e)}"
        yield f"data: {json.dumps({'content': error_msg})}\n\n"
        yield "data: [DONE]\n\n"

def get_local_response(message, model, deep_thinking=True):
    """本地模拟AI回复"""
    import random
    
    # 根据消息内容生成不同类型的回复
    message_lower = message.lower()
    
    if any(word in message_lower for word in ['你好', 'hello', 'hi', '您好']):
        responses = [
            f"你好！我是{MODEL_MAPPING.get(model, 'AI助手')}，很高兴为您服务！有什么我可以帮助您的吗？",
            f"您好！我是基于{MODEL_MAPPING.get(model, 'AI')}的智能助手，请问有什么问题需要我帮助解答吗？",
            f"Hi！我是{MODEL_MAPPING.get(model, 'AI助手')}，随时为您提供帮助。请告诉我您想了解什么？"
        ]
    elif any(word in message_lower for word in ['谢谢', 'thank', '感谢']):
        responses = [
            "不客气！很高兴能帮助到您。如果还有其他问题，随时可以问我。",
            "您太客气了！这是我应该做的。还有什么其他需要帮助的吗？",
            "不用谢！能为您提供帮助是我的荣幸。"
        ]
    elif any(word in message_lower for word in ['再见', 'bye', '拜拜']):
        responses = [
            "再见！祝您生活愉快，有需要随时找我聊天！",
            "拜拜！期待下次为您服务！",
            "再见！希望我们的对话对您有所帮助。"
        ]
    elif '?' in message or '？' in message:
        responses = [
            f"这是一个很好的问题！基于{MODEL_MAPPING.get(model, 'AI')}的分析，我认为这个问题涉及多个方面。让我为您详细解答一下...",
            f"感谢您的提问！作为{MODEL_MAPPING.get(model, 'AI助手')}，我很乐意为您解答这个问题。",
            f"您提出了一个非常有趣的问题！让我用{MODEL_MAPPING.get(model, 'AI')}的能力来为您分析一下。"
        ]
    else:
        responses = [
            f"我理解您的意思。作为{MODEL_MAPPING.get(model, 'AI助手')}，我会尽力为您提供有用的信息和建议。",
            f"这是一个很有意思的话题！基于{MODEL_MAPPING.get(model, 'AI')}的知识库，我可以为您提供一些见解。",
            f"感谢您与我分享这个内容。让我用{MODEL_MAPPING.get(model, 'AI')}的能力来为您提供一些有价值的回应。",
            f"您说得很对！作为{MODEL_MAPPING.get(model, 'AI助手')}，我认为这个话题确实值得深入探讨。"
        ]
    
    # 如果启用深度思考，添加更详细的内容
    if deep_thinking:
        base_response = random.choice(responses)
        additional_content = [
            "\n\n经过深度思考，我还想补充几点：\n1. 这个问题可能涉及多个层面的考虑\n2. 建议您从不同角度来看待这个问题\n3. 如果需要更具体的建议，请提供更多详细信息",
            "\n\n通过深度分析，我发现：\n• 这个话题确实很有价值\n• 可能需要结合实际情况来判断\n• 我建议您可以进一步探索相关资源",
            "\n\n深度思考后，我的建议是：\n→ 保持开放的心态\n→ 多角度思考问题\n→ 如有疑问随时与我交流"
        ]
        return base_response + random.choice(additional_content)
    
    return random.choice(responses)

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