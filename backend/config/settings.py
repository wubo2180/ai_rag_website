from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-your-secret-key-here')

DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS = ['*']

# 数据库配置 - 支持SQLite和MySQL
if os.environ.get('DATABASE_TYPE') == 'mysql':
        DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('MYSQL_DATABASE', 'ai_rag_db'),
            'USER': os.environ.get('MYSQL_USER', 'ai_rag_user'),
            'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'airag_user123'),
            'HOST': os.environ.get('MYSQL_HOST', 'localhost'),
            'PORT': os.environ.get('MYSQL_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
        }
else:
    # 默认使用SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
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
    'corsheaders',
    'dj_rest_auth',
    
    # Local apps
    'apps.accounts',
    'apps.chat',
    'apps.knowledge',
    'apps.ai_service',
    'apps.documents',
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

# AI模型配置 - Dify API
DIFY_API_KEY = os.environ.get('DIFY_API_KEY', 'app-2WflAIBZKQGLwUImUXbYaLsN')
DIFY_BASE_URL = os.environ.get('DIFY_BASE_URL', 'http://172.20.46.18:8088/v1')
DIFY_DEFAULT_MODEL = os.environ.get('DIFY_DEFAULT_MODEL', 'deepseek深度思考')  # 默认模型

# 可用的AI模型列表
AVAILABLE_AI_MODELS = os.environ.get('AVAILABLE_AI_MODELS', 'deepseek深度思考,通义千问,腾讯混元,豆包,Kimi,GPT-5,Claude4,Gemini2.5,Grok-4,Llama4').split(',')

# 可选：其他AI服务配置
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')

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
# AI_UI_928_2 集成 - 外部AI服务配置
# 使用经过验证的API配置
# DIFY_API_URL = os.environ.get(
#     'DIFY_API_URL', 
#     'http://172.20.46.18:8088/v1/chat-messages'
# )
DIFY_API_URL = os.environ.get(
    'DIFY_API_URL', 
    'http://localhost:8088/v1/chat-messages'
)
DIFY_API_KEY = os.environ.get(
    'DIFY_API_KEY', 
    'app-2WflAIBZKQGLwUImUXbYaLsN'
)

# Dify 知识库配置
# DIFY_DATASET_BASE_URL = os.environ.get(
#     'DIFY_DATASET_BASE_URL',
#     'http://172.20.46.18:8088/v1'
# )
DIFY_DATASET_BASE_URL = os.environ.get(
    'DIFY_DATASET_BASE_URL',
    'http://localhost:8088/v1'
)
DIFY_DATASET_API_KEY = os.environ.get(
    'DIFY_DATASET_API_KEY',
    'dataset-XGhjOXFbkSkJqagNLbs0SDEy'
)

# 模型配置
DEFAULT_AI_MODEL = os.environ.get('DEFAULT_AI_MODEL', 'deepseek')
ENABLE_DEEP_THINKING = os.environ.get('ENABLE_DEEP_THINKING', 'True') == 'True'

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