# dashboard/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import timedelta
import json


@login_required
def index(request):
    # ── Superadmin et staff Django n'ont pas de mutualité ─────────
    if request.user.est_super_admin:
        return redirect('superadmin:dashboard')
    if request.user.is_superuser or request.user.is_staff:
        return redirect('admin:index')

    now = timezone.now()
    mois = now.month
    annee = now.year

    stats = {
        'nb_affilies': 0,
        'nb_ayants_droit': 0,
        'nb_partenaires': 0,
        'cotisations_mois': 0,
        'factures_mois': 0,
        'factures_en_attente': 0,
        'solde': 0,
        'top_partenaires': [],
        'alertes': [],
        'affilies_recents': [],
    }

    # ── Modèles importés une seule fois ──────────────────────────
    Affilie = AyantDroit = Partenaire = Cotisation = Facture = None

    try:
        from affilies.models import Affilie as _Affilie
        Affilie = _Affilie
    except Exception:
        pass

    try:
        from ayants_droit.models import AyantDroit as _AD
        AyantDroit = _AD
    except Exception:
        pass

    try:
        from partenaires.models import Partenaire as _Part
        Partenaire = _Part
    except Exception:
        pass

    try:
        from cotisations.models import Cotisation as _Cot
        Cotisation = _Cot
    except Exception:
        pass

    try:
        from factures.models import Facture as _Fac
        Facture = _Fac
    except Exception:
        pass

    # ── Filtre par la mutualité de l'utilisateur ─────────────────
    mutualite = request.user.mutualite

    # ── Comptages ────────────────────────────────────────────────
    if Affilie:
        stats['nb_affilies'] = Affilie.objects.filter(mutualite=mutualite, actif=True, supprime=False).count()
        stats['affilies_recents'] = Affilie.objects.filter(mutualite=mutualite, supprime=False).order_by('-date_creation')[:5]

    if AyantDroit:
        stats['nb_ayants_droit'] = AyantDroit.objects.filter(mutualite=mutualite, actif=True, supprime=False).count()

    if Partenaire:
        stats['nb_partenaires'] = Partenaire.objects.filter(mutualite=mutualite, statut='ACTIF').count()
        stats['top_partenaires'] = Partenaire.objects.filter(mutualite=mutualite, statut='ACTIF').annotate(
            factures_count=Count('factures')
        ).order_by('-factures_count')[:5]

    if Cotisation:
        stats['cotisations_mois'] = Cotisation.objects.filter(
            mutualite=mutualite,
            mois=mois,
            annee=annee,
            statut='PAYE'
        ).aggregate(total=Sum('montant'))['total'] or 0

    if Facture:
        stats['factures_mois'] = Facture.objects.filter(
            mutualite=mutualite,
            date__month=mois,
            date__year=annee,
        ).exclude(statut__in=['REJETE', 'BROUILLON']).aggregate(total=Sum('montant_mutualite'))['total'] or 0

        stats['factures_en_attente'] = Facture.objects.filter(mutualite=mutualite, statut='SOUMIS').count()

    stats['solde'] = stats['cotisations_mois'] - stats['factures_mois']

    # ── Graphique 6 derniers mois ─────────────────────────────────
    labels = []
    data_cotisations = []
    data_factures = []

    for i in range(5, -1, -1):
        d = now - timedelta(days=i * 30)
        labels.append(d.strftime('%b %Y'))

        c_val = 0
        if Cotisation:
            c_val = float(Cotisation.objects.filter(
                mutualite=mutualite,
                mois=d.month,
                annee=d.year,
                statut='PAYE'
            ).aggregate(t=Sum('montant'))['t'] or 0)
        data_cotisations.append(c_val)

        f_val = 0
        if Facture:
            f_val = float(Facture.objects.filter(
                mutualite=mutualite,
                date__month=d.month,
                date__year=d.year,
            ).exclude(statut__in=['REJETE', 'BROUILLON']).aggregate(t=Sum('montant_mutualite'))['t'] or 0)
        data_factures.append(f_val)

    return render(request, 'dashboard/index.html', {
        **stats,
        'chart_labels': json.dumps(labels),
        'chart_cotisations': json.dumps(data_cotisations),
        'chart_factures': json.dumps(data_factures),
        'mois_nom': now.strftime('%B %Y'),
    })

