# ayants_droit/models.py
from django.db import models
from django.utils import timezone
from affilies.models import Affilie
from core.models import TenantManager


class AyantDroit(models.Model):
    LIEN_CHOICES = [
        ('CONJOINT', 'Conjoint(e)'),
        ('ENFANT', 'Enfant'),
        ('ENFANT_ADOPTE', 'Enfant adopté'),
        ('PARENT', 'Parent à charge'),
        ('FRERE_SOEUR', 'Frère/Sœur'),
        ('AUTRE', 'Autre'),
    ]
    SEXE_CHOICES = [('M', 'Masculin'), ('F', 'Féminin')]
    STATUT_CHOICES = [
        ('ACTIF', 'Actif'),
        ('SUSPENDU', 'Suspendu'),
        ('RADIE', 'Radié'),
        ('DECEDE', 'Décédé'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )

    affilie = models.ForeignKey(
        Affilie,
        on_delete=models.CASCADE,
        related_name='ayants_droit',
        verbose_name='Chef de ménage',
    )
    nom = models.CharField(max_length=100, db_index=True, verbose_name='Nom')
    postnom = models.CharField(max_length=100, blank=True, verbose_name='Postnom')
    prenom = models.CharField(max_length=100, blank=True, verbose_name='Prénom')
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name='Sexe')
    date_naissance = models.DateField(verbose_name='Date de naissance')
    numero_identite = models.CharField(
        max_length=30, blank=True, verbose_name="Numéro d'identité",
    )
    lien_parente = models.CharField(
        max_length=20,
        choices=LIEN_CHOICES,
        verbose_name='Lien de parenté',
    )
    date_ajout = models.DateField(
        default=timezone.now, verbose_name="Date d'ajout",
    )
    statut = models.CharField(
        max_length=20,
        choices=STATUT_CHOICES,
        default='ACTIF',
        db_index=True,
        verbose_name='Statut',
    )
    telephone = models.CharField(max_length=20, blank=True, verbose_name='Téléphone')
    notes = models.TextField(blank=True, verbose_name='Notes')

    # Soft delete
    actif = models.BooleanField(default=True, db_index=True)
    supprime = models.BooleanField(default=False, db_index=True)
    date_suppression = models.DateTimeField(null=True, blank=True)

    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Ayant droit'
        verbose_name_plural = 'Ayants droit'
        ordering = ['affilie', 'lien_parente', 'nom']

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.get_lien_parente_display()}) — {self.affilie}"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.postnom} {self.prenom}".strip()

    @property
    def age(self):
        from datetime import date
        today = date.today()
        b = self.date_naissance
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))

    def soft_delete(self):
        self.supprime = True
        self.actif = False
        self.date_suppression = timezone.now()
        self.save(update_fields=['supprime', 'actif', 'date_suppression'])
