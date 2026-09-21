# affilies/models.py
from django.db import models
from django.utils import timezone
from core.models import Utilisateur, TenantManager

class Affilie(models.Model):
    SEXE_CHOICES = [('M','Masculin'),('F','Féminin')]
    ETAT_CIVIL_CHOICES = [
        ('CELIBATAIRE', 'Célibataire'),
        ('MARIE', 'Marié(e)'),
        ('DIVORCE', 'Divorcé(e)'),
        ('VEUF', 'Veuf/Veuve'),
    ]
    TYPE_ADHESION_CHOICES = [
        ('INDIVIDUELLE', 'Individuelle'),
        ('FAMILIALE', 'Familiale'),
        ('GROUPE', 'Groupe/Association'),
    ]
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('ACTIF', 'Actif'),
        ('SUSPENDU', 'Suspendu'),
        ('EXPIRE', 'Expiré'),
        ('RADIE', 'Radié'),
    ]
    GROUPE_SANGUIN_CHOICES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
        ('NSP', 'Non connu'),
    ]

    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )
    
    numero_affiliation = models.CharField(max_length=20, unique=True, verbose_name='ID du membre')
    nom = models.CharField(max_length=100, db_index=True, verbose_name='Nom')
    prenom = models.CharField(max_length=100, db_index=True, verbose_name='Prénom')
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, verbose_name='Sexe')
    date_naissance = models.DateField(verbose_name='Date de naissance')
    etat_civil = models.CharField(
        max_length=20, choices=ETAT_CIVIL_CHOICES, default='CELIBATAIRE',
        verbose_name='État civil',
    )
    numero_carte_identite = models.CharField(
        max_length=30, blank=True, verbose_name='N° Carte nationale d\'identité (CIN/NIF)',
    )

    province = models.CharField(max_length=100, blank=True, verbose_name='Province')
    commune = models.CharField(max_length=100, blank=True, verbose_name='Commune')
    zone = models.CharField(max_length=100, blank=True, verbose_name='Zone')
    colline = models.CharField(max_length=100, blank=True, verbose_name='Colline/Quartier')
    adresse = models.TextField(blank=True, verbose_name='Adresse complément')
    telephone = models.CharField(max_length=20, blank=True, db_index=True, verbose_name='Téléphone')
    email = models.EmailField(blank=True, verbose_name='Email')
    profession = models.CharField(max_length=100, blank=True, verbose_name='Profession')

    photo = models.ImageField(upload_to='affilies/portraits/', blank=True, null=True, verbose_name='Photo du membre')

    groupe_sanguin = models.CharField(
        max_length=3, choices=GROUPE_SANGUIN_CHOICES, blank=True,
        verbose_name='Groupe sanguin',
    )
    contact_urgence_nom = models.CharField(
        max_length=200, blank=True, verbose_name='Personne à contacter (urgence)',
    )
    contact_urgence_telephone = models.CharField(
        max_length=20, blank=True, verbose_name='Téléphone (urgence)',
    )
    centre_sante_reference = models.CharField(
        max_length=200, blank=True, verbose_name='Centre de santé de référence',
    )
    hopital_reference = models.CharField(
        max_length=200, blank=True, verbose_name='Hôpital de référence',
    )

    date_adhesion = models.DateField(default=timezone.localdate, verbose_name="Date d'inscription")
    type_adhesion = models.CharField(
        max_length=20, choices=TYPE_ADHESION_CHOICES, default='INDIVIDUELLE',
        verbose_name="Type d'adhésion",
    )
    section_antenne = models.CharField(
        max_length=100, blank=True, verbose_name='Section/Antenne locale',
    )
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='ACTIF', db_index=True)
    notes = models.TextField(blank=True, verbose_name='Notes')
    
    origine = models.ForeignKey(
        'origines.Origine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='affilies',
        verbose_name='Origine',
    )
    categorie_origine = models.ForeignKey(
        'origines.CategorieOrigine',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='affilies',
        verbose_name='Catégorie d\'origine',
    )
    
    # ── Garanties / Plafonds de remboursement ────────────────────
    cotisation_mensuelle = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Cotisation mensuelle (BIF)',
    )
    limite_laboratoire = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Laboratoire (BIF)',
    )
    limite_kinesitherapie = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Kinésithérapie (BIF)',
    )
    limite_reanimation = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Réanimation (BIF)',
    )
    limite_imagerie_medicale = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Imagerie Médicale (BIF)',
    )
    soins_ambulatoires = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Soins Ambulatoires (BIF)',
    )
    hopital_plafond_chambre = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Hôpital plafond chambre/nuit (BIF)',
    )
    hpc_nuit = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='HPC / Nuit (BIF)',
    )
    limite_hospitalisation_generale = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limite Hospitalisation Générale (BIF)',
    )
    maternite_forfait = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Maternité forfait (BIF)',
    )
    pourcentage_maternite = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Pourcentage Maternité (%)',
    )
    pharmacie_forfait = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Pharmacie forfait (BIF)',
    )
    limites_medicaments = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limites Médicaments (BIF)',
    )
    limites_lunettes = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limites Lunettes (verre et monture) (BIF)',
    )
    limites_dents = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Limites Soins Dentaires (BIF)',
    )

    # ── Plafond mensuel global & blocage ─────────────────────────
    plafond_mensuel = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        verbose_name='Plafond mensuel global (BIF)',
        help_text='Montant total remboursable par mois. 0 = pas de limite.',
    )
    bloque = models.BooleanField(default=False, verbose_name='Bloqué')
    bloque_definitif = models.BooleanField(default=False, verbose_name='Bloqué définitivement')

    # Soft delete
    actif = models.BooleanField(default=True, db_index=True)
    supprime = models.BooleanField(default=False, db_index=True, verbose_name='Supprimé')
    date_suppression = models.DateTimeField(null=True, blank=True)
    
    # Audit
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='affilies_crees',
        verbose_name="Agent d'enregistrement",
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    objects = TenantManager()

    class Meta:
        verbose_name = 'Affilié'
        verbose_name_plural = 'Affiliés'
        ordering = ['nom', 'prenom']
    
    def __str__(self):
        return f"{self.numero_affiliation} — {self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        return f"{self.nom} {self.prenom}".strip()
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        b = self.date_naissance
        return today.year - b.year - ((today.month, today.day) < (b.month, b.day))
    
    @property
    def nombre_beneficiaires(self):
        return self.ayants_droit.filter(actif=True).count()

    @property
    def total_cotisations_payees(self):
        from django.db.models import Sum
        from cotisations.models import Cotisation
        return Cotisation.objects.filter(affilie=self, statut='PAYE').aggregate(
            total=Sum('montant')
        )['total'] or 0

    @property
    def total_cotisations_dues(self):
        from django.db.models import Sum
        from cotisations.models import Cotisation
        return Cotisation.objects.filter(affilie=self).aggregate(
            total=Sum('montant')
        )['total'] or 0

    @property
    def cotisations_en_retard(self):
        from cotisations.models import Cotisation
        from datetime import date
        return Cotisation.objects.filter(
            affilie=self, 
            statut__in=['EN_ATTENTE', 'EN_RETARD'],
            date_echeance__lt=date.today()
        ).count()

    def factures_mensuelles_mutualite(self, mois=None, annee=None):
        """Montant total que la mutualité paiera pour cet affilié (Part Mutualité) par mois."""
        from factures.models import Facture
        from django.db.models import Sum
        from datetime import date
        
        if mois is None:
            mois = date.today().month
        if annee is None:
            annee = date.today().year
            
        # Include factures where affiliate is either titulaire or having right
        from django.db.models import Q
        return Facture.objects.filter(
            Q(affilie=self) | Q(ayant_droit__affilie=self),
            mutualite=self.mutualite,
            date__month=mois,
            date__year=annee,
            statut__in=['VALIDE', 'PAYE']  # Only validated/paid factures
        ).aggregate(total=Sum('montant_mutualite'))['total'] or 0

    def factures_mensuelles_total(self, mois=None, annee=None):
        """Montant total des factures (tout statut) pour cet affilié par mois."""
        from factures.models import Facture
        from django.db.models import Sum
        from datetime import date
        
        if mois is None:
            mois = date.today().month
        if annee is None:
            annee = date.today().year
            
        from django.db.models import Q
        return Facture.objects.filter(
            Q(affilie=self) | Q(ayant_droit__affilie=self),
            mutualite=self.mutualite,
            date__month=mois,
            date__year=annee
        ).aggregate(total=Sum('montant_total'))['total'] or 0

    def total_factures_mutualite(self):
        """Total Part Mutualité sur toutes les factures VALIDE/PAYE."""
        from factures.models import Facture
        from django.db.models import Sum
        from django.db.models import Q
        return Facture.objects.filter(
            Q(affilie=self) | Q(ayant_droit__affilie=self),
            mutualite=self.mutualite,
            statut__in=['VALIDE', 'PAYE']
        ).aggregate(total=Sum('montant_mutualite'))['total'] or 0

    def total_factures_all(self):
        """Total Montant Total sur toutes les factures."""
        from factures.models import Facture
        from django.db.models import Sum
        from django.db.models import Q
        return Facture.objects.filter(
            Q(affilie=self) | Q(ayant_droit__affilie=self),
            mutualite=self.mutualite
        ).aggregate(total=Sum('montant_total'))['total'] or 0

    def total_cotisations_payees_all(self):
        """Total cotisations PAYE sur toute la période."""
        from cotisations.models import Cotisation
        from django.db.models import Sum
        return Cotisation.objects.filter(
            affilie=self, statut='PAYE'
        ).aggregate(total=Sum('montant'))['total'] or 0

    def total_cotisations_all(self):
        """Total cotisations dues sur toute la période."""
        from cotisations.models import Cotisation
        from django.db.models import Sum
        return Cotisation.objects.filter(affilie=self).aggregate(total=Sum('montant'))['total'] or 0

    def factures_par_mois(self, annee=None):
        """Détail des factures (mutualité et total) groupé par mois."""
        from factures.models import Facture
        from django.db.models import Sum
        from django.db.models import Q
        from datetime import date
        
        if annee is None:
            annee = date.today().year
            
        qs = Facture.objects.filter(
            Q(affilie=self) | Q(ayant_droit__affilie=self),
            mutualite=self.mutualite,
            date__year=annee
        ).values('date__month').annotate(
            total_mutualite=Sum('montant_mutualite', filter=Q(statut__in=['VALIDE', 'PAYE'])),
            total_all=Sum('montant_total')
        ).order_by('date__month')
        
        result = []
        for item in qs:
            result.append({
                'mois': item['date__month'],
                'mutualite': item['total_mutualite'] or 0,
                'total': item['total_all'] or 0,
            })
        return result

    def cotisations_par_mois(self, annee=None):
        """Détail des cotisations payées groupé par mois."""
        from cotisations.models import Cotisation
        from django.db.models import Sum
        from datetime import date
        
        if annee is None:
            annee = date.today().year
            
        qs = Cotisation.objects.filter(
            affilie=self,
            annee=annee,
            statut='PAYE'
        ).values('mois').annotate(
            total=Sum('montant')
        ).order_by('mois')
        
        result = []
        for item in qs:
            result.append({
                'mois': item['mois'],
                'total': item['total'] or 0,
            })
        return result

    @property
    def plafonds_effectifs(self):
        from decimal import Decimal
        champs = [
            'cotisation_mensuelle', 'taux_prise_en_charge', 'soins_ambulatoires', 'limite_laboratoire',
            'limite_kinesitherapie', 'limite_reanimation', 'limite_imagerie_medicale',
            'hopital_plafond_chambre', 'hpc_nuit', 'limite_hospitalisation_generale',
            'maternite_forfait', 'pourcentage_maternite', 'pharmacie_forfait',
            'limites_medicaments', 'limites_lunettes', 'limites_dents',
        ]
        resultat = {}
        for champ in champs:
            valeur = getattr(self, champ, None) or Decimal('0')
            # 1. Check category first
            if valeur <= 0 and self.categorie_origine:
                valeur = getattr(self.categorie_origine, champ, None) or Decimal('0')
            # 2. Then origine
            if valeur <= 0 and self.origine:
                valeur = getattr(self.origine, champ, None) or Decimal('0')
            # 3. Then mutualité defaults
            if valeur <= 0 and self.mutualite_id:
                valeur = getattr(self.mutualite, f'def_{champ}', None) or Decimal('0')
            resultat[champ] = valeur
        return resultat
    
    def save(self, *args, **kwargs):
        if not self.numero_affiliation:
            super().save(*args, **kwargs)
            code = self.mutualite.code_mutualite if self.mutualite else 'MUT'
            self.numero_affiliation = f"{code}-{self.pk}"
            super().save(update_fields=['numero_affiliation'])
        else:
            super().save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False, hard=False, user=None):
        if hard:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            self.supprime = True
            self.actif = False
            self.date_suppression = timezone.now()
            self.save(update_fields=['supprime', 'actif', 'date_suppression'])
            from comptabilite.models import DeletedItem
            DeletedItem.objects.enregistrer(self, user)

    def restore(self, user=None):
        self.supprime = False
        self.actif = True
        self.date_suppression = None
        self.save(update_fields=['supprime', 'actif', 'date_suppression'])
        from comptabilite.models import DeletedItem
        from django.contrib.contenttypes.models import ContentType
        DeletedItem.objects.filter(
            content_type=ContentType.objects.get_for_model(self),
            object_id=self.pk,
            mutualite=getattr(self, 'mutualite', None),
            restored_at__isnull=True
        ).update(restored_at=timezone.now(), restored_by=user)

    def _serialiser_pour_corbeille(self):
        return {
            'numero_affiliation': self.numero_affiliation,
            'nom': self.nom,
            'prenom': self.prenom,
            'sexe': self.sexe,
            'date_naissance': str(self.date_naissance) if self.date_naissance else None,
            'etat_civil': self.etat_civil,
            'telephone': self.telephone,
            'email': self.email,
            'statut': self.statut,
            'cotisation_mensuelle': str(self.cotisation_mensuelle),
            'plafond_mensuel': str(self.plafond_mensuel),
        }


class AffilieExclusion(models.Model):
    mutualite = models.ForeignKey(
        'core.Mutualite', on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss',
        verbose_name='Mutualité',
    )
    affilie = models.ForeignKey(
        Affilie, on_delete=models.CASCADE,
        related_name='exclusions', verbose_name='Affilié',
    )
    medicament = models.ForeignKey(
        'pharmacie.Medicament', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Médicament',
    )
    service = models.ForeignKey(
        'services_sante.ServiceSante', on_delete=models.CASCADE,
        null=True, blank=True, verbose_name='Service',
    )
    motif = models.TextField(blank=True, verbose_name='Motif d\'exclusion')
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name='Date de création')
    cree_par = models.ForeignKey(
        Utilisateur, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Créé par',
    )

    objects = TenantManager()

    class Meta:
        verbose_name = 'Exclusion'
        verbose_name_plural = 'Exclusions'
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(medicament__isnull=False, service__isnull=True) |
                    models.Q(medicament__isnull=True, service__isnull=False)
                ),
                name='exclusion_un_seul_type',
                violation_error_message='Une exclusion doit concerner soit un médicament, soit un service.',
            ),
        ]

    def __str__(self):
        if self.medicament:
            return f"{self.affilie.nom_complet} → Médicament: {self.medicament.nom}"
        if self.service:
            return f"{self.affilie.nom_complet} → Service: {self.service.nom}"
        return f"Exclusion #{self.pk}"
