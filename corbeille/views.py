from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator

from comptabilite.models import DeletedItem
from core.models import Utilisateur


class RequireMutualiteMixin:
    def dispatch(self, request, *args, **kwargs):
        self.mutualite = request.user.mutualite
        if not self.mutualite:
            messages.error(request, "Aucune mutualité associée à votre compte.")
            return redirect('dashboard:index')
        return super().dispatch(request, *args, **kwargs)


class CorbeilleListView(LoginRequiredMixin, RequireMutualiteMixin, ListView):
    model = DeletedItem
    template_name = 'corbeille/liste.html'
    context_object_name = 'items'
    paginate_by = 30

    def get_queryset(self):
        qs = DeletedItem.objects.filter(
            mutualite=self.mutualite,
            restored_at__isnull=True,
            purged_at__isnull=True
        ).select_related(
            'content_type', 'deleted_by', 'restored_by', 'purged_by'
        )

        f = self.request.GET

        if f.get('type'):
            qs = qs.filter(type_objet=f['type'])

        if f.get('date_debut'):
            qs = qs.filter(deleted_at__date__gte=f['date_debut'])
        if f.get('date_fin'):
            qs = qs.filter(deleted_at__date__lte=f['date_fin'])

        if f.get('deleted_by'):
            qs = qs.filter(deleted_by_id=f['deleted_by'])

        if f.get('expires') == '1':
            qs = qs.filter(expire_at__lt=timezone.now())
        elif f.get('expires') == '0':
            qs = qs.filter(expire_at__gte=timezone.now())

        if f.get('q'):
            q = f['q']
            qs = qs.filter(
                Q(objet_repr__icontains=q) |
                Q(type_objet__icontains=q)
            )

        if f.get('app'):
            app_filter = f['app']
            if app_filter == 'membres':
                qs = qs.filter(type_objet__in=['AFFILIE', 'AYANT_DROIT', 'ORIGINE', 'GROUPE'])
            elif app_filter == 'sante':
                qs = qs.filter(type_objet__in=['SERVICE_SANTE', 'MEDICAMENT', 'PARTENAIRE'])
            elif app_filter == 'cotisations':
                qs = qs.filter(type_objet__in=['COTISATION'])
            elif app_filter == 'facturation':
                qs = qs.filter(type_objet__in=['FACTURE'])
            elif app_filter == 'finance':
                qs = qs.filter(type_objet__in=['ECRITURE', 'COMPTE', 'CENTRE', 'BUDGET', 'PREVISION', 'RAPPROCHEMENT'])

        return qs.order_by('-deleted_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        base_qs = DeletedItem.objects.filter(
            mutualite=self.mutualite,
            restored_at__isnull=True,
            purged_at__isnull=True
        )

        ctx['stats'] = {
            'total': base_qs.count(),
            'expires': base_qs.filter(expire_at__lt=timezone.now()).count(),
            'par_type': dict(base_qs.values_list('type_objet').annotate(c=Count('id'))),
        }

        ctx['types'] = DeletedItem.TYPE_CHOICES
        ctx['apps'] = [
            ('membres', 'Membres'),
            ('sante', 'Santé'),
            ('cotisations', 'Cotisations'),
            ('facturation', 'Facturation'),
            ('finance', 'Finance & Comptabilité'),
        ]

        ctx['deleted_by_users'] = Utilisateur.objects.filter(
            mutualite=self.mutualite,
            corbeille_supprimes__isnull=False
        ).distinct()

        ctx['peut_purger'] = self.request.user.est_admin or self.request.user.est_super_admin
        ctx['current_app'] = self.request.GET.get('app', '')

        return ctx


class CorbeilleDetailView(LoginRequiredMixin, RequireMutualiteMixin, DetailView):
    model = DeletedItem
    template_name = 'corbeille/detail.html'
    context_object_name = 'item'

    def get_queryset(self):
        return DeletedItem.objects.filter(mutualite=self.mutualite).select_related(
            'content_type', 'deleted_by', 'restored_by', 'purged_by'
        )


@require_POST
def corbeille_restaurer(request, pk):
    mutualite = request.user.mutualite
    item = get_object_or_404(DeletedItem, pk=pk, mutualite=mutualite)

    if item.restored_at:
        return JsonResponse({'success': False, 'error': 'Déjà restauré'})

    try:
        item.restaurer(request.user)
        messages.success(request, f"Élément restauré : {item.objet_repr}")
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def corbeille_restaurer_multiple(request):
    mutualite = request.user.mutualite
    ids = request.POST.getlist('ids[]')

    if not ids:
        return JsonResponse({'success': False, 'error': 'Aucun élément sélectionné'})

    items = DeletedItem.objects.filter(
        mutualite=mutualite,
        restored_at__isnull=True,
        purged_at__isnull=True,
        pk__in=ids
    )
    count = 0
    for item in items:
        try:
            item.restaurer(request.user)
            count += 1
        except Exception:
            pass

    return JsonResponse({'success': True, 'count': count})


@require_POST
def corbeille_purger(request, pk):
    mutualite = request.user.mutualite
    item = get_object_or_404(DeletedItem, pk=pk, mutualite=mutualite)

    if not (request.user.est_admin or request.user.est_super_admin):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    try:
        item.purger(request.user)
        messages.success(request, f"Élément purgé : {item.objet_repr}")
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@require_POST
def corbeille_purger_multiple(request):
    mutualite = request.user.mutualite

    if not (request.user.est_admin or request.user.est_super_admin):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    ids = request.POST.getlist('ids[]')
    if not ids:
        return JsonResponse({'success': False, 'error': 'Aucun élément sélectionné'})

    items = DeletedItem.objects.filter(mutualite=mutualite, pk__in=ids)
    count = 0
    for item in items:
        try:
            item.purger(request.user)
            count += 1
        except Exception:
            pass

    return JsonResponse({'success': True, 'count': count})


@require_POST
def corbeille_vider_expires(request):
    mutualite = request.user.mutualite

    if not (request.user.est_admin or request.user.est_super_admin):
        return JsonResponse({'success': False, 'error': 'Permission refusée'})

    items = DeletedItem.objects.filter(
        mutualite=mutualite,
        restored_at__isnull=True,
        purged_at__isnull=True,
        expire_at__lt=timezone.now()
    )
    count = items.count()

    for item in items:
        try:
            item.purger(request.user)
        except Exception:
            pass

    return JsonResponse({'success': True, 'count': count})