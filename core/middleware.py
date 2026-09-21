import logging
import time
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.core.cache import cache
from django.core.management import call_command

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

        self._nettoyer_mutualites_expirees()

        response = self.get_response(request)
        set_current_mutualite(None)
        return response

    def _nettoyer_mutualites_expirees(self):
        last_cleanup = cache.get('last_mutualite_cleanup')
        now = timezone.now()
        if last_cleanup and (now - last_cleanup).total_seconds() < 86400:
            return
        cache.set('last_mutualite_cleanup', now, 86400)
        try:
            from core.nettoyage import nettoyer_mutualites_en_attente
            n = nettoyer_mutualites_en_attente(jours=7)
            if n:
                logger.info(f'Nettoyage automatique : {n} mutualité(s) en attente supprimée(s).')
        except Exception as e:
            logger.error(f'Erreur nettoyage mutualités: {e}')


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