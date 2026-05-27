import logging

import requests
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .services.proxy_service import OcrProxyService

logger = logging.getLogger(__name__)
ocr_proxy_service = OcrProxyService()


def _relay_response(resp: requests.Response) -> HttpResponse:
    return HttpResponse(
        content=resp.content,
        status=resp.status_code,
        content_type=resp.headers.get('Content-Type', 'application/json'),
    )


@csrf_exempt
@require_http_methods(['GET'])
def ocr_health(request):
    result = ocr_proxy_service.health()
    return JsonResponse(result, status=200)


@csrf_exempt
@require_http_methods(['GET'])
def ocr_task_status(request, task_id):
    preferred_service = request.GET.get('service', '').strip().lower()
    query_result = ocr_proxy_service.query_task_status(task_id, preferred_service, request)
    return JsonResponse(query_result['body'], status=query_result['status_code'])


@csrf_exempt
@require_http_methods(['GET'])
def ocr_service_health(request, service):
    result = ocr_proxy_service.service_health(service)
    return JsonResponse(result['body'], status=result['status_code'])


@csrf_exempt
@require_http_methods(['GET'])
def ocr_service_entry(request, service):
    result = ocr_proxy_service.service_health(service)
    body = result['body']
    status_text = body.get('status', 'unknown')
    title = f"OCR 统一入口 - {service}"
    color = '#166534' if status_text == 'ok' else '#b91c1c'
    mode = body.get('mode', 'proxy-upstream')
    note = '服务已切换为 Django 进程内模式。' if mode.startswith('local-in-django') else '如果状态为 down，请先启动对应 OCR 上游服务，再回到系统页面重试。'

    html = f"""
<!doctype html>
<html lang=\"zh-CN\">
<head>
    <meta charset=\"utf-8\" />
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
        .tag {{ display:inline-block; padding:4px 10px; border-radius:999px; color:white; background:{color}; font-size:12px; }}
        pre {{ background:#111827; color:#e5e7eb; padding:12px; border-radius:8px; overflow:auto; }}
        .note {{ color:#475569; margin-top:12px; }}
    </style>
</head>
<body>
    <h2>{title}</h2>
    <p>状态：<span class=\"tag\">{status_text}</span></p>
    <p>统一代理路径：<code>/api/ocr/{service}/...</code></p>
    <p>上游地址：<code>{body.get('upstream', '-')}</code></p>
    <p class=\"note\">{note}</p>
    <h3>诊断信息</h3>
    <pre>{body}</pre>
</body>
</html>
"""
    return HttpResponse(html, content_type='text/html; charset=utf-8')


@csrf_exempt
@require_http_methods(['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def ocr_service_proxy(request, service, path=''):
    proxy_result = ocr_proxy_service.proxy(request, service, path)
    if proxy_result['ok']:
        if proxy_result.get('is_local'):
            if proxy_result.get('local_raw_body') is not None:
                return HttpResponse(
                    content=proxy_result.get('local_raw_body', b''),
                    status=proxy_result.get('local_status_code', 200),
                    content_type=proxy_result.get('local_content_type', 'application/octet-stream'),
                )

            local_body = proxy_result.get('local_body', {})
            return JsonResponse(
                local_body,
                status=proxy_result.get('local_status_code', 200),
                safe=not isinstance(local_body, list),
            )
        return _relay_response(proxy_result['response'])

    if proxy_result['status_code'] == 502:
        logger.error('OCR proxy request failed: %s', proxy_result['body'].get('detail'))

    return JsonResponse(proxy_result['body'], status=proxy_result['status_code'])
