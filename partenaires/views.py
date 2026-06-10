import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from .models import Partenaire, Convention
from .forms import PartenaireForm
from core.mixins import enregistrer_audit

logger = logging.getLogger('core.security')


def _get_mutualite_queryset(model, user):
    if user.est_super_admin:
        return model.objects.none()
    if user.mutualite_id:
        return model.objects.filter(mutualite=user.mutualite)
    return model.objects.none()


def _check_super_admin(user):
    if user.est_super_admin:
        return True
    return False


@login_required
def liste(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    qs = _get_mutualite_queryset(Partenaire, request.user)

    q = request.GET.get('q', '')
    type_partenaire = request.GET.get('type', '')
    statut = request.GET.get('statut', '')

    if q:
        qs = qs.filter(
            Q(nom_etablissement__icontains=q) |
            Q(code_partenaire__icontains=q) |
            Q(nif__icontains=q)
        )
    if type_partenaire:
        qs = qs.filter(type_partenaire=type_partenaire)
    if statut:
        qs = qs.filter(statut=statut)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    partenaires = paginator.get_page(page)

    return render(request, 'partenaires/liste.html', {
        'partenaires': partenaires,
        'q': q,
        'type': type_partenaire,
        'statut': statut,
        'total': qs.count(),
        'type_choices': Partenaire.TYPE_CHOICES,
        'statut_choices': Partenaire.STATUT_CHOICES,
    })


@login_required
def detail(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    partenaire = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    conventions = partenaire.conventions.all().order_by('-date_debut')
    factures = []
    try:
        factures = partenaire.factures.all().order_by('-date')[:20]
    except Exception as e:
        logger.warning("Erreur chargement factures pour partenaire %s: %s", pk, e)

    return render(request, 'partenaires/detail.html', {
        'partenaire': partenaire,
        'conventions': conventions,
        'factures': factures,
    })


@login_required
def ajouter(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')

    if not request.user.mutualite_id:
        messages.error(request, "Vous n'êtes pas rattaché à une mutualité.")
        return redirect('partenaires:liste')

    if request.method == 'POST':
        form = PartenaireForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.mutualite = request.user.mutualite
            obj.created_by = request.user
            obj.save()
            enregistrer_audit(request, 'CREATION', 'partenaires',
                              f"Création partenaire : {obj.nom_etablissement}",
                              'Partenaire', obj.pk)
            messages.success(request, f"Partenaire {obj.nom_etablissement} ajouté avec succès.")
            return redirect('partenaires:liste')
    else:
        initial = {}
        type_partenaire = request.GET.get('type', '')
        if type_partenaire:
            initial['code_partenaire'] = Partenaire.generer_code(type_partenaire)
        form = PartenaireForm(initial=initial)

    return render(request, 'partenaires/form.html', {
        'form': form,
        'titre': 'Ajouter un partenaire',
        'type_choices': Partenaire.TYPE_CHOICES,
    })


@login_required
def modifier(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')

    obj = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    if request.method == 'POST':
        form = PartenaireForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            enregistrer_audit(request, 'MODIFICATION', 'partenaires',
                              f"Modification partenaire : {obj.nom_etablissement}",
                              'Partenaire', obj.pk)
            messages.success(request, f"Partenaire {obj.nom_etablissement} modifié.")
            return redirect('partenaires:detail', pk=obj.pk)
    else:
        form = PartenaireForm(instance=obj)

    return render(request, 'partenaires/form.html', {
        'form': form,
        'obj': obj,
        'titre': 'Modifier le partenaire',
    })


@login_required
def supprimer(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_supprimer:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')

    obj = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    if request.method == 'POST':
        nom = obj.nom_etablissement
        if obj.nb_factures > 0:
            messages.error(request, f"Impossible de supprimer {nom} car il a des factures associées.")
            return redirect('partenaires:liste')
        obj.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'partenaires',
                          f"Suppression partenaire : {nom}",
                          'Partenaire', pk)
        messages.success(request, f"Partenaire {nom} supprimé.")
        return redirect('partenaires:liste')

    return render(request, 'partenaires/confirm_supprimer.html', {'obj': obj})


@login_required
def suspendre(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    obj = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')
    if obj.statut not in ('ACTIF', 'EN_ATTENTE'):
        messages.error(request, f"Impossible de suspendre un partenaire avec le statut '{obj.get_statut_display()}'.")
        return redirect('partenaires:detail', pk=pk)
    obj.statut = 'SUSPENDU'
    obj.save()
    enregistrer_audit(request, 'SUSPENSION', 'partenaires',
                      f"Suspension partenaire : {obj.nom_etablissement}",
                      'Partenaire', pk)
    messages.success(request, f"Partenaire {obj.nom_etablissement} suspendu.")
    return redirect('partenaires:detail', pk=pk)


@login_required
def reactiver(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    obj = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')
    if obj.statut != 'SUSPENDU':
        messages.error(request, "Seuls les partenaires suspendus peuvent être réactivés.")
        return redirect('partenaires:detail', pk=pk)
    obj.statut = 'ACTIF'
    obj.save()
    enregistrer_audit(request, 'REACTIVATION', 'partenaires',
                      f"Réactivation partenaire : {obj.nom_etablissement}",
                      'Partenaire', pk)
    messages.success(request, f"Partenaire {obj.nom_etablissement} réactivé.")
    return redirect('partenaires:detail', pk=pk)
