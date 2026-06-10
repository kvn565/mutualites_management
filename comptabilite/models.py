# comptabilite/models.py
from django.db import models
from django.utils import timezone
from core.models import Utilisateur, TenantManager

class Compte(models.Model):
    objects = TenantManager()

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    TYPE_CHOICES = [
        ('ACTIF', 'Actif (Trésorerie/Banque)'),
        ('PASSIF', 'Passif (Dettes)'),
        ('PRODUIT', 'Produit (Revenus/Cotisations)'),
        ('CHARGE', 'Charge (Dépenses/Factures)'),
    ]
    
    numero = models.CharField(max_length=20, unique=True)
    intitule = models.CharField(max_length=200)
    type_compte = models.CharField(max_length=20, choices=TYPE_CHOICES)
    solde_initial = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    
    objects = TenantManager()

    class Meta:
        ordering = ['numero']
        
    def __str__(self):
        return f"{self.numero} - {self.intitule}"
        
    @property
    def solde_actuel(self):
        total_debit = self.ecritures.filter(type_mouvement='DEBIT').aggregate(models.Sum('montant'))['montant__sum'] or 0
        total_credit = self.ecritures.filter(type_mouvement='CREDIT').aggregate(models.Sum('montant'))['montant__sum'] or 0
        
        if self.type_compte in ['ACTIF', 'CHARGE']:
            return self.solde_initial + total_debit - total_credit
        else:
            return self.solde_initial + total_credit - total_debit

class Transaction(models.Model):
    objects = TenantManager()

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    reference = models.CharField(max_length=50, unique=True)
    date = models.DateField(default=timezone.now, db_index=True)
    libelle = models.CharField(max_length=255)
    piece_justificative = models.FileField(upload_to='compta/', blank=True, null=True)
    
    enregistre_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-id']
        
    def __str__(self):
        return f"{self.reference} - {self.date}"

class Ecriture(models.Model):
    objects = TenantManager()

    TYPE_MOUVEMENT = [
        ('DEBIT', 'Débit'),
        ('CREDIT', 'Crédit'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )
    
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='ecritures')
    compte = models.ForeignKey(Compte, on_delete=models.RESTRICT, related_name='ecritures')
    type_mouvement = models.CharField(max_length=10, choices=TYPE_MOUVEMENT)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    libelle_ligne = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['id']
        
    def __str__(self):
        return f"{self.compte.numero} - {self.type_mouvement} {self.montant}"
