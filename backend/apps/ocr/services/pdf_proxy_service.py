"""
PDF 代理下载服务

从 .env 中配置的 PDF_SERVER_BASE_URL 地址拉取 PDF 文件二进制内容，
解决本地后端与远程文件存储分离时的预览/下载问题。

配置项 (.env):
    PDF_SERVER_BASE_URL=http://172.20.46.18:8000   # 远程后端地址（含端口）
"""

import logging
from pathlib import Path

import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from ..models import File

logger = logging.getLogger(__name__)


def _get_pdf_server_base_url() -> str:
    """从 settings / .env 读取远程 PDF 服务器地址。"""
    url = getattr(settings, 'PDF_SERVER_BASE_URL', '').strip().rstrip('/')
    if not url:
        raise ValueError(
            'PDF_SERVER_BASE_URL 未配置，请在 .env 中添加如：'
            'PDF_SERVER_BASE_URL=http://172.20.46.18:8000'
        )
    return url


def _get_timeout() -> float:
    return float(getattr(settings, 'PDF_PROXY_TIMEOUT', 120))


@csrf_exempt
@require_http_methods(['GET'])
def pdf_preview(request, file_id: int):
    """
    PDF 预览信息接口（对应前端 getFilePreviewUrl）。

    GET /api/ocr/pdf/{file_id}/preview
    返回诊断信息 + fallback 标记，前端据此走 blob 下载预览。
    """
    try:
        file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
        if not file_obj:
            return JsonResponse({
                'success': False,
                'message': '文件不存在',
            }, status=404)

        base_url = _get_pdf_server_base_url()
        diagnostics = {
            'mode': 'remote-proxy',
            'file_id': file_obj.pk,
            'filename': file_obj.filename,
            'file_path': file_obj.file_path or '',
            'local_exists': False,
            'proxy_target': f'{base_url}/api/ocr/checker/api/files/{file_id}/download',
        }

        return JsonResponse({
            'success': True,
            'message': '使用远程代理方式预览 PDF',
            'data': {
                'fallback': True,
                'diagnostics': diagnostics,
            },
        })
    except ValueError as exc:
        return JsonResponse({
            'success': False,
            'message': str(exc),
        }, status=500)
    except Exception as exc:
        logger.exception('PDF preview failed for file_id=%s', file_id)
        return JsonResponse({
            'success': False,
            'message': f'预览失败: {exc}',
        }, status=500)


@csrf_exempt
@require_http_methods(['GET'])
def pdf_download(request, file_id: int):
    """
    PDF 下载接口（对应前端 downloadFileBlob）。

    GET /api/ocr/pdf/{file_id}/download?preview=true|false
    向远程服务器发起请求，将 PDF 二进制原样转发给前端。
    """
    try:
        file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
        if not file_obj:
            return JsonResponse({
                'success': False,
                'message': '文件不存在',
            }, status=404)

        base_url = _get_pdf_server_base_url()
        timeout = _get_timeout()
        preview_flag = request.GET.get('preview', 'true')

        remote_url = (
            f'{base_url}/api/ocr/checker/api/files/{file_id}/download'
            f'?preview={preview_flag}'
        )

        headers = {}
        auth = request.META.get('HTTP_AUTHORIZATION')
        if auth:
            headers['Authorization'] = auth

        resp = requests.get(remote_url, headers=headers, timeout=timeout)

        if resp.status_code != 200:
            logger.warning(
                'Remote PDF download returned %s for file_id=%s, url=%s',
                resp.status_code, file_id, remote_url,
            )
            return HttpResponse(
                content=resp.content,
                status=resp.status_code,
                content_type=resp.headers.get('Content-Type', 'application/json'),
            )

        content_type = (
            resp.headers.get('Content-Type')
            or file_obj.mime_type
            or 'application/pdf'
        )

        return HttpResponse(
            content=resp.content,
            status=200,
            content_type=content_type,
        )
    except ValueError as exc:
        return JsonResponse({
            'success': False,
            'message': str(exc),
        }, status=500)
    except requests.RequestException as exc:
        logger.exception('Remote PDF download failed for file_id=%s', file_id)
        return JsonResponse({
            'success': False,
            'message': f'从远程服务器下载 PDF 失败: {exc}',
        }, status=502)
    except Exception as exc:
        logger.exception('PDF download failed for file_id=%s', file_id)
        return JsonResponse({
            'success': False,
            'message': f'下载失败: {exc}',
        }, status=500)
