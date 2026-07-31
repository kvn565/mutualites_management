from django.apps import AppConfig


class GroupeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'groupe'
    verbose_name = 'Groupes'

    def ready(self):
        import groupe.signals  # noqa
