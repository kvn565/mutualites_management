from django.db.models import Sum, Q
from django.utils import timezone
from decimal import Decimal

def consommation_mensuelle_affilie(affilie, mois=None, annee=None):
    today = timezone.localdate()
    mois = mois or today.month
    annee = annee or today.year

    from factures.models import Facture
    total = Facture.objects.filter(
        affilie=affilie,
        date__year=annee,
        date__month=mois,
        statut__in=['SOUMIS', 'VALIDE', 'PAYE'],
    ).aggregate(total=Sum('montant_mutualite'))['total'] or Decimal('0.00')

    return total


def verifier_plafond_affilie(affilie, mois=None, annee=None):
    plafond = affilie.plafond_mensuel
    if plafond <= 0:
        return

    today = timezone.localdate()
    mois = mois or today.month
    annee = annee or today.year

    consommation = consommation_mensuelle_affilie(affilie, mois, annee)
    pourcentage = (consommation / plafond) * 100 if plafond > 0 else 0

    from core.models import Notification

    if pourcentage >= 100:
        if not affilie.bloque and not affilie.bloque_definitif:
            affilie.bloque = True
            affilie.save(update_fields=['bloque'])
            Notification.objects.create(
                mutualite=affilie.mutualite,
                affilie=affilie,
                type_notification='ATTEINT',
                message=(
                    f"L'affilié {affilie.nom_complet} ({affilie.numero_affiliation}) "
                    f"a atteint {pourcentage:.0f}% de son plafond mensuel "
                    f"({consommation:,.0f} FBU / {plafond:,.0f} FBU). "
                    f"Compte bloqué."
                ),
                consommation=consommation,
                plafond=plafond,
                pourcentage=pourcentage,
            )
    elif pourcentage >= 95:
        existing = Notification.objects.filter(
            affilie=affilie,
            type_notification='APPROCHE',
            vue=False,
        ).exists()
        if not existing:
            Notification.objects.create(
                mutualite=affilie.mutualite,
                affilie=affilie,
                type_notification='APPROCHE',
                message=(
                    f"L'affilié {affilie.nom_complet} ({affilie.numero_affiliation}) "
                    f"a atteint {pourcentage:.0f}% de son plafond mensuel "
                    f"({consommation:,.0f} FBU / {plafond:,.0f} FBU)."
                ),
                consommation=consommation,
                plafond=plafond,
                pourcentage=pourcentage,
            )
