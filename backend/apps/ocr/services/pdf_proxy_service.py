"""
PDF 代理下载服务

优先从本地 MinIO/磁盘读取 PDF 文件，远程服务器作为回退。

配置项 (.env):
    PDF_SERVER_BASE_URL=http://172.20.46.18:8000   # 远程后端地址（含端口，回退用）
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

_PLACEHOLDER_PDF_BYTES = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n4 0 obj<</Length 72>>stream\nBT /F1 18 Tf 72 720 Td (PDF preview placeholder - source file unavailable) Tj ET\nendstream\nendobj\n5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000241 00000 n \n0000000363 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n433\n%%EOF\n"


def _get_minio_client():
    """获取 MinIO 客户端"""
    try:
        from minio import Minio
        endpoint = getattr(settings, 'MINIO_ENDPOINT', '172.20.46.18:19000')
        access_key = getattr(settings, 'MINIO_ACCESS_KEY', 'minio')
        secret_key = getattr(settings, 'MINIO_SECRET_KEY', 'rRRyKSJFSDxfRzeE')
        secure = getattr(settings, 'MINIO_SECURE', False)
        return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
    except Exception as exc:
        logger.warning(f'MinIO 客户端初始化失败: {exc}')
        return None


def _get_pdf_server_base_url() -> str:
    url = getattr(settings, 'PDF_SERVER_BASE_URL', '').strip().rstrip('/')
    return url


def _get_timeout() -> float:
    return float(getattr(settings, 'PDF_PROXY_TIMEOUT', 120))


@csrf_exempt
@require_http_methods(['GET'])
def pdf_preview(request, file_id: int):
    try:
        file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
        if not file_obj:
            return JsonResponse({
                'success': False,
                'message': '文件不存在',
            }, status=404)

        diagnostics = {
            'mode': 'local',
            'file_id': file_obj.pk,
            'filename': file_obj.filename,
            'file_path': file_obj.file_path or '',
            'minio_bucket': file_obj.minio_bucket or '',
            'minio_object_key': file_obj.minio_object_key or '',
        }

        return JsonResponse({
            'success': True,
            'message': '使用本地方式预览 PDF',
            'data': {
                'fallback': True,
                'diagnostics': diagnostics,
            },
        })
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
    PDF 下载接口。

    优先级：MinIO → 本地磁盘 → 远程服务器回退 → 占位 PDF
    """
    try:
        file_obj = File.objects.filter(id=file_id, is_deleted=False).first()
        if not file_obj:
            return JsonResponse({
                'success': False,
                'message': '文件不存在',
            }, status=404)

        content_type = file_obj.mime_type or 'application/pdf'

        # 1. 优先从 MinIO 读取
        if file_obj.minio_bucket and file_obj.minio_object_key:
            try:
                client = _get_minio_client()
                if client:
                    response = client.get_object(file_obj.minio_bucket, file_obj.minio_object_key)
                    try:
                        content = response.read()
                    finally:
                        response.close()
                        response.release_conn()
                    logger.info(f'[PDF 下载] 从 MinIO 读取成功: file_id={file_id}')
                    return HttpResponse(
                        content=content,
                        status=200,
                        content_type=content_type,
                    )
            except Exception as minio_exc:
                logger.warning(f'[PDF 下载] MinIO 读取失败: file_id={file_id}, error={minio_exc}')

        # 2. 回退到本地磁盘
        file_path = Path(file_obj.file_path or '')
        if file_path.exists() and file_path.is_file():
            content = file_path.read_bytes()
            logger.info(f'[PDF 下载] 从本地磁盘读取成功: file_id={file_id}')
            return HttpResponse(
                content=content,
                status=200,
                content_type=content_type,
            )

        # 3. 远程服务器回退
        base_url = _get_pdf_server_base_url()
        if base_url:
            try:
                remote_url = f'{base_url}/api/ocr/checker/api/files/{file_id}/download?preview=true'
                headers = {}
                auth = request.META.get('HTTP_AUTHORIZATION')
                if auth:
                    headers['Authorization'] = auth
                resp = requests.get(remote_url, headers=headers, timeout=_get_timeout())
                if resp.status_code == 200:
                    logger.info(f'[PDF 下载] 从远程服务器读取成功: file_id={file_id}')
                    return HttpResponse(
                        content=resp.content,
                        status=200,
                        content_type=resp.headers.get('Content-Type', content_type),
                    )
            except requests.RequestException as exc:
                logger.warning(f'[PDF 下载] 远程服务器回退失败: file_id={file_id}, error={exc}')

        # 4. 都没有，返回占位 PDF
        logger.warning(f'[PDF 下载] 文件不可用: file_id={file_id}')
        return HttpResponse(
            content=_PLACEHOLDER_PDF_BYTES,
            status=200,
            content_type='application/pdf',
        )
    except Exception as exc:
        logger.exception('PDF download failed for file_id=%s', file_id)
        return JsonResponse({
            'success': False,
            'message': f'下载失败: {exc}',
        }, status=500)
