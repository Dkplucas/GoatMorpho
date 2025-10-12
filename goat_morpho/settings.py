import os
import sys
import io
from dotenv import load_dotenv
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-w_&2ei37mfaexa#u!u&10((7*3$a-&+oe7!84paf9d*pn@5oc!')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = [
    'goatmorpho.info',  # Your primary domain
    'www.goatmorpho.info',  # Optional: if you use www subdomain
    '130.61.228.97',  # Your server IP
    'localhost',  # For local access
    '127.0.0.1',  # For local access
]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django_extensions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'corsheaders',
    
    # Local apps
    'measurements',
]

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'upload': '50/hour',  # Special rate for image uploads
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'goat_morpho.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'goat_morpho.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases
# Uncomment below for PostgreSQL in production
# if 'test' in sys.argv or os.environ.get('TESTING') or os.environ.get('DJANGO_DEBUG', 'False').lower() == 'true':
#     # Use SQLite for testing and development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'goat_morpho',
        'USER': 'goat_morpho_user',
        'PASSWORD': '123456789',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (Uploaded content)
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# CORS settings (for frontend integration)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React default
    "http://127.0.0.1:3000",
    "http://localhost:8080",  # Vue default
    "http://127.0.0.1:8080",
    "https://goatmorpho.info",  # Your production domain
    "http://goatmorpho.info",  # Your production domain (non-https)
]

CORS_ALLOW_CREDENTIALS = True

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Email settings
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@goatmorpho.info')

# Enhanced Redis Configuration with Production-Ready Settings
REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_DB = int(os.environ.get('REDIS_DB', '1'))
REDIS_TIMEOUT = int(os.environ.get('REDIS_TIMEOUT', '5'))
REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', '50'))

# Build Redis URL with authentication
if REDIS_PASSWORD:
    REDIS_URL = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Production-Ready Cache Configuration
try:
    import django_redis
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': REDIS_MAX_CONNECTIONS,
                    'retry_on_timeout': True,
                    'socket_connect_timeout': REDIS_TIMEOUT,
                    'socket_timeout': REDIS_TIMEOUT,
                    'health_check_interval': 30,
                },
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            },
            'KEY_PREFIX': 'goatmorpho',
            'VERSION': 1,
            'TIMEOUT': int(os.environ.get('CACHE_TIMEOUT', '300')),
        }
    }
    
    # Hybrid Session Configuration (Redis + Database fallback)
    if os.environ.get('REDIS_SESSIONS_ONLY', 'False').lower() == 'true':
        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
        SESSION_CACHE_ALIAS = 'default'
    else:
        # Safer: Cache-backed database sessions
        SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
        SESSION_SAVE_EVERY_REQUEST = False
    
    SESSION_COOKIE_AGE = int(os.environ.get('SESSION_COOKIE_AGE', '1209600'))  # 2 weeks
    
except ImportError:
    # Enhanced fallback configuration
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'goatmorpho-cache',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }
    # Use database sessions as fallback
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'
    SESSION_SAVE_EVERY_REQUEST = False

# CV Processing URL
CV_PROCESSING_URL = os.environ.get('CV_PROCESSING_URL', 'http://127.0.0.1:8001')

# AI/ML Configuration
AI_ML_SETTINGS = {
    'ENABLE_ADVANCED_CV': os.environ.get('ENABLE_ADVANCED_CV', 'True').lower() == 'true',
    'ENABLE_BREED_MODELS': os.environ.get('ENABLE_BREED_MODELS', 'True').lower() == 'true',
    'ENABLE_USER_MODELS': os.environ.get('ENABLE_USER_MODELS', 'True').lower() == 'true',
    'MODEL_DIR': os.path.join(BASE_DIR, 'measurements', 'ml_models'),
    'MIN_TRAINING_SAMPLES': int(os.environ.get('MIN_TRAINING_SAMPLES', '50')),
    'DEFAULT_CONFIDENCE_THRESHOLD': float(os.environ.get('CONFIDENCE_THRESHOLD', '0.7')),
    'ENABLE_UNCERTAINTY_QUANTIFICATION': os.environ.get('ENABLE_UNCERTAINTY', 'True').lower() == 'true',
    'BOOTSTRAP_SAMPLES': int(os.environ.get('BOOTSTRAP_SAMPLES', '50')),
    'ANOMALY_DETECTION_CONTAMINATION': float(os.environ.get('ANOMALY_CONTAMINATION', '0.1')),
    'AUTO_RETRAIN_MODELS': os.environ.get('AUTO_RETRAIN_MODELS', 'False').lower() == 'true',
    'RETRAIN_THRESHOLD_DAYS': int(os.environ.get('RETRAIN_THRESHOLD_DAYS', '30')),
}

# Image Processing Configuration
IMAGE_PROCESSING_SETTINGS = {
    'ENABLE_IMAGE_ENHANCEMENT': os.environ.get('ENABLE_IMAGE_ENHANCEMENT', 'True').lower() == 'true',
    'ENABLE_ENSEMBLE_DETECTION': os.environ.get('ENABLE_ENSEMBLE_DETECTION', 'True').lower() == 'true',
    'MIN_IMAGE_QUALITY_SCORE': float(os.environ.get('MIN_IMAGE_QUALITY', '0.3')),
    'MAX_IMAGE_SIZE': int(os.environ.get('MAX_IMAGE_SIZE', '1920')),
    'ENABLE_BLUR_DETECTION': os.environ.get('ENABLE_BLUR_DETECTION', 'True').lower() == 'true',
    'ENABLE_CONTRAST_ENHANCEMENT': os.environ.get('ENABLE_CONTRAST_ENHANCEMENT', 'True').lower() == 'true',
}

# Performance Monitoring
PERFORMANCE_MONITORING = {
    'TRACK_PROCESSING_TIME': os.environ.get('TRACK_PROCESSING_TIME', 'True').lower() == 'true',
    'TRACK_MODEL_PERFORMANCE': os.environ.get('TRACK_MODEL_PERFORMANCE', 'True').lower() == 'true',
    'PERFORMANCE_LOG_FILE': os.path.join(BASE_DIR, 'ai_performance.log'),
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'goat_morpho.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'measurements': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Authentication settings
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Security settings for production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')