from django.apps import AppConfig


class SecretsManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'secrets_manager'
    verbose_name = 'OpenBao Secrets Manager'
