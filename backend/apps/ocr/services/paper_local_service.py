import importlib.util
import json
import os
import tempfile
import time
from pathlib import Path


class PaperLocalService:
    """paper 服务适配器：仅保留上游回退，不再依赖本地 sources 目录。"""

    @property
    def service_name(self):
        return 'paper'

    def health(self):
        return {
            'status': 'down',
            'service': self.service_name,
            'mode': 'upstream-only',
            'message': 'paper 本地模式已下线，请使用上游服务',
        }

    def proxy(self, request, path: str):
        return None
