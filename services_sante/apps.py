# services_sante/apps.py
from django.apps import AppConfig

class ServicesSanteConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services_sante'
    verbose_name = 'Services de santé'
