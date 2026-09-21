from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from core.models import TenantManager, Mutualite, get_current_mutualite
from comptabilite.models import SoftDeleteMixin


class PartenaireManager(TenantManager):
    def get_queryset(self):
        return super().get_queryset().filter(supprime=False)


class Partenaire(SoftDeleteMixin):
    TYPE_CHOICES = [
        ('HOPITAL', 'Hôpital'),
        ('CENTRE_SANTE', 'Centre de Santé'),
        ('CLINIQUE', 'Clinique'),
        ('PHARMACIE', 'Pharmacie'),
        ('LABORATOIRE', 'Laboratoire'),
        ('AMBULANCE', 'Ambulance'),
        ('CABINET_MEDICAL', 'Cabinet Médical'),
        ('DENTISTE', 'Dentiste'),
        ('OPTICIEN', 'Opticien'),
        ('KINESITHERAPEUTE', 'Kinésithérapeute'),
        ('AUTRE', 'Autre'),
    ]

    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('SUSPENDU', 'Suspendu'),
        ('BLOQUE', 'Bloqué'),
        ('EXPIRE', 'Expiré'),
        ('EN_ATTENTE', 'En attente'),
    ]

    CODE_PREFIX_MAP = {
        'HOPITAL': 'HOP',
        'CENTRE_SANTE': 'CDS',
        'CLINIQUE': 'CLI',
        'PHARMACIE': 'PHA',
        'LABORATOIRE': 'LAB',
        'AMBULANCE': 'AMB',
        'CABINET_MEDICAL': 'CAB',
        'DENTISTE': 'DEN',
        'OPTICIEN': 'OPT',
        'KINESITHERAPEUTE': 'KIN',
        'AUTRE': 'AUT',
    }

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    code_partenaire = models.CharField(
        max_length=20, unique=True, verbose_name='Code partenaire',
        help_text='Généré automatiquement (ex: HOP-0001, PHA-0001)',
    )
    type_partenaire = models.CharField(
        max_length=20, choices=TYPE_CHOICES, db_index=True,
        verbose_name='Type de partenaire',
    )
    nom_etablissement = models.CharField(
        max_length=200, verbose_name="Nom de l'établissement",
    )
    nif = models.CharField(max_length=50, blank=True, verbose_name='NIF')
    assujetti_tva = models.BooleanField(default=False, verbose_name='Assujetti à la TVA')
    logo = models.ImageField(
        upload_to='logos_partenaires/', blank=True, null=True,
        verbose_name='Logo',
    )
    # ── Thème / Apparence ──────────────────────────────────────────
    primary_color = models.CharField(
        max_length=7, default='#0a5c36',
        verbose_name='Couleur principale',
        help_text='Format hexa (ex: #0a5c36)',
    )
    accent_color = models.CharField(
        max_length=7, default='#c9a84c',
        verbose_name='Couleur secondaire',
        help_text='Format hexa (ex: #c9a84c)',
    )
    background_color = models.CharField(
        max_length=7, default='#f0f4f8',
        verbose_name='Couleur de fond',
        help_text='Format hexa (ex: #f0f4f8)',
    )
    text_color = models.CharField(
        max_length=7, default='#1e293b',
        verbose_name='Couleur du texte',
        help_text='Format hexa (ex: #1e293b)',
    )
    background_image = models.ImageField(
        upload_to='themes_partenaires/', blank=True, null=True,
        verbose_name='Image de fond',
        help_text="Image d'arrière-plan pour le portail partenaire",
    )
    background_opacity = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.25,
        verbose_name='Opacité',
        help_text="Opacité de l'image (0.00 = invisible, 1.00 = opaque)",
    )
    background_brightness = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.40,
        verbose_name='Luminosité',
        help_text="Luminosité de l'image (0.00 = noir, 1.00 = normal, 2.00 = très lumineux)",
    )
    numero_agrement = models.CharField(
        max_length=50, blank=True, verbose_name="Numéro d'agrément",
    )

    province = models.CharField(max_length=100, blank=True, verbose_name='Province')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
    zone = models.CharField(max_length=100, blank=True, verbose_name='Zone')
    quartier = models.CharField(max_length=100, blank=True, verbose_name='Quartier')
    avenue = models.CharField(max_length=100, blank=True, verbose_name='Avenue')
    numero = models.CharField(max_length=50, blank=True, verbose_name='Numéro')
    colline = models.CharField(max_length=100, blank=True, verbose_name='Colline')
    adresse_complete = models.TextField(blank=True, verbose_name='Adresse complète')

    telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    telephone_secondaire = models.CharField(
        max_length=50, blank=True, verbose_name='Téléphone secondaire',
    )
    email = models.EmailField(blank=True, verbose_name='Email')
    site_web = models.URLField(blank=True, verbose_name='Site web')

    nom_responsable = models.CharField(
        max_length=200, blank=True, verbose_name='Nom du responsable',
    )
    fonction_responsable = models.CharField(
        max_length=100, blank=True, verbose_name='Fonction du responsable',
    )
    telephone_responsable = models.CharField(
        max_length=50, blank=True, verbose_name='Téléphone du responsable',
    )
    email_responsable = models.EmailField(
        blank=True, verbose_name='Email du responsable',
    )

    date_debut_convention = models.DateField(
        null=True, blank=True, verbose_name='Date début convention',
    )
    date_fin_convention = models.DateField(
        null=True, blank=True, verbose_name='Date fin convention',
    )
    taux_prise_en_charge = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Taux de prise en charge (%)',
    )
    plafond_couverture = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Plafond de couverture',
    )
    observations = models.TextField(blank=True, verbose_name='Observations')

    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE', db_index=True,
    )

    created_by = models.ForeignKey(
        'core.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='partenaires_crees', verbose_name='Créé par',
    )
    supprime = models.BooleanField(default=False, db_index=True, verbose_name='Supprimé')
    date_suppression = models.DateTimeField(null=True, blank=True, verbose_name='Date de suppression')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = PartenaireManager()
    all_objects = models.Manager()

    class Meta:
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'
        ordering = ['nom_etablissement']

    def __str__(self):
        return f"{self.code_partenaire} — {self.nom_etablissement}"

    def save(self, *args, **kwargs):
        if not self.code_partenaire:
            self.code_partenaire = self.generer_code(self.type_partenaire)
        super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, hard=False, user=None):
        if hard:
            super(SoftDeleteMixin, self).delete(using=using, keep_parents=keep_parents)
        else:
            self.soft_delete(user=user)

    def soft_delete(self, user=None):
        # Sauvegarder le statut original avant de le changer
        self._statut_avant_suppression = self.statut
        self.supprime = True
        self.statut = 'EXPIRE'
        self.date_suppression = timezone.now()
        self.save(update_fields=['supprime', 'statut', 'date_suppression'])
        # Enregistrer dans DeletedItem pour la corbeille
        from comptabilite.models import DeletedItem
        DeletedItem.objects.enregistrer(self, user)

    def restore(self, user=None):
        self.supprime = False
        self.date_suppression = None
        # Restaurer le statut original
        if hasattr(self, '_statut_avant_suppression'):
            self.statut = self._statut_avant_suppression
        else:
            # Fallback : lire depuis DeletedItem
            from comptabilite.models import DeletedItem
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(self)
            deleted = DeletedItem.objects.filter(
                content_type=ct, object_id=self.pk, mutualite=self.mutualite, restored_at__isnull=True
            ).first()
            if deleted and deleted.objet_data.get('statut'):
                self.statut = deleted.objet_data['statut']
        self.save(update_fields=['supprime', 'date_suppression', 'statut'])
        # Marquer comme restauré dans DeletedItem
        from comptabilite.models import DeletedItem
        from django.contrib.contenttypes.models import ContentType
        ct = ContentType.objects.get_for_model(self)
        DeletedItem.objects.filter(
            content_type=ct,
            object_id=self.pk,
            mutualite=self.mutualite,
            restored_at__isnull=True
        ).update(restored_at=timezone.now(), restored_by=user)

    def _serialiser_pour_corbeille(self):
        return {
            'code_partenaire': self.code_partenaire,
            'type_partenaire': self.type_partenaire,
            'nom_etablissement': self.nom_etablissement,
            'nif': self.nif,
            'telephone': self.telephone,
            'email': self.email,
            'statut': self.statut,
            'taux_prise_en_charge': str(self.taux_prise_en_charge) if self.taux_prise_en_charge else None,
            'plafond_couverture': str(self.plafond_couverture) if self.plafond_couverture else None,
        }

    @classmethod
    def generer_code(cls, type_partenaire):
        prefix = cls.CODE_PREFIX_MAP.get(type_partenaire, 'AUT')
        base = f"{prefix}-"
        codes = cls._base_manager.filter(
            code_partenaire__startswith=base
        ).values_list('code_partenaire', flat=True)
        max_num = 0
        for c in codes:
            try:
                num_part = int(c.split('-')[-1])
                if num_part > max_num:
                    max_num = num_part
            except (ValueError, IndexError):
                pass
        num = max(max_num + 1, 1)
        code = f"{base}{num:04d}"
        while cls._base_manager.filter(code_partenaire=code).exists():
            num += 1
            code = f"{base}{num:04d}"
        return code

    @property
    def convention_active(self):
        if not self.date_fin_convention:
            return bool(self.date_debut_convention)
        return self.date_fin_convention >= timezone.now().date()

    @property
    def nb_factures(self):
        from factures.models import Facture
        return Facture._base_manager.filter(partenaire=self).count()

    @property
    def mutualites_liees(self):
        ids = set()
        if self.mutualite_id:
            ids.add(self.mutualite_id)
        active_rel = self.relations.filter(statut='ACTIVE').values_list('mutualite_id', flat=True)
        ids.update(active_rel)
        active_conv = self.conventions.filter(statut='ACTIVE').values_list('mutualite_id', flat=True)
        ids.update(active_conv)
        return Mutualite.objects.filter(pk__in=ids)

    @property
    def conventions_actives(self):
        return self.conventions.filter(statut='ACTIVE')


class RelationPartenaireMutualite(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACTIVE', 'Active'),
        ('BLOQUEE', 'Bloquée'),
        ('REJETEE', 'Rejetée'),
    ]

    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.CASCADE,
        related_name='relations', verbose_name='Partenaire',
    )
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        related_name='relations_partenaires', verbose_name='Mutualité',
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE', db_index=True,
        verbose_name='Statut',
    )
    date_demande = models.DateTimeField(auto_now_add=True, verbose_name='Date de la demande')
    date_action = models.DateTimeField(null=True, blank=True, verbose_name="Date d'action")
    bloque_par_partenaire = models.BooleanField(default=False, verbose_name='Bloqué par le partenaire')

    class Meta:
        unique_together = ('partenaire', 'mutualite')
        verbose_name = 'Relation partenaire-mutualité'
        verbose_name_plural = 'Relations partenaires-mutualités'
        ordering = ['-date_demande']

    def __str__(self):
        return f"{self.partenaire} ↔ {self.mutualite} [{self.get_statut_display()}]"


class Convention(models.Model):
    STATUT_CHOICES = [
        ('ACTIVE', 'Active'),
        ('SUSPENDUE', 'Suspendue'),
        ('EXPIREE', 'Expirée'),
        ('RESILIEE', 'Résiliée'),
    ]

    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.CASCADE,
        related_name='conventions', verbose_name='Partenaire',
    )
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='conventions',
        verbose_name='Mutualité',
    )
    numero_convention = models.CharField(
        max_length=50, unique=True, verbose_name='Numéro de convention',
    )
    date_debut = models.DateField(verbose_name='Date de début')
    date_fin = models.DateField(verbose_name='Date de fin')
    taux_prise_en_charge = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Taux de prise en charge (%)',
    )
    plafond_couverture = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name='Plafond de couverture',
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='ACTIVE', db_index=True,
    )
    observations = models.TextField(blank=True, verbose_name='Observations')
    document = models.FileField(
        upload_to='conventions/', blank=True, null=True,
        verbose_name='Document scanné',
    )

    created_by = models.ForeignKey(
        'core.Utilisateur', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='conventions_crees', verbose_name='Créé par',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Convention'
        verbose_name_plural = 'Conventions'
        ordering = ['-date_debut']

    def __str__(self):
        return f"{self.numero_convention} — {self.partenaire.nom_etablissement}"

    def save(self, *args, **kwargs):
        if not self.numero_convention:
            self.numero_convention = self._generer_numero()
        if not self.mutualite_id and self.partenaire_id:
            self.mutualite = self.partenaire.mutualite
        super().save(*args, **kwargs)

    def _generer_numero(self):
        today = timezone.now()
        annee = today.year
        base = f"CONV-{annee}-"
        codes = Convention._base_manager.filter(
            numero_convention__startswith=base
        ).values_list('numero_convention', flat=True)
        max_num = 0
        for c in codes:
            try:
                num_part = int(c.split('-')[-1])
                if num_part > max_num:
                    max_num = num_part
            except (ValueError, IndexError):
                pass
        num = max(max_num + 1, len(codes) + 1, 1)
        numero = f"{base}{num:04d}"
        while Convention._base_manager.filter(numero_convention=numero).exists():
            num += 1
            numero = f"{base}{num:04d}"
        return numero


class UtilisateurPartenaire(models.Model):
    ROLE_CHOICES = [
        ('GESTIONNAIRE', 'Gestionnaire'),
        ('PHARMACIEN', 'Pharmacien'),
        ('MEDECIN', 'Médecin'),
        ('RECEPTIONNISTE', 'Réceptionniste'),
        ('COMPTABLE', 'Comptable'),
    ]

    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.CASCADE,
        related_name='utilisateurs', verbose_name='Partenaire',
    )
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='utilisateurs_partenaires',
        verbose_name='Mutualité',
    )
    username = models.CharField(max_length=100, unique=True, verbose_name="Nom d'utilisateur")
    email = models.EmailField(blank=True, verbose_name='Email')
    telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    password = models.CharField(max_length=255, verbose_name='Mot de passe')
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='GESTIONNAIRE',
        verbose_name='Rôle',
    )
    actif = models.BooleanField(default=True, verbose_name='Actif')
    photo = models.ImageField(
        upload_to='utilisateurs_partenaires/', blank=True, null=True,
        verbose_name='Photo du gestionnaire',
    )

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Utilisateur partenaire'
        verbose_name_plural = 'Utilisateurs partenaires'
        ordering = ['username']

    def __str__(self):
        return f"{self.username} ({self.partenaire.nom_etablissement})"

    def save(self, *args, **kwargs):
        if not self.mutualite_id and self.partenaire_id:
            self.mutualite = self.partenaire.mutualite
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    @property
    def nom_affichage(self):
        return f"{self.username} ({self.get_role_display()})"


class DocumentMedical(models.Model):
    TYPE_CHOICES = [
        ('ORDONNANCE', 'Ordonnance'),
        ('RESULTAT_ANALYSE', "Résultat d'analyse"),
        ('COMPTE_RENDU', 'Compte rendu médical'),
        ('IMAGERIE', "Imagerie médicale"),
        ('CARTE_MEMBRE', 'Carte membre'),
        ('AUTRE', 'Autre'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='documents_medicaux',
        verbose_name='Mutualité',
    )
    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.CASCADE,
        related_name='documents_medicaux', verbose_name='Hôpital',
    )
    affilie = models.ForeignKey(
        'affilies.Affilie', on_delete=models.CASCADE,
        related_name='documents_medicaux', verbose_name='Membre',
    )
    ayant_droit = models.ForeignKey(
        'ayants_droit.AyantDroit', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents_medicaux',
        verbose_name='Ayant droit',
    )
    facture = models.ForeignKey(
        'factures.Facture', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents_medicaux',
        verbose_name='Facture liée',
    )
    type_document = models.CharField(
        max_length=30, choices=TYPE_CHOICES, default='AUTRE',
        verbose_name='Type de document',
    )
    fichier = models.FileField(
        upload_to='dossiers_medicaux/%Y/%m/', verbose_name='Fichier',
    )
    description = models.TextField(blank=True, verbose_name='Description')
    cree_par_partenaire = models.ForeignKey(
        'UtilisateurPartenaire', on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Créé par',
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Document médical'
        verbose_name_plural = 'Documents médicaux'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.get_type_document_display()} — {self.affilie.nom_complet}"
