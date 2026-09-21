from django.apps import AppConfig


class SingleTenantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'single_tenant'
    verbose_name = 'Single-Tenant'

    def ready(self):
        pass
