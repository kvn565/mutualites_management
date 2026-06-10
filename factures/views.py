from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum

from .models import Facture, LigneFacture
from .forms import FactureForm, LigneFactureFormSet
from core.mixins import enregistrer_audit


def _get_facture_qs(user):
    if user.est_super_admin:
        return Facture.objects.none()
    if user.mutualite_id:
        return Facture.objects.filter(mutualite=user.mutualite)
    return Facture.objects.none()


def _check_super_admin(user):
    if user.est_super_admin:
        return True
    return False


@login_required
def liste(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    qs = _get_facture_qs(request.user).select_related('partenaire', 'affilie')

    q = request.GET.get('q', '')
    statut = request.GET.get('statut', '')

    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(partenaire__nom_etablissement__icontains=q) |
            Q(affilie__nom__icontains=q) |
            Q(affilie__numero_affiliation__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    factures = paginator.get_page(page)

    return render(request, 'factures/liste.html', {
        'factures': factures,
        'q': q,
        'statut': statut,
        'total': qs.count(),
        'statut_choices': Facture.STATUT_CHOICES,
    })


@login_required
def journal(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    qs = _get_facture_qs(request.user).filter(statut='VALIDE')

    total_mut = qs.aggregate(Sum('montant_mutualite'))['montant_mutualite__sum'] or 0
    total_patient = qs.aggregate(Sum('montant_ticket_moderateur'))['montant_ticket_moderateur__sum'] or 0
    total_global = qs.aggregate(Sum('montant_total'))['montant_total__sum'] or 0

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    factures = paginator.get_page(page)

    return render(request, 'factures/journal.html', {
        'factures': factures,
        'total_mut': total_mut,
        'total_patient': total_patient,
        'total_global': total_global,
    })


@login_required
def detail(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk)
    return render(request, 'factures/detail.html', {'facture': facture})


@login_required
def ajouter(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')

    if not request.user.mutualite_id:
        messages.error(request, "Vous n'êtes pas rattaché à une mutualité.")
        return redirect('factures:liste')

    if request.method == 'POST':
        form = FactureForm(request.POST, request.FILES)
        formset = LigneFactureFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            facture = form.save(commit=False)
            if not facture.numero:
                facture.numero = Facture.generer_numero()
            facture.mutualite = request.user.mutualite
            facture.cree_par = request.user
            facture.save()

            formset.instance = facture
            lignes = formset.save()
            for ligne in lignes:
                if not ligne.mutualite_id:
                    ligne.mutualite = facture.mutualite
                    ligne.save(update_fields=['mutualite'])

            _update_facture_totals(facture)

            enregistrer_audit(request, 'CREATION', 'factures', f"Création facture : {facture.numero}", 'Facture', facture.pk)
            messages.success(request, f"Facture {facture.numero} enregistrée avec succès.")
            return redirect('factures:detail', pk=facture.pk)
    else:
        form = FactureForm(initial={'numero': Facture.generer_numero()})
        formset = LigneFactureFormSet()

    return render(request, 'factures/form.html', {'form': form, 'formset': formset, 'titre': 'Saisir une facture'})


@login_required
def modifier(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')

    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk)

    if facture.statut in ['VALIDE', 'PAYE'] and not request.user.est_admin:
        messages.error(request, "Cette facture est déjà validée ou payée, modification impossible.")
        return redirect('factures:detail', pk=pk)

    if request.method == 'POST':
        form = FactureForm(request.POST, request.FILES, instance=facture)
        formset = LigneFactureFormSet(request.POST, instance=facture)

        if form.is_valid() and formset.is_valid():
            form.save()
            lignes = formset.save()
            for ligne in lignes:
                if not ligne.mutualite_id:
                    ligne.mutualite = facture.mutualite
                    ligne.save(update_fields=['mutualite'])

            _update_facture_totals(facture)

            enregistrer_audit(request, 'MODIFICATION', 'factures', f"Modification facture : {facture.numero}", 'Facture', facture.pk)
            messages.success(request, f"Facture {facture.numero} modifiée.")
            return redirect('factures:detail', pk=facture.pk)
    else:
        form = FactureForm(instance=facture)
        formset = LigneFactureFormSet(instance=facture)

    return render(request, 'factures/form.html', {'form': form, 'formset': formset, 'obj': facture, 'titre': 'Modifier la facture'})


@login_required
def supprimer(request, pk):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    if not request.user.peut_supprimer:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')

    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk)

    if facture.statut in ['VALIDE', 'PAYE'] and not request.user.est_admin:
        messages.error(request, "Impossible de supprimer une facture validée/payée.")
        return redirect('factures:liste')

    if request.method == 'POST':
        numero = facture.numero
        facture.delete()
        enregistrer_audit(request, 'SUPPRESSION', 'factures', f"Suppression facture : {numero}", 'Facture', pk)
        messages.success(request, f"Facture {numero} supprimée.")
        return redirect('factures:liste')

    return render(request, 'factures/confirm_supprimer.html', {'obj': facture})


def _update_facture_totals(facture):
    lignes = list(facture.lignes.all())
    total = sum(l.total_ligne for l in lignes)
    mut = sum(l.part_mutualite for l in lignes)
    pat = sum(l.part_patient for l in lignes)
    Facture.objects.filter(pk=facture.pk).update(
        montant_total=total,
        montant_mutualite=mut,
        montant_ticket_moderateur=pat,
    )
    facture.montant_total = total
    facture.montant_mutualite = mut
    facture.montant_ticket_moderateur = pat


@login_required
def soumettre(request, pk):
    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')
    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk, statut='BROUILLON')
    if request.method == 'POST':
        facture.statut = 'SOUMIS'
        facture.save(update_fields=['statut'])
        enregistrer_audit(request, 'MODIFICATION', 'factures', f"Soumission facture : {facture.numero}", 'Facture', pk)
        messages.success(request, f"Facture {facture.numero} soumise pour validation.")
    return redirect('factures:detail', pk=pk)


@login_required
def valider(request, pk):
    if not request.user.peut_valider:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')
    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk, statut='SOUMIS')
    if request.method == 'POST':
        facture.statut = 'VALIDE'
        facture.save(update_fields=['statut'])
        enregistrer_audit(request, 'VALIDATION', 'factures', f"Validation facture : {facture.numero}", 'Facture', pk)
        messages.success(request, f"Facture {facture.numero} validée.")
    return redirect('factures:detail', pk=pk)


@login_required
def rejeter(request, pk):
    if not request.user.peut_valider:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')
    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk, statut='SOUMIS')
    if request.method == 'POST':
        motif = request.POST.get('motif_rejet', '').strip()
        if not motif:
            messages.error(request, "Le motif de rejet est obligatoire.")
            return redirect('factures:detail', pk=pk)
        facture.statut = 'REJETE'
        facture.motif_rejet = motif
        facture.save(update_fields=['statut', 'motif_rejet'])
        enregistrer_audit(request, 'REJET', 'factures', f"Rejet facture : {facture.numero} — {motif[:50]}", 'Facture', pk)
        messages.warning(request, f"Facture {facture.numero} rejetée.")
    return redirect('factures:detail', pk=pk)


@login_required
def marquer_paye(request, pk):
    if not request.user.peut_valider:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')
    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk, statut='VALIDE')
    if request.method == 'POST':
        facture.statut = 'PAYE'
        facture.save(update_fields=['statut'])
        enregistrer_audit(request, 'PAIEMENT', 'factures', f"Paiement facture : {facture.numero}", 'Facture', pk)
        messages.success(request, f"Facture {facture.numero} marquée comme payée.")
    return redirect('factures:detail', pk=pk)
