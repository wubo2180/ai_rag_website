from django.conf import settings


def get_service_base_urls():
    return {
        'commission': getattr(settings, 'OCR_COMMISSION_BASE_URL', 'http://127.0.0.1:6001').rstrip('/'),
        'paper': getattr(settings, 'OCR_PAPER_BASE_URL', 'http://127.0.0.1:6002').rstrip('/'),
        'checker': getattr(settings, 'OCR_CHECKER_BASE_URL', 'http://127.0.0.1:5001').rstrip('/'),
    }


def get_timeout() -> float:
    return float(getattr(settings, 'OCR_PROXY_TIMEOUT', 120))


def get_paper_dify_config():
    enabled = str(getattr(settings, 'OCR_PAPER_DIRECT_DIFY_ENABLED', True)).lower() == 'true'

    base_url = (
        getattr(settings, 'OCR_PAPER_DIFY_BASE_URL', None)
        or getattr(settings, 'DIFY_API_URL', '')
        or ''
    ).strip().rstrip('/')

    api_key = (
        getattr(settings, 'OCR_PAPER_DIFY_API_KEY', None)
        or getattr(settings, 'DIFY_API_KEY', None)
        or ''
    ).strip()

    return {
        'enabled': enabled,
        'base_url': base_url,
        'api_key': api_key,
        'default_user': getattr(settings, 'OCR_PAPER_DIFY_DEFAULT_USER', 'ai-rag-django'),
        'upload_endpoint': getattr(settings, 'OCR_PAPER_DIFY_UPLOAD_ENDPOINT', '/files/upload'),
        'workflow_endpoint': getattr(settings, 'OCR_PAPER_DIFY_WORKFLOW_ENDPOINT', '/workflows/run'),
        'response_mode': getattr(settings, 'OCR_PAPER_DIFY_RESPONSE_MODE', 'blocking'),
        'transfer_method': getattr(settings, 'OCR_PAPER_DIFY_TRANSFER_METHOD', 'local_file'),
        'file_type': getattr(settings, 'OCR_PAPER_DIFY_FILE_TYPE', 'document'),
        'timeout': float(getattr(settings, 'OCR_PAPER_DIFY_TIMEOUT', get_timeout())),
    }
