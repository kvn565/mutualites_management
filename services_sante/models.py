# services_sante/models.py
from django.db import models
from core.models import TenantManager
from comptabilite.models import SoftDeleteMixin

class ServiceSante(SoftDeleteMixin):
    CATEGORIE_CHOICES = [
        ('CONSULTATION','Consultation'),
        ('HOSPITALISATION','Hospitalisation'),
        ('CHIRURGIE','Chirurgie'),
        ('MATERNITE','Maternité'),
        ('LABORATOIRE','Laboratoire'),
        ('IMAGERIE','Imagerie médicale'),
        ('DENTAIRE','Soins dentaires'),
        ('OPHTALMOLOGIE','Ophtalmologie'),
        ('PHARMACIE','Pharmacie'),
        ('AUTRE','Autre'),
    ]
    
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    code = models.CharField(max_length=20, unique=True, verbose_name='Code service')
    nom = models.CharField(max_length=200, db_index=True, verbose_name='Nom du service')
    categorie = models.CharField(max_length=20, db_index=True, choices=CATEGORIE_CHOICES)
    description = models.TextField(blank=True)
    taux_prise_en_charge = models.DecimalField(
        max_digits=5, decimal_places=2, default=80,
        verbose_name='Taux prise en charge (%)'
    )
    plafond = models.DecimalField(
        max_digits=15, decimal_places=2, default=0,
        verbose_name='Plafond (BIF)'
    )
    conditions = models.TextField(blank=True, verbose_name='Conditions')
    actif = models.BooleanField(default=True, db_index=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Service de santé'
        verbose_name_plural = 'Services de santé'
        ordering = ['categorie','nom']
    
    def __str__(self):
        return f"{self.code} — {self.nom}"
    
    @classmethod
    def generer_code(cls, categorie):
        prefix = categorie[:3].upper()
        count = cls.objects.filter(categorie=categorie).count() + 1
        return f"{prefix}-{count:03d}"

    def _serialiser_pour_corbeille(self):
        return {
            'code': self.code,
            'nom': self.nom,
            'categorie': self.categorie,
            'description': self.description,
            'taux_prise_en_charge': str(self.taux_prise_en_charge),
            'plafond': str(self.plafond),
            'actif': self.actif,
        }
