# pharmacie/models.py
from django.db import models
from core.models import TenantManager
from comptabilite.models import SoftDeleteMixin

class CategorieMedicament(models.Model):
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    nom = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Catégorie de médicament'
        verbose_name_plural = 'Catégories de médicaments'
        ordering = ['nom']
        
    def __str__(self):
        return self.nom

class Medicament(SoftDeleteMixin):
    FORME_CHOICES = [
        ('COMPRIME', 'Comprimé'),
        ('SIROP', 'Sirop'),
        ('INJECTION', 'Injection'),
        ('GELULE', 'Gélule'),
        ('POMMADE', 'Pommade / Crème'),
        ('GOUTTES', 'Gouttes'),
        ('SUPPOSITOIRE', 'Suppositoire'),
        ('AUTRE', 'Autre'),
    ]
    
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    code = models.CharField(max_length=50, unique=True, verbose_name='Code (AMM/Interne)')
    nom = models.CharField(max_length=200, db_index=True, verbose_name='Nom commercial')
    dci = models.CharField(max_length=200, blank=True, db_index=True, verbose_name='DCI (Principe actif)')
    categorie = models.ForeignKey(CategorieMedicament, on_delete=models.SET_NULL, null=True, blank=True)
    forme = models.CharField(max_length=30, choices=FORME_CHOICES, default='COMPRIME')
    dosage = models.CharField(max_length=100, blank=True)
    
    pris_en_charge = models.BooleanField(default=True, verbose_name='Pris en charge par la mutuelle')
    taux_remboursement = models.DecimalField(max_digits=5, decimal_places=2, default=80, verbose_name='Taux remboursement (%)')
    prix_reference = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Prix de référence (BIF)')
    
    observations = models.TextField(blank=True)
    actif = models.BooleanField(default=True, db_index=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Médicament'
        verbose_name_plural = 'Médicaments'
        ordering = ['nom']
        
    def __str__(self):
        return f"{self.nom} {self.dosage} ({self.forme})"

    @classmethod
    def generer_code(cls):
        prefix = "MED"
        count = cls.objects.count() + 1
        return f"{prefix}-{count:04d}"

    def _serialiser_pour_corbeille(self):
        return {
            'code': self.code,
            'nom': self.nom,
            'dci': self.dci,
            'categorie': self.categorie.nom if self.categorie else None,
            'forme': self.forme,
            'dosage': self.dosage,
            'pris_en_charge': self.pris_en_charge,
            'taux_remboursement': str(self.taux_remboursement),
            'prix_reference': str(self.prix_reference),
            'observations': self.observations,
            'actif': self.actif,
        }
