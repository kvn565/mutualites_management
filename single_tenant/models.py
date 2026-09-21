from django.db import models


class SingleTenantConfig(models.Model):
    """Configuration du mode single-tenant : une seule mutualité active."""
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
    STATUT_CHOICES = [
        (ACTIVE, 'Active'),
        (INACTIVE, 'Inactive'),
    ]

    mutualite = models.OneToOneField(
        'core.Mutualite',
        on_delete=models.CASCADE,
        unique=True,
        verbose_name='Mutualité unique',
        help_text='La mutualité unique gérée par cette instance',
    )
    nom_instance = models.CharField(
        max_length=200,
        default='Mutualité de Santé',
        verbose_name='Nom de l\'instance',
    )
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default=INACTIVE,
        verbose_name='Statut',
    )
    date_activation = models.DateTimeField(
        null=True, blank=True, verbose_name='Date d\'activation',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuration Single-Tenant'
        verbose_name_plural = 'Configuration Single-Tenant'

    def __str__(self):
        return f"{self.nom_instance} — {self.mutualite.nom}"

    @property
    def est_active(self):
        return self.statut == self.ACTIVE

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.statut == self.ACTIVE:
            SingleTenantConfig.objects.exclude(pk=self.pk).update(statut=self.INACTIVE)
            from core.models import Mutualite
            Mutualite.objects.exclude(pk=self.mutualite_id).filter(statut__in=['ACTIF', 'ESSAI']).update(statut='SUSPENDU')
