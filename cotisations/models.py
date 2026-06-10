# cotisations/models.py
from django.db import models
from django.utils import timezone
from affilies.models import Affilie
from core.models import Utilisateur, TenantManager

class Cotisation(models.Model):
    PERIODE_CHOICES = [
        ('MENSUEL', 'Mensuel'),
        ('TRIMESTRIEL', 'Trimestriel'),
        ('ANNUEL', 'Annuel'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('PAYE', 'Payé'),
        ('PARTIEL', 'Paiement partiel'),
        ('RETARD', 'En retard'),
    ]
    MODE_PAIEMENT_CHOICES = [
        ('CASH', 'Espèces'),
        ('MOBILE', 'Mobile Money'),
        ('BANQUE', 'Banque'),
        ('COOPERATIVE', 'Coopérative'),
        ('CHEQUE', 'Chèque'),
    ]
    
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    affilie = models.ForeignKey(Affilie, on_delete=models.CASCADE, related_name='cotisations')
    
    reference = models.CharField(max_length=50, unique=True, verbose_name='Référence paiement')
    montant = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Montant (BIF)')
    
    periode_type = models.CharField(max_length=20, choices=PERIODE_CHOICES, default='MENSUEL')
    mois = models.PositiveIntegerField(null=True, blank=True, verbose_name='Mois concerné (1-12)')
    annee = models.PositiveIntegerField(default=timezone.now().year, db_index=True, verbose_name='Année')
    
    date_emission = models.DateField(default=timezone.now, verbose_name='Date d\'émission')
    date_echeance = models.DateField(null=True, blank=True, verbose_name='Date d\'échéance')
    date_paiement = models.DateField(null=True, blank=True, verbose_name='Date de paiement')
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE', db_index=True)
    mode_paiement = models.CharField(max_length=20, choices=MODE_PAIEMENT_CHOICES, blank=True)
    
    recu_fichier = models.FileField(upload_to='recus_cotisation/', blank=True, null=True, verbose_name='Preuve de paiement')
    notes = models.TextField(blank=True)
    
    enregistre_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='cotisations_enregistrees')
    date_creation = models.DateTimeField(auto_now_add=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Cotisation'
        verbose_name_plural = 'Cotisations'
        ordering = ['-annee', '-mois', '-date_emission']
        
    def __str__(self):
        return f"{self.reference} - {self.affilie.nom_complet}"
        
    @classmethod
    def generer_reference(cls):
        date_str = timezone.now().strftime('%Y%m')
        count = cls.objects.filter(date_creation__year=timezone.now().year, date_creation__month=timezone.now().month).count() + 1
        return f"COT-{date_str}-{count:04d}"
