"""
AI service module - clean implementation to call Dify with optional web_search.

Provides:
- `ai_service.generate_response(...)` synchronous wrapper that collects the full answer
- `ai_service.generate_response_stream(...)` generator that yields streaming chunks

The implementation is defensive and only forwards `web_search` into the `inputs`
payload when set to True.
"""
import json
import logging
from typing import Generator, Optional

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.api_key = getattr(settings, 'DIFY_API_KEY', '')
        self.base_url = getattr(settings, 'DIFY_API_URL', '').rstrip('/')

    def _get_model_timeout(self, model: Optional[str]) -> int:
        timeouts = getattr(settings, 'AI_MODEL_TIMEOUTS', {}) or {}
        return int(timeouts.get(model, timeouts.get('default', 90)))

    def generate_response(self, message: str, user_id: str = "default_user", session_id: Optional[str] = None, model: Optional[str] = None, web_search: bool = False) -> dict:
        """Synchronous response: collect full result from streaming endpoint."""
        try:
            resp = self._call_dify_api_streaming(message, user_id, session_id, model, web_search=web_search)
            return {
                'success': True,
                'response': resp.get('answer', ''),
                'conversation_id': resp.get('conversation_id'),
                'message_id': resp.get('message_id'),
                'model': None,
            }
        except Exception as e:
            logger.exception("AI service synchronous call failed")
            return {
                'success': False,
                'error': str(e),
                'response': f'抱歉，AI服务暂时不可用。错误信息：{str(e)}'
            }

    def generate_response_stream(self, message: str, user_id: str = "default_user", session_id: Optional[str] = None, model: Optional[str] = None, web_search: bool = False) -> Generator[dict, None, None]:
        """Yield streaming chunks from Dify. Each yielded dict contains keys like `content`, `done`, and optional ids."""
        timeout = self._get_model_timeout(None)
        url = f"{self.base_url}/chat-messages"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'query': message,
            'response_mode': 'streaming',
            'user': user_id,
        }

        # inputs always exists to allow adding flags
        inputs = {}
        inputs['webSearch'] = 'yes' if web_search else 'no'
        inputs['Aggregation'] = 'no'
        if inputs:
            payload['inputs'] = inputs

        if session_id and session_id.strip():
            payload['conversation_id'] = session_id

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)
        except requests.exceptions.Timeout:
            logger.exception("Dify API request timed out")
            yield {'content': 'AI 服务响应超时，请稍后再试', 'done': True, 'error': True}
            return
        except Exception as e:
            logger.exception("Dify API request failed")
            yield {'content': f'请求异常: {str(e)}', 'done': True, 'error': True}
            return

        if response.status_code != 200:
            logger.error("Dify API error: %s", response.text)
            yield {'content': f'AI服务错误: {response.text}', 'done': True, 'error': True}
            return

        conversation_id = None
        message_id = None

        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            try:
                line_text = raw_line.decode('utf-8')
            except Exception:
                line_text = raw_line.decode('utf-8', errors='ignore')

            if not line_text.startswith('data: '):
                continue

            try:
                data = json.loads(line_text[6:])
            except json.JSONDecodeError:
                logger.warning('Failed to decode SSE payload: %s', line_text)
                continue

            event = data.get('event', '')

            if event == 'message':
                conversation_id = data.get('conversation_id') or conversation_id
                message_id = data.get('message_id') or message_id
                yield {
                    'content': data.get('answer', ''),
                    'done': False,
                    'conversation_id': conversation_id,
                    'message_id': message_id
                }

            elif event == 'message_end':
                conversation_id = data.get('conversation_id') or conversation_id
                message_id = data.get('message_id') or message_id
                yield {
                    'content': '',
                    'done': True,
                    'conversation_id': conversation_id,
                    'message_id': message_id,
                    'metadata': data.get('metadata', {})
                }
                return

            elif event == 'error':
                yield {'content': data.get('message', '未知错误'), 'done': True, 'error': True}
                return

        # If stream ends without explicit message_end, finalize
        yield {'content': '', 'done': True, 'conversation_id': conversation_id, 'message_id': message_id}

    def _call_dify_api_streaming(self, message: str, user_id: str, session_id: Optional[str], model: str, web_search: bool = False) -> dict:
        """Call Dify streaming API and collect full answer. Raises exceptions on errors."""
        timeout = self._get_model_timeout(None)
        url = f"{self.base_url}/chat-messages"

        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            'query': message,
            'response_mode': 'streaming',
            'user': user_id,
        }

        inputs = {}
        inputs['webSearch'] = 'yes' if web_search else 'no'
        inputs['Aggregation'] = 'no'
        if inputs:
            payload['inputs'] = inputs

        if session_id and session_id.strip():
            payload['conversation_id'] = session_id

        logger.info('Calling Dify API %s without model override, timeout=%s', url, timeout)

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=timeout, stream=True)
        except requests.exceptions.Timeout:
            logger.exception('Dify API timeout')
            raise Exception('AI 服务响应超时，请稍后再试')
        except Exception as e:
            logger.exception('Dify API connection failed')
            raise Exception(f'无法连接到 AI 服务: {e}')

        if response.status_code != 200:
            logger.error('Dify API returned non-200: %s', response.text)
            raise Exception(f'Dify API 错误 ({response.status_code}): {response.text}')

        full_answer = ''
        conversation_id = None
        message_id = None

        for raw_line in response.iter_lines():
            if not raw_line:
                continue
            try:
                line_text = raw_line.decode('utf-8')
            except Exception:
                line_text = raw_line.decode('utf-8', errors='ignore')

            if not line_text.startswith('data: '):
                continue

            try:
                data = json.loads(line_text[6:])
            except json.JSONDecodeError:
                logger.warning('Failed to parse SSE chunk: %s', line_text)
                continue

            event = data.get('event', '')

            if event == 'message':
                full_answer += data.get('answer', '')
                conversation_id = data.get('conversation_id') or conversation_id
                message_id = data.get('message_id') or message_id

            elif event == 'message_end':
                conversation_id = data.get('conversation_id') or conversation_id
                message_id = data.get('message_id') or message_id
                break

            elif event == 'error':
                raise Exception(data.get('message', '未知错误'))

        logger.info('Collected full answer length=%d', len(full_answer))
        return {'answer': full_answer, 'conversation_id': conversation_id, 'message_id': message_id}

    def get_available_models(self):
        return getattr(settings, 'AVAILABLE_AI_MODELS', [
            'deepseek深度思考',
            '通义千问',
            '腾讯混元',
            '豆包',
            'Kimi',
            'GPT-5',
            'Claude4',
            'Gemini2.5',
            'Grok-4',
            'Llama4'
        ])


# global instance
ai_service = AIService()