from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView
from django.http import JsonResponse, HttpResponseNotAllowed
from django.utils import timezone

from .models import SingleTenantConfig


def get_active_mutualite():
    """Retourne la mutualité unique du mode single-tenant."""
    try:
        config = SingleTenantConfig.objects.get(statut='ACTIVE')
        return config.mutualite
    except SingleTenantConfig.DoesNotExist:
        return None
    except SingleTenantConfig.MultipleObjectsReturned:
        config = SingleTenantConfig.objects.filter(statut='ACTIVE').first()
        return config.mutualite if config else None


class SingleTenantConfigView(TemplateView):
    """Vue de configuration du mode single-tenant."""
    template_name = 'single_tenant/config.html'

    def get(self, request, *args, **kwargs):
        config = SingleTenantConfig.objects.first()
        return render(request, self.template_name, {'config': config})


class SingleTenantConfigUpdateView(UpdateView):
    """Vue pour activer/désactiver la mutualité unique."""
    template_name = 'single_tenant/config_form.html'
    model = SingleTenantConfig
    fields = ['nom_instance', 'statut']
    success_url = reverse_lazy('single_tenant:config')

    def form_valid(self, form):
        if form.instance.statut == 'ACTIVE':
            SingleTenantConfig.objects.filter(pk=form.instance.pk).update(statut='INACTIVE')
            form.instance.statut = 'ACTIVE'
            form.instance.date_activation = timezone.now()
        messages.success(self.request, f"Mutualité '{form.instance.mutualite.nom}' configurée.")
        return super().form_valid(form)


def toggle_active(request, pk):
    """Active une mutualité comme unique (désactive les autres)."""
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])
    try:
        config = SingleTenantConfig.objects.get(pk=pk)
        config.statut = 'ACTIVE'
        config.date_activation = timezone.now()
        config.save()
        from core.models import Mutualite
        active = get_active_mutualite()
        if active:
            Mutualite.objects.exclude(pk=active.pk).filter(statut__in=['ACTIF', 'ESSAI']).update(statut='SUSPENDU')
        return JsonResponse({'status': 'ok', 'message': f"Mutualité '{config.mutualite.nom}' activée."})
    except SingleTenantConfig.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Configuration non trouvée.'}, status=404)
