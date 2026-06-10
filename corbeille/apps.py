# corbeille/apps.py
from django.apps import AppConfig

class CorbeilleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'corbeille'
    verbose_name = 'Corbeille'
