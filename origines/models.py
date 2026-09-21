# origines/models.py
from django.db import models
from core.models import TenantManager
from comptabilite.models import SoftDeleteMixin


class CategorieOrigine(models.Model):
    """Catégories d'affiliés au sein d'une origine (ex: Cadre, Employé, Agent, etc.)"""
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='categories_origine',
        verbose_name='Mutualité',
    )
    origine = models.ForeignKey(
        'Origine', on_delete=models.CASCADE,
        related_name='categories', verbose_name='Origine',
    )
    nom = models.CharField(max_length=100, verbose_name='Nom de la catégorie')
    description = models.TextField(blank=True, verbose_name='Description')
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')
    actif = models.BooleanField(default=True, verbose_name='Actif')

    objects = TenantManager()

    # Cotisation et plafonds spécifiques à cette catégorie
    cotisation_mensuelle = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Cotisation mensuelle (BIF)')
    taux_prise_en_charge = models.DecimalField(max_digits=5, decimal_places=2, default=80, verbose_name='Taux prise en charge mutualité (%)')
    soins_ambulatoires = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Soins Ambulatoires (BIF)')
    limite_laboratoire = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Laboratoire (BIF)')
    limite_kinesitherapie = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Kinésithérapie (BIF)')
    limite_reanimation = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Réanimation (BIF)')
    limite_imagerie_medicale = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Imagerie Médicale (BIF)')
    hopital_plafond_chambre = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Hôpital plafond chambre/nuit (BIF)')
    hpc_nuit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='HPC / Nuit (BIF)')
    limite_hospitalisation_generale = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Hospitalisation Générale (BIF)')
    maternite_forfait = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Maternité forfait (BIF)')
    pourcentage_maternite = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Pourcentage Maternité (%)')
    pharmacie_forfait = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Pharmacie forfait (BIF)')
    limites_medicaments = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limites Médicaments (BIF)')
    limites_lunettes = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limites Lunettes (BIF)')
    limites_dents = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limites Soins Dentaires (BIF)')

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Catégorie d\'origine'
        verbose_name_plural = 'Catégories d\'origine'
        ordering = ['origine', 'ordre', 'nom']
        unique_together = ['origine', 'nom']

    def __str__(self):
        return f"{self.origine.nom} — {self.nom}"

    def save(self, *args, **kwargs):
        if self.origine_id and not self.mutualite_id:
            self.mutualite = self.origine.mutualite
        super().save(*args, **kwargs)


class Origine(SoftDeleteMixin):
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    TYPE_CHOICES = [
        ('ENTREPRISE','Entreprise'),
        ('COOPERATIVE','Coopérative'),
        ('ASSOCIATION','Association'),
        ('INDIVIDUEL','Individuel'),
        ('ONG','ONG'),
        ('INSTITUTION','Institution publique'),
    ]
    nom = models.CharField(max_length=200, db_index=True, verbose_name='Nom')
    type_origine = models.CharField(max_length=20, choices=TYPE_CHOICES, db_index=True, verbose_name='Type')
    description = models.TextField(blank=True)
    contact = models.CharField(max_length=100, blank=True, verbose_name='Contact principal')
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.TextField(blank=True)
    actif = models.BooleanField(default=True, db_index=True)
    # Plafonds par défaut pour les affiliés de cette origine
    cotisation_mensuelle = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Cotisation mensuelle (BIF)')
    soins_ambulatoires = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Soins Ambulatoires (BIF)')
    limite_laboratoire = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Laboratoire (BIF)')
    limite_kinesitherapie = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Kinésithérapie (BIF)')
    limite_reanimation = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Réanimation (BIF)')
    limite_imagerie_medicale = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Imagerie Médicale (BIF)')
    hopital_plafond_chambre = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Hôpital plafond chambre/nuit (BIF)')
    hpc_nuit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='HPC / Nuit (BIF)')
    limite_hospitalisation_generale = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limite Hospitalisation Générale (BIF)')
    maternite_forfait = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Maternité forfait (BIF)')
    pourcentage_maternite = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='Pourcentage Maternité (%)')
    pharmacie_forfait = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Pharmacie forfait (BIF)')
    limites_medicaments = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limites Médicaments (BIF)')
    limites_lunettes = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limites Lunettes (verre et monture) (BIF)')
    limites_dents = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Limites Soins Dentaires (BIF)')

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Origine'
        verbose_name_plural = 'Origines'
        ordering = ['nom']
    
    def __str__(self):
        return f"{self.nom} ({self.get_type_origine_display()})"
    
    @property
    def nb_affilies(self):
        try:
            return self.affilies.filter(actif=True).count()
        except:
            return 0

    def _serialiser_pour_corbeille(self):
        return {
            'nom': self.nom,
            'type_origine': self.type_origine,
            'description': self.description,
            'contact': self.contact,
            'telephone': self.telephone,
            'email': self.email,
            'adresse': self.adresse,
            'actif': self.actif,
            'cotisation_mensuelle': str(self.cotisation_mensuelle),
        }


class OrigineExclusion(models.Model):
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )
    origine = models.ForeignKey(
        Origine, on_delete=models.CASCADE,
        related_name='exclusions', verbose_name='Origine',
    )
    medicament = models.ForeignKey(
        'pharmacie.Medicament', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Médicament',
    )
    service = models.ForeignKey(
        'services_sante.ServiceSante', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Service',
    )
    motif = models.TextField(blank=True, verbose_name="Motif d'exclusion")
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    cree_par = models.ForeignKey(
        'core.Utilisateur', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Créé par',
    )

    objects = TenantManager()

    class Meta:
        verbose_name = "Exclusion d'origine"
        verbose_name_plural = "Exclusions d'origine"
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(medicament__isnull=False, service__isnull=True) |
                    models.Q(medicament__isnull=True, service__isnull=False)
                ),
                name='origine_exclusion_un_seul_type',
                violation_error_message='Une exclusion doit concerner soit un médicament, soit un service.',
            ),
        ]

    def __str__(self):
        if self.medicament:
            return f"Origine {self.origine.nom} → Médicament: {self.medicament.nom}"
        if self.service:
            return f"Origine {self.origine.nom} → Service: {self.service.nom}"
        return f"Exclusion origine #{self.pk}"
