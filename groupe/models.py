from django.db import models
from core.models import Utilisateur, Mutualite, TenantManager
from comptabilite.models import SoftDeleteMixin


class Menu(models.Model):
    CATEGORIE_CHOICES = [
        ('PRINCIPAL', 'Principal'),
        ('MEMBRES', 'Membres'),
        ('SANTE', 'Santé'),
        ('FACTURATION', 'Facturation'),
        ('COTISATIONS', 'Cotisations'),
        ('FINANCE', 'Finance & Comptabilité'),
        ('ADMIN', 'Administration'),
        ('OUTILS', 'Outils'),
        ('SUPERADMIN', 'Super Admin'),
    ]

    nom = models.CharField(max_length=100, verbose_name='Nom affiché')
    url_name = models.CharField(max_length=200, verbose_name='URL name', unique=True)
    icone = models.CharField(max_length=50, blank=True, verbose_name='Icône Bootstrap')
    categorie = models.CharField(max_length=20, choices=CATEGORIE_CHOICES, verbose_name='Catégorie')
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name="Ordre d'affichage")
    actif = models.BooleanField(default=True, verbose_name='Actif')

    class Meta:
        ordering = ['categorie', 'ordre']
        verbose_name = 'Menu'
        verbose_name_plural = 'Menus'

    def __str__(self):
        return f"{self.nom}"


class Groupe(SoftDeleteMixin):
    nom = models.CharField(max_length=100, verbose_name='Nom du groupe')
    description = models.TextField(blank=True, verbose_name='Description')
    module_chambres_actif = models.BooleanField(
        default=False, verbose_name='Module Chambres activé',
        help_text='Permet aux membres de ce groupe d\'accéder à la gestion des chambres d\'hospitalisation',
    )
    membres = models.ManyToManyField(
        Utilisateur, blank=True, related_name='groupes',
        verbose_name='Membres',
    )
    menus = models.ManyToManyField(
        Menu, blank=True, verbose_name='Menus autorisés',
        help_text='Cochez les menus auxquels ce groupe donne accès.',
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

    def _serialiser_pour_corbeille(self):
        return {
            'nom': self.nom,
            'description': self.description,
            'module_chambres_actif': self.module_chambres_actif,
            'membres': [u.username for u in self.membres.all()],
            'menus': [m.url_name for m in self.menus.all()],
        }
