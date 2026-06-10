# affilies/models.py
from django.db import models
from django.utils import timezone
from core.models import Utilisateur, TenantManager

class Affilie(models.Model):
    SEXE_CHOICES = [('M','Masculin'),('F','Féminin')]
    ETAT_CIVIL_CHOICES = [
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE', 'Marié(e)'),
        ('DIVORCE', 'Divorcé(e)'),
        ('VEUF', 'Veuf/Veuve'),
    ]
    TYPE_ADHESION_CHOICES = [
        ('INDIVIDUELLE', 'Individuelle'),
        ('FAMILIALE', 'Familiale'),
        ('GROUPE', 'Groupe/Association'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACTIF', 'Actif'),
        ('SUSPENDU', 'Suspendu'),
        ('EXPIRE', 'Expiré'),
        ('RADIE', 'Radié'),
    ]
    GROUPE_SANGUIN_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('NSP', 'Non connu'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )
    
    numero_affiliation = models.CharField(max_length=20, unique=True, verbose_name='N° de membre')
    nom = models.CharField(max_length=100, db_index=True, verbose_name='Nom')
    postnom = models.CharField(max_length=100, blank=True, db_index=True, verbose_name='Postnom')
    prenom = models.CharField(max_length=100, db_index=True, verbose_name='Prénom')
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name='Sexe')
    date_naissance = models.DateField(verbose_name='Date de naissance')
    etat_civil = models.CharField(
        max_length=20, choices=ETAT_CIVIL_CHOICES, default='CELIBATAIRE',
        verbose_name='État civil',
    )
    numero_carte_identite = models.CharField(
        max_length=30, blank=True, verbose_name='N° Carte nationale d\'identité (CIN/NIF)',
    )

    province = models.CharField(max_length=100, blank=True, verbose_name='Province')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
    zone = models.CharField(max_length=100, blank=True, verbose_name='Zone')
    colline = models.CharField(max_length=100, blank=True, verbose_name='Colline/Quartier')
    adresse = models.TextField(blank=True, verbose_name='Adresse complément')
    telephone = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    profession = models.CharField(max_length=100, blank=True, verbose_name='Profession')

    photo = models.ImageField(upload_to='affilies/portraits/', blank=True, null=True, verbose_name='Photo du membre')

    groupe_sanguin = models.CharField(
        max_length=3, choices=GROUPE_SANGUIN_CHOICES, blank=True,
        verbose_name='Groupe sanguin',
    )
    contact_urgence_nom = models.CharField(
        max_length=200, blank=True, verbose_name='Personne à contacter (urgence)',
    )
    contact_urgence_telephone = models.CharField(
        max_length=20, blank=True, verbose_name='Téléphone (urgence)',
    )
    centre_sante_reference = models.CharField(
        max_length=200, blank=True, verbose_name='Centre de santé de référence',
    )
    hopital_reference = models.CharField(
        max_length=200, blank=True, verbose_name='Hôpital de référence',
    )

    date_adhesion = models.DateField(default=timezone.now, verbose_name="Date d'inscription")
    type_adhesion = models.CharField(
        max_length=20, choices=TYPE_ADHESION_CHOICES, default='INDIVIDUELLE',
        verbose_name="Type d'adhésion",
    )
    section_antenne = models.CharField(
        max_length=100, blank=True, verbose_name='Section/Antenne locale',
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF', db_index=True)
    notes = models.TextField(blank=True, verbose_name='Notes')
    
    origine = models.ForeignKey(
        'origines.Origine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='affilies',
        verbose_name='Origine',
    )
    
    # Soft delete
    actif = models.BooleanField(default=True, db_index=True)
    supprime = models.BooleanField(default=False, db_index=True, verbose_name='Supprimé')
    date_suppression = models.DateTimeField(null=True, blank=True)
    
    # Audit
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='affilies_crees',
        verbose_name="Agent d'enregistrement",
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Affilié'
        verbose_name_plural = 'Affiliés'
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.numero_affiliation} — {self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.postnom} {self.prenom}".strip()
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        b = self.date_naissance
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    
    @property
    def nombre_beneficiaires(self):
        return self.ayants_droit.filter(actif=True).count()
    
    def soft_delete(self):
        self.supprime = True
        self.actif = False
        self.date_suppression = timezone.now()
        self.save(update_fields=['supprime','actif','date_suppression'])
    
    @classmethod
    def generer_numero(cls):
        """Génère le prochain numéro d'affiliation automatiquement."""
        annee = timezone.now().year
        count = cls.objects.filter(
            date_creation__year=annee
        ).count() + 1
        return f"AFF-{annee}-{count:04d}"
