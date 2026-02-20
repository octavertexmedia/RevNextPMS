"""
Django settings for channel_manager project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application definition
INSTALLED_APPS = [
    'unfold',  # Must be before django.contrib.admin
    'unfold.contrib.filters',  # Optional: Additional filters
    'unfold.contrib.forms',  # Optional: Form enhancements
    
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'guardian',
    'import_export',
    'simple_history',
    'constance',
    'constance.backends.database',
    'django_celery_beat',
    'modeltranslation',
    'djmoney',
    'location_field.apps.DefaultConfig',
    'djangoql',
    'rest_framework',  # Django REST Framework
    'drf_yasg',  # Swagger/OpenAPI documentation
    
    # Local apps
    'tenants',  # Must be before other apps for custom user model
    'core',
    'integrations',
    'bookings',
    'reports',
    # Solution apps (eGlobe parity)
    'cloud_pms',
    'cloud_pos',
    'booking_engine',
    'website_builder',
    'b2b_network',
    'ota_listing',
    'google_hotel_ads',
    'payment_gateways',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenants.middleware.TenantMiddleware',  # Add tenant context to request
    'tenants.middleware.SubscriptionMiddleware',  # Enforce subscription limits
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'channel_manager.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'channel_manager.wsgi.application'

# Custom User Model
AUTH_USER_MODEL = 'tenants.TenantUser'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'channel_manager'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Password validation
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
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
] if (BASE_DIR / 'static').exists() else []

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django Unfold Configuration
UNFOLD = {
    "SITE_TITLE": "RevNext Admin Management",
    "SITE_HEADER": "RevNext Admin Management",
    "SITE_URL": "/",
    "SITE_ICON": "https://www.revnext.in/logo.png",
    "SITE_LOGO": "https://www.revnext.in/logo.png",
    "SITE_SYMBOL": "speed",  # Icon from https://fonts.google.com/icons
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "channel_manager.settings.environment_callback",
    "DASHBOARD_CALLBACK": None,  # We handle this in core/admin.py
    "LOGIN": {
        "image": "https://www.revnext.in/logo.png",
        "redirect_after_login": lambda request: "/admin/",
    },
    "STYLES": [],
    "SCRIPTS": [],
}

def environment_callback(request):
    """Return environment name for Unfold"""
    return "Production" if not DEBUG else "Development"

# Constance Configuration (Dynamic Settings)
CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_CONFIG = {
    'SYSTEM_NAME': ('RevNext Channel Manager', 'System name'),
    'SYSTEM_EMAIL': ('support@revnext.in', 'System support email'),
    'MAX_PROPERTIES_FREE': (1, 'Maximum properties for free plan'),
    'MAX_PROPERTIES_BASIC': (5, 'Maximum properties for basic plan'),
    'MAX_PROPERTIES_PROFESSIONAL': (25, 'Maximum properties for professional plan'),
    'MAX_PROPERTIES_ENTERPRISE': (100, 'Maximum properties for enterprise plan'),
    'TRIAL_PERIOD_DAYS': (14, 'Trial period in days'),
    'API_RATE_LIMIT_PER_MINUTE': (60, 'API rate limit per minute'),
}

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'channel_manager.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'channel_manager': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Django Money Configuration
DJANGO_MONEY = {
    'DEFAULT_CURRENCY': 'INR',
    'DEFAULT_CURRENCY_CODE': 'INR',
}

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# Swagger/OpenAPI Configuration
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Token': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Token-based authentication. Format: "Token <your-token>"',
        },
        'Session': {
            'type': 'apiKey',
            'name': 'Cookie',
            'in': 'cookie',
            'description': 'Session-based authentication using cookies',
        },
    },
    'USE_SESSION_AUTH': True,
    'LOGIN_URL': '/admin/login/',
    'LOGOUT_URL': '/admin/logout/',
    'DOC_EXPANSION': 'list',
    'DEEP_LINKING': True,
    'SHOW_EXTENSIONS': True,
    'DEFAULT_MODEL_RENDERING': 'example',
    'DEFAULT_INFO': {
        'title': 'RevNext Channel Manager API',
        'version': '1.0.0',
        'description': '''
# RevNext Channel Manager API Documentation

Complete REST API for managing hotel properties, OTA integrations, reservations, and subscriptions.

## Authentication

The API supports two authentication methods:
1. **Token Authentication**: Use `Token <your-token>` in the Authorization header
2. **Session Authentication**: Use Django session cookies (for browser-based access)

## Rate Limiting

- Anonymous users: 100 requests/hour
- Authenticated users: 1000 requests/hour
- API calls are tracked per tenant subscription plan

## Subscription Plans

- **Free**: 1 property, 5 integrations/property, 1000 API calls/month
- **Basic**: 5 properties, 10 integrations/property, 10000 API calls/month
- **Professional**: 25 properties, 25 integrations/property, 100000 API calls/month
- **Enterprise**: 100 properties, unlimited integrations, unlimited API calls

## Endpoints

- `/api/properties/` - Manage hotel properties
- `/api/integrations/` - Manage OTA platform integrations
- `/api/reservations/` - View and manage reservations
- `/api/subscriptions/` - Manage subscription plans and payments
- `/api/tenants/` - Tenant information and settings

For detailed endpoint documentation, explore the sections below.
        ''',
        'contact': {
            'name': 'RevNext Support',
            'email': 'support@revnext.in',
            'url': 'https://www.revnext.in',
        },
        'license': {
            'name': 'Proprietary',
        },
    },
}

REDOC_SETTINGS = {
    'LAZY_RENDERING': True,
    'HIDE_HOSTNAME': False,
    'EXPAND_RESPONSES': '200,201',
    'PATH_IN_MIDDLE': True,
    'NATIVE_SCROLLBARS': False,
    'REQUIRED_PROPS_FIRST': True,
    'SORT_OPERATIONS_ALPHA': True,
    'SORT_TAGS_ALPHA': True,
    'SORT_PROPS_ALPHA': True,
    'HIDE_SINGLE_REQUEST_SAMPLE_TAG': False,
    'HIDE_LOADING': False,
    'MENU_TOGGLE': True,
    'THEME': {
        'colors': {
            'primary': {
                'main': '#4f46e5',
            },
        },
    },
}

# Celery Beat Schedule
CELERY_BEAT_SCHEDULE = {
    'generate-scheduled-reports': {
        'task': 'reports.tasks.generate_scheduled_reports',
        'schedule': 60.0 * 60,  # Every hour
    },
    'cleanup-expired-reports': {
        'task': 'reports.tasks.cleanup_expired_reports',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
    'apply-seasonal-pricing': {
        'task': 'core.tasks.apply_seasonal_pricing_adjustments',
        'schedule': 60.0 * 60 * 24,  # Daily
    },
    'optimize-rates-for-demand': {
        'task': 'core.tasks.optimize_rates_for_demand',
        'schedule': 60.0 * 60 * 4,  # Every 4 hours
    },
    'apply-pricing-rules': {
        'task': 'core.tasks.apply_pricing_rules',
        'schedule': 60.0 * 60,  # Every hour
    },
}

# Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
