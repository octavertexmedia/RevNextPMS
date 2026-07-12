"""
Canonical secret key groups for bootstrap / sync commands and OpenBao loader allowlist.
"""

SECRET_GROUPS = {
    'django': [
        'SECRET_KEY',
        'DEBUG',
        'SITE_URL',
        'ALLOWED_HOSTS',
        'CSRF_TRUSTED_ORIGINS',
        'CORS_ALLOWED_ORIGINS',
        'SECURE_SSL_REDIRECT',
        'SENTRY_DSN',
        'SUPERUSER_PASSWORD',
        'ENVIRONMENT',
    ],
    'database': [
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD',
        'DB_HOST',
        'DB_PORT',
    ],
    'celery': [
        'CELERY_BROKER_URL',
        'CELERY_RESULT_BACKEND',
    ],
    'billing': [
        'BILLING_GATEWAY',
        'RAZORPAY_KEY_ID',
        'RAZORPAY_KEY_SECRET',
        'RAZORPAY_WEBHOOK_SECRET',
        'PAYU_MERCHANT_KEY',
        'PAYU_MERCHANT_SALT',
        'PAYU_MODE',
    ],
    'oidc': [
        'OIDC_ENABLED',
        'OIDC_OP_ISSUER',
        'OIDC_RP_CLIENT_ID',
        'OIDC_RP_CLIENT_SECRET',
        'OIDC_RP_CALLBACK_URL',
        'OIDC_RP_SCOPES',
        'OIDC_CLIENT_CHANNEL_MANAGER_ID',
        'OIDC_CLIENT_CHANNEL_MANAGER_SECRET',
        'OIDC_CLIENT_PMS_ID',
        'OIDC_CLIENT_PMS_SECRET',
        'OIDC_CLIENT_POS_ID',
        'OIDC_CLIENT_POS_SECRET',
        'OIDC_CLIENT_CMS_ID',
        'OIDC_CLIENT_CMS_SECRET',
        'OIDC_CLIENT_BOOKING_ID',
        'OIDC_CLIENT_BOOKING_SECRET',
        'OIDC_CLIENT_HOTELS_ID',
        'OIDC_CLIENT_HOTELS_SECRET',
        'OIDC_CLIENT_NETWORKS_ID',
        'OIDC_CLIENT_NETWORKS_SECRET',
        'OIDC_CLIENT_TOURS_ID',
        'OIDC_CLIENT_TOURS_SECRET',
    ],
    'integrations': [
        'GOOGLE_MAPS_API_KEY',
        'FCM_SERVER_KEY',
    ],
    'email': [
        'EMAIL_HOST',
        'EMAIL_PORT',
        'EMAIL_HOST_USER',
        'EMAIL_HOST_PASSWORD',
        'EMAIL_USE_TLS',
        'DEFAULT_FROM_EMAIL',
    ],
    'cloud': [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY',
        'AWS_STORAGE_BUCKET_NAME',
        'AWS_S3_REGION_NAME',
    ],
}


def all_managed_secret_keys() -> tuple[str, ...]:
    """Flat allowlist derived from SECRET_GROUPS (stable order, unique)."""
    seen: set[str] = set()
    keys: list[str] = []
    for group in SECRET_GROUPS.values():
        for key in group:
            if key not in seen:
                seen.add(key)
                keys.append(key)
    return tuple(keys)
