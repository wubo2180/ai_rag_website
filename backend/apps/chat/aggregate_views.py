"""
聚合模式：将问题并行发给所有已配置模型，收齐后由 deepseek 流式总结
SSE 事件格式：
  {"stage": "collecting"}                          - 开始并行收集
  {"stage": "model_done", "model": "xx", "content": "..."}  - 某模型完成
  {"stage": "summarizing"}                         - 开始汇总
  {"stage": "answer", "content": "..."}            - 汇总内容 token
  {"stage": "done"}                                - 全部完成
"""

import json
import logging
import threading
import queue
import requests

from django.conf import settings
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .models import ChatSession, ChatMessage

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 同步调用单个 Dify 模型，返回完整文本（阻塞）
# ---------------------------------------------------------------------------

def _call_model_sync(model_name: str, message: str, user_id: str) -> str:
    """同步调用 Dify，收集完整回复文本后返回。失败时返回错误描述。"""
    api_key = getattr(settings, 'DIFY_API_KEY', '')
    api_url = getattr(settings, 'DIFY_API_URL', 'http://localhost:8088/v1')
    model_timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {})
    timeout = model_timeouts.get(model_name, model_timeouts.get('default', 120))

    if not api_key:
        return f'[{model_name}] API 密钥未配置'

    payload = {
        'inputs': {'largeModel': model_name},
        'query': message,
        'user': user_id,
        'response_mode': 'streaming',
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(
            f'{api_url}/chat-messages',
            json=payload,
            headers=headers,
            timeout=timeout,
            stream=True,
        )
        if resp.status_code != 200:
            return f'[{model_name}] 服务错误 ({resp.status_code})'

        collected = []
        for line in resp.iter_lines():
            if not line:
                continue
            text = line.decode('utf-8')
            if not text.startswith('data: '):
                continue
            data_str = text[6:]
            if data_str.strip() == '[DONE]':
                break
            try:
                data = json.loads(data_str)
                event = data.get('event', '')
                if event == 'message' or 'answer' in data:
                    chunk = data.get('answer', '')
                    if chunk:
                        collected.append(chunk)
                elif event == 'message_end':
                    break
                elif event == 'error':
                    return f'[{model_name}] {data.get("message", "未知错误")}'
            except json.JSONDecodeError:
                continue

        result = ''.join(collected).strip()
        return result if result else f'[{model_name}] 未返回有效内容'

    except requests.exceptions.Timeout:
        return f'[{model_name}] 响应超时'
    except Exception as e:
        return f'[{model_name}] 请求异常: {str(e)}'


# ---------------------------------------------------------------------------
# 流式调用 deepseek 进行汇总
# ---------------------------------------------------------------------------

def _build_summary_prompt(original_question: str, model_answers: dict) -> str:
    answers_text = '\n\n'.join(
        f'【{model}】\n{answer}' for model, answer in model_answers.items()
    )
    return (
        f'你是一个专业的答案整合专家。多个 AI 模型分别回答了同一个问题，'
        f'请综合所有回答，给出一个最准确、最全面、条理最清晰的最终答案。\n\n'
        f'【用户问题】\n{original_question}\n\n'
        f'【各模型回答】\n{answers_text}\n\n'
        f'【要求】\n'
        f'1. 综合所有模型的优质信息，去除重复和错误内容\n'
        f'2. 用清晰的结构呈现最终答案\n'
        f'3. 如果各模型有分歧，说明分歧点并给出判断\n'
        f'4. 直接输出最终答案，不要说"根据以上模型..."之类的引导语\n\n'
        f'【最终答案】'
    )


def _stream_summary(prompt: str, user_id: str):
    """生成器：流式调用 deepseek 汇总，逐 token yield 文本片段"""
    api_key = getattr(settings, 'DIFY_API_KEY', '')
    api_url = getattr(settings, 'DIFY_API_URL', 'http://localhost:8088/v1')
    timeout = getattr(settings, 'AI_MODEL_TIMEOUTS', {}).get('deepseek深度思考', 300)

    payload = {
        'inputs': {'largeModel': 'deepseek深度思考'},
        'query': prompt,
        'user': user_id,
        'response_mode': 'streaming',
    }
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }

    try:
        resp = requests.post(
            f'{api_url}/chat-messages',
            json=payload,
            headers=headers,
            timeout=timeout,
            stream=True,
        )
        if resp.status_code != 200:
            yield f'汇总服务错误 ({resp.status_code})'
            return

        for line in resp.iter_lines():
            if not line:
                continue
            text = line.decode('utf-8')
            if not text.startswith('data: '):
                continue
            data_str = text[6:]
            if data_str.strip() == '[DONE]':
                break
            try:
                data = json.loads(data_str)
                event = data.get('event', '')
                if event == 'message' or 'answer' in data:
                    chunk = data.get('answer', '')
                    if chunk:
                        yield chunk
                elif event == 'message_end':
                    break
                elif event == 'error':
                    yield f'\n[汇总出错: {data.get("message", "未知")}]'
                    return
            except json.JSONDecodeError:
                continue

    except requests.exceptions.Timeout:
        yield '\n[汇总超时，请稍后重试]'
    except Exception as e:
        yield f'\n[汇总异常: {str(e)}]'


# ---------------------------------------------------------------------------
# 主视图
# ---------------------------------------------------------------------------

class AggregateStreamAPIView(APIView):
    """
    聚合模式流式接口
    POST /api/chat/aggregate/stream/
    Body: { "message": "...", "user_id": "...", "session_id": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        message = request.data.get('message', '').strip()
        user_id = request.data.get('user_id', 'web_anonymous')
        session_id = request.data.get('session_id')

        if not message:
            def _err():
                yield f"data: {json.dumps({'error': '消息不能为空'}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingHttpResponse(_err(), content_type='text/event-stream')

        # 获取或创建会话
        user = request.user if request.user.is_authenticated else None
        try:
            if session_id:
                session = ChatSession.objects.get(id=session_id)
            else:
                title = message[:50] + ('...' if len(message) > 50 else '')
                session = ChatSession.objects.create(user=user, title=title)
        except ChatSession.DoesNotExist:
            title = message[:50] + ('...' if len(message) > 50 else '')
            session = ChatSession.objects.create(user=user, title=title)

        # 保存用户消息
        ChatMessage.objects.create(session=session, content=message, is_user=True)

        resp = StreamingHttpResponse(
            self._generate(message, user_id, session),
            content_type='text/event-stream; charset=utf-8',
        )
        resp['Cache-Control'] = 'no-cache'
        resp['X-Accel-Buffering'] = 'no'
        resp['Access-Control-Allow-Origin'] = '*'
        return resp

    def _generate(self, message: str, user_id: str, session):
        """主生成器：并行收集 → 流式汇总"""

        # ---- 1. 通知前端开始并行收集 ----
        yield f"data: {json.dumps({'stage': 'collecting', 'session_id': str(session.id)}, ensure_ascii=False)}\n\n"

        # ---- 2. 并行调用所有模型（线程池） ----
        models = getattr(settings, 'AVAILABLE_AI_MODELS', ['deepseek深度思考'])
        result_queue = queue.Queue()

        def worker(model_name):
            answer = _call_model_sync(model_name, message, user_id)
            result_queue.put((model_name, answer))

        threads = [threading.Thread(target=worker, args=(m,), daemon=True) for m in models]
        for t in threads:
            t.start()

        # 等待所有线程完成，收到一个就立即推送给前端
        model_answers = {}
        for _ in models:
            model_name, answer = result_queue.get()
            model_answers[model_name] = answer
            payload = {
                'stage': 'model_done',
                'model': model_name,
                'content': answer,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        for t in threads:
            t.join()

        # ---- 3. 通知前端开始汇总 ----
        yield f"data: {json.dumps({'stage': 'summarizing'}, ensure_ascii=False)}\n\n"

        # ---- 4. 流式汇总 ----
        summary_prompt = _build_summary_prompt(message, model_answers)
        full_summary = []
        for chunk in _stream_summary(summary_prompt, user_id):
            full_summary.append(chunk)
            yield f"data: {json.dumps({'stage': 'answer', 'content': chunk}, ensure_ascii=False)}\n\n"

        # ---- 5. 保存 AI 汇总消息到数据库 ----
        summary_text = ''.join(full_summary)
        ai_message = None
        if summary_text:
            ai_message = ChatMessage.objects.create(
                session=session,
                content=summary_text,
                is_user=False,
            )

        # ---- 6. 完成 ----
        done_payload = {
            'stage': 'done',
            'done': True,
            'session_id': str(session.id),
        }
        if ai_message:
            done_payload['message_id'] = str(ai_message.id)
        yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

        logger.info(f'✅ 聚合模式完成, session={session.id}, 汇总长度={len(summary_text)}')
