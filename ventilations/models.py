from django.db import models
from django.utils import timezone
from decimal import Decimal
from core.models import Utilisateur, TenantManager


class Branche(models.Model):
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='branches',
        verbose_name='Mutualité',
    )
    code = models.CharField(max_length=20, verbose_name='Code branche')
    libelle = models.CharField(max_length=200, verbose_name='Libellé')
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    objects = TenantManager()

    class Meta:
        ordering = ['code']
        unique_together = [('mutualite', 'code')]
        verbose_name = 'Branche'
        verbose_name_plural = 'Branches'

    def __str__(self):
        return f"{self.code} — {self.libelle}"


class RegleVentilation(models.Model):
    TYPE_ORIGINE = [
        ('COTISATION', 'Cotisation'),
        ('PRESTATION', 'Prestation/Sinistre'),
        ('FACTURE', 'Facture partenaire'),
        ('CHARGE', 'Charge générale'),
        ('PRODUIT', 'Produit divers'),
        ('TOUT', 'Toute écriture'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='regles_ventilation',
    )
    libelle = models.CharField(max_length=200, verbose_name='Libellé de la règle')
    type_origine = models.CharField(
        max_length=20, choices=TYPE_ORIGINE, default='TOUT',
        verbose_name="Type d'écriture concerné",
    )
    centre = models.ForeignKey(
        'comptabilite.CentreAnalytique', on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Centre analytique',
    )
    branche = models.ForeignKey(
        Branche, on_delete=models.SET_NULL, null=True, blank=True,
        verbose_name='Branche',
    )
    pourcentage = models.DecimalField(
        max_digits=6, decimal_places=2,
        verbose_name='Pourcentage (%)',
        help_text='Part de la ventilation (ex: 50 pour 50%)',
    )
    appliquer_solde_restant = models.BooleanField(
        default=False,
        verbose_name='Appliquer au solde restant',
        help_text='Si coché, prend le pourcentage du reste après autres règles',
    )
    priorite = models.PositiveIntegerField(default=0, verbose_name='Priorité (ordre)')
    actif = models.BooleanField(default=True)
    date_debut = models.DateField(null=True, blank=True, verbose_name='Début validité')
    date_fin = models.DateField(null=True, blank=True, verbose_name='Fin validité')
    notes = models.TextField(blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        ordering = ['type_origine', 'priorite', 'libelle']
        verbose_name = 'Règle de ventilation'
        verbose_name_plural = 'Règles de ventilation'

    def __str__(self):
        base = f"{self.libelle} ({self.pourcentage}%)"
        if self.centre:
            base += f" — {self.centre}"
        if self.branche:
            base += f" — {self.branche}"
        return base

    def est_applicable(self, origine, date_ecriture=None):
        """Vérifie si cette règle s'applique à une écriture donnée."""
        if not self.actif:
            return False
        if self.type_origine != 'TOUT' and self.type_origine != origine:
            return False
        if date_ecriture:
            if self.date_debut and date_ecriture < self.date_debut:
                return False
            if self.date_fin and date_ecriture > self.date_fin:
                return False
        return True


class Ventilation(models.Model):
    STATUT = [
        ('PROVISOIRE', 'Provisoire'),
        ('VALIDEE', 'Validée'),
        ('ANNULEE', 'Annulée'),
    ]
    TYPE_VENTILATION = [
        ('AUTO', 'Automatique — règle'),
        ('MANUEL', 'Manuelle'),
        ('REPARTITION', 'Répartition globale'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='ventilations',
    )
    ecriture = models.ForeignKey(
        'comptabilite.Ecriture', on_delete=models.CASCADE,
        related_name='ventilations', verbose_name='Écriture comptable',
    )
    centre = models.ForeignKey(
        'comptabilite.CentreAnalytique', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ventilations',
        verbose_name='Centre analytique',
    )
    branche = models.ForeignKey(
        Branche, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ventilations',
        verbose_name='Branche',
    )
    pourcentage = models.DecimalField(
        max_digits=7, decimal_places=2,
        verbose_name='Pourcentage (%)',
    )
    montant = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Montant ventilé (BIF)',
    )
    type_ventilation = models.CharField(
        max_length=20, choices=TYPE_VENTILATION, default='MANUEL',
    )
    statut = models.CharField(
        max_length=20, choices=STATUT, default='PROVISOIRE',
    )
    regle = models.ForeignKey(
        RegleVentilation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='ventilations',
        verbose_name='Règle appliquée',
    )
    commentaire = models.TextField(blank=True)

    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='ventilations_effectuees',
    )
    date_ventilation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-date_ventilation']
        verbose_name = 'Ventilation'
        verbose_name_plural = 'Ventilations'

    def __str__(self):
        return f"Ventilation {self.ecriture.piece_reference} — {self.centre or '?'} / {self.branche or '?'}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.pourcentage <= 0 or self.pourcentage > 100:
            raise ValidationError({'pourcentage': 'Le pourcentage doit être entre 0 et 100.'})
        if self.montant <= 0:
            raise ValidationError({'montant': 'Le montant doit être positif.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_pourcentage_ecriture(self):
        """Retourne la somme des pourcentages ventilés pour la même écriture."""
        from django.db.models import Sum
        total = Ventilation.objects.filter(
            ecriture=self.ecriture,
            statut__in=['PROVISOIRE', 'VALIDEE'],
        ).exclude(pk=self.pk).aggregate(
            total=Sum('pourcentage')
        )['total'] or Decimal('0.00')
        return total + self.pourcentage


class VentilationHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATION', 'Création'),
        ('MODIFICATION', 'Modification'),
        ('VALIDATION', 'Validation'),
        ('ANNULATION', 'Annulation'),
        ('REVENTILATION', 'Ré-ventilation'),
    ]

    ventilation = models.ForeignKey(
        Ventilation, on_delete=models.CASCADE, related_name='historique',
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    ancien_pourcentage = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
    )
    nouveau_pourcentage = models.DecimalField(
        max_digits=7, decimal_places=2, null=True, blank=True,
    )
    ancien_montant = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    nouveau_montant = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
    )
    ancien_centre = models.ForeignKey(
        'comptabilite.CentreAnalytique', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )
    nouveau_centre = models.ForeignKey(
        'comptabilite.CentreAnalytique', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='+',
    )
    ancienne_branche = models.ForeignKey(
        Branche, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    nouvelle_branche = models.ForeignKey(
        Branche, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
    )
    commentaire = models.TextField(blank=True)
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
    )
    date_action = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_action']
        verbose_name = 'Historique de ventilation'
        verbose_name_plural = 'Historiques de ventilation'

    def __str__(self):
        return f"{self.get_action_display()} — {self.ventilation} ({self.date_action:%d/%m/%Y %H:%M})"


class VentilationGlobale(models.Model):
    """Ventilation globale sur une période — répartit un montant global."""
    STATUT = [
        ('BROUILLON', 'Brouillon'),
        ('VALIDEE', 'Validée'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='ventilations_globales',
    )
    libelle = models.CharField(max_length=255, verbose_name='Libellé')
    date_debut = models.DateField(verbose_name='Période début')
    date_fin = models.DateField(verbose_name='Période fin')
    montant_total = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Montant total à ventiler',
    )
    statut = models.CharField(max_length=20, choices=STATUT, default='BROUILLON')
    notes = models.TextField(blank=True)

    valide_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='ventilations_globales_validees',
    )
    enregistre_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True,
        related_name='ventilations_globales_creations',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation = models.DateTimeField(null=True, blank=True)

    objects = TenantManager()

    class Meta:
        ordering = ['-date_fin']
        verbose_name = 'Ventilation globale'
        verbose_name_plural = 'Ventilations globales'

    def __str__(self):
        return f"{self.libelle} ({self.date_debut} → {self.date_fin})"

    @property
    def total_ventile(self):
        from django.db.models import Sum
        return self.lignes.aggregate(total=Sum('montant'))['total'] or Decimal('0.00')

    @property
    def solde_a_ventiler(self):
        return self.montant_total - self.total_ventile


class LigneVentilationGlobale(models.Model):
    ventilation_globale = models.ForeignKey(
        VentilationGlobale, on_delete=models.CASCADE, related_name='lignes',
    )
    centre = models.ForeignKey(
        'comptabilite.CentreAnalytique', on_delete=models.SET_NULL,
        null=True, blank=True,
    )
    branche = models.ForeignKey(
        Branche, on_delete=models.SET_NULL, null=True, blank=True,
    )
    pourcentage = models.DecimalField(max_digits=7, decimal_places=2, verbose_name='%')
    montant = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Montant')
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Ligne de ventilation globale'
        verbose_name_plural = 'Lignes de ventilation globale'

    def __str__(self):
        centre = self.centre or 'Général'
        branche = self.branche or 'Toutes'
        return f"{centre} / {branche} — {self.montant} BIF ({self.pourcentage}%)"
