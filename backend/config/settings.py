from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# 加载 .env 文件
# load_dotenv(BASE_DIR / '.env.dev')
load_dotenv(BASE_DIR / '.env.dev')


# 基础配置
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here')
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS = ['*']

# 数据库配置 - 支持SQLite和MySQL
DATABASE_TYPE = os.environ.get('DATABASE_TYPE', 'sqlite')
if DATABASE_TYPE == 'mysql':
        DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_DATABASE', 'ai_rag_db'),
            'USER': os.environ.get('MYSQL_USER', 'ai_rag_user'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD'),
            'HOST': os.environ.get('MYSQL_HOST', 'localhost'),
            'PORT': os.environ.get('MYSQL_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
        # 'ocr_db': {
        #     'ENGINE': 'django.db.backends.mysql',
        #     'NAME': os.environ.get('MYSQL_DB_OCR'),
        #     'USER': os.environ.get('MYSQL_USER_OCR'),
        #     'PASSWORD': os.environ.get('MYSQL_PASSWORD_OCR'),
        #     'HOST': os.environ.get('MYSQL_HOST_OCR', 'localhost'),
        #     'PORT': os.environ.get('MYSQL_PORT_OCR', '3306'),
        #     'OPTIONS': {
        #         'charset': 'utf8mb4',
        #         'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        #     },
        # }
        }
else:
    # 默认使用SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
# DATABASE_ROUTERS = ['db_router.DatabaseRouter']
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'dj_rest_auth',
    
    # Local apps
    'apps.accounts',
    'apps.chat',
    'apps.knowledgegraph',
    'apps.ocr',
    'apps.ai_service',
    'apps.documents',
    'apps.knowledgebase',
    'apps.smart_agent'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR.parent / 'frontend' / 'dist'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True

STATIC_URL = '/static/'
# 生产环境收集静态文件的目录
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# 开发环境下的静态文件目录
STATICFILES_DIRS = [
    os.path.join(BASE_DIR.parent, "frontend/dist/static/"),  # Vue.js构建的静态文件
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'apps.ai_service': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# ======================== REST Framework 配置 ========================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
}

# ======================== JWT 配置 ========================
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# ======================== CORS 配置 ========================
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Vue 开发服务器
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue 可能的端口
    "http://127.0.0.1:8080",
]
# 开发环境允许所有源（生产环境请删除）
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
    CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# ======================== AI 服务配置 ========================
# Dify API 配置 - 从环境变量读取，生产环境中必须设置
DIFY_API_KEY = os.environ.get('DIFY_API_KEY')
# 临时注释掉以允许开发环境不设置也能运行
# if not DIFY_API_KEY:
#     raise ValueError("DIFY_API_KEY must be set in environment variables (.env file)")

DIFY_API_URL = os.environ.get('DIFY_API_URL', 'http://localhost:8088/v1')
DIFY_DEFAULT_MODEL = os.environ.get('DIFY_DEFAULT_MODEL', 'deepseek深度思考')  # 默认模型

AVAILABLE_AI_MODELS = os.environ.get('AVAILABLE_AI_MODELS', 'deepseek深度思考,通义千问,腾讯混元,豆包,Kimi,GPT-5,Claude4,Gemini2.5,Grok-4,Llama4').split(',')

# Dify 知识库配置 - 从环境变量读取，生产环境中必须设置
DIFY_DATASET_BASE_URL = os.environ.get('DIFY_DATASET_BASE_URL')
DIFY_DATASET_API_KEY = os.environ.get('DIFY_DATASET_API_KEY')
DIFY_API_KEY_data4line = os.environ.get('DIFY_API_KEY_data4line')
# 临时注释掉以允许开发环境不设置也能运行
# if not DIFY_DATASET_API_KEY:
#     raise ValueError("DIFY_DATASET_API_KEY must be set in environment variables (.env file)")

# 模型配置
DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'deepseek')
ENABLE_DEEP_THINKING = os.environ.get('ENABLE_DEEP_THINKING', 'True').lower() == 'true'

# 流式响应配置
STREAM_TIMEOUT = int(os.environ.get('STREAM_TIMEOUT', '120'))  # 增加到120秒
MAX_STREAM_RETRIES = int(os.environ.get('MAX_STREAM_RETRIES', '3'))

# AI模型特定超时配置（秒）
AI_MODEL_TIMEOUTS = {
    'deepseek深度思考': 500,  # 深度思考模式需要更长时间
    'GPT-5': 240,             # GPT-5响应较慢
    '豆包': 90,               # 豆包中等速度
    '通义千问': 60,           # 通义千问较快
    'Claude4': 120,           # Claude4中等速度
    'Kimi': 90,               # Kimi中等速度
    'default': 120             # 默认超时
}

# OCR 服务直连配置（Django 统一代理层）
# 默认端口与 sources 下各服务启动脚本保持一致：commission=6001, paper=6002, checker=5001
OCR_COMMISSION_BASE_URL = os.environ.get('OCR_COMMISSION_BASE_URL', 'http://127.0.0.1:6001')
OCR_PAPER_BASE_URL = os.environ.get('OCR_PAPER_BASE_URL', 'http://127.0.0.1:6002')
OCR_CHECKER_BASE_URL = os.environ.get('OCR_CHECKER_BASE_URL', 'http://127.0.0.1:5001')
OCR_PROXY_TIMEOUT = float(os.environ.get('OCR_PROXY_TIMEOUT', '120'))

# paper OCR：后端内部直连 Dify（默认开启），不依赖独立 6002 服务进程
OCR_PAPER_DIRECT_DIFY_ENABLED = os.environ.get('OCR_PAPER_DIRECT_DIFY_ENABLED', 'true').lower() == 'true'
OCR_PAPER_DIFY_BASE_URL = os.environ.get('OCR_PAPER_DIFY_BASE_URL', DIFY_API_URL)
OCR_PAPER_DIFY_API_KEY = os.environ.get('OCR_PAPER_DIFY_API_KEY', DIFY_API_KEY)
OCR_PAPER_DIFY_DEFAULT_USER = os.environ.get('OCR_PAPER_DIFY_DEFAULT_USER', 'ai-rag-django')
OCR_PAPER_DIFY_UPLOAD_ENDPOINT = os.environ.get('OCR_PAPER_DIFY_UPLOAD_ENDPOINT', '/files/upload')
OCR_PAPER_DIFY_WORKFLOW_ENDPOINT = os.environ.get('OCR_PAPER_DIFY_WORKFLOW_ENDPOINT', '/workflows/run')
OCR_PAPER_DIFY_RESPONSE_MODE = os.environ.get('OCR_PAPER_DIFY_RESPONSE_MODE', 'blocking')
OCR_PAPER_DIFY_TRANSFER_METHOD = os.environ.get('OCR_PAPER_DIFY_TRANSFER_METHOD', 'local_file')
OCR_PAPER_DIFY_FILE_TYPE = os.environ.get('OCR_PAPER_DIFY_FILE_TYPE', 'document')
OCR_PAPER_DIFY_TIMEOUT = float(os.environ.get('OCR_PAPER_DIFY_TIMEOUT', str(OCR_PROXY_TIMEOUT)))