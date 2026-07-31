# aide/models.py
from django.db import models
from core.models import Mutualite, Utilisateur, TenantManager


class CategorieAide(models.Model):
    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        related_name='categories_aide', verbose_name='Mutualité',
    )
    nom = models.CharField(max_length=100, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    icone = models.CharField(max_length=50, blank=True, verbose_name='Icône Bootstrap')
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name='Ordre')
    actif = models.BooleanField(default=True, verbose_name='Actif')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Catégorie d\'aide'
        verbose_name_plural = 'Catégories d\'aide'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return self.nom

    def articles_publies_count(self):
        return self.articles.filter(publie=True).count()

    @property
    def nb_articles_publies(self):
        return self.articles_publies_count()


class ArticleAide(models.Model):
    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        related_name='articles_aide', verbose_name='Mutualité',
    )
    categorie = models.ForeignKey(
        CategorieAide, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='articles',
        verbose_name='Catégorie',
    )
    titre = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(max_length=220, verbose_name='Identifiant URL')
    resume = models.TextField(blank=True, verbose_name='Résumé')
    contenu = models.TextField(verbose_name='Contenu (HTML/Markdown)')
    mots_cles = models.CharField(max_length=255, blank=True, verbose_name='Mots-clés (séparés par des virgules)')
    publie = models.BooleanField(default=True, verbose_name='Publié')
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name='Ordre dans la catégorie')
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='articles_aide_crees',
        verbose_name='Créé par',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Article d\'aide'
        verbose_name_plural = 'Articles d\'aide'
        ordering = ['categorie__ordre', 'ordre', 'titre']
        unique_together = [('mutualite', 'slug')]

    def __str__(self):
        return self.titre

    @property
    def mots_cles_list(self):
        if not self.mots_cles:
            return []
        return [m.strip() for m in self.mots_cles.split(',') if m.strip()]

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('aide:article', kwargs={'slug': self.slug})


# ──────────────────────────────────────────────
# SuperAdmin ↔ Mutualité : Messages & Documents
# ──────────────────────────────────────────────

class MessageSuperAdmin(models.Model):
    """Message d'un admin mutualité vers le SuperAdmin plateforme."""
    STATUT_CHOICES = [
        ('NOUVEAU', 'Nouveau'),
        ('EN_COURS', 'En cours de traitement'),
        ('REPONDU', 'Répondu'),
        ('FERME', 'Fermé'),
    ]
    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        related_name='messages_superadmin', verbose_name='Mutualité',
    )
    expediteur = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messages_envoyes_superadmin',
        verbose_name='Expéditeur',
    )
    sujet = models.CharField(max_length=200, verbose_name='Sujet')
    message = models.TextField(verbose_name='Message')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='NOUVEAU', verbose_name='Statut')
    reponse = models.TextField(blank=True, verbose_name='Réponse du SuperAdmin')
    repondu_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='messages_repondu_superadmin',
        verbose_name='Répondu par',
    )
    date_reponse = models.DateTimeField(null=True, blank=True, verbose_name='Date de réponse')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Message au SuperAdmin'
        verbose_name_plural = 'Messages au SuperAdmin'
        ordering = ['-date_creation']

    def __str__(self):
        return f"[{self.mutualite.code_mutualite}] {self.sujet}"


class TypeDocumentSuperAdmin(models.TextChoices):
    DOCUMENTATION = 'DOCUMENTATION', 'Documentation'
    GUIDE = 'GUIDE', 'Guide'
    FAQ = 'FAQ', 'FAQ'


class DocumentSuperAdmin(models.Model):
    """Documents publiés par le SuperAdmin pour toutes les mutualités."""
    type_document = models.CharField(
        max_length=20, choices=TypeDocumentSuperAdmin.choices,
        verbose_name='Type de document',
    )
    titre = models.CharField(max_length=200, verbose_name='Titre')
    slug = models.SlugField(max_length=220, unique=True, verbose_name='Identifiant URL')
    resume = models.TextField(blank=True, verbose_name='Résumé')
    contenu = models.TextField(verbose_name='Contenu (HTML/Markdown)')
    fichier = models.FileField(
        upload_to='superadmin/documents/', blank=True, null=True,
        verbose_name='Fichier joint (PDF, DOC, etc.)',
    )
    version = models.CharField(max_length=20, blank=True, verbose_name='Version')
    publie = models.BooleanField(default=True, verbose_name='Publié')
    ordre = models.PositiveSmallIntegerField(default=0, verbose_name='Ordre d\'affichage')
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='documents_superadmin_crees',
        verbose_name='Créé par',
    )
    video_url = models.URLField(blank=True, verbose_name='Lien vidéo (YouTube/Vimeo)')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_publication = models.DateTimeField(null=True, blank=True, verbose_name='Date de publication')

    class Meta:
        verbose_name = 'Document SuperAdmin'
        verbose_name_plural = 'Documents SuperAdmin'
        ordering = ['type_document', 'ordre', '-date_publication']
        indexes = [
            models.Index(fields=['type_document', 'publie']),
        ]

    def __str__(self):
        return f"[{self.get_type_document_display()}] {self.titre}"

    def save(self, *args, **kwargs):
        if self.publie and not self.date_publication:
            from django.utils import timezone
            self.date_publication = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('aide:doc_superadmin_detail', kwargs={'slug': self.slug})