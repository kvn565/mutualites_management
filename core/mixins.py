# core/mixins.py
"""
Mixins de permissions basés sur les rôles pour les vues basées sur des classes.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin):
    """Mixin de base avec vérification de rôle."""
    roles_requis = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if self.roles_requis and not request.user.est_admin:
            role = request.user.role
            if role not in self.roles_requis:
                messages.error(request, "⛔ Vous n'avez pas les permissions nécessaires.")
                return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(LoginRequiredMixin):
    """Réservé aux administrateurs."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.est_admin:
            messages.error(request, "⛔ Accès réservé aux administrateurs.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class ComptableRequiredMixin(LoginRequiredMixin):
    """Réservé aux comptables et supérieurs."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.est_comptable:
            messages.error(request, "⛔ Accès réservé aux comptables.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class ModificationRequiredMixin(LoginRequiredMixin):
    """Interdit les modifications pour le rôle Consultation."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.peut_modifier:
            messages.error(request, "⛔ Vous êtes en mode consultation uniquement.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class MutualiteRequiredMixin(LoginRequiredMixin):
    """Bloque les Super Admins et isole par mutualité."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if request.user.est_super_admin:
            messages.warning(request, "⛔ Les Super Admins ne peuvent pas gérer les données d'une mutualité spécifique.")
            return redirect('superadmin:dashboard')
        return super().dispatch(request, *args, **kwargs)


def enregistrer_audit(request, action, module, description, objet_type='', objet_id=None):
    """Enregistre une action dans le journal d'audit."""
    from .models import JournalAudit
    try:
        JournalAudit.objects.create(
            utilisateur=request.user if request.user.is_authenticated else None,
            action=action,
            module=module,
            description=description,
            objet_type=objet_type,
            objet_id=objet_id,
            adresse_ip=request.META.get('REMOTE_ADDR', ''),
        )
    except Exception:
        pass
