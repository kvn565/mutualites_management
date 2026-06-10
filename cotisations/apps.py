# cotisations/apps.py
from django.apps import AppConfig

class CotisationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cotisations'
    verbose_name = 'Cotisations'
