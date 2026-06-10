# origines/models.py
from django.db import models
from core.models import TenantManager

class Origine(models.Model):
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
