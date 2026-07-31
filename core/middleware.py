import logging
import time
from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect

from core.models import JournalAudit, HistoriqueConnexion, set_current_mutualite

logger = logging.getLogger('core.security')


class MutualiteMiddleware:
    """Détecte et définit la mutualité courante pour la requête."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        mutualite = None
        if request.user.is_authenticated:
            mutualite = request.user.mutualite
        set_current_mutualite(mutualite)
        request.current_mutualite = mutualite
        response = self.get_response(request)
        set_current_mutualite(None)
        return response


class LicenseMiddleware:
    """
    Vérifie que la licence de la mutualité est valide à chaque requête.
    Redirige vers la page d'activation si la licence est expirée.
    Les super admins et certaines pages sont exemptés.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    ALLOWED_PATHS = ('/connexion/activer-licence', '/licence/', '/connexion/', '/connexion/deconnexion/', '/admin/')

    def __call__(self, request):
        path = request.path
        if any(path.startswith(p) for p in self.ALLOWED_PATHS):
            return self.get_response(request)

        if request.user.is_authenticated and not request.user.est_super_admin:
            mutualite = request.user.mutualite
            if mutualite and not mutualite.licence_valide:
                return redirect('activer_licence')

        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        path = request.path
        if any(path.startswith(p) for p in self.ALLOWED_PATHS):
            return None
        if request.user.is_authenticated and not request.user.est_super_admin:
            mutualite = request.user.mutualite
            if mutualite and not mutualite.licence_valide:
                return redirect('activer_licence')
        return None


class RateLimitMiddleware:
    """Anti brute-force sur la page de connexion."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('REMOTE_ADDR', '')
        if request.path == '/connexion/' and request.method == 'POST':
            from django.core.cache import cache
            key = f'login_attempts_{ip}'
            attempts = cache.get(key, 0)
            if attempts >= 10:
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, "⛔ Trop de tentatives. Réessayez dans 5 minutes.")
                return redirect('core:login')
            cache.set(key, attempts + 1, 300)
        return self.get_response(request)


class AuditLogMiddleware:
    """Enregistre les accès aux pages importantes."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated and response.status_code == 404:
            JournalAudit.objects.create(
                mutualite=request.user.mutualite,
                utilisateur=request.user,
                action='MODIFICATION',
                module='core',
                description=f"Page non trouvée : {request.path}",
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
            )
        return response
