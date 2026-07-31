from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from core.models import Mutualite, TenantManager, get_current_mutualite


class Etablissement(models.Model):
    """Établissement de santé : Hôpital, Clinique, Centre de santé..."""

    TYPE_CHOICES = [
        ('HOPITAL', 'Hôpital'),
        ('CLINIQUE', 'Clinique'),
        ('CENTRE_SANTE', 'Centre de santé'),
        ('POLYCLINIQUE', 'Polyclinique'),
        ('CENTRE_SPECIALISE', 'Centre spécialisé'),
        ('AUTRE', 'Autre'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='etablissements',
        verbose_name='Mutualité',
    )
    code = models.CharField(max_length=20, unique=True, verbose_name='Code')
    nom = models.CharField(max_length=200, verbose_name='Nom de l\'établissement')
    sigle = models.CharField(max_length=20, blank=True, verbose_name='Sigle/Abréviation')
    type_etablissement = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='HOPITAL',
        verbose_name='Type d\'établissement',
    )
    adresse = models.TextField(blank=True, verbose_name='Adresse')
    ville = models.CharField(max_length=100, blank=True, verbose_name='Ville')
    telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    directeur = models.CharField(max_length=200, blank=True, verbose_name='Directeur')
    autorisation_fonctionnement = models.CharField(
        max_length=100, blank=True, verbose_name='N° autorisation de fonctionnement',
    )
    conventionne = models.BooleanField(default=True, verbose_name='Conventionné mutualité')
    taux_prise_en_charge_defaut = models.DecimalField(
        max_digits=5, decimal_places=2, default=80.00,
        verbose_name='Taux de prise en charge défaut (%)',
        help_text='Pourcentage pris en charge par la mutualité pour cet établissement',
    )
    actif = models.BooleanField(default=True, verbose_name='Actif')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Établissement'
        verbose_name_plural = 'Établissements'
        ordering = ['nom']

    def __str__(self):
        return f"{self.code} — {self.nom}"

    @property
    def nb_services(self):
        return self.services.filter(actif=True).count()

    @property
    def nb_chambres(self):
        return self.chambres.count()

    @property
    def nb_chambres_libres(self):
        return self.chambres.filter(statut='LIBRE').count()

    @property
    def taux_occupation_moyen(self):
        total = self.chambres.count()
        if total == 0:
            return 0
        occupees = self.chambres.filter(statut='OCCUPEE').count()
        return round((occupees / total) * 100, 2)


class Service(models.Model):
    """Service médical : Médecine, Chirurgie, Maternité, Pédiatrie, Réanimation..."""

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='services',
        verbose_name='Mutualité',
    )
    etablissement = models.ForeignKey(
        Etablissement, on_delete=models.CASCADE,
        related_name='services', verbose_name='Établissement',
    )
    code = models.CharField(max_length=20, verbose_name='Code')
    nom = models.CharField(max_length=100, verbose_name='Nom du service')
    description = models.TextField(blank=True, verbose_name='Description')
    specialite = models.CharField(max_length=100, blank=True, verbose_name='Spécialité')
    responsable = models.CharField(max_length=200, blank=True, verbose_name='Responsable du service')
    telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    etage = models.CharField(max_length=20, blank=True, verbose_name='Étage')
    aile = models.CharField(max_length=50, blank=True, verbose_name='Aile/Bâtiment')
    actif = models.BooleanField(default=True, verbose_name='Actif')
    ordre = models.PositiveIntegerField(default=0, verbose_name='Ordre d\'affichage')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Service'
        verbose_name_plural = 'Services'
        ordering = ['etablissement', 'ordre', 'nom']
        constraints = [
            models.UniqueConstraint(
                fields=['etablissement', 'code'],
                name='unique_service_par_etablissement'
            ),
        ]

    def __str__(self):
        return f"{self.code} — {self.nom} ({self.etablissement.nom})"

    @property
    def nombre_chambres(self):
        return self.chambres.count()

    @property
    def taux_occupation(self):
        total = self.chambres.count()
        if total == 0:
            return 0
        occupees = self.chambres.filter(statut='OCCUPEE').count()
        return round((occupees / total) * 100, 1)


class TypeChambre(models.Model):
    """Types de chambres : Standard, Privée, Suite, Réanimation, etc."""

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='types_chambre',
        verbose_name='Mutualité',
    )
    code = models.CharField(max_length=20, unique=True, verbose_name='Code')
    nom = models.CharField(max_length=100, verbose_name='Nom')
    description = models.TextField(blank=True, verbose_name='Description')
    tarif_base = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Tarif de base (BIF/jour)',
    )
    capacite = models.PositiveIntegerField(default=1, verbose_name='Capacité (lits)')
    equipements = models.TextField(blank=True, verbose_name='Équipements inclus')
    actif = models.BooleanField(default=True, verbose_name='Actif')
    ordre = models.PositiveIntegerField(default=0, verbose_name='Ordre d\'affichage')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Type de chambre'
        verbose_name_plural = 'Types de chambres'
        ordering = ['ordre', 'nom']

    def __str__(self):
        return f"{self.code} — {self.nom}"


class Chambre(models.Model):
    """Chambre d'hospitalisation physique."""

    STATUT_CHOICES = [
        ('LIBRE', 'Libre'),
        ('OCCUPEE', 'Occupée'),
        ('MAINTENANCE', 'Maintenance'),
        ('NETTOYAGE', 'Nettoyage'),
        ('RESERVEE', 'Réservée'),
        ('HORS_SERVICE', 'Hors service'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='chambres',
        verbose_name='Mutualité',
    )
    etablissement = models.ForeignKey(
        Etablissement, on_delete=models.CASCADE,
        related_name='chambres', verbose_name='Établissement',
        null=True, blank=True,
    )
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE,
        related_name='chambres', verbose_name='Service',
        null=True, blank=True,
    )
    type_chambre = models.ForeignKey(
        TypeChambre, on_delete=models.PROTECT,
        related_name='chambres', verbose_name='Type de chambre',
    )
    numero = models.CharField(max_length=20, verbose_name='Numéro')
    etage = models.CharField(max_length=20, blank=True, verbose_name='Étage')
    aile = models.CharField(max_length=50, blank=True, verbose_name='Aile/Bâtiment')
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='LIBRE',
        db_index=True, verbose_name='Statut',
    )
    lit_principal = models.CharField(max_length=20, default='Lit 1', verbose_name='Lit principal')
    lits_supplementaires = models.PositiveIntegerField(default=0, verbose_name='Lits supplémentaires')
    equipements = models.TextField(blank=True, verbose_name='Équipements spécifiques')
    observations = models.TextField(blank=True, verbose_name='Observations')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Chambre'
        verbose_name_plural = 'Chambres'
        ordering = ['etablissement', 'service', 'etage', 'aile', 'numero']
        constraints = [
            models.UniqueConstraint(
                fields=['etablissement', 'numero'],
                name='unique_chambre_par_etablissement'
            ),
        ]

    def __str__(self):
        return f"Ch. {self.numero} ({self.type_chambre.nom}) — {self.etablissement.nom}"

    @property
    def capacite_totale(self):
        return 1 + self.lits_supplementaires

    @property
    def hospitalisation_active(self):
        return self.hospitalisations.filter(statut__in=['EN_COURS', 'PROLONGEE']).first()

    @property
    def est_disponible(self):
        return self.statut == 'LIBRE' and not self.hospitalisation_active

    @property
    def tarif_journalier(self):
        return self.type_chambre.tarif_base


class Hospitalisation(models.Model):
    """Séjour d'un patient en chambre."""

    STATUT_CHOICES = [
        ('PREVUE', 'Prévue'),
        ('EN_COURS', 'En cours'),
        ('PROLONGEE', 'Prolongée'),
        ('TERMINEE', 'Terminée'),
        ('ANNULEE', 'Annulée'),
        ('TRANSFEREE', 'Transférée'),
    ]

    MODE_SORTIE_CHOICES = [
        ('GUERISON', 'Guérison'),
        ('AMELIORATION', 'Amélioration'),
        ('TRANSFERT', 'Transfert vers autre établissement'),
        ('DECES', 'Décès'),
        ('SORTIE_CONTRE_AVIS', 'Sortie contre avis médical'),
        ('AUTRE', 'Autre'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='hospitalisations',
        verbose_name='Mutualité',
    )
    etablissement = models.ForeignKey(
        Etablissement, on_delete=models.PROTECT,
        related_name='hospitalisations', verbose_name='Établissement',
        null=True, blank=True,
    )
    service = models.ForeignKey(
        Service, on_delete=models.PROTECT,
        related_name='hospitalisations', verbose_name='Service',
        null=True, blank=True,
    )
    numero_dossier = models.CharField(max_length=30, unique=True, verbose_name='N° dossier')
    chambre = models.ForeignKey(
        Chambre, on_delete=models.PROTECT,
        related_name='hospitalisations', verbose_name='Chambre',
    )
    patient_nom = models.CharField(max_length=200, verbose_name='Nom du patient')
    patient_prenom = models.CharField(max_length=200, verbose_name='Prénom du patient')
    patient_sexe = models.CharField(max_length=1, choices=[('M', 'Masculin'), ('F', 'Féminin')], verbose_name='Sexe')
    patient_date_naissance = models.DateField(verbose_name='Date de naissance')
    patient_telephone = models.CharField(max_length=50, blank=True, verbose_name='Téléphone')
    patient_adresse = models.TextField(blank=True, verbose_name='Adresse')
    affilie = models.ForeignKey(
        'affilies.Affilie', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hospitalisations',
        verbose_name='Affilié (si connu)',
    )
    date_entree = models.DateTimeField(default=timezone.now, verbose_name='Date d\'entrée')
    date_sortie_prevue = models.DateTimeField(null=True, blank=True, verbose_name='Date de sortie prévue')
    date_sortie_reelle = models.DateTimeField(null=True, blank=True, verbose_name='Date de sortie réelle')
    motif_hospitalisation = models.TextField(verbose_name='Motif d\'hospitalisation')
    diagnostic_entree = models.TextField(blank=True, verbose_name='Diagnostic à l\'entrée')
    diagnostic_sortie = models.TextField(blank=True, verbose_name='Diagnostic à la sortie')
    soins = models.TextField(blank=True, verbose_name='Soins / Traitements administrés',
        help_text='Détail des soins, médicaments, interventions quotidiens')
    medecin_referent = models.CharField(max_length=200, blank=True, verbose_name='Médecin référent')
    statut = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default='PREVUE',
        db_index=True, verbose_name='Statut',
    )
    mode_sortie = models.CharField(
        max_length=20, choices=MODE_SORTIE_CHOICES, blank=True,
        verbose_name='Mode de sortie',
    )
    observations = models.TextField(blank=True, verbose_name='Observations')
    created_by = models.ForeignKey(
        'core.Utilisateur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='hospitalisations_creees',
        verbose_name='Créé par',
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    # Champs financiers
    cout_total = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Coût total (BIF)',
        help_text='Coût total de l\'hospitalisation (chambre + soins + actes)',
    )
    taux_prise_en_charge = models.DecimalField(
        max_digits=5, decimal_places=2, default=80.00,
        verbose_name='Taux de prise en charge mutualité (%)',
        help_text='Pourcentage pris en charge par la mutualité',
    )
    prise_en_charge_mutualite = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Montant pris en charge par la mutualité (BIF)',
    )
    reste_a_charge = models.DecimalField(
        max_digits=14, decimal_places=2, default=0,
        verbose_name='Reste à charge patient (BIF)',
    )

    objects = TenantManager()

    class Meta:
        verbose_name = 'Hospitalisation'
        verbose_name_plural = 'Hospitalisations'
        ordering = ['-date_entree']

    def __str__(self):
        return f"{self.numero_dossier} — {self.patient_nom} {self.patient_prenom}"

    def calculer_finances(self):
        """Calcule automatiquement les montants financiers."""
        jours = self.duree_sejour or 1
        # Coût chambre
        cout_chambre = self.chambre.type_chambre.tarif_base * jours
        # Coût soins (à partir des objets Soin liés)
        cout_soins = self.soins_realises.aggregate(total=models.Sum('cout'))['total'] or 0
        self.cout_total = cout_chambre + cout_soins
        # Prise en charge
        taux = self.taux_prise_en_charge / 100
        self.prise_en_charge_mutualite = round(self.cout_total * taux, 2)
        self.reste_a_charge = self.cout_total - self.prise_en_charge_mutualite
        self.save(update_fields=['cout_total', 'prise_en_charge_mutualite', 'reste_a_charge'])

    @property
    def duree_sejour(self):
        if self.date_sortie_reelle:
            return (self.date_sortie_reelle - self.date_entree).days
        return (timezone.now() - self.date_entree).days

    @property
    def cout_estime(self):
        jours = self.duree_sejour or 1
        return self.chambre.type_chambre.tarif_base * jours

    def terminer(self, mode_sortie, diagnostic_sortie='', user=None):
        self.statut = 'TERMINEE'
        self.date_sortie_reelle = timezone.now()
        self.mode_sortie = mode_sortie
        self.diagnostic_sortie = diagnostic_sortie
        if user:
            self.created_by = user
        self.calculer_finances()
        self.save()
        self.chambre.statut = 'LIBRE'
        self.chambre.save(update_fields=['statut'])

    def prolonger(self, nouvelle_date_sortie):
        self.statut = 'PROLONGEE'
        self.date_sortie_prevue = nouvelle_date_sortie
        self.save(update_fields=['statut', 'date_sortie_prevue'])


class Soin(models.Model):
    """Soin / Traitement / Acte médical réalisé pendant une hospitalisation."""

    TYPE_SOIN_CHOICES = [
        ('MEDICAMENT', 'Médicament'),
        ('PANSEMENT', 'Pansement / Soin de plaie'),
        ('INJECTION', 'Injection / Perfusion'),
        ('EXAMEN', 'Examen / Bilan'),
        ('INTERVENTION', 'Intervention chirurgicale'),
        ('KINESITHERAPIE', 'Kinésithérapie / Rééducation'),
        ('SURVEILLANCE', 'Surveillance / Monitoring'),
        ('AUTRE', 'Autre'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='soins',
        verbose_name='Mutualité',
    )
    hospitalisation = models.ForeignKey(
        Hospitalisation, on_delete=models.CASCADE,
        related_name='soins_realises', verbose_name='Hospitalisation',
    )
    date_heure = models.DateTimeField(default=timezone.now, db_index=True, verbose_name='Date et heure')
    type_soin = models.CharField(max_length=20, choices=TYPE_SOIN_CHOICES, db_index=True, verbose_name='Type de soin')
    description = models.TextField(verbose_name='Description du soin')
    realise_par = models.ForeignKey(
        'core.Utilisateur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='soins_realises',
        verbose_name='Réalisé par',
    )
    cout = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Coût (BIF)',
    )
    quantite = models.PositiveIntegerField(default=1, verbose_name='Quantité')
    observations = models.TextField(blank=True, verbose_name='Observations')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    objects = TenantManager()

    class Meta:
        verbose_name = 'Soin'
        verbose_name_plural = 'Soins'
        ordering = ['-date_heure']

    def __str__(self):
        return f"{self.get_type_soin_display()} — {self.hospitalisation.numero_dossier} — {self.date_heure:%d/%m/%Y %H:%M}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Recalculer les finances de l'hospitalisation
        self.hospitalisation.calculer_finances()


class MouvementChambre(models.Model):
    """Historique des mouvements d'une chambre (entrée, sortie, transfert, maintenance)."""

    TYPE_CHOICES = [
        ('ENTREE', 'Entrée patient'),
        ('SORTIE', 'Sortie patient'),
        ('TRANSFERT_ENTRANT', 'Transfert entrant'),
        ('TRANSFERT_SORTANT', 'Transfert sortant'),
        ('MAINTENANCE_DEBUT', 'Début maintenance'),
        ('MAINTENANCE_FIN', 'Fin maintenance'),
        ('NETTOYAGE_DEBUT', 'Début nettoyage'),
        ('NETTOYAGE_FIN', 'Fin nettoyage'),
        ('RESERVATION', 'Réservation'),
        ('LIBERATION', 'Libération'),
        ('CHANGEMENT_STATUT', 'Changement de statut'),
    ]

    mutualite = models.ForeignKey(
        Mutualite, on_delete=models.CASCADE,
        null=True, blank=True, related_name='mouvements_chambre',
        verbose_name='Mutualité',
    )
    chambre = models.ForeignKey(
        Chambre, on_delete=models.CASCADE,
        related_name='mouvements', verbose_name='Chambre',
    )
    hospitalisation = models.ForeignKey(
        Hospitalisation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mouvements',
        verbose_name='Hospitalisation liée',
    )
    type_mouvement = models.CharField(max_length=30, choices=TYPE_CHOICES, db_index=True, verbose_name='Type')
    ancien_statut = models.CharField(max_length=20, choices=Chambre.STATUT_CHOICES, blank=True, verbose_name='Ancien statut')
    nouveau_statut = models.CharField(max_length=20, choices=Chambre.STATUT_CHOICES, blank=True, verbose_name='Nouveau statut')
    date_mouvement = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Date')
    utilisateur = models.ForeignKey(
        'core.Utilisateur', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='mouvements_chambre',
        verbose_name='Utilisateur',
    )
    commentaire = models.TextField(blank=True, verbose_name='Commentaire')

    class Meta:
        verbose_name = 'Mouvement de chambre'
        verbose_name_plural = 'Mouvements de chambres'
        ordering = ['-date_mouvement']

    def __str__(self):
        return f"{self.chambre} — {self.get_type_mouvement_display()} — {self.date_mouvement:%d/%m/%Y %H:%M}"