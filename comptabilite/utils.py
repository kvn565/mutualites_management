from decimal import Decimal
from django.utils import timezone
from django.db import transaction as db_transaction
from .models import Compte, Ecriture, CentreAnalytique, AuditComptable


def _audit(mutualite, utilisateur, action, modele, objet_id, description, ip=None):
    AuditComptable.objects.create(
        mutualite=mutualite,
        utilisateur=utilisateur,
        action=action,
        modele=modele,
        objet_id=objet_id,
        description=description,
        adresse_ip=ip,
    )


def _piece_ref(prefixe, mutualite):
    """Génère une référence de pièce comptable."""
    today = timezone.now()
    count = Ecriture.objects.filter(
        mutualite=mutualite,
        date_creation__date=today.date(),
    ).count() + 1
    return f"{prefixe}-{today.strftime('%Y%m%d')}-{count:04d}"


def comptabiliser_cotisation(cotisation, utilisateur=None, ip=None):
    """
    Comptabilise une cotisation payée :
      Débit   banque/caisse
      Crédit  cotisations (701)
    Retourne la liste des écritures créées.
    """
    mutualite = cotisation.mutualite or cotisation.affilie.mutualite
    compte_tresorerie = _compte_tresorerie(mutualite, cotisation.mode_paiement)
    compte_produit = Compte.objects.filter(mutualite=mutualite, numero='701').first()
    if not compte_tresorerie or not compte_produit:
        raise ValueError("Configuration comptable incomplète : comptes 50x ou 701 manquants.")

    piece = _piece_ref('COT', mutualite)
    libelle = f"Cotisation {cotisation.reference} — {cotisation.affilie.nom_complet}"

    ecritures = _ecriture_double(
        mutualite=mutualite,
        date=cotisation.date_paiement or cotisation.date_emission,
        piece=piece,
        libelle=libelle,
        compte_debit=compte_tresorerie,
        compte_credit=compte_produit,
        montant=cotisation.montant,
        origine='AUTO_COTISATION',
        utilisateur=utilisateur,
    )

    _audit(mutualite, utilisateur, 'COMPTABILISATION', 'ECRITURE',
           ecritures[0].id if ecritures else None,
           f"Comptabilisation cotisation {cotisation.reference}",
           ip=ip)
    return ecritures


def comptabiliser_prestation(prestation, utilisateur=None, ip=None):
    """
    Comptabilise une prestation médicale payée :
      Débit   prestations médicales (601)
      Crédit  banque/caisse
    Retourne la liste des écritures créées.
    """
    mutualite = prestation.mutualite or prestation.affilie.mutualite
    compte_charge = Compte.objects.filter(mutualite=mutualite, numero='601').first()
    compte_tresorerie = Compte.objects.filter(mutualite=mutualite, numero='571').first()
    if not compte_charge or not compte_tresorerie:
        raise ValueError("Configuration comptable incomplète : comptes 601 ou 571 manquants.")

    piece = _piece_ref('PREST', mutualite)
    libelle = f"Prestation {prestation.reference} — {prestation.affilie.nom_complet}"

    ecritures = _ecriture_double(
        mutualite=mutualite,
        date=prestation.date_paiement,
        piece=piece,
        libelle=libelle,
        compte_debit=compte_charge,
        compte_credit=compte_tresorerie,
        montant=prestation.montant_rembourse or prestation.montant_total,
        origine='AUTO_PRESTATION',
        utilisateur=utilisateur,
    )

    _audit(mutualite, utilisateur, 'COMPTABILISATION', 'ECRITURE',
           ecritures[0].id if ecritures else None,
           f"Comptabilisation prestation {prestation.reference}",
           ip=ip)
    return ecritures


def comptabiliser_facture(facture, utilisateur=None, ip=None):
    """
    Comptabilise une facture partenaire :
      Débit   charge
      Crédit  fournisseur
    """
    mutualite = facture.mutualite
    compte_fournisseur = Compte.objects.filter(mutualite=mutualite, numero='401').first()
    if not compte_fournisseur:
        raise ValueError("Compte fournisseur (401) manquant")

    piece = _piece_ref('FACT', mutualite)
    libelle = f"Facture {facture.reference} — {facture.partenaire}"

    ecritures = _ecriture_double(
        mutualite=mutualite,
        date=facture.date_facture or timezone.now().date(),
        piece=piece,
        libelle=libelle,
        compte_debit=Compte.objects.filter(mutualite=mutualite, numero='612').first(),
        compte_credit=compte_fournisseur,
        montant=facture.montant_net if hasattr(facture, 'montant_net') else facture.montant_total,
        origine='AUTO_FACTURE',
        utilisateur=utilisateur,
    )
    _audit(mutualite, utilisateur, 'COMPTABILISATION', 'ECRITURE',
           ecritures[0].id if ecritures else None,
           f"Comptabilisation facture {facture.reference}",
           ip=ip)
    return ecritures


@db_transaction.atomic
def _ecriture_double(mutualite, date, piece, libelle,
                     compte_debit, compte_credit, montant,
                     origine='MANUEL', utilisateur=None):
    """Crée l'écriture de débit et de crédit en une transaction."""
    debit = Ecriture.objects.create(
        mutualite=mutualite,
        date=date,
        piece_reference=piece,
        libelle=libelle,
        compte=compte_debit,
        type_mouvement='DEBIT',
        montant=montant,
        statut='VALIDE',
        origine=origine,
        enregistre_par=utilisateur,
        date_validation=timezone.now(),
        valide_par=utilisateur,
    )
    credit = Ecriture.objects.create(
        mutualite=mutualite,
        date=date,
        piece_reference=piece,
        libelle=libelle,
        compte=compte_credit,
        type_mouvement='CREDIT',
        montant=montant,
        statut='VALIDE',
        origine=origine,
        contrepartie=debit,
        enregistre_par=utilisateur,
        date_validation=timezone.now(),
        valide_par=utilisateur,
    )
    debit.contrepartie = credit
    debit.save(update_fields=['contrepartie'])
    return [debit, credit]


def _compte_tresorerie(mutualite, mode_paiement):
    """Retourne le compte de trésorerie selon le mode de paiement."""
    mapping = {
        'BANQUE': '50',
        'CHEQUE': '50',
        'MOBILE': '522',
        'COOPERATIVE': '50',
        'CASH': '571',
        'ESPECES': '571',
    }
    prefixe = mapping.get(mode_paiement, '571')
    return Compte.objects.filter(mutualite=mutualite, numero__startswith=prefixe).first()


def _compte_contrepartie_defaut(mutualite, type_compte):
    mapping = {
        'ACTIF': '571',
        'CHARGE': '401',
        'PRODUIT': '421',
    }
    numero = mapping.get(type_compte, '471')
    return Compte.objects.filter(mutualite=mutualite, numero=numero).first()


def generer_balance(mutualite, date_debut, date_fin, centre=None):
    """Génère la balance des comptes pour une période."""
    qs = Ecriture.objects.filter(
        mutualite=mutualite,
        statut='VALIDE',
        date__gte=date_debut,
        date__lte=date_fin,
    )
    if centre:
        qs = qs.filter(centre=centre)

    from django.db.models import Sum, Q
    balances = Compte.objects.filter(mutualite=mutualite, actif=True).annotate(
        total_debit=Sum('ecritures__montant', filter=Q(
            ecritures__in=qs, ecritures__type_mouvement='DEBIT')),
        total_credit=Sum('ecritures__montant', filter=Q(
            ecritures__in=qs, ecritures__type_mouvement='CREDIT')),
    ).order_by('numero')

    result = []
    for compte in balances:
        total_debit = compte.total_debit or Decimal('0.00')
        total_credit = compte.total_credit or Decimal('0.00')
        solde = total_debit - total_credit
        if compte.type_compte in ('PASSIF', 'PRODUIT'):
            solde = -solde
        result.append({
            'compte': compte,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'solde': solde,
        })
    return result


def generer_bilan(mutualite, date_arret):
    """Génère le bilan au 31/12/N ou à une date donnée."""
    actif = []
    passif = []
    for c in Compte.objects.filter(mutualite=mutualite, actif=True):
        s = c.solde
        if c.type_compte == 'ACTIF' and s != 0:
            actif.append({'compte': c, 'solde': s})
        elif c.type_compte == 'PASSIF' and s != 0:
            passif.append({'compte': c, 'solde': s})
    return {
        'actif': sorted(actif, key=lambda x: x['compte'].numero),
        'passif': sorted(passif, key=lambda x: x['compte'].numero),
        'total_actif': sum(a['solde'] for a in actif),
        'total_passif': sum(p['solde'] for p in passif),
    }


def generer_cpc(mutualite, date_debut, date_fin):
    """Compte de résultat (pertes et profits)."""
    charges = []
    produits = []
    qs = Ecriture.objects.filter(
        mutualite=mutualite, statut='VALIDE',
        date__gte=date_debut, date__lte=date_fin,
    )
    from django.db.models import Sum
    for c in Compte.objects.filter(mutualite=mutualite, actif=True):
        somme = qs.filter(compte=c).aggregate(
            total=Sum('montant'))['total'] or Decimal('0.00')
        if somme == 0:
            continue
        if c.type_compte == 'CHARGE':
            charges.append({'compte': c, 'total': somme})
        elif c.type_compte == 'PRODUIT':
            produits.append({'compte': c, 'total': somme})
    total_charges = sum(c['total'] for c in charges)
    total_produits = sum(p['total'] for p in produits)
    return {
        'charges': sorted(charges, key=lambda x: x['compte'].numero),
        'produits': sorted(produits, key=lambda x: x['compte'].numero),
        'total_charges': total_charges,
        'total_produits': total_produits,
        'resultat': total_produits - total_charges,
    }


def cloturer_exercice(mutualite, annee):
    """
    Clôture l'exercice : report à nouveau du résultat.
    Le résultat de l'annee N devient le solde initial de l'année N+1.
    """
    debut = timezone.date(annee, 1, 1)
    fin = timezone.date(annee, 12, 31)
    cpc = generer_cpc(mutualite, debut, fin)
    resultat = cpc['resultat']

    compte_resultat = Compte.objects.filter(mutualite=mutualite, numero='12').first()
    compte_report = Compte.objects.filter(mutualite=mutualite, numero='106').first()
    if not compte_resultat or not compte_report:
        raise ValueError("Comptes 12 (résultat) et 106 (réserves) requis.")

    with db_transaction.atomic():
        piece = f"CLOTURE-{annee}"
        if resultat >= 0:
            _ecriture_double(mutualite, fin, piece,
                             f"Affectation résultat {annee}",
                             compte_resultat, compte_report,
                             abs(resultat), 'REPORT')
        else:
            _ecriture_double(mutualite, fin, piece,
                             f"Report déficitaire {annee}",
                             compte_report, compte_resultat,
                             abs(resultat), 'REPORT')

    return resultat


def exporter_grand_livre(ecritures):
    """Retourne une liste de lignes CSV pour le grand livre."""
    lignes = ["Date;Pièce;Libellé;Compte;Débit;Crédit;Solde"]
    solde = Decimal('0.00')
    for e in ecritures.order_by('date', 'id'):
        debit = e.montant if e.type_mouvement == 'DEBIT' else Decimal('0.00')
        credit = e.montant if e.type_mouvement == 'CREDIT' else Decimal('0.00')
        solde = solde + debit - credit
        lignes.append(f"{e.date};{e.piece_reference};{e.libelle};"
                      f"{e.compte.numero};{debit};{credit};{solde}")
    return "\n".join(lignes)
