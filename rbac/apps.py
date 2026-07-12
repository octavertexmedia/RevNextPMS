from django.apps import AppConfig


class RbacConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rbac'
    verbose_name = 'RBAC & Access Control'

    def ready(self):
        # Ensure system catalog is importable; seeding is via management command.
        pass
