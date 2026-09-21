import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q

from django.utils import timezone
from .models import Partenaire, Convention, RelationPartenaireMutualite
from .forms import PartenaireForm
from core.mixins import enregistrer_audit
from core.models import Mutualite

logger = logging.getLogger('core.security')


def _get_mutualite_queryset(model, user):
    if user.est_super_admin:
        return model.objects.none()
    if user.mutualite_id:
        ids_via_relation = list(RelationPartenaireMutualite.objects.filter(
            mutualite=user.mutualite, statut='ACTIVE',
        ).values_list('partenaire_id', flat=True))
        owned_ids = list(model.objects.filter(mutualite=user.mutualite).values_list('pk', flat=True))
        all_ids = list(set(owned_ids + ids_via_relation))
        if not all_ids:
            return model.objects.none()
        return Partenaire.all_objects.filter(pk__in=all_ids, supprime=False)
    return model.objects.none()


def _get_partenaires_en_attente(mutualite):
    """Retourne les partenaires en attente qui n'ont pas encore de relation avec cette mutualité."""
    already_linked = RelationPartenaireMutualite.objects.filter(
        mutualite=mutualite,
    ).values_list('partenaire_id', flat=True)
    return Partenaire.all_objects.filter(
        mutualite__isnull=True,
        statut='EN_ATTENTE',
        supprime=False,
    ).exclude(pk__in=already_linked)


def _check_super_admin(user):
    if user.est_super_admin:
        return True
    return False


@login_required
def liste(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    filtre = request.GET.get('filtre', 'actifs')

    if filtre == 'en_attente':
        qs = _get_partenaires_en_attente(request.user.mutualite)
        paginator = Paginator(qs, 10)
        page = request.GET.get('page', 1)
        partenaires = paginator.get_page(page)
        return render(request, 'partenaires/liste.html', {
            'partenaires': partenaires,
            'filtre': filtre,
            'total': qs.count(),
            'type_choices': Partenaire.TYPE_CHOICES,
            'statut_choices': Partenaire.STATUT_CHOICES,
        })

    if filtre == 'corbeille':
        all_ids = list(Partenaire.all_objects.filter(
            mutualite=request.user.mutualite, supprime=True
        ).values_list('pk', flat=True))
        ids_via_relation = list(RelationPartenaireMutualite.objects.filter(
            mutualite=request.user.mutualite,
        ).values_list('partenaire_id', flat=True))
        corbeille_ids = list(set(all_ids + [i for i in ids_via_relation if Partenaire.all_objects.filter(pk=i, supprime=True).exists()]))
        qs = Partenaire.all_objects.filter(pk__in=corbeille_ids, supprime=True)
        paginator = Paginator(qs, 10)
        page = request.GET.get('page', 1)
        partenaires = paginator.get_page(page)
        return render(request, 'partenaires/liste.html', {
            'partenaires': partenaires,
            'filtre': filtre,
            'total': qs.count(),
            'type_choices': Partenaire.TYPE_CHOICES,
            'statut_choices': Partenaire.STATUT_CHOICES,
        })

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
        'filtre': filtre,
        'type_choices': Partenaire.TYPE_CHOICES,
        'statut_choices': Partenaire.STATUT_CHOICES,
    })


@login_required
def detail(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    partenaire = _get_mutualite_queryset(Partenaire, request.user).filter(pk=pk).first()
    if not partenaire:
        partenaire = _get_partenaires_en_attente(request.user.mutualite).filter(pk=pk).first()
    if not partenaire:
        messages.error(request, "Partenaire non trouvé.")
        return redirect('partenaires:liste')

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
        obj.delete(user=request.user)
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


@login_required
def accepter_demande(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier or not request.user.mutualite_id:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')

    mutualite = request.user.mutualite
    try:
        partenaire = Partenaire.all_objects.get(pk=pk, statut='EN_ATTENTE', mutualite__isnull=True)
    except Partenaire.DoesNotExist:
        messages.error(request, "Partenaire non trouvé ou déjà accepté.")
        return redirect('partenaires:liste')

    if RelationPartenaireMutualite.objects.filter(partenaire=partenaire, mutualite=mutualite).exists():
        messages.warning(request, "Une relation existe déjà avec ce partenaire.")
        return redirect('partenaires:liste')

    partenaire.mutualite = mutualite
    partenaire.statut = 'EN_ATTENTE'
    partenaire.save(update_fields=['mutualite', 'statut'])

    relation = RelationPartenaireMutualite(
        partenaire=partenaire,
        mutualite=mutualite,
        statut='EN_ATTENTE',
        date_action=timezone.now(),
    )
    relation.save()

    enregistrer_audit(request, 'VALIDATION', 'partenaires',
                      f"Demande partenaire : {partenaire.nom_etablissement} par {mutualite.nom} — en attente validation superadmin",
                      'Partenaire', pk)
    messages.success(request, f"Demande pour {partenaire.nom_etablissement} envoyée. En attente de validation superadmin.")
    return redirect('partenaires:liste')


@login_required
def bloquer_relation(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier or not request.user.mutualite_id:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')

    partenaire = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    relation = RelationPartenaireMutualite.objects.filter(
        partenaire=partenaire, mutualite=request.user.mutualite, statut='ACTIVE'
    ).first()
    if not relation:
        messages.error(request, "Aucune relation active avec ce partenaire.")
        return redirect('partenaires:detail', pk=pk)

    relation.statut = 'BLOQUEE'
    relation.date_action = timezone.now()
    relation.save(update_fields=['statut', 'date_action'])

    partenaire.statut = 'SUSPENDU'
    partenaire.save(update_fields=['statut'])

    enregistrer_audit(request, 'MODIFICATION', 'partenaires',
                      f"Blocage relation avec {partenaire.nom_etablissement}",
                      'RelationPartenaireMutualite', relation.pk)
    messages.success(request, f"Relation avec {partenaire.nom_etablissement} bloquée.")
    return redirect('partenaires:detail', pk=pk)


@login_required
def debloquer_relation(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier or not request.user.mutualite_id:
        messages.error(request, "Permission refusée.")
        return redirect('partenaires:liste')

    partenaire = get_object_or_404(
        _get_mutualite_queryset(Partenaire, request.user), pk=pk
    )
    relation = RelationPartenaireMutualite.objects.filter(
        partenaire=partenaire, mutualite=request.user.mutualite, statut='BLOQUEE'
    ).first()
    if not relation:
        messages.error(request, "Aucune relation bloquée avec ce partenaire.")
        return redirect('partenaires:detail', pk=pk)

    relation.statut = 'EN_ATTENTE'
    relation.date_action = timezone.now()
    relation.save(update_fields=['statut', 'date_action'])

    partenaire.statut = 'EN_ATTENTE'
    partenaire.save(update_fields=['statut'])

    enregistrer_audit(request, 'MODIFICATION', 'partenaires',
                      f"Demande déblocage {partenaire.nom_etablissement} — en attente validation superadmin",
                      'RelationPartenaireMutualite', relation.pk)
    messages.success(request, f"Demande envoyée pour {partenaire.nom_etablissement}. En attente de validation superadmin.")
    return redirect('partenaires:detail', pk=pk)


@login_required
def supprimer_attente(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    partenaire = get_object_or_404(
        _get_partenaires_en_attente(request.user.mutualite), pk=pk
    )
    partenaire.soft_delete()
    enregistrer_audit(request, 'SUPPRESSION', 'partenaires',
                      f"Mise à la corbeille du partenaire {partenaire.nom_etablissement}",
                      'Partenaire', partenaire.pk)
    messages.success(request, f"{partenaire.nom_etablissement} a été mis à la corbeille.")
    return redirect('partenaires:liste')


@login_required
def restaurer(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    partenaire = get_object_or_404(
        Partenaire.all_objects.filter(supprime=True), pk=pk
    )
    partenaire.restore(user=request.user)
    enregistrer_audit(request, 'MODIFICATION', 'partenaires',
                      f"Restauration du partenaire {partenaire.nom_etablissement}",
                      'Partenaire', partenaire.pk)
    messages.success(request, f"{partenaire.nom_etablissement} a été restauré.")
    return redirect('partenaires:liste')


from django.db.models import RestrictedError

@login_required
def purger(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    partenaire = get_object_or_404(
        Partenaire.all_objects.filter(supprime=True), pk=pk
    )
    if partenaire.nb_factures > 0:
        messages.error(request, f"Impossible de purger {partenaire.nom_etablissement} car il a des factures associées.")
        return redirect('partenaires:liste')
    nom = partenaire.nom_etablissement
    try:
        partenaire.delete(hard=True, user=request.user)
    except RestrictedError as e:
        messages.error(request, f"Impossible de purger {nom} car il est référencé par d'autres enregistrements.")
        logger.error("Erreur purge partenaire %s: %s", pk, e)
        return redirect('partenaires:liste')
    enregistrer_audit(request, 'SUPPRESSION', 'partenaires',
                      f"Suppression définitive du partenaire {nom}",
                      'Partenaire', pk)
    messages.success(request, f"{nom} a été supprimé définitivement.")
    return redirect('partenaires:liste')
