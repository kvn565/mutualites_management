import logging
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger('core.tenant')


class Mutualite(models.Model):
    """Modèle tenant — une mutualité cliente de la plateforme SaaS."""

    TYPE_MUTUALITE = [
        ('SANTE', 'Santé'),
        ('EPARGNE', 'Épargne et crédit'),
        ('PROFESSIONNELLE', 'Professionnelle'),
        ('COMMUNAUTAIRE', 'Communautaire'),
        ('AUTRE', 'Autre'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ESSAI', 'Essai gratuit'),
        ('ACTIF', 'Actif'),
        ('SUSPENDU', 'Suspendu'),
        ('EXPIRE', 'Expiré'),
        ('BLOQUE', 'Bloqué'),
    ]

    # ── Identification ──────────────────────────────────────────
    code_mutualite = models.CharField(
        max_length=20, unique=True, verbose_name='Code mutualité',
        help_text='Code unique généré automatiquement',
        blank=True, null=True,
    )
    nif = models.CharField(
        max_length=50, unique=True, verbose_name='NIF',
        help_text="Numéro d'Identification Fiscale",
        blank=True, null=True,
    )
    nom = models.CharField(max_length=200, verbose_name='Nom de la mutualité')
    sigle = models.CharField(max_length=20, blank=True, verbose_name='Sigle/Abréviation')
    slug = models.SlugField(unique=True, verbose_name='Identifiant')
    type_mutualite = models.CharField(
        max_length=20, choices=TYPE_MUTUALITE, default='SANTE',
        verbose_name='Type de mutualité',
    )
    # ── Responsable ─────────────────────────────────────────────
    nom_responsable = models.CharField(
        max_length=200, blank=True, verbose_name='Nom du responsable',
    )
    fonction_responsable = models.CharField(
        max_length=100, blank=True, verbose_name='Fonction du responsable',
    )
    telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')

    # ── Logo ─────────────────────────────────────────────────────
    logo = models.ImageField(
        upload_to='logos_mutualite/', blank=True, null=True,
        verbose_name='Logo de la mutualité',
    )
    signature = models.ImageField(
        upload_to='signatures_mutualite/', blank=True, null=True,
        verbose_name='Signature du responsable',
    )

    # ── Apparence / Thème ──────────────────────────────────────
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
    background_image = models.ImageField(
        upload_to='themes_mutualite/', blank=True, null=True,
        verbose_name='Image de fond',
        help_text="Image d'arrière-plan pour le portail partenaire",
    )
    background_opacity = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.25,
        verbose_name='Opacité',
        help_text='Opacité de l\'image (0.00 = invisible, 1.00 = opaque)',
    )
    background_brightness = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.40,
        verbose_name='Luminosité',
        help_text='Luminosité de l\'image (0.00 = noir, 1.00 = normal, 2.00 = très lumineux)',
    )
    text_color = models.CharField(
        max_length=7, default='#1e293b',
        verbose_name='Couleur du texte',
        help_text='Format hexa (ex: #1e293b)',
    )

    # ── Localisation ────────────────────────────────────────────
    province = models.CharField(max_length=100, blank=True, verbose_name='Province')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
    quartier = models.CharField(max_length=100, blank=True, verbose_name='Quartier')
    adresse = models.TextField(blank=True, verbose_name='Adresse')

    # ── Essai gratuit ───────────────────────────────────────────
    essai_gratuit = models.BooleanField(
        default=False, verbose_name='Essai gratuit',
    )
    date_debut_essai = models.DateTimeField(
        null=True, blank=True, verbose_name='Date début essai',
    )
    date_fin_essai = models.DateTimeField(
        null=True, blank=True, verbose_name='Date fin essai',
    )

    # ── Abonnement (sans clé — connexion libre) ───────────────────
    date_activation = models.DateTimeField(
        null=True, blank=True, verbose_name="Date d'activation",
    )
    date_expiration = models.DateTimeField(
        null=True, blank=True, verbose_name="Date d'expiration",
    )
    type_abonnement = models.CharField(
        max_length=20, blank=True, verbose_name="Type d'abonnement",
    )
    max_utilisateurs = models.PositiveIntegerField(
        default=10, verbose_name="Nombre max d'utilisateurs",
    )

    # ── Modules optionnels ────────────────────────────────────────
    module_chambres_actif = models.BooleanField(
        default=False, verbose_name='Module Gestion des Chambres actif',
        help_text='Activer la gestion des chambres d\'hospitalisation pour cette mutualité',
    )

    # ── Compte admin (créé lors de l'inscription) ──────────────
    username_admin = models.CharField(
        max_length=150, blank=True, verbose_name="Username admin",
    )
    email_admin = models.EmailField(
        blank=True, verbose_name="Email admin",
    )

    # ── Statut ──────────────────────────────────────────────────
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE',
        verbose_name='Statut',
    )

    # ── Modules activés ────────────────────────────────────────
    module_chambres_actif = models.BooleanField(
        default=False, verbose_name='Module Gestion des Chambres',
        help_text='Activer la gestion des chambres d\'hospitalisation',
    )

    # ── Plafonds par défaut (appliqués aux nouveaux affiliés) ───
    def_cotisation_mensuelle = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Cotisation mensuelle (BIF)',
    )
    def_soins_ambulatoires = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Soins Ambulatoires (BIF)',
    )
    def_limite_hospitalisation_generale = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Hospitalisation Générale (BIF)',
    )
    def_hopital_plafond_chambre = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Hôpital plafond chambre/nuit (BIF)',
    )
    def_hpc_nuit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='HPC / Nuit (BIF)',
    )
    def_limite_laboratoire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Laboratoire (BIF)',
    )
    def_limite_imagerie_medicale = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Imagerie Médicale (BIF)',
    )
    def_limite_kinesitherapie = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Kinésithérapie (BIF)',
    )
    def_limite_reanimation = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Réanimation (BIF)',
    )
    def_maternite_forfait = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Maternité forfait (BIF)',
    )
    def_pourcentage_maternite = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Pourcentage Maternité (%)',
    )
    def_pharmacie_forfait = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Pharmacie forfait (BIF)',
    )
    def_limites_medicaments = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limites Médicaments (BIF)',
    )
    def_limites_lunettes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limites Lunettes (verre et monture) (BIF)',
    )
    def_limites_dents = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limites Soins Dentaires (BIF)',
    )

    # ── Audit ───────────────────────────────────────────────────
    created_by = models.ForeignKey(
        'Utilisateur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mutualites_crees',
        verbose_name='Créé par',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # ── Anciens champs (conservés pour compatibilité) ───────────
    actif = models.BooleanField(default=True, verbose_name='Actif')
    # Les champs métier (taux_cotisation_base, etc.) sont supprimés
    # car le SuperAdmin ne gère que la plateforme, pas les opérations internes.

    class Meta:
        verbose_name = 'Mutualité'
        verbose_name_plural = 'Mutualités'
        ordering = ['-date_creation']

    def __str__(self):
        return f"{self.code_mutualite} — {self.nom}"

    def save(self, *args, **kwargs):
        if not self.code_mutualite:
            self.code_mutualite = self._generer_code()
        if not self.slug:
            base = slugify(self.nom or 'mutualite')
            self.slug = base
            counter = 1
            while Mutualite.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base}-{counter}"
                counter += 1
        self._mettre_a_jour_statut()
        if self.statut in ('ACTIF', 'ESSAI'):
            try:
                from single_tenant.models import SingleTenantConfig
                cfg = SingleTenantConfig.objects.filter(statut='ACTIVE').first()
                if cfg and cfg.mutualite_id and cfg.mutualite_id != self.pk:
                    self.statut = 'SUSPENDU'
            except Exception:
                pass
        super().save(*args, **kwargs)

    def _generer_code(self):
        """Génère un code mutualité unique au format MUT-XXXXX."""
        import secrets
        alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        while True:
            code = 'MUT-' + ''.join(secrets.choice(alphabet) for _ in range(6))
            if not Mutualite.objects.filter(code_mutualite=code).exists():
                return code

    def _mettre_a_jour_statut(self):
        """Mode sans clé : connexion libre, aucun blocage automatique.

        Préserve EN_ATTENTE (demande en attente de validation),
        BLOQUE et SUSPENDU (décisions manuelles).
        """
        if self.statut in ('BLOQUE', 'SUSPENDU', 'EN_ATTENTE'):
            return
        # Toute autre mutualité est ACTIF (pas d'expiration auto sans clé).
        if self.statut != 'ACTIF':
            self.statut = 'ACTIF'
        return

    def activer_essai(self, cree_par=None):
        """Conservé pour compatibilité : active directement sans clé."""
        now = timezone.now()
        self.essai_gratuit = False
        self.date_activation = now
        self.type_abonnement = 'SANS_CLE'
        self.statut = 'ACTIF'
        self.save()

    @property
    def chef(self):
        return self.utilisateurs.filter(role='ADMIN_MUTUALITE').first()

    @property
    def inscription_complete(self):
        return self.utilisateurs.filter(role='ADMIN_MUTUALITE').exists()



class TenantManager(models.Manager):
    """Manager qui filtre automatiquement par mutualité courante."""

    def get_queryset(self):
        qs = super().get_queryset()
        
        # Filtrage Soft Delete
        if hasattr(self.model, 'is_deleted'):
            qs = qs.filter(is_deleted=False)
        elif hasattr(self.model, 'supprime'):
            qs = qs.filter(supprime=False)
            
        mutualite = get_current_mutualite()
        if mutualite:
            return qs.filter(mutualite=mutualite)
        return qs


def get_current_mutualite():
    """Retourne la mutualité courante depuis le thread local ou la session."""
    from threading import current_thread
    return getattr(current_thread(), 'current_mutualite', None)


def set_current_mutualite(mutualite):
    from threading import current_thread
    current_thread().current_mutualite = mutualite


class Utilisateur(AbstractUser):
    ROLE_CHOICES = [
        ('SUPER_ADMIN',     'Super Administrateur'),
        ('ADMIN_MUTUALITE', 'Administrateur Mutualité'),
        ('COMPTABLE',       'Comptable'),
        ('AGENT',           'Agent'),
        ('CONSULTATION',    'Consultation seule'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='utilisateurs',
        verbose_name='Mutualité',
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default='AGENT', verbose_name='Rôle',
    )
    telephone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    photo = models.ImageField(upload_to='users/', blank=True, null=True, verbose_name='Photo')
    actif = models.BooleanField(default=True, verbose_name='Actif')
    date_creation = models.DateTimeField(auto_now_add=True)
    derniere_modification = models.DateTimeField(auto_now=True)
    nom = models.CharField(max_length=100, blank=True, verbose_name='Nom')
    postnom = models.CharField(max_length=100, blank=True, verbose_name='Postnom')
    prenom = models.CharField(max_length=100, blank=True, verbose_name='Prénom')

    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return self.nom_complet or self.username

    @property
    def nom_complet(self):
        nom = self.nom or self.last_name
        prenom = self.prenom or self.first_name
        return ' '.join(p for p in [nom, prenom] if p) or self.username

    @property
    def initiales(self):
        nom = self.nom or self.last_name
        prenom = self.prenom or self.first_name
        parts = [prenom, nom]
        return ''.join(p[0].upper() for p in parts if p) or self.username[0].upper()

    @property
    def est_super_admin(self):
        return self.role == 'SUPER_ADMIN' or self.is_superuser

    @property
    def est_admin(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN_MUTUALITE') or self.is_superuser

    @property
    def est_comptable(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN_MUTUALITE', 'COMPTABLE') or self.is_superuser

    @property
    def est_agent(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN_MUTUALITE', 'COMPTABLE', 'AGENT') or self.is_superuser

    @property
    def peut_modifier(self):
        return self.role != 'CONSULTATION'

    @property
    def peut_supprimer(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN_MUTUALITE') or self.is_superuser

    @property
    def peut_valider(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN_MUTUALITE', 'COMPTABLE') or self.is_superuser

    @property
    def peut_exporter(self):
        return self.role in ('SUPER_ADMIN', 'ADMIN_MUTUALITE', 'COMPTABLE') or self.is_superuser

    @property
    def menus_autorises(self):
        from django.apps import apps
        Menu = apps.get_model('groupe', 'Menu')
        if self.est_admin or self.est_super_admin:
            return list(Menu.objects.filter(actif=True).values_list('url_name', flat=True))
        menu_ids = self.groupes.values_list('menus__id', flat=True)
        return list(Menu.objects.filter(id__in=menu_ids, actif=True).values_list('url_name', flat=True))


class JournalAudit(models.Model):
    ACTION_CHOICES = [
        ('CREATION', 'Création'), ('MODIFICATION', 'Modification'),
        ('SUPPRESSION', 'Suppression'), ('CONNEXION', 'Connexion'),
        ('DECONNEXION', 'Déconnexion'), ('VALIDATION', 'Validation'),
        ('REJET', 'Rejet'), ('PAIEMENT', 'Paiement'),
        ('EXPORT', 'Export'), ('RESTAURATION', 'Restauration'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='journaux',
        verbose_name='Mutualité',
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='journaux', verbose_name='Utilisateur',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, db_index=True, verbose_name='Action')
    module = models.CharField(max_length=100, db_index=True, verbose_name='Module')
    description = models.TextField(verbose_name='Description')
    objet_type = models.CharField(max_length=100, blank=True, verbose_name='Type objet')
    objet_id = models.PositiveIntegerField(null=True, blank=True, verbose_name='ID objet')
    adresse_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='Adresse IP')
    date_action = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date')

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journal d'audit"
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.get_action_display()} — {self.module} — {self.date_action:%d/%m/%Y %H:%M}"


class HistoriqueConnexion(models.Model):
    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='connexions',
        verbose_name='Mutualité',
    )
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE,
        related_name='connexions', verbose_name='Utilisateur',
    )
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    date_connexion = models.DateTimeField(auto_now_add=True)
    date_deconnexion = models.DateTimeField(null=True, blank=True)
    succes = models.BooleanField(default=True, verbose_name='Connexion réussie')

    class Meta:
        verbose_name = 'Historique de connexion'
        verbose_name_plural = 'Historique des connexions'
        ordering = ['-date_connexion']

    def __str__(self):
        return f"{self.utilisateur} — {self.date_connexion:%d/%m/%Y %H:%M}"

    def terminer_session(self):
        self.date_deconnexion = timezone.now()
        self.save(update_fields=['date_deconnexion'])


class ConfigurationApp(models.Model):
    nom_app = models.CharField(
        max_length=100, default='Mutualité de Santé',
        verbose_name="Nom de l'application",
    )
    logo_app = models.ImageField(
        upload_to='config_app/', blank=True, null=True,
        verbose_name="Logo de l'application",
    )
    favicon = models.ImageField(
        upload_to='config_app/', blank=True, null=True,
        verbose_name='Favicône',
    )
    primary_color = models.CharField(
        max_length=7, default='#0a5c36',
        verbose_name='Couleur principale',
        help_text='Format hexadécimal (ex: #0a5c36)',
    )
    accent_color = models.CharField(
        max_length=7, default='#c9a84c',
        verbose_name='Couleur secondaire',
        help_text='Format hexadécimal (ex: #c9a84c)',
    )
    background_color = models.CharField(
        max_length=7, default='#f0f4f8',
        verbose_name='Couleur de fond',
        help_text='Format hexadécimal (ex: #f0f4f8)',
    )
    background_image = models.ImageField(
        upload_to='config_app/', blank=True, null=True,
        verbose_name='Image de fond',
        help_text="Image d'arrière-plan pour la page de connexion",
    )
    background_opacity = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.25,
        verbose_name='Opacité',
        help_text='Opacité de l\'image (0.00 = invisible, 1.00 = opaque)',
    )
    background_brightness = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.40,
        verbose_name='Luminosité',
        help_text='Luminosité de l\'image (0.00 = noir, 1.00 = normal, 2.00 = très lumineux)',
    )
    text_color = models.CharField(
        max_length=7, default='#1e293b',
        verbose_name='Couleur du texte',
        help_text='Format hexa (ex: #1e293b)',
    )

    class Meta:
        verbose_name = "Configuration de l'application"
        verbose_name_plural = "Configuration de l'application"

    def __str__(self):
        return self.nom_app

    @classmethod
    def get_config(cls):
        config = cls.objects.first()
        if not config:
            config = cls.objects.create(nom_app='Mutualité de Santé')
        return config


class Notification(models.Model):
    TYPE_CHOICES = [
        ('APPROCHE', 'Approche limite (95%)'),
        ('ATTEINT', 'Limite atteinte (100%)'),
        ('DEBLOCAGE', 'Débloqué par la mutualité'),
        ('BLOCAGE_DEF', 'Bloqué définitivement'),
        ('FACTURE', 'Nouvelle facture'),
    ]

    mutualite = models.ForeignKey(Mutualite, on_delete=models.CASCADE, related_name='notifications')
    affilie = models.ForeignKey('affilies.Affilie', on_delete=models.CASCADE, related_name='notifications')
    type_notification = models.CharField(max_length=20, choices=TYPE_CHOICES, verbose_name='Type')
    message = models.TextField()
    consommation = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Consommation mensuelle (BIF)')
    plafond = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Plafond mensuel (BIF)')
    pourcentage = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Pourcentage atteint')
    vue = models.BooleanField(default=False, verbose_name='Vue')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        s = f"[{self.get_type_notification_display()}] {self.affilie.nom_complet}"
        if self.pourcentage:
            s += f" — {self.pourcentage}%"
        return s


class MutualiteExclusion(models.Model):
    mutualite = models.ForeignKey(Mutualite, on_delete=models.CASCADE, related_name='exclusions_globales')
    medicament = models.ForeignKey('pharmacie.Medicament', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Médicament')
    service = models.ForeignKey('services_sante.ServiceSante', on_delete=models.CASCADE, null=True, blank=True, verbose_name='Service')
    motif = models.TextField(blank=True, verbose_name="Motif d'exclusion")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Créé par',
    )

    objects = TenantManager()

    class Meta:
        verbose_name = 'Exclusion globale'
        verbose_name_plural = 'Exclusions globales'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(medicament__isnull=False, service__isnull=True) |
                    models.Q(medicament__isnull=True, service__isnull=False)
                ),
                name='mutualite_exclusion_un_seul_type',
                violation_error_message='Une exclusion doit concerner soit un médicament, soit un service.',
            ),
        ]

    def __str__(self):
        if self.medicament:
            return f"Global → Médicament: {self.medicament.nom}"
        if self.service:
            return f"Global → Service: {self.service.nom}"
        return f"Exclusion globale #{self.pk}"
