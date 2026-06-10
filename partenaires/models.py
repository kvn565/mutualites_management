from django.db import models
from django.utils import timezone
from core.models import TenantManager


class Partenaire(models.Model):
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
    numero_agrement = models.CharField(
        max_length=50, blank=True, verbose_name="Numéro d'agrément",
    )

    province = models.CharField(max_length=100, blank=True, verbose_name='Province')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
    zone = models.CharField(max_length=100, blank=True, verbose_name='Zone')
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
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Partenaire'
        verbose_name_plural = 'Partenaires'
        ordering = ['nom_etablissement']

    def __str__(self):
        return f"{self.code_partenaire} — {self.nom_etablissement}"

    def save(self, *args, **kwargs):
        if not self.code_partenaire:
            self.code_partenaire = self._generer_code()
        super().save(*args, **kwargs)

    def _generer_code(self):
        prefix = self.CODE_PREFIX_MAP.get(self.type_partenaire, 'AUT')
        last = Partenaire.objects.filter(
            code_partenaire__startswith=f'{prefix}-',
        ).order_by('code_partenaire').last()
        if last:
            num = int(last.code_partenaire.split('-')[1]) + 1
        else:
            num = 1
        return f"{prefix}-{num:04d}"

    @classmethod
    def generer_code(cls, type_partenaire):
        prefix = cls.CODE_PREFIX_MAP.get(type_partenaire, 'AUT')
        last = cls.objects.filter(
            code_partenaire__startswith=f'{prefix}-',
        ).order_by('code_partenaire').last()
        if last:
            num = int(last.code_partenaire.split('-')[1]) + 1
        else:
            num = 1
        return f"{prefix}-{num:04d}"

    @property
    def convention_active(self):
        if not self.date_fin_convention:
            return bool(self.date_debut_convention)
        return self.date_fin_convention >= timezone.now().date()

    @property
    def nb_factures(self):
        try:
            return self.factures.count()
        except Exception:
            return 0


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
        count = Convention.objects.filter(
            date_debut__year=annee,
        ).count() + 1
        return f"CONV-{annee}-{count:04d}"


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
    username = models.CharField(max_length=100, unique=True, verbose_name='Nom d\'utilisateur')
    email = models.EmailField(blank=True, verbose_name='Email')
    telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    password = models.CharField(max_length=255, verbose_name='Mot de passe')
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='GESTIONNAIRE',
        verbose_name='Rôle',
    )
    actif = models.BooleanField(default=True, verbose_name='Actif')

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
        super().save(*args, **kwargs)
