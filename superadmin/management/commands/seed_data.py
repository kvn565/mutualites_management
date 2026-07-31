from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from core.models import Mutualite, Utilisateur
from partenaires.models import Partenaire, Convention, UtilisateurPartenaire
from affilies.models import Affilie
from ayants_droit.models import AyantDroit
from factures.models import Facture, LigneFacture
from services_sante.models import ServiceSante
from pharmacie.models import Medicament, CategorieMedicament


class Command(BaseCommand):
    help = "Insere des donnees de test (membres, factures, conventions, etc.)"

    def handle(self, *args, **options):
        today = timezone.now().date()

        # ── Récupérer les objets existants ──────────────────
        try:
            hopital = Partenaire.objects.get(code_partenaire='HOP-0001')
        except Partenaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Partenaire HOP-0001 introuvable."))
            return

        try:
            pharmacie = Partenaire.objects.get(code_partenaire='PHARM-0001')
        except Partenaire.DoesNotExist:
            self.stdout.write(self.style.ERROR("Partenaire PHARM-0001 introuvable. Executez d'abord le script de creation."))
            return

        mutualites = list(Mutualite.objects.all())
        if not mutualites:
            self.stdout.write(self.style.ERROR("Aucune mutualite en base."))
            return

        super_admin = Utilisateur.objects.filter(role='SUPER_ADMIN').first()
        if not super_admin:
            self.stdout.write(self.style.ERROR("Aucun super admin trouve."))
            return

        kevin = Utilisateur.objects.filter(role='ADMIN_MUTUALITE').first()
        agent_ref = kevin or super_admin

        services = list(ServiceSante.objects.all())

        # ── Conventions ──────────────────────────────────────────
        Convention.objects.get_or_create(
            numero_convention='CONV-2026-0001',
            defaults={
                'partenaire': hopital,
                'mutualite': mutualites[0],
                'date_debut': today - timedelta(days=30),
                'date_fin': today + timedelta(days=335),
                'taux_prise_en_charge': 80.00,
                'plafond_couverture': 500000.00,
                'statut': 'ACTIVE',
                'observations': 'Convention principale - Hopital Prince Louis Rwagasore',
                'created_by': super_admin,
            },
        )

        if len(mutualites) > 1:
            Convention.objects.get_or_create(
                numero_convention='CONV-2026-0002',
                defaults={
                    'partenaire': hopital,
                    'mutualite': mutualites[1],
                    'date_debut': today - timedelta(days=15),
                    'date_fin': today + timedelta(days=180),
                    'taux_prise_en_charge': 75.00,
                    'plafond_couverture': 300000.00,
                    'statut': 'ACTIVE',
                    'observations': f'Convention avec {mutualites[1].nom}',
                    'created_by': super_admin,
                },
            )

        # ── Utilisateur partenaire ───────────────────────────────
        UtilisateurPartenaire.objects.get_or_create(
            username='gestionnaire_hopital',
            defaults={
                'partenaire': hopital,
                'mutualite': hopital.mutualite,
                'email': 'gestionnaire@hopital-prince-louis.bi',
                'telephone': '+25779990001',
                'password': 'Test123!',
                'role': 'GESTIONNAIRE',
                'actif': True,
            },
        )

        # ── Membres (affilies) ────────────────────────────────────
        membres_data = [
            {
                'numero_affiliation': 'AFF-2026-0002',
                'nom': 'Niyonzima',
                'postnom': 'Pierre',
                'prenom': 'Celestin',
                'sexe': 'M',
                'date_naissance': date(1985, 3, 15),
                'etat_civil': 'MARIE',
                'telephone': '+25771110001',
                'province': 'Bujumbura Mairie',
                'commune': 'Ntahangwa',
                'profession': 'Enseignant',
                'statut': 'ACTIF',
            },
            {
                'numero_affiliation': 'AFF-2026-0003',
                'nom': 'Havyarimana',
                'postnom': 'Jeanne',
                'prenom': 'dArc',
                'sexe': 'F',
                'date_naissance': date(1990, 7, 22),
                'etat_civil': 'MARIE',
                'telephone': '+25771110002',
                'province': 'Bujumbura Mairie',
                'commune': 'Mukaza',
                'profession': 'Infirmiere',
                'statut': 'ACTIF',
            },
            {
                'numero_affiliation': 'AFF-2026-0004',
                'nom': 'Manirakiza',
                'postnom': 'Alain',
                'prenom': 'Gilbert',
                'sexe': 'M',
                'date_naissance': date(1978, 11, 5),
                'etat_civil': 'CELIBATAIRE',
                'telephone': '+25771110003',
                'province': 'Gitega',
                'commune': 'Gitega',
                'profession': 'Comptable',
                'statut': 'ACTIF',
            },
        ]

        # Créer les affilies sous chaque mutualite liee a l hopital
        conventions_actives = Convention.objects.filter(
            partenaire=hopital, statut='ACTIVE'
        ).select_related('mutualite')

        conv_mutualites = [c.mutualite for c in conventions_actives]
        if not conv_mutualites:
            conv_mutualites = mutualites[:2]

        for i, mut in enumerate(conv_mutualites):
            for j, data in enumerate(membres_data):
                aff, created = Affilie.objects.get_or_create(
                    numero_affiliation=f'{data["numero_affiliation"]}-{i+1}',
                    defaults={
                        'mutualite': mut,
                        'nom': data['nom'],
                        'postnom': data['postnom'],
                        'prenom': data['prenom'],
                        'sexe': data['sexe'],
                        'date_naissance': data['date_naissance'],
                        'etat_civil': data['etat_civil'],
                        'telephone': data['telephone'],
                        'province': data['province'],
                        'commune': data['commune'],
                        'profession': data['profession'],
                        'statut': data['statut'],
                        'cotisation_mensuelle': Decimal('15000.00'),
                        'limite_laboratoire': Decimal('50000.00'),
                        'limite_hospitalisation_generale': Decimal('500000.00'),
                        'pharmacie_forfait': Decimal('75000.00'),
                        'cree_par': agent_ref,
                    },
                )
                if created:
                    self.stdout.write(f"  [OK] Affilie cree : {aff.nom_complet} ({mut.nom})")

                    # Ayants droit pour les membres maries
                    if data['etat_civil'] == 'MARIE' and j < 2:
                        ayants = [
                            {'nom': data['nom'], 'prenom': 'Enfant 1', 'lien': 'ENFANT', 'sexe': 'M',
                             'date_naissance': date(2015, 6, 10)},
                            {'nom': data['nom'], 'prenom': 'Enfant 2', 'lien': 'ENFANT', 'sexe': 'F',
                             'date_naissance': date(2018, 9, 20)},
                        ]
                        for ay in ayants:
                            AyantDroit.objects.get_or_create(
                                affilie=aff,
                                nom=ay['nom'],
                                prenom=ay['prenom'],
                                lien_parente=ay['lien'],
                                defaults={
                                    'mutualite': mut,
                                    'sexe': ay['sexe'],
                                    'date_naissance': ay['date_naissance'],
                                    'actif': True,
                                },
                            )
                            self.stdout.write(f"    -> Ayant droit ajoute : {ay['prenom']}")

        # ── Services (si aucun) ──────────────────────────────────
        if not services:
            services_data = [
                {'code': 'CONS-001', 'nom': 'Consultation generale', 'categorie': 'CONSULTATION'},
                {'code': 'LAB-001', 'nom': 'Analyse de sang', 'categorie': 'LABORATOIRE'},
                {'code': 'IMG-001', 'nom': 'Radio pulmonaire', 'categorie': 'IMAGERIE'},
                {'code': 'HOSP-001', 'nom': 'Hospitalisation jour', 'categorie': 'HOSPITALISATION'},
                {'code': 'PHARM-001', 'nom': 'Paracetamol 500mg', 'categorie': 'PHARMACIE'},
            ]
            for svc in services_data:
                s, created = ServiceSante.objects.get_or_create(
                    code=svc['code'],
                    defaults={
                        'nom': svc['nom'],
                        'categorie': svc['categorie'],
                        'actif': True,
                    },
                )
                if created:
                    services.append(s)
                    self.stdout.write(f"  [OK] Service cree : {s.nom}")

        # ── Factures ────────────────────────────────────────────
        affilies_list = list(Affilie.objects.filter(
            mutualite__in=[m.id for m in conv_mutualites]
        )[:5])

        if affilies_list and services:
            for idx, aff in enumerate(affilies_list):
                date_facture = today - timedelta(days=idx * 3)
                facture, created = Facture.objects.get_or_create(
                    numero=f'FAC-202607-{idx+1:04d}',
                    defaults={
                        'mutualite': aff.mutualite,
                        'date': date_facture,
                        'partenaire': hopital,
                        'affilie': aff,
                        'diagnostic': 'Consultation de routine',
                        'statut': 'PAYE' if idx < 2 else ('VALIDE' if idx < 4 else 'SOUMIS'),
                        'cree_par': agent_ref,
                    },
                )
                if created:
                    # Ajouter des lignes de facture
                    for k in range(1, min(3, len(services) + 1)):
                        taux = 80 if facture.mutualite == mutualites[0] else 75
                        prix_map = {
                            'Consultation generale': '20000',
                            'Analyse de sang': '15000',
                            'Radio pulmonaire': '35000',
                            'Hospitalisation jour': '50000',
                            'Paracetamol 500mg': '5000',
                        }
                        prix = Decimal(prix_map.get(services[k - 1].nom, '10000'))
                        LigneFacture.objects.get_or_create(
                            facture=facture,
                            service=services[k - 1],
                            defaults={
                                'mutualite': aff.mutualite,
                                'designation': services[k - 1].nom,
                                'quantite': 1,
                                'prix_unitaire': prix,
                                'taux_applique': Decimal(str(taux)),
                            },
                        )

                    # Recalculer les montants
                    total = Decimal('0')
                    part_mut = Decimal('0')
                    for ligne in facture.lignes.all():
                        total += ligne.total_ligne
                        part_mut += ligne.part_mutualite
                    facture.montant_total = total
                    facture.montant_mutualite = part_mut
                    facture.montant_ticket_moderateur = total - part_mut
                    facture.save(update_fields=[
                        'montant_total', 'montant_mutualite', 'montant_ticket_moderateur'
                    ])
                    self.stdout.write(f"  [OK] Facture creee : {facture.numero} pour {aff.nom}")

        # ═══════════════════════════════════════════════════════
        # ── PHARMACIE : Médicaments ──────────────────────────
        # ═══════════════════════════════════════════════════════
        cat_analgesique, _ = CategorieMedicament.objects.get_or_create(
            nom='Analgésiques',
            defaults={'mutualite': mutualites[0], 'description': 'Antidouleurs et antipyrétiques'}
        )
        cat_antibio, _ = CategorieMedicament.objects.get_or_create(
            nom='Antibiotiques',
            defaults={'mutualite': mutualites[0], 'description': 'Anti-infectieux bactériens'}
        )
        cat_antiinflam, _ = CategorieMedicament.objects.get_or_create(
            nom='Anti-inflammatoires',
            defaults={'mutualite': mutualites[0], 'description': 'Anti-inflammatoires stéroïdiens et non stéroïdiens'}
        )
        cat_cardiaque, _ = CategorieMedicament.objects.get_or_create(
            nom='Cardiovasculaires',
            defaults={'mutualite': mutualites[0], 'description': 'Traitements cardiovasculaires'}
        )
        cat_digestif, _ = CategorieMedicament.objects.get_or_create(
            nom='Digestifs',
            defaults={'mutualite': mutualites[0], 'description': 'Traitements du système digestif'}
        )

        medicaments_data = [
            {'code': 'AMOX-500', 'nom': 'Amoxicilline', 'dci': 'Amoxicilline trihydratée', 'cat': cat_antibio, 'forme': 'GELULE', 'dosage': '500 mg', 'prix': '4500.00'},
            {'code': 'PARA-500', 'nom': 'Paracétamol', 'dci': 'Paracétamol', 'cat': cat_analgesique, 'forme': 'COMPRIME', 'dosage': '500 mg', 'prix': '1500.00'},
            {'code': 'IBU-400', 'nom': 'Ibuprofène', 'dci': 'Ibuprofène', 'cat': cat_antiinflam, 'forme': 'COMPRIME', 'dosage': '400 mg', 'prix': '2500.00'},
            {'code': 'OMEP-20', 'nom': 'Oméprazole', 'dci': 'Oméprazole', 'cat': cat_digestif, 'forme': 'GELULE', 'dosage': '20 mg', 'prix': '5500.00'},
            {'code': 'DICLO-50', 'nom': 'Diclofénac', 'dci': 'Diclofénac sodique', 'cat': cat_antiinflam, 'forme': 'COMPRIME', 'dosage': '50 mg', 'prix': '2000.00'},
            {'code': 'AMLO-5', 'nom': 'Amlodipine', 'dci': 'Amlodipine', 'cat': cat_cardiaque, 'forme': 'COMPRIME', 'dosage': '5 mg', 'prix': '6000.00'},
            {'code': 'CIPRO-500', 'nom': 'Ciprofloxacine', 'dci': 'Ciprofloxacine', 'cat': cat_antibio, 'forme': 'COMPRIME', 'dosage': '500 mg', 'prix': '7500.00'},
            {'code': 'METFO-850', 'nom': 'Metformine', 'dci': 'Metformine HCl', 'cat': cat_digestif, 'forme': 'COMPRIME', 'dosage': '850 mg', 'prix': '3500.00'},
        ]

        for md in medicaments_data:
            med, created = Medicament.objects.get_or_create(
                code=md['code'],
                defaults={
                    'mutualite': mutualites[0],
                    'nom': md['nom'],
                    'dci': md['dci'],
                    'categorie': md['cat'],
                    'forme': md['forme'],
                    'dosage': md['dosage'],
                    'prix_reference': Decimal(md['prix']),
                    'pris_en_charge': True,
                    'taux_remboursement': Decimal('80.00'),
                    'actif': True,
                }
            )
            if created:
                self.stdout.write(f"  [OK] Médicament créé : {med.nom} {med.dosage}")

        # ═══════════════════════════════════════════════════════
        # ── PHARMACIE : Factures ─────────────────────────────
        # ═══════════════════════════════════════════════════════
        # Créer ou récupérer un service générique "Pharmacie"
        service_pharma, _ = ServiceSante.objects.get_or_create(
            code='PHARM-001',
            defaults={
                'nom': 'Délivrance médicaments',
                'categorie': 'PHARMACIE',
                'description': 'Délivrance de médicaments en pharmacie',
                'taux_prise_en_charge': Decimal('80.00'),
                'actif': True,
            }
        )
        if _:
            self.stdout.write(f"  [OK] Service pharmacie créé")

        affilies_pharma = list(Affilie.objects.filter(
            mutualite=mutualites[0],
        )[:3])

        medicaments_list = list(Medicament.objects.filter(
            mutualite=mutualites[0], actif=True
        )[:5])

        if affilies_pharma and medicaments_list:
            for idx, aff in enumerate(affilies_pharma):
                date_facture = today - timedelta(days=idx * 4)
                facture, created = Facture.objects.get_or_create(
                    numero=f'FAC-PHARM-202607-{idx+1:04d}',
                    defaults={
                        'mutualite': mutualites[0],
                        'date': date_facture,
                        'partenaire': pharmacie,
                        'affilie': aff,
                        'diagnostic': 'Délivrance de médicaments prescrits',
                        'statut': 'PAYE' if idx < 1 else ('VALIDE' if idx < 2 else 'SOUMIS'),
                        'cree_par': agent_ref,
                    },
                )
                if created:
                    for k in range(1, min(4, len(medicaments_list) + 1)):
                        med = medicaments_list[k - 1]
                        taux = Decimal('80')
                        prix = med.prix_reference
                        LigneFacture.objects.get_or_create(
                            facture=facture,
                            service=service_pharma,
                            defaults={
                                'mutualite': mutualites[0],
                                'designation': f'{med.nom} {med.dosage} ({med.forme})',
                                'quantite': k,
                                'prix_unitaire': prix,
                                'taux_applique': taux,
                            },
                        )

                    total = Decimal('0')
                    part_mut = Decimal('0')
                    for ligne in facture.lignes.all():
                        total += ligne.total_ligne
                        part_mut += ligne.part_mutualite
                    facture.montant_total = total
                    facture.montant_mutualite = part_mut
                    facture.montant_ticket_moderateur = total - part_mut
                    facture.save(update_fields=[
                        'montant_total', 'montant_mutualite', 'montant_ticket_moderateur'
                    ])
                    self.stdout.write(f"  [OK] Facture pharmacie créée : {facture.numero} pour {aff.nom}")

        self.stdout.write(self.style.SUCCESS("\n[OK] Donnees de test inserees avec succes."))
