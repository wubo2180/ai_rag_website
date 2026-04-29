import asyncio
import importlib.util
import sys
import tempfile
import time
import traceback
from pathlib import Path


class CommissionLocalService:
    """commission OCR 的 Django 进程内适配器（不经 HTTP 端口转发）。"""

    def __init__(self):
        self._server = None
        self._load_error = None

    @property
    def service_name(self):
        return 'commission'

    def _module_path(self) -> Path:
        return Path(__file__).resolve().parent.parent / 'sources' / 'commission' / 'api_server.py'

    def _load_server(self):
        if self._server is not None:
            return self._server

        if self._load_error:
            raise RuntimeError(self._load_error)

        module_path = self._module_path()
        if not module_path.exists():
            self._load_error = f'未找到 commission 源码入口: {module_path}'
            raise RuntimeError(self._load_error)

        try:
            project_root = module_path.parent
            settings_path = project_root / 'config' / 'settings.py'

            backup_config = sys.modules.get('config')
            backup_config_settings = sys.modules.get('config.settings')

            temp_config_module = None
            temp_settings_module = None

            try:
                if settings_path.exists():
                    settings_spec = importlib.util.spec_from_file_location('config.settings', str(settings_path))
                    if settings_spec and settings_spec.loader:
                        temp_settings_module = importlib.util.module_from_spec(settings_spec)
                        settings_spec.loader.exec_module(temp_settings_module)

                        import types
                        temp_config_module = types.ModuleType('config')
                        temp_config_module.__path__ = [str(project_root / 'config')]
                        setattr(temp_config_module, 'settings', temp_settings_module)

                        sys.modules['config'] = temp_config_module
                        sys.modules['config.settings'] = temp_settings_module

                spec = importlib.util.spec_from_file_location('ocr_commission_api_server', str(module_path))
                if spec is None or spec.loader is None:
                    self._load_error = 'commission API 模块加载失败（spec 无效）'
                    raise RuntimeError(self._load_error)

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            finally:
                # 恢复 Django 原有 config 模块
                if backup_config is not None:
                    sys.modules['config'] = backup_config
                else:
                    sys.modules.pop('config', None)

                if backup_config_settings is not None:
                    sys.modules['config.settings'] = backup_config_settings
                else:
                    sys.modules.pop('config.settings', None)

            server_cls = getattr(module, 'OCRAPIServer', None)
            if server_cls is None:
                self._load_error = 'commission API 模块中未找到 OCRAPIServer'
                raise RuntimeError(self._load_error)

            self._server = server_cls()
            return self._server
        except Exception as exc:
            self._load_error = f'commission 本地服务初始化失败: {exc}'
            raise RuntimeError(self._load_error) from exc

    def health(self):
        try:
            self._load_server()
            return {
                'status': 'ok',
                'service': self.service_name,
                'mode': 'local-in-django',
                'message': 'commission 已切换为 Django 进程内直调模式',
            }
        except Exception as exc:
            return {
                'status': 'down',
                'service': self.service_name,
                'mode': 'local-in-django',
                'message': 'commission 本地服务不可用',
                'detail': str(exc),
            }

    def _analyze(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return {
                'status_code': 400,
                'body': {
                    'success': False,
                    'message': '缺少文件参数 file',
                    'data': {},
                    'processing_time': 0,
                },
            }

        filename = file_obj.name or 'upload.pdf'
        if not filename.lower().endswith('.pdf'):
            return {
                'status_code': 400,
                'body': {
                    'success': False,
                    'message': '只支持PDF文件',
                    'data': {},
                    'processing_time': 0,
                },
            }

        started = time.time()
        try:
            server = self._load_server()

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                pdf_path = temp_path / filename

                with open(pdf_path, 'wb') as fp:
                    for chunk in file_obj.chunks():
                        fp.write(chunk)

                result = asyncio.run(server._analyze_pdf_file(pdf_path, temp_path))

            body = {
                'success': result.get('success', False),
                'message': result.get('message', ''),
                'data': {
                    'total_pages': result.get('total_pages', 0),
                    'ocr_raw_data': result.get('ocr_raw_data', []),
                    'field_extraction_results': result.get('field_extraction_results', []),
                    'combined_results': result.get('combined_results'),
                },
                'processing_time': time.time() - started,
                'mode': 'local-in-django',
            }
            return {'status_code': 200, 'body': body}
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'commission 本地分析失败: {exc}',
                    'data': {},
                    'processing_time': time.time() - started,
                    'mode': 'local-in-django',
                    'traceback': traceback.format_exc(),
                },
            }

    def proxy(self, request, path: str):
        normalized = (path or '').lstrip('/').lower()

        if normalized in ('', '/') and request.method == 'GET':
            return {
                'status_code': 200,
                'body': {
                    'service': 'IBoxTech OCR分析API (Django Local)',
                    'version': '1.0.0',
                    'status': '运行中',
                    'mode': 'local-in-django',
                    'endpoints': {
                        'analyze': '/api/ocr/commission/api/analyze - POST - 上传PDF文件进行OCR分析',
                        'health': '/api/ocr/commission/health - GET - 服务健康检查',
                    },
                },
            }

        if normalized == 'health' and request.method == 'GET':
            health = self.health()
            return {
                'status_code': 200,
                'body': health,
            }

        if normalized == 'api/analyze' and request.method == 'POST':
            return self._analyze(request)

        return None
