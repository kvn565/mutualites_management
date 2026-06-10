# factures/models.py
from django.db import models
from django.utils import timezone
from core.models import Utilisateur, TenantManager
from affilies.models import Affilie
from ayants_droit.models import AyantDroit
from partenaires.models import Partenaire
from services_sante.models import ServiceSante

class Facture(models.Model):
    STATUT_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('SOUMIS', 'Soumise (en attente)'),
        ('VALIDE', 'Validée'),
        ('PAYE', 'Payée'),
        ('REJETE', 'Rejetée'),
    ]
    
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    numero = models.CharField(max_length=50, unique=True, verbose_name='N° Facture')
    numero_dossier_soins = models.CharField(
        max_length=50, blank=True, verbose_name='N° dossier de soins',
    )
    date = models.DateField(default=timezone.now, db_index=True, verbose_name='Date de consultation')
    
    partenaire = models.ForeignKey(
        Partenaire, on_delete=models.RESTRICT, related_name='factures',
        verbose_name='Structure sanitaire',
    )
    
    affilie = models.ForeignKey(Affilie, on_delete=models.RESTRICT, related_name='factures')
    ayant_droit = models.ForeignKey(AyantDroit, on_delete=models.SET_NULL, null=True, blank=True, related_name='factures')
    
    diagnostic = models.TextField(blank=True, verbose_name='Diagnostic')
    
    montant_total = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Montant total')
    montant_ticket_moderateur = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Ticket modérateur (Patient)')
    montant_mutualite = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='Part Mutualité')
    
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='BROUILLON', db_index=True)
    motif_rejet = models.TextField(blank=True)
    
    fichier_joint = models.FileField(upload_to='factures_scans/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, related_name='factures_crees')
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Facture'
        verbose_name_plural = 'Factures'
        ordering = ['-date', '-id']
        
    def __str__(self):
        return f"Facture {self.numero} - {self.partenaire.nom_etablissement}"
        
    @classmethod
    def generer_numero(cls):
        date_str = timezone.now().strftime('%Y%m')
        count = cls.objects.filter(date__year=timezone.now().year, date__month=timezone.now().month).count() + 1
        return f"FAC-{date_str}-{count:04d}"

class LigneFacture(models.Model):
    objects = TenantManager()

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    facture = models.ForeignKey(Facture, on_delete=models.CASCADE, related_name='lignes')
    service = models.ForeignKey(ServiceSante, on_delete=models.RESTRICT)
    designation = models.CharField(max_length=200, blank=True, help_text="Spécifiez l'acte ou médicament exact")
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    
    taux_applique = models.DecimalField(max_digits=5, decimal_places=2, help_text="Taux de prise en charge appliqué (%)")
    
    class Meta:
        verbose_name = 'Ligne de facture'
        verbose_name_plural = 'Lignes de facture'
        
    @property
    def total_ligne(self):
        return self.quantite * self.prix_unitaire
        
    @property
    def part_mutualite(self):
        return (self.total_ligne * self.taux_applique) / 100
        
    @property
    def part_patient(self):
        return self.total_ligne - self.part_mutualite
