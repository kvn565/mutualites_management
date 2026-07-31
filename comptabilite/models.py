from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from decimal import Decimal
from core.models import Utilisateur, TenantManager


class SoftDeleteMixin(models.Model):
    """Mixin pour soft delete - ajoute is_deleted et deleted_at"""
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name='Supprimé')
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True, verbose_name='Supprimé le')
    deleted_by = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_deleted', verbose_name='Supprimé par'
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False, user=None):
        if hard:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.is_deleted = True
            self.deleted_at = timezone.now()
            if user:
                self.deleted_by = user
            self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
            # Enregistrer dans DeletedItem pour la corbeille
            DeletedItem.objects.enregistrer(self, user)

    def restore(self, user=None):
        """Restaure un objet soft-deleted"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
        # Marquer comme restauré dans DeletedItem
        DeletedItem.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            mutualite=getattr(self, 'mutualite', None),
            restored_at__isnull=True
        ).update(restored_at=timezone.now(), restored_by=user)


class DeletedItemQuerySet(models.QuerySet):
    def for_mutualite(self, mutualite):
        return self.filter(mutualite=mutualite)

    def actifs(self):
        return self.filter(restored_at__isnull=True, purged_at__isnull=True)

    def par_type(self, model_class):
        ct = ContentType.objects.get_for_model(model_class)
        return self.filter(content_type=ct)


class DeletedItemManager(models.Manager):
    def get_queryset(self):
        return DeletedItemQuerySet(self.model, using=self._db).select_related('content_type', 'deleted_by', 'restored_by')

    def for_mutualite(self, mutualite):
        return self.get_queryset().for_mutualite(mutualite)

    def actifs(self):
        return self.get_queryset().actifs()

    def par_type(self, model_class):
        return self.get_queryset().par_type(model_class)

    def enregistrer(self, obj, user=None):
        """Enregistre un objet supprimé dans la corbeille"""
        ct = ContentType.objects.get_for_model(obj)
        mutualite = getattr(obj, 'mutualite', None)

        # Déterminer le type d'objet
        type_mapping = {
            'Ecriture': 'ECRITURE',
            'Compte': 'COMPTE',
            'CentreAnalytique': 'CENTRE',
            'Budget': 'BUDGET',
            'PrevisionTresorerie': 'PREVISION',
            'RapprochementBancaire': 'RAPPROCHEMENT',
            'Medicament': 'MEDICAMENT',
            'ServiceSante': 'SERVICE_SANTE',
            'Affilie': 'AFFILIE',
            'AyantDroit': 'AYANT_DROIT',
            'Groupe': 'GROUPE',
            'Facture': 'FACTURE',
            'Cotisation': 'COTISATION',
        }
        type_objet = type_mapping.get(obj.__class__.__name__, 'AUTRE')

        # Calculer la date d'expiration (30 jours par défaut)
        from django.conf import settings
        jours = getattr(settings, 'CORBEILLE_RETENTION_JOURS', 30)
        expire_at = timezone.now() + timezone.timedelta(days=jours)

        return self.create(
            content_type=ct,
            object_id=obj.pk,
            mutualite=mutualite,
            type_objet=type_objet,
            objet_repr=str(obj)[:500],
            objet_data=obj._serialiser_pour_corbeille() if hasattr(obj, '_serialiser_pour_corbeille') else {},
            deleted_by=user,
            expire_at=expire_at,
        )


class DeletedItem(models.Model):
    """Modèle générique pour tracker tous les éléments dans la corbeille"""
    TYPE_CHOICES = [
        ('ECRITURE', 'Écriture comptable'),
        ('COMPTE', 'Compte comptable'),
        ('CENTRE', 'Centre analytique'),
        ('BUDGET', 'Budget'),
        ('PREVISION', 'Prévision trésorerie'),
        ('RAPPROCHEMENT', 'Rapprochement bancaire'),
        ('MEDICAMENT', 'Médicament'),
        ('SERVICE_SANTE', 'Service de santé'),
        ('AFFILIE', 'Affilié'),
        ('AYANT_DROIT', 'Ayant droit'),
        ('GROUPE', 'Groupe d\'affiliés'),
        ('FACTURE', 'Facture'),
        ('COTISATION', 'Cotisation'),
        ('AUTRE', 'Autre'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='corbeille_items',
        verbose_name='Mutualité'
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    type_objet = models.CharField(max_length=20, choices=TYPE_CHOICES, default='AUTRE', db_index=True)
    objet_repr = models.CharField(max_length=500, verbose_name='Représentation')
    objet_data = models.JSONField(default=dict, blank=True, verbose_name='Données sérialisées')

    deleted_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Supprimé le')
    deleted_by = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='corbeille_supprimes', verbose_name='Supprimé par'
    )

    restored_at = models.DateTimeField(null=True, blank=True, verbose_name='Restauré le')
    restored_by = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='corbeille_restores', verbose_name='Restauré par'
    )

    purged_at = models.DateTimeField(null=True, blank=True, verbose_name='Purgé le')
    purged_by = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='corbeille_purges', verbose_name='Purgé par'
    )

    expire_at = models.DateTimeField(db_index=True, verbose_name='Expire le', null=True, blank=True)
    auto_purge = models.BooleanField(default=True, verbose_name='Purge auto')

    objects = DeletedItemManager()

    class Meta:
        ordering = ['-deleted_at']
        verbose_name = 'Élément corbeille'
        verbose_name_plural = 'Corbeille'
        indexes = [
            models.Index(fields=['mutualite', 'deleted_at']),
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['expire_at', 'auto_purge']),
        ]

    def __str__(self):
        return f"{self.get_type_objet_display()} — {self.objet_repr} ({self.deleted_at:%d/%m/%Y})"

    def est_expire(self):
        return self.expire_at and timezone.now() >= self.expire_at

    def peut_etre_purge(self, user):
        """Seul admin mutualité ou super admin peut purger"""
        return user.est_admin or user.est_super_admin

    def get_real_instance(self):
        try:
            return self.content_type.model_class()._base_manager.get(pk=self.object_id)
        except Exception:
            return None

    def purger(self, user):
        """Supprime définitivement"""
        obj = self.get_real_instance()
        if obj and hasattr(obj, 'delete'):
            obj.delete(hard=True)
        self.purged_at = timezone.now()
        self.purged_by = user
        self.save(update_fields=['purged_at', 'purged_by'])

    def restaurer(self, user):
        """Restaure l'objet original"""
        obj = self.get_real_instance()
        if obj and hasattr(obj, 'restore'):
            obj.restore(user)
        self.restored_at = timezone.now()
        self.restored_by = user
        self.save(update_fields=['restored_at', 'restored_by'])


class PlanComptableManager(TenantManager):
    def base_syscohada(self, mutualite):
        """Crée le plan comptable SYSCOHADA de base pour une mutualité."""
        from decimal import Decimal
        base = [
            ('101', 'Capital social', 'PASSIF'),
            ('106', 'Réserves', 'PASSIF'),
            ('12',  "Résultat de l'exercice", 'PASSIF'),
            ('13',  'Subventions', 'PASSIF'),
            ('15',  'Provisions réglementées', 'PASSIF'),
            ('161', 'Emprunts', 'PASSIF'),
            ('401', 'Fournisseurs', 'PASSIF'),
            ('404', 'Personnel', 'PASSIF'),
            ('411', 'Clients', 'ACTIF'),
            ('421', 'Adhérents - cotisations à recevoir', 'ACTIF'),
            ('471', 'Comptes d\'attente', 'ACTIF'),
            ('481', 'Charges constatées d\'avance', 'ACTIF'),
            ('50',  'Banques', 'ACTIF'),
            ('521', 'Caisse espèces', 'ACTIF'),
            ('522', 'Mobile Money', 'ACTIF'),
            ('531', 'Titres de placement', 'ACTIF'),
            ('571', 'Caisse', 'ACTIF'),
            ('601', 'Prestations médicales', 'CHARGE'),
            ('602', 'Frais pharmaceutiques', 'CHARGE'),
            ('611', 'Frais de personnel', 'CHARGE'),
            ('612', 'Frais de gestion', 'CHARGE'),
            ('613', 'Frais administratifs', 'CHARGE'),
            ('62',  'Charges financières', 'CHARGE'),
            ('63',  'Dotations aux amortissements', 'CHARGE'),
            ('64',  'Dotations aux provisions', 'CHARGE'),
            ('701', 'Cotisations des adhérents', 'PRODUIT'),
            ('702', 'Revenus de placement', 'PRODUIT'),
            ('703', 'Subventions d\'exploitation', 'PRODUIT'),
            ('72',  'Produits financiers', 'PRODUIT'),
            ('75',  'Produits exceptionnels', 'PRODUIT'),
        ]
        created = []
        for code, libelle, typ in base:
            obj, _ = self.get_or_create(
                mutualite=mutualite, numero=code,
                defaults={'intitule': libelle, 'type_compte': typ, 'actif': True}
            )
            created.append(obj)
        return created


class Compte(SoftDeleteMixin):
    TYPE_COMPTE = [
        ('ACTIF', "Actif (Trésorerie/Banque/Créances)"),
        ('PASSIF', "Passif (Dettes/Capitaux propres)"),
        ('PRODUIT', "Produit (Revenus/Cotisations)"),
        ('CHARGE', "Charge (Dépenses/Prestations)"),
    ]
    CATEGORIE_SYSCOHADA = [
        ('1', 'Classe 1 — Capitaux propres'),
        ('2', 'Classe 2 — Immobilisations'),
        ('3', 'Classe 3 — Stocks'),
        ('4', 'Classe 4 — Tiers'),
        ('5', 'Classe 5 — Trésorerie'),
        ('6', 'Classe 6 — Charges'),
        ('7', 'Classe 7 — Produits'),
        ('8', 'Classe 8 — Engagements'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='comptes',
        verbose_name='Mutualité',
    )
    numero = models.CharField(max_length=20, verbose_name='Code compte')
    intitule = models.CharField(max_length=200, verbose_name='Intitulé')
    type_compte = models.CharField(max_length=20, choices=TYPE_COMPTE, verbose_name='Type')
    categorie_syscohada = models.CharField(
        max_length=2, choices=CATEGORIE_SYSCOHADA, blank=True,
        verbose_name='Classe SYSCOHADA',
    )
    solde_initial = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    compte_parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sous_comptes', verbose_name='Compte parent',
    )
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ['numero']
        unique_together = [('mutualite', 'numero')]
        verbose_name = 'Compte comptable'
        verbose_name_plural = 'Plan comptable'

    def __str__(self):
        return f"{self.numero} — {self.intitule}"

    @property
    def solde(self):
        total_debit = self.ecritures.filter(is_deleted=False, type_mouvement='DEBIT').aggregate(
            total=models.Sum('montant'))['total'] or Decimal('0.00')
        total_credit = self.ecritures.filter(is_deleted=False, type_mouvement='CREDIT').aggregate(
            total=models.Sum('montant'))['total'] or Decimal('0.00')
        if self.type_compte in ('ACTIF', 'CHARGE'):
            return self.solde_initial + total_debit - total_credit
        return self.solde_initial + total_credit - total_debit

    @property
    def solde_periode(self, debut=None, fin=None):
        qs = self.ecritures.filter(is_deleted=False)
        if debut:
            qs = qs.filter(ecriture__date__gte=debut)
        if fin:
            qs = qs.filter(ecriture__date__lte=fin)
        total_debit = qs.filter(type_mouvement='DEBIT').aggregate(
            total=models.Sum('montant'))['total'] or Decimal('0.00')
        total_credit = qs.filter(type_mouvement='CREDIT').aggregate(
            total=models.Sum('montant'))['total'] or Decimal('0.00')
        if self.type_compte in ('ACTIF', 'CHARGE'):
            return self.solde_initial + total_debit - total_credit
        return self.solde_initial + total_credit - total_debit

    def generer_ecriture(self, date, libelle, montant, type_mvt, centre=None, **kwargs):
        """Crée une écriture sur ce compte."""
        return self.ecritures.create(
            mutualite=self.mutualite,
            date=date,
            libelle=libelle,
            montant=montant,
            type_mouvement=type_mvt,
            centre=centre,
            **kwargs,
        )

    def _serialiser_pour_corbeille(self):
        return {
            'numero': self.numero,
            'intitule': self.intitule,
            'type_compte': self.type_compte,
            'categorie_syscohada': self.categorie_syscohada,
            'solde_initial': str(self.solde_initial),
            'compte_parent': self.compte_parent.numero if self.compte_parent else None,
            'description': self.description,
            'actif': self.actif,
        }


class CentreAnalytique(SoftDeleteMixin):
    TYPE_CENTRE = [
        ('ANTENNE', "Antenne locale"),
        ('REGION', "Région"),
        ('BRANCHE', "Branche maladie"),
        ('PROJET', "Projet spécifique"),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='centres_analytiques',
    )
    code = models.CharField(max_length=20, verbose_name='Code centre')
    libelle = models.CharField(max_length=200, verbose_name='Libellé')
    type_centre = models.CharField(max_length=20, choices=TYPE_CENTRE, verbose_name='Type')
    actif = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ['code']
        unique_together = [('mutualite', 'code')]
        verbose_name = 'Centre analytique'
        verbose_name_plural = 'Centres analytiques'

    def __str__(self):
        return f"{self.code} — {self.libelle}"

    def _serialiser_pour_corbeille(self):
        return {
            'code': self.code,
            'libelle': self.libelle,
            'type_centre': self.type_centre,
            'actif': self.actif,
        }


class Ecriture(SoftDeleteMixin):
    STATUT = [
        ('BROUILLON', 'Brouillon'),
        ('SOUMIS', 'Soumis — en attente de validation'),
        ('VALIDE', 'Validé'),
        ('REJETE', 'Rejeté'),
    ]
    TYPE_MOUVEMENT = [
        ('DEBIT', 'Débit'),
        ('CREDIT', 'Crédit'),
    ]
    ORIGINE = [
        ('MANUEL', 'Saisie manuelle'),
        ('AUTO_COTISATION', 'Automatique — Cotisation'),
        ('AUTO_PRESTATION', 'Automatique — Prestation'),
        ('AUTO_FACTURE', 'Automatique — Facture partenaire'),
        ('REPORT', 'Report à nouveau'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='ecritures',
    )
    date = models.DateField(db_index=True, verbose_name='Date écriture')
    piece_reference = models.CharField(max_length=50, blank=True, verbose_name='Pièce comptable nº')
    libelle = models.CharField(max_length=255, verbose_name='Libellée')
    compte = models.ForeignKey(
        Compte, on_delete=models.RESTRICT, related_name='ecritures',
        verbose_name='Compte',
    )
    type_mouvement = models.CharField(max_length=10, choices=TYPE_MOUVEMENT, verbose_name='Mouvement')
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Montant (BIF)')
    centre = models.ForeignKey(
        CentreAnalytique, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ecritures', verbose_name='Centre analytique',
    )
    origine = models.CharField(max_length=20, choices=ORIGINE, default='MANUEL')
    statut = models.CharField(max_length=20, choices=STATUT, default='BROUILLON')
    contrepartie = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ecritures_liees',
        help_text="Écriture de contrepartie dans la même pièce",
    )
    numero_lot = models.CharField(max_length=50, blank=True, verbose_name='Nº de lot')
    date_echeance = models.DateField(null=True, blank=True)
    date_validation = models.DateTimeField(null=True, blank=True)
    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ecritures_validees',
    )
    rejete_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ecritures_rejetees',
    )
    motif_rejet = models.TextField(blank=True)
    piece_jointe = models.FileField(upload_to='compta/pieces/', blank=True, null=True)
    notes = models.TextField(blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='ecritures_enregistrees',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-date', '-id']
        verbose_name = 'Écriture comptable'
        verbose_name_plural = 'Écritures comptables'

    def __str__(self):
        return f"{self.piece_reference} — {self.compte.numero} {self.type_mouvement} {self.montant} BIF"

    def valider(self, utilisateur):
        self.statut = 'VALIDE'
        self.date_validation = timezone.now()
        self.valide_par = utilisateur
        self.save(update_fields=['statut', 'date_validation', 'valide_par'])

    def rejeter(self, utilisateur, motif):
        self.statut = 'REJETE'
        self.rejete_par = utilisateur
        self.motif_rejet = motif
        self.save(update_fields=['statut', 'rejete_par', 'motif_rejet'])

    def _serialiser_pour_corbeille(self):
        date_val = self.date
        if isinstance(date_val, str):
            date_str = date_val
        else:
            date_str = date_val.isoformat() if date_val else None
        
        date_echeance_val = self.date_echeance
        if isinstance(date_echeance_val, str):
            date_echeance_str = date_echeance_val
        elif date_echeance_val:
            date_echeance_str = date_echeance_val.isoformat()
        else:
            date_echeance_str = None
        
        return {
            'date': date_str,
            'piece_reference': self.piece_reference,
            'libelle': self.libelle,
            'compte': self.compte.numero,
            'type_mouvement': self.type_mouvement,
            'montant': str(self.montant),
            'centre': self.centre.code if self.centre else None,
            'origine': self.origine,
            'statut': self.statut,
            'numero_lot': self.numero_lot,
            'date_echeance': date_echeance_str,
            'notes': self.notes,
        }


class Budget(SoftDeleteMixin):
    STATUT = [
        ('BROUILLON', 'Brouillon'),
        ('APPROUVE', 'Approuvé'),
        ('EN_EXECUTION', 'En exécution'),
        ('CLOTURE', 'Clôturé'),
    ]
    TYPE_BUDGET = [
        ('ANNUEL', 'Budget annuel'),
        ('TRIMESTRIEL', 'Budget trimestriel'),
        ('PROJET', 'Budget projet'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='budgets',
    )
    annee = models.PositiveIntegerField(verbose_name='Exercice')
    type_budget = models.CharField(max_length=20, choices=TYPE_BUDGET, default='ANNUEL')
    centre = models.ForeignKey(
        CentreAnalytique, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets',
    )
    statut = models.CharField(max_length=20, choices=STATUT, default='BROUILLON')
    description = models.TextField(blank=True)

    approuve_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='budgets_approuves',
    )
    date_approbation = models.DateTimeField(null=True, blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='budgets_enregistres',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-annee', 'centre']
        unique_together = [('mutualite', 'annee', 'centre', 'type_budget')]
        verbose_name = 'Budget'
        verbose_name_plural = 'Budgets'

    def __str__(self):
        centre = f" - {self.centre}" if self.centre else ""
        return f"Budget {self.annee}{centre}"

    @property
    def total_prevu(self):
        return self.lignes.aggregate(total=models.Sum('montant_prevu'))['total'] or Decimal('0.00')

    @property
    def total_realise(self):
        return self.lignes.aggregate(total=models.Sum('montant_realise'))['total'] or Decimal('0.00')

    @property
    def taux_execution(self):
        if self.total_prevu == 0:
            return Decimal('0.00')
        return (self.total_realise / self.total_prevu) * 100

    def _serialiser_pour_corbeille(self):
        return {
            'annee': self.annee,
            'type_budget': self.type_budget,
            'centre': self.centre.code if self.centre else None,
            'statut': self.statut,
            'description': self.description,
        }


class LigneBudget(models.Model):
    budget = models.ForeignKey(Budget, on_delete=models.CASCADE, related_name='lignes')
    compte = models.ForeignKey(Compte, on_delete=models.RESTRICT, related_name='lignes_budget')
    montant_prevu = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Montant prévu')
    montant_realise = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='Montant réalisé')
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [('budget', 'compte')]
        verbose_name = 'Ligne budgétaire'
        verbose_name_plural = 'Lignes budgétaires'

    @property
    def ecart(self):
        return self.montant_prevu - self.montant_realise

    @property
    def taux(self):
        if self.montant_prevu == 0:
            return Decimal('0.00')
        return (self.montant_realise / self.montant_prevu) * 100


class PrevisionTresorerie(SoftDeleteMixin):
    TYPE = [
        ('ENCAISSEMENT', 'Encaissement prévu'),
        ('DECAISSEMENT', 'Décaissement prévu'),
    ]
    STATUT = [
        ('PREVU', 'Prévu'),
        ('REALISE', 'Réalisé'),
        ('ANNULE', 'Annulé'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='previsions_tresorerie',
    )
    date_prevision = models.DateField(verbose_name='Date prévisionnelle')
    libelle = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    compte = models.ForeignKey(
        Compte, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='previsions',
    )
    centre = models.ForeignKey(
        CentreAnalytique, on_delete=models.SET_NULL, null=True, blank=True,
    )
    statut = models.CharField(max_length=20, choices=STATUT, default='PREVU')
    ecriture = models.ForeignKey(
        Ecriture, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='prevision',
        help_text="Écriture qui a réalisé cette prévision",
    )
    notes = models.TextField(blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ['date_prevision']
        verbose_name = 'Prévision de trésorerie'
        verbose_name_plural = 'Prévisions de trésorerie'

    def __str__(self):
        return f"{self.get_type_display()} — {self.libelle} ({self.montant} BIF)"

    def _serialiser_pour_corbeille(self):
        dp = self.date_prevision
        if isinstance(dp, str):
            try:
                from datetime import date
                dp = date.fromisoformat(dp)
            except Exception:
                dp = None
        return {
            'date_prevision': dp.isoformat() if dp else None,
            'libelle': self.libelle,
            'type': self.type,
            'montant': str(self.montant),
            'compte': self.compte.numero if self.compte else None,
            'centre': self.centre.code if self.centre else None,
            'statut': self.statut,
            'notes': self.notes,
        }


class RapprochementBancaire(SoftDeleteMixin):
    STATUT = [
        ('EN_COURS', 'En cours'),
        ('EQUILIBRE', 'Équilibré'),
        ('ECART', 'Écart constaté'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='rapprochements',
    )
    compte = models.ForeignKey(
        Compte, on_delete=models.RESTRICT, related_name='rapprochements',
        limit_choices_to={'type_compte': 'ACTIF'},
    )
    date_debut = models.DateField()
    date_fin = models.DateField()
    solde_comptable = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Solde comptable')
    solde_bancaire = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Solde bancaire')
    solde_ajuste = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name='Solde après rapprochement')
    statut = models.CharField(max_length=20, choices=STATUT, default='EN_COURS')
    date_rapprochement = models.DateTimeField(null=True, blank=True)
    rapproche_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
    )
    notes = models.TextField(blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='rapprochements_enregistres',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-date_fin']
        unique_together = [('mutualite', 'compte', 'date_fin')]
        verbose_name = 'Rapprochement bancaire'
        verbose_name_plural = 'Rapprochements bancaires'

    def __str__(self):
        return f"Rapprochement {self.compte.numero} — {self.date_debut} au {self.date_fin}"

    @property
    def ecart(self):
        return self.solde_ajuste - self.solde_bancaire

    def _serialiser_pour_corbeille(self):
        return {
            'compte': self.compte.numero,
            'date_debut': self.date_debut.isoformat(),
            'date_fin': self.date_fin.isoformat(),
            'solde_comptable': str(self.solde_comptable),
            'solde_bancaire': str(self.solde_bancaire),
            'solde_ajuste': str(self.solde_ajuste),
            'statut': self.statut,
            'notes': self.notes,
        }


class LigneRapprochement(models.Model):
    rapprochement = models.ForeignKey(
        RapprochementBancaire, on_delete=models.CASCADE, related_name='lignes',
    )
    ecriture = models.ForeignKey(
        Ecriture, on_delete=models.CASCADE, related_name='lignes_rapprochement',
    )
    rapproche = models.BooleanField(default=False, verbose_name='Pointé')
    date_pointage = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = [('rapprochement', 'ecriture')]
        verbose_name = 'Ligne de rapprochement'
        verbose_name_plural = 'Lignes de rapprochement'


class AuditComptable(models.Model):
    ACTION = [
        ('CREATION', 'Création'),
        ('MODIFICATION', 'Modification'),
        ('VALIDATION', 'Validation'),
        ('REJET', 'Rejet'),
        ('SUPPRESSION', 'Suppression'),
        ('EXPORT', 'Export'),
        ('COMPTABILISATION', 'Comptabilisation automatique'),
    ]
    MODELE = [
        ('COMPTE', 'Compte'),
        ('ECRITURE', 'Écriture'),
        ('BUDGET', 'Budget'),
        ('PREVISION', 'Prévision'),
        ('RAPPROCHEMENT', 'Rapprochement'),
        ('RAPPORT', 'Rapport'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True,
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
    )
    action = models.CharField(max_length=20, choices=ACTION)
    modele = models.CharField(max_length=20, choices=MODELE)
    objet_id = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField()
    adresse_ip = models.GenericIPAddressField(blank=True, null=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_action']
        verbose_name = 'Audit comptable'
        verbose_name_plural = 'Audits comptables'

    def __str__(self):
        return f"{self.get_action_display()} — {self.get_modele_display()} ({self.date_action})"
