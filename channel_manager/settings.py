"""
Django settings for channel_manager project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 1) Bootstrap from .env (includes OPENBAO_* connection settings)
load_dotenv()

# 2) Overlay application secrets from OpenBao when enabled
from channel_manager.openbao import apply_openbao_secrets  # noqa: E402
apply_openbao_secrets()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    ','.join(__import__('channel_manager.domains', fromlist=['default_allowed_hosts']).default_allowed_hosts()),
).split(',')

# Product host → product code (see products.catalog.HOST_ALIASES)
PRODUCT_BASE_DOMAIN = os.getenv('PRODUCT_BASE_DOMAIN', 'revnext.in')

# CSRF for multi-host product suite + auth/secrets
CSRF_TRUSTED_ORIGINS = [
    o for o in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        ','.join(__import__('channel_manager.domains', fromlist=['csrf_trusted_origins']).csrf_trusted_origins()),
    ).split(',')
    if o
]

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
    'rest_framework.authtoken',  # Token auth for mobile / API clients
    'django_filters',
    'corsheaders',
    'drf_yasg',  # Swagger/OpenAPI documentation
    
    # Local apps
    'tenants',  # Must be before other apps for custom user model
    'rbac',  # Enterprise hospitality RBAC
    'products',  # Multi-product catalog & billing
    'secrets_manager',  # OpenBao secrets management commands
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
    'tours',  # Tours planner (tours.revnext.in)
    'hotels',  # Hotels aggregator discovery (hotels.revnext.in)
]

# Auth backends (ModelBackend + django-guardian object permissions)
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'guardian.backends.ObjectPermissionBackend',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'tenants.middleware.TenantMiddleware',  # Add tenant context to request
    'products.middleware.ProductHostMiddleware',  # Resolve product from Host
    'tenants.middleware.SubscriptionMiddleware',  # Enforce legacy subscription limits
    'products.middleware.ProductEntitlementMiddleware',  # Per-product billing gates
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
    "SITE_ICON": "https://www.revnext.in/favicon.ico",
    "SITE_LOGO": "https://www.revnext.in/logo.png",
    "SITE_SYMBOL": "speed",  # Icon from https://fonts.google.com/icons
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "ENVIRONMENT": "channel_manager.settings.environment_callback",
    "DASHBOARD_CALLBACK": None,  # We handle this in core/admin.py
    "LOGIN": {
        "image": "https://www.revnext.in/favicon.ico",
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
    'BILLING_GATEWAY': (
        'razorpay',
        'Preferred SaaS billing gateway: razorpay or payu (one over the other)',
    ),
}

# Platform SaaS billing (RevNext subscription payments — not hotel guest checkout)
BILLING_GATEWAY = os.getenv('BILLING_GATEWAY', 'razorpay').lower()
RAZORPAY_KEY_ID = os.getenv('RAZORPAY_KEY_ID', '')
RAZORPAY_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
RAZORPAY_WEBHOOK_SECRET = os.getenv('RAZORPAY_WEBHOOK_SECRET', '')
PAYU_MERCHANT_KEY = os.getenv('PAYU_MERCHANT_KEY', '')
PAYU_MERCHANT_SALT = os.getenv('PAYU_MERCHANT_SALT', '')
PAYU_MODE = os.getenv('PAYU_MODE', 'test').lower()  # test | live
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')

# OpenBao secrets manager — production host is secrets.revnext.in
OPENBAO_ENABLED = os.getenv('OPENBAO_ENABLED', 'false').lower() in ('1', 'true', 'yes')
OPENBAO_ADDR = os.getenv(
    'OPENBAO_ADDR',
    os.getenv('BAO_ADDR', 'https://secrets.revnext.in'),
)
OPENBAO_MOUNT_POINT = os.getenv('OPENBAO_MOUNT_POINT', 'secret')
OPENBAO_SECRET_PATH = os.getenv('OPENBAO_SECRET_PATH', 'revnext/channel-manager')
OPENBAO_REQUIRED = os.getenv('OPENBAO_REQUIRED', 'false').lower() in ('1', 'true', 'yes')

# OIDC relying party → auth.revnext.in (IdP). Client secrets live in OpenBao.
OIDC_ENABLED = os.getenv('OIDC_ENABLED', 'false').lower() in ('1', 'true', 'yes')
OIDC_OP_ISSUER = os.getenv('OIDC_OP_ISSUER', 'https://auth.revnext.in')
OIDC_RP_CLIENT_ID = os.getenv('OIDC_RP_CLIENT_ID', '')
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET', '')
OIDC_RP_SIGN_ALGO = os.getenv('OIDC_RP_SIGN_ALGO', 'RS256')
OIDC_RP_SCOPES = os.getenv('OIDC_RP_SCOPES', 'openid profile email')
LOGIN_REDIRECT_URL = os.getenv('LOGIN_REDIRECT_URL', '/tenants/dashboard/')
LOGOUT_REDIRECT_URL = os.getenv('LOGOUT_REDIRECT_URL', '/')
# Absolute callback used by the IdP (per product host in production)
OIDC_RP_CALLBACK_URL = os.getenv(
    'OIDC_RP_CALLBACK_URL',
    'https://channel-manager.revnext.in/oidc/callback/',
)

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
        'django_filters.rest_framework.DjangoFilterBackend',
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

# Security Settings (behind nginx TLS termination)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True
# Health checks hit gunicorn over plain HTTP inside Docker — do not redirect those.
SECURE_REDIRECT_EXEMPT = [r'^health/?$']

if not DEBUG:
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('1', 'true', 'yes')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    # SAMEORIGIN (not DENY) — booking widget uses @xframe_options_exempt for embeds
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# CORS — product hosts + local SPAs (override via CORS_ALLOWED_ORIGINS)
from channel_manager.domains import production_cors_origins_csv  # noqa: E402
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        production_cors_origins_csv(),
    ).split(',')
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True
# Flutter mobile apps do not send Origin; allow non-browser clients
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

# Optional FCM legacy server key for mobile push (tenants.push)
FCM_SERVER_KEY = os.getenv('FCM_SERVER_KEY', '')
