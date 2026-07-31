# factures/apps.py
from django.apps import AppConfig

class FacturesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'factures'
    verbose_name = 'Factures de santé'


