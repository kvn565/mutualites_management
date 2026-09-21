from datetime import timedelta
from django.utils import timezone


def get_mutualite_active():
    try:
        from single_tenant.models import SingleTenantConfig
        cfg = SingleTenantConfig.objects.filter(statut='ACTIVE').select_related('mutualite').first()
        return cfg.mutualite if cfg else None
    except Exception:
        return None


def reassigner_partages(m, active):
    from partenaires.models import Partenaire
    from services_sante.models import ServiceSante
    from pharmacie.models import Medicament
    from factures.models import Facture, LigneFacture
    for p in Partenaire.objects.filter(mutualite=m):
        if Facture.objects.exclude(mutualite=m).filter(partenaire=p).exists():
            p.mutualite = active
            p.save(update_fields=['mutualite'])
    for s in ServiceSante.objects.filter(mutualite=m):
        if LigneFacture.objects.exclude(mutualite=m).filter(service=s).exists():
            s.mutualite = active
            s.save(update_fields=['mutualite'])
    for med in Medicament.objects.filter(mutualite=m):
        if LigneFacture.objects.exclude(mutualite=m).filter(medicament=med).exists():
            med.mutualite = active
            med.save(update_fields=['mutualite'])


def supprimer_mutualite_complete(m):
    from django.apps import apps
    active = get_mutualite_active()
    if active and active.pk != m.pk:
        try:
            reassigner_partages(m, active)
        except Exception:
            pass
    ordre = [
        'factures.LigneFacture',
        'factures.Facture',
        'gestion_chambres.Soin',
        'gestion_chambres.MouvementChambre',
        'gestion_chambres.Hospitalisation',
        'gestion_chambres.Chambre',
        'gestion_chambres.Service',
        'gestion_chambres.Etablissement',
        'gestion_chambres.TypeChambre',
        'comptabilite.Ecriture',
        'comptabilite.RapprochementBancaire',
        'comptabilite.Budget',
        'comptabilite.PrevisionTresorerie',
        'comptabilite.AuditComptable',
        'comptabilite.DeletedItem',
        'comptabilite.CentreAnalytique',
        'comptabilite.Compte',
        'ventilations.Ventilation',
        'ventilations.VentilationGlobale',
        'ventilations.RegleVentilation',
        'ventilations.Branche',
        'cotisations.Cotisation',
        'ayants_droit.AyantDroit',
        'affilies.AffilieExclusion',
        'affilies.Affilie',
        'partenaires.DocumentMedical',
        'partenaires.Convention',
        'partenaires.UtilisateurPartenaire',
        'partenaires.RelationPartenaireMutualite',
        'partenaires.Partenaire',
        'pharmacie.Medicament',
        'pharmacie.CategorieMedicament',
        'services_sante.ServiceSante',
        'origines.OrigineExclusion',
        'origines.Origine',
        'origines.CategorieOrigine',
        'groupe.Groupe',
        'aide.ArticleAide',
        'aide.CategorieAide',
        'aide.MessageSuperAdmin',
        'core.HistoriqueConnexion',
        'core.JournalAudit',
        'core.AuditCle',
        'core.CleActivation',
        'core.MutualiteExclusion',
        'core.Notification',
        'core.Utilisateur',
    ]
    for label in ordre:
        try:
            model = apps.get_model(label)
        except Exception:
            continue
        try:
            model.objects.filter(mutualite=m).delete()
        except Exception:
            pass
    try:
        from single_tenant.models import SingleTenantConfig
        SingleTenantConfig.objects.filter(mutualite=m).delete()
    except Exception:
        pass
    m.delete()


def nettoyer_mutualites_en_attente(jours=7):
    from django.db.models import Q
    from core.models import Mutualite, JournalAudit, Utilisateur
    try:
        from single_tenant.models import SingleTenantConfig
        actif_ids = list(SingleTenantConfig.objects.filter(statut='ACTIVE').values_list('mutualite_id', flat=True))
    except Exception:
        actif_ids = []
    seuil = timezone.now() - timedelta(days=jours)
    qs = Mutualite.objects.filter(
        Q(statut='EN_ATTENTE', date_creation__lt=seuil) |
        Q(statut='SUSPENDU', date_creation__lt=seuil)
    )
    if actif_ids:
        qs = qs.exclude(pk__in=actif_ids)
    supprimes = 0
    for m in list(qs):
        age = (timezone.now() - m.date_creation).days
        try:
            supprimer_mutualite_complete(m)
        except Exception:
            continue
        JournalAudit.objects.create(
            mutualite=None,
            utilisateur=None,
            action='SUPPRESSION',
            module='core',
            description=f"Suppression automatique : mutualité '{m.nom}' ({m.code_mutualite}) en attente depuis {age} jours",
            objet_type='Mutualite',
            objet_id=m.pk,
            adresse_ip='system',
        )
        supprimes += 1
    return supprimes
