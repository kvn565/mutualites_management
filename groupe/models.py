from django.db import models
from core.models import Utilisateur, Mutualite, TenantManager


class Groupe(models.Model):
    nom = models.CharField(max_length=100, verbose_name='Nom du groupe')
    description = models.TextField(blank=True, verbose_name='Description')
    membres = models.ManyToManyField(
        Utilisateur, blank=True, related_name='groupes',
        verbose_name='Membres',
    )
    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        related_name='groupes', verbose_name='Mutualité',
    )
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='groupes_crees',
        verbose_name='Créé par',
    )
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    date_modification = models.DateTimeField(auto_now=True, verbose_name='Dernière modification')

    objects = TenantManager()

    class Meta:
        verbose_name = 'Groupe'
        verbose_name_plural = 'Groupes'
        ordering = ['nom']

    def __str__(self):
        return self.nom
