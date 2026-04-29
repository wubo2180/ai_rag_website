from pathlib import Path


class CheckerLocalService:
    """checker 的 Django 本地适配器（纯 Django 轻量模式，不依赖 Flask 运行时）。"""

    def __init__(self):
        self._load_error = None

    @property
    def service_name(self):
        return 'checker'

    def _checker_source_root(self) -> Path:
        return Path(__file__).resolve().parent.parent / 'sources' / 'checker'

    def _validate_source(self):
        source_root = self._checker_source_root()
        readme_file = source_root / 'README.md'
        docs_dir = source_root / 'docs'

        if not source_root.exists():
            self._load_error = f'未找到 checker 源码目录: {source_root}'
            return False
        if not readme_file.exists():
            self._load_error = f'未找到 checker 说明文件: {readme_file}'
            return False
        if not docs_dir.exists():
            self._load_error = f'未找到 checker 文档目录: {docs_dir}'
            return False

        self._load_error = None
        return True

    def health(self):
        ok = self._validate_source()
        if ok:
            return {
                'status': 'ok',
                'service': self.service_name,
                'mode': 'local-in-django-lite',
                'message': 'checker 已切换为 Django 轻量模式（不依赖 Flask 运行时）',
            }

        return {
            'status': 'down',
            'service': self.service_name,
            'mode': 'local-in-django-lite',
            'message': 'checker 本地模式不可用',
            'detail': self._load_error,
        }

    def proxy(self, request, path: str):
        normalized = (path or '').lstrip('/').lower()

        if normalized in ('', '/') and request.method == 'GET':
            health = self.health()
            return {
                'status_code': 200,
                'body': {
                    'message': 'Checker OCR API (Django Local)',
                    'service': self.service_name,
                    'version': '1.0.0',
                    'mode': health.get('mode', 'local-in-django-lite'),
                    'health': health,
                    'endpoints': {
                        'health': '/api/ocr/checker/health - GET - 服务健康检查',
                        'proxy': '/api/ocr/checker/<path> - 统一代理入口（按策略回退）',
                    },
                },
            }

        if normalized == 'health' and request.method == 'GET':
            return {
                'status_code': 200,
                'body': self.health(),
            }

        return None
