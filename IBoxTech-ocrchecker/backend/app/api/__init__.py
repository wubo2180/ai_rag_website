"""
API蓝图模块
"""
from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 导入所有路由
from . import auth
from . import users
from . import files
from . import health
from . import dashboard
from . import file_assignments
from . import model_configs
from . import file_type_configs
