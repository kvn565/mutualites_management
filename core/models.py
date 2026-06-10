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

    # ── Localisation ────────────────────────────────────────────
    province = models.CharField(max_length=100, blank=True, verbose_name='Province')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
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

    # ── Licence ─────────────────────────────────────────────────
    cle_activation = models.CharField(
        max_length=50, blank=True, verbose_name="Clé d'activation",
    )
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
        """Met à jour le statut en fonction de l'état de la licence."""
        if self.statut in ('BLOQUE', 'SUSPENDU'):
            return
        if not self.essai_gratuit and not self.cle_activation:
            if self.statut != 'EN_ATTENTE':
                self.statut = 'EN_ATTENTE'
            return
        if self.date_expiration and self.date_expiration < timezone.now():
            self.statut = 'EXPIRE'
            return
        if self.essai_gratuit:
            if self.date_fin_essai and self.date_fin_essai < timezone.now():
                self.statut = 'EXPIRE'
            else:
                self.statut = 'ESSAI'
            return
        if self.cle_activation:
            self.statut = 'ACTIF'
            return

    def activer_essai(self, cree_par=None):
        """Active la période d'essai gratuit de 14 jours."""
        from datetime import timedelta
        now = timezone.now()
        self.essai_gratuit = True
        self.date_debut_essai = now
        self.date_fin_essai = now + timedelta(days=14)
        self.statut = 'ESSAI'
        self.cle_activation = self._generer_cle_unique()
        self.date_activation = now
        self.date_expiration = self.date_fin_essai
        self.type_abonnement = 'ESSAI_14J'
        self.save()

    def _generer_cle_unique(self):
        """Génère une clé d'activation unique."""
        import secrets
        alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        while True:
            alea = ''.join(secrets.choice(alphabet) for _ in range(12))
            code = f"KEY-{self.code_mutualite}-{alea}"
            if not Mutualite.objects.filter(cle_activation=code).exists():
                return code

    def activer_licence(self, type_abonnement, duree_jours, date_debut=None):
        """Active une licence payante pour la mutualité."""
        from datetime import timedelta
        self.essai_gratuit = False
        self.cle_activation = self._generer_cle_unique()
        self.date_activation = date_debut or timezone.now()
        self.date_expiration = self.date_activation + timedelta(days=duree_jours)
        self.type_abonnement = type_abonnement
        self.statut = 'ACTIF'
        self.save()

    @property
    def licence_valide(self):
        """Vérifie si la licence est valide (non expirée)."""
        if self.statut in ('EXPIRE', 'BLOQUE', 'EN_ATTENTE'):
            return False
        if self.date_expiration and self.date_expiration < timezone.now():
            return False
        if self.essai_gratuit and self.date_fin_essai and self.date_fin_essai < timezone.now():
            return False
        return True

    @property
    def jours_restants(self):
        """Nombre de jours restants avant expiration."""
        if self.date_expiration:
            reste = (self.date_expiration - timezone.now()).days
            return max(0, reste)
        return 0

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
        parts = [self.last_name, self.first_name]
        return ' '.join(p for p in parts if p) or self.username

    @property
    def initiales(self):
        parts = [self.first_name, self.last_name]
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


# ═══════════════════════════════════════════════════════════════
#  CLÉ D'ACTIVATION
# ═══════════════════════════════════════════════════════════════

class CleActivation(models.Model):
    TYPE_PLAN = [
        ('ESSAI',       'Essai gratuit (14 jours)'),
        ('1MOIS',       '1 Mois'),
        ('6MOIS',       '6 Mois'),
        ('12MOIS',      '12 Mois'),
        ('24MOIS',      '24 Mois'),
        ('PERSONNALISE','Personnalisé'),
    ]

    cle_visible    = models.CharField(max_length=50, unique=True, editable=False)
    empreinte_hmac = models.CharField(max_length=64, editable=False, blank=True)

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        related_name='cles_activation',
        verbose_name="Mutualité",
    )

    type_plan  = models.CharField("Type de plan", max_length=20,
                                   choices=TYPE_PLAN, default='STARTER')
    duree_mois = models.PositiveSmallIntegerField(
        "Durée (mois)", default=6,
    )

    STATUT = [
        ('DISPONIBLE', 'Disponible — prête à être remise'),
        ('ACTIVE',     'Active'),
        ('EXPIREE',    'Expirée'),
        ('REVOQUEE',   "Révoquée par l'admin"),
    ]
    statut = models.CharField(
        "Statut", max_length=20, choices=STATUT, default='DISPONIBLE',
    )

    date_debut = models.DateTimeField("Valide à partir du", default=timezone.now)
    date_fin   = models.DateTimeField("Valide jusqu'au", null=True, blank=True)

    active = models.BooleanField("Activée par l'admin", default=True)

    utilisee = models.BooleanField("Utilisée", default=False)
    date_utilisation = models.DateTimeField("Date d'activation", null=True, blank=True)

    cree_par          = models.CharField(max_length=100, default='superadmin')
    date_creation     = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    motif_revocation  = models.TextField(blank=True)
    notes             = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name        = "Clé d'activation"
        verbose_name_plural = "Clés d'activation"
        ordering            = ['-date_creation']

    def __str__(self):
        statut = "✅" if self.utilisee else "🔑"
        return f"{statut} {self.cle_visible} — {self.mutualite.nom} [{self.label_plan}]"

    def generer_cle_unique(self):
        import secrets
        alphabet = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        nom_clean  = ''.join(c for c in self.mutualite.nom.upper() if c.isalpha())
        nom_prefix = (nom_clean + 'MUT')[:3]
        nif_digits = ''.join(c for c in (self.mutualite.nif or '') if c.isdigit())
        nif_suffix = nif_digits[-4:] if len(nif_digits) >= 4 else nif_digits.zfill(4)
        
        periodes = {'ESSAI': '14J', '1MOIS': '1M', '6MOIS': '6M',
                    '12MOIS': '12M', '24MOIS': '24M', 'PERSONNALISE': 'CUST'}
        periode  = periodes.get(self.type_plan, '6M')

        while True:
            alea = ''.join(secrets.choice(alphabet) for _ in range(6))
            code = f"{nom_prefix}-{nif_suffix}-{periode}-{alea}"
            if not CleActivation.objects.filter(cle_visible=code).exists():
                return code

    def save(self, *args, **kwargs):
        from datetime import timedelta
        plan_to_duree = {
            'ESSAI': 14, '1MOIS': 30, '6MOIS': 182,
            '12MOIS': 365, '24MOIS': 730, 'PERSONNALISE': 0,
        }
        duree_jours = plan_to_duree.get(self.type_plan, 182)

        plan_to_mois = {
            'ESSAI': 0, '1MOIS': 1, '6MOIS': 6,
            '12MOIS': 12, '24MOIS': 24, 'PERSONNALISE': 0,
        }
        self.duree_mois = plan_to_mois.get(self.type_plan, 6)

        if self.type_plan == 'PERSONNALISE':
            self.duree_mois = 0

        if not self.date_debut:
            self.date_debut = timezone.now()
        if not self.date_fin:
            if self.type_plan == 'PERSONNALISE':
                self.date_fin = self.date_debut + timedelta(days=365)
            else:
                self.date_fin = self.date_debut + timedelta(days=duree_jours)

        if not self.cle_visible:
            self.cle_visible = self.generer_cle_unique()
            
        self.statut = self._calculer_statut()
        super().save(*args, **kwargs)

    def _calculer_statut(self):
        if not self.active: return 'REVOQUEE'
        if self.date_fin and timezone.localdate() > self.date_fin.date(): return 'EXPIREE'
        if self.utilisee: return 'ACTIVE'
        return 'DISPONIBLE'

    @property
    def label_plan(self):
        labels = {
            'ESSAI':       'Essai 14j', '1MOIS':       '1 Mois',
            '6MOIS':       '6 Mois',    '12MOIS':      '12 Mois',
            '24MOIS':      '24 Mois',   'PERSONNALISE':'Personnalisé',
        }
        return labels.get(self.type_plan, self.type_plan)

    @classmethod
    def creer_essai(cls, mutualite, cree_par='superadmin'):
        from datetime import timedelta
        now = timezone.now()
        cle = cls(
            mutualite        = mutualite,
            type_plan        = 'ESSAI',
            date_debut       = now,
            date_fin         = now + timedelta(days=14),
            active           = True,
            utilisee         = True,
            statut           = 'ACTIVE',
            date_utilisation = now,
            cree_par         = cree_par,
            notes            = "Essai gratuit 14 jours — généré automatiquement",
        )
        cle.save()
        return cle

class AuditCle(models.Model):
    ACTION = [
        ('CREEE',     'Clé créée'),
        ('ACTIVEE',   'Clé activée'),
        ('REVOQUEE',  'Clé révoquée'),
        ('ECHEC',     'Tentative échouée'),
        ('SUSPENDUE', 'Mutualité suspendue'),
        ('REACTIVEE', 'Mutualité réactivée'),
        ('PROLONGEE', 'Clé prolongée'),
    ]

    cle     = models.ForeignKey(CleActivation, on_delete=models.SET_NULL, null=True, blank=True)
    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        related_name='audits',
        null=True, blank=True,
    )
    action      = models.CharField(max_length=20, choices=ACTION)
    message     = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_action']

    def __str__(self):
        nom = self.mutualite.nom if self.mutualite else 'N/A'
        return f"{nom} | {self.action} | {self.date_action:%d/%m/%Y %H:%M}"
