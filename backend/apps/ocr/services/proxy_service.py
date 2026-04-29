import requests

from .commission_local_service import CommissionLocalService
from .config import get_service_base_urls, get_timeout
from .checker_local_service import CheckerLocalService
from .paper_local_service import PaperLocalService


class OcrProxyService:
    def __init__(self):
        self.upstreams = get_service_base_urls()
        self.timeout = get_timeout()
        self.commission_local_service = CommissionLocalService()
        self.paper_local_service = PaperLocalService()
        self.checker_local_service = CheckerLocalService()
        self.local_services = {
            'commission': self.commission_local_service,
            'paper': self.paper_local_service,
            'checker': self.checker_local_service,
        }

    @staticmethod
    def filter_headers(request):
        headers = {}
        content_type = request.META.get('CONTENT_TYPE')
        if content_type:
            headers['Content-Type'] = content_type

        auth = request.META.get('HTTP_AUTHORIZATION')
        if auth:
            headers['Authorization'] = auth

        return headers

    def health(self):
        result = {
            'status': 'ok',
            'service': 'django-ocr-proxy',
            'upstreams': {},
        }

        has_down = False
        for name, base_url in self.upstreams.items():
            if name in self.local_services:
                local_health = self.local_services[name].health()
                is_ok = local_health.get('status') == 'ok'
                if is_ok:
                    result['upstreams'][name] = {
                        'status': 'ok',
                        'mode': local_health.get('mode', 'local-in-django'),
                        'detail': local_health,
                    }
                    continue

            url = f"{base_url}/health"
            try:
                resp = requests.get(url, timeout=self.timeout)
                ok = 200 <= resp.status_code < 300
                result['upstreams'][name] = {
                    'status': 'ok' if ok else 'down',
                    'base_url': base_url,
                    'health_url': url,
                    'http_status': resp.status_code,
                }
                if not ok:
                    has_down = True
            except requests.RequestException as exc:
                has_down = True
                result['upstreams'][name] = {
                    'status': 'down',
                    'base_url': base_url,
                    'health_url': url,
                    'detail': str(exc),
                }

                if name in self.local_services:
                    result['upstreams'][name]['mode'] = 'local-failed-upstream-failed'
                    result['upstreams'][name]['local_detail'] = local_health

        if has_down:
            result['status'] = 'degraded'

        return result

    def service_health(self, service: str):
        service = (service or '').strip().lower()
        if service not in self.upstreams:
            return {
                'ok': False,
                'status_code': 404,
                'body': {
                    'status': 'error',
                    'message': f'不支持的OCR服务: {service}',
                    'service': service,
                },
            }

        if service in self.local_services:
            local_health = self.local_services[service].health()
            is_ok = local_health.get('status') == 'ok'
            if not is_ok:
                base_url = self.upstreams[service]
                health_url = f"{base_url}/health"
                try:
                    resp = requests.get(health_url, timeout=self.timeout)
                    if 200 <= resp.status_code < 300:
                        payload = None
                        try:
                            payload = resp.json()
                        except ValueError:
                            payload = {'raw': resp.text}
                        return {
                            'ok': True,
                            'status_code': 200,
                            'body': {
                                'status': 'ok',
                                'service': service,
                                'mode': 'upstream-fallback',
                                'message': f'{service} 本地模式不可用，已回退到上游服务',
                                'local_detail': local_health,
                                'upstream': base_url,
                                'health_url': health_url,
                                'upstream_status': resp.status_code,
                                'upstream_payload': payload,
                            },
                        }
                except requests.RequestException:
                    pass

            return {
                'ok': is_ok,
                'status_code': 200,
                'body': {
                    'status': 'ok' if is_ok else 'down',
                    'service': service,
                    'mode': local_health.get('mode', 'local-in-django'),
                    'message': local_health.get('message'),
                    'detail': local_health,
                },
            }

        base_url = self.upstreams[service]
        health_url = f"{base_url}/health"
        try:
            resp = requests.get(health_url, timeout=self.timeout)
            if 200 <= resp.status_code < 300:
                payload = None
                try:
                    payload = resp.json()
                except ValueError:
                    payload = {'raw': resp.text}
                return {
                    'ok': True,
                    'status_code': 200,
                    'body': {
                        'status': 'ok',
                        'service': service,
                        'upstream': base_url,
                        'health_url': health_url,
                        'upstream_status': resp.status_code,
                        'upstream_payload': payload,
                    },
                }

            return {
                'ok': False,
                'status_code': 200,
                'body': {
                    'status': 'down',
                    'service': service,
                    'upstream': base_url,
                    'health_url': health_url,
                    'upstream_status': resp.status_code,
                    'message': '上游服务返回非成功状态码',
                },
            }
        except requests.RequestException as exc:
            return {
                'ok': False,
                'status_code': 200,
                'body': {
                    'status': 'down',
                    'service': service,
                    'upstream': base_url,
                    'health_url': health_url,
                    'message': '上游服务不可达',
                    'detail': str(exc),
                },
            }

    def query_task_status(self, task_id: str, preferred_service: str, request):
        if preferred_service and preferred_service in self.upstreams:
            service_order = [preferred_service]
        else:
            service_order = ['checker', 'commission', 'paper']

        probe_paths = [
            f'tasks/{task_id}',
            f'task/{task_id}',
            f'api/tasks/{task_id}',
            f'api/task/{task_id}',
            f'files/ocr/task/{task_id}',
            f'api/files/ocr/task/{task_id}',
        ]

        trace = []
        for service in service_order:
            base_url = self.upstreams.get(service)
            if not base_url:
                continue

            if service in self.local_services:
                for probe_path in probe_paths:
                    try:
                        local_result = self.local_services[service].proxy(request, probe_path)
                        if local_result is None:
                            continue

                        trace.append({
                            'service': service,
                            'url': f'local://{service}/{probe_path}',
                            'status': local_result.get('status_code'),
                            'mode': 'local-in-django',
                        })

                        status_code = local_result.get('status_code', 500)
                        if 200 <= status_code < 300 and 'body' in local_result:
                            return {
                                'ok': True,
                                'status_code': 200,
                                'body': {
                                    'status': 'success',
                                    'task_id': task_id,
                                    'service': service,
                                    'upstream_url': f'local://{service}/{probe_path}',
                                    'data': local_result.get('body'),
                                    'trace': trace,
                                },
                            }
                    except Exception as exc:
                        trace.append({
                            'service': service,
                            'url': f'local://{service}/{probe_path}',
                            'status': 'error',
                            'mode': 'local-in-django',
                            'detail': str(exc),
                        })

            for probe_path in probe_paths:
                target_url = f"{base_url}/{probe_path}"
                try:
                    resp = requests.get(
                        target_url,
                        headers=self.filter_headers(request),
                        timeout=self.timeout,
                    )
                    trace.append({'service': service, 'url': target_url, 'status': resp.status_code})
                    if 200 <= resp.status_code < 300:
                        try:
                            payload = resp.json()
                        except ValueError:
                            payload = {'raw': resp.text}
                        return {
                            'ok': True,
                            'status_code': 200,
                            'body': {
                                'status': 'success',
                                'task_id': task_id,
                                'service': service,
                                'upstream_url': target_url,
                                'data': payload,
                                'trace': trace,
                            },
                        }
                except requests.RequestException as exc:
                    trace.append({'service': service, 'url': target_url, 'status': 'error', 'detail': str(exc)})

        return {
            'ok': False,
            'status_code': 404,
            'body': {
                'status': 'error',
                'message': '未找到任务状态或上游OCR服务不可达',
                'task_id': task_id,
                'trace': trace,
            },
        }

    def proxy(self, request, service: str, path: str):
        service = (service or '').strip().lower()
        if service not in self.upstreams:
            return {
                'ok': False,
                'status_code': 404,
                'body': {'status': 'error', 'message': f'不支持的OCR服务: {service}'},
            }

        if service in self.local_services:
            local_result = self.local_services[service].proxy(request, path)
            if local_result is not None:
                if local_result.get('status_code', 500) >= 500:
                    # 本地模式失败时，回退到上游 HTTP 代理
                    pass
                elif 'raw_body' in local_result:
                    return {
                        'ok': True,
                        'is_local': True,
                        'local_status_code': local_result['status_code'],
                        'local_raw_body': local_result.get('raw_body', b''),
                        'local_content_type': local_result.get('content_type', 'application/octet-stream'),
                    }
                elif 'body' in local_result:
                    return {
                        'ok': True,
                        'is_local': True,
                        'local_status_code': local_result['status_code'],
                        'local_body': local_result['body'],
                        'local_content_type': local_result.get('content_type', 'application/json'),
                    }

                local_error_body = local_result.get('body', {})
            else:
                local_error_body = None

            base_url = f"{self.upstreams[service]}/{path.lstrip('/')}"
            query = request.META.get('QUERY_STRING')
            target_url = f"{base_url}?{query}" if query else base_url
            try:
                resp = requests.request(
                    method=request.method,
                    url=target_url,
                    headers=self.filter_headers(request),
                    data=request.body or None,
                    timeout=self.timeout,
                )
                return {
                    'ok': True,
                    'response': resp,
                }
            except requests.RequestException as exc:
                body = {
                    'status': 'error',
                    'message': 'OCR代理请求失败',
                    'service': service,
                    'detail': str(exc),
                }
                if local_error_body is not None:
                    body['local_error'] = local_error_body
                return {
                    'ok': False,
                    'status_code': 502,
                    'body': body,
                }

        base_url = f"{self.upstreams[service]}/{path.lstrip('/')}"
        query = request.META.get('QUERY_STRING')
        target_url = f"{base_url}?{query}" if query else base_url

        try:
            resp = requests.request(
                method=request.method,
                url=target_url,
                headers=self.filter_headers(request),
                data=request.body or None,
                timeout=self.timeout,
            )
            return {'ok': True, 'response': resp}
        except requests.RequestException as exc:
            return {
                'ok': False,
                'status_code': 502,
                'body': {
                    'status': 'error',
                    'message': 'OCR代理请求失败',
                    'service': service,
                    'detail': str(exc),
                },
            }
