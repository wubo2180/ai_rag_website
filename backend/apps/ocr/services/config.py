from django.conf import settings


def get_service_base_urls():
    return {
        'commission': getattr(settings, 'OCR_COMMISSION_BASE_URL', 'http://127.0.0.1:6001').rstrip('/'),
        'paper': getattr(settings, 'OCR_PAPER_BASE_URL', 'http://127.0.0.1:6002').rstrip('/'),
        'checker': getattr(settings, 'OCR_CHECKER_BASE_URL', 'http://127.0.0.1:5001').rstrip('/'),
    }


def get_timeout() -> float:
    return float(getattr(settings, 'OCR_PROXY_TIMEOUT', 120))
