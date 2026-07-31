import json
from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse

from .models import Facture, LigneFacture
from .forms import FactureForm, LigneFactureFormSet
from core.mixins import enregistrer_audit
from affilies.models import Affilie
from ayants_droit.models import AyantDroit
from partenaires.models import Partenaire
from services_sante.models import ServiceSante
from pharmacie.models import Medicament


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
    mois = request.GET.get('mois', '')
    annee = request.GET.get('annee', '')

    if q:
        qs = qs.filter(
            Q(numero__icontains=q) |
            Q(partenaire__nom_etablissement__icontains=q) |
            Q(affilie__nom__icontains=q) |
            Q(affilie__prenom__icontains=q) |
            Q(affilie__numero_affiliation__icontains=q) |
            Q(affilie__numero_carte_identite__icontains=q)
        )
    if statut:
        qs = qs.filter(statut=statut)
    if mois:
        qs = qs.filter(date__month=mois)
    if annee:
        qs = qs.filter(date__year=annee)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    factures = paginator.get_page(page)

    from datetime import datetime
    annee_courante = datetime.now().year
    annees = [str(a) for a in range(annee_courante, annee_courante - 5, -1)]

    return render(request, 'factures/liste.html', {
        'factures': factures,
        'q': q,
        'statut': statut,
        'mois': mois,
        'annee': annee,
        'total': qs.count(),
        'statut_choices': Facture.STATUT_CHOICES,
        'mois_choices': [
            (1, 'Janvier'), (2, 'Février'), (3, 'Mars'), (4, 'Avril'),
            (5, 'Mai'), (6, 'Juin'), (7, 'Juillet'), (8, 'Août'),
            (9, 'Septembre'), (10, 'Octobre'), (11, 'Novembre'), (12, 'Décembre'),
        ],
        'annees': annees,
    })


@login_required
def journal(request):
    if _check_super_admin(request.user):
        messages.warning(request, "Accès réservé aux utilisateurs de la mutualité.")
        return redirect('superadmin:dashboard')

    mutualite = request.user.mutualite
    if not mutualite:
        messages.error(request, "Aucune mutualité associée.")
        return redirect('dashboard')

    annee = request.GET.get('annee', str(date.today().year))
    try:
        annee = int(annee)
    except ValueError:
        annee = date.today().year

    q = request.GET.get('q', '').strip()

    facture_qs = Facture.objects.filter(
        mutualite=mutualite,
        date__year=annee,
        statut__in=('SOUMIS', 'VALIDE', 'PAYE'),
        affilie__isnull=False,
    ).select_related('affilie')

    rows = {}
    for fac in facture_qs:
        aff = fac.affilie
        pk = aff.pk
        if pk not in rows:
            rows[pk] = {
                'affilie': aff,
                'mois': [0] * 13,
            }
        rows[pk]['mois'][fac.date.month] += fac.montant_total

    lignes = sorted(rows.values(), key=lambda r: (r['affilie'].nom, r['affilie'].prenom))
    for r in lignes:
        r['total'] = sum(r['mois'][1:])

    if q:
        q_lower = q.lower()
        lignes = [
            r for r in lignes
            if q_lower in r['affilie'].numero_affiliation.lower()
            or (r['affilie'].numero_carte_identite and q_lower in r['affilie'].numero_carte_identite.lower())
            or q_lower in r['affilie'].nom.lower()
            or q_lower in r['affilie'].prenom.lower()
        ]

    total_mut = facture_qs.aggregate(Sum('montant_mutualite'))['montant_mutualite__sum'] or 0
    total_global = facture_qs.aggregate(Sum('montant_total'))['montant_total__sum'] or 0

    total_par_mois = [0] * 13
    for r in lignes:
        for i in range(1, 13):
            total_par_mois[i] += r['mois'][i]

    annees_qs = list(Facture.objects.filter(
        mutualite=mutualite, affilie__isnull=False,
    ).dates('date', 'year', order='DESC'))
    annees_list = sorted(set(
        [a.year for a in annees_qs] + list(range(date.today().year, date.today().year - 5, -1))
    ), reverse=True)

    paginator = Paginator(lignes, 15)
    page = request.GET.get('page', 1)
    lignes_page = paginator.get_page(page)

    return render(request, 'factures/journal.html', {
        'lignes': lignes_page,
        'annee': annee,
        'q': q,
        'annees': annees_list,
        'total_mut': total_mut,
        'total_global': total_global,
        'total_par_mois': total_par_mois,
        'mois_noms': ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                       'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'],
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
        form = FactureForm(initial={'numero': Facture.generer_numero(), 'date': date.today()})
        form.fields['ayant_droit'].queryset = AyantDroit.objects.none()
        formset = LigneFactureFormSet()

    mutualite = request.user.mutualite

    if not Partenaire.objects.filter(mutualite=mutualite).exists():
        Partenaire.objects.create(
            mutualite=mutualite,
            code_partenaire=f"MUT-{mutualite.pk:04d}",
            nom_etablissement=mutualite.nom,
            type_partenaire='CENTRE_SANTE',
        )
    form.fields['partenaire'].queryset = Partenaire.objects.filter(mutualite=mutualite)

    services = ServiceSante.objects.filter(mutualite=mutualite, actif=True)
    medicaments = Medicament.objects.filter(mutualite=mutualite, actif=True, pris_en_charge=True)

    for f in formset:
        f.fields['service'].queryset = services
        f.fields['medicament'].queryset = medicaments

    services_json = json.dumps([
        {'id': s.pk, 'nom': str(s), 'taux': float(s.taux_prise_en_charge or 80)}
        for s in services
    ])
    medicaments_json = json.dumps([
        {'id': m.pk, 'nom': str(m), 'prix': float(m.prix_reference or 0), 'taux': float(m.taux_remboursement or 80)}
        for m in medicaments
    ])

    return render(request, 'factures/form.html', {
        'form': form,
        'formset': formset,
        'titre': 'Saisir une facture',
        'services': services,
        'medicaments': medicaments,
        'services_json': services_json,
        'medicaments_json': medicaments_json,
    })


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
        form.fields['partenaire'].queryset = Partenaire.objects.filter(mutualite=facture.mutualite)
        form.fields['ayant_droit'].queryset = AyantDroit.objects.filter(affilie=facture.affilie, actif=True, supprime=False) if facture.affilie else AyantDroit.objects.none()
        formset = LigneFactureFormSet(instance=facture)

    services = ServiceSante.objects.filter(mutualite=facture.mutualite, actif=True)
    medicaments = Medicament.objects.filter(mutualite=facture.mutualite, actif=True, pris_en_charge=True)
    for f in formset:
        f.fields['service'].queryset = services
        f.fields['medicament'].queryset = medicaments

    return render(request, 'factures/form.html', {'form': form, 'formset': formset, 'obj': facture, 'titre': 'Modifier la facture'})


@login_required
def rechercher_affilie_json(request):
    q = request.GET.get('q', '').strip()
    if not q or len(q) < 2:
        return JsonResponse([], safe=False)
    mutualite = request.user.mutualite
    affilies = Affilie.objects.filter(
        mutualite=mutualite, supprime=False, actif=True
    ).filter(
        Q(numero_carte_identite__icontains=q) |
        Q(numero_affiliation__icontains=q) |
        Q(nom__icontains=q) |
        Q(prenom__icontains=q)
    )[:10]
    results = []
    for a in affilies:
        ayants_droit = list(AyantDroit.objects.filter(
            affilie=a, actif=True, supprime=False
        ).values('pk', 'nom', 'postnom', 'prenom', 'lien_parente'))
        results.append({
            'pk': a.pk,
            'nom': a.nom,
            'postnom': a.postnom,
            'prenom': a.prenom,
            'numero_carte_identite': a.numero_carte_identite,
            'numero_affiliation': a.numero_affiliation,
            'ayants_droit': ayants_droit,
        })
    return JsonResponse(results, safe=False)


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
        facture.delete(user=request.user)
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
    if facture.affilie and facture.statut in ('SOUMIS', 'VALIDE', 'PAYE'):
        from core.utils import verifier_plafond_affilie
        verifier_plafond_affilie(facture.affilie)
        from core.models import Notification
        if not Notification.objects.filter(
            mutualite=facture.mutualite,
            affilie=facture.affilie,
            type_notification='FACTURE',
            message__startswith=f"Nouvelle facture {facture.numero} —",
        ).exists():
            Notification.objects.create(
                mutualite=facture.mutualite,
                affilie=facture.affilie,
                type_notification='FACTURE',
                message=(
                    f"Nouvelle facture {facture.numero} — "
                    f"{facture.affilie.nom_complet} — "
                    f"{facture.montant_mutualite:,.0f} FBU"
                ),
            )


@login_required
def soumettre(request, pk):
    if not request.user.peut_modifier:
        messages.error(request, "Permission refusée.")
        return redirect('factures:liste')
    facture = get_object_or_404(_get_facture_qs(request.user), pk=pk, statut='BROUILLON')
    if request.method == 'POST':
        if facture.affilie and facture.affilie.bloque:
            messages.error(
                request,
                f"L'affilié {facture.affilie.nom_complet} est actuellement bloqué "
                f"(plafond mensuel atteint). La soumission est refusée."
            )
            return redirect('factures:detail', pk=pk)
        facture.statut = 'SOUMIS'
        facture.save(update_fields=['statut'])
        _update_facture_totals(facture)
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
        if facture.affilie and facture.affilie.bloque:
            messages.error(
                request,
                f"L'affilié {facture.affilie.nom_complet} est bloqué "
                f"(plafond mensuel atteint). Validation refusée."
            )
            return redirect('factures:detail', pk=pk)
        facture.statut = 'VALIDE'
        facture.save(update_fields=['statut'])
        _update_facture_totals(facture)
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
