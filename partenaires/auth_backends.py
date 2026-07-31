from django.contrib.auth.backends import BaseBackend
from .models import UtilisateurPartenaire


class PartenaireAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        try:
            user = UtilisateurPartenaire.objects.get(username=username, actif=True)
        except UtilisateurPartenaire.DoesNotExist:
            return None
        if user.check_password(password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return UtilisateurPartenaire.objects.get(pk=user_id)
        except UtilisateurPartenaire.DoesNotExist:
            return None
