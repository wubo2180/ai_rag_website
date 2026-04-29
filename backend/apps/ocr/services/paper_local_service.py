import importlib.util
import json
import os
import tempfile
import time
from pathlib import Path


class PaperLocalService:
    """paper OCR 的 Django 进程内适配器（不经 HTTP 端口转发）。"""

    def __init__(self):
        self._client = None
        self._load_error = None

    @property
    def service_name(self):
        return 'paper'

    def _paper_root(self) -> Path:
        return Path(__file__).resolve().parent.parent / 'sources' / 'paper'

    def _load_client(self):
        if self._client is not None:
            return self._client

        if self._load_error:
            raise RuntimeError(self._load_error)

        root = self._paper_root()
        module_path = root / 'dify_client.py'
        config_path = root / 'config.yaml'

        if not module_path.exists():
            self._load_error = f'未找到 paper 源码入口: {module_path}'
            raise RuntimeError(self._load_error)
        if not config_path.exists():
            self._load_error = f'未找到 paper 配置文件: {config_path}'
            raise RuntimeError(self._load_error)

        try:
            spec = importlib.util.spec_from_file_location('ocr_paper_dify_client', str(module_path))
            if spec is None or spec.loader is None:
                self._load_error = 'paper DifyClient 模块加载失败（spec 无效）'
                raise RuntimeError(self._load_error)

            module = importlib.util.module_from_spec(spec)

            old_cwd = os.getcwd()
            try:
                os.chdir(root)
                spec.loader.exec_module(module)
            finally:
                os.chdir(old_cwd)

            client_cls = getattr(module, 'DifyClient', None)
            if client_cls is None:
                self._load_error = 'paper DifyClient 模块中未找到 DifyClient'
                raise RuntimeError(self._load_error)

            self._client = client_cls(config_path=str(config_path))
            return self._client
        except Exception as exc:
            self._load_error = f'paper 本地服务初始化失败: {exc}'
            raise RuntimeError(self._load_error) from exc

    def health(self):
        try:
            client = self._load_client()
            return {
                'status': 'ok',
                'service': self.service_name,
                'mode': 'local-in-django',
                'message': 'paper 已切换为 Django 进程内直调模式',
                'dify_base_url': getattr(client, 'base_url', None),
            }
        except Exception as exc:
            return {
                'status': 'down',
                'service': self.service_name,
                'mode': 'local-in-django',
                'message': 'paper 本地服务不可用',
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
                    'data': None,
                    'processing_time': 0,
                },
            }

        filename = file_obj.name or 'upload.pdf'
        ext = Path(filename).suffix.lower().lstrip('.')

        started = time.time()
        try:
            client = self._load_client()
            allowed = client.config.get('dify', {}).get('upload', {}).get('allowed_extensions', ['pdf'])
            if ext not in allowed:
                return {
                    'status_code': 400,
                    'body': {
                        'success': False,
                        'message': f"不支持的文件类型。允许的类型: {', '.join(allowed)}",
                        'data': None,
                        'processing_time': time.time() - started,
                    },
                }

            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir) / filename
                with open(temp_path, 'wb') as fp:
                    for chunk in file_obj.chunks():
                        fp.write(chunk)

                user = request.POST.get('user') or None
                response_mode = request.POST.get('response_mode') or None
                extra = request.POST.get('extra') or None
                additional_inputs = None
                if extra:
                    try:
                        additional_inputs = json.loads(extra)
                    except json.JSONDecodeError:
                        additional_inputs = None

                dify_result = client.process_file(
                    file_path=str(temp_path),
                    user=user,
                    response_mode=response_mode,
                    additional_inputs=additional_inputs,
                )

            processing_time = time.time() - started
            if isinstance(dify_result, dict) and dify_result.get('status') == 'error':
                return {
                    'status_code': 200,
                    'body': {
                        'success': False,
                        'message': dify_result.get('message', '论文分析失败'),
                        'data': dify_result,
                        'processing_time': processing_time,
                        'mode': 'local-in-django',
                    },
                }

            return {
                'status_code': 200,
                'body': {
                    'success': True,
                    'message': '论文分析成功',
                    'data': dify_result if isinstance(dify_result, dict) else {'result': dify_result},
                    'processing_time': processing_time,
                    'mode': 'local-in-django',
                },
            }
        except Exception as exc:
            return {
                'status_code': 500,
                'body': {
                    'success': False,
                    'message': f'paper 本地分析失败: {exc}',
                    'data': None,
                    'processing_time': time.time() - started,
                    'mode': 'local-in-django',
                },
            }

    def proxy(self, request, path: str):
        normalized = (path or '').lstrip('/').lower()

        if normalized in ('', '/') and request.method == 'GET':
            return {
                'status_code': 200,
                'body': {
                    'message': 'Dify 论文分析 API (Django Local)',
                    'version': '1.0.0',
                    'mode': 'local-in-django',
                    'endpoints': {
                        'health': '/api/ocr/paper/health - GET - 服务健康检查',
                        'analyze': '/api/ocr/paper/api/analyze - POST - 上传PDF文件进行分析',
                    },
                },
            }

        if normalized == 'health' and request.method == 'GET':
            return {
                'status_code': 200,
                'body': self.health(),
            }

        if normalized == 'api/analyze' and request.method == 'POST':
            return self._analyze(request)

        return None
