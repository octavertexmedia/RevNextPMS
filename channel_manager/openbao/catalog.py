"""
Canonical secret key groups for bootstrap / sync commands.
"""

SECRET_GROUPS = {
    'django': [
        'SECRET_KEY',
        'SITE_URL',
        'ALLOWED_HOSTS',
        'SENTRY_DSN',
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
}
