from decimal import Decimal
from django.db import transaction as db_transaction
from django.utils import timezone
from .models import Ventilation, VentilationHistory, RegleVentilation, Branche
from comptabilite.models import CentreAnalytique


@db_transaction.atomic
def ventiler_ecriture(ecriture, utilisateur=None, forcer=False):
    """
    Ventile automatiquement une écriture selon les règles actives.
    Retourne la liste des ventilations créées.
    """
    if ecriture.statut != 'VALIDE':
        return []

    # Si déjà ventilée manuellement et pas de force, ne pas écraser
    ventilations_existantes = Ventilation.objects.filter(ecriture=ecriture)
    if ventilations_existantes.exists():
        if not forcer:
            return list(ventilations_existantes)
        ventilations_existantes.delete()

    # Mapper le type d'écriture vers le type d'origine des règles
    mapping_origine = {
        'AUTO_COTISATION': 'COTISATION',
        'AUTO_PRESTATION': 'PRESTATION',
        'AUTO_FACTURE': 'FACTURE',
        'MANUEL': 'TOUT',
    }
    type_origine = mapping_origine.get(ecriture.origine, 'TOUT')

    # Règles applicables
    regles = RegleVentilation.objects.filter(
        mutualite=ecriture.mutualite,
        actif=True,
    ).filter(
        type_origine__in=[type_origine, 'TOUT'],
    ).order_by('priorite')

    if not regles.exists():
        return []

    created = []
    montant_restant = ecriture.montant
    pourcentage_utilise = Decimal('0.00')

    # Appliquer les règles non "solde restant" d'abord
    regles_normales = regles.filter(appliquer_solde_restant=False)
    regles_solde = regles.filter(appliquer_solde_restant=True)

    for regle in regles_normales:
        pct = regle.pourcentage
        if pourcentage_utilise + pct > 100:
            pct = Decimal('100.00') - pourcentage_utilise
        if pct <= 0:
            continue

        montant = (ecriture.montant * pct / Decimal('100.00')).quantize(Decimal('0.01'))
        v = Ventilation.objects.create(
            mutualite=ecriture.mutualite,
            ecriture=ecriture,
            centre=regle.centre,
            branche=regle.branche,
            pourcentage=pct,
            montant=montant,
            type_ventilation='AUTO',
            statut='VALIDEE',
            regle=regle,
            enregistre_par=utilisateur,
        )
        _historique(v, 'CREATION', utilisateur)
        created.append(v)
        pourcentage_utilise += pct
        montant_restant -= montant

    if montant_restant > 0 and pourcentage_utilise < 100:
        # Appliquer les règles "solde restant"
        for regle in regles_solde:
            if montant_restant <= 0:
                break
            pct = regle.pourcentage
            if pourcentage_utilise + pct > 100:
                pct = Decimal('100.00') - pourcentage_utilise
            if pct <= 0:
                continue
            montant = (montant_restant * pct / Decimal('100.00')).quantize(Decimal('0.01'))
            v = Ventilation.objects.create(
                mutualite=ecriture.mutualite,
                ecriture=ecriture,
                centre=regle.centre,
                branche=regle.branche,
                pourcentage=pct,
                montant=montant,
                type_ventilation='AUTO',
                statut='VALIDEE',
                regle=regle,
                enregistre_par=utilisateur,
            )
            _historique(v, 'CREATION', utilisateur)
            created.append(v)
            pourcentage_utilise += pct
            montant_restant -= montant

    return created


def _historique(ventilation, action, utilisateur, ancien=None):
    """Enregistre une entrée d'historique pour une ventilation."""
    kwargs = {
        'ventilation': ventilation,
        'action': action,
        'utilisateur': utilisateur or ventilation.enregistre_par,
    }
    if ancien:
        kwargs.update({
            'ancien_pourcentage': ancien.get('pourcentage'),
            'nouveau_pourcentage': ventilation.pourcentage,
            'ancien_montant': ancien.get('montant'),
            'nouveau_montant': ventilation.montant,
            'ancien_centre': ancien.get('centre'),
            'nouveau_centre': ventilation.centre,
            'ancienne_branche': ancien.get('branche'),
            'nouvelle_branche': ventilation.branche,
        })
    VentilationHistory.objects.create(**kwargs)


@db_transaction.atomic
def re_ventiler(ventilation, nouveau_pourcentage, nouveau_montant,
                nouveau_centre=None, nouvelle_branche=None, utilisateur=None,
                commentaire=''):
    """Modifie une ventilation existante et trace l'historique."""
    ancien = {
        'pourcentage': ventilation.pourcentage,
        'montant': ventilation.montant,
        'centre': ventilation.centre,
        'branche': ventilation.branche,
    }
    ventilation.pourcentage = nouveau_pourcentage
    ventilation.montant = nouveau_montant
    ventilation.centre = nouveau_centre or ventilation.centre
    ventilation.branche = nouvelle_branche or ventilation.branche
    ventilation.save()
    _historique(ventilation, 'REVENTILATION', utilisateur, ancien)
    return ventilation


def resumer_ventilations(mutualite, date_debut, date_fin, centre=None, branche=None):
    """
    Retourne un résumé des ventilations par centre/branche pour une période.
    """
    from django.db.models import Sum
    qs = Ventilation.objects.filter(
        mutualite=mutualite,
        statut='VALIDEE',
        ecriture__date__gte=date_debut,
        ecriture__date__lte=date_fin,
    )
    if centre:
        qs = qs.filter(centre=centre)
    if branche:
        qs = qs.filter(branche=branche)

    # Résumé par centre
    par_centre = qs.values('centre__code', 'centre__libelle').annotate(
        total=Sum('montant'),
        total_pct=Sum('pourcentage'),
    ).order_by('-total')

    # Résumé par branche
    par_branche = qs.values('branche__code', 'branche__libelle').annotate(
        total=Sum('montant'),
    ).order_by('-total')

    # Résumé croisé centre × branche
    croise = qs.values(
        'centre__code', 'centre__libelle',
        'branche__code', 'branche__libelle',
    ).annotate(total=Sum('montant')).order_by('centre__code', 'branche__code')

    return {
        'par_centre': par_centre,
        'par_branche': par_branche,
        'croise': croise,
        'total_ventile': qs.aggregate(total=Sum('montant'))['total'] or 0,
    }


def exporter_ventilations_csv(queryset):
    """Génère le contenu CSV des ventilations sélectionnées."""
    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Pièce', 'Montant écriture', 'Centre', 'Branche',
                     'Pourcentage', 'Montant ventilé', 'Type', 'Statut', 'Commentaire'])
    for v in queryset.select_related('ecriture', 'centre', 'branche').iterator():
        writer.writerow([
            v.ecriture.date,
            v.ecriture.piece_reference,
            str(v.ecriture.montant),
            str(v.centre) if v.centre else '',
            str(v.branche) if v.branche else '',
            str(v.pourcentage),
            str(v.montant),
            v.get_type_ventilation_display(),
            v.get_statut_display(),
            v.commentaire,
        ])
    return output.getvalue()
