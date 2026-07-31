from django.apps import AppConfig


class GestionChambresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_chambres'
    verbose_name = 'Gestion des Chambres d\'Hospitalisation'

    def ready(self):
        import gestion_chambres.signals  # noqa